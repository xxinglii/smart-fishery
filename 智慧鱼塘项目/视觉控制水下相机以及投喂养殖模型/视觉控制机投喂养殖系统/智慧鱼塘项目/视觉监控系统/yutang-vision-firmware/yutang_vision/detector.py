"""5 类事件判据（契约 §8）。

| 类型 | 判据 | 本文件的实现 |
|---|---|---|
| `splash_activity` | 投料区 ROI 内运动像素占比（V-Value）相对滚动基线的比值 ≥ `thresholds.splash_ratio` | 帧差（有 numpy 用灰度阈值帧差；没有则退化为**字节异或**变化率） |
| `surface_aggregation` | 暗斑连通域面积占比 ≥ `thresholds.aggregation_area_pct` 且持续 ≥ N 帧 | 均值-kσ 阈值 + 连通域（有 cv2 用 `connectedComponentsWithStats`，否则纯 Python BFS） |
| `person` | 警戒区检出人形 | 优先 MobileNet-SSD（若配置了模型文件），否则 OpenCV HOG；**不上 YOLO** |
| `offline` | RTSP 连续失败 ≥ 30 s | 由运行期看门狗调用 `offline_event()` |
| `tamper` | 画面整体亮度/方差突变 | 亮度均值 EMA 突变 或 方差塌陷（遮挡/糊镜头） |

诚实性约束（写死在代码里）：
- 每个事件都带 `confidence` 与 `evidence="C"`（未标定，不得声称 A/B）。
- 缺 numpy / OpenCV 时，相应能力直接禁用或降级，并在日志与 health 里说明，**不假装检出**。
- HOG 没有标定过的置信度，代码里用单调映射并在 detail 里注明"未标定"。

明确不做（项目内证据否决）：数鱼、数饲料颗粒、鱼体估重、生物量反演。
"""

from __future__ import annotations

import math
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import EVIDENCE_LEVEL, has, note_degraded
from .metrics import MetricsService

#: ROI 全画面
FULL_ROI: Tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def roi_to_pixels(roi: Optional[Sequence[float]], w: int, h: int) -> Tuple[int, int, int, int]:
    """归一化 ROI [x, y, w, h] -> 像素 (x0, y0, x1, y1)，带边界裁剪。"""
    if not roi or len(roi) != 4:
        return 0, 0, w, h
    try:
        x, y, rw, rh = [float(v) for v in roi]
    except Exception:
        return 0, 0, w, h
    x0 = int(_clamp(x, 0.0, 1.0) * w)
    y0 = int(_clamp(y, 0.0, 1.0) * h)
    x1 = int(_clamp(x + rw, 0.0, 1.0) * w)
    y1 = int(_clamp(y + rh, 0.0, 1.0) * h)
    if x1 - x0 < 4:
        x1 = min(w, x0 + 4)
    if y1 - y0 < 4:
        y1 = min(h, y0 + 4)
    return x0, y0, x1, y1


class GrayView:
    """灰度帧的统一访问层：有 numpy 走向量化，没有就走纯标准库近似。"""

    __slots__ = ("gray", "w", "h", "_np")

    def __init__(self, gray: bytes, w: int, h: int) -> None:
        self.gray = gray
        self.w = int(w)
        self.h = int(h)
        self._np = None

    # ---------- numpy 视图 ----------
    def array(self):
        if not has("numpy"):
            return None
        if self._np is None:
            import numpy as np  # type: ignore

            if len(self.gray) != self.w * self.h:
                return None
            self._np = np.frombuffer(self.gray, dtype=np.uint8).reshape(self.h, self.w)
        return self._np

    # ---------- 统计量 ----------
    def mean_std(self, roi: Optional[Sequence[float]] = None) -> Tuple[float, float]:
        x0, y0, x1, y1 = roi_to_pixels(roi, self.w, self.h)
        arr = self.array()
        if arr is not None:
            patch = arr[y0:y1, x0:x1]
            if patch.size == 0:
                return 0.0, 0.0
            return float(patch.mean()), float(patch.std())
        # 纯标准库：按行跨列抽样，够用且快
        total = 0
        total_sq = 0
        count = 0
        for y in range(y0, y1, 2):
            base = y * self.w
            row = self.gray[base + x0 : base + x1 : 2]
            for value in row:
                total += value
                total_sq += value * value
                count += 1
        if count == 0:
            return 0.0, 0.0
        mean = total / float(count)
        var = max(0.0, total_sq / float(count) - mean * mean)
        return mean, math.sqrt(var)

    # ---------- 运动（帧差） ----------
    def motion_ratio(
        self, prev: "Optional[GrayView]", roi: Optional[Sequence[float]] = None, pixel_thr: int = 25
    ) -> float:
        """ROI 内运动像素占比（V-Value）。无上一帧时返回 0。"""
        if prev is None or prev.w != self.w or prev.h != self.h or len(prev.gray) != len(self.gray):
            return 0.0
        x0, y0, x1, y1 = roi_to_pixels(roi, self.w, self.h)
        arr, prev_arr = self.array(), prev.array()
        if arr is not None and prev_arr is not None:
            patch = arr[y0:y1, x0:x1].astype("int16")
            prev_patch = prev_arr[y0:y1, x0:x1].astype("int16")
            diff = abs(patch - prev_patch)
            if diff.size == 0:
                return 0.0
            return float((diff > int(pixel_thr)).sum()) / float(diff.size)
        # 纯标准库近似：把两行字节做 XOR，统计"变化过的像素"比例
        # （注意：这是「是否变化」而不是「变化是否超过阈值」，README 里写明了）
        changed = 0
        total = 0
        for y in range(y0, y1):
            base = y * self.w
            row_a = self.gray[base + x0 : base + x1]
            row_b = prev.gray[base + x0 : base + x1]
            if not row_a:
                continue
            xor_int = int.from_bytes(row_a, "big") ^ int.from_bytes(row_b, "big")
            # 统计非零字节数 = 变化像素数
            changed += len(row_a) - xor_int.to_bytes(len(row_a), "big").count(0)
            total += len(row_a)
        if total == 0:
            return 0.0
        return changed / float(total)

    # ---------- 暗斑连通域 ----------
    def dark_area_pct(self, roi: Optional[Sequence[float]] = None, k: float = 1.5) -> float:
        """最大暗斑面积占 ROI 的百分比（surface_aggregation 的粗略代理）。"""
        x0, y0, x1, y1 = roi_to_pixels(roi, self.w, self.h)
        arr = self.array()
        if arr is not None:
            import numpy as np  # type: ignore

            patch = arr[y0:y1, x0:x1]
            if patch.size == 0:
                return 0.0
            mean = float(patch.mean())
            std = float(patch.std())
            thr = mean - float(k) * std
            mask = (patch < thr).astype("uint8")
            if mask.sum() == 0:
                return 0.0
            if has("cv2"):
                import cv2  # type: ignore

                kernel = np.ones((3, 3), np.uint8)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
                count, _labels, stats, _centroids = cv2.connectedComponentsWithStats(mask, 8)
                if count <= 1:
                    return 0.0
                biggest = int(stats[1:, 4].max()) if count > 1 else 0
            else:
                biggest = _max_component_pure(mask.reshape(-1).tolist(), mask.shape[1], mask.shape[0])
            return 100.0 * float(biggest) / float(mask.size)
        # 纯标准库：抽样成网格再做连通域
        step = max(1, int(math.sqrt(max(1, ((x1 - x0) * (y1 - y0)) / 4000.0))))
        gw = max(1, (x1 - x0) // step)
        gh = max(1, (y1 - y0) // step)
        values: List[int] = []
        total = 0
        total_sq = 0
        for gy in range(gh):
            y = y0 + gy * step
            base = y * self.w
            for gx in range(gw):
                value = self.gray[base + x0 + gx * step]
                values.append(value)
                total += value
                total_sq += value * value
        if not values:
            return 0.0
        n = float(len(values))
        mean = total / n
        std = math.sqrt(max(0.0, total_sq / n - mean * mean))
        thr = mean - float(k) * std
        mask = [1 if v < thr else 0 for v in values]
        if not any(mask):
            return 0.0
        biggest = _max_component_pure(mask, gw, gh)
        return 100.0 * float(biggest) / n


def _max_component_pure(mask: Sequence[int], w: int, h: int) -> int:
    """纯 Python 4-邻域连通域最大面积（BFS）。mask 为 0/1 序列，行优先。"""
    if w <= 0 or h <= 0 or len(mask) < w * h:
        return 0
    visited = bytearray(w * h)
    best = 0
    for start in range(w * h):
        if not mask[start] or visited[start]:
            continue
        area = 0
        stack = [start]
        visited[start] = 1
        while stack:
            idx = stack.pop()
            area += 1
            y, x = divmod(idx, w)
            if x > 0 and mask[idx - 1] and not visited[idx - 1]:
                visited[idx - 1] = 1
                stack.append(idx - 1)
            if x < w - 1 and mask[idx + 1] and not visited[idx + 1]:
                visited[idx + 1] = 1
                stack.append(idx + 1)
            if y > 0 and mask[idx - w] and not visited[idx - w]:
                visited[idx - w] = 1
                stack.append(idx - w)
            if y < h - 1 and mask[idx + w] and not visited[idx + w]:
                visited[idx + w] = 1
                stack.append(idx + w)
        best = max(best, area)
    return best


class _CameraDetState:
    """单相机的检测状态。"""

    def __init__(self) -> None:
        self.prev: Optional[GrayView] = None
        self.prev_ts: int = 0
        self.frame_index: int = 0
        self.burst_start_ts: Optional[int] = None
        self.burst_peak: float = 0.0
        self.agg_streak: int = 0
        self.agg_start_ts: Optional[int] = None
        self.ema_mean: Optional[float] = None
        self.ema_std: Optional[float] = None
        self.low_std_streak: int = 0
        self.cooldown_until: Dict[str, float] = {}
        self.last_ratio: float = 0.0
        self.last_baseline: float = 0.0
        self.last_v: float = 0.0
        self.last_ts: int = 0


class Detector:
    """把一帧灰度图变成事件（不写库，写库/抓图由 Runtime 统一做）。"""

    def __init__(self, cfg, metrics: MetricsService, logger=None, simulate: bool = False) -> None:
        self.cfg = cfg
        self.metrics = metrics
        self._log = logger
        self._simulate = simulate
        self._states: Dict[str, _CameraDetState] = {}
        self._hog = None
        self._hog_ready = False
        self._svm = None
        self._netsd = None
        self._netsd_ready = False
        self._warned: set = set()
        self._baseline_ready: Dict[str, bool] = {}

    # ------------------------------------------------------------------
    def _warn_once(self, key: str, msg: str) -> None:
        """记一次"能力降级"：日志 + health.services 里出现 ok=false 的条目。"""
        if key in self._warned:
            return
        self._warned.add(key)
        note_degraded(key, msg)
        if self._log:
            self._log("warn", "detector", msg)

    def _log_once(self, key: str, msg: str, level: str = "info") -> None:
        """只写一次日志，不算降级（例如基线预热这种正常过程）。"""
        if key in self._warned:
            return
        self._warned.add(key)
        if self._log:
            self._log(level, "detector", msg)

    def _state(self, camera_id: str) -> _CameraDetState:
        state = self._states.get(camera_id)
        if state is None:
            state = _CameraDetState()
            self._states[camera_id] = state
        return state

    def _cooling(self, state: _CameraDetState, kind: str, ts: int) -> bool:
        return state.cooldown_until.get(kind, 0) > ts

    def _set_cooldown(self, state: _CameraDetState, kind: str, ts: int, seconds: float) -> None:
        state.cooldown_until[kind] = ts + float(seconds)

    # ------------------------------------------------------------------
    # 人形检测后端
    # ------------------------------------------------------------------
    def _load_person_backend(self) -> None:
        if self._hog_ready or self._netsd_ready:
            return
        proto = self.cfg.get("detector.mobilenet_prototxt") or ""
        model = self.cfg.get("detector.mobilenet_caffemodel") or ""
        if proto and model and has("cv2"):
            import os

            if os.path.exists(proto) and os.path.exists(model):
                try:
                    import cv2  # type: ignore

                    self._netsd = cv2.dnn.readNetFromCaffe(proto, model)
                    self._netsd_ready = True
                    if self._log:
                        self._log("info", "detector", "人形检测后端：MobileNet-SSD")
                    return
                except Exception as exc:
                    self._warn_once("netsd", "MobileNet-SSD 加载失败，回退 HOG：%s" % exc)
        if has("cv2"):
            try:
                import cv2  # type: ignore
                import numpy as np  # type: ignore

                hog = cv2.HOGDescriptor()
                detector = cv2.HOGDescriptor_getDefaultPeopleDetector()
                hog.setSVMDetector(detector)
                self._hog = hog
                # 自己留一份权重：不同 OpenCV 版本有的没有 getSVMDetector()
                self._svm = np.asarray(detector, dtype="float64").reshape(-1)
                self._hog_ready = True
                if self._log:
                    self._log("info", "detector", "人形检测后端：OpenCV HOG（未标定，仅作粗筛）")
            except Exception as exc:
                self._warn_once("hog", "HOG 初始化失败，人形检测禁用：%s" % exc)
        else:
            self._hog_ready = True  # 标记已尝试，避免反复告警
            self._warn_once(
                "person",
                "缺少 opencv-python：person 事件在 live 模式下不产出（simulate 模式的假数据流不受影响）",
            )

    def _detect_person(self, view: GrayView, roi: Sequence[float]) -> Optional[Tuple[float, float, Tuple[int, int, int, int]]]:
        """返回 (confidence, score, box) 或 None。"""
        self._load_person_backend()
        x0, y0, x1, y1 = roi_to_pixels(roi, view.w, view.h)
        arr = view.array()
        if self._netsd_ready and arr is not None:
            try:
                import cv2  # type: ignore

                patch = arr[y0:y1, x0:x1]
                if patch.size == 0:
                    return None
                blob = cv2.dnn.blobFromImage(
                    cv2.cvtColor(patch, cv2.COLOR_GRAY2BGR), 0.007843, (300, 300), 127.5
                )
                self._netsd.setInput(blob)
                detections = self._netsd.forward()
                best = None
                for i in range(detections.shape[2]):
                    conf = float(detections[0, 0, i, 2])
                    cls = int(detections[0, 0, i, 1])
                    if cls == 15 and conf >= 0.2:  # VOC class 15 = person
                        box = detections[0, 0, i, 3:7]
                        if best is None or conf > best[0]:
                            best = (
                                conf,
                                conf,
                                (
                                    x0 + int(box[0] * (x1 - x0)),
                                    y0 + int(box[1] * (y1 - y0)),
                                    x0 + int(box[2] * (x1 - x0)),
                                    y0 + int(box[3] * (y1 - y0)),
                                ),
                            )
                return best
            except Exception as exc:
                self._warn_once("netsd_run", "MobileNet-SSD 推理失败，改用 HOG：%s" % exc)
                self._netsd_ready = False
        if not self._hog_ready or self._hog is None:
            return None
        try:
            import numpy as np  # type: ignore

            if (x1 - x0) < 64 or (y1 - y0) < 128:
                return None  # HOG 窗口最小 64x128
            arr = view.array()
            if arr is None:
                return None
            patch = arr[y0:y1, x0:x1]
            h, w = patch.shape
            stride = int(self.cfg.get("detector.hog_win_stride", 16) or 16)
            detector = self._svm_detector()
            best_score = None
            best_xy = (0, 0)
            # 自己滑窗 + 自己算 SVM 分数：OpenCV Python 绑定的 detect(locations=...)
            # 在部分版本上不可用，而 detectMultiScale 不返回分数（无法给 confidence）。
            for yy in range(0, max(1, h - 128 + 1), stride):
                for xx in range(0, max(1, w - 64 + 1), stride):
                    win = np.ascontiguousarray(patch[yy : yy + 128, xx : xx + 64])
                    if win.shape != (128, 64):
                        continue
                    feature = self._hog.compute(win).reshape(-1)
                    if detector is not None and detector.size == feature.size + 1:
                        score = float(np.dot(feature, detector[:-1]) + detector[-1])
                    elif detector is not None and detector.size >= feature.size:
                        score = float(np.dot(feature, detector[: feature.size]))
                    else:
                        score = float(feature.sum())
                    if best_score is None or score > best_score:
                        best_score, best_xy = score, (xx, yy)
            if best_score is None or best_score <= 0:
                return None
            # HOG 的 SVM 分数没有做过现场标定：这里只做**单调映射**，detail 里会注明
            confidence = _clamp(0.45 + 0.25 * best_score, 0.3, 0.90)
            bx, by = best_xy
            return confidence, best_score, (x0 + bx, y0 + by, x0 + bx + 64, y0 + by + 128)
        except Exception as exc:
            self._warn_once("hog_run", "HOG 推理失败（本帧跳过）：%s" % exc)
            return None

    def _svm_detector(self):
        """HOG 的 SVM 权重（3781 = 3780 权重 + 1 偏置）。

        优先用加载时自己留下的那份；再退回 `hog.svmDetector` / `getSVMDetector()`
        （不同 OpenCV 版本暴露的属性名不一样，这里逐个试，试不到就返回 None，
        由调用方退化为特征和，不影响"不崩"这条底线）。
        """
        if self._svm is not None:
            return self._svm
        try:
            import numpy as np  # type: ignore

            raw = getattr(self._hog, "svmDetector", None)
            if raw is None:
                getter = getattr(self._hog, "getSVMDetector", None)
                raw = getter() if callable(getter) else None
            if raw is not None and len(raw):
                self._svm = np.asarray(raw, dtype="float64").reshape(-1)
        except Exception as exc:
            self._warn_once("hog_svm", "读取 HOG SVM 权重失败（退化为特征和）：%s" % exc)
        return self._svm

    # ------------------------------------------------------------------
    # 对外：最近一帧的摄食信号
    # ------------------------------------------------------------------
    def last_signal(self, camera_id: str) -> Optional[Dict[str, Any]]:
        """返回该相机最近一帧的 {ts, v_value, baseline, ratio, baseline_ready, frozen}。

        为什么单开这个访问器、而不是让投喂状态机订阅 splash_activity 事件：
        splash_activity 只在强度"上去"时发一次，随后进 120 s 冷却，它从不表达
        "强度下来了" —— 而饱食点恰恰是回落。所以状态机必须直接读实时值。
        """
        state = self._states.get(camera_id)
        if state is None or state.last_ts == 0:
            return None
        frozen = False
        try:
            frozen = bool(self.metrics.baseline_frozen(camera_id))
        except AttributeError:
            frozen = False
        return {
            "ts": int(state.last_ts),
            "v_value": round(float(state.last_v), 5),
            "baseline": round(float(state.last_baseline), 5),
            "ratio": round(float(state.last_ratio), 3),
            "baseline_ready": bool(self._baseline_ready.get(camera_id)),
            "frozen": frozen,
        }

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    def process(
        self,
        camera_id: str,
        frame,
        analysis_cfg: Optional[Dict[str, Any]] = None,
        feed_window_active: bool = False,
    ) -> List[Dict[str, Any]]:
        """处理一帧，返回事件列表（可能为空）。"""
        analysis_cfg = analysis_cfg or {}
        roi = analysis_cfg.get("roi")
        pixel_thr = int(self.cfg.get("analysis.pixel_thr", 25) or 25)
        ts = int(getattr(frame, "ts", time.time()))
        view = GrayView(frame.gray, frame.w, frame.h)
        state = self._state(camera_id)
        events: List[Dict[str, Any]] = []

        # ---------- 1. V-Value（运动像素占比）----------
        v_value = view.motion_ratio(state.prev, roi, pixel_thr)
        observed = self.metrics.observe(camera_id, ts, v_value)
        baseline = observed["baseline"]
        ratio = observed["ratio"]
        state.last_v, state.last_baseline, state.last_ratio = v_value, baseline, ratio
        state.last_ts = ts
        tracker_len = len(self.metrics.tracker(camera_id))
        # 基线预热：至少 10 个采样点且基线非零才允许出 splash 事件，避免冷启动误报
        baseline_ready = tracker_len >= 10 and baseline > 1e-4
        if not baseline_ready:
            self._log_once(
                "baseline_%s" % camera_id,
                "%s 基线预热中（需 ≥10 个采样点且基线 >0，当前 %d 点）：预热期内不产生 splash 事件"
                % (camera_id, tracker_len),
            )
        self._baseline_ready[camera_id] = baseline_ready

        splash_ratio_thr = float(self.cfg.get("thresholds.splash_ratio", 1.6) or 1.6)
        splash_min_s = float(self.cfg.get("detector.splash_min_s", 8) or 8)
        require_window = bool(self.cfg.get("detector.splash_require_feed_window", False))
        splash_ctx = (not require_window) or feed_window_active
        absolute_floor = float(self.cfg.get("detector.splash_floor", 0.005) or 0.005)

        if (
            self._baseline_ready.get(camera_id)
            and baseline > 1e-4
            and ratio >= splash_ratio_thr
            and v_value >= absolute_floor
            and splash_ctx
        ):
            if state.burst_start_ts is None:
                state.burst_start_ts = ts
                state.burst_peak = v_value
            else:
                state.burst_peak = max(state.burst_peak, v_value)
            duration = ts - state.burst_start_ts
            if duration >= splash_min_s and not self._cooling(state, "splash_activity", ts):
                # 置信度：与超阈幅度、持续时间单调相关，未标定 -> evidence C
                margin = ratio / splash_ratio_thr - 1.0
                confidence = _clamp(
                    0.5 + 0.15 * min(margin, 2.0) + 0.1 * min(duration / 30.0, 1.0), 0.3, 0.95
                )
                events.append(
                    {
                        "ts": ts,
                        "camera_id": camera_id,
                        "type": "splash_activity",
                        "severity": "info",
                        "confidence": round(confidence, 3),
                        "title": "摄食水花强度短时上升",
                        "detail": "V-Value %.3f，基线 %.3f，比值 %.2f×（阈值 %.2f×），持续 %d s%s"
                        % (
                            v_value,
                            baseline,
                            ratio,
                            splash_ratio_thr,
                            duration,
                            "，投料窗口内" if feed_window_active else "",
                        ),
                        "metric": {
                            "v_value": round(v_value, 4),
                            "baseline": round(baseline, 4),
                            "ratio": round(ratio, 3),
                            "duration_s": int(duration),
                        },
                        "evidence": EVIDENCE_LEVEL,
                    }
                )
                self._set_cooldown(
                    state, "splash_activity", ts, float(self.cfg.get("detector.splash_cooldown_s", 120) or 120)
                )
                state.burst_start_ts = None
                state.burst_peak = 0.0
        else:
            state.burst_start_ts = None
            state.burst_peak = 0.0

        # ---------- 2. 暗斑聚集（浮头代理）----------
        dark_pct = view.dark_area_pct(roi, float(self.cfg.get("detector.dark_k", 1.5) or 1.5))
        agg_thr = float(self.cfg.get("thresholds.aggregation_area_pct", 4.0) or 4.0)
        if dark_pct >= agg_thr:
            if state.agg_streak == 0:
                state.agg_start_ts = ts
            state.agg_streak += 1
        else:
            state.agg_streak = 0
            state.agg_start_ts = None
        need_frames = int(self.cfg.get("detector.aggregation_frames", 15) or 15)
        if (
            state.agg_streak >= need_frames
            and not self._cooling(state, "surface_aggregation", ts)
        ):
            duration = int(ts - (state.agg_start_ts or ts))
            confidence = _clamp(0.45 + 0.25 * min(dark_pct / max(agg_thr, 1e-6) - 1.0, 1.5), 0.3, 0.85)
            events.append(
                {
                    "ts": ts,
                    "camera_id": camera_id,
                    "type": "surface_aggregation",
                    "severity": "notice",
                    "confidence": round(confidence, 3),
                    "title": "水面暗斑聚集（浮头粗代理）",
                    "detail": "暗斑面积占比 %.2f%%（阈值 %.2f%%），连续 %d 帧，约 %d s；"
                    "该指标只是氧债/浮头的粗略代理，未做现场标定"
                    % (dark_pct, agg_thr, state.agg_streak, duration),
                    "metric": {
                        "area_pct": round(dark_pct, 3),
                        "thr_pct": round(agg_thr, 3),
                        "frames": int(state.agg_streak),
                        "duration_s": duration,
                    },
                    "evidence": EVIDENCE_LEVEL,
                }
            )
            self._set_cooldown(
                state,
                "surface_aggregation",
                ts,
                float(self.cfg.get("detector.aggregation_cooldown_s", 300) or 300),
            )
            state.agg_streak = 0

        # ---------- 3. 人形（防偷捕）----------
        person_every = int(self.cfg.get("detector.person_every_n_frames", 5) or 5)
        person_roi = self.cfg.get("detector.person_roi") or [0.0, 0.3, 0.35, 0.6]
        if state.frame_index % max(1, person_every) == 0 and not self._cooling(state, "person", ts):
            hit = self._detect_person(view, person_roi)
            if hit:
                confidence, score, box = hit
                need_conf = float(self.cfg.get("thresholds.person_confidence", 0.6) or 0.6)
                if confidence >= need_conf:
                    events.append(
                        {
                            "ts": ts,
                            "camera_id": camera_id,
                            "type": "person",
                            "severity": "warn",
                            "confidence": round(confidence, 3),
                            "title": "警戒区检出人形",
                            "detail": "置信度 %.2f（阈值 %.2f），命中框 x=%d,y=%d,w=%d,h=%d；"
                            "HOG 分数未标定，仅作粗筛，请人工确认"
                            % (confidence, need_conf, box[0], box[1], box[2] - box[0], box[3] - box[1]),
                            "metric": {
                                "confidence": round(confidence, 3),
                                "score": round(float(score), 3),
                                "duration_s": 0,
                            },
                            "evidence": EVIDENCE_LEVEL,
                        }
                    )
                    self._set_cooldown(
                        state, "person", ts, float(self.cfg.get("detector.person_cooldown_s", 60) or 60)
                    )

        # ---------- 4. 画面异常（遮挡/移位）----------
        mean, std = view.mean_std(roi)
        if state.ema_mean is None:
            state.ema_mean, state.ema_std = mean, std
        else:
            alpha = 0.05
            ema_mean_before, ema_std_before = state.ema_mean, state.ema_std
            state.ema_mean = (1 - alpha) * state.ema_mean + alpha * mean
            state.ema_std = (1 - alpha) * state.ema_std + alpha * std
            mean_delta = abs(mean - ema_mean_before)
            std_thr = float(self.cfg.get("detector.tamper_std_min", 4.0) or 4.0)
            if std < std_thr and ema_std_before > std_thr * 3:
                state.low_std_streak += 1
            else:
                state.low_std_streak = 0
            sudden = mean_delta >= float(self.cfg.get("detector.tamper_mean_delta", 28.0) or 28.0)
            obscured = state.low_std_streak >= 10
            if (sudden or obscured) and not self._cooling(state, "tamper", ts):
                kind = "亮度突变" if sudden else "画面方差塌陷（疑似遮挡/糊镜头）"
                events.append(
                    {
                        "ts": ts,
                        "camera_id": camera_id,
                        "type": "tamper",
                        "severity": "warn",
                        "confidence": round(_clamp(0.5 + (mean_delta / 100.0), 0.3, 0.85), 3),
                        "title": "画面异常（疑似遮挡/移位）",
                        "detail": "%s：亮度均值 %.1f（基线 %.1f，差 %.1f），方差 %.1f（基线 %.1f）"
                        % (kind, mean, ema_mean_before, mean_delta, std, ema_std_before),
                        "metric": {
                            "mean": round(mean, 2),
                            "baseline_mean": round(ema_mean_before, 2),
                            "std": round(std, 2),
                            "duration_s": int(state.low_std_streak),
                        },
                        "evidence": EVIDENCE_LEVEL,
                    }
                )
                self._set_cooldown(
                    state, "tamper", ts, float(self.cfg.get("detector.tamper_cooldown_s", 300) or 300)
                )
                state.low_std_streak = 0

        # ---------- 5. 通用运动（非投料窗口的异常活动）----------
        motion_ratio_thr = float(self.cfg.get("detector.motion_ratio", 0.02) or 0.02)
        if (
            v_value >= motion_ratio_thr
            and not feed_window_active
            and not self._cooling(state, "motion", ts)
            # 摄食爆发期间由 splash_activity 代表，不再重复报 motion
            and state.burst_start_ts is None
            and not any(e["type"] == "splash_activity" for e in events)
        ):
            events.append(
                {
                    "ts": ts,
                    "camera_id": camera_id,
                    "type": "motion",
                    "severity": "info",
                    "confidence": round(_clamp(0.4 + v_value * 5, 0.3, 0.8), 3),
                    "title": "画面运动超阈值",
                    "detail": "非投料窗口内运动像素占比 %.3f（阈值 %.3f），基线 %.3f"
                    % (v_value, motion_ratio_thr, baseline),
                    "metric": {
                        "v_value": round(v_value, 4),
                        "baseline": round(baseline, 4),
                        "ratio": round(ratio, 3),
                        "duration_s": 0,
                    },
                    "evidence": EVIDENCE_LEVEL,
                }
            )
            self._set_cooldown(state, "motion", ts, float(self.cfg.get("detector.motion_cooldown_s", 60) or 60))

        state.prev = view
        state.prev_ts = ts
        state.frame_index += 1
        return events

    # ------------------------------------------------------------------
    def offline_event(
        self, camera_id: str, down_s: int, failures: int, ts: Optional[int] = None, name: str = ""
    ) -> Dict[str, Any]:
        """相机离线事件（由运行期看门狗在连续失败 ≥ offline_after_s 时调用一次）。"""
        ts = int(ts or time.time())
        return {
            "ts": ts,
            "camera_id": camera_id,
            "type": "offline",
            "severity": "critical" if down_s >= 300 else "warn",
            "confidence": 1.0,  # 拉流失败是确定事实，不是推断
            "title": "相机离线",
            "detail": "%sRTSP 连续失败 %d s（累计 %d 次重连尝试），已指数退避重试"
            % (("%s " % name) if name else "", int(down_s), int(failures)),
            "metric": {"duration_s": int(down_s), "failures": int(failures)},
            "evidence": EVIDENCE_LEVEL,
        }

    def status(self) -> Dict[str, Any]:
        """给 health.services / 自检用。"""
        return {
            "person_backend": "mobilenet-ssd"
            if self._netsd_ready
            else ("hog" if self._hog_ready and self._hog is not None else "unavailable"),
            "motion_backend": "numpy" if has("numpy") else "stdlib-xor",
            "components_backend": "cv2" if has("cv2") else "python-bfs",
        }


__all__ = ["Detector", "GrayView", "roi_to_pixels", "FULL_ROI"]
