"""回放对比：投喂期「冻结基线」与「不冻结基线」，停料判定差多少。

这个脚本回答的是本项目最容易被忽略的一个坑：
    基线是 1800 s 滚动中位数；一次投喂 20 分钟。
    不冻结的话，投喂期的高峰值会滚进基线窗口，把"平时"抬到接近峰值，
    ratio = v_value / baseline 自己塌回 1.0 —— 判据把自己算死。

用法：
    python3 tools/replay_feeding.py

输入是合成的 V-Value 序列（量级按现场估：平时 1.8% 像素在动，峰值 2.6 倍），
不含任何现场数据。它验证的是「基线机制」而不是「阈值准不准」——
阈值准不准只能靠真塘口对账，脚本给不了。
"""

from __future__ import annotations

import math
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from yutang_vision.feeding_fsm import STOPPED, FeedingFSM  # noqa: E402
from yutang_vision.metrics import BaselineTracker  # noqa: E402

PRE_S = 1800.0      # 预热：模拟系统已跑满一个基线窗口
DURATION = 2400.0   # 回放总时长
DT = 2.0            # 采样步长（中位数对采样率不敏感；2 s 足够跑完且快）
CALM = 0.018        # 平时 ROI 运动像素占比
PEAK = 2.6          # 峰值 / 平时
TAU = 635.0         # 衰减时间常数：料落水 1320 s 后 ratio 正好回到 1.2
RISE_S = 120.0      # 料落水到鱼群围上来的滞后
NOISE = 0.06        # 相对噪声（水面自然波动、光照抖动）

FSM_CFG = {
    "gorge_ratio": 1.6,
    "stop_ratio": 1.2,
    "gorge_confirm_s": 8,
    "hold_s": 30,
    "max_gorge_s": 1800,
    "arm_timeout_s": 300,
}


def v_value_at(t: float, rng: random.Random) -> float:
    if t < RISE_S:
        ratio = 1.02
    else:
        ratio = 1.0 + (PEAK - 1.0) * math.exp(-(t - RISE_S) / TAU)
    return CALM * ratio * (1.0 + rng.gauss(0.0, NOISE))


def replay(freeze: bool, fsm_cfg=None):
    """跑一遍。freeze=True 表示投喂开始时锁基线（改后的行为）。"""
    rng = random.Random(20261112)
    tracker = BaselineTracker(1800.0)
    fsm = FeedingFSM(fsm_cfg or FSM_CFG)

    # ---- 预热：投喂开始前已经在跑的 30 分钟 ----
    t = -PRE_S
    while t < 0:
        tracker.add(t, v_value_at(-1e9, rng))
        t += DT

    fsm.start(0)
    if freeze:
        frozen_base = tracker.freeze(0)

    trace = []
    stop = None
    t = 0.0
    while t <= DURATION + 1e-9:
        v = v_value_at(t, rng)
        tracker.add(t, v)
        baseline = tracker.value(t)
        ratio = tracker.ratio(v, t)
        tr = fsm.tick(int(t), ratio, v_value=v, baseline=baseline, ready=True)
        if tr is not None and tr.to == STOPPED and stop is None:
            stop = (int(t), tr.reason, dict(tr.metric))
        if abs(t % 300.0) < 1e-6:
            trace.append((int(t), v, baseline, ratio))
        t += DT

    return {
        "freeze": freeze,
        "frozen_base": frozen_base if freeze else None,
        "stop": stop,
        "trace": trace,
        "skipped": tracker.skipped,
    }


def fmt_min(sec) -> str:
    return "%.1f min" % (sec / 60.0) if sec is not None else "—"


def main() -> int:
    print("=" * 78)
    print("投喂停料判据 · 基线冻结回放对比（合成序列，非现场数据）")
    print("=" * 78)
    print("序列设定：平时 V-Value=%.3f，峰值 %.1f×，料落水 %d s 后开始衰减"
          % (CALM, PEAK, int(RISE_S)))
    print("判定阈值：停料线 %.2f×，需连续 %d s 安静；抢食门槛 %.2f×"
          % (FSM_CFG["stop_ratio"], FSM_CFG["hold_s"], FSM_CFG["gorge_ratio"]))
    print()

    a = replay(freeze=False)
    b = replay(freeze=True)

    print("%-6s %-10s %-10s %-10s" % ("时刻", "不冻结 ratio", "冻结 ratio", "说明"))
    print("-" * 78)
    for (ta, va, ba, ra), (tb, vb, bb, rb) in zip(a["trace"], b["trace"]):
        note = ""
        if ra < FSM_CFG["stop_ratio"] <= rb:
            note = "← 不冻结已跌破停料线，冻结还在线上"
        print("%-6s %-12.2f %-12.2f %s" % ("%d s" % ta, ra, rb, note))

    print()
    print("-" * 78)
    for row in (a, b):
        name = "不冻结（改前）" if not row["freeze"] else "冻结（改后）"
        if row["stop"]:
            ts, reason, m = row["stop"]
            print("%-16s 停料于 %-12s 原因 %-8s 峰值 %.2f×"
                  % (name, fmt_min(ts), reason, m.get("peak_ratio") or 0))
        else:
            print("%-16s 整轮未停料" % name)

    if a["stop"] and b["stop"]:
        delta = (b["stop"][0] - a["stop"][0]) / 60.0
        print()
        print("差值：不冻结提前 %.1f 分钟停料 —— 这 %.1f 分钟的料是白投的，"
              % (delta, delta))
        print("      而且此时鱼正在抢食（真实 ratio 仍 > 1.6×），系统却认为它吃饱了。")
    print()
    print("冻结期丢弃的高峰样本：%d 个（这些样本若进基线，会永久污染后续判定）"
          % b["skipped"])

    # ---- 阈值敏感度：stop_ratio 调错一天的代价 ----
    print()
    print("-" * 78)
    print("停料线敏感度（冻结基线，其余参数不变）")
    print("-" * 78)
    for sr in (1.10, 1.15, 1.20, 1.25, 1.30, 1.40):
        cfg = dict(FSM_CFG, stop_ratio=sr)
        row = replay(freeze=True, fsm_cfg=cfg)
        if row["stop"]:
            ts = row["stop"][0]
            print("  stop_ratio=%.2f  ->  %-10s （比 %.2f 早/晚 %+.1f min）"
                  % (sr, fmt_min(ts), 1.20, (ts - b["stop"][0]) / 60.0 if b["stop"] else 0))
        else:
            print("  stop_ratio=%.2f  ->  整轮不停（判据被架空，等于没有停料控制）" % sr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
