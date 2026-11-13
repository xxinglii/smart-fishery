"""投喂停料状态机单元测试：不接相机、不联网、不写库、不依赖 pytest。

跑法：
    python3 tests/test_feeding_fsm.py        # 直接跑，打印逐项结果
    python3 -m pytest tests/test_feeding_fsm.py -q

为什么要单独测：这套判据的阈值（1.2× / 30 s）是经验值，没有文献能给出
"鲤鱼饱食时正好是 1.2 倍"。所以状态机必须能脱离现场、用录下来的 V-Value 序列
反复回放，否则现场每次调参都得等一次投喂。
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from yutang_vision.feeding_fsm import (  # noqa: E402
    ARMED,
    GORGE,
    IDLE,
    SETTLE,
    STOPPED,
    FeedingFSM,
)

BASE_CFG = {
    "gorge_ratio": 1.6,
    "stop_ratio": 1.2,
    "gorge_confirm_s": 8,
    "hold_s": 30,
    "max_gorge_s": 1800,
    "arm_timeout_s": 300,
}


def run(fsm: FeedingFSM, t0: float, t1: float, ratio_at, step: float = 0.2):
    """按 5 fps 回放：ts 取整秒，同一秒会 tick 多次（与现场一致）。"""
    out = []
    t = float(t0)
    while t <= t1:
        tr = fsm.tick(int(t), ratio_at(t))
        if tr is not None:
            out.append((int(t), tr))
        t += step
    return out


# --------------------------------------------------------------------------
def test_normal_satiety():
    """正常一轮：料落水 2 min 后抢食，之后指数衰减，约 24 min 跌破 1.2。"""
    fsm = FeedingFSM(BASE_CFG)
    fsm.start(0)

    def ratio_at(t: float) -> float:
        if t < 120:
            return 1.05
        # tau=635：料落水后 1320 s（22 min）时 ratio 正好降到 1.2
        return 1.0 + 1.6 * (2.718281828 ** (-(t - 120.0) / 635.0))

    out = run(fsm, 0, 1800, ratio_at)
    reasons = [tr.reason for _ts, tr in out]
    stop = [x for x in out if x[1].to == STOPPED]

    assert "gorge_detected" in reasons, reasons
    assert "settle_begin" in reasons, reasons
    assert stop, "应产生停料判定"
    ts, tr = stop[0]
    assert tr.reason == "satiety", tr.reason
    # 1440 s 跌破 1.2，再持续 30 s -> 应落在 1440~1500 之间
    assert 1435 <= ts <= 1505, "停料时刻 %d s 不在预期区间（约 1470 s）" % ts
    assert fsm.state == STOPPED
    return "第 %d s 判停（%.1f min），峰值 %.2f×" % (ts, ts / 60.0, tr.metric["peak_ratio"])


def test_jitter_no_stop():
    """阈值附近抖动不该触发停料：ratio 在 1.21~1.30 之间来回。"""
    fsm = FeedingFSM(BASE_CFG)
    fsm.start(0)
    seq = [2.5] * 100 + [1.21, 1.30, 1.22, 1.28, 1.25, 1.24] * 200

    def ratio_at(t: float) -> float:
        idx = min(int(t / 0.2), len(seq) - 1)
        return seq[idx]

    out = run(fsm, 0, 1100, ratio_at)
    assert not [x for x in out if x[1].to == STOPPED], "1.21 以上不应判停"
    return "1100 s 抖动未误停"


def test_real_dip_still_stops():
    """真掉下去就得停：1.21 抖动之后再压到 1.05，仍要停。"""
    fsm = FeedingFSM(BASE_CFG)
    fsm.start(0)

    def ratio_at(t: float) -> float:
        if t < 300:
            return 2.6
        if t < 600:
            return 1.25
        return 1.05

    out = run(fsm, 0, 900, ratio_at)
    stop = [x for x in out if x[1].to == STOPPED]
    assert stop, "压到 1.05 应判停"
    ts, tr = stop[0]
    assert tr.reason == "satiety"
    assert 625 <= ts <= 645, "停料时刻 %d s（应为 600+30）" % ts
    return "第 %d s 判停" % ts


def test_hysteresis_reentry():
    """SETTLE 中又抢起来 -> 回到 GORGE，安静计时清零。"""
    fsm = FeedingFSM(BASE_CFG)
    fsm.start(0)
    run(fsm, 0, 200, lambda t: 2.6)
    assert fsm.state == GORGE
    run(fsm, 200, 215, lambda t: 1.1)
    assert fsm.state == SETTLE
    out = run(fsm, 215, 230, lambda t: 1.45)
    assert fsm.state == GORGE, out
    assert any(tr.reason == "gorge_resumed" for _ts, tr in out)
    return "回落 15 s 后又抢起来，正确撤销停料"


def test_timeout_guard():
    """画面卡在高峰值也得停：抢食累计超过 max_gorge_s 兜底。"""
    cfg = dict(BASE_CFG, max_gorge_s=600)
    fsm = FeedingFSM(cfg)
    fsm.start(0)
    out = run(fsm, 0, 900, lambda t: 2.9)
    stop = [x for x in out if x[1].to == STOPPED]
    assert stop, "超时应兜底停料"
    ts, tr = stop[0]
    assert tr.reason == "timeout"
    assert 595 <= ts <= 620, ts
    return "第 %d s 超时兜底停" % ts


def test_pause_does_not_count_as_quiet():
    """云台转动期间不能算「安静」：暂停 300 s 后不应立刻判停。"""
    fsm = FeedingFSM(BASE_CFG)
    fsm.start(0)
    run(fsm, 0, 200, lambda t: 2.6)
    assert fsm.state == GORGE
    fsm.pause(200, "ptz")
    out = run(fsm, 200, 500, lambda t: 0.9)  # 转台期间画面全黑，ratio 很低
    assert not out, "暂停期不应产生任何跃迁"
    fsm.resume(500)
    out = run(fsm, 500, 560, lambda t: 0.9)
    stop = [x for x in out if x[1].to == STOPPED]
    assert stop and stop[0][0] >= 530, "恢复后应重新计满 30 s，而不是立刻停"
    return "暂停 300 s 被正确剔除，恢复后第 %d s 才停" % stop[0][0]


def test_baseline_unready_blocks_judgement():
    """基线没预热好就直接拒绝判定，不能拿 0 当分母除出 99 倍。"""
    fsm = FeedingFSM(BASE_CFG)
    tr = fsm.start(0, ready=False)
    assert tr is not None and tr.to == STOPPED and tr.reason == "baseline_unready"
    for t in range(0, 100):
        assert fsm.tick(t, 99.0) is None
    assert fsm.state == STOPPED
    return "基线未就绪 -> 本轮不出建议（而非报错或误判）"


def test_no_response_warns_but_keeps_feeding():
    """投料后完全没响应：只告警，不自动停（可能只是鱼没发现料）。"""
    fsm = FeedingFSM(BASE_CFG)
    fsm.start(0)
    out = run(fsm, 0, 320, lambda t: 1.02)
    warns = [x for x in out if x[1].reason == "no_response"]
    assert warns, "应在 arm_timeout_s 后告警"
    assert warns[0][0] == 300, warns[0][0]
    assert fsm.state == ARMED, "告警后仍应继续等响应，不得停料"
    assert not [x for x in out if x[1].to == STOPPED]
    return "第 %d s 告警，状态保持 ARMED 未停料" % warns[0][0]


def test_invalid_threshold_rejected():
    """stop_ratio >= gorge_ratio 会让迟滞带消失，必须建对象时就拒绝。"""
    for bad in ({"gorge_ratio": 1.2, "stop_ratio": 1.2}, {"gorge_ratio": 1.2, "stop_ratio": 1.4}):
        try:
            FeedingFSM(bad)
        except ValueError:
            continue
        raise AssertionError("非法阈值未被拒绝：%s" % bad)
    return "阈值倒置/重合被拒"


def test_close_reports_after_stop_average():
    """窗口结束时给出「停料后均值」，这是判断停早了还是停晚了的唯一依据。"""
    fsm = FeedingFSM(BASE_CFG)
    fsm.start(0)
    run(fsm, 0, 200, lambda t: 2.6)
    run(fsm, 200, 260, lambda t: 1.05)
    assert fsm.state == STOPPED
    run(fsm, 260, 300, lambda t: 1.02)
    tr = fsm.close(300)
    assert tr is not None and tr.reason == "window_closed"
    assert tr.metric["after_stop_ratio_avg"] is not None
    assert 1.0 <= tr.metric["after_stop_ratio_avg"] <= 1.5
    assert fsm.state == IDLE
    return "停料后均值 %.2f×（%d 个样本）" % (
        tr.metric["after_stop_ratio_avg"],
        tr.metric["after_stop_samples"],
    )


TESTS = [
    ("正常饱食判定", test_normal_satiety),
    ("阈值抖动不误停", test_jitter_no_stop),
    ("真回落必停", test_real_dip_still_stops),
    ("迟滞回退", test_hysteresis_reentry),
    ("抢食超时兜底", test_timeout_guard),
    ("暂停不计入安静时长", test_pause_does_not_count_as_quiet),
    ("基线未就绪拒绝判定", test_baseline_unready_blocks_judgement),
    ("无响应只告警不停料", test_no_response_warns_but_keeps_feeding),
    ("非法阈值拒绝", test_invalid_threshold_rejected),
    ("窗口结算含停料后均值", test_close_reports_after_stop_average),
]


def run_all() -> int:
    passed = failed = 0
    width = max(len(name) for name, _ in TESTS) + 2
    print("=" * 78)
    print("投喂停料状态机 · 单元测试")
    print("=" * 78)
    for name, fn in TESTS:
        try:
            msg = fn()
            print("PASS %-*s  %s" % (width, name, msg or ""))
            passed += 1
        except AssertionError as exc:
            print("FAIL %-*s  %s" % (width, name, exc))
            failed += 1
        except Exception as exc:  # noqa: BLE001
            print("ERROR %-*s  %s: %s" % (width - 1, name, type(exc).__name__, exc))
            failed += 1
    print("-" * 78)
    print("通过 %d / %d，失败 %d" % (passed, passed + failed, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(run_all())
