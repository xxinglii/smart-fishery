"""RTSP 拉流（ffmpeg 子进程优先，OpenCV 兜底）+ 指数退避重连 + 抓图 + 本地录像。

三条硬要求：

1. **连不上不许崩**：默认模式下相机打不开只会把 `online` 置 false、按指数退避重连，
   并在连续失败 ≥ `detector.offline_after_s`（默认 30 s，契约 §8）时由看门狗发 `offline` 事件。
2. **抓图 4G 友好**：默认 1920 宽 / JPEG q85（契约 §6 capture 默认值）。
   抓图优先级：ffmpeg 一次性抓帧（真机） → 最新帧 OpenCV 编码 → 最新帧纯标准库 JPEG 编码。
   最后一条是给"没装 ffmpeg 也没装 opencv"的极端情况兜底的，输出会自动限宽（见 encode_jpeg_gray）。
3. **灰度分析帧**：统一 `bytes` 灰度（长度 = w*h），下游 detector / 编码器都吃这个格式，
   所以 ffmpeg / OpenCV / 模拟源三条链路对检测器完全等价。

本文件还包含一个**纯标准库的 baseline JPEG 编码器**（`_encode_jpeg_pure`）：
没装 opencv / PIL / ffmpeg 时，抓图接口仍然能返回合法的 image/jpeg，而不是报 500。
"""

from __future__ import annotations

import math
import os
import re
import random
import shutil
import struct
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from . import note_degraded

# ==========================================================================
# 帧
# ==========================================================================


class Frame:
    """一帧灰度图。timestamp 是 Unix 秒（整数）。"""

    __slots__ = ("gray", "w", "h", "ts", "seq", "camera_id")

    def __init__(self, gray: bytes, w: int, h: int, ts: Optional[int] = None, seq: int = 0, camera_id: str = "") -> None:
        self.gray = gray
        self.w = int(w)
        self.h = int(h)
        self.ts = int(ts if ts is not None else time.time())
        self.seq = int(seq)
        self.camera_id = camera_id


# ==========================================================================
# 纯标准库 baseline JPEG 编码器（灰度）
# ==========================================================================
_ZIGZAG = [
    0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5,
    12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13, 6, 7, 14, 21, 28,
    35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51,
    58, 59, 52, 45, 38, 31, 39, 46, 53, 60, 61, 54, 47, 55, 62, 63,
]
_STD_QUANT = [
    16, 11, 10, 16, 24, 40, 51, 61,
    12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56,
    14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77,
    24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101,
    72, 92, 95, 98, 112, 100, 103, 99,
]
_DC_BITS = [0, 1, 5, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
_DC_VALS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
_AC_BITS = [0, 2, 1, 3, 3, 2, 4, 3, 5, 5, 4, 4, 0, 0, 1, 0x7D]
_AC_VALS = [
    0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
    0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
    0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
    0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
    0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
    0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
    0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
    0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
    0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
    0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
    0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
    0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
    0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
    0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA,
]


def _build_huff(bits: List[int], vals: List[int]) -> Dict[int, Tuple[int, int]]:
    table: Dict[int, Tuple[int, int]] = {}
    code = 0
    idx = 0
    for length in range(1, 17):
        for _ in range(bits[length - 1]):
            table[vals[idx]] = (code, length)
            code += 1
            idx += 1
        code <<= 1
    return table


_HUFF_DC = _build_huff(_DC_BITS, _DC_VALS)
_HUFF_AC = _build_huff(_AC_BITS, _AC_VALS)
_COS = [[math.cos((2 * x + 1) * u * math.pi / 16.0) for x in range(8)] for u in range(8)]
_C = [1.0 / math.sqrt(2.0)] + [1.0] * 7


def _scaled_quant(quality: int) -> List[int]:
    quality = int(max(1, min(100, quality)))
    scale = 5000.0 / quality if quality < 50 else 200.0 - 2.0 * quality
    out = []
    for value in _STD_QUANT:
        q = int((value * scale + 50.0) / 100.0)
        out.append(max(1, min(255, q)))
    return out


class _BitWriter:
    __slots__ = ("buf", "acc", "nbits")

    def __init__(self) -> None:
        self.buf = bytearray()
        self.acc = 0
        self.nbits = 0

    def write(self, code: int, length: int) -> None:
        self.acc = (self.acc << length) | (code & ((1 << length) - 1))
        self.nbits += length
        while self.nbits >= 8:
            self.nbits -= 8
            byte = (self.acc >> self.nbits) & 0xFF
            self.buf.append(byte)
            if byte == 0xFF:  # 字节填充，避免与标记混淆
                self.buf.append(0x00)

    def flush(self) -> None:
        if self.nbits > 0:
            self.write((1 << (8 - self.nbits)) - 1, 8 - self.nbits)


def _fdct_block(block: List[int]) -> List[float]:
    """分离式 8x8 DCT-II（纯 Python，兜底路径专用）。"""
    tmp = [[0.0] * 8 for _ in range(8)]
    for y in range(8):
        row = block[y * 8 : y * 8 + 8]
        for u in range(8):
            cu = _COS[u]
            total = 0.0
            for x in range(8):
                total += row[x] * cu[x]
            tmp[y][u] = total * _C[u] * 0.5
    out = [0.0] * 64
    for u in range(8):
        for v in range(8):
            cv = _COS[v]
            total = 0.0
            for y in range(8):
                total += tmp[y][u] * cv[y]
            out[v * 8 + u] = total * _C[v] * 0.5
    return out


def _category(value: int) -> int:
    return abs(int(value)).bit_length()


def _amp_bits(value: int, size: int) -> int:
    if value < 0:
        return value + (1 << size) - 1
    return value


def _encode_jpeg_pure(gray: bytes, w: int, h: int, quality: int = 85) -> bytes:
    """纯标准库 baseline JPEG（灰度、4:2:0 无关、标准 Huffman 表）。"""
    quant = _scaled_quant(quality)
    out = bytearray()
    out += b"\xff\xd8"  # SOI
    out += b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    # DQT（按 zigzag 顺序写）
    out += b"\xff\xdb" + struct.pack(">H", 2 + 1 + 64) + bytes([0x00])
    out += bytes(quant[z] for z in _ZIGZAG)
    # SOF0
    out += b"\xff\xc0" + struct.pack(">HBHHB", 11, 8, h, w, 1) + bytes([1, 0x11, 0])
    # DHT
    out += b"\xff\xc4" + struct.pack(">H", 2 + 1 + 16 + len(_DC_VALS)) + bytes([0x00])
    out += bytes(_DC_BITS) + bytes(_DC_VALS)
    out += b"\xff\xc4" + struct.pack(">H", 2 + 1 + 16 + len(_AC_VALS)) + bytes([0x10])
    out += bytes(_AC_BITS) + bytes(_AC_VALS)
    # SOS
    out += b"\xff\xda" + struct.pack(">HB", 8, 1) + bytes([1, 0x00, 0, 63, 0])

    writer = _BitWriter()
    prev_dc = 0
    blocks_x = (w + 7) // 8
    blocks_y = (h + 7) // 8
    for by in range(blocks_y):
        for bx in range(blocks_x):
            block = [0] * 64
            for y in range(8):
                sy = min(h - 1, by * 8 + y)
                base = sy * w
                for x in range(8):
                    sx = min(w - 1, bx * 8 + x)
                    block[y * 8 + x] = gray[base + sx] - 128
            coeffs = _fdct_block(block)
            zz = [0] * 64
            for i, z in enumerate(_ZIGZAG):
                value = coeffs[z] / float(quant[z])
                zz[i] = int(math.floor(value + 0.5))
            diff = zz[0] - prev_dc
            prev_dc = zz[0]
            size = _category(diff)
            code, length = _HUFF_DC[size]
            writer.write(code, length)
            if size:
                writer.write(_amp_bits(diff, size), size)
            run = 0
            for i in range(1, 64):
                value = zz[i]
                if value == 0:
                    run += 1
                    continue
                while run > 15:
                    code, length = _HUFF_AC[0xF0]
                    writer.write(code, length)
                    run -= 16
                size = _category(value)
                code, length = _HUFF_AC[(run << 4) | size]
                writer.write(code, length)
                writer.write(_amp_bits(value, size), size)
                run = 0
            if run > 0:
                code, length = _HUFF_AC[0x00]
                writer.write(code, length)
    writer.flush()
    out += writer.buf
    out += b"\xff\xd9"  # EOI
    return bytes(out)


def downscale_gray(gray: bytes, w: int, h: int, max_width: int) -> Tuple[bytes, int, int]:
    """等比缩到 max_width 以内（有 cv2 走 cv2.resize，否则最近邻抽样）。"""
    if max_width <= 0 or w <= max_width:
        return gray, w, h
    ratio = float(max_width) / float(w)
    nw = max(16, int(w * ratio))
    nh = max(16, int(h * ratio))
    if _has_cv2():
        try:
            import cv2  # type: ignore
            import numpy as np  # type: ignore

            arr = np.frombuffer(gray, dtype=np.uint8).reshape(h, w)
            resized = cv2.resize(arr, (nw, nh), interpolation=cv2.INTER_AREA)
            return resized.tobytes(), nw, nh
        except Exception:
            pass
    # 最近邻抽样（整数步长，够快）
    step_x = w / float(nw)
    step_y = h / float(nh)
    out = bytearray(nw * nh)
    idx = 0
    for y in range(nh):
        base = int(y * step_y) * w
        for x in range(nw):
            out[idx] = gray[base + int(x * step_x)]
            idx += 1
    return bytes(out), nw, nh


_CRED_RE = re.compile(r"(rtsp://[^:/@\s]+:)[^@\s]+@")


def mask_credentials(text: str) -> str:
    """把 rtsp://user:pass@host 里的口令换成 ***（日志/接口里绝不出现明文口令）。"""
    if not text:
        return text
    return _CRED_RE.sub(r"\1***@", text)


def _has_cv2() -> bool:
    from . import has

    return bool(has("cv2"))


def encode_jpeg_gray(
    gray: bytes, w: int, h: int, quality: int = 85, max_width: int = 1920, force_pure: bool = False
) -> bytes:
    """灰度 -> JPEG。

    - 有 opencv：cv2.imencode（快，且缩放到 max_width）
    - 没有 opencv：纯标准库编码器；为保证 <1 s 返回，会把图限到 ≤256 宽
      （现场树莓派上装了 opencv 或 ffmpeg，不会走到这条路）
    """
    if not gray or w <= 0 or h <= 0 or len(gray) < w * h:
        raise ValueError("灰度数据与尺寸不匹配")
    if not force_pure and max_width > 0:
        gray, w, h = downscale_gray(gray, w, h, max_width)
    if not force_pure and _has_cv2():
        try:
            import cv2  # type: ignore
            import numpy as np  # type: ignore

            arr = np.frombuffer(gray, dtype=np.uint8).reshape(h, w)
            ok, buf = cv2.imencode(
                ".jpg", arr, [int(cv2.IMWRITE_JPEG_QUALITY), int(max(1, min(100, quality)))]
            )
            if ok:
                return bytes(buf.tobytes())
        except Exception:
            pass
    if max_width > 256:
        gray, w, h = downscale_gray(gray, w, h, 256)
    return _encode_jpeg_pure(gray, w, h, quality)


def jpeg_dimensions(data: bytes) -> Tuple[Optional[int], Optional[int]]:
    """从 JPEG 字节流里读出宽高（给抓图记录用；读不出返回 None）。"""
    idx = 2
    try:
        while idx + 9 < len(data):
            if data[idx] != 0xFF:
                idx += 1
                continue
            marker = data[idx + 1]
            if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                idx += 2
                continue
            length = struct.unpack(">H", data[idx + 2 : idx + 4])[0]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                height = struct.unpack(">H", data[idx + 5 : idx + 7])[0]
                width = struct.unpack(">H", data[idx + 7 : idx + 9])[0]
                return width, height
            idx += 2 + length
    except Exception:
        return None, None
    return None, None


def jpeg_to_qscale(quality: int) -> int:
    """JPEG 质量 -> ffmpeg 的 -q:v（近似映射，够用即可）。"""
    quality = int(max(1, min(100, quality)))
    return int(max(2, min(31, round(31 - 0.29 * quality))))


# ==========================================================================
# 相机数据源
# ==========================================================================
class CameraSource:
    """一路相机的采集线程。"""

    def __init__(self, cam_cfg: Dict[str, Any], cfg, store=None, logger=None, simulate: bool = False,
                 sim_cfg: Optional[Dict[str, Any]] = None) -> None:
        self.cam = dict(cam_cfg)
        self.cfg = cfg
        self.store = store
        self._log = logger
        self.simulate = simulate
        self.sim_cfg = sim_cfg or {}

        self.id = str(self.cam.get("id"))
        self.name = str(self.cam.get("name") or self.id)
        role = str(self.cam.get("role") or "panorama")
        if role not in ("panorama", "detail"):
            # 契约 §2 的 role 只有两个取值，配错了不许原样吐给前端
            if self._log:
                self._log("warn", "rtsp-ingest", "%s 的 role=%r 非法，已按 panorama 处理" % (self.id, role))
            role = "panorama"
        self.role = role
        analysis = self.cam.get("analysis") or {}
        self.analysis_w = int(analysis.get("width") or cfg.get("analysis.width", 640) or 640)
        self.analysis_h = int(analysis.get("height") or cfg.get("analysis.height", 360) or 360)
        self.analysis_fps = float(analysis.get("fps") or cfg.get("analysis.max_fps", 5) or 5)
        if simulate:
            self.analysis_w = int(self.sim_cfg.get("width") or self.analysis_w)
            self.analysis_h = int(self.sim_cfg.get("height") or self.analysis_h)
            self.analysis_fps = float(self.sim_cfg.get("fps") or self.analysis_fps)

        self._frame: Optional[Frame] = None
        self._frame_lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._seq = 0
        self._sim_source = None
        self._proc: Optional[subprocess.Popen] = None
        self._stderr_lines: List[str] = []
        self._ffmpeg = shutil.which("ffmpeg")
        self._opencv_probe_done = False
        self._snapshot_lock = threading.Lock()
        self._snapshot_cache: Tuple[float, bytes] = (0.0, b"")

        # 状态（供 /api/v1/cameras 与看门狗使用）
        self.online = False
        self.failures = 0
        self.last_frame_ts = 0
        self.last_ok_ts = 0
        self.down_since: Optional[float] = None
        self.total_frames = 0
        self.backend = "simulate" if simulate else ("ffmpeg" if self._ffmpeg else "opencv")
        self._offline_event_sent = False

    # ---------------- 基本信息 ----------------
    @property
    def ip(self) -> str:
        return str(self.cam.get("ip") or "")

    @property
    def model(self) -> str:
        return str(self.cam.get("model") or "")

    @property
    def resolution(self) -> str:
        return str(self.cam.get("resolution") or "1920x1080")

    @property
    def fps(self) -> int:
        try:
            return int(self.cam.get("fps") or 25)
        except Exception:
            return 25

    @property
    def bitrate_kbps(self) -> int:
        try:
            return int(self.cam.get("bitrate_kbps") or 4096)
        except Exception:
            return 4096

    @property
    def ir_m(self) -> int:
        try:
            return int(self.cam.get("ir_m") or 0)
        except Exception:
            return 0

    @property
    def ptz_cfg(self) -> Optional[Dict[str, Any]]:
        value = self.cam.get("ptz")
        if isinstance(value, dict) and value:
            return value
        return None

    @property
    def has_ptz(self) -> bool:
        return self.ptz_cfg is not None

    @property
    def onvif(self) -> bool:
        return bool(self.cam.get("onvif"))

    def rtsp_url(self, mask_password: bool = True) -> str:
        user = self.cam.get("rtsp_user") or "admin"
        password = self.cam.get("rtsp_password") or ""
        if mask_password and password:
            password = "***"
        port = int(self.cam.get("rtsp_port") or 554)
        path = self.cam.get("rtsp_path") or "/Streaming/Channels/101"
        return "rtsp://%s:%s@%s:%d%s" % (user, password, self.ip, port, path)

    # ---------------- 生命周期 ----------------
    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, name="cam-%s" % self.id, daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 5.0) -> None:
        self._running = False
        proc = self._proc
        if proc is not None:
            try:
                proc.terminate()
            except Exception:
                pass
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def latest(self) -> Optional[Frame]:
        with self._frame_lock:
            return self._frame

    # ---------------- 采集主循环 ----------------
    def _logw(self, level: str, msg: str) -> None:
        if self._log:
            self._log(level, "rtsp-ingest", msg)

    def _run(self) -> None:
        backoff = 1.0
        while self._running:
            started_ok = False
            try:
                if self.simulate:
                    started_ok = self._run_simulate()
                elif self._ffmpeg:
                    started_ok = self._run_ffmpeg()
                else:
                    started_ok = self._run_opencv()
            except Exception as exc:  # 任何异常都不能让线程死掉
                self._logw("warn", "%s 采集异常：%s" % (self.id, exc))
            if not self._running:
                break
            self.failures += 1
            if self.down_since is None:
                self.down_since = time.time()
            self.online = False
            if started_ok:
                backoff = 1.0  # 曾经成功过：下次失败从 1 s 重新退避
            self._logw(
                "warn",
                "%s 拉流中断（第 %d 次），%.1f s 后重连（后端 %s）"
                % (self.id, self.failures, backoff, self.backend),
            )
            slept = 0.0
            while self._running and slept < backoff:
                time.sleep(0.2)
                slept += 0.2
            backoff = min(60.0, backoff * 2.0) * (0.85 + 0.3 * random.random())

    def _mark_ok(self, frame: Frame) -> None:
        now = time.time()
        with self._frame_lock:
            self._frame = frame
        self._seq += 1
        frame.seq = self._seq
        self.total_frames += 1
        self.last_frame_ts = now
        if not self.online:
            if self.failures:
                self._logw("info", "%s 重连成功（第 %d 次尝试后）" % (self.id, self.failures))
            self.online = True
            self.down_since = None
            self.failures = 0
            self._offline_event_sent = False
        self.last_ok_ts = now

    # ---- ffmpeg 后端 ----
    def _run_ffmpeg(self) -> bool:
        rtsp_timeout_s = float(self.cfg.get("detector.rtsp_timeout_s", 15) or 15)
        cmd = [
            self._ffmpeg or "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel", "error",
            "-rtsp_transport", "tcp",
            # socket 超时（微秒）：相机关机/网线掉了能快速失败，而不是干等 2 分钟
            "-timeout", str(int(rtsp_timeout_s * 1_000_000)),
            "-i", self.rtsp_url(mask_password=False),
            "-an", "-sn", "-dn",
            "-vf", "scale=%d:%d,fps=%s" % (self.analysis_w, self.analysis_h, self.analysis_fps),
            "-f", "rawvideo",
            "-pix_fmt", "gray",
            "-",
        ]
        self._logw("info", "%s 启动 ffmpeg 拉流：%dx%d @ %sfps" % (self.id, self.analysis_w, self.analysis_h, self.analysis_fps))
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=self.analysis_w * self.analysis_h
        )
        self._proc = proc
        drain = threading.Thread(target=self._drain_stderr, args=(proc,), daemon=True)
        drain.start()
        self._last_read_mono = time.monotonic()
        monitor = threading.Thread(target=self._stall_monitor, args=(proc,), daemon=True)
        monitor.start()
        frame_bytes = self.analysis_w * self.analysis_h
        ok = False
        try:
            stdout = proc.stdout
            assert stdout is not None
            while self._running:
                buf = self._read_exact(stdout, frame_bytes)
                if buf is None:
                    break
                self._last_read_mono = time.monotonic()
                ok = True
                self._mark_ok(Frame(buf, self.analysis_w, self.analysis_h, camera_id=self.id))
        finally:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            self._proc = None
            if self._stderr_lines:
                tail = mask_credentials(" | ".join(self._stderr_lines[-3:]))
                self._logw("warn", "%s ffmpeg 输出：%s" % (self.id, tail))
                self._stderr_lines = []
        return ok

    def _stall_monitor(self, proc: subprocess.Popen) -> None:
        """看门狗：ffmpeg 卡住不出帧时把它杀掉，让上层走重连。

        （只靠 app.py 的看门狗只能把 online 置 false，没法解除 stdout 上的阻塞读。）
        """
        stall_s = float(self.cfg.get("detector.stream_stall_s", 12) or 12)
        while self._running and proc.poll() is None:
            time.sleep(0.5)
            if time.monotonic() - getattr(self, "_last_read_mono", time.monotonic()) > stall_s:
                self._logw("warn", "%s 超过 %.0f s 没有新帧，重启拉流进程" % (self.id, stall_s))
                try:
                    proc.kill()
                except Exception:
                    pass
                return

    @staticmethod
    def _read_exact(stream, size: int) -> Optional[bytes]:
        chunks = []
        remaining = size
        while remaining > 0:
            chunk = stream.read(remaining)
            if not chunk:
                return None
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def _drain_stderr(self, proc: subprocess.Popen) -> None:
        try:
            assert proc.stderr is not None
            for line in proc.stderr:
                text = line.decode("utf-8", "replace").strip()
                if text:
                    self._stderr_lines.append(text)
                    if len(self._stderr_lines) > 20:
                        self._stderr_lines.pop(0)
        except Exception:
            pass

    # ---- OpenCV 后端 ----
    def _run_opencv(self) -> bool:
        try:
            import cv2  # type: ignore
        except Exception:
            if not self._opencv_probe_done:
                self._opencv_probe_done = True
                note_degraded(
                    "camera",
                    "既没有 ffmpeg 也没有 opencv-python：无法拉 RTSP，相机将一直 offline（simulate 模式不受影响）",
                )
                self._logw("error", "既没有 ffmpeg 也没有 opencv-python，无法拉流：%s" % self.id)
            time.sleep(5)
            return False
        cap = cv2.VideoCapture(self.rtsp_url(mask_password=False), cv2.CAP_FFMPEG)
        if not cap.isOpened():
            self._logw("warn", "%s OpenCV 打开失败" % self.id)
            try:
                cap.release()
            except Exception:
                pass
            return False
        self._logw("info", "%s 启动 OpenCV 拉流（ffmpeg 不可用时的兜底后端）" % self.id)
        interval = 1.0 / max(0.5, self.analysis_fps)
        ok = False
        try:
            while self._running:
                grabbed = cap.grab()
                if not grabbed:
                    break
                ret, frame = cap.retrieve()
                if not ret or frame is None:
                    continue
                ok = True
                resized = cv2.resize(frame, (self.analysis_w, self.analysis_h))
                gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
                self._mark_ok(Frame(gray.tobytes(), self.analysis_w, self.analysis_h, camera_id=self.id))
                time.sleep(interval)
        finally:
            try:
                cap.release()
            except Exception:
                pass
        return ok

    def _mark_stalled(self) -> None:
        """视频流卡住/掉线：先把 online 置 false（事件由看门狗按 30 s 规则发）。"""
        if self.online:
            self._logw("warn", "%s 视频流中断" % self.id)
        self.online = False
        if self.down_since is None:
            self.down_since = time.time()

    # ---- 模拟源 ----
    def _run_simulate(self) -> bool:
        if self._sim_source is None:
            from .simulate import SimSource  # 延迟导入，避免循环依赖

            self._sim_source = SimSource(self.id, self.cam, self.sim_cfg)
            self._logw("info", "%s 使用模拟视频源（%dx%d @ %sfps）" % (self.id, self.analysis_w, self.analysis_h, self.analysis_fps))
        interval = 1.0 / max(0.5, self.analysis_fps)
        stalled = False
        while self._running:
            frame = self._sim_source.next_frame(self.analysis_w, self.analysis_h)
            if frame is None:
                # 剧本里的"相机掉线"阶段：不退出线程，只是暂时没有帧
                if not stalled:
                    stalled = True
                    self.failures += 1
                    self._logw("warn", "%s 模拟阶段：相机掉线（用于演示 offline 事件）" % self.id)
                self._mark_stalled()
                time.sleep(1.0)
                continue
            if stalled:
                self._logw("info", "%s 模拟阶段：相机恢复" % self.id)
                stalled = False
            self._mark_ok(frame)
            time.sleep(interval)
        return True

    # ---------------- 抓图 ----------------
    def snapshot_jpeg(self, max_width: int = 1920, quality: int = 85) -> Optional[bytes]:
        """抓一张 JPEG。优先 ffmpeg 抓帧（真机），否则用最新分析帧编码。"""
        now = time.time()
        with self._snapshot_lock:
            cached_ts, cached = self._snapshot_cache
            if cached and (now - cached_ts) < 5.0:
                return cached
        data: Optional[bytes] = None
        if not self.simulate and self._ffmpeg:
            data = self._snapshot_ffmpeg(max_width, quality)
        if data is None:
            frame = self.latest()
            if frame is not None:
                try:
                    data = encode_jpeg_gray(frame.gray, frame.w, frame.h, quality, max_width)
                except Exception as exc:
                    self._logw("warn", "%s 抓图编码失败：%s" % (self.id, exc))
                    data = None
        if data:
            with self._snapshot_lock:
                self._snapshot_cache = (now, data)
        return data

    def _snapshot_ffmpeg(self, max_width: int, quality: int) -> Optional[bytes]:
        cmd = [
            self._ffmpeg or "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel", "error",
            "-rtsp_transport", "tcp",
            "-timeout", "6000000",
            "-i", self.rtsp_url(mask_password=False),
            "-frames:v", "1",
        ]
        if max_width > 0:  # max_width<=0 = upload.policy=full，保留原始分辨率（不加 scale）
            cmd += ["-vf", "scale=%d:-2" % int(max_width)]
        cmd += [
            "-q:v", str(jpeg_to_qscale(quality)),
            "-f", "image2",
            "-c:v", "mjpeg",
            "-",
        ]
        try:
            proc = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=8, check=False
            )
            if proc.returncode == 0 and proc.stdout[:2] == b"\xff\xd8":
                return bytes(proc.stdout)
            self._logw("warn", "%s ffmpeg 抓图失败（code=%s），改用最新帧编码" % (self.id, proc.returncode))
        except Exception as exc:
            self._logw("warn", "%s ffmpeg 抓图异常：%s" % (self.id, exc))
        return None


# ==========================================================================
# 本地录像（全码流）
# ==========================================================================
class Recorder:
    """ffmpeg -c copy 分段录像到 SD 卡。没有 ffmpeg 就明确降级并记日志。"""

    def __init__(self, camera: CameraSource, store, logger=None) -> None:
        self.camera = camera
        self.store = store
        self._log = logger
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._proc: Optional[subprocess.Popen] = None
        self._ffmpeg = shutil.which("ffmpeg")
        self.dir = os.path.join(store.recording_dir, camera.id)
        self.ok = False
        self.last_error = ""
        self._started_at = 0.0

    def _logw(self, level: str, msg: str) -> None:
        if self._log:
            self._log(level, "recorder", msg)

    def start(self) -> None:
        if self._thread is not None:
            return
        if not self._ffmpeg:
            self.last_error = "未安装 ffmpeg，无法本地录像"
            note_degraded("recorder", "%s：未安装 ffmpeg，本地全码流录像不可用（检测/抓图不受影响）" % self.camera.id)
            self._logw("warn", "%s 未安装 ffmpeg，跳过录像" % self.camera.id)
            return
        os.makedirs(self.dir, exist_ok=True)
        self._running = True
        self._thread = threading.Thread(target=self._run, name="rec-%s" % self.camera.id, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._proc is not None:
            try:
                self._proc.terminate()
            except Exception:
                pass
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _run(self) -> None:
        segment = int(self.camera.cfg.get("record.segment_s", 600) or 600)
        pattern = os.path.join(self.dir, "%Y%m%d-%H%M%S.mp4")
        while self._running:
            cmd = [
                self._ffmpeg or "ffmpeg",
                "-nostdin",
                "-hide_banner",
                "-loglevel", "error",
                "-rtsp_transport", "tcp",
                "-timeout", "15000000",
                "-i", self.camera.rtsp_url(mask_password=False),
                "-c", "copy",
                "-an",
                "-f", "segment",
                "-segment_time", str(segment),
                "-segment_format", "mp4",
                "-reset_timestamps", "1",
                "-strftime", "1",
                pattern,
            ]
            try:
                self._logw("info", "%s 开始本地录像（分段 %d s）" % (self.camera.id, segment))
                self._started_at = time.time()
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, bufsize=0
                )
                self._proc = proc
                self.ok = True  # 进程起来了；是否真的在录，看 healthy()
                _out, err = proc.communicate()
                self.ok = False
                if err:
                    self.last_error = mask_credentials(
                        err.decode("utf-8", "replace").strip().splitlines()[-1][:300]
                    )
                    self._logw("warn", "%s 录像中断：%s" % (self.camera.id, self.last_error))
            except Exception as exc:
                self.last_error = str(exc)
                self._logw("warn", "%s 录像进程异常：%s" % (self.camera.id, exc))
            finally:
                self._proc = None
            if not self._running:
                break
            time.sleep(10)  # 录像失败退避

    def healthy(self) -> bool:
        """真的在录像吗？判据是"本次启动之后确实写出了分段文件"，而不是"进程还活着"。

        （相机连不上时 ffmpeg 会起得来但一个字节也写不出，那种情况下报 recording=true
        就是在骗人——现场会以为在录，其实卡里什么都没有。）
        """
        proc = self._proc
        if proc is None or proc.poll() is not None:
            return False
        try:
            newest = 0.0
            for name in os.listdir(self.dir):
                if name.endswith(".mp4"):
                    newest = max(newest, os.path.getmtime(os.path.join(self.dir, name)))
        except OSError:
            return False
        return newest >= self._started_at > 0

    def storage_bytes_per_day(self) -> int:
        return int(self.camera.bitrate_kbps * 86400 / 8.0 * 1000)


# ==========================================================================
# 相机管理
# ==========================================================================
class CameraManager:
    """所有相机的集合：启动/停止、状态查询、契约 §2 的 JSON 组装。"""

    def __init__(self, cfg, store, logger=None, simulate: bool = False) -> None:
        self.cfg = cfg
        self.store = store
        self._log = logger
        self.simulate = simulate
        sim_cfg = cfg.get("sim", {}) or {}
        self.cameras: List[CameraSource] = []
        self.recorders: List[Recorder] = []
        for cam_cfg in cfg.get("cameras", []) or []:
            self.cameras.append(
                CameraSource(cam_cfg, cfg, store=store, logger=logger, simulate=simulate, sim_cfg=sim_cfg)
            )

    def get(self, camera_id: str) -> Optional[CameraSource]:
        for cam in self.cameras:
            if cam.id == camera_id:
                return cam
        return None

    def start(self) -> None:
        for cam in self.cameras:
            cam.start()
        if self.cfg.get("record.local_full_stream", True):
            for cam in self.cameras:
                if self.simulate:
                    continue  # 模拟模式没有真流可录
                recorder = Recorder(cam, self.store, logger=self._log)
                recorder.start()
                self.recorders.append(recorder)
        elif self._log:
            self._log("info", "recorder", "record.local_full_stream=false，本地全码流录像已关闭")

    def stop(self) -> None:
        for recorder in self.recorders:
            recorder.stop()
        for cam in self.cameras:
            cam.stop()

    def json(self, ptz_provider=None) -> List[Dict[str, Any]]:
        """契约 §2 的相机数组；`ptz` 由 ptz_provider(camera) 提供（无云台给 null）。"""
        out = []
        for cam in self.cameras:
            item: Dict[str, Any] = {
                "id": cam.id,
                "name": cam.name,
                "role": cam.role,
                "model": cam.model,
                "ip": cam.ip,
                "rtsp": cam.rtsp_url(mask_password=True),
                "onvif": cam.onvif,
                "online": bool(cam.online),
                "resolution": cam.resolution,
                "fps": cam.fps,
                "bitrate_kbps": cam.bitrate_kbps,
                "ir_m": cam.ir_m,
                "ptz": None,
                "snapshot_url": "/api/v1/cameras/%s/snapshot" % cam.id,
            }
            if ptz_provider is not None and cam.has_ptz:
                item["ptz"] = ptz_provider(cam)
            out.append(item)
        return out

    def recording(self) -> bool:
        """是否真的在往卡里写录像（不是"配置里打开了录像"）。"""
        return bool(self.recorders) and any(r.healthy() for r in self.recorders)

    def bytes_per_day(self) -> int:
        total = 0
        for cam in self.cameras:
            total += int(cam.bitrate_kbps * 86400 / 8.0 * 1000)
        return total


__all__ = [
    "Frame",
    "mask_credentials",
    "CameraSource",
    "CameraManager",
    "Recorder",
    "encode_jpeg_gray",
    "downscale_gray",
    "jpeg_dimensions",
    "jpeg_to_qscale",
]
