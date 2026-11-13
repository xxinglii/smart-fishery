"""事件总线 + SSE 推送。

- 进程内发布/订阅，主题目前只有 `event`（SSE 用）与 `log`（内部用）。
- 每个订阅者一个定长队列：4G 下客户端慢/断线时**丢最旧的**而不是无限堆积，
  丢包数量会计入日志，绝不阻塞采集线程。
- SSE 心跳在 app.py 里做（15 s 一条注释行），这里只管投递。
"""

from __future__ import annotations

import itertools
import queue
import threading
import time
from typing import Any, Dict, List, Optional


class Subscription:
    """一个订阅者（通常对应一条 SSE 连接）。"""

    _ids = itertools.count(1)

    def __init__(self, topics: Optional[List[str]] = None, maxsize: int = 256) -> None:
        self.id = next(Subscription._ids)
        self.topics = set(topics) if topics else None  # None = 全部主题
        self.queue: "queue.Queue[Dict[str, Any]]" = queue.Queue(maxsize=maxsize)
        self.dropped = 0
        self.created_at = int(time.time())

    def matches(self, topic: str) -> bool:
        return self.topics is None or topic in self.topics

    def put(self, message: Dict[str, Any]) -> bool:
        """非阻塞投递；队列满时丢最旧的一条再放新的。"""
        try:
            self.queue.put_nowait(message)
            return True
        except queue.Full:
            try:
                self.queue.get_nowait()
                self.dropped += 1
                self.queue.put_nowait(message)
            except (queue.Empty, queue.Full):
                self.dropped += 1
            return False

    def get(self, timeout: float) -> Optional[Dict[str, Any]]:
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None


class Bus:
    """极简事件总线。线程安全。"""

    def __init__(self, on_drop=None) -> None:
        self._lock = threading.RLock()
        self._subs: List[Subscription] = []
        self._on_drop = on_drop
        self._published = 0

    def subscribe(self, topics: Optional[List[str]] = None, maxsize: int = 256) -> Subscription:
        sub = Subscription(topics=topics, maxsize=maxsize)
        with self._lock:
            self._subs.append(sub)
        return sub

    def unsubscribe(self, sub: Subscription) -> None:
        with self._lock:
            if sub in self._subs:
                self._subs.remove(sub)

    def publish(self, topic: str, data: Dict[str, Any]) -> int:
        """发布一条消息，返回成功入队的订阅者数量。"""
        message = {"topic": topic, "ts": int(time.time()), "data": data}
        with self._lock:
            subs = list(self._subs)
            self._published += 1
        delivered = 0
        for sub in subs:
            if not sub.matches(topic):
                continue
            before = sub.dropped
            sub.put(message)
            if sub.dropped > before and self._on_drop:
                self._on_drop(sub, topic)
            else:
                delivered += 1
        return delivered

    @property
    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subs)

    @property
    def published_count(self) -> int:
        return self._published


__all__ = ["Bus", "Subscription"]
