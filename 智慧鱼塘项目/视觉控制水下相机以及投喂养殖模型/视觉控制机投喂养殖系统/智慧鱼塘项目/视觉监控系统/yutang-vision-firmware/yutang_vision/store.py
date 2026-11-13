"""SQLite 存储：事件 / 指标 / 日志 / 抓图（落盘与清理）。

要点：
- 单连接 + RLock（够用：写入频率是每秒个位数），**WAL** 模式，`synchronous=NORMAL`。
- 所有时间戳都是 **Unix 秒整数**（契约 §0）。
- 抓图文件按天分目录：`data/snapshots/YYYY-MM-DD/<ts>_<camera_id>.jpg`，DB 里只存路径。
- 磁盘剩余不足时自动清理**最旧抓图**（先按保留天数清，再按剩余空间清），并记日志。
- 事件 ID 形如 `ev-20260919-0007`（按天自增），与契约示例一致。
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import threading
import time
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

#: 契约 §3 事件类型（§8 的五类 + 通用 motion）
EVENT_TYPES: Tuple[str, ...] = (
    "splash_activity",
    "surface_aggregation",
    "person",
    "offline",
    "tamper",
    "motion",
)
SEVERITIES: Tuple[str, ...] = ("info", "notice", "warn", "critical")
SNAPSHOT_TRIGGERS: Tuple[str, ...] = ("interval", "event", "manual")
LOG_LEVELS: Tuple[str, ...] = ("debug", "info", "warn", "error")

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id            TEXT PRIMARY KEY,
    ts            INTEGER NOT NULL,
    camera_id     TEXT NOT NULL,
    type          TEXT NOT NULL,
    severity      TEXT NOT NULL,
    confidence    REAL NOT NULL,
    title         TEXT NOT NULL,
    detail        TEXT NOT NULL,
    metric        TEXT NOT NULL,
    snapshot_path TEXT,
    clip_path     TEXT,
    acked         INTEGER NOT NULL DEFAULT 0,
    evidence      TEXT NOT NULL DEFAULT 'C'
);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts DESC);
CREATE INDEX IF NOT EXISTS idx_events_type_ts ON events(type, ts DESC);

CREATE TABLE IF NOT EXISTS metrics (
    camera_id TEXT NOT NULL,
    ts        INTEGER NOT NULL,
    v_value   REAL NOT NULL,
    PRIMARY KEY (camera_id, ts)
);

CREATE TABLE IF NOT EXISTS logs (
    ts    INTEGER NOT NULL,
    level TEXT NOT NULL,
    src   TEXT NOT NULL,
    msg   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_logs_ts ON logs(ts DESC);

CREATE TABLE IF NOT EXISTS snapshots (
    ts        INTEGER NOT NULL,
    camera_id TEXT NOT NULL,
    path      TEXT NOT NULL,
    trigger   TEXT NOT NULL,
    width     INTEGER,
    height    INTEGER,
    bytes     INTEGER,
    PRIMARY KEY (ts, camera_id)
);
CREATE INDEX IF NOT EXISTS idx_snapshots_ts ON snapshots(ts DESC);

CREATE TABLE IF NOT EXISTS counters (
    k TEXT PRIMARY KEY,
    v TEXT NOT NULL
);
"""


def _now() -> int:
    return int(time.time())


class Store:
    """事件/指标/日志/抓图的统一存储层。"""

    def __init__(self, data_dir: str, logger=None) -> None:
        self.data_dir = os.path.abspath(data_dir)
        self.db_path = os.path.join(self.data_dir, "yutang.db")
        self.snapshot_dir = os.path.join(self.data_dir, "snapshots")
        self.recording_dir = os.path.join(self.data_dir, "recordings")
        for path in (self.data_dir, self.snapshot_dir, self.recording_dir):
            os.makedirs(path, exist_ok=True)
        self._lock = threading.RLock()
        self._log = logger
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=15.0)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------
    def _exec(self, sql: str, params: Sequence[Any] = ()) -> sqlite3.Cursor:
        with self._lock:
            cur = self._conn.execute(sql, params)
            return cur

    def _commit(self) -> None:
        with self._lock:
            self._conn.commit()

    def _warn(self, msg: str) -> None:
        if self._log:
            self._log("warn", "store", msg)

    # ------------------------------------------------------------------
    # 通用计数/状态键值（月流量基线、事件序号等）
    # ------------------------------------------------------------------
    def get_counter_text(self, key: str) -> Optional[str]:
        row = self._exec("SELECT v FROM counters WHERE k=?", (key,)).fetchone()
        return str(row["v"]) if row else None

    def get_counter(self, key: str) -> Optional[int]:
        raw = self.get_counter_text(key)
        if raw is None or raw == "":
            return None
        try:
            return int(raw)
        except ValueError:
            return None

    def set_counter(self, key: str, value) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO counters(k, v) VALUES(?,?)", (key, str(value))
            )
            self._conn.commit()

    # ------------------------------------------------------------------
    # 事件
    # ------------------------------------------------------------------
    def _next_event_id(self, ts: int) -> str:
        day = time.strftime("%Y%m%d", time.localtime(ts))
        key = "event_seq_%s" % day
        seq = (self.get_counter(key) or 0) + 1
        self.set_counter(key, seq)
        return "ev-%s-%04d" % (day, seq)

    def add_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """写入事件并返回契约形状的事件对象。"""
        ts = int(event.get("ts") or _now())
        eid = event.get("id") or self._next_event_id(ts)
        metric = event.get("metric") or {}
        row = (
            eid,
            ts,
            str(event.get("camera_id") or ""),
            str(event.get("type") or "motion"),
            str(event.get("severity") or "info"),
            float(event.get("confidence") or 0.0),
            str(event.get("title") or ""),
            str(event.get("detail") or ""),
            json.dumps(metric, ensure_ascii=False),
            event.get("snapshot_path"),
            event.get("clip_path"),
            1 if event.get("acked") else 0,
            str(event.get("evidence") or "C"),
        )
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO events(id, ts, camera_id, type, severity, confidence,"
                " title, detail, metric, snapshot_path, clip_path, acked, evidence)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                row,
            )
            self._conn.commit()
        return self.get_event(eid)  # type: ignore[return-value]

    def _row_to_event(self, row: sqlite3.Row) -> Dict[str, Any]:
        try:
            metric = json.loads(row["metric"]) if row["metric"] else {}
        except Exception:
            metric = {}
        eid = row["id"]
        return {
            "id": eid,
            "ts": int(row["ts"]),
            "camera_id": row["camera_id"],
            "type": row["type"],
            "severity": row["severity"],
            "confidence": round(float(row["confidence"]), 3),
            "title": row["title"],
            "detail": row["detail"],
            "metric": metric if isinstance(metric, dict) else {},
            "snapshot_url": "/api/v1/events/%s/snapshot" % eid,
            "clip_url": "/api/v1/events/%s/clip" % eid,
            "acked": bool(row["acked"]),
            "evidence": row["evidence"],
        }

    def list_events(
        self,
        since: Optional[int] = None,
        type_: Optional[str] = None,
        camera_id: Optional[str] = None,
        limit: int = 200,
        unacked_only: bool = False,
    ) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM events WHERE 1=1"
        params: List[Any] = []
        if since is not None:
            sql += " AND ts >= ?"
            params.append(int(since))
        if type_:
            sql += " AND type = ?"
            params.append(type_)
        if camera_id:
            sql += " AND camera_id = ?"
            params.append(camera_id)
        if unacked_only:
            sql += " AND acked = 0"
        sql += " ORDER BY ts DESC, rowid DESC LIMIT ?"
        params.append(max(1, int(limit)))
        rows = self._exec(sql, params).fetchall()
        return [self._row_to_event(r) for r in rows]

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        row = self._exec("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
        return self._row_to_event(row) if row else None

    def ack_event(self, event_id: str) -> bool:
        with self._lock:
            cur = self._conn.execute("UPDATE events SET acked=1 WHERE id=?", (event_id,))
            self._conn.commit()
            return cur.rowcount > 0

    def link_event_snapshot(self, event_id: str, path: str) -> None:
        with self._lock:
            self._conn.execute("UPDATE events SET snapshot_path=? WHERE id=?", (path, event_id))
            self._conn.commit()

    def link_event_clip(self, event_id: str, path: str) -> None:
        with self._lock:
            self._conn.execute("UPDATE events SET clip_path=? WHERE id=?", (path, event_id))
            self._conn.commit()

    def event_snapshot_path(self, event_id: str) -> Optional[str]:
        row = self._exec("SELECT snapshot_path, camera_id FROM events WHERE id=?", (event_id,)).fetchone()
        if not row:
            return None
        path = row["snapshot_path"]
        if path and os.path.exists(path):
            return path
        # 抓图丢了 / 离线事件没抓到图：退化用该相机最近一张，避免前端出现裂图
        latest = self.latest_snapshot(row["camera_id"])
        return latest["path"] if latest else None

    def event_clip_path(self, event_id: str) -> Optional[str]:
        row = self._exec("SELECT clip_path FROM events WHERE id=?", (event_id,)).fetchone()
        if row and row["clip_path"] and os.path.exists(row["clip_path"]):
            return row["clip_path"]
        return None

    # ------------------------------------------------------------------
    # 指标（V-Value 采样）
    # ------------------------------------------------------------------
    def add_metric(self, camera_id: str, ts: int, v_value: float) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO metrics(camera_id, ts, v_value) VALUES(?,?,?)",
                (camera_id, int(ts), float(v_value)),
            )
            self._conn.commit()

    def add_metrics(self, rows: Iterable[Tuple[str, int, float]]) -> None:
        with self._lock:
            self._conn.executemany(
                "INSERT OR REPLACE INTO metrics(camera_id, ts, v_value) VALUES(?,?,?)", list(rows)
            )
            self._conn.commit()

    def series(self, camera_id: str, since: int, until: int) -> List[Tuple[int, float]]:
        rows = self._exec(
            "SELECT ts, v_value FROM metrics WHERE camera_id=? AND ts>=? AND ts<=? ORDER BY ts ASC",
            (camera_id, int(since), int(until)),
        ).fetchall()
        return [(int(r["ts"]), float(r["v_value"])) for r in rows]

    # ------------------------------------------------------------------
    # 日志
    # ------------------------------------------------------------------
    def add_log(self, ts: int, level: str, src: str, msg: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO logs(ts, level, src, msg) VALUES(?,?,?,?)",
                (int(ts), level, src, msg[:2000]),
            )
            self._conn.commit()

    def list_logs(self, limit: int = 200, since: Optional[int] = None, level: Optional[str] = None) -> List[Dict[str, Any]]:
        sql = "SELECT ts, level, src, msg FROM logs WHERE 1=1"
        params: List[Any] = []
        if since is not None:
            sql += " AND ts >= ?"
            params.append(int(since))
        if level:
            sql += " AND level = ?"
            params.append(level)
        sql += " ORDER BY ts DESC, rowid DESC LIMIT ?"
        params.append(max(1, int(limit)))
        rows = self._exec(sql, params).fetchall()
        return [
            {"ts": int(r["ts"]), "level": r["level"], "src": r["src"], "msg": r["msg"]}
            for r in rows
        ]

    # ------------------------------------------------------------------
    # 抓图
    # ------------------------------------------------------------------
    def _snapshot_abspath(self, ts: int, camera_id: str) -> str:
        day = time.strftime("%Y-%m-%d", time.localtime(ts))
        folder = os.path.join(self.snapshot_dir, day)
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, "%d_%s.jpg" % (int(ts), camera_id))

    def save_snapshot(
        self,
        ts: int,
        camera_id: str,
        data: bytes,
        trigger: str = "interval",
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """写抓图文件 + 记一行 DB。数据不是 JPEG 时拒绝写入（避免存坏图）。"""
        if not data or len(data) < 4 or data[:2] != b"\xff\xd8":
            self._warn("抓图数据不是合法 JPEG，已丢弃（camera=%s ts=%s）" % (camera_id, ts))
            return None
        if trigger not in SNAPSHOT_TRIGGERS:
            trigger = "manual"
        ts = int(ts)
        # 契约 §5 的 url 是 /api/v1/snapshots/{ts}.jpg（不带相机名），所以同一秒
        # 不能被两台相机占用：占了就顺延 1 s，保证 URL 全局可寻址。
        for _ in range(6):
            row = self._exec(
                "SELECT camera_id FROM snapshots WHERE ts=?", (ts,)
            ).fetchone()
            if row is None or row["camera_id"] == camera_id:
                break
            ts += 1
        path = self._snapshot_abspath(ts, camera_id)
        tmp = path + ".tmp"
        try:
            with open(tmp, "wb") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
        except Exception as exc:
            self._warn("写抓图失败 %s：%s" % (path, exc))
            return None
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO snapshots(ts, camera_id, path, trigger, width, height, bytes)"
                " VALUES(?,?,?,?,?,?,?)",
                (ts, camera_id, path, trigger, width, height, len(data)),
            )
            self._conn.commit()
        return {
            "ts": ts,
            "camera_id": camera_id,
            "url": "/api/v1/snapshots/%d.jpg" % ts,
            "trigger": trigger,
            "path": path,
        }

    def latest_snapshot(self, camera_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if camera_id:
            row = self._exec(
                "SELECT * FROM snapshots WHERE camera_id=? ORDER BY ts DESC LIMIT 1", (camera_id,)
            ).fetchone()
        else:
            row = self._exec("SELECT * FROM snapshots ORDER BY ts DESC LIMIT 1").fetchone()
        if not row:
            return None
        return {
            "ts": int(row["ts"]),
            "camera_id": row["camera_id"],
            "path": row["path"],
            "trigger": row["trigger"],
            "url": "/api/v1/snapshots/%d.jpg" % int(row["ts"]),
        }

    def list_snapshots(
        self,
        date: Optional[str] = None,
        camera_id: Optional[str] = None,
        limit: int = 500,
        trigger: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        sql = "SELECT ts, camera_id, trigger, path FROM snapshots WHERE 1=1"
        params: List[Any] = []
        if date:
            try:
                day_start = int(time.mktime(time.strptime(date, "%Y-%m-%d")))
            except Exception:
                return []
            sql += " AND ts >= ? AND ts < ?"
            params.extend([day_start, day_start + 86400])
        if camera_id:
            sql += " AND camera_id = ?"
            params.append(camera_id)
        if trigger:
            sql += " AND trigger = ?"
            params.append(trigger)
        sql += " ORDER BY ts DESC LIMIT ?"
        params.append(max(1, int(limit)))
        rows = self._exec(sql, params).fetchall()
        out = []
        for r in rows:
            out.append(
                {
                    "ts": int(r["ts"]),
                    "camera_id": r["camera_id"],
                    "url": "/api/v1/snapshots/%d.jpg" % int(r["ts"]),
                    "trigger": r["trigger"],
                }
            )
        return out

    def snapshot_path_by_ts(self, ts: int, camera_id: Optional[str] = None) -> Optional[str]:
        if camera_id:
            row = self._exec(
                "SELECT path FROM snapshots WHERE ts=? AND camera_id=?", (int(ts), camera_id)
            ).fetchone()
        else:
            row = self._exec(
                "SELECT path FROM snapshots WHERE ts=? ORDER BY trigger='event' DESC LIMIT 1", (int(ts),)
            ).fetchone()
        if row and row["path"] and os.path.exists(row["path"]):
            return row["path"]
        return None

    # ------------------------------------------------------------------
    # 清理与磁盘
    # ------------------------------------------------------------------
    def disk_free_gb(self, path: Optional[str] = None) -> float:
        target = path or self.data_dir
        try:
            usage = shutil.disk_usage(target)
            return round(usage.free / float(1024 ** 3), 2)
        except Exception:
            return 0.0

    def _delete_snapshot_rows(self, rows: Sequence[sqlite3.Row]) -> int:
        deleted = 0
        for row in rows:
            try:
                if row["path"] and os.path.exists(row["path"]):
                    os.remove(row["path"])
            except Exception as exc:
                self._warn("删除抓图失败 %s：%s" % (row["path"], exc))
            with self._lock:
                self._conn.execute(
                    "DELETE FROM snapshots WHERE ts=? AND camera_id=?", (row["ts"], row["camera_id"])
                )
            deleted += 1
        return deleted

    def cleanup(
        self,
        snapshot_keep_days: int = 14,
        events_keep_days: int = 90,
        logs_keep_days: int = 14,
        metrics_keep_days: int = 30,
        min_free_gb: float = 3.0,
        recordings_keep_days: Optional[int] = None,
        recording_dirs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """按保留天数清理 + 磁盘吃紧时清最旧抓图。返回统计。"""
        now = _now()
        summary = {
            "deleted_events": 0,
            "deleted_logs": 0,
            "deleted_metrics": 0,
            "deleted_snapshots": 0,
            "deleted_recordings": 0,
            "free_gb": self.disk_free_gb(),
            "forced": False,
        }
        with self._lock:
            cur = self._conn.execute("DELETE FROM events WHERE ts < ?", (now - events_keep_days * 86400,))
            summary["deleted_events"] = cur.rowcount if cur.rowcount > 0 else 0
            cur = self._conn.execute("DELETE FROM logs WHERE ts < ?", (now - logs_keep_days * 86400,))
            summary["deleted_logs"] = cur.rowcount if cur.rowcount > 0 else 0
            cur = self._conn.execute("DELETE FROM metrics WHERE ts < ?", (now - metrics_keep_days * 86400,))
            summary["deleted_metrics"] = cur.rowcount if cur.rowcount > 0 else 0
            self._conn.commit()
        old = self._exec(
            "SELECT * FROM snapshots WHERE ts < ? ORDER BY ts ASC LIMIT 2000",
            (now - snapshot_keep_days * 86400,),
        ).fetchall()
        summary["deleted_snapshots"] += self._delete_snapshot_rows(old)

        # 录像保留（只删我们自己的录像目录，不动用户其它文件）
        if recordings_keep_days and recording_dirs:
            cutoff = now - recordings_keep_days * 86400
            for folder in recording_dirs:
                if not os.path.isdir(folder):
                    continue
                for name in sorted(os.listdir(folder)):
                    fpath = os.path.join(folder, name)
                    try:
                        if os.path.isfile(fpath) and os.path.getmtime(fpath) < cutoff:
                            os.remove(fpath)
                            summary["deleted_recordings"] += 1
                    except Exception as exc:
                        self._warn("删除录像失败 %s：%s" % (fpath, exc))

        # 磁盘不足：强制清最旧抓图，直到达标或没有可清的
        free = self.disk_free_gb()
        guard = 0
        while free < float(min_free_gb) and guard < 50:
            guard += 1
            batch = self._exec("SELECT * FROM snapshots ORDER BY ts ASC LIMIT 200").fetchall()
            if not batch:
                break
            removed = self._delete_snapshot_rows(batch)
            summary["deleted_snapshots"] += removed
            summary["forced"] = True
            free = self.disk_free_gb()
            if removed == 0:
                break
        summary["free_gb"] = free
        if summary["forced"]:
            self._warn(
                "磁盘剩余 %.2f GB 低于阈值 %.2f GB，已强制清理最旧抓图 %d 张"
                % (free, float(min_free_gb), summary["deleted_snapshots"])
            )
        with self._lock:
            self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        return summary

    def stats(self) -> Dict[str, Any]:
        def count(table: str) -> int:
            row = self._exec("SELECT COUNT(*) AS c FROM %s" % table).fetchone()
            return int(row["c"]) if row else 0

        size = 0
        for root, _dirs, files in os.walk(self.data_dir):
            for name in files:
                try:
                    size += os.path.getsize(os.path.join(root, name))
                except OSError:
                    pass
        return {
            "events": count("events"),
            "snapshots": count("snapshots"),
            "logs": count("logs"),
            "metrics": count("metrics"),
            "data_bytes": size,
        }

    def close(self) -> None:
        with self._lock:
            try:
                self._conn.commit()
                self._conn.close()
            except Exception:
                pass
