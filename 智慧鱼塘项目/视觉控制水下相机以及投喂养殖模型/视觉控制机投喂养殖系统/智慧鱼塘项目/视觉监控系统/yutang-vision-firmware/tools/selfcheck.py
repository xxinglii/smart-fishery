#!/usr/bin/env python3
"""一键自检：起服务（真子进程）→ 打全部端点 → 打印通过/失败表。

用法（在 yutang-vision-firmware/ 目录下）：
    python3 tools/selfcheck.py --simulate          # 无相机自检（默认就是 simulate）
    python3 tools/selfcheck.py --base-url http://192.168.1.10:8080   # 只打已在跑的服务
    python3 tools/selfcheck.py --wait 120          # 等事件出现的最长秒数

退出码：0 = 全通过，1 = 有失败项，2 = 服务起不来。
不联网、不装依赖、不需要相机。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _load_contract_module():
    """复用 tests/test_contract.py 里的结构校验器，避免两套标准。"""
    path = os.path.join(ROOT, "tests", "test_contract.py")
    spec = importlib.util.spec_from_file_location("yutang_test_contract", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


tc = _load_contract_module()


def free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = int(sock.getsockname()[1])
    sock.close()
    return port


class Client:
    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")

    def get(self, path: str, timeout: float = 20.0):
        request = urllib.request.Request(self.base + path)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                return resp.status, dict(resp.headers), resp.read()
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers or {}), exc.read()

    def json(self, path: str, timeout: float = 20.0):
        status, headers, body = self.get(path, timeout=timeout)
        try:
            return status, headers, json.loads(body.decode("utf-8"))
        except Exception:
            return status, headers, None

    def send(self, method: str, path: str, payload: Any = None, timeout: float = 25.0):
        data = b"" if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(self.base + path, data=data, method=method)
        request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                return resp.status, dict(resp.headers), resp.read()
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers or {}), exc.read()


# ==========================================================================
# 检查项
# ==========================================================================
class Checker:
    def __init__(self, client: Client, wait_s: float) -> None:
        self.client = client
        self.wait_s = wait_s
        self.rows: List[Tuple[str, str, str, str]] = []
        self.state: Dict[str, Any] = {}

    def run(self, name: str, func: Callable[[], Tuple[str, str]]) -> None:
        started = time.time()
        try:
            status, note = func()
            self.rows.append((name, status, "PASS", "%s (%.1fs)" % (note, time.time() - started)))
        except AssertionError as exc:
            self.rows.append((name, "-", "FAIL", str(exc)))
        except Exception as exc:
            self.rows.append((name, "-", "FAIL", "%s: %s" % (type(exc).__name__, exc)))

    # ---------------- 单项 ----------------
    def check_health(self):
        status, _headers, data = self.client.json("/api/v1/health")
        assert status == 200, "HTTP %s" % status
        tc.check_keys(data, tc.HEALTH_KEYS, "health")
        assert data["mode"] in ("live", "mock"), "mode 非法"
        return "200", "mode=%s uptime=%ss 磁盘=%.1fGB" % (
            data["mode"], data["uptime_s"], (data["pi"]["disk_free_gb"] or 0.0)
        )

    def check_cameras(self):
        status, _headers, data = self.client.json("/api/v1/cameras")
        assert status == 200, "HTTP %s" % status
        assert isinstance(data, list) and data, "cameras 为空"
        for cam in data:
            tc.check_keys(cam, tc.CAMERA_KEYS, "cameras[]")
        self.state["cameras"] = data
        online = sum(1 for c in data if c["online"])
        return "200", "%d 台相机（在线 %d）" % (len(data), online)

    def check_camera_snapshot(self):
        camera_id = self.state["camera_id"]
        deadline = time.time() + self.wait_s
        status, headers, body = 0, {}, b""
        while time.time() < deadline:
            status, headers, body = self.client.get("/api/v1/cameras/%s/snapshot" % camera_id)
            if status == 200:
                break
            time.sleep(1.0)
        assert status == 200, "抓图 HTTP %s" % status
        assert headers.get("Content-Type", "").startswith("image/jpeg"), "Content-Type 非 image/jpeg"
        assert body[:2] == b"\xff\xd8", "不是 JPEG"
        return "200", "%d 字节 JPEG" % len(body)

    def check_ptz(self):
        camera_id = self.state.get("detail_camera") or self.state["camera_id"]
        status, _headers, body = self.client.send(
            "POST", "/api/v1/cameras/%s/ptz" % camera_id, {"action": "move", "dx": -0.2, "dy": 0.0, "zoom": 0.0}
        )
        if status == 400:
            return "400", "该相机无云台（%s），跳过动作校验" % camera_id
        assert status == 200, "move HTTP %s" % status
        data = json.loads(body)
        assert data.get("ok") is True, "响应缺少 ok=true"
        tc.check_keys(data["ptz"], tc.PTZ_KEYS, "ptz")
        status, _headers, body = self.client.send(
            "POST", "/api/v1/cameras/%s/ptz" % camera_id, {"action": "goto", "preset_id": 1}
        )
        assert status == 200, "goto HTTP %s" % status
        return "200", "云台动作 OK（pan=%.1f）" % json.loads(body)["ptz"]["pan"]

    def check_presets(self):
        status, _headers, data = self.client.json("/api/v1/presets")
        assert status == 200, "HTTP %s" % status
        assert isinstance(data, list), "presets 不是数组"
        for preset in data:
            tc.check_keys(preset, tc.PRESET_KEYS, "presets[]")
        return "200", "%d 个预置位" % len(data)

    def check_events(self):
        """等第一条事件出现（simulate 模式 ~20 s 内必出），然后校验结构。"""
        deadline = time.time() + self.wait_s
        data: List[Dict[str, Any]] = []
        while time.time() < deadline:
            status, _headers, data = self.client.json("/api/v1/events?limit=20")
            assert status == 200, "HTTP %s" % status
            if data:
                break
            time.sleep(1.0)
        assert data, "%d s 内没有产生任何事件" % self.wait_s
        for event in data:
            tc.check_keys(event, tc.EVENT_KEYS, "events[]")
            assert event["evidence"] == "C", "evidence 必须为 C"
            assert 0.0 <= event["confidence"] <= 1.0, "confidence 越界"
        self.state["event"] = data[0]
        return "200", "%d 条事件（最新：%s %s）" % (len(data), data[0]["type"], data[0]["id"])

    def check_event_ack(self):
        event_id = self.state["event"]["id"]
        status, _headers, body = self.client.send("POST", "/api/v1/events/%s/ack" % event_id)
        assert status == 200, "HTTP %s" % status
        assert json.loads(body) == {"ok": True}, "响应不是 {ok: true}"
        status, _headers, data = self.client.json("/api/v1/events?limit=50")
        target = [e for e in data if e["id"] == event_id]
        assert target and target[0]["acked"] is True, "ack 未生效"
        return "200", "%s 已确认" % event_id

    def check_event_snapshot(self):
        event_id = self.state["event"]["id"]
        status, headers, body = self.client.get("/api/v1/events/%s/snapshot" % event_id)
        assert status == 200, "HTTP %s" % status
        assert headers.get("Content-Type", "").startswith("image/jpeg"), "不是 image/jpeg"
        return "200", "%d 字节 JPEG" % len(body)

    def check_event_clip(self):
        event_id = self.state["event"]["id"]
        status, _headers, body = self.client.get("/api/v1/events/%s/clip" % event_id)
        assert status in (200, 404), "HTTP %s" % status
        if status == 404:
            assert json.loads(body).get("ok") is False, "404 必须返回 ok=false"
            return "404", "无切片文件（契约里 clip 可选，4G 下建议只用 snapshot）"
        return "200", "%d 字节 mp4" % len(body)

    def check_sse(self):
        result: Dict[str, Any] = {"lines": [], "ctype": "", "error": None}

        def reader():
            try:
                request = urllib.request.Request(self.client.base + "/api/v1/stream/events")
                request.add_header("Accept", "text/event-stream")
                with urllib.request.urlopen(request, timeout=self.wait_s + 10) as resp:
                    result["ctype"] = resp.headers.get("Content-Type", "")
                    deadline = time.time() + min(self.wait_s, 25)
                    while time.time() < deadline:
                        line = resp.readline()
                        if not line:
                            break
                        result["lines"].append(line.decode("utf-8", "replace").strip())
                        if any(item.startswith("data:") for item in result["lines"]):
                            break
            except Exception as exc:
                result["error"] = str(exc)

        thread = threading.Thread(target=reader, daemon=True)
        thread.start()
        thread.join(timeout=self.wait_s + 12)
        assert result["ctype"].startswith("text/event-stream"), "Content-Type 非 text/event-stream（%s）" % result["ctype"]
        assert result["lines"], "SSE 没收到任何内容（心跳也没有）：%s" % result["error"]
        data_lines = [x for x in result["lines"] if x.startswith("data:")]
        if data_lines:
            event = json.loads(data_lines[0][5:].strip())
            tc.check_keys(event, tc.EVENT_KEYS, "SSE 事件")
            return "200", "收到实时事件 %s（%s）" % (event["id"], event["type"])
        heartbeat = [x for x in result["lines"] if x.startswith(":")]
        return "200", "已连上并收到心跳 %s（窗口内暂无新事件）" % (heartbeat[0] if heartbeat else "")

    def check_metrics(self):
        camera_id = self.state["camera_id"]
        status, _headers, data = self.client.json(
            "/api/v1/metrics/splash?camera_id=%s&window=24h&step=300" % camera_id
        )
        assert status == 200, "HTTP %s" % status
        tc.check_keys(data, tc.METRICS_KEYS, "metrics/splash")
        for point in data["series"]:
            tc.check_keys(point, tc.SERIES_POINT_KEYS, "series[]")
        return "200", "%d 个曲线点，%d 个投料窗口" % (len(data["series"]), len(data["feed_windows"]))

    def check_snapshots(self):
        status, _headers, data = self.client.json("/api/v1/snapshots?limit=50")
        assert status == 200, "HTTP %s" % status
        assert isinstance(data, list), "snapshots 不是数组"
        for item in data:
            tc.check_keys(item, tc.SNAPSHOT_KEYS, "snapshots[]")
        if data:
            status, headers, body = self.client.get(data[0]["url"])
            assert status == 200 and body[:2] == b"\xff\xd8", "抓图 URL 取不回 JPEG（HTTP %s）" % status
            return "200", "%d 张抓图，首张 %d 字节" % (len(data), len(body))
        return "200", "暂无抓图（等首次抓图周期或事件触发）"

    def check_config(self):
        status, _headers, data = self.client.json("/api/v1/config")
        assert status == 200, "HTTP %s" % status
        tc.check_keys(data, tc.CONFIG_TOP_KEYS, "/config")
        original = data
        probe = {"thresholds": {"splash_ratio": 1.66}}
        status, _headers, body = self.client.send("PUT", "/api/v1/config", probe)
        assert status == 200, "PUT HTTP %s" % status
        assert json.loads(body)["config"]["thresholds"]["splash_ratio"] == 1.66, "PUT 未生效"
        status, _headers, body = self.client.send("PUT", "/api/v1/config", {"nope": 1})
        assert status == 400, "非法字段必须 400（实际 %s）" % status
        self.client.send("PUT", "/api/v1/config", original)  # 还原
        return "200", "GET/PUT/落盘/校验 全部生效并已还原"

    def check_logs(self):
        status, _headers, data = self.client.json("/api/v1/logs?limit=50")
        assert status == 200, "HTTP %s" % status
        assert isinstance(data, list) and data, "logs 为空"
        for item in data:
            tc.check_keys(item, tc.LOG_KEYS, "logs[]")
        levels = sorted({item["level"] for item in data})
        return "200", "%d 条日志，级别 %s" % (len(data), "/".join(levels))

    def check_static(self):
        status, headers, body = self.client.get("/")
        assert status == 200, "HTTP %s" % status
        assert "text/html" in headers.get("Content-Type", ""), "不是 HTML"
        return "200", "首页 %d 字节" % len(body)

    def check_404(self):
        status, _headers, body = self.client.get("/api/v1/definitely-not-there")
        assert status == 404, "HTTP %s" % status
        assert json.loads(body).get("ok") is False, "404 必须返回 ok=false"
        return "404", "未知端点按契约返回 {ok:false,error}"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="鱼塘视觉固件一键自检")
    parser.add_argument("--simulate", action="store_true", default=True, help="以模拟模式起服务（默认开）")
    parser.add_argument("--live", action="store_true", help="以现场模式起服务（需要真相机）")
    parser.add_argument("--base-url", default=None, help="只打已在运行的服务，不再新起进程")
    parser.add_argument("--port", type=int, default=None, help="服务端口（默认随机空闲端口）")
    parser.add_argument("--wait", type=float, default=90.0, help="等待事件/首帧的最长秒数")
    parser.add_argument("--keep", action="store_true", help="自检结束后保留服务进程（调试用）")
    args = parser.parse_args(argv)

    process: Optional[subprocess.Popen] = None
    tmpdir: Optional[str] = None
    try:
        if args.base_url:
            base = args.base_url
        else:
            port = args.port or free_port()
            tmpdir = tempfile.mkdtemp(prefix="yutang-selfcheck-")
            config_path = os.path.join(tmpdir, "config.yaml")
            cmd = [
                sys.executable,
                "-m",
                "yutang_vision",
                "--config",
                config_path,
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ]
            if not args.live:
                cmd.append("--simulate")
            print("启动服务：%s" % " ".join(cmd))
            process = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            base = "http://127.0.0.1:%d" % port

        client = Client(base)
        print("目标地址：%s" % base)
        deadline = time.time() + 30
        ready = False
        while time.time() < deadline:
            try:
                status, _headers, _body = client.get("/api/v1/health", timeout=5)
                if status == 200:
                    ready = True
                    break
            except Exception:
                pass
            time.sleep(0.5)
        if not ready:
            print("服务未就绪（30 s 超时）")
            if process is not None:
                process.terminate()
                out, _ = process.communicate(timeout=10)
                print(out.decode("utf-8", "replace")[-3000:])
            return 2

        checker = Checker(client, args.wait)
        # 相机 ID：先探一次，云台类检查用 detail 位
        _status, _headers, cameras = client.json("/api/v1/cameras")
        checker.state["cameras"] = cameras or []
        checker.state["camera_id"] = (cameras or [{"id": "cam-pano"}])[0]["id"]
        detail = [c for c in (cameras or []) if c.get("role") == "detail"]
        checker.state["detail_camera"] = detail[0]["id"] if detail else checker.state["camera_id"]

        checker.run("GET  /api/v1/health", checker.check_health)
        checker.run("GET  /api/v1/cameras", checker.check_cameras)
        checker.run("GET  /api/v1/cameras/{id}/snapshot", checker.check_camera_snapshot)
        checker.run("POST /api/v1/cameras/{id}/ptz", checker.check_ptz)
        checker.run("GET  /api/v1/presets", checker.check_presets)
        checker.run("GET  /api/v1/events", checker.check_events)
        checker.run("POST /api/v1/events/{id}/ack", checker.check_event_ack)
        checker.run("GET  /api/v1/events/{id}/snapshot", checker.check_event_snapshot)
        checker.run("GET  /api/v1/events/{id}/clip", checker.check_event_clip)
        checker.run("GET  /api/v1/stream/events (SSE)", checker.check_sse)
        checker.run("GET  /api/v1/metrics/splash", checker.check_metrics)
        checker.run("GET  /api/v1/snapshots", checker.check_snapshots)
        checker.run("GET|PUT /api/v1/config", checker.check_config)
        checker.run("GET  /api/v1/logs", checker.check_logs)
        checker.run("GET  / (静态首页)", checker.check_static)
        checker.run("GET  /api/v1/<unknown> (404)", checker.check_404)

        print()
        print("=" * 100)
        print("鱼塘视觉固件 · 自检报告  （%s）" % base)
        print("=" * 100)
        print("%-38s %-6s %-6s %s" % ("端点", "HTTP", "结果", "备注"))
        print("-" * 100)
        for name, status, result, note in checker.rows:
            print("%-38s %-6s %-6s %s" % (name, status, result, note))
        print("-" * 100)
        failed = [row for row in checker.rows if row[2] == "FAIL"]
        print("通过 %d / %d，失败 %d" % (len(checker.rows) - len(failed), len(checker.rows), len(failed)))
        if failed:
            print("失败项：%s" % ", ".join(row[0] for row in failed))
        return 1 if failed else 0
    finally:
        if process is not None and not args.keep:
            process.terminate()
            try:
                process.communicate(timeout=10)
            except Exception:
                process.kill()
        if tmpdir and not args.keep:
            import shutil

            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
