"""契约一致性测试：断言每个端点的响应结构 100% 符合《视觉系统_API契约_v1.md》。

两种跑法（都不需要联网、不需要相机）：
    python3 tests/test_contract.py        # 无 pytest 也能跑，打印逐项通过/失败表
    python3 -m pytest tests/ -q           # 装了 pytest 时同样可用

覆盖范围：health / cameras / snapshot / ptz / presets / events(+ack/snapshot/clip) /
SSE / metrics/splash / snapshots / config(GET+PUT+落盘) / logs / 静态页 / 404 /
limit 截断 / 时间戳整数 / 枚举值 / 事件必带 confidence+evidence。
另外包含两项单元测试：纯标准库 JPEG 编码器、配置校验规则。
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from yutang_vision import EVIDENCE_LEVEL, __version__  # noqa: E402
from yutang_vision.app import Runtime, make_server  # noqa: E402
from yutang_vision.camera import encode_jpeg_gray, jpeg_dimensions, mask_credentials  # noqa: E402
from yutang_vision.config import CONTRACT_KEYS, Config, validate_contract_patch  # noqa: E402
from yutang_vision.store import EVENT_TYPES, LOG_LEVELS, SEVERITIES, SNAPSHOT_TRIGGERS  # noqa: E402

# ==========================================================================
# 契约里写死的结构（照抄《视觉系统_API契约_v1.md》，一个字段都不许差）
# ==========================================================================
HEALTH_KEYS = {"ok", "version", "uptime_s", "mode", "pi", "net", "storage", "services"}
PI_KEYS = {"cpu_pct", "mem_pct", "temp_c", "disk_free_gb"}
NET_KEYS = {"type", "rssi_dbm", "carrier", "uplink_kbps", "month_bytes", "month_quota_bytes"}
STORAGE_KEYS = {"recording", "days_kept", "bytes_per_day"}
CAMERA_KEYS = {
    "id", "name", "role", "model", "ip", "rtsp", "onvif", "online",
    "resolution", "fps", "bitrate_kbps", "ir_m", "ptz", "snapshot_url",
}
PTZ_KEYS = {"pan", "tilt", "zoom", "zoom_max", "moving", "preset_id"}
PRESET_KEYS = {"id", "name", "camera_id", "pan", "tilt", "zoom"}
EVENT_KEYS = {
    "id", "ts", "camera_id", "type", "severity", "confidence", "title", "detail",
    "metric", "snapshot_url", "clip_url", "acked", "evidence",
}
SERIES_POINT_KEYS = {"ts", "v_value", "baseline", "thr"}
METRICS_KEYS = {"window", "step", "series", "feed_windows"}
SNAPSHOT_KEYS = {"ts", "camera_id", "url", "trigger"}
LOG_KEYS = {"ts", "level", "src", "msg"}
CONFIG_TOP_KEYS = set(CONTRACT_KEYS)
CONFIG_NESTED = {
    "thresholds": {"splash_ratio", "aggregation_area_pct", "person_confidence"},
    "capture": {"interval_s", "on_event", "jpeg_quality", "max_width"},
    "upload": {"policy", "max_kbps", "quota_gb_month"},
    "record": {"local_full_stream", "keep_days"},
    "patrol": {"on", "preset_ids", "dwell_s"},
}

_STATE = {}


# ==========================================================================
# 测试脚手架
# ==========================================================================
def _start_server():
    tmp = tempfile.mkdtemp(prefix="yutang-contract-")
    cfg = Config(path=os.path.join(tmp, "config.yaml"))
    # 关掉自动巡航：否则球机自己动，会干扰 PTZ 断言（test_ptz_actions 里会显式打开）
    cfg.update({"patrol": {"on": False}})
    runtime = Runtime(cfg, simulate=True, force_ptz_mock=True)
    runtime.start()
    server = make_server(runtime, "127.0.0.1", 0)
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.1}, daemon=True)
    thread.start()
    _STATE.update(
        {
            "tmp": tmp,
            "cfg": cfg,
            "runtime": runtime,
            "server": server,
            "thread": thread,
            "base": "http://127.0.0.1:%d" % port,
        }
    )
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            status, _headers, _body = http_get("/api/v1/health")
            if status == 200:
                return _STATE
        except Exception:
            pass
        time.sleep(0.3)
    raise RuntimeError("测试服务未能在 20 s 内就绪")


def _stop_server():
    server = _STATE.get("server")
    runtime = _STATE.get("runtime")
    if server is not None:
        server.shutdown()
        server.server_close()
    if runtime is not None:
        runtime.stop()
    tmp = _STATE.get("tmp")
    if tmp and os.path.isdir(tmp):
        shutil.rmtree(tmp, ignore_errors=True)
    _STATE.clear()


def ensure_server():
    if not _STATE:
        _start_server()
    return _STATE


def http_get(path, timeout=15.0):
    url = _STATE["base"] + path
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers or {}), exc.read()


def http_json(path, timeout=15.0):
    status, headers, body = http_get(path, timeout=timeout)
    try:
        data = json.loads(body.decode("utf-8"))
    except Exception:
        data = None
    return status, headers, data


def http_send(method, path, payload=None, timeout=20.0):
    url = _STATE["base"] + path
    if payload is None:
        data = b""
    elif isinstance(payload, (bytes, bytearray)):
        data = bytes(payload)
    else:
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            body = resp.read()
            return resp.status, dict(resp.headers), body
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers or {}), exc.read()


def send_json(method, path, payload=None, timeout=20.0):
    status, headers, body = http_send(method, path, payload, timeout=timeout)
    try:
        data = json.loads(body.decode("utf-8")) if body else None
    except Exception:
        data = None
    return status, headers, data


def cameras():
    """按需拉相机列表（各用例彼此独立，不依赖执行顺序）。"""
    if "cameras" not in _STATE:
        status, _headers, data = http_json("/api/v1/cameras")
        check(status == 200, "GET /cameras 应返回 200")
        _STATE["cameras"] = data
        _STATE["camera_ids"] = [cam["id"] for cam in data]
        detail = [cam for cam in data if cam["role"] == "detail" and cam["ptz"] is not None]
        _STATE["detail_camera"] = detail[0]["id"] if detail else None
    return _STATE["cameras"]


def ensure_event():
    """按需造一条事件（走 runtime.emit_event 真实路径，带抓图落盘）。"""
    if "event_id" not in _STATE:
        cameras()
        stored = _make_event(_STATE["runtime"], _STATE["camera_ids"][0])
        _STATE["event_id"] = stored["id"]
    return _STATE["event_id"]


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def check_keys(obj, expected, where):
    check(isinstance(obj, dict), "%s 必须是 JSON 对象，实际 %r" % (where, type(obj).__name__))
    actual = set(obj.keys())
    missing = expected - actual
    extra = actual - expected
    check(not missing, "%s 缺少字段：%s" % (where, sorted(missing)))
    check(not extra, "%s 多出字段（契约不允许）：%s" % (where, sorted(extra)))


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def is_num_or_none(value):
    return value is None or (isinstance(value, (int, float)) and not isinstance(value, bool))


# ==========================================================================
# 1. 健康与状态
# ==========================================================================
def test_health():
    ensure_server()
    status, headers, body = http_get("/api/v1/health")
    check(status == 200, "GET /health 应返回 200，实际 %s" % status)
    check(headers.get("Content-Type", "").startswith("application/json"), "health 必须是 JSON")
    data = json.loads(body)
    check_keys(data, HEALTH_KEYS, "health")
    check(data["ok"] is True, "health.ok 必须是 true")
    check(data["version"] == __version__, "health.version 必须是当前版本")
    check(is_int(data["uptime_s"]) and data["uptime_s"] >= 0, "uptime_s 必须是整数秒")
    check(data["mode"] in ("live", "mock"), "mode 必须是 live|mock")
    check(data["mode"] == "mock", "--simulate 下 mode 必须是 mock")
    check_keys(data["pi"], PI_KEYS, "health.pi")
    for key in PI_KEYS:
        check(is_num_or_none(data["pi"][key]), "health.pi.%s 必须是数字或 null" % key)
    check_keys(data["net"], NET_KEYS, "health.net")
    check(isinstance(data["net"]["type"], str), "net.type 必须是字符串")
    for key in ("rssi_dbm", "uplink_kbps", "month_bytes", "month_quota_bytes"):
        check(is_num_or_none(data["net"][key]), "health.net.%s 必须是数字或 null" % key)
    check(data["net"]["carrier"] is None or isinstance(data["net"]["carrier"], str), "net.carrier 必须是字符串或 null")
    check_keys(data["storage"], STORAGE_KEYS, "health.storage")
    check(isinstance(data["storage"]["recording"], bool), "storage.recording 必须是布尔")
    check(is_int(data["storage"]["days_kept"]), "storage.days_kept 必须是整数")
    check(is_int(data["storage"]["bytes_per_day"]), "storage.bytes_per_day 必须是整数")
    check(isinstance(data["services"], list) and data["services"], "services 必须是非空数组")
    for item in data["services"]:
        check_keys(item, {"name", "ok"}, "health.services[]")
        check(isinstance(item["ok"], bool), "services[].ok 必须是布尔")
    names = {item["name"] for item in data["services"]}
    check({"rtsp-ingest", "detector"} <= names, "services 至少要有 rtsp-ingest 与 detector")


# ==========================================================================
# 2. 相机
# ==========================================================================
def test_cameras():
    ensure_server()
    data = cameras()
    check(isinstance(data, list) and len(data) >= 2, "cameras 至少包含两台相机")
    roles = set()
    for cam in data:
        check_keys(cam, CAMERA_KEYS, "cameras[]")
        check(isinstance(cam["id"], str) and cam["id"], "cameras[].id 必须是非空字符串")
        check(cam["role"] in ("panorama", "detail"), "cameras[].role 必须是 panorama|detail")
        roles.add(cam["role"])
        check(isinstance(cam["online"], bool), "cameras[].online 必须是布尔")
        check(isinstance(cam["onvif"], bool), "cameras[].onvif 必须是布尔")
        check(isinstance(cam["fps"], int) and not isinstance(cam["fps"], bool), "cameras[].fps 必须是整数")
        check(isinstance(cam["bitrate_kbps"], int), "cameras[].bitrate_kbps 必须是整数")
        check(isinstance(cam["ir_m"], int), "cameras[].ir_m 必须是整数")
        check(cam["snapshot_url"] == "/api/v1/cameras/%s/snapshot" % cam["id"], "snapshot_url 形状不对")
        check(cam["rtsp"].startswith("rtsp://"), "rtsp 必须是 rtsp:// URL")
        check("***" in cam["rtsp"], "rtsp URL 里的口令必须打码为 ***")
        if cam["ptz"] is not None:
            check_keys(cam["ptz"], PTZ_KEYS, "cameras[].ptz")
            check(isinstance(cam["ptz"]["moving"], bool), "ptz.moving 必须是布尔")
            check(isinstance(cam["ptz"]["zoom_max"], (int, float)), "ptz.zoom_max 必须是数字")
            check(
                cam["ptz"]["preset_id"] is None or is_int(cam["ptz"]["preset_id"]),
                "ptz.preset_id 必须是整数或 null",
            )
    check(roles == {"panorama", "detail"}, "必须同时有全景位与细节位")


def test_camera_snapshot():
    ensure_server()
    camera_id = cameras()[0]["id"]
    deadline = time.time() + 30
    status = 0
    while time.time() < deadline:
        status, headers, body = http_get("/api/v1/cameras/%s/snapshot" % camera_id, timeout=20)
        if status == 200:
            break
        time.sleep(1.0)
    check(status == 200, "相机抓图应返回 200（等首帧），实际 %s" % status)
    check(headers.get("Content-Type", "").startswith("image/jpeg"), "抓图 Content-Type 必须是 image/jpeg")
    check(body[:2] == b"\xff\xd8" and body[-2:] == b"\xff\xd9", "抓图必须是完整 JPEG")
    width, height = jpeg_dimensions(body)
    check(bool(width) and bool(height), "抓图必须能解出宽高")
    # 4G 友好：?w= 可以要到更小的图
    status, _headers, small = http_get("/api/v1/cameras/%s/snapshot?w=320" % camera_id)
    check(status == 200, "缩略抓图应返回 200")
    swidth, _sh = jpeg_dimensions(small)
    check(swidth is not None and swidth <= 320, "?w=320 抓图宽度必须 <= 320，实际 %s" % swidth)
    status, _headers, _body = http_get("/api/v1/cameras/cam-not-exist/snapshot")
    check(status == 404, "不存在的相机抓图应 404")


def test_presets():
    ensure_server()
    status, _headers, data = http_json("/api/v1/presets")
    check(status == 200, "GET /presets 应返回 200")
    check(isinstance(data, list) and data, "presets 必须是非空数组")
    for preset in data:
        check_keys(preset, PRESET_KEYS, "presets[]")
        check(is_int(preset["id"]), "presets[].id 必须是整数")
        for key in ("pan", "tilt", "zoom"):
            check(isinstance(preset[key], (int, float)) and not isinstance(preset[key], bool),
                  "presets[].%s 必须是数字" % key)
    camera_id = cameras()[0]["id"]
    status, _headers, filtered = http_json("/api/v1/presets?camera_id=%s" % camera_id)
    check(status == 200, "带 camera_id 的 presets 应返回 200")
    check(all(p["camera_id"] == camera_id for p in filtered), "camera_id 过滤失效")
    status, _headers, _body = http_json("/api/v1/presets?camera_id=nope")
    check(status == 404, "未知相机的 presets 应 404")


def test_ptz_actions():
    ensure_server()
    cameras()
    camera_id = _STATE["detail_camera"]
    check(camera_id is not None, "默认配置里应有一台带云台的球机（cam-detail）")
    path = "/api/v1/cameras/%s/ptz" % camera_id
    status, _headers, data = send_json("POST", path, {"action": "move", "dx": -0.2, "dy": 0.1, "zoom": 0.0})
    check(status == 200, "ptz move 应返回 200，实际 %s" % status)
    check(isinstance(data, dict) and data.get("ok") is True, "ptz 响应必须是 {ok: true, ...}")
    check_keys(data, {"ok", "ptz"}, "ptz 响应")
    check_keys(data["ptz"], PTZ_KEYS, "ptz 响应.ptz")
    before = data["ptz"]["pan"]
    status, _headers, data2 = send_json("POST", path, {"action": "move", "dx": 0.5, "dy": 0.0, "zoom": 0.2})
    check(status == 200, "第二次 move 应返回 200")
    check(data2["ptz"]["pan"] != before, "move 后 pan 必须变化")
    status, _headers, data3 = send_json("POST", path, {"action": "goto", "preset_id": 2})
    check(status == 200 and data3["ptz"]["preset_id"] == 2, "goto 必须把 preset_id 置为 2")
    check(abs(data3["ptz"]["pan"] - 168.0) < 0.6, "goto 后 pan 应等于预置位的 pan（契约示例为 168.0）")
    status, _headers, data4 = send_json("POST", path, {"action": "save", "preset_id": 9, "name": "测试点"})
    check(status == 200 and data4["ok"] is True, "save 应返回 ok")
    status, _headers, presets = http_json("/api/v1/presets?camera_id=%s" % camera_id)
    check(any(p["id"] == 9 and p["name"] == "测试点" for p in presets), "save 的预置位必须出现在 /presets")
    status, _headers, data5 = send_json("POST", path, {"action": "home"})
    check(status == 200 and data5["ptz"]["zoom"] == 1.0, "home 应回到 zoom=1.0")
    status, _headers, data6 = send_json("POST", path, {"action": "patrol", "on": True, "preset_ids": [1, 2], "dwell_s": 5})
    check(status == 200 and data6["ok"] is True, "patrol 应返回 ok")
    status, _headers, data7 = send_json("POST", path, {"action": "fly"})
    check(status == 400 and data7 and data7.get("ok") is False, "未知 action 应 400 且 ok=false")
    status, _headers, data8 = send_json("POST", path, {"action": "goto", "preset_id": 99})
    check(status == 404, "不存在的预置位应 404")
    # 全景枪机没有云台 -> 明确 400
    pano = next((c["id"] for c in cameras() if c["ptz"] is None), None)
    if pano:
        status, _headers, data9 = send_json("POST", "/api/v1/cameras/%s/ptz" % pano, {"action": "home"})
        check(status == 400 and data9.get("ok") is False, "无云台相机调 ptz 应 400")


# ==========================================================================
# 3. 事件
# ==========================================================================
def _make_event(runtime, camera_id, **overrides):
    event = {
        "ts": int(time.time()),
        "camera_id": camera_id,
        "type": "splash_activity",
        "severity": "info",
        "confidence": 0.77,
        "title": "测试事件",
        "detail": "契约测试注入",
        "metric": {"v_value": 0.4, "baseline": 0.2, "ratio": 2.0, "duration_s": 10},
        "evidence": EVIDENCE_LEVEL,
    }
    event.update(overrides)
    return runtime.emit_event(event)


def test_events_shape_and_filters():
    ensure_server()
    ensure_event()
    status, _headers, data = http_json("/api/v1/events?limit=50")
    check(status == 200, "GET /events 应返回 200")
    check(isinstance(data, list) and data, "events 必须是非空数组")
    for event in data:
        check_keys(event, EVENT_KEYS, "events[]")
        check(is_int(event["ts"]), "events[].ts 必须是 Unix 秒整数")
        check(event["type"] in EVENT_TYPES, "events[].type 非法：%s" % event["type"])
        check(event["severity"] in SEVERITIES, "events[].severity 非法：%s" % event["severity"])
        check(isinstance(event["confidence"], (int, float)) and 0.0 <= event["confidence"] <= 1.0,
              "events[].confidence 必须是 0..1 的数字")
        check(isinstance(event["metric"], dict), "events[].metric 必须是对象")
        check(isinstance(event["acked"], bool), "events[].acked 必须是布尔")
        check(event["evidence"] in ("A", "B", "C"), "events[].evidence 必须是 A|B|C")
        check(event["evidence"] == "C", "未标定前必须是 C（不得声称 A）")
        check(event["snapshot_url"] == "/api/v1/events/%s/snapshot" % event["id"], "snapshot_url 形状不对")
        # mock 模式必须自带"[模拟]"标记，避免演示截图被当成实测
        check(event["title"].startswith("[模拟]"), "mock 模式事件标题必须带 [模拟] 前缀：%s" % event["title"])
        check(event["clip_url"] == "/api/v1/events/%s/clip" % event["id"], "clip_url 形状不对")
    ids = [e["id"] for e in data]
    check(_STATE["event_id"] in ids, "刚写入的事件必须能查到")
    status, _headers, filtered = http_json("/api/v1/events?type=offline")
    check(status == 200 and all(e["type"] == "offline" for e in filtered), "type 过滤失效")
    status, _headers, _body = http_json("/api/v1/events?type=count_fish")
    check(status == 400, "未知事件类型应 400（防止前端写错）")
    status, _headers, limited = http_json("/api/v1/events?limit=1")
    check(len(limited) == 1, "limit=1 必须只返回 1 条")
    newest = max(e["ts"] for e in data)
    status, _headers, since = http_json("/api/v1/events?since=%d" % newest)
    check(all(e["ts"] >= newest for e in since), "since 过滤失效")


def test_event_snapshot_and_ack():
    ensure_server()
    event_id = ensure_event()
    status, headers, body = http_get("/api/v1/events/%s/snapshot" % event_id)
    check(status == 200, "事件抓图应返回 200（事件抓图由 emit_event 落盘）")
    check(headers.get("Content-Type", "").startswith("image/jpeg"), "事件抓图必须是 image/jpeg")
    check(body[:2] == b"\xff\xd8", "事件抓图必须是 JPEG")
    status, _headers, data = send_json("POST", "/api/v1/events/%s/ack" % event_id)
    check(status == 200 and data == {"ok": True}, "ack 必须返回 {\"ok\": true}，实际 %s %s" % (status, data))
    status, _headers, events = http_json("/api/v1/events?limit=200")
    target = [e for e in events if e["id"] == event_id]
    check(target and target[0]["acked"] is True, "ack 后 acked 必须为 true")
    status, _headers, data = send_json("POST", "/api/v1/events/ev-nope/ack")
    check(status == 404 and data.get("ok") is False, "不存在的 ack 应 404 且 ok=false")
    status, headers, body = http_get("/api/v1/events/%s/clip" % event_id)
    check(status == 404, "没有切片时 clip 应 404（契约里 clip 是可选的）")
    check(json.loads(body).get("ok") is False, "clip 404 也要返回 {\"ok\": false, \"error\": ...}")


def test_offline_event_contract():
    """offline 事件（相机掉线 ≥30 s）也必须是契约形状。"""
    ensure_server()
    runtime = _STATE["runtime"]
    event = runtime.detector.offline_event("cam-pano", 42, 3, name="全景位")
    check_keys(event, EVENT_KEYS - {"id", "snapshot_url", "clip_url", "acked"}, "offline 事件（未入库）")
    stored = runtime.emit_event(event)
    check_keys(stored, EVENT_KEYS, "offline 事件（入库后）")
    check(stored["type"] == "offline" and stored["severity"] in SEVERITIES, "offline 事件字段不对")
    check(stored["metric"]["duration_s"] == 42, "offline 事件必须带 duration_s")


# ==========================================================================
# 4. SSE
# ==========================================================================
def test_sse_stream():
    ensure_server()
    runtime = _STATE["runtime"]
    received = []
    errors = []

    def reader():
        try:
            request = urllib.request.Request(_STATE["base"] + "/api/v1/stream/events")
            request.add_header("Accept", "text/event-stream")
            with urllib.request.urlopen(request, timeout=25) as resp:
                ctype = resp.headers.get("Content-Type", "")
                if not ctype.startswith("text/event-stream"):
                    errors.append("SSE Content-Type 不对：%s" % ctype)
                    return
                deadline = time.time() + 20
                while time.time() < deadline and len(received) < 2:
                    line = resp.readline()
                    if not line:
                        break
                    text = line.decode("utf-8", "replace").strip()
                    if text.startswith("data:"):
                        received.append(text[5:].strip())
                    elif text.startswith(":"):
                        received.append(text)
        except Exception as exc:  # 超时/连接关闭都算读取结束
            errors.append(str(exc))

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    time.sleep(2.0)  # 等 SSE 建立连接
    _make_event(runtime, cameras()[0]["id"], type="motion", title="SSE 测试事件")
    thread.join(timeout=22)
    check(not errors or received, "SSE 读取失败：%s" % errors)
    payloads = [item for item in received if item.startswith("{")]
    check(payloads, "SSE 必须推来 event: event / data: {...}（收到：%r）" % received[:4])
    event = json.loads(payloads[0])
    check_keys(event, EVENT_KEYS, "SSE 事件对象")
    check(event["type"] == "motion", "SSE 推送的必须是刚发的事件")


# ==========================================================================
# 5. 指标曲线 / 抓图墙
# ==========================================================================
def test_metrics_splash():
    ensure_server()
    camera_id = cameras()[0]["id"]
    status, _headers, data = http_json("/api/v1/metrics/splash?camera_id=%s&window=24h&step=300" % camera_id)
    check(status == 200, "GET /metrics/splash 应返回 200")
    check_keys(data, METRICS_KEYS, "metrics/splash")
    check(data["window"] == "24h", "window 必须回显请求值")
    check(is_int(data["step"]) and data["step"] == 300, "step 必须是整数且回显")
    check(isinstance(data["series"], list), "series 必须是数组")
    check(isinstance(data["feed_windows"], list), "feed_windows 必须是数组")
    for window in data["feed_windows"]:
        check_keys(window, {"start", "end"}, "feed_windows[]")
        check(isinstance(window["start"], str) and ":" in window["start"], "feed_windows[].start 必须是 \"HH:MM\" 字符串")
    for point in data["series"]:
        check_keys(point, SERIES_POINT_KEYS, "series[]")
        check(is_int(point["ts"]), "series[].ts 必须是整数")
        for key in ("v_value", "baseline", "thr"):
            check(isinstance(point[key], (int, float)) and not isinstance(point[key], bool),
                  "series[].%s 必须是数字" % key)
    if data["series"]:
        check(all(data["series"][i]["ts"] <= data["series"][i + 1]["ts"] for i in range(len(data["series"]) - 1)),
              "series 必须按 ts 升序")
    status, _headers, limited = http_json("/api/v1/metrics/splash?step=60&limit=5")
    check(status == 200 and len(limited["series"]) <= 5, "series 必须支持 limit 降采样")
    status, _headers, _body = http_json("/api/v1/metrics/splash?camera_id=nope")
    check(status == 404, "未知相机应 404")


def test_snapshots_wall():
    ensure_server()
    runtime = _STATE["runtime"]
    camera_id = cameras()[0]["id"]
    frame = runtime.cameras.get(camera_id).latest()
    check(frame is not None, "模拟源应该已经产出帧")
    jpeg = encode_jpeg_gray(frame.gray, frame.w, frame.h, 85, 640)
    row = runtime.store.save_snapshot(int(time.time()), camera_id, jpeg, "manual", 640, 360)
    check(row is not None, "抓图落盘失败")
    status, _headers, data = http_json("/api/v1/snapshots?limit=50")
    check(status == 200, "GET /snapshots 应返回 200")
    check(isinstance(data, list) and data, "snapshots 必须是非空数组")
    for item in data:
        check_keys(item, SNAPSHOT_KEYS, "snapshots[]")
        check(is_int(item["ts"]), "snapshots[].ts 必须是整数")
        check(item["trigger"] in SNAPSHOT_TRIGGERS, "snapshots[].trigger 非法：%s" % item["trigger"])
        check(item["url"] == "/api/v1/snapshots/%d.jpg" % item["ts"], "snapshots[].url 形状不对")
    urls = {item["url"] for item in data}
    check(len(urls) == len(data), "抓图 URL 必须两两不同（同秒不同相机也不行）")
    # 每个 url 都必须能取回真图
    status, headers, body = http_get(data[0]["url"])
    check(status == 200 and headers.get("Content-Type", "").startswith("image/jpeg"),
          "抓图 URL 必须能取回 image/jpeg")
    check(body[:2] == b"\xff\xd8", "抓图文件必须是 JPEG")
    status, _headers, filtered = http_json("/api/v1/snapshots?camera_id=%s&limit=10" % camera_id)
    check(all(item["camera_id"] == camera_id for item in filtered), "camera_id 过滤失效")
    status, _headers, filtered = http_json("/api/v1/snapshots?trigger=manual&limit=10")
    check(all(item["trigger"] == "manual" for item in filtered), "trigger 过滤失效")
    status, _headers, _body = http_json("/api/v1/snapshots/1.jpg")
    check(status == 404, "不存在的抓图应 404")


# ==========================================================================
# 6. 配置
# ==========================================================================
def test_config_get_and_put():
    ensure_server()
    cfg = _STATE["cfg"]
    status, _headers, data = http_json("/api/v1/config")
    check(status == 200, "GET /config 应返回 200")
    check_keys(data, CONFIG_TOP_KEYS, "/config 顶层")
    for key, nested in CONFIG_NESTED.items():
        check_keys(data[key], nested, "/config.%s" % key)
    check(isinstance(data["feed_windows"], list), "feed_windows 必须是数组")
    for window in data["feed_windows"]:
        check_keys(window, {"start", "end"}, "feed_windows[]")
    check(data["upload"]["policy"] in ("thumbs_only", "events_only", "full"), "upload.policy 枚举非法")
    check(is_int(data["capture"]["interval_s"]), "capture.interval_s 必须是整数")
    check(is_int(data["capture"]["max_width"]), "capture.max_width 必须是整数")
    check(is_int(data["capture"]["jpeg_quality"]), "capture.jpeg_quality 必须是整数")

    original = data
    patch = {
        "thresholds": {"splash_ratio": 1.75},
        "capture": {"interval_s": 90},
        "feed_windows": [{"start": "05:45", "end": "06:30"}],
    }
    status, _headers, result = send_json("PUT", "/api/v1/config", patch)
    check(status == 200, "PUT /config 应返回 200，实际 %s %s" % (status, result))
    check(isinstance(result, dict), "PUT /config 必须返回 JSON 对象")
    check(result.get("ok") is True, "PUT 必须返回 {ok: true, ...}")
    check(result["config"]["thresholds"]["splash_ratio"] == 1.75, "PUT 后阈值必须生效")
    check(result["config"]["feed_windows"][0]["start"] == "05:45", "PUT 后投料窗口必须生效")
    status, _headers, again = http_json("/api/v1/config")
    check(again["capture"]["interval_s"] == 90, "PUT 必须持久化到内存配置")
    check(again["thresholds"]["splash_ratio"] == 1.75, "PUT 必须持久化到内存配置")
    # 落盘校验：重新从磁盘读一遍
    reloaded = Config(path=cfg.path)
    check(reloaded.public()["thresholds"]["splash_ratio"] == 1.75, "PUT 必须落盘（重读配置一致）")
    # 非法输入必须被拒（而不是静默接受）
    for bad in (
        {"thresholds": {"splash_ratio": -1}},
        {"patrol": {"dwell_s": 1}},
        {"upload": {"policy": "everything"}},
        {"capture": {"jpeg_quality": 200}},
        {"camera_id": "x"},
        {"unknown_key": 1},
    ):
        status, _headers, data = send_json("PUT", "/api/v1/config", bad)
        check(status == 400, "非法配置 %r 必须 400，实际 %s" % (bad, status))
        check(isinstance(data, dict) and data.get("ok") is False, "非法配置必须返回 ok=false + error")
    status, _headers, data = send_json("PUT", "/api/v1/config", b"")
    check(status == 400, "空请求体必须 400，实际 %s" % status)
    # 还原，避免影响后续用例
    status, _headers, _data = send_json("PUT", "/api/v1/config", original)
    check(status == 200, "还原配置失败")


def test_config_validation_unit():
    """配置校验规则本身（不经过 HTTP）。"""
    check(validate_contract_patch({"thresholds": {"person_confidence": 1.5}}), "person_confidence>1 必须被拒")
    check(not validate_contract_patch({"thresholds": {"person_confidence": 0.6}}), "合法阈值不该报错")
    check(validate_contract_patch({"feed_windows": [{"start": "6:30", "end": "07:10"}]}) == [],
          "6:30 应被规范化为 06:30 而不是报错")
    check(validate_contract_patch({"feed_windows": [{"start": "25:00", "end": "07:10"}]}), "非法时间必须被拒")
    check(validate_contract_patch({"record": {"keep_days": 0}}), "keep_days=0 必须被拒")
    check(validate_contract_patch({"patrol": {"preset_ids": ["a"]}}), "preset_ids 必须是整数数组")


# ==========================================================================
# 7. 日志 / 静态 / 404 / limit
# ==========================================================================
def test_logs():
    ensure_server()
    status, _headers, data = http_json("/api/v1/logs?limit=50")
    check(status == 200, "GET /logs 应返回 200")
    check(isinstance(data, list) and data, "logs 必须是非空数组（启动日志）")
    for item in data:
        check_keys(item, LOG_KEYS, "logs[]")
        check(is_int(item["ts"]), "logs[].ts 必须是整数")
        check(item["level"] in LOG_LEVELS, "logs[].level 非法：%s" % item["level"])
        check(isinstance(item["src"], str) and isinstance(item["msg"], str), "logs[] src/msg 必须是字符串")
    status, _headers, limited = http_json("/api/v1/logs?limit=3")
    check(len(limited) <= 3, "logs 必须支持 limit")
    status, _headers, _body = http_json("/api/v1/logs?level=shout")
    check(status == 400, "未知日志级别应 400")


def test_static_and_404():
    ensure_server()
    status, headers, body = http_get("/")
    check(status == 200, "GET / 必须返回 200（前端或兜底页）")
    check("text/html" in headers.get("Content-Type", ""), "GET / 必须是 HTML")
    check(b"<html" in body.lower(), "GET / 必须是网页")
    status, _headers, body = http_get("/api/v1/nope")
    check(status == 404, "未知 API 应 404")
    check(json.loads(body).get("error"), "404 必须带 error 字段")
    status, _headers, data = http_json("/api/v1")
    check(status == 200 and isinstance(data.get("endpoints"), list), "/api/v1 索引页应列出端点")


def test_limit_and_types_unit():
    """大响应必须支持 ?limit=；所有时间戳必须是整数。"""
    ensure_server()
    for path, key in (
        ("/api/v1/events?limit=2", None),
        ("/api/v1/snapshots?limit=2", None),
        ("/api/v1/logs?limit=2", None),
    ):
        status, _headers, data = http_json(path)
        check(status == 200 and len(data) <= 2, "%s 未按 limit 截断" % path)


def test_pure_jpeg_encoder():
    """纯标准库 JPEG 编码器必须产出可解码的 JPEG（无 opencv 时的兜底路径）。"""
    width, height = 64, 48
    gray = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            gray[y * width + x] = (x * 4 + y * 2) % 256
    data = encode_jpeg_gray(bytes(gray), width, height, 80, 64, force_pure=True)
    check(data[:2] == b"\xff\xd8" and data[-2:] == b"\xff\xd9", "纯编码器必须产出 SOI..EOI")
    decoded_w, decoded_h = jpeg_dimensions(data)
    check((decoded_w, decoded_h) == (width, height), "纯编码器宽高必须正确，实际 %s" % ((decoded_w, decoded_h),))
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore

        arr = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
        check(arr is not None and arr.shape == (height, width), "opencv 必须能解码纯编码器的输出")
        check(abs(int(arr[24, 32]) - int(gray[24 * width + 32])) < 24, "解码后像素值应接近原图")
    except ImportError:
        pass  # 没有 opencv 时只校验结构


def test_simulate_injected_event_unit():
    """剧本注入的事件不得编造 confidence（诚实性硬要求）。"""
    from yutang_vision.simulate import SimSource

    source = SimSource("cam-pano", {}, {"first_event_s": 5})
    injected = source.injected_event("person")
    check(injected is not None and injected["type"] == "person", "person 阶段应注入事件")
    check(injected["confidence"] == 0.0, "剧本注入的事件必须把 confidence 置 0，不得编造")
    check(injected["metric"]["score"] == 0.0, "剧本注入的事件不得编造检测分数")
    check(injected["detail"].startswith("[模拟]"), "注入事件 detail 必须标注 [模拟]")
    check(source.injected_event("idle") is None, "非注入阶段不应产出事件")
    check(source.scenario.phase() in ("idle", "splash", "aggregation", "person", "tamper", "offline"),
          "剧本阶段名非法")


def test_mask_credentials_unit():
    """日志/接口里绝不能出现 RTSP 明文口令。"""
    raw = "Error opening input file rtsp://admin:SUPERSECRET@192.0.2.11:554/Streaming/Channels/101."
    masked = mask_credentials(raw)
    check("SUPERSECRET" not in masked, "口令必须被打码：%s" % masked)
    check("admin:***@" in masked, "打码后应保留用户名：%s" % masked)
    check(mask_credentials("no url here") == "no url here", "不含口令的文本不该被改动")


def test_health_after_traffic():
    """跑过一圈请求之后，health 仍然必须严格合规（服务项 ok 反映真实状态）。"""
    ensure_server()
    status, _headers, data = http_json("/api/v1/health")
    check(status == 200, "health 应始终可用")
    check_keys(data, HEALTH_KEYS, "health")
    check(any(item["name"] == "detector" and item["ok"] for item in data["services"]), "detector 服务应为 ok")




# ==========================================================================
# 8. 极端降级：把 numpy / opencv / pyyaml / onvif / psutil 全部屏蔽掉
# ==========================================================================
DEGRADED_PROBE = r"""
import importlib.abc, json, os, sys, tempfile, threading, time, urllib.request
BLOCK = {"numpy", "cv2", "yaml", "onvif", "zeep", "psutil", "PIL"}


class Blocker(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in BLOCK:
            raise ImportError("blocked by contract test: %s" % fullname)
        return None


sys.meta_path.insert(0, Blocker())
for name in list(sys.modules):
    if name.split(".")[0] in BLOCK:
        del sys.modules[name]

from yutang_vision.app import Runtime, make_server
from yutang_vision.camera import encode_jpeg_gray
from yutang_vision.config import Config

tmp = tempfile.mkdtemp(prefix="yutang-degraded-")
cfg = Config(path=os.path.join(tmp, "config.yaml"))
cfg.data["sim"]["width"] = 160
cfg.data["sim"]["height"] = 90
runtime = Runtime(cfg, simulate=True, force_ptz_mock=True)
runtime.start()
server = make_server(runtime, "127.0.0.1", 0)
port = server.server_address[1]
threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.2}, daemon=True).start()


def get(path, timeout=90):
    with urllib.request.urlopen("http://127.0.0.1:%d%s" % (port, path), timeout=timeout) as resp:
        return resp.status, resp.headers.get("Content-Type", ""), resp.read()


out = {}
status, _ctype, body = get("/api/v1/health")
out["health_status"] = status
out["health"] = json.loads(body)
status, ctype, body = get("/api/v1/cameras/cam-pano/snapshot?w=320")
out["snapshot"] = [status, ctype, len(body), body[:2].hex(), body[-2:].hex()]
# 纯标准库编码器（显式 force_pure，绕开 cv2）
frame = runtime.cameras.get("cam-pano").latest()
if frame is None:
    time.sleep(3)
    frame = runtime.cameras.get("cam-pano").latest()
pure = encode_jpeg_gray(frame.gray, frame.w, frame.h, 80, 320, force_pure=True)
out["pure_jpeg"] = [len(pure), pure[:2].hex(), pure[-2:].hex()]
time.sleep(8)
status, _ctype, body = get("/api/v1/events?limit=5")
out["events_status"] = status
out["events"] = json.loads(body)
runtime.stop()
server.shutdown()
print("PROBE_JSON " + json.dumps(out))
"""


def test_degrades_without_any_third_party():
    """把 numpy/opencv/pyyaml/onvif/psutil 全部屏蔽后，服务仍要能起、能出合规数据。"""
    import subprocess

    proc = subprocess.run(
        [sys.executable, "-c", DEGRADED_PROBE],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=240,
    )
    output = proc.stdout.decode("utf-8", "replace")
    marker = [line for line in output.splitlines() if line.startswith("PROBE_JSON ")]
    check(bool(marker), "降级探针没有输出结果，退出码 %s；末尾输出：\n%s" % (proc.returncode, output[-1500:]))
    data = json.loads(marker[0][len("PROBE_JSON ") :])
    check(data["health_status"] == 200, "缺全部第三方依赖时 /health 仍须 200")
    check_keys(data["health"], HEALTH_KEYS, "降级模式下的 health")
    check(data["health"]["mode"] == "mock", "降级模式下 mode 仍是 mock")
    degraded = [item["name"] for item in data["health"]["services"] if not item["ok"]]
    check(len(degraded) >= 3, "health.services 里必须能看到降级项（实际 %s）" % degraded)
    status, ctype, size, head, tail = data["snapshot"]
    check(status == 200 and ctype.startswith("image/jpeg"), "没有 opencv 时抓图仍须返回 image/jpeg")
    check(head == "ffd8" and tail == "ffd9", "没有 opencv 时抓图仍须是完整 JPEG（纯标准库编码器）")
    check(data["pure_jpeg"][1] == "ffd8" and data["pure_jpeg"][2] == "ffd9", "纯标准库 JPEG 编码器输出非法")
    check(data["events_status"] == 200, "降级模式下 /events 仍须 200")


# ==========================================================================
# 运行器（pytest 与独立运行两用）
# ==========================================================================
def _iter_tests():
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            yield name, func


def run_all(verbose: bool = True) -> int:
    ensure_server()
    results = []
    started = time.time()
    for name, func in _iter_tests():
        begin = time.time()
        try:
            func()
            results.append((name, True, "%.2fs" % (time.time() - begin), ""))
        except Exception as exc:
            results.append((name, False, "%.2fs" % (time.time() - begin), "%s: %s" % (type(exc).__name__, exc)))
    _stop_server()

    passed = sum(1 for r in results if r[1])
    failed = len(results) - passed
    if verbose:
        width = max(len(r[0]) for r in results) + 2
        print("=" * 78)
        print("鱼塘视觉固件 · 契约一致性测试（%d 项，用时 %.1fs）" % (len(results), time.time() - started))
        print("=" * 78)
        for name, ok, cost, message in results:
            print("%-4s %-*s %8s  %s" % ("PASS" if ok else "FAIL", width, name, cost, message))
        print("-" * 78)
        print("通过 %d / %d，失败 %d" % (passed, len(results), failed))
    return 1 if failed else 0


def setup_module(module):  # pytest 入口
    ensure_server()


def teardown_module(module):  # pytest 入口
    _stop_server()


if __name__ == "__main__":
    sys.exit(run_all())
