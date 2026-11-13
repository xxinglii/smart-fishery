# -*- coding: utf-8 -*-
"""状态机两个边界的实测：低帧率误停、停料线附近抖动。

这两个不是"理论风险"，是当前实现（feeding_fsm.py）在特定输入下会真的出错。
本脚本只读状态机，不改它。
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yutang_vision import feeding_fsm as F


def make(hold_s=30, stop_ratio=1.20, gorge_ratio=1.60):
    fsm = F.FeedingFSM({"stop_ratio": stop_ratio, "hold_s": hold_s,
                        "gorge_ratio": gorge_ratio})
    fsm.start(0)
    return fsm


def drive(fsm, ts0, ts1, dt, ratio_fn):
    """按固定步长喂，返回首个"停料"跃迁（若无则 None）。"""
    t = ts0
    while t <= ts1:
        tr = fsm.tick(int(t), ratio_fn(t))
        if tr is not None and tr.reason in ("satiety", "timeout"):
            return t, tr.reason
        t += dt
    return None, None


def exp_gorge():
    """先让状态机进入 GORGE，再返回时刻。"""
    fsm = make()
    t = 0
    while t < 60:
        tr = fsm.tick(int(t), 2.5)
        if tr is not None and tr.to == F.GORGE:
            return fsm, t + 1
        t += 1
    raise RuntimeError("没能进入 GORGE")


def case_low_fps():
    print("=" * 62)
    print("案例 A：帧率掉到 0.2 fps（4G 抖动 / 相机卡顿），水面其实一直在响")
    print("=" * 62)
    print("设定：ratio 恒为 1.10（全部低于停料线 1.2），但只有 0.2 帧/秒")
    print()
    for dt in (0.2, 1.0, 5.0):
        fsm, t0 = exp_gorge()
        ts, why = drive(fsm, t0, t0 + 3000, dt, lambda t: 1.10)
        n = int((ts - t0) / dt) if ts else 0
        fps = 1.0 / dt
        print("  %.1f fps：%s，期间只采到 %d 个样本"
              % (fps, ("第 %.0f 秒判定停料（%s）" % (ts - t0, why)) if ts else "未停", n))
    print()
    print("  说明：判据只看\"时间过了 30 秒\"，不看\"采到几个样本\"。")
    print("        单帧低于阈值的概率按 0.7 估，全部命中的概率：")
    print("          1 fps  × 30 帧  = 0.7^30  = %.2e" % (0.7 ** 30))
    print("          0.2fps ×  6 帧  = 0.7^6   = %.2f  ← 约每 8 次抖动就误停一次" % (0.7 ** 6))
    print()


def case_hysteresis():
    print("=" * 62)
    print("案例 B：带噪声的衰减曲线（真实水面必然如此）")
    print("=" * 62)
    print("设定：均值从 2.4 指数衰减到 1.0，时间常数 400 秒，叠加 σ=0.08 高斯噪声，1 fps")
    print()
    import random
    import math

    def trace(seed=20261112):
        rng = random.Random(seed)
        out = []
        for t in range(0, 3600):
            mu = 1.0 + 1.4 * math.exp(-t / 400.0)
            out.append(mu + rng.gauss(0, 0.08))
        return out

    series = trace()
    true_1p2 = next(t for t, r in enumerate(series) if r < 1.20)
    print("  第一次跌破 1.2 发生在第 %d 秒（%0.1f 分钟）" % (true_1p2, true_1p2 / 60))

    # 当前实现
    fsm, t0 = exp_gorge()
    ts, why = drive(fsm, t0, t0 + 3600, 1.0, lambda t: series[min(int(t - t0), len(series) - 1)])
    if ts is None:
        print("  当前实现（要求连续 30 秒每帧都低于 1.2）：**一直没停**")
        print("    → 靠 1800 秒超时兜底，比第一次跌破晚 %.1f 分钟"
              % ((1800 - true_1p2) / 60))
    else:
        print("  当前实现：第 %.1f 分钟才停（比第一次跌破晚 %.1f 分钟）"
              % ((ts - t0) / 60, (ts - t0 - true_1p2) / 60))
    print()

    # 候选方案：窗口占比
    print("  候选方案（最近 90 秒内低于 1.2 的样本占比 ≥ 阈值即判停）：")
    for need in (0.75, 0.80, 0.90):
        hist = []
        hit = None
        for t in range(0, 3600):
            hist.append(series[t])
            if len(hist) > 90:
                hist.pop(0)
            if len(hist) == 90:
                frac = sum(1 for v in hist if v < 1.20) / 90
                if frac >= need:
                    hit = t
                    break
        if hit is None:
            print("    占比 ≥ %.0f%%：未判停" % (need * 100))
        else:
            print("    占比 ≥ %.0f%%：第 %.1f 分钟判停（比第一次跌破晚 %.1f 分钟）"
                  % (need * 100, hit / 60, (hit - true_1p2) / 60))
    print()
    print("  说明：噪声下\"每帧都低于 1.2\"几乎不可能连续成立，")
    print("        而\"窗口内大部分低于 1.2\"是稳定可判的。")
    print()


def case_override():
    print("=" * 62)
    print("案例 C：人工覆盖入口")
    print("=" * 62)
    has = hasattr(F.FeedingFSM, "override")
    print("  状态机是否有 override()/hold() 之类的人工介入接口：%s" % ("有" if has else "**没有**"))
    print("  现有接口：%s" % ", ".join(m for m in dir(F.FeedingFSM) if not m.startswith("_")))
    print()
    print("  影响：影子期对账时，如果人不同意机器的判断，只能事后写在纸上；")
    print("        而这些\"人和机器不一致\"的时刻，恰恰是校准阈值最值钱的样本。")
    print()


if __name__ == "__main__":
    case_low_fps()
    case_hysteresis()
    case_override()
