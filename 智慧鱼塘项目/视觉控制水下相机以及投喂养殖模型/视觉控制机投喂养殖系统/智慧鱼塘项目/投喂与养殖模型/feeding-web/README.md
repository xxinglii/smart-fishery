# 鱼塘投喂养殖模型（feeding-web）

带 Web 界面的鱼塘日投喂方案计算器。外部系统通过 REST API 上报鱼群数量，
环境条件通过 API 或网页录入，系统按投喂率表与环境修正系数给出每日投喂方案。

## 启动

```bash
cd feeding-web
python3 -m uvicorn app.main:app --port 8931
# 打开 http://127.0.0.1:8931/
```

依赖仅 fastapi + uvicorn（`pip install -r requirements.txt`）。
数据库为 SQLite（标准库 sqlite3），首次启动自动创建于 `data/feeding.db`。

## API 示例（curl）

```bash
# 1. 外部系统上报鱼群：5000 尾、抽样均重 400 g
curl -X POST http://127.0.0.1:8931/api/fish \
  -H 'Content-Type: application/json' \
  -d '{"count": 5000, "avg_weight_g": 400, "note": "春季抽样"}'

# 2. 录入环境：水温 25℃、溶氧 6 mg/L、晴
curl -X POST http://127.0.0.1:8931/api/environment \
  -H 'Content-Type: application/json' \
  -d '{"water_temp_c": 25, "dissolved_oxygen_mgl": 6, "weather": "晴"}'

# 3. 当日投喂方案
curl 'http://127.0.0.1:8931/api/plan'
# 指定日期：curl 'http://127.0.0.1:8931/api/plan?date=2026-10-09'

# 4. 鱼群状态 + 最新环境 + 最近 20 条事件
curl http://127.0.0.1:8931/api/state
```

手工核对基准：B = 5000 × 400 / 1000 = 2000 kg；r(25℃, 400g) = 3.6 %/天；
W_day = 2000 × 3.6 / 100 = 72 kg/天；3 餐（07:30 / 11:30 / 16:00）各 24 kg；
区间 [50.4, 93.6] kg/天。

## 模型依据

- 投喂率表 r(T, W)：T/SCFA 0011—2023 表 4（黄河鲤，%体重/天），
  温度 × 规格（按区间中点 75/200/400/600/850/1200 g）双线性插值，越界钳制不外推。
- 日投喂量：`W_day = B × r × f_env / 100`，B = N × w̄ / 1000。
- 环境修正 f_env = f_DO × f_水温 × f_天气（乘性）：
  - 溶氧 <5 → ×0.5；<3 → ×0（停喂，告警并建议增氧）
  - 水温 >32 且 <33℃ → ×0.5；≥33℃ → ×0；<10℃ → ×0.3（少量维持）
  - 天气（自定义默认值，官方无定量系数，可在 `app/model.py` 的 `WEATHER_FACTORS` 配置）：
    晴 1.0 / 阴 0.8 / 雷雨·暴雨 0（停喂）/ 闷热低压 0.7
- 安全钳制：W_day ≤ 4.7% × B（当季投喂率上限）。
- 精度 ±30%：输出区间 [0.7×W, 1.3×W]，宁可按下限执行（过量代价远大于不足）。
- 餐次（T/SCFA 表 3 + DB4102/T 002）：≥15℃ 默认 3 餐 07:30/11:30/16:00
  （可选第 4 餐 19:00 前）；10–15℃ 默认 11:30 一餐；<10℃ 每 2–3 天少量，人工判断。
- 生物量估算：距上次抽样 >1 天时按 w̄×(1+SGR/100)^天数 估算，响应标 estimated=true；
  SGR 默认 1.5 %/天（估计值，15–20 天须抽样校核）。
  绝不根据累计投料量反推生物量（正反馈发散风险）。

## 已知简化 / 缺口

- 天气系数、SGR 默认值均为自定义估计值，官方标准无定量系数，须现场校核。
- 湿度仅记录展示，不参与投喂量计算（调研明确缺口）；湿度影响投饵机下料速率漂移，
  换料/换季需复标定。
- 投喂率表品种为黄河鲤，其他品种需换表。
- 事件日志为"四本账"简化版（鱼群上报 / 死亡 / 环境），未含完整投喂执行记录表。
- 无鉴权，假定部署在受信任的现场内网/单机。

## 文件结构

```
feeding-web/
  app/__init__.py
  app/main.py        # FastAPI 路由 + 静态页
  app/model.py       # 投喂率表、插值、f_env、钳制、餐次（纯函数）
  app/db.py          # sqlite3 初始化与读写（data/feeding.db）
  app/static/index.html
  requirements.txt
  README.md
```
