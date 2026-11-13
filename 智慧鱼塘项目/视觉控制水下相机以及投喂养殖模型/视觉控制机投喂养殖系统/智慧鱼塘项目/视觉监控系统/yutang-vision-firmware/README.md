# 鱼塘视觉监控系统 · 树莓派端固件（yutang-vision-firmware）

> 现场：塘边有市电、没有宽带，用 **4G CPE** 上网（上行只有几 Mbps）。
> 硬件：**树莓派 5（8GB）** + 海康 `DS-2CD3T86FWDV3-I3S`（800 万定焦，全景位）
> + 海康 `DS-2DC4423IW-D`（400 万 23 倍球机，细节位）+ PoE 交换机。
> 本固件负责：**拉流 → 轻量检测 → 存事件/指标/抓图 → 用 4G 回传缩略图与告警 + SSE 实时推送**，
> 全码流录像留在本地 SD/TF 卡。
>
> 接口按《视觉系统_API契约_v1.md》实现：**每个端点的对象层级字段名、类型、枚举值严格一致**
> （契约里的 13 个事件字段、14 个相机字段、6 个配置键……逐字对齐）。
> 只在数组/响应层做了向后兼容的扩展（`health.services` 多列了几项服务、`PUT /config` 多回一个
> `config`、多了 `/api/v1` 索引页与 `?w=`/`?save=1` 之类可选参数），**对象内部不增不减**，
> 前端按契约写的解析代码不需要改；详见 §6 末尾"扩展点"。
> 前端把 `API_BASE` 从 mock 改成 `http://<树莓派IP>:8080` 即可无缝切换。

---

## 0. 一句话上手

```bash
cd yutang-vision-firmware

# ① 无相机也能跑：假数据流，专供前端联调（health.mode = "mock"）
python3 -m yutang_vision --simulate

# ② 现场模式（先改 config.yaml 里的相机 IP 与口令）
cp config.example.yaml config.yaml && vi config.yaml
python3 -m yutang_vision --config config.yaml

# ③ 一键自检：起服务 → 打全部端点 → 打印通过/失败表
python3 tools/selfcheck.py --simulate

# ④ 契约一致性测试（21 项，不需要 pytest、不需要相机、不联网）
python3 tests/test_contract.py
```

打开 `http://<树莓派IP>:8080/` 就是网页端；没有前端产物时会给一个**内置自检页**（列出各端点）。

---

## 1. 这个固件做什么 / 不做什么

**做**（契约 §8 的五类 + 一类通用）：

| 事件类型 | 判据（v1 可落地版） | 严重级 |
|---|---|---|
| `splash_activity` | 投料区 ROI 内**运动像素占比（V-Value）** ÷ 滚动基线 ≥ `thresholds.splash_ratio`，且持续 ≥ `detector.splash_min_s`（默认 8 s） | info |
| `surface_aggregation` | 暗斑**连通域**面积占比 ≥ `thresholds.aggregation_area_pct`，连续 ≥ `detector.aggregation_frames` 帧 | notice |
| `person` | 立杆侧警戒区检出人形（**MobileNet-SSD** 有模型时优先，否则 **OpenCV HOG**；**不上 YOLO**） | warn |
| `offline` | RTSP 连续失败 ≥ 30 s（契约 §8 写死的 30 s） | warn/critical |
| `tamper` | 画面整体亮度均值突变 或 方差塌陷（遮挡、喷水、移位、糊镜头） | warn |
| `motion` | 非投料窗口内运动占比超阈值（通用兜底，避免漏掉异常活动） | info |

**明确不做**（有项目内证据否决，前端也不提供这些页面）：

- ❌ 数鱼、数饲料颗粒
- ❌ 鱼体估重、生物量反演

**能力边界写在界面上，不是写在说明书里**：以上六类就是全部。

---

## 2. 架构与线程模型

```
        海康全景枪机 ─┐
                      ├─ RTSP ─→ camera.py（每机一条采集线程，ffmpeg 优先 / OpenCV 兜底）
        海康细节球机 ─┘                    │
                                           ▼
                              detector.py（1 条线程，5 fps 灰度分析）
                       ┌───────────────────┼────────────────────┐
                       ▼                   ▼                    ▼
                 bus.py(SSE)         store.py(SQLite WAL)   metrics.py(V-Value 曲线)
                       │                   │                    │
                       ▼                   ▼                    ▼
                GET /api/v1/stream/events  events/snapshots/logs  metrics/splash
                       └──────────── app.py（标准库 http.server，契约全部端点）────────────┘
                                           ▲
   onvif_ptz.py（真 ONVIF / 本地状态机）────┘        netmeter.py（/proc/net/dev + mmcli）
```

| 线程 | 频率 | 干什么 |
|---|---|---|
| HTTP | 每请求 | ThreadingHTTPServer，全部端点 + SSE + 静态托管 |
| 采集 | 每相机 1 条 | 拉流（`scale=640x360,fps=5` 灰度 rawvideo），只保留最新帧 |
| detector | 5 Hz | 帧差/暗斑/人形/tamper，产出事件 |
| watchdog | 1 Hz | 相机卡死检测、`offline` 事件、健康指标采样、模拟剧本注入 |
| capture | `capture.interval_s` | 定时抓图（1920 宽 / q85），错开两台相机的抓图时刻 |
| cleanup | `storage.cleanup_interval_s` | 按天清理 + 磁盘不足时清最旧抓图 |
| netmeter | 5 s | 流量增量、月用量、mmcli 信号 |
| recorder | 常驻子进程 | `ffmpeg -c copy` 分段录像到 SD 卡 |
| ptz-patrol | 1 Hz | 巡航：按 `patrol.dwell_s` 轮转预置位 |

---

## 3. 目录结构

```
yutang-vision-firmware/
├── README.md                  # 本文件
├── requirements.txt           # 依赖（标注了哪些可选、缺了怎么降级）
├── config.example.yaml        # 对应 /api/v1/config 的结构（前 6 个键就是契约 §6）
├── install.sh                 # 一键安装：venv + 依赖 + systemd + 自启
├── systemd/yutang-vision.service
├── yutang_vision/
│   ├── __main__.py            # python -m yutang_vision 启动
│   ├── config.py              # 配置加载/校验/热更新落盘（含纯标准库 YAML 子集解析器）
│   ├── app.py                 # HTTP 服务：契约全部端点 + SSE + 静态托管 + 运行期编排
│   ├── bus.py                 # 事件总线 + SSE 投递
│   ├── store.py               # SQLite(WAL) 存事件/指标/日志 + 抓图落盘与清理
│   ├── camera.py              # RTSP 拉流/退避重连/抓图/录像 + 纯标准库 JPEG 编码器
│   ├── onvif_ptz.py           # ONVIF 真控制 + 本地状态机（mock）
│   ├── detector.py            # 5 类事件判据
│   ├── metrics.py             # V-Value 聚合 + 基线 + 降采样 + 主机指标采样
│   ├── netmeter.py            # 4G 信号/流量（读不到就 None，绝不编）
│   └── simulate.py            # 无相机也能跑：合成视频流 + 剧本 + 历史指标回填
├── tests/test_contract.py     # 断言每个端点 100% 符合契约（pytest / 独立运行两用）
└── tools/selfcheck.py         # 一键自检：起服务 → 打全部端点 → 打印通过/失败表
```

---

## 4. 安装

### 4.1 树莓派（推荐）

```bash
# 系统依赖（ffmpeg 负责拉流与录像，强烈建议装）
sudo apt update && sudo apt install -y python3 python3-venv ffmpeg

# 一键安装（venv + 依赖 + systemd + 开机自启）
cd yutang-vision-firmware
bash install.sh                      # 默认端口 8080，当前用户跑服务
# 可选参数：
#   --offline      不联网：不装任何第三方包，纯标准库跑（功能降级，见 §7）
#   --no-systemd   只准备环境
#   --simulate     systemd 里带 --simulate（先联调前端）
#   --port 8080 --user pi
```

装完：

```bash
systemctl status yutang-vision
journalctl -u yutang-vision -f
curl -s http://127.0.0.1:8080/api/v1/health | python3 -m json.tool
```

### 4.2 开发机（macOS / Linux，无相机）

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt        # 全装不上也没关系，纯标准库能跑
python3 -m yutang_vision --simulate
```

### 4.3 手动装依赖（不想用脚本）

```bash
python3 -m pip install numpy opencv-python-headless PyYAML onvif-zeep
```

> 树莓派上装 `opencv-python-headless`（无 GUI 依赖，省空间）。
> **不要装 ultralytics/YOLO**：树莓派 5 长期值守跑不动，契约 §8 也明确"不必上 YOLO"。

---

## 5. 运行

```bash
python3 -m yutang_vision --simulate                  # 模拟模式：无相机，假数据流，health.mode=mock
python3 -m yutang_vision --config config.yaml        # 现场模式：连真相机，health.mode=live
python3 -m yutang_vision --check                     # 只校验配置并打印契约 §6 的 6 个键
python3 -m yutang_vision --host 0.0.0.0 --port 8080  # 覆盖监听地址/端口
python3 -m yutang_vision --force-ptz-mock            # 即使装了 onvif-zeep 也用本地状态机
python3 -m yutang_vision --help
```

**模拟模式（`--simulate`）产出什么**

- 一段**真的合成灰度视频流**交给**真的检测器**跑：`splash_activity` / `surface_aggregation` /
  `tamper` / `motion` 都是检测器在合成画面上真算出来的，`offline` 走真的看门狗（30 s 规则）。
- 只有 `person` 是**剧本直接注入**的：合成剪影 HOG 检不出来，与其假装"检测到了"，
  不如把它的 **`confidence` 置 0**（不是"刚好过阈值"的编造值），并在 `detail` 里写明"剧本注入"。
- **mock 模式的所有事件都会被打上标记**：标题前缀 `[模拟] `、detail 后缀
  "（mock 数据：由合成视频流/剧本产生，非现场实测）"，且 `health.mode == "mock"`。
  这样演示截图不会被当成实测证据。
- 剧本按 `splash → aggregation → person → tamper → offline → idle` 轮转，
  约 **3 分钟**能让前端看到全部 5 类事件；第一条事件约在启动后 **16 s**。
- 启动时会回填 24 h 的模拟历史 V-Value（否则曲线只有一个点），
  并用 **warn 级别**日志写明"已回填 N 条**模拟**历史指标（…曲线不是现场实测数据）"，
  配合 `health.mode="mock"` 一起判断。不想要这条假曲线就删掉 `simulate.py::backfill_history`
  的调用，或直接用现场模式。

---

## 6. 接口（严格等于契约）

| 端点 | 说明 |
|---|---|
| `GET /api/v1/health` | 版本/运行时长/mode/CPU·内存·温度·磁盘/4G 流量/录像/服务列表 |
| `GET /api/v1/cameras` | 两台相机：`online`、`ptz`（枪机为 `null`）、打码后的 `rtsp` |
| `GET /api/v1/cameras/{id}/snapshot` | `image/jpeg`。`?w=640&q=70` 可要更小的缩略图（4G 省流量）；`?save=1` 存档到抓图墙 |
| `POST /api/v1/cameras/{id}/ptz` | `move` / `goto` / `save` / `home` / `patrol`，返回 `{ok, ptz}` |
| `GET /api/v1/presets?camera_id=` | 预置位列表（默认 1 投料点 / 2 塘中央 / 3 进水口，可 `save` 新增） |
| `GET /api/v1/events?since=&type=&limit=` | 事件倒序；`type` 非法值直接 400（防止前端写错） |
| `POST /api/v1/events/{id}/ack` | `{"ok": true}` |
| `GET /api/v1/events/{id}/snapshot` | `image/jpeg`；离线事件退化用该机最近一张，避免裂图 |
| `GET /api/v1/events/{id}/clip` | `video/mp4`（可选）。没有切片时 404 + `{ok:false,error}` |
| `GET /api/v1/stream/events` | **SSE**，`event: event\ndata: {...}`，心跳 15 s（注释行 `: hb <ts>`） |
| `GET /api/v1/metrics/splash?camera_id=&window=&step=&limit=` | V-Value 曲线（含 baseline/thr 与投料窗口） |
| `GET /api/v1/snapshots?date=&camera_id=&limit=&trigger=` | 抓图墙；`trigger ∈ interval/event/manual` |
| `GET /api/v1/snapshots/{ts}.jpg` | 抓图文件本体 |
| `GET / PUT /api/v1/config` | 契约 §6 的 6 个键；PUT 校验 + 深合并 + 落盘 + 热生效 |
| `GET /api/v1/logs?limit=&level=` | 日志；`level ∈ debug/info/warn/error` |
| `GET /` | 网页端（同源部署）；没有前端产物时给内置自检页 |

约定：全部 `GET` 返回 JSON；`POST/PUT` 请求体 JSON，成功 `{"ok": true, ...}`，失败 `{"ok": false, "error": "..."}`（4xx/5xx）；
**所有时间戳都是 Unix 秒整数**；大响应都支持 `?limit=`（上限 2000）；已开 CORS 方便前端跨域调试。

**扩展点（对象内部不改，只加在外围）**：`health.services` 会多列几个服务项（每个都是 `{name, ok}`，
`ok=false` 表示该能力降级，例如 `ptz` 在用本地状态机、`onvif-zeep` 没装）；
`PUT /api/v1/config` 成功时多回一个 `config` 键（契约允许 `{"ok": true, ...}`）；
`GET /api/v1` 是端点索引页；`?w=`/`?q=`/`?save=1`/`?trigger=`/`?level=` 等都是可选查询参数，
不传就是契约里的默认行为。**这些都不影响按契约写的解析代码。**

`health.services` 的语义是"**这项能力现在真的可用吗**"，不是"配置里写了吗"：
`rtsp-ingest` 要求至少一路出帧、`detector` 要求检测线程有心跳、`store` 要求 SQLite 可查、
`recorder` 要求 ffmpeg **真的写出了分段文件**、`ptz` 要求后端是**真 ONVIF**（mock 状态机算降级）。
所以相机离线时 `storage.recording` 会是 `false`——它反映"**正在录**"，而不是"打算录"
（"打算录"看 `/api/v1/config` 的 `record.local_full_stream`）。mock 模式下同样为 `false`：
模拟模式没有真流可录，前端联调时别把它当成故障。

### V-Value 与基线怎么算（诚实版）

- `V-Value` = 投料区 ROI（`analysis.roi`，归一化 `[x,y,w,h]`）内**运动像素占比**，取值 0..1。
- 帧差阈值 `analysis.pixel_thr=25`（灰度级）。**没有 numpy 时**降级为"字节异或变化率"
  （即"这一像素变没变"，而不是"变化是否超过 25"）——灵敏度与噪声表现不同，日志里会写明。
- `baseline` = 最近 `metrics.baseline_window_s`（默认 30 min）内 V-Value 的**滚动中位数**
  （中位数对摄食爆发的尖峰不敏感，比均值稳）。
- `ratio = v_value / baseline`，`thr = baseline × thresholds.splash_ratio`。
- **冷启动保护**：基线需要 ≥10 个采样点且 >0 才允许出 `splash_activity`，
  并且要求 `V-Value ≥ detector.splash_floor`（默认 0.5%），避免开机场误报。
- 曲线端点按 `step` 分桶取**均值**降采样；历史不足时用已有桶的中位数兜底（不假装有历史）。

---

## 7. 依赖降级矩阵（缺依赖不许起不来）

| 缺失 | 后果 | 兜底路径 | 在哪里能看到 |
|---|---|---|---|
| 全部第三方包 | 仍能启动、仍符合契约（simulate 模式完整可用） | 纯标准库：YAML 子集解析器 + 字节异或运动检测 + 网格连通域 + 纯 Python baseline JPEG 编码器 | `/api/v1/logs` |
| `numpy` | 运动检测精度下降（噪声也算变化，基线偏高） | 纯 Python 异或变化率 | 日志 + `health.services` 里 `numpy: ok=false` |
| `opencv-python` | live 模式下**不产出** `person` 事件（不假装检出）；暗斑用纯 Python BFS | 网格抽样 + BFS 连通域 | 日志 + `services` 里 `opencv-python: ok=false` |
| `pyyaml` | 用内置极简 YAML 子集解析（块映射/列表/行内流式/注释/引号） | `config.py::mini_yaml_load` | 日志 |
| `onvif-zeep` | 云台走**本地状态机**：接口行为完全一致，但不会真的转相机 | `onvif_ptz.py` 的 mock 后端（位置持久化到 `data/ptz.json`） | 日志 + `services` 里 `ptz` 项 |
| `ffmpeg` | 不能 `-c copy` 录像；拉流改用 OpenCV | 日志明确写出"未安装 ffmpeg，本地全码流录像不可用（检测/抓图不受影响）" | `health.storage.recording=false` |
| `ffmpeg` 和 `opencv` 都没有 | 拉不了 RTSP，相机一直 `online:false` | 不崩：指数退避重连 + 发 `offline` 事件 | 日志 |
| `mmcli` / CPE 路由模式 | `net.rssi_dbm`、`net.carrier` 为 `null` | —— | 日志（说明这是 CPE 路由模式下的正常现象） |

降级原因**同时**出现在：① `/api/v1/logs` 的 `warn` 行；② `/api/v1/health` 的 `services[]`
（缺哪个能力就有一条 `{"name": "<组件>", "ok": false}`）；③ systemd 日志（stdout）。

---

## 8. 4G 友好设计

- **默认只回传缩略图**：抓图默认 `capture.max_width=1920`、`jpeg_quality=85`；
  前端要更省可以 `?w=480`。事件本体只有几百字节 JSON。
- **SSE 而不是 WebSocket**：心跳 15 s（注释行，不触发前端 `onmessage`），断线由浏览器自动重连。
- **所有大响应支持 `?limit=`**：`events` / `snapshots` / `logs` 默认 200/500/200，上限 2000；
  曲线支持 `?step=` 降采样 + `?limit=` 截断。
- **回传策略** `upload.policy`（三个值都有真实行为，不是装饰）：
  `thumbs_only`（默认：定时 + 事件抓图，缩放到 `capture.max_width`）；
  `events_only`（只存事件抓图，定时抓图循环直接空转）；
  `full`（抓图**不缩放**，保留相机原始分辨率——4G 下最费流量，仅在本地存档场景用）。`health.net.month_bytes` 从 `/proc/net/dev` 累计并持久化，
  重启不清零，可对 `month_quota_bytes` 做超量预警。
- **`clip` 默认不产出**：契约 §3 写明 4G 下建议只给 snapshot，所以没有切片时明确 404，
  而不是偷偷回一个大 mp4。

---

## 9. 稳健性

- **断流重连**：指数退避 1→2→4→…→60 s（带 ±15% 抖动），重连成功写 `info` 日志；
  连续失败 ≥30 s 发一次 `offline` 事件（同一次掉线只发一次，恢复后重新武装）。
  实测：相机掉电/断网时，`detector.stream_stall_s=10`（10 s 没有新帧就杀掉拉流进程重连）
  + 契约要求的 30 s 判定 ≈ **40 s** 就会在事件流里看到 `offline`，进程不会崩。
- **ffmpeg 不会挂死**：拉流进程额外挂了 `-timeout`（socket 超时，默认 10 s）与一个
  卡死监控线程（`stream_stall_s`，默认 10 s 无新帧就 kill 重启），避免阻塞读永远不返回。
- **口令不外泄**：`/api/v1/cameras` 里的 RTSP URL 一律是 `admin:***@…`；
  ffmpeg/录像进程的 stderr 在写日志前也会把 `rtsp://user:pass@` 打码（`camera.mask_credentials`）。
- **永不崩**：采集/检测/清理/网络各线程全部 `try/except` 兜底，异常只记日志；
  相机连不上、RTSP 半死不活、磁盘写满、ONVIF 报错都不会让进程退出。
- **SQLite WAL** + `synchronous=NORMAL`，单连接加锁；事件 ID 形如 `ev-20260919-0007`（按天自增）。
- **磁盘管理**：先按保留天数清（抓图 14 天 / 事件 90 天 / 日志 14 天 / 指标 30 天 / 录像 14 天），
  剩余空间低于 `storage.min_free_gb`（默认 3 GB）时**继续清最旧抓图**直到达标，并写 `warn` 日志。
  只动自己的 `data/` 目录，不碰系统与用户文件。
- **断电安全**：配置与 `ptz.json` 都是 `写临时文件 + os.replace`；抓图先写 `.tmp` 再改名。
- **抓图 URL 唯一**：契约 §5 的 URL 形如 `/api/v1/snapshots/{ts}.jpg`（不含相机名），
  所以同一秒内第二台相机的抓图会自动顺延 1 s，保证每个 URL 都能寻址到唯一文件。

---

## 10. 排障

| 现象 | 先看这里 | 常见原因与处理 |
|---|---|---|
| 相机一直 `online:false` | `curl /api/v1/logs?limit=50` | ① IP/口令不对；② 相机 RTSP 没开或端口不是 554；③ 不在同一网段；④ 密码里有 `@`/`:` 等特殊字符（URL 里要转义，建议换成字母数字）；⑤ PoE 交换机没上电 |
| 日志里 "既没有 ffmpeg 也没有 opencv-python" | `which ffmpeg` | `sudo apt install -y ffmpeg` |
| `person` 事件从来不出现 | `GET /api/v1/health` 的 `services` | 缺 `opencv-python`（装了才有 HOG）；或 `person_roi` 太小（HOG 需要 ≥64×128 像素）；或阈值 `thresholds.person_confidence` 太高 |
| `splash_activity` 不触发 | `/api/v1/logs` 里有没有"基线预热中" | ① 基线要在 10 个采样点后才有意义（约 1 分钟）；② `analysis.roi` 没圈到投料点；③ 基线本身太高（水面一直在动）→ 调大 `thresholds.splash_ratio` 或缩小 ROI |
| 误报太多 | `/api/v1/metrics/splash` 看曲线 | 调大 `splash_ratio`、加长 `splash_min_s`、把 `splash_require_feed_window` 设为 `true`（只在投料窗口内报） |
| 云台点了不动 | `/api/v1/logs` 里 `ptz` 的 warn | ① 没装 `onvif-zeep` → 走 mock（预期行为，接口一致但不动真机）；② 相机端没开 ONVIF（配置 → 网络 → 高级配置 → 集成协议，建一个 ONVIF 用户）；③ 相机 ONVIF 端口不是 80 → 改 `onvif_port` |
| `net.rssi_dbm` 是 `null` | 正常 | 4G CPE 路由模式下，树莓派看不到 4G 模组，读不到信号强度。要看信号请登录 CPE 管理页，或把 `net.carrier` 手工填上 |
| `net.uplink_kbps` 是 `null` | `ls /proc/net/dev` | 非 Linux（开发机）没有 `/proc`。树莓派上一定有 |
| `health.pi.temp_c` 是 `null` | `ls /sys/class/thermal/` | 开发机（macOS）没有该节点；树莓派上有，读不到时固件会写 warn 日志说明原因，**不编温度** |
| 磁盘满 | `/api/v1/logs` + `health.pi.disk_free_gb` | 固件会自动清最旧抓图；仍不够就调小 `record.keep_days`、关掉 `record.local_full_stream`、或换更大的卡 |
| 相机断电后多久能看到 `offline` 事件 | `/api/v1/events?type=offline` | 实测约 40 s：10 s 无帧杀进程重连（`stream_stall_s`）+ 契约要求的 30 s 判定。想更快就调小这两个值 |
| 时间不对导致投料窗口错乱 | `date` | 树莓派没有 RTC，开机要等 NTP。`timedatectl set-ntp true`；同时 systemd 单元已 `After=time-sync.target` |
| 端口被占 | `ss -lntp \| grep 8080` | 改 `--port` 或 `server.port` |
| 前端改了 `API_BASE` 还是连不上 | 浏览器控制台 | 固件已开 CORS；确认是 `http://<树莓派IP>:8080`（不是 https），并且树莓派防火墙放行 |

---

## 11. 验收标准（照着跑，全绿即验收通过）

```bash
# 1) 契约一致性（21 项，不需要 pytest、不需要相机、不联网）
python3 tests/test_contract.py
#    期望：21/21 PASS，最后一行 "通过 21 / 21，失败 0"

# 2) 一键自检（真起子进程，打全部端点）
python3 tools/selfcheck.py --simulate
#    期望：16/16 PASS，包含 health/cameras/snapshot/ptz/presets/events/ack/snapshot/clip/
#          SSE/metrics/snapshots/config/logs/静态页/404

# 3) 装了 pytest 的话
python3 -m pytest tests/ -q

# 4) 手动抽验（服务已在跑）
curl -s http://127.0.0.1:8080/api/v1/health | python3 -m json.tool
curl -s "http://127.0.0.1:8080/api/v1/events?limit=5" | python3 -m json.tool
curl -s "http://127.0.0.1:8080/api/v1/metrics/splash?window=24h&step=300" | python3 -m json.tool
curl -s -o /tmp/s.jpg -w '%{content_type} %{size_download}\n' \
     http://127.0.0.1:8080/api/v1/cameras/cam-pano/snapshot     # 期望 image/jpeg <N>
curl -sN http://127.0.0.1:8080/api/v1/stream/events | head -5    # 期望看到 ": connected" / event: event
```

硬性验收点：

1. `--simulate` 能起、能出合规数据，`health.mode == "mock"`；
2. 默认模式连不上相机**不崩**，相机 `online:false` 且发 `offline` 事件；
3. 拔掉/不装 `numpy`、`opencv-python`、`pyyaml`、`onvif-zeep` 里的任意组合仍能启动，且降级原因可见
   （`tests/test_contract.py::test_degrades_without_any_third_party` 会把这几项全部屏蔽后重跑一遍）；
4. 每个 `GET` 的字段/类型/枚举与契约逐字一致（`tests/test_contract.py` 断言）；
5. 抓图是合法 JPEG、SSE 能收到实时事件、`PUT /config` 能落盘并在重读后生效。

---

## 11.5 现场必看：SD 卡容量账

按契约示例的码率（每台 4096 kbps）估算：

| 项目 | 数值 |
|---|---|
| 单路全码流 | ≈ 43 GB/天 |
| 两路（全景 + 细节） | ≈ 86 GB/天 |
| 保留 14 天 | ≈ **1.2 TB** |
| 常见 TF 卡 | 64 / 128 / 256 GB |

**所以默认的 `record.keep_days: 14` + 全码流在 TF 卡上一定不够**。三种正解，按推荐顺序：

1. 录**子码流**：把 `cameras[].rtsp_path` 改成 `/Streaming/Channels/102`（海康子码流，通常 512 kbps~1 Mbps，
   降到约 1/8 容量），主码流只用来抓图；
2. 把 `record.keep_days` 调到磁盘装得下的天数（例如 128 GB 卡 + 子码流 ≈ 10~20 天）；
3. 外接 USB SSD/HDD 并把 `storage.data_dir` 指过去。

固件在启动时会算这笔账，估算需求超过磁盘容量 80% 就在 `/api/v1/logs` 里写一条 `warn`
（"容量告警：…"，见 `Runtime._warn_capacity`），不会等你写满才发现。

---

## 12. 证据等级与已知限制（别把 mock 当实测）

- 本项目沿用既有的证据分级：**A 实测 / B 经验 / C 演示**。
  当前固件**全部事件都标 `evidence: "C"`**，因为：没有现场标定数据、没有真机验证、
  阈值来自调研报告的默认值。**在完成现场标定之前，不得把任何事件当作 A 级结论。**
- `person` 的 HOG 置信度不是标定过的概率，只是 SVM 分数的**单调映射**（`detail` 里已注明"未标定"）；
  误报漏报都需要现场用真实画面重新定阈值（必要时配 MobileNet-SSD 模型，会更准）。
- `surface_aggregation` 只是"浮头/聚集"的**粗略代理**，不是溶氧结论。
- `splash_activity` 是**相对基线**的比值，不是绝对摄食量；不同天气/光照下基线会漂。
- 未实现：录像切片回放（`clip` 端点只在有切片文件时返回）、上传限速（`upload.max_kbps` 目前只记录不执行）、
  Web 端构建产物（前端由 `yutang-vision-console/` 提供，固件只负责托管）、
  真实 ONVIF 云台与相机在本机**未实测**（无设备）。
