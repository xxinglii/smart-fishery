"""投喂停料状态机（纯逻辑，必须能脱离相机离线回放验证）。

它负责这个项目里唯一一个「不用数鱼也能闭环」的判断：
    鱼还抢不抢食？不抢了就停料。

输入只有三个数，全部由 detector 每帧已经算出来，不新增任何采集：
    ratio     摄食强度 = ROI 运动像素占比 / 平时基线（比平时"吵"几倍）
    v_value   原始运动像素占比（只用于留证据）
    baseline  当前基线值

刻意不做的事：
- 不发 MQTT、不写库、不抓图。只返回状态跃迁，由 app.py 决定怎么落地。
- 不猜。基线没预热好就拒绝判定（ready=False），而不是拿 0 当分母除出个 99 倍。
- 不听 splash_activity 事件。那个事件只在强度"上去"时发一次并进 120s 冷却，
  从不表达"下来了"，而饱食点恰恰是回落。

五个状态：
    IDLE ──start()──▶ ARMED ──ratio≥gorge_ratio 持续──▶ GORGE
                        │                                 │
                        │ 等不到响应只告警，不自动停         │ ratio < stop_ratio
                        ▼                                 ▼
                     （保持 ARMED）                     SETTLE
                                                          │ ratio≥stop 回来 → GORGE
                                                          │ 安静持续 hold_s → STOPPED
                                                          │ 累计 max_gorge_s → STOPPED
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

IDLE = "idle"
ARMED = "armed"
GORGE = "gorge"
SETTLE = "settle"
STOPPED = "stopped"

STATE_LABELS: Dict[str, str] = {
    IDLE: "未投喂",
    ARMED: "已投料·等响应",
    GORGE: "抢食中",
    SETTLE: "动静回落·观察中",
    STOPPED: "已判停料",
}

# 停料原因 -> 人话
REASON_LABELS: Dict[str, str] = {
    "satiety": "摄食强度持续回落到停料线以下（判为吃饱）",
    "timeout": "抢食时间超过上限（兜底停，防画面卡在高峰值）",
    "window_closed": "投喂窗口结束",
    "manual": "人工停料",
    "no_response": "投料后始终没有摄食响应（可能没鱼、料撒偏或画面失焦）",
    "baseline_unready": "基线未预热，本轮不做自动判定",
}


@dataclass
class Transition:
    """一次状态跃迁。纯数据，不含 I/O。"""

    ts: int
    frm: str
    to: str
    reason: str
    label: str
    metric: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ts": int(self.ts),
            "from": self.frm,
            "to": self.to,
            "reason": self.reason,
            "label": self.label,
            "metric": dict(self.metric),
        }


class FeedingFSM:
    """单相机单次投喂的状态机。用完即弃，下一次投喂重新 start()。"""

    def __init__(self, cfg: Optional[Dict[str, Any]] = None) -> None:
        c = dict(cfg or {})
        self.gorge_ratio = float(c.get("gorge_ratio", 1.6))
        self.stop_ratio = float(c.get("stop_ratio", 1.2))
        self.gorge_confirm_s = float(c.get("gorge_confirm_s", 8))
        self.hold_s = float(c.get("hold_s", 30))
        self.max_gorge_s = float(c.get("max_gorge_s", 1800))
        self.arm_timeout_s = float(c.get("arm_timeout_s", 300))
        self.observe_after_s = float(c.get("observe_after_s", 60))
        if self.stop_ratio >= self.gorge_ratio:
            raise ValueError(
                "stop_ratio(%.2f) 必须小于 gorge_ratio(%.2f)：两者之间是迟滞带，"
                "重合或倒置会让阈值附近的抖动直接触发停料" % (self.stop_ratio, self.gorge_ratio)
            )

        self.state = IDLE
        self.session_start: Optional[int] = None
        self.gorge_start: Optional[int] = None
        self.settle_start: Optional[int] = None
        self.stop_ts: Optional[int] = None
        self.stop_reason: Optional[str] = None

        self._pause_started: Optional[int] = None
        self._pause_total = 0.0
        self._pause_reason: str = ""

        self.peak_ratio = 0.0
        self.last_ratio = 0.0
        self.samples = 0
        self.ticked = 0
        # 停料后观察期的累积值（用于事后对账"这次停对了没"）
        self._obs_sum = 0.0
        self._obs_n = 0

    # ------------------------------------------------------------------
    # 计时：暂停 = 时间轴平移（所有起点后移），而不是从 duration 里减累计值
    # ------------------------------------------------------------------
    def _elapsed(self, ts: int, since: Optional[int]) -> float:
        if since is None:
            return 0.0
        if self._pause_started is not None:
            return max(0.0, float(self._pause_started - since))
        return max(0.0, float(ts - since))

    def _transition(self, ts: int, to: str, reason: str, metric: Optional[Dict[str, Any]] = None) -> Transition:
        frm = self.state
        self.state = to
        m = {
            "from": frm,
            "to": to,
            "ratio": round(float(self.last_ratio), 3),
            "peak_ratio": round(float(self.peak_ratio), 3),
            "held_s": int(self._elapsed(ts, self.session_start)),
            "samples": int(self.ticked),
        }
        if metric:
            m.update(metric)
        return Transition(
            ts=int(ts),
            frm=frm,
            to=to,
            reason=reason,
            label=REASON_LABELS.get(reason, reason),
            metric=m,
        )

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------
    def start(self, ts: int, ready: bool = True) -> Optional[Transition]:
        """投喂窗口开始。ready=False 表示基线没预热好，本轮直接标为不判定。"""
        if self.state in (ARMED, GORGE, SETTLE):
            return None
        self.session_start = int(ts)
        self.gorge_start = None
        self.settle_start = None
        self.stop_ts = None
        self.stop_reason = None
        self.peak_ratio = 0.0
        self.last_ratio = 0.0
        self.ticked = 0
        self._pause_started = None
        self._pause_total = 0.0
        self._obs_sum = 0.0
        self._obs_n = 0
        if not ready:
            self.stop_ts = int(ts)
            self.stop_reason = "baseline_unready"
            return self._transition(ts, STOPPED, "baseline_unready")
        return self._transition(ts, ARMED, "window_opened")

    def pause(self, ts: int, reason: str = "ptz") -> None:
        """暂停计时（云台转动、相机掉线、夜间降级路径）。"""
        if self._pause_started is None:
            self._pause_started = int(ts)
            self._pause_reason = str(reason)

    def resume(self, ts: int) -> None:
        if self._pause_started is None:
            return
        dur = max(0, int(ts) - self._pause_started)
        self._pause_total += dur
        # 时间轴平移：把三个计时起点一起后移 dur 秒，等价于「暂停期间时钟停摆」。
        # 这样无论 settle_start 是在暂停前还是暂停后设的，都不会被重复扣减。
        for attr in ("session_start", "gorge_start", "settle_start"):
            value = getattr(self, attr)
            if value is not None:
                setattr(self, attr, value + dur)
        self._pause_started = None
        self._pause_reason = ""

    @property
    def paused(self) -> bool:
        return self._pause_started is not None

    # ------------------------------------------------------------------
    # 每帧喂一次
    # ------------------------------------------------------------------
    def tick(
        self,
        ts: int,
        ratio: float,
        v_value: float = 0.0,
        baseline: float = 0.0,
        ready: bool = True,
    ) -> Optional[Transition]:
        self.ticked += 1
        self.samples = self.ticked
        self.last_ratio = float(ratio)

        if self.state in (IDLE, STOPPED):
            if self.state == STOPPED and self.stop_reason == "satiety":
                self._obs_sum += float(ratio)
                self._obs_n += 1
            return None
        if self.paused or not ready:
            return None

        if self.state == ARMED:
            if ratio >= self.gorge_ratio:
                if self.gorge_start is None:
                    self.gorge_start = int(ts)
                if self._elapsed(ts, self.gorge_start) >= self.gorge_confirm_s:
                    self.peak_ratio = max(self.peak_ratio, float(ratio))
                    return self._transition(ts, GORGE, "gorge_detected")
            else:
                self.gorge_start = None
                if self._elapsed(ts, self.session_start) >= self.arm_timeout_s:
                    # 只告警，不自动停：可能只是鱼还没发现料，窗口结束会兜底。
                    # 这里若直接停料，一次画面失焦就会把整轮投喂掐掉。
                    elapsed = self._elapsed(ts, self.session_start)
                    self.session_start = int(ts)  # 重置，避免每帧重复告警
                    return self._transition(ts, ARMED, "no_response", {"waited_s": int(elapsed)})
            return None

        if self.state == GORGE:
            self.peak_ratio = max(self.peak_ratio, float(ratio))
            if ratio < self.stop_ratio:
                self.settle_start = int(ts)
                return self._transition(ts, SETTLE, "settle_begin")
            if self._elapsed(ts, self.session_start) >= self.max_gorge_s:
                self.stop_ts = int(ts)
                self.stop_reason = "timeout"
                return self._transition(ts, STOPPED, "timeout")
            return None

        if self.state == SETTLE:
            if ratio >= self.stop_ratio:
                quiet = self._elapsed(ts, self.settle_start)
                self.settle_start = None
                return self._transition(ts, GORGE, "gorge_resumed", {"quiet_s": int(quiet)})
            if self.settle_start is None:
                self.settle_start = int(ts)
            if self._elapsed(ts, self.settle_start) >= self.hold_s:
                self.stop_ts = int(ts)
                self.stop_reason = "satiety"
                return self._transition(ts, STOPPED, "satiety", {"quiet_s": int(self.hold_s)})
            if self._elapsed(ts, self.session_start) >= self.max_gorge_s:
                self.stop_ts = int(ts)
                self.stop_reason = "timeout"
                return self._transition(ts, STOPPED, "timeout")
            return None

        return None

    # ------------------------------------------------------------------
    def close(self, ts: int) -> Optional[Transition]:
        """投喂窗口结束。返回本轮的结算（含停料后观察期均值），供事后对账。"""
        if self.state == IDLE:
            return None
        frm = self.state
        obs_avg = round(self._obs_sum / self._obs_n, 3) if self._obs_n else None
        self.state = IDLE
        return Transition(
            ts=int(ts),
            frm=frm,
            to=IDLE,
            reason="window_closed",
            label=REASON_LABELS["window_closed"],
            metric={
                "stopped_at": self.stop_ts,
                "stop_reason": self.stop_reason,
                "peak_ratio": round(float(self.peak_ratio), 3),
                "samples": int(self.ticked),
                "after_stop_ratio_avg": obs_avg,
                "after_stop_samples": int(self._obs_n),
            },
        )

    def snapshot(self) -> Dict[str, Any]:
        """给 API / 前端用的实时状态。"""
        return {
            "state": self.state,
            "state_label": STATE_LABELS.get(self.state, self.state),
            "paused": self.paused,
            "pause_reason": self._pause_reason,
            "last_ratio": round(float(self.last_ratio), 3),
            "peak_ratio": round(float(self.peak_ratio), 3),
            "stop_ts": self.stop_ts,
            "stop_reason": self.stop_reason,
            "samples": int(self.ticked),
        }


__all__ = [
    "FeedingFSM",
    "Transition",
    "STATE_LABELS",
    "REASON_LABELS",
    "IDLE",
    "ARMED",
    "GORGE",
    "SETTLE",
    "STOPPED",
]
