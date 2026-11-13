# -*- coding: utf-8 -*-
"""同一段衰减曲线，跑 200 次不同噪声，比较两种停料判据的稳定性。

判据 A（当前实现）：需要连续 30 个样本（30 秒）每一帧都低于 1.2
判据 B（候选）：最近 90 秒内，低于 1.2 的样本占比 >= 80%

比的不只是"平均早几秒"，而是"稳不稳"：
一个判据如果有时 15 分钟停、有时永远不停，现场就没法用。
"""
import random
import math

STOP = 1.20
HOLD_FRAMES = 30        # A：连续多少帧
WIN = 90                # B：窗口多少帧
NEED = 0.80             # B：窗口内占比门槛
LIMIT = 3600            # 只模拟一小时
SEEDS = 200


def series(seed, sigma=0.08):
    """均值 2.4 -> 1.0 指数衰减（时间常数 400 秒），叠加高斯噪声。"""
    rng = random.Random(seed)
    out = []
    for t in range(LIMIT):
        mu = 1.0 + 1.4 * math.exp(-t / 400.0)
        out.append(mu + rng.gauss(0, sigma))
    return out


def judge_a(xs):
    run = 0
    for i, v in enumerate(xs):
        if i < 60:          # 前 60 秒是抢食期，跳过
            continue
        if v < STOP:
            run += 1
            if run >= HOLD_FRAMES:
                return i
        else:
            run = 0
    return None


def judge_b(xs):
    hits = 0
    for i, v in enumerate(xs):
        if v < STOP:
            hits += 1
        if i >= WIN and xs[i - WIN] < STOP:
            hits -= 1
        if i >= WIN:
            if hits / WIN >= NEED:
                return i
    return None


def stats(name, res, first_break):
    got = [r for r in res if r is not None]
    miss = len(res) - len(got)
    if not got:
        print("  %-10s 全部未判停" % name)
        return
    got_sorted = sorted(got)
    med = got_sorted[len(got_sorted) // 2]
    p10 = got_sorted[int(len(got_sorted) * 0.1)]
    p90 = got_sorted[int(len(got_sorted) * 0.9)]
    print("  %-10s 中位 %5.1f 分 | 最快 %5.1f | 最慢 %5.1f | 未判停 %3d/%d"
          % (name, med / 60, p10 / 60, p90 / 60, miss, len(res)))
    print("  %-10s 相对真实跌破点（%.1f 分）：中位晚 %.1f 分，最快晚 %.1f，最慢晚 %.1f"
          % ("", first_break / 60,
             (med - first_break) / 60,
             (p10 - first_break) / 60,
             (p90 - first_break) / 60))


def main():
    a_res, b_res, breaks = [], [], []
    for s in range(SEEDS):
        xs = series(s)
        breaks.append(next(i for i, v in enumerate(xs) if v < STOP))
        a_res.append(judge_a(xs))
        b_res.append(judge_b(xs))

    fb = sorted(breaks)[len(breaks) // 2]
    print("=" * 68)
    print("200 段带噪声的衰减曲线，均值在 %.1f 分钟跌破 1.2" % (fb / 60))
    print("=" * 68)
    stats("判据 A（现状）", a_res, fb)
    print()
    stats("判据 B（候选）", b_res, fb)
    print()

    a_miss = sum(1 for r in a_res if r is None)
    b_miss = sum(1 for r in b_res if r is None)
    print("关键差别：")
    print("  A 有 %d/%d 次（%.0f%%）在一小时内根本没判停，只能等 30 分钟强制超时兜底。"
          % (a_miss, SEEDS, a_miss / SEEDS * 100))
    print("  B 未判停 %d/%d 次。" % (b_miss, SEEDS))
    print()
    a_ok = [r for r in a_res if r]
    if a_ok:
        spread_a = (max(a_ok) - min(a_ok)) / 60
        print("  A 的停料时刻跨度 %.1f 分钟（最快到最慢）；B 的跨度 %.1f 分钟。"
              % (spread_a,
                 (max(r for r in b_res if r) - min(r for r in b_res if r)) / 60))
    print()
    print("大白话：A 相当于\"要求水面连续半分钟一次都不许晃\"——晃一下就重新数，")
    print("        于是常常永远数不满；B 相当于\"只要最近一分半里大部分时间是静的就行\"。")


if __name__ == "__main__":
    main()
