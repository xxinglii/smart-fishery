# -*- coding: utf-8 -*-
"""FastAPI 路由 + 静态页入口。"""

import os
from datetime import date, datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import db, model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(title="鱼塘投喂养殖模型", version="1.0")


@app.on_event("startup")
def _startup():
    db.init_db()


class FishReport(BaseModel):
    count: int
    avg_weight_g: Optional[float] = None
    mortality: Optional[int] = None
    sampled_at: Optional[str] = None
    note: Optional[str] = None


class EnvReport(BaseModel):
    water_temp_c: float
    air_temp_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    dissolved_oxygen_mgl: Optional[float] = None
    weather: Optional[str] = None
    recorded_at: Optional[str] = None


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.post("/api/fish")
def post_fish(report: FishReport):
    if report.count < 0:
        raise HTTPException(status_code=400, detail="count 不能为负数")
    if report.mortality is not None and report.mortality < 0:
        raise HTTPException(status_code=400, detail="mortality 不能为负数")
    if report.avg_weight_g is not None and report.avg_weight_g <= 0:
        raise HTTPException(status_code=400, detail="avg_weight_g 必须为正数")
    if report.sampled_at is not None:
        try:
            datetime.strptime(report.sampled_at, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="sampled_at 格式须为 YYYY-MM-DD")
    state = db.update_fish(
        count=report.count,
        avg_weight_g=report.avg_weight_g,
        mortality=report.mortality,
        sampled_at=report.sampled_at,
        note=report.note,
    )
    return {"结果": "已更新鱼群状态并记录事件", "鱼群状态": state}


@app.post("/api/environment")
def post_environment(report: EnvReport):
    if report.weather is not None and report.weather not in model.WEATHER_FACTORS:
        raise HTTPException(
            status_code=400,
            detail="weather 可选值：" + "、".join(model.WEATHER_FACTORS.keys()),
        )
    if report.recorded_at is not None:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                datetime.strptime(report.recorded_at, fmt)
                break
            except ValueError:
                continue
        else:
            raise HTTPException(status_code=400, detail="recorded_at 格式须为 ISO 日期时间")
    saved = db.insert_env(
        water_temp_c=report.water_temp_c,
        air_temp_c=report.air_temp_c,
        humidity_pct=report.humidity_pct,
        dissolved_oxygen_mgl=report.dissolved_oxygen_mgl,
        weather=report.weather,
        recorded_at=report.recorded_at,
    )
    return {"结果": "已保存环境记录", "环境记录": saved}


@app.get("/api/plan")
def get_plan(date_str: Optional[str] = Query(default=None, alias="date")):
    plan_date = date_str or date.today().isoformat()
    try:
        datetime.strptime(plan_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="date 格式须为 YYYY-MM-DD")

    state = db.get_state()
    env = db.latest_env(before_date=plan_date)
    if state["count"] <= 0 or state["avg_weight_g"] <= 0:
        raise HTTPException(
            status_code=409,
            detail="鱼群状态未初始化（尾数或均重为 0），请先 POST /api/fish 上报。",
        )
    if env is None:
        raise HTTPException(
            status_code=409,
            detail="尚无环境记录，请先 POST /api/environment 录入水温等环境条件。",
        )

    plan = model.compute_plan(
        count=state["count"],
        sampled_avg_weight_g=state["avg_weight_g"],
        last_sampled_at=state["last_sampled_at"],
        sgr_pct=state["sgr_pct"],
        env=env,
        plan_date=plan_date,
    )
    plan["环境记录时间"] = env.get("recorded_at")
    return plan


@app.get("/api/state")
def get_state():
    state = db.get_state()
    env = db.latest_env()
    days_since_sampling = None
    if state.get("last_sampled_at"):
        try:
            sampled = datetime.strptime(state["last_sampled_at"], "%Y-%m-%d").date()
            days_since_sampling = (date.today() - sampled).days
        except ValueError:
            days_since_sampling = None
    return {
        "鱼群状态": state,
        "距上次抽样天数": days_since_sampling,
        "estimated提醒": ("距上次抽样超过 1 天，计算方案时将按 SGR %.1f%%/天估算均重（estimated=true）；"
                        "SGR 为估计值，15–20 天须抽样校核。" % state["sgr_pct"])
        if days_since_sampling is not None and days_since_sampling > 1 else None,
        "最新环境": env,
        "事件日志": db.recent_events(20),
    }
