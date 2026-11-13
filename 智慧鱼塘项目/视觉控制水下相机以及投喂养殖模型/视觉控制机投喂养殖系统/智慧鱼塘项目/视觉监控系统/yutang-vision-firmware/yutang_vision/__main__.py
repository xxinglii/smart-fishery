"""启动入口：`python -m yutang_vision [--simulate] [--config ...]`。

常用：
    python -m yutang_vision --simulate                 # 无相机，假数据流（前端联调）
    python -m yutang_vision --config config.yaml       # 现场默认模式
    python -m yutang_vision --check                    # 只校验配置，不起服务
"""

from __future__ import annotations

import argparse
import os
import signal
import sys
import threading
from typing import List, Optional

from . import __version__, degraded_notes
from .app import Runtime, make_server
from .config import load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m yutang_vision",
        description="鱼塘视觉监控系统 · 树莓派端固件（实现《视觉系统_API契约_v1.md》）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  python -m yutang_vision --simulate                # 无相机，跑假数据流\n"
            "  python -m yutang_vision --config ./config.yaml    # 现场模式\n"
            "  python -m yutang_vision --check                   # 只校验配置\n"
        ),
    )
    parser.add_argument("--config", "-c", default=None, help="配置文件路径（默认 ./config.yaml）")
    parser.add_argument("--host", default=None, help="监听地址（默认取配置 server.host，0.0.0.0）")
    parser.add_argument("--port", "-p", type=int, default=None, help="监听端口（默认取配置 server.port，8080）")
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="模拟模式：不需要相机，生成合规假数据流；health.mode 返回 mock",
    )
    parser.add_argument("--force-ptz-mock", action="store_true", help="即使装了 onvif-zeep 也用本地状态机")
    parser.add_argument("--check", action="store_true", help="只加载并校验配置，然后退出")
    parser.add_argument("--version", action="version", version="yutang-vision %s" % __version__)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    config_path = args.config
    if config_path is None:
        default_path = os.path.join(os.getcwd(), "config.yaml")
        config_path = default_path if os.path.exists(default_path) else None
    cfg = load_config(config_path)

    if args.check:
        print("配置文件：%s" % (cfg.path or "(未指定，使用内置默认值)"))
        if cfg.last_error:
            print("警告：%s" % cfg.last_error)
        import json

        print(json.dumps(cfg.public(), ensure_ascii=False, indent=2))
        for note in degraded_notes():
            print("降级：%s —— %s" % (note["component"], note["reason"]))
        return 0

    runtime = Runtime(cfg, simulate=args.simulate, force_ptz_mock=args.force_ptz_mock)
    host = args.host or str(cfg.get("server.host", "0.0.0.0") or "0.0.0.0")
    port = int(args.port or cfg.get("server.port", 8080) or 8080)

    runtime.start()
    try:
        server = make_server(runtime, host, port)
    except OSError as exc:
        runtime.log("error", "http", "端口 %d 绑定失败：%s" % (port, exc))
        runtime.stop()
        return 2

    actual_host, actual_port = server.server_address[0], server.server_address[1]
    runtime.log(
        "info",
        "http",
        "服务就绪：http://%s:%d/api/v1/health （模式 %s）" % (actual_host, actual_port, runtime.mode),
    )

    def _shutdown(_signum=None, _frame=None):
        runtime.log("info", "shutdown", "收到退出信号，准备停止")
        threading.Thread(target=server.shutdown, daemon=True).start()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _shutdown)
        except Exception:
            pass

    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            server.server_close()
        except Exception:
            pass
        runtime.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
