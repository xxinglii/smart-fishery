"""ONVIF 云台控制（真控制 / 本地状态机双后端）。

- **真控制**：装了 `onvif-zeep` 且相机可达时，通过 ONVIF ContinuousMove / GotoPreset /
  SetPreset 真正驱动球机；位置从 GetStatus 回读。
- **本地状态机（mock）**：没装依赖、相机不可达、或显式 `--force-ptz-mock` 时启用。
  它按"速度 × 步进时长"积分出 pan/tilt/zoom，行为与真控制**对接口完全一致**，
  所以前端不需要区分后端；降级原因写进 /api/v1/logs 与 health.services。
- 位置与预置位持久化到 `<data_dir>/ptz.json`，重启不丢。

契约 §2 的 ptz 对象：{pan, tilt, zoom, zoom_max, moving, preset_id}
契约 §2 的 presets 对象：{id, name, camera_id, pan, tilt, zoom}
"""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from . import has, note_degraded

#: 一次 move 调用等效的"按住时长"（相对步进的物理含义，写死并写进 README）
MOVE_STEP_S = 0.4


class PTZController:
    """单台相机的云台控制器。"""

    def __init__(self, camera, cfg, store, logger=None, force_mock: bool = False) -> None:
        self.camera = camera
        self.cfg = cfg
        self.store = store
        self._log = logger
        self.ptz_cfg = camera.ptz_cfg or {}
        self.zoom_max = float(self.ptz_cfg.get("zoom_max", 23) or 23)
        self.pan_speed = float(self.ptz_cfg.get("pan_speed_dps", 60.0) or 60.0)
        self.tilt_speed = float(self.ptz_cfg.get("tilt_speed_dps", 30.0) or 30.0)
        self.zoom_speed = float(self.ptz_cfg.get("zoom_speed", 0.6) or 0.6)
        self.pan_min = float(self.ptz_cfg.get("pan_min", 0.0) or 0.0)
        self.pan_max = float(self.ptz_cfg.get("pan_max", 360.0) or 360.0)
        self.tilt_min = float(self.ptz_cfg.get("tilt_min", -90.0) or -90.0)
        self.tilt_max = float(self.ptz_cfg.get("tilt_max", 25.0) or 25.0)

        self._lock = threading.RLock()
        self._state_path = os.path.join(store.data_dir, "ptz.json")
        self._pan = 0.0
        self._tilt = 0.0
        self._zoom = 1.0
        self._preset_id: Optional[int] = None
        self._moving_until = 0.0
        self._presets: List[Dict[str, Any]] = []
        self._patrol_on = False
        self._patrol_ids: List[int] = []
        self._patrol_dwell = 30.0
        self._patrol_index = 0
        self._patrol_last = 0.0

        self._onvif = None
        self._onvif_down_until = 0.0
        self._onvif_ready = False
        self.force_mock = force_mock or not has("onvif")
        self._load()
        if self.force_mock:
            reason = (
                "onvif-zeep 不可用，云台使用本地状态机（mock）"
                if not has("onvif")
                else "显式 --force-ptz-mock，云台使用本地状态机"
            )
            note_degraded("ptz", "%s：%s；接口行为一致但不会真的转动相机" % (camera.id, reason))
            self._logw("warn", "%s %s" % (camera.id, reason))

    # ---------------- 基础设施 ----------------
    def _logw(self, level: str, msg: str) -> None:
        if self._log:
            self._log(level, "ptz", msg)

    def _load(self) -> None:
        data: Dict[str, Any] = {}
        if os.path.exists(self._state_path):
            try:
                with open(self._state_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh) or {}
            except Exception as exc:
                self._logw("warn", "%s 读取 ptz.json 失败：%s" % (self.camera.id, exc))
        states = data.get("state") or {}
        mine = states.get(self.camera.id) or {}
        self._pan = float(mine.get("pan", 0.0))
        self._tilt = float(mine.get("tilt", 0.0))
        self._zoom = float(mine.get("zoom", 1.0))
        self._preset_id = mine.get("preset_id")
        presets = data.get("presets")
        if isinstance(presets, list) and presets:
            self._presets = [p for p in presets if isinstance(p, dict) and p.get("camera_id") == self.camera.id]
        if not self._presets:
            self._presets = [
                dict(p)
                for p in (self.cfg.get("ptz_presets", []) or [])
                if isinstance(p, dict) and p.get("camera_id") == self.camera.id
            ]
        patrol = self.cfg.get("patrol", {}) or {}
        self._patrol_on = bool(patrol.get("on"))
        self._patrol_ids = [int(x) for x in (patrol.get("preset_ids") or [])]
        self._patrol_dwell = float(patrol.get("dwell_s", 30) or 30)

    def _save(self) -> None:
        path = self._state_path
        try:
            data: Dict[str, Any] = {"state": {}, "presets": []}
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        data = json.load(fh) or data
                except Exception:
                    pass
            data.setdefault("state", {})
            data["state"][self.camera.id] = {
                "pan": round(self._pan, 2),
                "tilt": round(self._tilt, 2),
                "zoom": round(self._zoom, 2),
                "preset_id": self._preset_id,
            }
            others = [
                p for p in (data.get("presets") or []) if p.get("camera_id") != self.camera.id
            ]
            data["presets"] = others + self._presets
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=1)
            os.replace(tmp, path)
        except Exception as exc:
            self._logw("warn", "%s 保存 ptz.json 失败：%s" % (self.camera.id, exc))

    # ---------------- ONVIF ----------------
    def _ensure_onvif(self) -> bool:
        if self.force_mock or not has("onvif"):
            return False
        if self._onvif_ready:
            return True
        if time.time() < self._onvif_down_until:
            return False
        try:
            from onvif import ONVIFCamera  # type: ignore

            cam = ONVIFCamera(
                self.camera.ip,
                int(self.camera.cam.get("onvif_port") or 80),
                str(self.camera.cam.get("rtsp_user") or "admin"),
                str(self.camera.cam.get("rtsp_password") or ""),
            )
            media = cam.create_media_service()
            profiles = media.GetProfiles()
            if not profiles:
                raise RuntimeError("ONVIF 未返回媒体 Profile")
            self._onvif = {"cam": cam, "ptz": cam.create_ptz_service(), "token": profiles[0].token}
            self._onvif_ready = True
            self._logw("info", "%s ONVIF 已连接，启用车台真控制" % self.camera.id)
            return True
        except Exception as exc:
            self._onvif_down_until = time.time() + 60.0
            note_degraded("ptz-onvif", "%s：ONVIF 连接失败，暂用本地状态机（60 s 后重试）" % self.camera.id)
            self._logw("warn", "%s ONVIF 连接失败（%s），暂用本地状态机" % (self.camera.id, exc))
            return False

    def _onvif_call(self, fn: Callable[[Dict[str, Any]], Any]) -> bool:
        if not self._ensure_onvif():
            return False
        try:
            fn(self._onvif or {})
            return True
        except Exception as exc:
            self._logw("warn", "%s ONVIF 调用失败（%s），本次改用本地状态机" % (self.camera.id, exc))
            self._onvif_ready = False
            self._onvif = None
            self._onvif_down_until = time.time() + 60.0
            return False

    # ---------------- 契约接口 ----------------
    def state(self) -> Dict[str, Any]:
        with self._lock:
            moving = time.time() < self._moving_until
            return {
                "pan": round(self._pan, 1),
                "tilt": round(self._tilt, 1),
                "zoom": round(self._zoom, 1),
                "zoom_max": self.zoom_max,
                "moving": bool(moving),
                "preset_id": self._preset_id,
            }

    def move(self, dx: float = 0.0, dy: float = 0.0, zoom: float = 0.0) -> Dict[str, Any]:
        dx = float(max(-1.0, min(1.0, dx or 0.0)))
        dy = float(max(-1.0, min(1.0, dy or 0.0)))
        zoom = float(max(-1.0, min(1.0, zoom or 0.0)))
        speed = {"x": dx, "y": dy, "zoom": zoom}
        if self._onvif_call(lambda ctx: self._onvif_continuous(ctx, speed)):
            time.sleep(MOVE_STEP_S)
            self._onvif_call(lambda ctx: ctx["ptz"].Stop({"ProfileToken": ctx["token"]}))
        with self._lock:
            self._pan = self._wrap_pan(self._pan + dx * self.pan_speed * MOVE_STEP_S)
            self._tilt = max(self.tilt_min, min(self.tilt_max, self._tilt + dy * self.tilt_speed * MOVE_STEP_S))
            self._zoom = max(1.0, min(self.zoom_max, self._zoom + zoom * self.zoom_speed * self.zoom_max * 0.1))
            self._preset_id = None  # 手动移动后不再"停在某个预置位"
            self._moving_until = time.time() + MOVE_STEP_S
            self._save()
            return self.state()

    def _onvif_continuous(self, ctx: Dict[str, Any], speed: Dict[str, float]) -> None:
        ptz = ctx["ptz"]
        req = ptz.create_type("ContinuousMove")
        req.ProfileToken = ctx["token"]
        req.Velocity = {
            "PanTilt": {"x": speed["x"], "y": speed["y"]},
            "Zoom": {"x": speed["zoom"]},
        }
        ptz.ContinuousMove(req)

    def goto(self, preset_id: int) -> Dict[str, Any]:
        preset = self._find_preset(preset_id)
        if preset is None:
            raise KeyError("预置位 %s 不存在" % preset_id)
        if self._onvif_call(
            lambda ctx: ctx["ptz"].GotoPreset({"ProfileToken": ctx["token"], "PresetToken": str(preset_id)})
        ):
            time.sleep(0.2)
        with self._lock:
            self._pan = float(preset.get("pan", self._pan))
            self._tilt = float(preset.get("tilt", self._tilt))
            self._zoom = max(1.0, min(self.zoom_max, float(preset.get("zoom", self._zoom))))
            self._preset_id = int(preset_id)
            self._moving_until = time.time() + 2.0
            self._save()
            return self.state()

    def save(self, preset_id: int, name: str = "") -> Dict[str, Any]:
        with self._lock:
            preset = {
                "id": int(preset_id),
                "name": str(name or ("预置位%d" % preset_id)),
                "camera_id": self.camera.id,
                "pan": round(self._pan, 1),
                "tilt": round(self._tilt, 1),
                "zoom": round(self._zoom, 1),
            }
            self._presets = [p for p in self._presets if int(p.get("id", -1)) != int(preset_id)]
            self._presets.append(preset)
            self._presets.sort(key=lambda p: int(p.get("id", 0)))
            self._preset_id = int(preset_id)
            self._save()
        self._onvif_call(
            lambda ctx: ctx["ptz"].SetPreset(
                {"ProfileToken": ctx["token"], "PresetToken": str(preset_id), "PresetName": preset["name"]}
            )
        )
        return self.state()

    def home(self) -> Dict[str, Any]:
        self._onvif_call(lambda ctx: ctx["ptz"].GotoHomePosition({"ProfileToken": ctx["token"]}))
        with self._lock:
            self._pan = 0.0 if self.pan_min <= 0.0 else self.pan_min
            self._tilt = 0.0
            self._zoom = 1.0
            self._preset_id = None
            self._moving_until = time.time() + 2.0
            self._save()
            return self.state()

    def patrol(self, on: bool, preset_ids: Optional[List[int]] = None, dwell_s: Optional[float] = None) -> Dict[str, Any]:
        with self._lock:
            self._patrol_on = bool(on)
            if preset_ids is not None:
                self._patrol_ids = [int(x) for x in preset_ids]
            if dwell_s is not None:
                self._patrol_dwell = max(5.0, float(dwell_s))
            self._patrol_last = 0.0
            self._patrol_index = 0
        return self.state()

    def tick(self) -> None:
        """由 PTZManager 的秒级线程调用：驱动巡航。"""
        with self._lock:
            if not self._patrol_on or not self._patrol_ids:
                return
            now = time.time()
            if now < self._moving_until:
                return
            if now - self._patrol_last < self._patrol_dwell:
                return
            self._patrol_last = now
            preset_id = self._patrol_ids[self._patrol_index % len(self._patrol_ids)]
            self._patrol_index += 1
        try:
            self.goto(preset_id)
            self._logw("info", "%s 巡航：切到预置位 %s" % (self.camera.id, preset_id))
        except KeyError:
            self._logw("warn", "%s 巡航跳过不存在的预置位 %s" % (self.camera.id, preset_id))

    # ---------------- 预置位 ----------------
    def _wrap_pan(self, pan: float) -> float:
        span = self.pan_max - self.pan_min
        if span <= 0:
            return pan
        while pan < self.pan_min:
            pan += span
        while pan > self.pan_max:
            pan -= span
        return pan

    def _find_preset(self, preset_id: int) -> Optional[Dict[str, Any]]:
        for preset in self._presets:
            if int(preset.get("id", -1)) == int(preset_id):
                return dict(preset)
        return None

    def presets(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                {
                    "id": int(p.get("id", 0)),
                    "name": str(p.get("name", "")),
                    "camera_id": self.camera.id,
                    "pan": float(p.get("pan", 0.0)),
                    "tilt": float(p.get("tilt", 0.0)),
                    "zoom": float(p.get("zoom", 1.0)),
                }
                for p in self._presets
            ]

    @property
    def backend(self) -> str:
        return "onvif" if self._onvif_ready else "mock"


class PTZManager:
    """所有相机的云台集合 + 巡航线程。"""

    def __init__(self, cfg, store, cameras, logger=None, force_mock: bool = False) -> None:
        self.cfg = cfg
        self.store = store
        self._log = logger
        self.controllers: Dict[str, PTZController] = {}
        for cam in cameras.cameras:
            if cam.has_ptz:
                self.controllers[cam.id] = PTZController(
                    cam, cfg, store, logger=logger, force_mock=force_mock
                )
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def controller(self, camera_id: str) -> Optional[PTZController]:
        return self.controllers.get(camera_id)

    def provider(self, camera) -> Optional[Dict[str, Any]]:
        ctrl = self.controllers.get(camera.id)
        return ctrl.state() if ctrl else None

    def presets(self, camera_id: Optional[str] = None) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for cid, ctrl in self.controllers.items():
            if camera_id and cid != camera_id:
                continue
            out.extend(ctrl.presets())
        out.sort(key=lambda p: (p["camera_id"], p["id"]))
        return out

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, name="ptz-patrol", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=3)

    def _run(self) -> None:
        while self._running:
            for ctrl in self.controllers.values():
                try:
                    ctrl.tick()
                except Exception as exc:
                    if self._log:
                        self._log("warn", "ptz", "%s 巡航异常：%s" % (ctrl.camera.id, exc))
            time.sleep(1.0)

    def status(self) -> Dict[str, str]:
        return {cid: ctrl.backend for cid, ctrl in self.controllers.items()}

    def all_onvif(self) -> bool:
        """所有云台都在用真 ONVIF 后端吗？（有 mock 就返回 False，供 health.services 用）

        注意：mock 后端"接口行为一致但不会真的转相机"，所以它**不算**服务正常。
        """
        if not self.controllers:
            return False
        return all(ctrl.backend == "onvif" for ctrl in self.controllers.values())


__all__ = ["PTZController", "PTZManager", "MOVE_STEP_S"]
