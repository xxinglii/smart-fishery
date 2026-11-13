# -*- coding: utf-8 -*-
"""投喂模型核心纯函数。

依据：项目调研报告引用的 T/SCFA 0011—2023（黄河鲤）表 4 投喂率表、
表 3 餐次安排与 DB4102/T 002 投喂时间，以及调研给出的环境修正系数与缺口说明。
本模块不读写数据库，全部为纯函数，便于单元测试。
"""

from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 投喂率表（T/SCFA 0011—2023 表 4，黄河鲤，单位 %体重/天）
# 行 = 水温，列 = 规格区间中点（75/200/400/600/850/1200 g）
# ---------------------------------------------------------------------------
RATE_TEMPS_C = [15.0, 18.0, 20.0, 23.0, 25.0, 27.0, 30.0, 32.0]
SIZE_MIDPOINTS_G = [75.0, 200.0, 400.0, 600.0, 850.0, 1200.0]
SIZE_LABELS = ["50–100g", "100–300g", "300–500g", "500–700g", "700–1000g", ">1000g"]
RATE_TABLE = [
    [2.8, 2.5, 1.8, 1.5, 1.2, 1.0],  # 15℃
    [3.0, 2.8, 2.2, 2.1, 1.8, 1.5],  # 18℃
    [4.0, 3.2, 2.8, 2.2, 2.0, 1.8],  # 20℃
    [4.1, 3.6, 3.3, 3.0, 2.6, 2.2],  # 23℃
    [4.3, 3.8, 3.6, 3.3, 2.7, 2.3],  # 25℃
    [4.5, 4.2, 3.8, 3.5, 2.8, 2.4],  # 27℃
    [4.7, 4.4, 3.9, 3.7, 3.2, 2.5],  # 30℃
    [4.6, 4.2, 3.7, 3.5, 3.0, 2.4],  # 32℃
]

# 安全钳制：日投喂率不超过当季上限 4.7% 体重/天
MAX_RATE_PCT = 4.7

# 天气修正系数（官方标准无定量系数，以下为可配置的自定义默认值，界面须注明）
WEATHER_FACTORS = {
    "晴": 1.0,
    "阴": 0.8,
    "雷雨": 0.0,
    "暴雨": 0.0,
    "闷热低压": 0.7,
}

# 默认日增长率 SGR（%/天）：估计值，15–20 天须抽样校核
DEFAULT_SGR_PCT = 1.5

# 精度预期 ±30%，输出区间 [0.7, 1.3]；过量代价远大于不足，宁可按下限执行
RANGE_LOW = 0.7
RANGE_HIGH = 1.3


def _bracket(axis, x):
    # type: (List[float], float) -> Tuple[int, int, float]
    """返回插值用的下标区间 (i0, i1, t)；越界时钳制到边界（不外推）。"""
    if x <= axis[0]:
        return 0, 0, 0.0
    if x >= axis[-1]:
        n = len(axis) - 1
        return n, n, 0.0
    for i in range(len(axis) - 1):
        if axis[i] <= x <= axis[i + 1]:
            t = (x - axis[i]) / (axis[i + 1] - axis[i])
            return i, i + 1, t
    n = len(axis) - 1
    return n, n, 0.0


def feeding_rate_pct(temp_c, avg_weight_g):
    # type: (float, float) -> float
    """r(T, W)：投喂率表双线性插值，单位 %体重/天。越界钳制到边界值。"""
    ti0, ti1, tt = _bracket(RATE_TEMPS_C, float(temp_c))
    wi0, wi1, wt = _bracket(SIZE_MIDPOINTS_G, float(avg_weight_g))
    r00 = RATE_TABLE[ti0][wi0]
    r01 = RATE_TABLE[ti0][wi1]
    r10 = RATE_TABLE[ti1][wi0]
    r11 = RATE_TABLE[ti1][wi1]
    r0 = r00 + (r01 - r00) * wt
    r1 = r10 + (r11 - r10) * wt
    return r0 + (r1 - r0) * tt


def env_factors(water_temp_c, dissolved_oxygen_mgl, weather):
    # type: (Optional[float], Optional[float], Optional[str]) -> Dict
    """环境修正系数 f_env = f_DO × f_T高 × f_天气（乘性），附告警列表。"""
    alarms = []  # type: List[Dict[str, str]]
    f_do = 1.0
    f_temp = 1.0
    f_weather = 1.0

    # 溶氧
    if dissolved_oxygen_mgl is None:
        alarms.append({"级别": "黄", "内容": "未提供溶氧数据，f_DO 按 1.0 处理；建议补录溶氧。"})
    elif dissolved_oxygen_mgl < 3.0:
        f_do = 0.0
        alarms.append({"级别": "红", "内容": "溶氧 %.1f mg/L < 3 mg/L：停喂！立即增氧。" % dissolved_oxygen_mgl})
    elif dissolved_oxygen_mgl < 5.0:
        f_do = 0.5
        alarms.append({"级别": "黄", "内容": "溶氧 %.1f mg/L < 5 mg/L：投喂量减半，注意增氧。" % dissolved_oxygen_mgl})

    # 水温（高温停喂 / 低温维持）
    if water_temp_c is None:
        alarms.append({"级别": "红", "内容": "缺少水温数据，无法可靠计算投喂方案。"})
    else:
        if water_temp_c >= 33.0:
            f_temp = 0.0
            alarms.append({"级别": "红", "内容": "水温 %.1f℃ ≥ 33℃：停喂！" % water_temp_c})
        elif water_temp_c > 32.0:
            f_temp = 0.5
            alarms.append({"级别": "黄", "内容": "水温 %.1f℃ 高于 32℃：投喂量减半。" % water_temp_c})
        elif water_temp_c < 10.0:
            f_temp = 0.3
            alarms.append({"级别": "黄", "内容": "水温 %.1f℃ < 10℃：按 0.3 系数少量维持投喂。" % water_temp_c})

    # 天气（自定义默认值，官方标准无定量系数）
    if weather is None or weather == "":
        alarms.append({"级别": "黄", "内容": "未提供天气，f_天气 按 1.0（晴）处理。"})
    elif weather in WEATHER_FACTORS:
        f_weather = WEATHER_FACTORS[weather]
        if f_weather == 0.0:
            alarms.append({"级别": "红", "内容": "天气「%s」：停喂（自定义系数 0）。" % weather})
        elif f_weather < 1.0:
            alarms.append({"级别": "黄", "内容": "天气「%s」：投喂量 ×%.1f（自定义系数）。" % (weather, f_weather)})
    else:
        alarms.append({"级别": "黄", "内容": "未知天气「%s」，f_天气 按 1.0 处理；可选值：%s。"
                       % (weather, "、".join(WEATHER_FACTORS.keys()))})

    f_env = f_do * f_temp * f_weather
    return {
        "f_DO": f_do,
        "f_水温": f_temp,
        "f_天气": f_weather,
        "f_env": f_env,
        "告警": alarms,
    }


def meals_for_temp(water_temp_c):
    # type: (Optional[float]) -> Dict
    """餐次安排（T/SCFA 表 3 + DB4102/T 002）。"""
    if water_temp_c is None:
        return {"餐次": [], "说明": "缺少水温，无法安排餐次。"}
    t = water_temp_c
    if t >= 15.0:
        # ≥20℃ 与 15–20℃ 同为默认 3 餐（可选 4 餐加 19:00 前，默认 3 餐）
        return {"餐次": ["07:30", "11:30", "16:00"],
                "说明": "默认 3 餐；如需 4 餐可在 19:00 前加一餐。"}
    if t >= 10.0:
        return {"餐次": ["11:30"], "说明": "10–15℃：1–2 餐，默认 11:30 一餐。"}
    return {"餐次": [], "说明": "<10℃：每 2–3 天少量投喂，需人工判断，不自动排餐。"}


def estimate_weight_g(sampled_weight_g, days_since_sampling, sgr_pct):
    # type: (float, int, float) -> float
    """距上次抽样超过 1 天时，按 SGR 复利估算当前均重。"""
    return sampled_weight_g * ((1.0 + sgr_pct / 100.0) ** days_since_sampling)


def compute_plan(count, sampled_avg_weight_g, last_sampled_at, sgr_pct, env, plan_date):
    # type: (int, float, str, float, Dict, str) -> Dict
    """计算某日投喂方案。

    参数：
        count               当前尾数 N
        sampled_avg_weight_g 抽样均重 w̄ (g)
        last_sampled_at     上次抽样日期 "YYYY-MM-DD"
        sgr_pct             日增长率 SGR (%/天)
        env                 环境快照 dict（water_temp_c / dissolved_oxygen_mgl / weather / ...）
        plan_date           方案日期 "YYYY-MM-DD"
    返回：中文键名的方案 dict。
    """
    alarms = []  # type: List[Dict[str, str]]
    pdate = datetime.strptime(plan_date, "%Y-%m-%d").date()
    sampled_date = datetime.strptime(last_sampled_at, "%Y-%m-%d").date()
    days = (pdate - sampled_date).days
    if days < 0:
        days = 0
        alarms.append({"级别": "黄", "内容": "抽样日期晚于方案日期，均重按抽样值直接使用。"})

    estimated = days > 1
    if estimated:
        avg_weight_g = estimate_weight_g(sampled_avg_weight_g, days, sgr_pct)
        alarms.append({"级别": "黄",
                       "内容": "距上次抽样 %d 天，均重按 SGR %.1f%%/天估算为 %.1f g（estimated=true）；"
                               "SGR 为估计值，15–20 天须抽样校核。" % (days, sgr_pct, avg_weight_g)})
    else:
        avg_weight_g = float(sampled_avg_weight_g)

    water_temp = env.get("water_temp_c")
    do = env.get("dissolved_oxygen_mgl")
    weather = env.get("weather")

    if count <= 0:
        alarms.append({"级别": "红", "内容": "当前尾数为 0，请先通过 POST /api/fish 上报鱼群数量。"})
    if water_temp is None:
        alarms.append({"级别": "红", "内容": "缺少水温数据，请先通过 POST /api/environment 录入环境条件。"})
        return {
            "日期": plan_date,
            "可计算": False,
            "告警": alarms,
        }

    biomass_kg = count * avg_weight_g / 1000.0
    rate = feeding_rate_pct(water_temp, avg_weight_g)
    envf = env_factors(water_temp, do, weather)
    alarms.extend(envf["告警"])

    # 湿度：接受输入但无决策层系数（调研明确缺口）
    if env.get("humidity_pct") is not None:
        alarms.append({"级别": "黄",
                       "内容": "湿度已记录（%.0f%%），但不参与投喂量计算；湿度影响投饵机下料速率漂移，"
                               "换料/换季需复标定。" % env["humidity_pct"]})

    w_day = biomass_kg * rate * envf["f_env"] / 100.0

    # 安全钳制：W_day ≤ 4.7% × B
    clamped = False
    w_cap = biomass_kg * MAX_RATE_PCT / 100.0
    if w_day > w_cap:
        w_day = w_cap
        clamped = True
        alarms.append({"级别": "黄", "内容": "日投喂量超出 4.7%% 体重上限，已钳制到 %.2f kg/天。" % w_cap})

    stop = envf["f_env"] == 0.0 or w_day <= 0.0
    w_day = round(w_day, 2)
    low = round(w_day * RANGE_LOW, 2)
    high = round(w_day * RANGE_HIGH, 2)

    meal_info = meals_for_temp(water_temp)
    meals = []  # type: List[Dict]
    if not stop and meal_info["餐次"]:
        per = round(w_day / len(meal_info["餐次"]), 2)
        for tstr in meal_info["餐次"]:
            meals.append({"时间": tstr, "每餐量kg": per})

    return {
        "日期": plan_date,
        "可计算": True,
        "输入快照": {
            "尾数": count,
            "抽样均重g": round(float(sampled_avg_weight_g), 1),
            "当前均重g": round(avg_weight_g, 1),
            "estimated": estimated,
            "距上次抽样天数": days,
            "上次抽样日期": last_sampled_at,
            "SGR_每天pct": sgr_pct,
            "水温℃": water_temp,
            "溶氧mgL": do,
            "天气": weather,
        },
        "生物量kg": round(biomass_kg, 1),
        "投喂率pct": round(rate, 3),
        "修正系数": {
            "f_DO": envf["f_DO"],
            "f_水温": envf["f_水温"],
            "f_天气": envf["f_天气"],
            "f_env": envf["f_env"],
            "天气系数说明": "天气系数为自定义默认值（官方标准无定量系数），可在 app/model.py 的 WEATHER_FACTORS 配置。",
        },
        "日投喂总量kg每天": w_day,
        "区间kg每天": [low, high],
        "区间说明": "精度预期 ±30%；过量代价远大于不足，宁可按下限执行。",
        "安全钳制": clamped,
        "停喂": stop,
        "餐次": meals,
        "餐次说明": meal_info["说明"],
        "告警": alarms,
        "依据": "T/SCFA 0011—2023 表4投喂率（黄河鲤）+ 表3餐次 + DB4102/T 002 投喂时间",
    }
