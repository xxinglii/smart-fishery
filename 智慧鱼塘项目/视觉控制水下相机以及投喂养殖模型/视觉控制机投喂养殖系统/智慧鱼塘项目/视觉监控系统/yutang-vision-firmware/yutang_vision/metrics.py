"""指标聚合：V-Value 曲线（含基线计算与降采样）+ 主机/存储指标采样。

V-Value 的定义（与 detector.py 保持一致）：
    投料区 ROI 内**运动像素占比**（0..1）。
    比值 ratio = v_value / baseline，baseline = 最近 baseline_window_s 内 V-Value 的
    **滚动中位数**（中位数对摄食爆发的短时尖峰不敏感，比均值稳）。
    thr = baseline * thresholds.splash_ratio。

曲线聚合：
- 原始采样每 `metrics.sample_s` 秒一条入库；
- 查询时按 `step` 分桶取均值（降采样），每个桶给出该时刻的 baseline 与 thr；
- 冷启动（历史不足）时用已有桶的中位数兜底，并在 README 里说明，不假装有历史。

另外本模块还提供 SystemSampler：CPU / 内存 / 温度 / 磁盘剩余（契约 §1 的 pi 对象）。
Linux 走 /proc 与 /sys（树莓派上四项都是真值）；macOS 等平台读不到的项给 None，
绝不编数。
"""

from __future__ import annotations

import os
import re
import shutil
import statistics
import subprocess
import threading
import time
from collections import deque
from typing import Any, Deque, Dict, List, Optional, Sequence, Tuple

from . import note_degraded

_WINDOW_RE = re.compile(r"^(\d+)\s*([smhd]?)$", re.I)
_UNIT_S = {"": 60, "s": 1, "m": 60, "h": 3600, "d": 86400}


def parse_window(text: Any, default: str = "24h") -> int:
    """'24h' / '30m' / '600' -> 秒。解析不了就用 default。"""
    if text is None:
        text = default
    if isinstance(text, (int, float)) and not isinstance(text, bool):
        return max(1, int(text))
    match = _WINDOW_RE.match(str(text).strip())
    if not match:
        match = _WINDOW_RE.match(default)
        if not match:
            return 86400
    return int(match.group(1)) * _UNIT_S[match.group(2).lower()]


def median(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return float(statistics.median(list(values)))


class BaselineTracker:
    """滚动中位数基线（带时间窗口）。"""

    def __init__(self, window_s: float = 1800.0, min_samples: int = 3) -> None:
        self.window_s = float(window_s)
        self.min_samples = int(min_samples)
        self._samples: Deque[Tuple[float, float]] = deque()

    def add(self, ts: float, value: float) -> None:
        self._samples.append((float(ts), float(value)))
        self._trim(float(ts))

    def _trim(self, now: float) -> None:
        cutoff = now - self.window_s
        while self._samples and self._samples[0][0] < cutoff:
            self._samples.popleft()

    def value(self, now: Optional[float] = None) -> float:
        if now is not None:
            self._trim(float(now))
        if not self._samples:
            return 0.0
        return median([v for _t, v in self._samples])

    def ratio(self, v_value: float, now: Optional[float] = None) -> float:
        base = self.value(now)
        if base <= 1e-6:
            # 基线为 0（画面完全静止）：用极小分母避免除零，比值只在有运动时才有意义
            return 0.0 if v_value <= 1e-6 else 99.0
        return v_value / base

    def __len__(self) -> int:
        return len(self._samples)


def aggregate_series(
    samples: Sequence[Tuple[int, float]],
    since: int,
    until: int,
    step: int,
    baseline_window_s: float,
    splash_ratio: float,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """把原始采样分桶成契约 §4 的 series。

    samples 可以包含 since 之前的数据（只用于算基线，不出点）。
    """
    step = max(1, int(step))
    buckets: Dict[int, List[float]] = {}
    for ts, value in samples:
        key = int(ts) - int(ts) % step
        buckets.setdefault(key, []).append(float(value))
    keys = sorted(buckets)
    means = [sum(buckets[k]) / float(len(buckets[k])) for k in keys]
    base_buckets = max(1, int(round(float(baseline_window_s) / step)))
    out: List[Dict[str, Any]] = []
    for idx, key in enumerate(keys):
        if key < since or key > until:
            continue
        lo = max(0, idx - base_buckets)
        history = means[lo:idx]
        if len(history) >= 3:
            base = median(history)
        else:
            # 冷启动：历史不足，用「含当前在内能拿到的全部桶」的中位数兜底
            base = median(means[: idx + 1])
        out.append(
            {
                "ts": int(key),
                "v_value": round(means[idx], 4),
                "baseline": round(base, 4),
                "thr": round(base * float(splash_ratio), 4),
            }
        )
    if limit and limit > 0 and len(out) > limit:
        out = out[-int(limit):]
    return out


class MetricsService:
    """V-Value 采样入库 + 曲线查询 + 供检测器使用的实时基线。"""

    def __init__(self, cfg, store, logger=None) -> None:
        self.cfg = cfg
        self.store = store
        self._log = logger
        self._lock = threading.RLock()
        self._trackers: Dict[str, BaselineTracker] = {}
        self._last_write: Dict[str, float] = {}
        self._sample_s = max(1.0, float(cfg.get("metrics.sample_s", 5) or 5))
        self._baseline_window_s = float(cfg.get("metrics.baseline_window_s", 1800) or 1800)

    # ---------------- 采样 ----------------
    def tracker(self, camera_id: str) -> BaselineTracker:
        with self._lock:
            tracker = self._trackers.get(camera_id)
            if tracker is None:
                tracker = BaselineTracker(self._baseline_window_s)
                self._trackers[camera_id] = tracker
            return tracker

    def preload(self, camera_ids: Sequence[str]) -> None:
        """进程启动时把最近一段历史装回内存，避免重启后基线从 0 开始。"""
        now = int(time.time())
        since = now - int(self._baseline_window_s)
        for cam in camera_ids:
            try:
                for ts, value in self.store.series(cam, since, now):
                    self.tracker(cam).add(ts, value)
            except Exception:
                continue

    def observe(self, camera_id: str, ts: int, v_value: float) -> Dict[str, float]:
        """记录一次 V-Value，返回 {v_value, baseline, ratio, thr}。"""
        tracker = self.tracker(camera_id)
        tracker.add(ts, v_value)
        baseline = tracker.value(ts)
        ratio = tracker.ratio(v_value, ts)
        thr = baseline * float(self.cfg.get("thresholds.splash_ratio", 1.6) or 1.6)
        with self._lock:
            last = self._last_write.get(camera_id, 0.0)
            if ts - last >= self._sample_s:
                self._last_write[camera_id] = float(ts)
                try:
                    self.store.add_metric(camera_id, int(ts), float(v_value))
                except Exception as exc:
                    if self._log:
                        self._log("warn", "metrics", "写入指标失败：%s" % exc)
        return {
            "v_value": round(float(v_value), 4),
            "baseline": round(float(baseline), 4),
            "ratio": round(float(ratio), 3),
            "thr": round(float(thr), 4),
        }

    def baseline(self, camera_id: str) -> float:
        return self.tracker(camera_id).value()

    # ---------------- 查询 ----------------
    def feed_windows(self) -> List[Dict[str, str]]:
        windows = self.cfg.get("feed_windows", []) or []
        out = []
        for item in windows:
            if isinstance(item, dict) and "start" in item and "end" in item:
                out.append({"start": str(item["start"]), "end": str(item["end"])})
        return out

    def series(
        self,
        camera_id: str,
        window: str = "24h",
        step: int = 300,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        window_s = parse_window(window, str(self.cfg.get("metrics.default_window", "24h")))
        step = max(5, int(step or self.cfg.get("metrics.default_step", 300) or 300))
        until = int(time.time())
        since = until - window_s
        samples = self.store.series(camera_id, since - int(self._baseline_window_s), until)
        series = aggregate_series(
            samples,
            since=since,
            until=until,
            step=step,
            baseline_window_s=self._baseline_window_s,
            splash_ratio=float(self.cfg.get("thresholds.splash_ratio", 1.6) or 1.6),
            limit=limit,
        )
        return {
            "window": str(window),
            "step": step,
            "series": series,
            "feed_windows": self.feed_windows(),
        }


class SystemSampler:
    """CPU / 内存 / 温度 / 磁盘剩余（契约 §1 health.pi）。

    采样频率很低（几秒一次），开销可以忽略。
    """

    def __init__(self, data_dir: str, logger=None) -> None:
        self.data_dir = data_dir
        self._log = logger
        self._lock = threading.RLock()
        self._last_cpu: Optional[Tuple[int, int]] = None  # (total, idle)
        self._temp_path: Optional[str] = None
        self._warned: set = set()
        self._psutil = None
        try:
            import psutil  # type: ignore

            self._psutil = psutil
        except Exception:
            self._psutil = None

    def _warn_once(self, key: str, msg: str) -> None:
        if key in self._warned:
            return
        self._warned.add(key)
        note_degraded(key, msg)
        if self._log:
            self._log("warn", "sysmon", msg)

    # ---- CPU ----
    def _cpu_pct(self) -> Optional[float]:
        try:
            with open("/proc/stat", "r", encoding="utf-8") as fh:
                line = fh.readline()
            parts = [int(x) for x in line.split()[1:]]
            idle = parts[3] + (parts[4] if len(parts) > 4 else 0)
            total = sum(parts)
            with self._lock:
                last = self._last_cpu
                self._last_cpu = (total, idle)
            if last is None:
                return None
            d_total = max(1, total - last[0])
            d_idle = max(0, idle - last[1])
            return round(100.0 * (1.0 - d_idle / float(d_total)), 1)
        except Exception:
            pass
        try:
            load = os.getloadavg()[0]
            cpus = os.cpu_count() or 1
            return round(min(100.0, 100.0 * load / cpus), 1)
        except Exception:
            self._warn_once("cpu", "读不到 CPU 使用率（既无 /proc/stat 也无 loadavg）：返回 null")
            return None

    # ---- 内存 ----
    def _mem_pct(self) -> Optional[float]:
        try:
            info: Dict[str, int] = {}
            with open("/proc/meminfo", "r", encoding="utf-8") as fh:
                for line in fh:
                    key, _, rest = line.partition(":")
                    info[key.strip()] = int(rest.strip().split()[0])
            total = info.get("MemTotal", 0)
            avail = info.get("MemAvailable", info.get("MemFree", 0))
            if total:
                return round(100.0 * (total - avail) / float(total), 1)
        except Exception:
            pass
        if self._psutil is not None:
            try:
                return round(float(self._psutil.virtual_memory().percent), 1)
            except Exception:
                pass
        try:  # macOS 兜底：sysctl 总量 + vm_stat 分页
            total = int(
                subprocess.run(
                    ["sysctl", "-n", "hw.memsize"],
                    stdout=subprocess.PIPE,
                    timeout=2,
                    check=False,
                ).stdout.strip()
                or 0
            )
            vm = subprocess.run(
                ["vm_stat"], stdout=subprocess.PIPE, timeout=2, check=False
            ).stdout.decode("utf-8", "replace")
            page = 4096
            match = re.search(r"page size of (\d+) bytes", vm)
            if match:
                page = int(match.group(1))
            free_pages = 0
            for name in ("Pages free", "Pages inactive", "Pages speculative"):
                m = re.search(r"%s:\s+(\d+)" % re.escape(name), vm)
                if m:
                    free_pages += int(m.group(1))
            if total:
                return round(100.0 * (total - free_pages * page) / float(total), 1)
        except Exception:
            pass
        self._warn_once("mem", "读不到内存占用（无 /proc/meminfo、无 psutil）：返回 null")
        return None

    # ---- 温度 ----
    def _temp_c(self) -> Optional[float]:
        if self._temp_path is None:
            candidates = [
                "/sys/class/thermal/thermal_zone0/temp",
                "/sys/class/hwmon/hwmon0/temp1_input",
            ]
            for path in candidates:
                if os.path.exists(path):
                    self._temp_path = path
                    break
            else:
                self._temp_path = ""
        if self._temp_path:
            try:
                with open(self._temp_path, "r", encoding="utf-8") as fh:
                    raw = float(fh.read().strip())
                return round(raw / 1000.0 if raw > 1000 else raw, 1)
            except Exception:
                pass
        if self._psutil is not None:
            try:
                sensors = self._psutil.sensors_temperatures()  # type: ignore[attr-defined]
                for entries in (sensors or {}).values():
                    if entries:
                        return round(float(entries[0].current), 1)
            except Exception:
                pass
        self._warn_once(
            "temp", "读不到 SoC 温度（无 /sys/class/thermal）：health.pi.temp_c 返回 null"
        )
        return None

    # ---- 磁盘 ----
    def _disk_free_gb(self) -> Optional[float]:
        try:
            return round(shutil.disk_usage(self.data_dir).free / float(1024 ** 3), 2)
        except Exception:
            self._warn_once("disk", "读不到磁盘剩余空间：返回 null")
            return None

    def sample(self) -> Dict[str, Any]:
        return {
            "cpu_pct": self._cpu_pct(),
            "mem_pct": self._mem_pct(),
            "temp_c": self._temp_c(),
            "disk_free_gb": self._disk_free_gb(),
        }


__all__ = [
    "BaselineTracker",
    "MetricsService",
    "SystemSampler",
    "aggregate_series",
    "parse_window",
    "median",
]
