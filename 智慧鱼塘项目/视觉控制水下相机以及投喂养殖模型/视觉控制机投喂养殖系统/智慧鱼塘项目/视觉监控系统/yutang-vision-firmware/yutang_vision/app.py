"""HTTP 服务：实现契约全部端点 + SSE 推送 + 静态托管（标准库 http.server，无强制第三方依赖）。

线程模型（全部 daemon，进程退出即回收）：
    HTTP 处理线程（ThreadingHTTPServer，每个请求一条）
    采集线程       每台相机一条（camera.py）
    detector 线程  1 条，按 analysis.max_fps 轮询各相机最新帧
    看门狗线程     1 条，1 Hz：相机掉线/离线事件、健康指标采样、模拟剧本注入
    抓图线程       1 条，按 capture.interval_s 定时抓图
    清理线程       1 条，按 storage.cleanup_interval_s 清旧数据
    netmeter 线程  1 条，按 5 s 采样流量/信号
    巡航线程       1 条（onvif_ptz.py）

契约一致性：每个端点的字段名/类型/枚举都严格按《视觉系统_API契约_v1.md》实现
（对象层级不增不减；只在数组与响应层做了向后兼容的扩展，例如 health.services 多列了几个
服务、PUT /config 多回一个 config、多了 /api/v1 索引页，见 README §6）。
错误统一返回 {"ok": false, "error": "..."}（HTTP 4xx/5xx）。
"""

from __future__ import annotations

import json
import mimetypes
import os
import posixpath
import re
import socket
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, List, Optional

from . import __version__, degraded_notes
from .bus import Bus
from .camera import CameraManager, jpeg_dimensions
from .config import CONTRACT_KEYS, Config
from .detector import Detector
from .metrics import MetricsService, SystemSampler
from .netmeter import NetMeter
from .onvif_ptz import PTZManager
from .store import EVENT_TYPES, LOG_LEVELS, SNAPSHOT_TRIGGERS, Store

MAX_LIMIT = 2000
MAX_BODY_BYTES = 1024 * 1024


# ==========================================================================
# 运行期
# ==========================================================================
class Runtime:
    """把配置、存储、采集、检测、云台、指标、网络统计缝在一起。"""

    def __init__(self, cfg: Config, simulate: bool = False, force_ptz_mock: bool = False) -> None:
        self.cfg = cfg
        self.simulate = bool(simulate)
        self.mode = "mock" if simulate else "live"
        self.started_at = int(time.time())
        self.running = False
        self._lock = threading.RLock()
        data_dir = cfg.get("storage.data_dir", "data") or "data"
        if not os.path.isabs(data_dir):
            base = os.path.dirname(os.path.abspath(cfg.path)) if cfg.path else os.getcwd()
            data_dir = os.path.join(base, data_dir)
        self.data_dir = data_dir

        self.store = Store(data_dir, logger=self.log)
        self.bus = Bus(on_drop=self._on_bus_drop)
        self.cameras = CameraManager(cfg, self.store, logger=self.log, simulate=self.simulate)
        self.metrics = MetricsService(cfg, self.store, logger=self.log)
        self.detector = Detector(cfg, self.metrics, logger=self.log, simulate=self.simulate)
        self.ptz = PTZManager(cfg, self.store, self.cameras, logger=self.log, force_mock=force_ptz_mock)
        self.netmeter = NetMeter(cfg, self.store, logger=self.log)
        self.sysmon = SystemSampler(data_dir, logger=self.log)

        self._net: Dict[str, Any] = {
            "type": cfg.get("net.type", "4g"),
            "rssi_dbm": None,
            "carrier": cfg.get("net.carrier") or None,
            "uplink_kbps": None,
            "month_bytes": None,
            "month_quota_bytes": int(float(cfg.get("upload.quota_gb_month", 10) or 10) * (1024 ** 3)),
        }
        self._pi: Dict[str, Any] = {"cpu_pct": None, "mem_pct": None, "temp_c": None, "disk_free_gb": None}
        self._threads: List[threading.Thread] = []
        self._sim_phase: Dict[str, str] = {}
        self._detector_tick_at: float = 0.0
        self._last_cleanup: Dict[str, Any] = {}
        self._log_lines = 0
        self._alert_level = {"info": "info", "notice": "info", "warn": "warn", "critical": "error"}
        # 先采一次：CPU 需要两次采样才有差值，所以构造时先"打底"一次，
        # start() 里再采一次，这样第一个 /health 请求就有真实数字（不是 null）。
        try:
            self.sysmon.sample()
            self.netmeter.sample()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 日志
    # ------------------------------------------------------------------
    def log(self, level: str, src: str, msg: str) -> None:
        level = level if level in LOG_LEVELS else "info"
        if level != "debug":
            try:
                if getattr(self, "store", None) is not None:
                    self.store.add_log(int(time.time()), level, src, msg)
            except Exception:
                pass
        stamp = time.strftime("%H:%M:%S")
        try:
            print("[%s] %-5s %-12s %s" % (stamp, level.upper(), src, msg), flush=True)
        except Exception:
            pass

    def _on_bus_drop(self, sub, topic: str) -> None:
        self.log("warn", "sse", "SSE 订阅者 #%d 队列满（主题 %s），已丢弃最旧消息" % (sub.id, topic))

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------
    def start(self) -> None:
        if self.running:
            return
        self.running = True
        for note in degraded_notes():
            self.log("warn", "startup", "降级：%s —— %s" % (note["component"], note["reason"]))
        self.log(
            "info",
            "startup",
            "鱼塘视觉固件 v%s 启动，模式=%s，数据目录=%s" % (__version__, self.mode, self.data_dir),
        )
        self.metrics.preload([cam.id for cam in self.cameras.cameras])
        if self.simulate:
            from .simulate import backfill_history

            backfill_history(self.cfg, self.store, [cam.id for cam in self.cameras.cameras], logger=self.log)
            self.metrics.preload([cam.id for cam in self.cameras.cameras])
        try:
            self._pi = self.sysmon.sample()
            self._net = self.netmeter.sample()
        except Exception as exc:
            self.log("warn", "startup", "首次主机/网络采样失败：%s" % exc)
        self._warn_capacity()
        self.cameras.start()
        self.ptz.start()
        self._spawn("watchdog", self._watchdog_loop)
        self._spawn("detector", self._detector_loop)
        self._spawn("capture", self._capture_loop)
        self._spawn("cleanup", self._cleanup_loop)
        self._spawn("netmeter", self._netmeter_loop)

    def _warn_capacity(self) -> None:
        """开机算一笔账：按配置码率，录像保留天数需要多大盘？装不下就明确告警。

        这是现场最容易踩的坑：两路 4 Mbps 全码流 ≈ 88 GB/天，14 天要 1.2 TB，
        而 TF 卡通常只有 64~256 GB。宁可开机就吼一声，也不要等到卡写满才发现。
        """
        if not self.cfg.get("record.local_full_stream", True):
            return
        try:
            import shutil

            per_day = self.cameras.bytes_per_day()
            keep_days = int(self.cfg.get("record.keep_days", 14) or 14)
            need = per_day * keep_days
            total = shutil.disk_usage(self.data_dir).total
            if need > total * 0.8:
                self.log(
                    "warn",
                    "startup",
                    "容量告警：按配置码率估算录像 %d 天需要 %.0f GB，而数据盘只有 %.0f GB。"
                    "建议：调小 record.keep_days、改用子码流（rtsp_path=/Streaming/Channels/102）、"
                    "或关闭 record.local_full_stream 改用事件抓图"
                    % (keep_days, need / float(1024 ** 3), total / float(1024 ** 3)),
                )
        except Exception as exc:
            self.log("debug", "startup", "容量估算跳过：%s" % exc)

    def _spawn(self, name: str, target: Callable[[], None]) -> None:
        thread = threading.Thread(target=target, name=name, daemon=True)
        thread.start()
        self._threads.append(thread)

    def stop(self) -> None:
        if not self.running:
            return
        self.running = False
        self.log("info", "shutdown", "正在停止……")
        self.cameras.stop()
        self.ptz.stop()
        for thread in self._threads:
            thread.join(timeout=3)
        self.store.close()

    # ------------------------------------------------------------------
    # 事件
    # ------------------------------------------------------------------
    def emit_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """统一出口：抓图 -> 入库 -> 广播 -> 日志。"""
        ts = int(event.get("ts") or time.time())
        camera_id = str(event.get("camera_id") or "")
        camera = self.cameras.get(camera_id)
        snapshot_path: Optional[str] = None
        # 只在相机在线时抓图：离线事件本来就没画面，硬抓一次 ffmpeg 要等 8~15 s，
        # 会把看门狗/检测线程卡住（而且抓回来也是空）。前端拿不到事件图时，
        # store.event_snapshot_path() 会退回该相机最近一张，不会出现裂图。
        if camera is not None and camera.online and self.cfg.get("capture.on_event", True):
            data = camera.snapshot_jpeg(
                self.capture_width(), int(self.cfg.get("capture.jpeg_quality", 85) or 85)
            )
            if data:
                width, height = jpeg_dimensions(data)
                row = self.store.save_snapshot(ts, camera_id, data, "event", width, height)
                if row:
                    snapshot_path = row["path"]
        event = dict(event)
        if self.mode == "mock":
            # 诚实标记：mock 模式下的事件全部来自合成视频流/剧本，标题前缀 + detail 后缀，
            # 且不改动任何契约字段（title/detail 本来就是自由文本）。
            title = str(event.get("title") or "")
            if not title.startswith("[模拟]"):
                event["title"] = "[模拟] %s" % title
            detail = str(event.get("detail") or "")
            if "mock 数据" not in detail:
                event["detail"] = "%s（mock 数据：由合成视频流/剧本产生，非现场实测）" % detail
        event["snapshot_path"] = snapshot_path
        stored = self.store.add_event(event)
        self.bus.publish("event", stored)
        self.log(
            self._alert_level.get(str(stored.get("severity")), "info"),
            "detector",
            "事件 %s %s@%s：%s（confidence=%.2f, evidence=%s）"
            % (stored["id"], stored["type"], camera_id, stored["title"], stored["confidence"], stored["evidence"]),
        )
        return stored

    def capture_width(self) -> int:
        """抓图宽度：upload.policy=full 时返回 0（= 相机原始分辨率，不缩放）。

        thumbs_only / events_only 用 capture.max_width（默认 1920，4G 友好）。
        """
        policy = str(self.cfg.get("upload.policy", "thumbs_only"))
        if policy == "full":
            return 0
        return int(self.cfg.get("capture.max_width", 1920) or 1920)

    def feed_window_active(self, ts: Optional[int] = None) -> bool:
        ts = int(ts or time.time())
        local = time.localtime(ts)
        minutes = local.tm_hour * 60 + local.tm_min
        for window in self.cfg.get("feed_windows", []) or []:
            try:
                sh, sm = [int(x) for x in str(window["start"]).split(":")]
                eh, em = [int(x) for x in str(window["end"]).split(":")]
            except Exception:
                continue
            start, end = sh * 60 + sm, eh * 60 + em
            if start <= end:
                if start <= minutes <= end:
                    return True
            else:  # 跨零点
                if minutes >= start or minutes <= end:
                    return True
        return False

    # ------------------------------------------------------------------
    # 后台线程
    # ------------------------------------------------------------------
    def _watchdog_loop(self) -> None:
        """1 Hz：相机掉线看护 + 离线事件 + 健康采样 + 模拟剧本注入。"""
        last_health = 0.0
        stall_s = float(self.cfg.get("detector.stall_after_s", 6) or 6)
        offline_after = float(self.cfg.get("detector.offline_after_s", 30) or 30)
        while self.running:
            now = time.time()
            try:
                for cam in self.cameras.cameras:
                    # 视频流卡住（ffmpeg 挂着不出帧）
                    if cam.online and cam.last_ok_ts and (now - cam.last_ok_ts) > stall_s:
                        cam._mark_stalled()
                    if cam.online:
                        continue
                    # 连续失败 ≥ offline_after_s -> 发一次 offline 事件
                    down_since = cam.down_since
                    if down_since is None:
                        continue
                    down_s = int(now - down_since)
                    if down_s >= offline_after and not cam._offline_event_sent:
                        cam._offline_event_sent = True
                        # 模拟模式也走这条真实路径（不是"假装发一条"）
                        self.emit_event(
                            self.detector.offline_event(
                                cam.id, down_s, max(1, cam.failures), ts=int(now), name=cam.name
                            )
                        )
                if self.simulate:
                    self._simulate_tick()
                if now - last_health >= 5.0:
                    last_health = now
                    self._pi = self.sysmon.sample()
            except Exception as exc:
                self.log("warn", "watchdog", "看门狗异常：%s" % exc)
            time.sleep(1.0)

    def _simulate_tick(self) -> None:
        """模拟模式：进入 person 阶段时注入一条剧本事件（其余类型由真检测器产出）。"""
        for cam in self.cameras.cameras:
            source = getattr(cam, "_sim_source", None)
            if source is None:
                continue
            phase = source.scenario.phase()
            if self._sim_phase.get(cam.id) == phase:
                continue
            self._sim_phase[cam.id] = phase
            event = source.injected_event(phase)
            if event:
                self.emit_event(event)

    def _detector_loop(self) -> None:
        max_fps = float(self.cfg.get("analysis.max_fps", 5) or 5)
        interval = 1.0 / max(0.5, max_fps)
        last_seq: Dict[str, int] = {}
        while self.running:
            started = time.time()
            self._detector_tick_at = started
            try:
                active = self.feed_window_active()
                for cam in self.cameras.cameras:
                    frame = cam.latest()
                    if frame is None:
                        continue
                    if last_seq.get(cam.id) == frame.seq:
                        continue
                    last_seq[cam.id] = frame.seq
                    if time.time() - frame.ts > 10:
                        continue  # 陈旧帧不参与检测
                    events = self.detector.process(
                        cam.id, frame, cam.cam.get("analysis") or {}, feed_window_active=active
                    )
                    for event in events:
                        self.emit_event(event)
            except Exception as exc:
                import traceback

                self.log("warn", "detector", "检测循环异常：%s" % exc)
                self.log("debug", "detector", traceback.format_exc().replace("\n", " | "))
            elapsed = time.time() - started
            time.sleep(max(0.02, interval - elapsed))

    def _capture_loop(self) -> None:
        """定时抓图：落盘 + 记 snapshots 表（trigger=interval）。"""
        next_at: Dict[str, float] = {}
        while self.running:
            try:
                interval = float(self.cfg.get("capture.interval_s", 60) or 60)
                policy = str(self.cfg.get("upload.policy", "thumbs_only"))
                if policy == "events_only":
                    time.sleep(2.0)
                    continue
                now = time.time()
                for idx, cam in enumerate(self.cameras.cameras):
                    due = next_at.get(cam.id)
                    if due is None:
                        next_at[cam.id] = now + 2.0 + idx * 2.0  # 错开抓图时刻，避免同一秒撞车
                        continue
                    if now < due:
                        continue
                    next_at[cam.id] = now + interval
                    if not cam.online:
                        continue
                    data = cam.snapshot_jpeg(
                        self.capture_width(), int(self.cfg.get("capture.jpeg_quality", 85) or 85)
                    )
                    if not data:
                        continue
                    ts = int(time.time())
                    width, height = jpeg_dimensions(data)
                    self.store.save_snapshot(ts, cam.id, data, "interval", width, height)
            except Exception as exc:
                self.log("warn", "capture", "定时抓图异常：%s" % exc)
            time.sleep(0.5)

    def _cleanup_loop(self) -> None:
        while self.running:
            try:
                summary = self.store.cleanup(
                    snapshot_keep_days=int(self.cfg.get("storage.snapshot_keep_days", 14) or 14),
                    events_keep_days=int(self.cfg.get("storage.events_keep_days", 90) or 90),
                    logs_keep_days=int(self.cfg.get("storage.logs_keep_days", 14) or 14),
                    metrics_keep_days=int(self.cfg.get("metrics.keep_days", 30) or 30),
                    min_free_gb=float(self.cfg.get("storage.min_free_gb", 3.0) or 3.0),
                    recordings_keep_days=int(self.cfg.get("record.keep_days", 14) or 14),
                    recording_dirs=[os.path.join(self.store.recording_dir, c.id) for c in self.cameras.cameras],
                )
                self._last_cleanup = summary
                if any(
                    summary.get(k)
                    for k in ("deleted_events", "deleted_logs", "deleted_metrics", "deleted_snapshots", "deleted_recordings")
                ):
                    self.log(
                        "info",
                        "cleanup",
                        "清理完成：事件 %d / 日志 %d / 指标 %d / 抓图 %d / 录像 %d，剩余磁盘 %.2f GB"
                        % (
                            summary["deleted_events"],
                            summary["deleted_logs"],
                            summary["deleted_metrics"],
                            summary["deleted_snapshots"],
                            summary["deleted_recordings"],
                            summary["free_gb"],
                        ),
                    )
            except Exception as exc:
                self.log("warn", "cleanup", "清理异常：%s" % exc)
            time.sleep(max(10.0, float(self.cfg.get("storage.cleanup_interval_s", 60) or 60)))

    def _netmeter_loop(self) -> None:
        while self.running:
            try:
                self._net = self.netmeter.sample()
                self._net["month_quota_bytes"] = int(
                    float(self.cfg.get("upload.quota_gb_month", 10) or 10) * (1024 ** 3)
                )
                self._net["type"] = self.cfg.get("net.type", "4g")
            except Exception as exc:
                self.log("warn", "netmeter", "采样异常：%s" % exc)
            time.sleep(5.0)

    # ------------------------------------------------------------------
    # 契约响应拼装
    # ------------------------------------------------------------------
    def health(self) -> Dict[str, Any]:
        recording = bool(self.cfg.get("record.local_full_stream", True))
        recorders_ok = self.cameras.recording()
        # recording 一律表示"**此刻真的在往卡里写**"：mock 模式没有真流可录 -> false；
        # live 模式下相机连不上、ffmpeg 写不出分段 -> 也是 false。
        # （"打算录"看 /api/v1/config 的 record.local_full_stream，别混为一谈。）
        storage = {
            "recording": bool(recording and recorders_ok),
            "days_kept": int(self.cfg.get("record.keep_days", 14) or 14),
            "bytes_per_day": self.cameras.bytes_per_day(),
        }
        # 每一项都要求是"真的在干活"，不是"配置里写了"：
        #   rtsp-ingest：至少一路相机出帧
        #   detector   ：检测线程有心跳（超过 10 s 没跑就是卡死）
        #   store      ：SQLite 还能查
        #   recorder   ：ffmpeg 真的写出了分段文件
        #   ptz        ：云台后端是不是真的 ONVIF（mock 状态机不算"真控制"）
        now = time.time()
        frames_ok = any(c.online for c in self.cameras.cameras) if self.cameras.cameras else False
        detector_ok = bool(self._detector_tick_at) and (now - self._detector_tick_at) < 10.0
        try:
            self.store.list_logs(limit=1)
            store_ok = True
        except Exception:
            store_ok = False
        services = [
            {"name": "rtsp-ingest", "ok": frames_ok},
            {"name": "detector", "ok": detector_ok},
            {"name": "store", "ok": store_ok},
            {"name": "recorder", "ok": bool(recorders_ok)},
            {"name": "netmeter", "ok": self._net.get("uplink_kbps") is not None},
        ]
        if self.ptz.controllers:
            services.append({"name": "ptz", "ok": self.ptz.all_onvif()})
        # 降级项一律并入，并且**覆盖**同名服务项：能力降级了就不许显示 ok=true
        index = {item["name"]: item for item in services}
        for note in degraded_notes():
            name = note["component"]
            if name in index:
                index[name]["ok"] = False
            else:
                item = {"name": name, "ok": False}
                services.append(item)
                index[name] = item
        return {
            "ok": True,
            "version": __version__,
            "uptime_s": int(time.time()) - self.started_at,
            "mode": self.mode,
            "pi": dict(self._pi),
            "net": dict(self._net),
            "storage": storage,
            "services": services,
        }

    def cameras_json(self) -> List[Dict[str, Any]]:
        return self.cameras.json(ptz_provider=self.ptz.provider)

    def default_camera_id(self) -> Optional[str]:
        for cam in self.cameras.cameras:
            if cam.role == "panorama":
                return cam.id
        return self.cameras.cameras[0].id if self.cameras.cameras else None


# ==========================================================================
# HTTP 处理
# ==========================================================================
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "yutang-vision/%s" % __version__
    runtime: Runtime  # 由 make_server 注入

    # ---------------- 基础 ----------------
    def log_message(self, fmt: str, *args: Any) -> None:
        try:
            self.runtime.log("debug", "http", "%s %s" % (self.address_string(), fmt % args))
        except Exception:
            pass

    def _cors(self) -> None:
        if self.runtime.cfg.get("server.cors", True):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send(self, status: int, body: bytes, ctype: str, extra: Optional[Dict[str, str]] = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

    def _json(self, obj: Any, status: int = 200) -> None:
        body = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _error(self, status: int, message: str) -> None:
        self._json({"ok": False, "error": message}, status=status)

    def _query(self) -> Dict[str, str]:
        parsed = urllib.parse.urlparse(self.path)
        raw = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        return {k: v[0] for k, v in raw.items()}

    def _path(self) -> str:
        return urllib.parse.urlparse(self.path).path

    def _int_param(self, params: Dict[str, str], name: str, default: Optional[int], lo: int, hi: int) -> Optional[int]:
        if name not in params or params[name] == "":
            return default
        try:
            value = int(float(params[name]))
        except Exception:
            return default
        return max(lo, min(hi, value))

    def _read_body(self) -> Optional[Dict[str, Any]]:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except Exception:
            length = 0
        if length <= 0:
            return {}
        if length > MAX_BODY_BYTES:
            return None
        try:
            raw = self.rfile.read(length)
            data = json.loads(raw.decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return None

    # ---------------- 方法分发 ----------------
    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self._cors()
        self.end_headers()

    def do_HEAD(self) -> None:  # noqa: N802
        self.do_GET()

    def do_GET(self) -> None:  # noqa: N802
        try:
            self._route_get()
        except BrokenPipeError:
            pass
        except Exception as exc:
            self.runtime.log("error", "http", "GET %s 异常：%s" % (self.path, exc))
            try:
                self._error(500, "内部错误：%s" % exc)
            except Exception:
                pass

    def do_POST(self) -> None:  # noqa: N802
        try:
            self._route_post()
        except Exception as exc:
            self.runtime.log("error", "http", "POST %s 异常：%s" % (self.path, exc))
            try:
                self._error(500, "内部错误：%s" % exc)
            except Exception:
                pass

    def do_PUT(self) -> None:  # noqa: N802
        try:
            self._route_put()
        except Exception as exc:
            self.runtime.log("error", "http", "PUT %s 异常：%s" % (self.path, exc))
            try:
                self._error(500, "内部错误：%s" % exc)
            except Exception:
                pass

    # ---------------- GET 路由 ----------------
    def _route_get(self) -> None:
        rt = self.runtime
        path = self._path()
        params = self._query()

        if path in ("/", "/index.html"):
            return self._serve_index()

        if path == "/api/v1/health":
            return self._json(rt.health())

        if path == "/api/v1/cameras":
            return self._json(rt.cameras_json())

        match = re.match(r"^/api/v1/cameras/([^/]+)/snapshot$", path)
        if match:
            return self._camera_snapshot(urllib.parse.unquote(match.group(1)), params)

        if path == "/api/v1/presets":
            camera_id = params.get("camera_id") or None
            if camera_id and not rt.cameras.get(camera_id):
                return self._error(404, "相机 %s 不存在" % camera_id)
            return self._json(rt.ptz.presets(camera_id))

        if path == "/api/v1/events":
            limit = self._int_param(params, "limit", 200, 1, MAX_LIMIT) or 200
            since = self._int_param(params, "since", None, 0, 2 ** 40)
            type_ = params.get("type") or None
            if type_ and type_ not in EVENT_TYPES:
                return self._error(400, "未知事件类型 %s（可选：%s）" % (type_, "/".join(EVENT_TYPES)))
            camera_id = params.get("camera_id") or None
            unacked = str(params.get("acked", "")).lower() in ("0", "false")
            return self._json(
                rt.store.list_events(since=since, type_=type_, camera_id=camera_id, limit=limit, unacked_only=unacked)
            )

        match = re.match(r"^/api/v1/events/([^/]+)/snapshot$", path)
        if match:
            return self._event_snapshot(urllib.parse.unquote(match.group(1)))

        match = re.match(r"^/api/v1/events/([^/]+)/clip$", path)
        if match:
            return self._event_clip(urllib.parse.unquote(match.group(1)))

        if path == "/api/v1/stream/events":
            return self._sse()

        if path == "/api/v1/metrics/splash":
            camera_id = params.get("camera_id") or rt.default_camera_id()
            if not camera_id:
                return self._error(404, "没有配置任何相机")
            if not rt.cameras.get(camera_id):
                return self._error(404, "相机 %s 不存在" % camera_id)
            window = params.get("window") or str(rt.cfg.get("metrics.default_window", "24h"))
            step = self._int_param(params, "step", int(rt.cfg.get("metrics.default_step", 300) or 300), 5, 86400)
            limit = self._int_param(params, "limit", None, 1, MAX_LIMIT)
            return self._json(rt.metrics.series(camera_id, window=window, step=step or 300, limit=limit))

        if path == "/api/v1/snapshots":
            limit = self._int_param(params, "limit", 500, 1, MAX_LIMIT) or 500
            trigger = params.get("trigger") or None
            if trigger and trigger not in SNAPSHOT_TRIGGERS:
                return self._error(400, "未知 trigger %s（可选：%s）" % (trigger, "/".join(SNAPSHOT_TRIGGERS)))
            return self._json(
                rt.store.list_snapshots(
                    date=params.get("date") or None,
                    camera_id=params.get("camera_id") or None,
                    limit=limit,
                    trigger=trigger,
                )
            )

        match = re.match(r"^/api/v1/snapshots/(\d+)(?:[-_]([A-Za-z0-9\-_]+))?\.jpg$", path)
        if match:
            ts = int(match.group(1))
            camera_id = match.group(2) or params.get("camera_id") or None
            file_path = rt.store.snapshot_path_by_ts(ts, camera_id)
            if not file_path:
                return self._error(404, "抓图不存在：ts=%d" % ts)
            return self._serve_file(file_path, "image/jpeg")

        if path == "/api/v1/config":
            return self._json(rt.cfg.public())

        if path == "/api/v1/logs":
            limit = self._int_param(params, "limit", 200, 1, MAX_LIMIT) or 200
            since = self._int_param(params, "since", None, 0, 2 ** 40)
            level = params.get("level") or None
            if level and level not in LOG_LEVELS:
                return self._error(400, "未知日志级别 %s（可选：%s）" % (level, "/".join(LOG_LEVELS)))
            return self._json(rt.store.list_logs(limit=limit, since=since, level=level))

        if path == "/api/v1":
            return self._json(
                {
                    "ok": True,
                    "version": __version__,
                    "mode": rt.mode,
                    "endpoints": [
                        "GET /api/v1/health",
                        "GET /api/v1/cameras",
                        "GET /api/v1/cameras/{id}/snapshot",
                        "POST /api/v1/cameras/{id}/ptz",
                        "GET /api/v1/presets",
                        "GET /api/v1/events",
                        "POST /api/v1/events/{id}/ack",
                        "GET /api/v1/events/{id}/snapshot",
                        "GET /api/v1/events/{id}/clip",
                        "GET /api/v1/stream/events",
                        "GET /api/v1/metrics/splash",
                        "GET /api/v1/snapshots",
                        "GET /api/v1/snapshots/{ts}.jpg",
                        "GET|PUT /api/v1/config",
                        "GET /api/v1/logs",
                    ],
                }
            )

        if path.startswith("/api/"):
            return self._error(404, "未知端点 %s" % path)
        return self._serve_static(path)

    # ---------------- POST 路由 ----------------
    def _route_post(self) -> None:
        rt = self.runtime
        path = self._path()
        match = re.match(r"^/api/v1/cameras/([^/]+)/ptz$", path)
        if match:
            return self._ptz(urllib.parse.unquote(match.group(1)))
        match = re.match(r"^/api/v1/events/([^/]+)/ack$", path)
        if match:
            event_id = urllib.parse.unquote(match.group(1))
            if rt.store.get_event(event_id) is None:
                return self._error(404, "事件 %s 不存在" % event_id)
            rt.store.ack_event(event_id)
            return self._json({"ok": True})
        return self._error(404, "未知端点 %s" % path)

    # ---------------- PUT 路由 ----------------
    def _route_put(self) -> None:
        rt = self.runtime
        path = self._path()
        if path != "/api/v1/config":
            return self._error(404, "未知端点 %s" % path)
        body = self._read_body()
        if body is None:
            return self._error(400, "请求体必须是合法 JSON 对象（且 < 1 MB）")
        if not body:
            return self._error(400, "请求体不能为空；允许的键：%s" % "/".join(CONTRACT_KEYS))
        ok, errors = rt.cfg.update(body)
        if not ok:
            return self._error(400, "；".join(errors))
        rt.log("info", "config", "配置已更新并落盘：%s" % "/".join(sorted(body.keys())))
        return self._json({"ok": True, "config": rt.cfg.public()})

    # ---------------- 各端点实现 ----------------
    def _camera_snapshot(self, camera_id: str, params: Dict[str, str]) -> None:
        rt = self.runtime
        camera = rt.cameras.get(camera_id)
        if camera is None:
            return self._error(404, "相机 %s 不存在" % camera_id)
        width = self._int_param(params, "w", rt.capture_width() or 7680, 64, 7680)
        quality = self._int_param(params, "q", int(rt.cfg.get("capture.jpeg_quality", 85) or 85), 1, 100)
        data = camera.snapshot_jpeg(width or 1920, quality or 85)
        if not data:
            return self._error(503, "相机 %s 当前取不到画面（online=%s）" % (camera_id, camera.online))
        if str(params.get("save", "")) in ("1", "true", "yes"):
            w, h = jpeg_dimensions(data)
            rt.store.save_snapshot(int(time.time()), camera_id, data, "manual", w, h)
        self._send(
            200,
            data,
            "image/jpeg",
            extra={"X-Camera-Online": "1" if camera.online else "0", "X-Snapshot-Mode": rt.mode},
        )

    def _event_snapshot(self, event_id: str) -> None:
        rt = self.runtime
        if rt.store.get_event(event_id) is None:
            return self._error(404, "事件 %s 不存在" % event_id)
        file_path = rt.store.event_snapshot_path(event_id)
        if not file_path:
            return self._error(404, "事件 %s 没有可用抓图（离线事件且无历史帧）" % event_id)
        return self._serve_file(file_path, "image/jpeg")

    def _event_clip(self, event_id: str) -> None:
        rt = self.runtime
        if rt.store.get_event(event_id) is None:
            return self._error(404, "事件 %s 不存在" % event_id)
        file_path = rt.store.event_clip_path(event_id)
        if not file_path:
            return self._error(
                404,
                "该事件没有切片文件；4G 下建议只用 /snapshot（契约 §3 说明 clip 为可选）",
            )
        return self._serve_file(file_path, "video/mp4")

    def _ptz(self, camera_id: str) -> None:
        rt = self.runtime
        camera = rt.cameras.get(camera_id)
        if camera is None:
            return self._error(404, "相机 %s 不存在" % camera_id)
        controller = rt.ptz.controller(camera_id)
        if controller is None:
            return self._error(400, "相机 %s 没有云台（配置里 ptz 为空）" % camera_id)
        body = self._read_body()
        if body is None:
            return self._error(400, "请求体必须是合法 JSON 对象")
        action = body.get("action")
        try:
            if action == "move":
                state = controller.move(
                    float(body.get("dx") or 0.0), float(body.get("dy") or 0.0), float(body.get("zoom") or 0.0)
                )
            elif action == "goto":
                if "preset_id" not in body:
                    return self._error(400, "action=goto 需要 preset_id")
                state = controller.goto(int(body["preset_id"]))
            elif action == "save":
                if "preset_id" not in body:
                    return self._error(400, "action=save 需要 preset_id")
                state = controller.save(int(body["preset_id"]), str(body.get("name") or ""))
            elif action == "home":
                state = controller.home()
            elif action == "patrol":
                state = controller.patrol(
                    bool(body.get("on")),
                    [int(x) for x in (body.get("preset_ids") or [])] or None,
                    float(body["dwell_s"]) if body.get("dwell_s") is not None else None,
                )
            else:
                return self._error(
                    400, "未知 action %r（可选：move/goto/save/home/patrol）" % (action,)
                )
        except KeyError as exc:
            return self._error(404, str(exc))
        except (TypeError, ValueError) as exc:
            return self._error(400, "参数错误：%s" % exc)
        rt.log("info", "ptz", "%s action=%s -> pan=%.1f tilt=%.1f zoom=%.1f" % (
            camera_id, action, state["pan"], state["tilt"], state["zoom"]))
        return self._json({"ok": True, "ptz": state})

    # ---------------- SSE ----------------
    def _sse(self) -> None:
        rt = self.runtime
        heartbeat = float(rt.cfg.get("server.sse_heartbeat_s", 15) or 15)
        sub = rt.bus.subscribe(["event"], maxsize=256)
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-transform")
            self.send_header("Connection", "close")
            self.send_header("X-Accel-Buffering", "no")
            self._cors()
            self.end_headers()
            self.close_connection = True
            self._sse_write(": connected %d\n\n" % int(time.time()))
            while rt.running:
                message = sub.get(timeout=heartbeat)
                if message is None:
                    self._sse_write(": hb %d\n\n" % int(time.time()))
                    continue
                payload = json.dumps(message["data"], ensure_ascii=False, separators=(",", ":"))
                self._sse_write("event: event\ndata: %s\n\n" % payload)
        except (BrokenPipeError, ConnectionResetError, socket.error):
            pass
        finally:
            rt.bus.unsubscribe(sub)
            rt.log("debug", "sse", "SSE 连接断开（订阅者 #%d，丢弃 %d 条）" % (sub.id, sub.dropped))

    def _sse_write(self, text: str) -> None:
        self.wfile.write(text.encode("utf-8"))
        self.wfile.flush()

    # ---------------- 静态托管 ----------------
    def _static_dir(self) -> Optional[str]:
        rt = self.runtime
        configured = str(rt.cfg.get("server.static_dir") or "")
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = []
        if configured:
            candidates.append(configured if os.path.isabs(configured) else os.path.join(root, configured))
        parent = os.path.dirname(root)
        candidates += [
            os.path.join(parent, "yutang-vision-console"),
            os.path.join(parent, "yutang-vision-console", "dist"),
            os.path.join(root, "static"),
            os.path.join(os.getcwd(), "static"),
        ]
        for path in candidates:
            if path and os.path.isdir(path) and (
                os.path.exists(os.path.join(path, "index.html")) or os.listdir(path)
            ):
                return path
        return None

    def _serve_index(self) -> None:
        folder = self._static_dir()
        if folder:
            index = os.path.join(folder, "index.html")
            if os.path.exists(index):
                return self._serve_file(index, "text/html; charset=utf-8")
        body = FALLBACK_INDEX.format(
            version=__version__,
            mode=self.runtime.mode,
            static_hint=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ).encode("utf-8")
        self._send(200, body, "text/html; charset=utf-8")

    def _serve_static(self, path: str) -> None:
        folder = self._static_dir()
        if not folder:
            return self._error(404, "静态目录未找到，且路径 %s 不是 API 端点" % path)
        relative = posixpath.normpath(urllib.parse.unquote(path)).lstrip("/")
        target = os.path.realpath(os.path.join(folder, relative))
        if not target.startswith(os.path.realpath(folder)):
            return self._error(403, "路径越界")
        if os.path.isdir(target):
            target = os.path.join(target, "index.html")
        if not os.path.isfile(target):
            return self._error(404, "文件不存在：%s" % relative)
        ctype = mimetypes.guess_type(target)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        return self._serve_file(target, ctype)

    def _serve_file(self, file_path: str, ctype: str) -> None:
        try:
            with open(file_path, "rb") as fh:
                data = fh.read()
        except Exception as exc:
            return self._error(500, "读取文件失败：%s" % exc)
        self._send(200, data, ctype)


FALLBACK_INDEX = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>鱼塘视觉监控 · 固件自检页</title>
<style>
 body{{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;margin:2rem;line-height:1.6;color:#123}}
 code,pre{{background:#f4f6f8;padding:.15rem .35rem;border-radius:4px}}
 .box{{max-width:52rem;margin:auto}} .tag{{background:#e8f3ff;color:#06c;border-radius:4px;padding:.1rem .4rem;font-size:.85em}}
 li{{margin:.25rem 0}} a{{color:#06c}}
</style></head><body><div class="box">
<h1>鱼塘视觉监控 · 固件已运行 <span class="tag">v{version} · mode={mode}</span></h1>
<p>这是固件内置的兜底页面：<b>没有找到网页端静态目录</b>（index.html）。
把前端产物放到 <code>{static_hint}/../yutang-vision-console/</code>，
或在配置里设置 <code>server.static_dir</code>，刷新本页即可看到正式界面。</p>
<h2>接口自检</h2>
<ul>
<li><a href="/api/v1/health">/api/v1/health</a> — 健康与状态（CPU/内存/温度/磁盘、4G 流量、服务列表）</li>
<li><a href="/api/v1/cameras">/api/v1/cameras</a> — 相机列表（online / ptz 状态）</li>
<li><a href="/api/v1/events?limit=20">/api/v1/events?limit=20</a> — 最近事件</li>
<li><a href="/api/v1/metrics/splash?window=24h&amp;step=300">/api/v1/metrics/splash</a> — V-Value 曲线</li>
<li><a href="/api/v1/snapshots?limit=20">/api/v1/snapshots?limit=20</a> — 抓图墙</li>
<li><a href="/api/v1/config">/api/v1/config</a> — 配置（PUT 可改）</li>
<li><a href="/api/v1/logs?limit=50">/api/v1/logs?limit=50</a> — 日志</li>
<li><a href="/api/v1/stream/events">/api/v1/stream/events</a> — SSE 实时事件流</li>
</ul>
<p>注意：mock 模式（<code>--simulate</code>）下的事件是**假数据**，仅供前端联调；
能力边界见 README「明确不做」一节（不数鱼、不数饲料、不估重、不反演生物量）。</p>
</div></body></html>
"""


# ==========================================================================
# 服务器
# ==========================================================================
def make_server(runtime: Runtime, host: str, port: int) -> ThreadingHTTPServer:
    handler = type("BoundHandler", (Handler,), {"runtime": runtime})
    server = ThreadingHTTPServer((host, port), handler)
    server.daemon_threads = True
    server.allow_reuse_address = True
    return server


def serve(runtime: Runtime, host: Optional[str] = None, port: Optional[int] = None) -> None:
    """阻塞式启动（__main__ 用）。"""
    host = host or str(runtime.cfg.get("server.host", "0.0.0.0") or "0.0.0.0")
    port = int(port or runtime.cfg.get("server.port", 8080) or 8080)
    server = make_server(runtime, host, port)
    runtime.log("info", "http", "监听 http://%s:%d （局域网内用树莓派 IP 访问）" % (host, port))
    try:
        server.serve_forever(poll_interval=0.5)
    finally:
        runtime.log("info", "http", "HTTP 服务停止")
        server.server_close()


__all__ = ["Runtime", "Handler", "make_server", "serve", "MAX_LIMIT", "MAX_BODY_BYTES"]
