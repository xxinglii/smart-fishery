"""鱼塘视觉监控系统 · 树莓派端固件应用。

设计目标（与《视觉系统_API契约_v1.md》一一对应）：

- 唯一的对外接口是 HTTP + SSE，字段/类型/枚举严格照契约，不做任何增删改。
- 无相机、无第三方依赖也能跑：`python -m yutang_vision --simulate` 生成合规假数据，
  供前端联调；默认模式下相机连不上不会崩，只会把相机标成 online=false 并发 offline 事件。
- 4G 友好：默认只回传缩略图，抓图 1920 宽 / JPEG q85，SSE 心跳 15 s，大响应支持 ?limit=。
- 检测只做契约 §8 的 5 类，禁止数鱼/数饲料/估重/估生物量（有项目内证据否决）。
"""

from __future__ import annotations

import threading
from typing import Dict, List

__version__ = "1.0.0"

#: 事件证据等级。v1 全部为 C（演示级）：没有任何现场标定数据，
#: 因此不得声称 A（实测）或 B（经验）。见 README「证据等级」一节。
EVIDENCE_LEVEL = "C"

_DEGRADED_LOCK = threading.Lock()
_DEGRADED: List[Dict[str, str]] = []


def note_degraded(component: str, reason: str) -> None:
    """登记一条"降级"记录（缺依赖/能力不可用）。

    降级记录会：① 打到标准输出与 /api/v1/logs；② 以 ok=false 的形式出现在
    /api/v1/health 的 services 列表里（契约里 services 是 {name, ok} 数组，
    增加条目不影响既有字段）。
    """
    with _DEGRADED_LOCK:
        for item in _DEGRADED:
            if item["component"] == component and item["reason"] == reason:
                return
        _DEGRADED.append({"component": component, "reason": reason})


def degraded_notes() -> List[Dict[str, str]]:
    """返回当前所有降级记录（副本）。"""
    with _DEGRADED_LOCK:
        return [dict(x) for x in _DEGRADED]


# --------------------------------------------------------------------------
# 可选依赖探测（缺了必须能跑，只是能力降级）
# --------------------------------------------------------------------------
def _probe_optional() -> Dict[str, object]:
    caps: Dict[str, object] = {}

    try:
        import numpy  # type: ignore

        caps["numpy"] = numpy
    except Exception:  # pragma: no cover - 取决于部署环境
        caps["numpy"] = None
        note_degraded("numpy", "未安装 numpy：运动检测退化为纯标准库字节异或近似，精度下降")

    try:
        import cv2  # type: ignore

        caps["cv2"] = cv2
    except Exception:  # pragma: no cover
        caps["cv2"] = None
        note_degraded("opencv-python", "未安装 opencv-python：目标检测禁用，surface_aggregation 用网格近似")

    try:
        import yaml  # type: ignore

        caps["yaml"] = yaml
    except Exception:  # pragma: no cover
        caps["yaml"] = None
        note_degraded("pyyaml", "未安装 pyyaml：改用内置极简 YAML 子集解析器（块映射/列表/行内流式）")

    try:
        import onvif  # type: ignore  # noqa: F401

        caps["onvif"] = True
    except Exception:  # pragma: no cover
        caps["onvif"] = False
        note_degraded("onvif-zeep", "未安装 onvif-zeep：云台走本地状态机（mock），接口行为一致但不动真机")

    return caps


CAPS: Dict[str, object] = _probe_optional()


def has(mod: str) -> bool:
    """可选依赖是否可用（'numpy' / 'cv2' / 'yaml' / 'onvif'）。"""
    v = CAPS.get(mod)
    return v is not None and v is not False


__all__ = [
    "__version__",
    "EVIDENCE_LEVEL",
    "CAPS",
    "has",
    "note_degraded",
    "degraded_notes",
]
