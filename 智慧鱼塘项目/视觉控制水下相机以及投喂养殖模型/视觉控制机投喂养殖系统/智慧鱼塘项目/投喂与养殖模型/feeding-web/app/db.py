# -*- coding: utf-8 -*-
"""SQLite 持久化（标准库 sqlite3，无新依赖）。

数据文件：feeding-web/data/feeding.db
表：
  fish_state    鱼群状态（单行，id=1）
  env_records   环境记录（保留历史）
  events        事件日志（"四本账"简化版：鱼群上报/环境/死亡等事件）
"""

import json
import os
import sqlite3
from datetime import date, datetime
from typing import Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "feeding.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS fish_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    count INTEGER NOT NULL DEFAULT 0,
    avg_weight_g REAL NOT NULL DEFAULT 0,
    initial_count INTEGER NOT NULL DEFAULT 0,
    cumulative_mortality INTEGER NOT NULL DEFAULT 0,
    last_sampled_at TEXT NOT NULL DEFAULT '',
    sgr_pct REAL NOT NULL DEFAULT 1.5,
    updated_at TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS env_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    water_temp_c REAL NOT NULL,
    air_temp_c REAL,
    humidity_pct REAL,
    dissolved_oxygen_mgl REAL,
    weather TEXT,
    recorded_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _now():
    # type: () -> str
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_conn():
    # type: () -> sqlite3.Connection
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    # type: () -> None
    conn = get_conn()
    try:
        conn.executescript(SCHEMA)
        cur = conn.execute("SELECT COUNT(*) AS c FROM fish_state")
        if cur.fetchone()["c"] == 0:
            conn.execute(
                "INSERT INTO fish_state (id, count, avg_weight_g, initial_count, "
                "cumulative_mortality, last_sampled_at, sgr_pct, updated_at) "
                "VALUES (1, 0, 0, 0, 0, ?, 1.5, ?)",
                (date.today().isoformat(), _now()),
            )
        conn.commit()
    finally:
        conn.close()


def log_event(event_type, payload):
    # type: (str, Dict) -> None
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO events (event_type, payload, created_at) VALUES (?, ?, ?)",
            (event_type, json.dumps(payload, ensure_ascii=False), _now()),
        )
        conn.commit()
    finally:
        conn.close()


def update_fish(count, avg_weight_g=None, mortality=None, sampled_at=None, note=None):
    # type: (int, Optional[float], Optional[int], Optional[str], Optional[str]) -> Dict
    """外部系统上报鱼群：更新状态 + 写事件表。返回更新后的状态。"""
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM fish_state WHERE id = 1").fetchone()
        initial_count = row["initial_count"] or count
        cumulative_mortality = row["cumulative_mortality"] + (mortality or 0)
        new_weight = avg_weight_g if avg_weight_g is not None else row["avg_weight_g"]
        # 上报均重即视为一次抽样
        if avg_weight_g is not None:
            last_sampled_at = sampled_at or date.today().isoformat()
        else:
            last_sampled_at = row["last_sampled_at"]
        conn.execute(
            "UPDATE fish_state SET count=?, avg_weight_g=?, initial_count=?, "
            "cumulative_mortality=?, last_sampled_at=?, updated_at=? WHERE id=1",
            (count, new_weight, initial_count, cumulative_mortality, last_sampled_at, _now()),
        )
        conn.commit()
    finally:
        conn.close()
    log_event("鱼群上报", {
        "count": count, "avg_weight_g": avg_weight_g, "mortality": mortality,
        "sampled_at": sampled_at, "note": note,
    })
    if mortality:
        log_event("死亡记录", {"mortality": mortality, "累计死亡": cumulative_mortality})
    return get_state()


def insert_env(water_temp_c, air_temp_c=None, humidity_pct=None,
               dissolved_oxygen_mgl=None, weather=None, recorded_at=None):
    # type: (float, Optional[float], Optional[float], Optional[float], Optional[str], Optional[str]) -> Dict
    rec_at = recorded_at or _now()
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO env_records (water_temp_c, air_temp_c, humidity_pct, "
            "dissolved_oxygen_mgl, weather, recorded_at, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (water_temp_c, air_temp_c, humidity_pct, dissolved_oxygen_mgl, weather, rec_at, _now()),
        )
        conn.commit()
        env_id = cur.lastrowid
    finally:
        conn.close()
    payload = {
        "water_temp_c": water_temp_c, "air_temp_c": air_temp_c,
        "humidity_pct": humidity_pct, "dissolved_oxygen_mgl": dissolved_oxygen_mgl,
        "weather": weather, "recorded_at": rec_at,
    }
    log_event("环境录入", payload)
    payload["id"] = env_id
    return payload


def get_state():
    # type: () -> Dict
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM fish_state WHERE id = 1").fetchone()
        return dict(row)
    finally:
        conn.close()


def latest_env(before_date=None):
    # type: (Optional[str]) -> Optional[Dict]
    """取最新一条环境记录；给定 before_date (YYYY-MM-DD) 时取该日 23:59:59 之前最新的。"""
    conn = get_conn()
    try:
        if before_date:
            row = conn.execute(
                "SELECT * FROM env_records WHERE recorded_at <= ? ORDER BY recorded_at DESC, id DESC LIMIT 1",
                (before_date + " 23:59:59",),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM env_records ORDER BY recorded_at DESC, id DESC LIMIT 1"
            ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def recent_events(limit=20):
    # type: (int) -> List[Dict]
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["payload"] = json.loads(d["payload"])
            out.append(d)
        return out
    finally:
        conn.close()
