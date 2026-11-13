"""接线冒烟测试：在模拟模式下真跑一遍 Runtime，确认状态机被真正启动。

单元测试只证明状态机逻辑对；这个脚本证明 app.py 里的接线是通的：
    投喂窗口打开 -> 冻结基线 -> 启动状态机 -> 每帧喂 ratio -> 窗口关闭 -> 结算事件入库

不需要相机、不联网。跑法：
    python3 tests/smoke_feeding_runtime.py
"""

from __future__ import annotations

import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from yutang_vision.app import Runtime  # noqa: E402
from yutang_vision.config import Config  # noqa: E402

WAIT_S = 18.0


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="yutang-smoke-")
    cfg = Config(path=os.path.join(tmp, "config.yaml"))
    # 注意：cfg.update() 只接受契约 6 键（feed_windows/thresholds/capture/upload/record/patrol），
    # 传 feeding_control 进去会被整包拒绝（连合法的键一起丢）。所以非契约段直接写 data。
    ok, errs = cfg.update(
        {
            "patrol": {"on": False},
            # 全天都是投喂窗口，保证起来就在窗口内
            "feed_windows": [{"start": "00:00", "end": "23:59"}],
        }
    )
    if not ok:
        print("配置更新失败：", errs)
        return 1
    cfg.data.setdefault("feeding_control", {}).update({"enabled": True, "shadow_mode": True})
    runtime = Runtime(cfg, simulate=True, force_ptz_mock=True)
    runtime.start()
    print("Runtime 已启动（simulate=True），等待 %.0f s 让检测循环跑起来……" % WAIT_S)
    time.sleep(WAIT_S)

    ok = True
    snap = runtime.feeding_snapshot()
    print()
    print("窗口内：", snap["in_feed_window"], " shadow：", snap["shadow_mode"])
    for cam in runtime.cameras.cameras:
        fsm = snap["cameras"].get(cam.id)
        sig = snap["cameras"].get(cam.id + ":signal")
        frozen = runtime.metrics.baseline_frozen(cam.id)
        print("-" * 70)
        print("相机 %s" % cam.id)
        print("  基线冻结   :", frozen, "（值 %.5f）" % runtime.metrics.baseline(cam.id))
        print("  状态机     :", (fsm or {}).get("state_label"), " 状态码", (fsm or {}).get("state"))
        print("  当前 ratio :", (fsm or {}).get("last_ratio"))
        print("  信号       :", sig)
        if not frozen:
            print("  !! 基线未冻结")
            ok = False
        if not fsm or fsm["state"] == "idle":
            print("  !! 状态机未被启动")
            ok = False

    # 窗口关闭 -> 应产生一条结算事件入库
    runtime._on_feed_window_edge(False, int(time.time()))
    time.sleep(0.5)
    rows = [e for e in runtime.store.list_events(limit=200) if e["type"] == "feeding_stop"]
    print()
    print("窗口关闭后 feeding_stop 事件数：", len(rows))
    for e in rows:
        print("  [%s] %s | %s" % (e["severity"], e["title"], e["detail"]))
    if not rows:
        print("  !! 没有产生结算事件")
        ok = False

    runtime.stop()
    print()
    print("结果：", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
