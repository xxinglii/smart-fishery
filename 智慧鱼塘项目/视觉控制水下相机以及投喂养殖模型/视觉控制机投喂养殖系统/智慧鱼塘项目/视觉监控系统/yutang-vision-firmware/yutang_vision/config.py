"""配置加载 / 校验 / 热更新（PUT /api/v1/config 落盘）。

三条硬约束：

1. **契约一致**：`GET /api/v1/config` 只返回契约 §6 里的 6 个键
   （feed_windows / thresholds / capture / upload / record / patrol），
   `PUT` 也只接受这 6 个键（未知字段直接拒绝，避免前端以为改生效了其实没有）。
   配置文件里其余键（server / cameras / analysis / detector / ...）属于运行期设置，
   不出现在契约响应里。
2. **缺 pyyaml 也能跑**：内置一个极简 YAML 子集解析器与序列化器（纯标准库），
   支持块映射、块列表、行内 `{a: 1}` / `[1, 2]`、引号、注释、int/float/bool/null。
3. **落盘原子**：先写 `config.yaml.tmp` 再 `os.replace`，断电不会写坏配置。

注意 YAML 1.1 的坑：`start: 06:30` 会被 PyYAML 解析成 390（六十进制）。
所以示例文件里时间一律加引号；同时本模块对 0..2359 的整数做兜底还原（390 -> "06:30"）。
"""

from __future__ import annotations

import copy
import json
import os
import re
import threading
from typing import Any, Dict, List, Optional, Tuple

from . import has, note_degraded

#: 契约 §6 的顶层键（顺序即 GET 返回的书写顺序）
CONTRACT_KEYS: Tuple[str, ...] = (
    "feed_windows",
    "thresholds",
    "capture",
    "upload",
    "record",
    "patrol",
)

UPLOAD_POLICIES: Tuple[str, ...] = ("thumbs_only", "events_only", "full")

_HHMM_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

# --------------------------------------------------------------------------
# 默认配置：与 config.example.yaml 保持一致
# --------------------------------------------------------------------------
DEFAULT_CONFIG: Dict[str, Any] = {
    "server": {
        "host": "0.0.0.0",
        "port": 8080,
        "sse_heartbeat_s": 15,
        "cors": True,
        # 前端文件目录；留空则自动查找 ../yutang-vision-console、./static
        "static_dir": "",
    },
    "cameras": [
        {
            "id": "cam-pano",
            "name": "全景位 · 塘东北角",
            "role": "panorama",
            "model": "DS-2CD3T86FWDV3-I3S",
            "ip": "192.168.1.64",
            "rtsp_user": "admin",
            "rtsp_password": "CHANGE_ME",
            "rtsp_path": "/Streaming/Channels/101",
            "rtsp_port": 554,
            "onvif": True,
            "onvif_port": 80,
            "resolution": "3840x2160",
            "fps": 20,
            "bitrate_kbps": 4096,
            "ir_m": 30,
            "ptz": False,
            "analysis": {"width": 640, "height": 360, "fps": 5},
        },
        {
            "id": "cam-detail",
            "name": "细节位 · 塘西南角",
            "role": "detail",
            "model": "DS-2DC4423IW-D",
            "ip": "192.168.1.65",
            "rtsp_user": "admin",
            "rtsp_password": "CHANGE_ME",
            "rtsp_path": "/Streaming/Channels/101",
            "rtsp_port": 554,
            "onvif": True,
            "onvif_port": 80,
            "resolution": "2560x1440",
            "fps": 25,
            "bitrate_kbps": 4096,
            "ir_m": 100,
            "ptz": {
                "zoom_max": 23,
                "pan_speed_dps": 60.0,
                "tilt_speed_dps": 30.0,
                "zoom_speed": 0.6,
                "pan_min": 0.0,
                "pan_max": 360.0,
                "tilt_min": -90.0,
                "tilt_max": 25.0,
            },
            "analysis": {"width": 640, "height": 360, "fps": 5},
        },
    ],
    # --- 以下 6 个键就是契约 §6 ---
    "feed_windows": [
        {"start": "06:30", "end": "07:10"},
        {"start": "16:30", "end": "17:20"},
    ],
    "thresholds": {
        "splash_ratio": 1.6,
        "aggregation_area_pct": 4.0,
        "person_confidence": 0.6,
    },
    "capture": {
        "interval_s": 60,
        "on_event": True,
        "jpeg_quality": 85,
        "max_width": 1920,
    },
    "upload": {
        "policy": "thumbs_only",
        "max_kbps": 512,
        "quota_gb_month": 10,
    },
    "record": {
        "local_full_stream": True,
        "keep_days": 14,
    },
    "patrol": {
        "on": True,
        "preset_ids": [1, 2, 3],
        "dwell_s": 30,
    },
    # --- 运行期设置（不在契约响应里）---
    "ptz_presets": [
        {"id": 1, "name": "投料点", "camera_id": "cam-detail", "pan": 118.0, "tilt": -22.0, "zoom": 6.0},
        {"id": 2, "name": "塘中央", "camera_id": "cam-detail", "pan": 168.0, "tilt": -9.0, "zoom": 1.0},
        {"id": 3, "name": "进水口", "camera_id": "cam-detail", "pan": 205.0, "tilt": -14.0, "zoom": 4.0},
    ],
    "analysis": {
        "roi": None,  # null = 全画面；否则 [x, y, w, h] 归一化到 0..1
        "pixel_thr": 25,  # 帧差灰度阈值（有 numpy 时生效）
        "max_fps": 5,
    },
    "detector": {
        "splash_min_s": 8,
        "splash_cooldown_s": 120,
        "aggregation_frames": 15,
        "aggregation_cooldown_s": 300,
        "person_cooldown_s": 60,
        "person_roi": [0.0, 0.02, 0.40, 0.95],  # 立杆侧警戒区（归一化 x,y,w,h；HOG 需要 ≥64x128 像素）
        "tamper_cooldown_s": 300,
        "tamper_mean_delta": 28.0,  # 亮度均值突变阈值（灰度级）
        "tamper_std_min": 4.0,  # 画面方差塌陷阈值（镜头被糊住）
        "motion_ratio": 0.02,
        "motion_cooldown_s": 60,
        "dark_k": 1.5,  # 暗斑阈值 = 均值 - k * 标准差
        "offline_after_s": 30,
        "rtsp_timeout_s": 15,  # ffmpeg socket 超时（相机掉线时快速失败）
        "stream_stall_s": 12,  # 超过这么久没有新帧就重启拉流进程
        "mobilenet_prototxt": "",
        "mobilenet_caffemodel": "",
        "hog_win_stride": 8,
    },
    "metrics": {
        "sample_s": 5,  # V-Value 采样间隔 -> 入库
        "baseline_window_s": 1800,  # 基线回看窗口（滚动中位数）
        "default_window": "24h",
        "default_step": 300,
        "keep_days": 30,
    },
    "storage": {
        "data_dir": "data",
        "min_free_gb": 3.0,
        "snapshot_keep_days": 14,
        "events_keep_days": 90,
        "logs_keep_days": 14,
        "cleanup_interval_s": 60,
    },
    "net": {
        "type": "4g",  # 契约 health.net.type
        "carrier": "",  # 留空 -> 由 mmcli 探测，探测不到给 null
        "iface_include": ["eth", "wlan", "usb", "wwan", "en", "enp", "end"],
        "iface_exclude": ["lo", "docker", "veth", "br-"],
        "mmcli_enable": True,
    },
    "sim": {
        # --simulate 的剧本：每个阶段持续多少秒，保证 5 类事件都能在前端看到
        "fps": 5,
        "width": 320,
        "height": 180,
        "first_event_s": 8,
        "phase_s": {
            "idle": 20,
            "splash": 40,
            "aggregation": 40,
            "person": 30,
            "tamper": 20,
            "offline": 40,
        },
        "offline_camera": "cam-detail",
        "seed": 20260919,
    },
    "logging": {"level": "info", "stdout": True, "ring_size": 2000},
}

DEFAULTS_LOCK = threading.RLock()


def default_config() -> Dict[str, Any]:
    """返回一份默认配置深拷贝（record 键在 DEFAULT_CONFIG 里只保留契约字段）。"""
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    return cfg


# ==========================================================================
# 极简 YAML 子集：解析
# ==========================================================================
def _strip_comment(line: str) -> str:
    out = []
    quote = ""
    for i, ch in enumerate(line):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = ""
            continue
        if ch in "\"'":
            quote = ch
            out.append(ch)
            continue
        if ch == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        out.append(ch)
    return "".join(out)


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _split_flow(text: str) -> List[str]:
    parts, buf, depth, quote = [], [], 0, ""
    for ch in text:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = ""
            continue
        if ch in "\"'":
            quote = ch
            buf.append(ch)
            continue
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if "".join(buf).strip():
        parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip() != ""]


def _is_kv(text: str) -> bool:
    quote = ""
    for i, ch in enumerate(text):
        if quote:
            if ch == quote:
                quote = ""
            continue
        if ch in "\"'":
            quote = ch
            continue
        if ch == ":" and (i + 1 >= len(text) or text[i + 1] in " \t"):
            return True
    return False


def _parse_flow_map(text: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for item in _split_flow(text):
        key, _, val = item.partition(":")
        result[key.strip().strip("\"'")] = _coerce_scalar(val)
    return result


def _coerce_scalar(token: str) -> Any:
    tok = token.strip()
    if tok == "":
        return None
    if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in "\"'":
        return tok[1:-1]
    low = tok.lower()
    if low in ("null", "~", "none"):
        return None
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if tok == "[]":
        return []
    if tok == "{}":
        return {}
    if tok.startswith("[") and tok.endswith("]"):
        return [_coerce_scalar(p) for p in _split_flow(tok[1:-1])]
    if tok.startswith("{") and tok.endswith("}"):
        return _parse_flow_map(tok[1:-1])
    try:
        return int(tok, 10)
    except ValueError:
        pass
    try:
        return float(tok)
    except ValueError:
        pass
    return tok


def _parse_block(lines: List[str], i: int, indent: int) -> Tuple[Any, int]:
    """递归下降解析同缩进的一个块，返回 (值, 下一行下标)。"""
    items: Optional[List[Any]] = None
    mapping: Optional[Dict[str, Any]] = None
    while i < len(lines):
        raw = lines[i]
        if not raw.strip():
            i += 1
            continue
        ind = _indent_of(raw)
        if ind < indent:
            break
        if ind > indent:
            raise ValueError("YAML 子集解析错误：缩进不一致（第 %d 行）" % (i + 1))
        text = raw.strip()
        if text.startswith("- "):
            if mapping is not None:
                raise ValueError("YAML 子集解析错误：同一层混用映射与列表（第 %d 行）" % (i + 1))
            if items is None:
                items = []
            rest = text[2:].strip()
            if not rest:
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines) and _indent_of(lines[j]) > ind:
                    sub, i = _parse_block(lines, j, _indent_of(lines[j]))
                    items.append(sub)
                else:
                    items.append(None)
                    i += 1
                continue
            if rest[0] in "[{":
                # 行内流式写法：- {start: "06:30", end: "07:10"}
                items.append(_coerce_scalar(rest))
                i += 1
                continue
            if _is_kv(rest):
                item_indent = ind + 2
                j = i + 1
                while j < len(lines) and (not lines[j].strip() or _indent_of(lines[j]) >= item_indent):
                    j += 1
                sub_lines = [" " * item_indent + rest] + lines[i + 1 :]
                sub, _ = _parse_block(sub_lines, 0, item_indent)
                items.append(sub)
                i = j
                continue
            items.append(_coerce_scalar(rest))
            i += 1
            continue
        if items is not None:
            raise ValueError("YAML 子集解析错误：同一层混用列表与映射（第 %d 行）" % (i + 1))
        if mapping is None:
            mapping = {}
        key, sep, val = text.partition(":")
        if not sep:
            raise ValueError("YAML 子集解析错误：缺少冒号（第 %d 行）" % (i + 1))
        key = key.strip().strip("\"'")
        val = val.strip()
        if val:
            mapping[key] = _coerce_scalar(val)
            i += 1
        else:
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and _indent_of(lines[j]) > ind:
                sub, i = _parse_block(lines, j, _indent_of(lines[j]))
                mapping[key] = sub
            else:
                mapping[key] = None
                i += 1
    if items is not None:
        return items, i
    return (mapping if mapping is not None else {}), i


def mini_yaml_load(text: str) -> Any:
    """纯标准库的 YAML 子集解析（pyyaml 缺失时的兜底）。"""
    lines = [_strip_comment(ln).rstrip() for ln in text.splitlines()]
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines):
        return {}
    value, _ = _parse_block(lines, i, _indent_of(lines[i]))
    return value


# ==========================================================================
# 极简 YAML 子集：序列化
# ==========================================================================
_YAML_PLAIN_RE = re.compile(r"^[A-Za-z_\u4e00-\u9fff][A-Za-z0-9_\u4e00-\u9fff./+-]*$")
_YAML_KEYWORDS = {"true", "false", "yes", "no", "on", "off", "null", "none", "~"}


def _scalar_str(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return repr(value)
    text = str(value)
    if text == "" or not _YAML_PLAIN_RE.match(text) or text.lower() in _YAML_KEYWORDS:
        return json.dumps(text, ensure_ascii=False)
    return text


def _dump_block(obj: Any, indent: int, out: List[str]) -> None:
    pad = " " * indent
    if isinstance(obj, dict):
        if not obj:
            return
        for key, val in obj.items():
            if isinstance(val, dict) and val:
                out.append("%s%s:" % (pad, key))
                _dump_block(val, indent + 2, out)
            elif isinstance(val, list) and val:
                out.append("%s%s:" % (pad, key))
                _dump_block(val, indent + 2, out)
            elif isinstance(val, dict):
                out.append("%s%s: {}" % (pad, key))
            elif isinstance(val, list):
                out.append("%s%s: []" % (pad, key))
            else:
                out.append("%s%s: %s" % (pad, key, _scalar_str(val)))
        return
    if isinstance(obj, list):
        for val in obj:
            if isinstance(val, dict) and val:
                sub: List[str] = []
                _dump_block(val, indent + 2, sub)
                out.append("%s- %s" % (pad, sub[0].strip()))
                out.extend(sub[1:])
            elif isinstance(val, list) and val and all(
                not isinstance(x, (dict, list)) for x in val
            ):
                # 列表套列表 / 短标量列表：写成行内流式，保证能被解析回来
                out.append("%s- [%s]" % (pad, ", ".join(_scalar_str(x) for x in val)))
            elif isinstance(val, list) and val:
                sub = []
                _dump_block(val, indent + 2, sub)
                out.append("%s- %s" % (pad, sub[0].strip()))
                out.extend(sub[1:])
            else:
                out.append("%s- %s" % (pad, _scalar_str(val)))
        return
    out.append("%s%s" % (pad, _scalar_str(obj)))


def mini_yaml_dump(obj: Any) -> str:
    """把配置写成 YAML（pyyaml 缺失时用；输出可被上面那个解析器读回）。"""
    out: List[str] = []
    _dump_block(obj, 0, out)
    return "\n".join(out) + "\n"


# ==========================================================================
# 取值辅助 / 校验
# ==========================================================================
def _deep_merge(base: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(base)
    for key, val in patch.items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = copy.deepcopy(val)
    return out


def _type_name(value: Any) -> str:
    return type(value).__name__


def _is_num(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _hhmm(value: Any) -> Optional[str]:
    """把时间字段规范成 "HH:MM"；YAML 六十进制误解析（06:30 -> 390）也还原。"""
    if isinstance(value, str):
        text = value.strip()
        if _HHMM_RE.match(text):
            return text
        if re.match(r"^\d{1,2}:\d{2}$", text):
            hh, mm = text.split(":")
            if 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59:
                return "%02d:%02d" % (int(hh), int(mm))
        return None
    if isinstance(value, int) and not isinstance(value, bool):
        if 0 <= value <= 2359 and value % 100 < 60:
            return "%02d:%02d" % (value // 100, value % 100)
    return None


def validate_contract_patch(patch: Dict[str, Any]) -> List[str]:
    """校验契约 §6 的配置片段，返回错误列表（空 = 通过）。"""
    errors: List[str] = []
    if not isinstance(patch, dict):
        return ["请求体必须是 JSON 对象"]

    for key in patch:
        if key not in CONTRACT_KEYS:
            errors.append(
                "未知字段 %r；/api/v1/config 只接受 %s" % (key, "/".join(CONTRACT_KEYS))
            )
    if errors:
        return errors

    if "feed_windows" in patch:
        fw = patch["feed_windows"]
        if not isinstance(fw, list):
            errors.append("feed_windows 必须是数组")
        else:
            for idx, item in enumerate(fw):
                if not isinstance(item, dict) or set(item.keys()) != {"start", "end"}:
                    errors.append("feed_windows[%d] 必须是 {start, end}" % idx)
                    continue
                if _hhmm(item.get("start")) is None or _hhmm(item.get("end")) is None:
                    errors.append(
                        "feed_windows[%d] 时间需为 HH:MM 字符串（YAML 里请加引号，"
                        "否则 06:30 会被解析成数字）" % idx
                    )

    if "thresholds" in patch:
        th = patch["thresholds"]
        if not isinstance(th, dict):
            errors.append("thresholds 必须是对象")
        else:
            allowed = {"splash_ratio", "aggregation_area_pct", "person_confidence"}
            for key in th:
                if key not in allowed:
                    errors.append("thresholds 不支持的字段 %r" % key)
            if "splash_ratio" in th and (not _is_num(th["splash_ratio"]) or th["splash_ratio"] <= 0):
                errors.append("thresholds.splash_ratio 必须是 >0 的数字")
            if "aggregation_area_pct" in th:
                val = th["aggregation_area_pct"]
                if not _is_num(val) or not (0 < float(val) <= 100):
                    errors.append("thresholds.aggregation_area_pct 必须是 (0,100] 的数字")
            if "person_confidence" in th:
                val = th["person_confidence"]
                if not _is_num(val) or not (0 <= float(val) <= 1):
                    errors.append("thresholds.person_confidence 必须是 [0,1] 的数字")

    if "capture" in patch:
        cap = patch["capture"]
        if not isinstance(cap, dict):
            errors.append("capture 必须是对象")
        else:
            allowed = {"interval_s", "on_event", "jpeg_quality", "max_width"}
            for key in cap:
                if key not in allowed:
                    errors.append("capture 不支持的字段 %r" % key)
            if "interval_s" in cap and (not _is_num(cap["interval_s"]) or cap["interval_s"] < 5):
                errors.append("capture.interval_s 必须是 >=5 的数字（单位秒）")
            if "on_event" in cap and not isinstance(cap["on_event"], bool):
                errors.append("capture.on_event 必须是布尔值")
            if "jpeg_quality" in cap:
                val = cap["jpeg_quality"]
                if not _is_num(val) or not (1 <= float(val) <= 100):
                    errors.append("capture.jpeg_quality 必须是 1..100 的整数")
            if "max_width" in cap:
                val = cap["max_width"]
                if not _is_num(val) or not (160 <= float(val) <= 7680):
                    errors.append("capture.max_width 必须是 160..7680 的整数")

    if "upload" in patch:
        up = patch["upload"]
        if not isinstance(up, dict):
            errors.append("upload 必须是对象")
        else:
            allowed = {"policy", "max_kbps", "quota_gb_month"}
            for key in up:
                if key not in allowed:
                    errors.append("upload 不支持的字段 %r" % key)
            if "policy" in up and up["policy"] not in UPLOAD_POLICIES:
                errors.append("upload.policy 必须是 %s 之一" % "/".join(UPLOAD_POLICIES))
            if "max_kbps" in up and (not _is_num(up["max_kbps"]) or up["max_kbps"] <= 0):
                errors.append("upload.max_kbps 必须是 >0 的数字")
            if "quota_gb_month" in up and (
                not _is_num(up["quota_gb_month"]) or up["quota_gb_month"] <= 0
            ):
                errors.append("upload.quota_gb_month 必须是 >0 的数字")

    if "record" in patch:
        rec = patch["record"]
        if not isinstance(rec, dict):
            errors.append("record 必须是对象")
        else:
            allowed = {"local_full_stream", "keep_days"}
            for key in rec:
                if key not in allowed:
                    errors.append("record 不支持的字段 %r" % key)
            if "local_full_stream" in rec and not isinstance(rec["local_full_stream"], bool):
                errors.append("record.local_full_stream 必须是布尔值")
            if "keep_days" in rec and (not _is_num(rec["keep_days"]) or rec["keep_days"] < 1):
                errors.append("record.keep_days 必须是 >=1 的整数")

    if "patrol" in patch:
        pat = patch["patrol"]
        if not isinstance(pat, dict):
            errors.append("patrol 必须是对象")
        else:
            allowed = {"on", "preset_ids", "dwell_s"}
            for key in pat:
                if key not in allowed:
                    errors.append("patrol 不支持的字段 %r" % key)
            if "on" in pat and not isinstance(pat["on"], bool):
                errors.append("patrol.on 必须是布尔值")
            if "preset_ids" in pat:
                ids = pat["preset_ids"]
                if not isinstance(ids, list) or any(
                    (not isinstance(x, int)) or isinstance(x, bool) for x in ids
                ):
                    errors.append("patrol.preset_ids 必须是整数数组")
            if "dwell_s" in pat and (not _is_num(pat["dwell_s"]) or pat["dwell_s"] < 5):
                errors.append("patrol.dwell_s 必须是 >=5 的数字（单位秒）")
    return errors


def fix_yaml11_keys(data: Dict[str, Any]) -> Dict[str, Any]:
    """YAML 1.1 会把裸 `on:` 解析成布尔键 True。这里兜底改回字符串 "on"。

    （PyYAML 走的是 YAML 1.1；不加这一步，用户写 `patrol:\n  on: true` 就会
    变成 {True: True}，契约字段 patrol.on 直接消失。）
    """
    for key, value in list(data.items()):
        if isinstance(value, dict):
            if True in value and "on" not in value:
                value["on"] = value.pop(True)
            if False in value and "off" not in value:
                value["off"] = value.pop(False)
            fix_yaml11_keys(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    fix_yaml11_keys(item)
    return data


def normalize_contract(data: Dict[str, Any]) -> Dict[str, Any]:
    """规范化 6 个契约键（时间统一成 "HH:MM" 字符串）。"""
    out = {key: copy.deepcopy(data.get(key)) for key in CONTRACT_KEYS}
    if isinstance(out.get("feed_windows"), list):
        fw = []
        for item in out["feed_windows"]:
            if isinstance(item, dict):
                start = _hhmm(item.get("start"))
                end = _hhmm(item.get("end"))
                if start and end:
                    fw.append({"start": start, "end": end})
        out["feed_windows"] = fw
    return out


# ==========================================================================
# Config
# ==========================================================================
class Config:
    """配置文件读写 + 契约 6 键投影 + 热更新。"""

    def __init__(self, path: Optional[str] = None, force_no_yaml: bool = False) -> None:
        self.path = os.path.abspath(path) if path else None
        self.force_no_yaml = force_no_yaml or not has("yaml")
        self._lock = threading.RLock()
        self.data: Dict[str, Any] = default_config()
        self.last_error: Optional[str] = None
        self.load()

    # ---------------- 读写 ----------------
    def load(self) -> Dict[str, Any]:
        with self._lock:
            data = default_config()
            if self.path and os.path.exists(self.path):
                try:
                    with open(self.path, "r", encoding="utf-8") as fh:
                        text = fh.read()
                    if self.force_no_yaml:
                        loaded = mini_yaml_load(text)
                    else:
                        import yaml  # type: ignore

                        loaded = yaml.safe_load(text)
                    if isinstance(loaded, dict):
                        data = _deep_merge(data, fix_yaml11_keys(loaded))
                    elif loaded is not None:
                        raise ValueError("配置文件顶层必须是映射（key: value）")
                    self.last_error = None
                except Exception as exc:  # 配置坏了也不能起不来：用默认值 + 记错误
                    self.last_error = "配置文件解析失败，已回退默认配置：%s" % exc
                    data = default_config()
            elif self.path and not os.path.exists(self.path):
                # 首次运行：把默认配置写出来，方便用户改
                self.data = data
                try:
                    self.save()
                except Exception:
                    pass
            self.data = data
            self.data["feed_windows"] = normalize_contract(self.data)["feed_windows"]
            return copy.deepcopy(self.data)

    def save(self) -> None:
        """原子落盘（tmp + os.replace）。"""
        with self._lock:
            if not self.path:
                return
            directory = os.path.dirname(self.path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            tmp = self.path + ".tmp"
            if self.force_no_yaml:
                text = mini_yaml_dump(self.data)
            else:
                import yaml  # type: ignore

                text = yaml.safe_dump(
                    self.data, allow_unicode=True, sort_keys=False, default_flow_style=False
                )
            header = (
                "# 鱼塘视觉监控系统 · 固件配置（由 PUT /api/v1/config 自动落盘，可手工编辑）\n"
                "# 前 6 个键（feed_windows/thresholds/capture/upload/record/patrol）就是 API 契约 §6 的结构。\n"
                "# 注意：时间务必写成带引号的字符串 \"06:30\"，否则 YAML 会当成六十进制数字。\n"
            )
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(header)
                fh.write(text)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self.path)

    # ---------------- 取值 ----------------
    def current(self) -> Dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self.data)

    def public(self) -> Dict[str, Any]:
        """契约 §6 的 GET 响应（严格 6 个键）。"""
        with self._lock:
            return normalize_contract(self.data)

    def get(self, dotted: str, default: Any = None) -> Any:
        node: Any = self.current()
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node if node is not None else default

    # ---------------- 热更新 ----------------
    def update(self, patch: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """校验 + 深合并 + 落盘。返回 (是否成功, 错误列表)。"""
        errors = validate_contract_patch(patch)
        if errors:
            return False, errors
        with self._lock:
            merged = fix_yaml11_keys(_deep_merge(self.data, patch))
            merged["feed_windows"] = normalize_contract(merged)["feed_windows"]
            old = self.data
            self.data = merged
            try:
                self.save()
            except Exception as exc:
                self.data = old
                return False, ["配置落盘失败：%s" % exc]
        return True, []

    def camera(self, camera_id: str) -> Optional[Dict[str, Any]]:
        for cam in self.get("cameras", []) or []:
            if cam.get("id") == camera_id:
                return copy.deepcopy(cam)
        return None


def load_config(path: Optional[str] = None, force_no_yaml: bool = False) -> Config:
    """便捷入口：加载配置，缺 pyyaml 时自动降级。"""
    cfg = Config(path=path, force_no_yaml=force_no_yaml)
    if cfg.force_no_yaml and not force_no_yaml:
        note_degraded("config", "使用内置 YAML 子集解析器（pyyaml 不可用）")
    if cfg.last_error:
        note_degraded("config", cfg.last_error)
    return cfg


__all__ = [
    "CONTRACT_KEYS",
    "UPLOAD_POLICIES",
    "DEFAULT_CONFIG",
    "Config",
    "load_config",
    "default_config",
    "mini_yaml_load",
    "mini_yaml_dump",
    "validate_contract_patch",
    "normalize_contract",
    "_hhmm",
]
