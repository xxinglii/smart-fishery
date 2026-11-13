"""无相机也能跑：合规的假数据流（供前端联调）。

`--simulate` 模式下，本模块提供：

1. **合成视频帧**（`SimSource`）：不做"假事件"，而是真的生成一段灰度视频流，
   交给真的检测器跑。除了人形之外，splash / aggregation / tamper / motion 四类事件
   都是检测器在合成画面上**真实算出来的**；offline 由真的看门狗按 30 s 规则发。
2. **剧本（scenario）**：按时间轮转 idle → splash → aggregation → person → tamper → offline，
   保证前端在 ~3 分钟内能看到全部 5 类事件。
   其中 `person` 是**剧本直接注入**的：OpenCV HOG 对合成剪影基本检不出，
   与其假装"检测到了"，不如明说这是注入的演示事件（detail 里带"[模拟]"前缀）。
3. **历史指标回填**（`backfill_history`）：给曲线端点造 24 h 的历史 V-Value，
   否则前端刚起来只能看到一条几个点的线。仅在 --simulate 且指标表为空时执行。

`health.mode` 在模拟模式下返回 `"mock"`，前端能一眼看出这是假数据。
"""

from __future__ import annotations

import math
import random
import time
from typing import Any, Dict, List, Optional, Tuple

from . import EVIDENCE_LEVEL, has, note_degraded
from .camera import Frame

#: 剧本阶段顺序（第一个 splash 放在最前，保证 20 s 内就有事件可看）
PHASE_ORDER: Tuple[str, ...] = ("splash", "aggregation", "person", "tamper", "offline", "idle")


class SimScenario:
    """按 wall-clock 推进的剧本。"""

    def __init__(self, camera_id: str, sim_cfg: Dict[str, Any]) -> None:
        self.camera_id = camera_id
        self.phase_s = dict(sim_cfg.get("phase_s") or {})
        self.first_event_s = float(sim_cfg.get("first_event_s", 8) or 8)
        self.offline_camera = str(sim_cfg.get("offline_camera") or "")
        self.order = [p for p in PHASE_ORDER if float(self.phase_s.get(p, 0) or 0) > 0]
        if not self.order:
            self.order = ["idle"]
        self.t0 = time.time()

    def _durations(self) -> List[Tuple[str, float, float]]:
        """返回 [(phase, start, end)]，从 first_event_s 开始排。"""
        spans: List[Tuple[str, float, float]] = []
        cursor = self.first_event_s
        for phase in self.order:
            duration = float(self.phase_s.get(phase, 20) or 20)
            spans.append((phase, cursor, cursor + duration))
            cursor += duration
        return spans

    @property
    def cycle_s(self) -> float:
        spans = self._durations()
        return spans[-1][2] if spans else 60.0

    def elapsed(self) -> float:
        return time.time() - self.t0

    def phase(self) -> str:
        """当前阶段名（first_event_s 之前是 idle 预热）。"""
        elapsed = self.elapsed()
        for phase, start, end in self._durations():
            if start <= elapsed < end:
                return phase
        return "idle"

    def cycle_index(self) -> int:
        return int(self.elapsed() // max(1.0, self.cycle_s))

    def camera_offline(self) -> bool:
        """当前是不是"本相机应当掉线"的阶段。"""
        if self.offline_camera and self.offline_camera != self.camera_id:
            return False
        return self.phase() == "offline"


# ==========================================================================
# 帧渲染
# ==========================================================================
class _NumpyRenderer:
    """numpy 版渲染器：背景 + 会动的亮斑（可控运动量）+ 暗斑/人形/亮度突变。"""

    def __init__(self, w: int, h: int, seed: int) -> None:
        import numpy as np  # type: ignore

        self.np = np
        self.w, self.h = w, h
        self.rng = np.random.default_rng(seed)
        ys = np.arange(h, dtype="float32")[:, None]
        xs = np.arange(w, dtype="float32")[None, :]
        # 水面底色：缓变 + 轻微纹理
        self.base = 96.0 + 14.0 * np.sin(xs / 41.0) + 9.0 * np.cos(ys / 27.0)
        self.base = self.base + 6.0 * np.sin((xs + ys) / 13.0)

    def render(self, t: float, phase: str) -> bytes:
        np = self.np
        frame = self.base.copy()
        density = 0.0018  # 静水期亮斑密度（≈1.5% 运动像素）
        jitter = 1.0
        if phase == "splash":
            density = 0.016
            jitter = 4.0
        elif phase in ("person", "tamper"):
            density = 0.004
            jitter = 2.0
        count = max(4, int(self.w * self.h * density))
        xs = self.rng.integers(0, self.w, size=count)
        ys = self.rng.integers(0, self.h, size=count)
        # 每帧随机位移 -> 亮的"水花点"在动
        dx = self.rng.integers(-int(jitter), int(jitter) + 1, size=count)
        dy = self.rng.integers(-int(jitter), int(jitter) + 1, size=count)
        xs = (xs + dx) % self.w
        ys = (ys + dy) % self.h
        gain = 62.0 if phase == "splash" else 46.0
        flat = frame.reshape(-1)
        idx = ys * self.w + xs
        flat[idx] = np.minimum(255.0, flat[idx] + gain)
        # 亮斑点半径 1 的十字，制造"块状"变化而不是孤立噪点
        for shift in (1, -1, self.w, -self.w):
            flat[(idx + shift) % flat.size] = np.minimum(255.0, flat[(idx + shift) % flat.size] + gain * 0.5)

        if phase == "aggregation":
            # 大面积暗斑（浮头/聚集的粗略代理）
            cy, cx = self.h * 0.55, self.w * 0.5
            ry, rx = self.h * 0.22, self.w * 0.26
            yy = np.arange(self.h, dtype="float32")[:, None]
            xx = np.arange(self.w, dtype="float32")[None, :]
            mask = (((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2) <= 1.0
            frame = np.where(mask, 14.0, frame)
        if phase == "person":
            x0 = int(self.w * 0.10)
            y0 = int(self.h * 0.18)
            # 人形剪影控制在 <3% 面积：避免顺带触发 surface_aggregation（阈值 4%）
            bw, bh = max(6, int(self.w * 0.075)), max(16, int(self.h * 0.35))
            frame[y0 : y0 + bh, x0 : x0 + bw] = 24.0
            head = max(3, bw // 2)
            frame[max(0, y0 - head) : y0, x0 : x0 + bw] = 30.0
        if phase == "tamper":
            frame = np.clip(frame + 70.0, 0, 255)  # 亮度突变 -> 真检测器会报 tamper
        noise = self.rng.normal(0.0, 2.5, size=frame.shape)
        frame = np.clip(frame + noise, 0, 255).astype("uint8")
        return frame.tobytes()


class _PureRenderer:
    """纯标准库渲染器（无 numpy 时使用；分辨率会被压低以省 CPU）。"""

    def __init__(self, w: int, h: int, seed: int) -> None:
        self.w, self.h = w, h
        self.rng = random.Random(seed)
        self.buf = bytearray(w * h)
        for y in range(h):
            base = y * w
            row_val = int(96 + 9 * math.cos(y / 27.0))
            for x in range(w):
                self.buf[base + x] = max(0, min(255, int(row_val + 14 * math.sin(x / 41.0))))

    def render(self, t: float, phase: str) -> bytes:
        buf = bytearray(self.buf)
        w, h = self.w, self.h
        density = 0.0018
        jitter = 1
        if phase == "splash":
            density = 0.016
            jitter = 4
        elif phase in ("person", "tamper"):
            density = 0.004
            jitter = 2
        count = max(4, int(w * h * density))
        gain = 62 if phase == "splash" else 46
        for _ in range(count):
            x = self.rng.randrange(w)
            y = self.rng.randrange(h)
            x = (x + self.rng.randint(-jitter, jitter)) % w
            y = (y + self.rng.randint(-jitter, jitter)) % h
            idx = y * w + x
            buf[idx] = min(255, buf[idx] + gain)
            for shift in (1, -1, w, -w):
                j = (idx + shift) % (w * h)
                buf[j] = min(255, buf[j] + gain // 2)
        if phase == "aggregation":
            cy, cx = h * 0.55, w * 0.5
            ry, rx = h * 0.22, w * 0.26
            for y in range(h):
                dy = (y - cy) / ry
                if abs(dy) > 1.0:
                    continue
                span = int(rx * math.sqrt(max(0.0, 1.0 - dy * dy)))
                base = y * w
                for x in range(max(0, int(cx - span)), min(w, int(cx + span))):
                    buf[base + x] = 14
        if phase == "person":
            x0, y0 = int(w * 0.10), int(h * 0.18)
            bw, bh = max(6, int(w * 0.075)), max(16, int(h * 0.35))
            for y in range(y0, min(h, y0 + bh)):
                base = y * w
                for x in range(x0, min(w, x0 + bw)):
                    buf[base + x] = 24
        if phase == "tamper":
            for i in range(len(buf)):
                buf[i] = min(255, buf[i] + 70)
        return bytes(buf)


class SimSource:
    """一路模拟相机：按剧本产出灰度帧（掉线阶段返回 None）。"""

    def __init__(self, camera_id: str, cam_cfg: Dict[str, Any], sim_cfg: Dict[str, Any]) -> None:
        self.camera_id = camera_id
        self.sim_cfg = sim_cfg or {}
        self.scenario = SimScenario(camera_id, self.sim_cfg)
        self._renderer = None
        self._size: Tuple[int, int] = (0, 0)
        seed = int(self.sim_cfg.get("seed", 20260919) or 20260919) + (abs(hash(camera_id)) % 1000)
        self._seed = seed
        self.t0 = time.time()

    def _get_renderer(self, w: int, h: int):
        if self._renderer is not None and self._size == (w, h):
            return self._renderer
        if has("numpy"):
            self._renderer = _NumpyRenderer(w, h, self._seed)
        else:
            # 纯 Python 渲染很慢，压到 ≤160x90，并说明原因
            nw, nh = (160, 90) if w > 160 else (w, h)
            if (nw, nh) != (w, h):
                note_degraded(
                    "simulate",
                    "无 numpy：模拟视频源降到 %dx%d 渲染（帧率不变，画面细节减少）" % (nw, nh),
                )
            w, h = nw, nh
            self._renderer = _PureRenderer(w, h, self._seed)
        self._size = (w, h)
        return self._renderer

    def next_frame(self, w: int, h: int) -> Optional[Frame]:
        phase = self.scenario.phase()
        if self.scenario.camera_offline():
            return None
        renderer = self._get_renderer(w, h)
        rw, rh = self._size
        t = time.time() - self.t0
        gray = renderer.render(t, phase)
        return Frame(gray, rw, rh, camera_id=self.camera_id)

    # ---------------- 剧本注入事件 ----------------
    def injected_event(self, phase: str) -> Optional[Dict[str, Any]]:
        """只有 person 需要注入（HOG 对合成剪影无效）；其余由真检测器产出。"""
        ts = int(time.time())
        if phase == "person":
            # 注意：confidence 一律给 0.0 —— 这条事件不是算出来的，是剧本演的，
            # 编一个"刚好过阈值"的置信度就是在骗人。metric.score 同理给 0。
            return {
                "ts": ts,
                "camera_id": self.camera_id,
                "type": "person",
                "severity": "warn",
                "confidence": 0.0,
                "title": "警戒区检出人形",
                "detail": "[模拟] 剧本注入的 person 事件（confidence 无意义，置 0）："
                "合成画面上的剪影 HOG 检不出，故在 mock 模式下直接注入；"
                "真实模式必须依赖真画面与已标定模型",
                "metric": {"confidence": 0.0, "score": 0.0, "duration_s": 0},
                "evidence": EVIDENCE_LEVEL,
            }
        return None


# ==========================================================================
# 历史指标回填（仅 --simulate）
# ==========================================================================
def backfill_history(cfg, store, cameras: List[str], logger=None, hours: int = 24) -> int:
    """给曲线端点造历史 V-Value（仅当该相机还没有任何采样时）。返回写入条数。"""
    step = int(cfg.get("metrics.default_step", 300) or 300)
    baseline = 0.012
    written = 0
    now = int(time.time())
    rng = random.Random(int(cfg.get("sim.seed", 20260919) or 20260919))
    windows = cfg.get("feed_windows", []) or []
    for cam in cameras:
        existing = store.series(cam, now - hours * 3600, now)
        if existing:
            continue
        rows = []
        for offset in range(hours * 3600, 0, -step):
            ts = now - offset
            local = time.localtime(ts)
            minutes = local.tm_hour * 60 + local.tm_min
            value = baseline * (0.7 + 0.6 * rng.random())
            for window in windows:
                try:
                    sh, sm = [int(x) for x in str(window["start"]).split(":")]
                    eh, em = [int(x) for x in str(window["end"]).split(":")]
                except Exception:
                    continue
                start, end = sh * 60 + sm, eh * 60 + em
                if start <= minutes <= end:
                    # 投喂窗口内抬高，模拟摄食水花
                    value += baseline * (1.2 + 1.6 * rng.random())
            if rng.random() < 0.02:
                value += baseline * 3.0  # 偶发尖峰
            rows.append((cam, ts, round(value, 4)))
        if rows:
            store.add_metrics(rows)
            written += len(rows)
    if written and logger:
        # 用 warn 级别：这条曲线是造出来的，必须显眼，不能被当成现场实测
        logger(
            "warn",
            "simulate",
            "已回填 %d 条**模拟**历史指标（24 h，仅 --simulate；health.mode=mock，"
            "曲线不是现场实测数据）" % written,
        )
    return written


__all__ = ["SimSource", "SimScenario", "backfill_history", "PHASE_ORDER"]
