"""4G 信号 / 流量统计。

诚实原则：**读得到才给数，读不到给 None，绝不编**。
- 流量：Linux 下读 `/proc/net/dev`，按接口名过滤（默认把 eth/wlan/usb/wwan 都算上，
  因为 4G CPE 通常以以太网/USB 网卡形式呈现给树莓派）。累计值持久化在 SQLite，
  所以重启不会把"本月已用流量"清零。
- 信号：`mmcli`（ModemManager）可用时读 RSSI 与运营商；读不到给 None。
  多数 4G CPE 以路由模式工作，树莓派看不到 4G 模组，此时 rssi_dbm / carrier 只能是
  None —— 这是**正常现象**，不是 bug（README 排障章节有说明）。
- 非 Linux（比如开发用的 macOS）：没有 /proc -> uplink_kbps / month_bytes 给 None。
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from . import note_degraded


def _run(cmd: List[str], timeout: float = 3.0) -> Optional[str]:
    try:
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=timeout, check=False
        )
        if proc.returncode != 0:
            return None
        return proc.stdout.decode("utf-8", "replace")
    except Exception:
        return None


def read_proc_net_dev(
    include: Optional[List[str]] = None, exclude: Optional[List[str]] = None
) -> Optional[Tuple[int, int]]:
    """返回 (rx_bytes, tx_bytes) 累计值；非 Linux 返回 None。"""
    path = "/proc/net/dev"
    if not os.path.exists(path):
        return None
    include = include or ["eth", "wlan", "usb", "wwan", "en", "enp", "end"]
    exclude = exclude or ["lo", "docker", "veth", "br-"]
    rx_total = tx_total = 0
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                if ":" not in line:
                    continue
                iface, _, rest = line.partition(":")
                iface = iface.strip()
                if any(bad in iface for bad in exclude):
                    continue
                if not any(good in iface for good in include):
                    continue
                fields = rest.split()
                if len(fields) < 9:
                    continue
                rx_total += int(fields[0])
                tx_total += int(fields[8])
    except Exception:
        return None
    return rx_total, tx_total


def read_mmcli_signal() -> Tuple[Optional[int], Optional[str]]:
    """用 mmcli 读 (rssi_dbm, carrier)；读不到返回 (None, None)。"""
    if not shutil.which("mmcli"):
        return None, None
    rssi: Optional[int] = None
    text = _run(["mmcli", "-m", "any", "--signal-get"])
    if text:
        match = re.search(r"rssi\s*:\s*(-?\d+(?:\.\d+)?)", text)
        if match:
            try:
                rssi = int(round(float(match.group(1))))
            except ValueError:
                rssi = None
    carrier: Optional[str] = None
    info = _run(["mmcli", "-m", "any"])
    if info:
        match = re.search(r"operator name\s*:\s*(.+)", info)
        if match:
            carrier = match.group(1).strip()
    return rssi, carrier


class NetMeter:
    """周期采样网络用量，产出契约 §1 的 net 对象。"""

    def __init__(self, cfg, store, logger=None) -> None:
        self.cfg = cfg
        self.store = store
        self._log = logger
        self._lock = threading.RLock()
        self._last: Optional[Tuple[int, int, float]] = None  # (rx, tx, monotonic)
        self._uplink_kbps: Optional[int] = None
        self._month_bytes: Optional[int] = None
        self._rssi: Optional[int] = None
        self._carrier: Optional[str] = None
        self._mmcli_ok: Optional[bool] = None
        self._mmcli_checked = 0.0
        self._warned_proc = False
        self._init_month_baseline()

    def _warn(self, msg: str) -> None:
        if self._log:
            self._log("warn", "netmeter", msg)

    # ---------------- 月流量累计 ----------------
    def _month_key(self) -> str:
        return time.strftime("%Y-%m", time.localtime())

    def _init_month_baseline(self) -> None:
        totals = read_proc_net_dev(
            self.cfg.get("net.iface_include"), self.cfg.get("net.iface_exclude")
        )
        if self.store.get_counter_text("net_month_key") != self._month_key():
            self.store.set_counter("net_month_key", self._month_key())
            self.store.set_counter("net_month_base_total", totals[1] if totals else 0)
            self.store.set_counter("net_month_bytes", 0)
            if totals:
                self._warn("检测到新的计费月（%s），本月流量计数已清零" % self._month_key())

    def _update_month_bytes(self, tx_total: int) -> Optional[int]:
        if self.store.get_counter_text("net_month_key") != self._month_key():
            self._init_month_baseline()
        base_total = self.store.get_counter("net_month_base_total") or 0
        base_bytes = self.store.get_counter("net_month_bytes") or 0
        value = base_bytes + max(0, tx_total - base_total)
        self.store.set_counter("net_month_bytes", value)
        return value

    # ---------------- 采样 ----------------
    def sample(self) -> Dict[str, Any]:
        now = time.monotonic()
        totals = read_proc_net_dev(
            self.cfg.get("net.iface_include"), self.cfg.get("net.iface_exclude")
        )
        if totals is not None:
            rx, tx = totals
            with self._lock:
                if self._last is not None:
                    dt = max(0.5, now - self._last[2])
                    self._uplink_kbps = int(round(max(0, tx - self._last[1]) * 8 / dt / 1000.0))
                self._last = (rx, tx, now)
                uplink = self._uplink_kbps
            self._month_bytes = self._update_month_bytes(tx)
        else:
            if not self._warned_proc:
                self._warned_proc = True
                note_degraded(
                    "netmeter",
                    "未找到 /proc/net/dev（非 Linux？）：net.uplink_kbps / net.month_bytes 返回 null",
                )
                self._warn(
                    "未找到 /proc/net/dev，net.uplink_kbps / net.month_bytes 将返回 null（不编数据）"
                )
            with self._lock:
                uplink = self._uplink_kbps

        # mmcli 每 60 s 最多探一次，避免刷子进程
        if self.cfg.get("net.mmcli_enable", True):
            with self._lock:
                need = self._mmcli_checked == 0.0 or (now - self._mmcli_checked) > 60.0
            if need:
                rssi, carrier = read_mmcli_signal()
                with self._lock:
                    self._mmcli_checked = now
                    self._rssi, self._carrier = rssi, carrier
                    if self._mmcli_ok is None:
                        self._mmcli_ok = rssi is not None
                        if not self._mmcli_ok:
                            note_degraded(
                                "mmcli",
                                "未读到 4G 模组信号（CPE 路由模式下树莓派看不到模组）："
                                "net.rssi_dbm / net.carrier 返回 null",
                            )
        with self._lock:
            rssi, carrier = self._rssi, self._carrier
            month_bytes = self._month_bytes

        cfg_carrier = self.cfg.get("net.carrier") or None
        try:
            quota_bytes = int(float(self.cfg.get("upload.quota_gb_month") or 0) * (1024 ** 3))
        except Exception:
            quota_bytes = 0
        return {
            "type": self.cfg.get("net.type", "4g"),
            "rssi_dbm": rssi,
            "carrier": cfg_carrier or carrier,
            "uplink_kbps": uplink,
            "month_bytes": month_bytes,
            "month_quota_bytes": quota_bytes,
        }


__all__ = ["NetMeter", "read_proc_net_dev", "read_mmcli_signal"]
