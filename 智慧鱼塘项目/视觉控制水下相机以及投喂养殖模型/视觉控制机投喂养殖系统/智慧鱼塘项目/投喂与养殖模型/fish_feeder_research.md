# 开源/DIY 自动喂鱼器（定量投料 + 称重闭环）联网调研

> 调研方法：web_search + web_fetch 实际抓取。**只列出我 fetch 成功并看到正文内容的 URL**；仅确认「页面存在 + 标题」而正文被 JS 渲染挡住的，会明确标注。参数一律引用原文片段，未编造。
> 检索关键词组（≥6 组）：① ESP32 fish feeder github auger stepper ② Arduino fish feeder HX711 load cell github ③ ESPHome fish feeder component ④ instructables automatic fish feeder auger ⑤ 自动喂鱼器 DIY 步进电机 螺旋 开源 ESP32 ⑥ 投饵机 称重 闭环 HX711 ⑦ 立创开源硬件平台 自动喂鱼器 ⑧ fish feeder load cell closed loop dispense weight feedback ⑨ load cell feed dispenser accuracy aquaculture paper ⑩ ArduPilot feeder component ⑪ DFRobot 自动喂鱼器 称重 ⑫ raspberry pi fish feeder auger

---

## 一、核心结论（先看这段）

1. **"称重闭环"在鱼类/水族喂食器上几乎没有成熟开源实现。** GitHub 仓库搜索 `fish feeder load cell` → **total_count: 0**（见 api.github.com/search/repositories?q=fish+feeder+load+cell，实际抓取结果）。称重闭环案例全部集中在**宠物（猫/狗）喂食器**，鱼类场景最接近的是「料斗余料称重监控」而非「投料量闭环」。
2. **鱼类喂食器的主流定量方式是「时间 × 转速」开环**，作者自己承认不可靠——见下文 joedvorak 项目的原文自述。
3. **ESPHome 生态没有现成的 `feeder` 自定义组件**：官方 devices 库只有「把某款成品喂食器刷成 ESPHome」的设备页（iLonda L88），社区版是通用 GPIO/switch/motor 拼装（VSON WP8621）。**没有可复用的 feeder 组件**。
4. **ArduPilot 生态未找到喂食器组件**（只有通用 servo/gripper 文档）。
5. 对鱼塘场景最值得借鉴的两个点：**① 绞龙（auger）+ 步进电机做容积式计量**；**② 料斗/投料仓称重做余量与投料量双重校核**（aquaculture 论文与 AquaFeeder 走的就是这条路）。

---

## 二、GitHub — ESP32 / Arduino 鱼类喂食器

### 1. itohio/FishFeeder ⭐23 — 最成熟的 ESP32 鱼类喂食器
- 链接：https://github.com/itohio/FishFeeder
- 平台：GitHub（Go / TinyGo）
- 技术方案：ESP32 **M5StickC**；**9g 舵机**投料；3D 打印投料器（FreeCAD）；M5Stack IR 温度传感器 MLX90614；串口远程控制（波特率 152000）
- 称重闭环：**无**
- 开源情况：**MIT License**，含 3D 模型（`parts/dispenser.jpg`、`parts/dispenser-drawing.jpg`）
- 最后活跃：`pushed_at: 2025-05-04`（GitHub API）
- 证据（README 原文）：*"Dispense food using a cheap 9g server"*；*"Three individually resettable timers: Feeding / water changes / filter maintenance"*
- 可借鉴点：**多定时器（投喂 24h / 换水 1 周 / 滤桶维护 3 个月）的状态机设计**，比单纯定时投喂更贴合鱼塘运维；串口字符命令协议（f/d/r/i/t）简洁可移植。

### 2. ataboo/esp-fish-feeder — ESP-IDF + 步进电机 + 限位开关
- 链接：https://github.com/ataboo/esp-fish-feeder
- 平台：GitHub（C / ESP-IDF）
- 技术方案：ESP32 dev kit、**4-pin 步进电机 + 驱动器**、**限位开关**、2 个按钮
- 称重闭环：**无**（用限位开关做位置闭环）
- 开源情况：GPL-3.0，纯代码无 3D 模型（size 36 KB）
- 最后活跃：`pushed_at: 2025-07-09`（⭐0）
- 证据（README 原文）：*"ESP32 dev kit / 4-pin stepper motor / driver / Limit switch / 2 push-buttons"*
- 可借鉴点：**限位开关归零 + 步进步数**是低成本「位置闭环」，可替代称重做粗略定量；低功耗休眠（日出/日落唤醒）。

### 3. Victor2266/Scheduled-Fish-Feeder — 28BYJ-48 + 3D 打印导轨
- 链接：https://github.com/Victor2266/Scheduled-Fish-Feeder
- 平台：GitHub
- 技术方案：ESP32 + **28BYJ-48 步进电机** + 3D 打印导轨推出饲料
- 称重闭环：**无**
- 开源情况：代码开源，3D 模型在 Thingiverse https://www.thingiverse.com/thing:5390070
- 最后活跃：未从 API 单独确认
- 证据（README 原文）：*"controls an ESP32 to move a 28ybj-48 stepper motor at specific times of the day to move a 3D printed rail that dispenses food for my betta fish"*
- 可借鉴点：**28BYJ-48 是最便宜的定量执行器**，导轨式出料适合颗粒料；作者自述 *"right now I just manually program the time"*，说明缺少配置界面是通病。

### 4. sunhanaix/FeedFish ⭐11 — 中文项目，ESP32 + MG995 + 小爱同学
- 链接：https://github.com/sunhanaix/FeedFish
- 平台：GitHub（Python / MicroPython）+ B站演示
- 视频：https://www.bilibili.com/video/BV1Sw4m117XV （已 fetch 确认标题：「ESP32+MG995舵机做一个户外自动喂鱼装置。」）
- 技术方案：ESP32 主控 + **MG995 舵机** + MQTT（mosquitto）+ Flask Web + SQLite + 巴法云（小爱同学语音）+ 自建 MQTT OTA
- 称重闭环：**无**
- 开源情况：MIT，代码开源
- 最后活跃：`pushed_at: 2024-08-03`
- 证据（README 原文，含**失败经验**，很有价值）：
  - *"后面发现这样转几天后，精度不够的原因，食料瓶子就头朝下了，这样再加上瓶子身上雨衣，下雨天时，鱼食会被淋湿，堵死出孔。"*
  - *"MG995只能给它正转指令或者反转指令…它没法儿像其它舵机那样，精确到某个角度"*
  - 实测电流：*"不加电容的话，带负载情况下启动舵机，电压在5V，电流在90mA-220mA之间"*
- 可借鉴点：**户外防雨 + 防潮堵料**是鱼塘的真实痛点（作者用外卖汤盒 + 热熔胶 + 矿泉水瓶 + 塑料袋裙边）；**360° 舵机无法定位，必须换 180° 舵机**——这是选型坑，鱼塘项目务必避开。

### 5. yyq8548/Smart-fish-feeder-digital-control ⭐62 — 工程化程度最高的 ESP32 喂食器
- 链接：https://github.com/yyq8548/Smart-fish-feeder-digital-control
- 平台：GitHub（Python/C++/JS）
- 技术方案：ESP32 + Arduino + **DS18B20 水温** + **双向泵（正转投料 / 反转清洗管路）** + 半导体制冷；MQTT over TLS + Mosquitto + FastAPI + SQLAlchemy + SQLite + Docker/Traefik；HMAC-SHA256 签名指令、NVS 防重放
- 称重闭环：**无**（靠时间控制泵：*"Enter a feed duration between 500 and 60,000 milliseconds"*）
- 开源情况：开源（无 LICENSE 字段，`license: null`），含 Wokwi 仿真
- 最后活跃：`pushed_at: 2026-08-02`
- 证据（README 原文）：
  - *"The ESP32 runs the pump forward to dispense food, pauses for safety, reverses the pump to clean the tube, and then returns to idle."*
  - Pin map：`GPIO 26 Pump driver forward` / `GPIO 27 Pump driver reverse` / `GPIO 33 Pump enable` / `GPIO 4 DS18B20`
  - *"It stores the accepted-command watermark in NVS so a reboot cannot replay an old feed instruction."*
- 可借鉴点：**液态饵料场景的「正转投喂 + 反转清洗」双泵方案**，解决管路残留堵塞；**指令幂等 + 防重放 + 离线禁用**的安全模型值得直接抄；投喂时长 500–60000 ms 的边界校验。

### 6. RiccardoBonesi/fishFeeder ⭐7 — Telegram 远程喂鱼
- 链接：https://github.com/RiccardoBonesi/fishFeeder
- 平台：GitHub（C++/Arduino）
- 技术方案：**NodeMCU ESP8266** + 舵机 + Telegram Bot（UniversalTelegramBot + ArduinoJson）
- 称重闭环：**无**
- 开源情况：开源
- 最后活跃：`pushed_at: 2019-06-10`
- 证据（README 原文）：*"fishFeeder is an Arduino (ESP8266) Telegram controlled fish feeder"*；安全设计 *"Replace with your chat_id to prevent other people from feeding your fish"*
- 可借鉴点：**Telegram/IM Bot 做远程手动投喂**是最低成本的远程控制路径（鱼塘无公网 IP 时尤其有用）；`chat_id` 白名单防误触发。

### 7. nahueltaibo/fish-feeder ⭐5 — ESP32 鱼类喂食器
- 链接：https://github.com/nahueltaibo/fish-feeder
- 平台：GitHub（C++）
- 技术方案：ESP32
- 称重闭环：**无**
- 最后活跃：`pushed_at: 2026-04-28`
- 证据：GitHub API `description: "Esp32 based automatic fish feeder"`
- 可借鉴点：体量小，可作代码骨架参考。

### 8. ColoMAX/fishfeeder ⭐5 — ESP8266 + ESPHome 独立喂食器
- 链接：https://github.com/ColoMAX/fishfeeder ｜ 文档：https://colomax.github.io/fishfeeder/
- 平台：GitHub（YAML / ESPHome）
- 技术方案：ESP8266 + ESPHome
- 称重闭环：**无**
- 开源情况：MIT，含 GitHub Pages 文档
- 最后活跃：`pushed_at: 2024-01-21`
- 证据：GitHub API `description: "Standalone automatic fish feeder, based on a ESP8266 with esphome."`，topics 含 `esphome`、`fishfeeder`
- 可借鉴点：**纯 YAML 配置（无需写 C++）**，适合快速迭代；可作 ESPHome 接入鱼塘的起点模板。

### 9. juanmcasillas/CatFeeder-Auger ⭐6 — 绞龙 + ESP8266（跨物种可借鉴）
- 链接：https://github.com/juanmcasillas/CatFeeder-Auger
- 平台：GitHub（JavaScript/C++）
- 技术方案：ESP8266 + **Auger 绞龙** + 3D 打印 + WWW 配置界面
- 称重闭环：**无**
- 开源情况：**GPL-3.0**
- 最后活跃：`pushed_at: 2019-10-30`
- 证据：GitHub API `description: "A 3D printable, fully programmable, automatic pet feeder with WWW interface support using ESP8266 (Auger Version)"`
- 可借鉴点：**绞龙是容积式计量，比闸门式更适合颗粒饲料**；3D 可打印 + 网页配置是完整闭环。

### 10. GermainBrunet/Arduino-Fish-Feeder — 舵机驱动绞龙
- 链接：https://github.com/GermainBrunet/Arduino-Fish-Feeder
- 平台：GitHub（C++）
- 技术方案：**Arduino UNO + OSEPP LCD Keypad Shield + EZRobot 360 连续旋转舵机** 驱动绞龙
- 称重闭环：**无**
- 开源情况：MIT
- 证据：GitHub API `description: "Software used with an Arduino UNO, OSEPP LCD Keypad Shield, EZRobot 360 servo, to control an auger used to deliver food to fish on a scheduled basis."`
- 可借鉴点：**连续旋转舵机 = 最廉价的绞龙驱动**（无需步进驱动器）；带 LCD 键盘面板可本地设置。

### 11. nbourre/fish_feeder — Arduino + 28BYJ-48
- 链接：https://github.com/nbourre/fish_feeder
- 证据：GitHub API `description: "Arduino based fish feeder using a 28BYJ-48 stepper motor"`
- 称重闭环：无 ｜ 最后活跃 `pushed_at: 2019-07-15`
- 可借鉴点：同 3，最简步进方案。

### 12. ⭐ joedvorak/Final-Project-24-Auto-Fish — 高校课程项目，绞龙 + 步进 + 3D 打印（**含"开环不可靠"的自我证词**）
- 链接：https://github.com/joedvorak/Final-Project-24-Auto-Fish
- 平台：GitHub（Arduino .ino）+ Onshape CAD
- 技术方案：**2× Arduino Uno**；**5V 步进电机 28BYJ-48 + 绞龙（auger）**；3D 打印料斗/支架/绞龙/垫片；LCD ×2、电位器 ×3、热敏电阻、浮子开关
- 称重闭环：**无**
- 定量方式：时间开环，*"the 6 hr., 12 hr., and 24 hr. intervals will begin with a feeding of approximately 15 seconds"*
- 开源情况：**代码 + Onshape 3D 文件全部公开**（Onshape 链接在 README 中）
- 证据（README 原文，**关键**）：
  - *"The design of the feeding system was a small hopper with an auger in the bottom of that would be turned by a stepper motor to slowly push the food out…"*
  - **"This system is incapable of knowing how much food to dispense at one time depending on volume, it dispenses based on a time interval. The same volume of food being dispensed every time is highly unlikely."**
  - *"The limitations of this system will be if it is in a moist environment, some of the electrical components may end up rusting"*
- 可借鉴点：**这是"为什么必须做称重闭环"的最直接论据**——绞龙容积式仍然受料位、湿度、颗粒分布影响；作者明确指出开环定量体积不可重复。3D 打印料斗+绞龙结构可直接参考。

---

## 三、含 load cell / HX711 称重闭环的项目

> ⚠️ 再次强调：以下是**宠物喂食器**为主，鱼类项目几乎没有。但机械与控制逻辑可迁移。

### 13. ⭐ bakeromso/petfeeder — 最接近"称重闭环"的实现（改造 Petwant F1）
- 链接：https://github.com/bakeromso/petfeeder
- 平台：GitHub（C / ESP8266 RTOS SDK）
- 技术方案：**改装 Petwant F1 成品喂食器** → ESP8266 + **HX711 称重电路**；MQTT → Home Assistant；`/petfeeder/calibrate/tick`（电机步进）、`/petfeeder/calibrate/raw/req|resp`（读原始秤值）
- **称重闭环：是**（用秤来细化出料量）
- 开源情况：开源，含 ESP8266 toolchain 与 CLion 完整构建说明
- 最后活跃：`pushed_at: 2022-07-15`
- 证据（GitHub API description 原文）：**"Modded pet feeder of Petwant F1, so that Home Assistant (or any server) can connect to it over MQTT. Modded hardware runs on ESP8266, and connects to an HX711 scale circuit. The scale is used make the dispensed amount more fine grained"**
- README 另有工程细节：*"It seems MQTT publish can not be called too frequently, crashes on 2 sec interval, seems fine on 5 sec. Alternative is to gather more readings, and publish all at once"*
- 可借鉴点：**「电机走一步 → 读一次秤 → 累加到目标重量停」的标定接口设计（tick / raw）非常干净，可直接移植到鱼塘投料机**；MQTT 发布频率限制（≥5s）是 ESP8266 + 称重的实测约束。

### 14. zming-huang/SmartFeeder-ESP32S3 — 明确宣称"真·数据闭环"
- 链接：https://github.com/zming-huang/SmartFeeder-ESP32S3
- 平台：GitHub（C++）
- 技术方案：ESP32-S3 + **HX711 称重传感器**
- **称重闭环：是**（自我描述为数据闭环）
- 开源情况：MIT
- 最后活跃：`created_at 2026-05-26, pushed_at 2026-05-26`（很新，代码量小 size 13 KB）
- 证据（GitHub API description 原文）：**"「拒绝无脑漏粮，做最懂狗子的智能管家！」—— 这是一个基于 ESP32-S3 与 HX711 称重传感器的真·数据闭环智能宠物补粮系统。"**
- ⚠️ 注意：其 README 我 **fetch 超时（2 次）**，未能看到实现细节与精度数据，仅确认仓库描述。**不做进一步断言。**
- 可借鉴点：中文项目、定位就是"拒绝无脑漏粮"，与鱼塘诉求一致，值得后续细读代码。

### 15. Jayamurugan-26/Automatic-Pet-Feeder — ESP32 + RTC + HX711 + 舵机
- 链接：https://github.com/Jayamurugan-26/Automatic-Pet-Feeder
- 技术方案：ESP32 + RTC + **load cell + HX711** + 舵机 + Arduino IoT Cloud
- **称重闭环：是**（称量投料量）
- 最后活跃：`pushed_at 2026-07-16`
- 证据（GitHub API description 原文）：*"The IoT-Based Smart Pet Feeder uses an ESP32, RTC module, load cell with HX711 module, and a servo motor to automate pet feeding… The system dispenses food on schedule and **measures the food quantity accurately** for reliable pet care."*
- 可借鉴点：RTC + 称重 + 云端的组合与鱼塘需求几乎同构。

### 16. snake-overlord/Raspberry-Pi-Auto-Feeder — 树莓派 5 + HX711 + VL53L0X
- 链接：https://github.com/snake-overlord/Raspberry-Pi-Auto-Feeder
- 技术方案：**Raspberry Pi 5**、FSM 状态机、Telegram Bot、**HX711（重量）+ VL53L0X（ToF 余料高度）**、舵机
- **称重闭环：是**
- 开源情况：MIT
- 最后活跃：`pushed_at 2026-05-02`
- 证据（GitHub API description 原文）：*"raspberry-pi pet feeder with FSM, Telegram bot and HX711/VL53L0X sensors"*；topics: `fsm, hx711, pet-feeder, python, raspberry-pi-5, servo-motor, telegram-bot, vl53l0x`
- 可借鉴点：**重量 + ToF 双传感器冗余**——ToF 测料仓余料高度，HX711 测投料量；FSM 状态机适合投料这种多阶段流程。

### 17. ImRoodyDev/PetFeeder-BitbyBit — load cell + 舵机 + ESP8266 + Micro:bit
- 链接：https://github.com/ImRoodyDev/PetFeeder-BitbyBit
- 技术方案：load cell + 舵机 + ESP8266 + Micro:bit + 自研 Java 桌面程序
- **称重闭环：是**
- 最后活跃：`pushed_at 2025-04-24`
- 证据（GitHub API description 原文）：*"The system **precisely measures food weight using a load cell**, dispenses food with a servo motor."*；topics 含 `loadcell`
- 可借鉴点：含 Blender 动画与完整过程文档，适合作为方案汇报素材。

### 18. gauribhale12/Pet-feeder-using-IoT — 树莓派 + 直流电机 + 精密 load cell
- 链接：https://github.com/gauribhale12/Pet-feeder-using-IoT
- 技术方案：Raspberry Pi + DC 电机 + 继电器 + **precision load cell** + MIT App Inventor + Firebase
- **称重闭环：是**（按品种精确称量）
- 最后活跃：`pushed_at 2023-09-21`
- 证据（GitHub API description 原文）：*"It employs a **precision load cell to measure food accurately** for individual pets based on their breed."*

### 19. lily-osp/Servo-and-Load-Cell-with-MQTT — 舵机 + 称重 + MQTT
- 链接：https://github.com/lily-osp/Servo-and-Load-Cell-with-MQTT
- 技术方案：ESP8266 + 舵机 + 称重 + MQTT（Arduino）
- **称重闭环：是**
- 最后活跃：`pushed_at 2023-06-12`
- 证据：GitHub API `description: "Auto pet feeder"`，topics: `arduino, automation, esp8266, feeder, iot, mqtt`

### 20. ⭐ 10Kang/AquaFeeder — **水产养殖**饲料重量实时上云（最贴近鱼塘）
- 链接：https://github.com/10Kang/AquaFeeder
- 平台：GitHub（Arduino）
- 技术方案：**Arduino Uno + ESP8266 WiFi 模块 → AWS IoT Core（MQTT）**；实时监测**水产饲料重量**；后续计划接入温度、pH、硝酸盐
- **称重闭环：部分是**——已做**重量实时监测上云**，目标是 *"potentially served as a automatic feeding machine to improve FCR ratio"*（FCR = 饲料转化率）
- 开源情况：开源（含 `images/aws-real-time.png`、`images/Arduino.jpeg`）
- 最后活跃：README 称 *"Continuous update of the project will be updated weekly"*，但仓库内容偏早期
- 证据（README 原文）：
  - *"A repository hosting the Arduino code for **real-time monitoring of aquaculture feed's weight**, and potentially served as a automatic feeding machine to improve FCR ratio in the aquaculture industry."*
  - *"Currently have established a MQTT connection via esp8266 WIFI modules with AWS cloud service"*
- 可借鉴点：**这是唯一明确以「水产养殖 FCR 提升」为目标的重量监测开源项目**——把「投了多少料 / 剩多少料」变成可上云数据，正是鱼塘场景做闭环的起点；FCR 是鱼塘的核心效益指标。

---

## 四、ESPHome / Home Assistant / ArduPilot 生态

### 21. ⭐ ESPHome 官方设备库：Ilonda Wifi Smart Fish Feeder (L88)（**非自定义组件，是成品设备适配**）
- 链接：https://devices.esphome.io/devices/ilonda-wifi-smart-fish-feeder/ （已 fetch 全文）
- 平台：ESPHome 官方 Devices 库
- 方案：涂鸦（Tuya）成品喂食器，用 **tuya-convert** 刷 ESPHome；ESP8266 (esp01_1m)
- **关键配置（原文抄录）**：
  ```yaml
  switch:  # 开 3 秒后自动关
    - platform: gpio
      name: 'Relay feeder'
      id: relay
      pin: GPIO14
      on_turn_on:
        - light.turn_on: led
        - delay: 3s
        - switch.turn_off: relay
        - light.turn_off: led
      restore_mode: ALWAYS_OFF
  sensor:  # 用脉冲计数记录投喂次数
    - platform: pulse_meter
      pin: GPIO12
      name: 'Counter/min'
      internal: true
      total:
        name: 'Counter feeder'
  ```
- **称重闭环：无**（只有投喂**次数**计数 `Counter feeder`，不是重量）
- 可借鉴点：**`pulse_meter` 做投喂次数累计**是零成本计量的最简做法；`delay: 3s` + `restore_mode: ALWAYS_OFF` 保证上电不会误投料——**鱼塘断电恢复安全性必须这样写**。

### 22. ⭐ Home Assistant 社区：VSON WP8621_V12 鱼缸喂食器 ESPHome 改造（含**份数定量**与**缺料检测**）
- 链接：https://community.home-assistant.io/t/vson-wp8621-v12-fish-feeder/759621 （已 fetch 全 18 楼）
- 平台：Home Assistant Community（ESPHome 版）
- 技术方案（硬改）：**拆掉原 WIFI001_V20 芯片，换 ESP12E**（或用 ESP32 Wemos S2 mini 整板替换）；GPIO 反推记录：`GPIO15 开合检测 / GPIO0 按钮 / GPIO4 蓝灯 / GPIO5 红灯 / GPIO8+GPIO10 TC118S 电机驱动 / GPIO14 缺料指示`
- **定量方式：按"份数"循环**（Home Assistant `input_number` 设定份数，每份 = 电机转一次 = 30s 或由开合传感器触发停止）
- **缺料检测：有**（`GPIO14 Food Level Sensor`，`device_class: problem`，红外对管原理）
- **称重闭环：无**（用开合开关当计数，属位置/次数闭环）
- 最后活跃：帖子从 2024-08-13 持续到 2025-12-12（有后续提问）
- 证据（原文片段）：
  - 计数逻辑：*"id(open_close_counter) += 1; id(open_close_counter_sensor).publish_state(id(open_close_counter));"*
  - 自动化：*"I've created a simple automation that allows you to set the time of feeding and the amount of servings the fish need."*（`repeat: count: {{ states('input_number.{{fish_meals}}') | int }}`）
  - **失败模式（重要）**：用户 mattias 报告 *"if home assistant is down for too long, the feeder dumps all of its food!"*，Neel Malik 回复定位到 *"GPIO 0 is not a safe pin to use, since it must be HIGH on boot"* 且 *"esphome gets nervous when HA doesn't contact it regularly, after some point it reboots, by design"*
  - 可靠性补丁（Elwinmage）：*"I also add 5 feeding slots to ensure the feeding even if homeassistant crash: On each slot you can set time and portion."*
- 可借鉴点：**这是最有价值的"踩坑合集"**——① 云端/HA 掉线导致 ESPHome 自动重启 → 上电即投料 → 一次投完整仓，鱼塘会直接死鱼，必须 `restore_mode: ALWAYS_OFF` + 避免用 GPIO0 触发；② **本地 5 个时段兜底**（不依赖云端）是鱼塘必备；③ 开合传感器做份数计数，等价于低成本位置闭环。

### 23. ESPHome 是否有现成 `feeder` 自定义组件？
- **未找到。** 检索 `ESPHome fish feeder component custom` 的结果只返回：① 上述 iLonda 官方设备页；② 上述 HA 社区 VSON 改造贴；③ 通用组件文档。ESPHome 组件库（https://esphome.io/components/ ）**没有 feeder 类组件**，可行路径只有 `switch` + `delay` + `globals/lambda` 或自写 `external_component`。

### 24. ArduPilot 是否有喂食器组件？
- **未找到可靠来源。** 检索 `ArduPilot feeder component` 只返回通用文档：https://ardupilot.org/copter/docs/common-servo.html 与 `common-gripper-servo.rst`（舵机/夹爪），**没有任何 aquaculture/feeder 相关组件**。若鱼塘用 ArduPilot（如船/无人机投饵），只能自行用 `SERVOx_FUNCTION` 映射舵机通道。

---

## 五、中文平台

### 25. 电子发烧友：物联网水族馆喂鱼器开源（**ESP32 + 舵机 + 绞龙**，含"未做称重"的自述）
- 链接：https://www.elecfans.com/soft/Mec/2022/202211171929355.html （已 fetch 正文）
- 平台：电子发烧友（资料下载 + 说明页，zip 0.11 MB，免费）
- 技术方案：**ESP32**（作者把 coberdas 项目的 Arduino Nano 换成 ESP32）；**舵机驱动螺旋钻（auger）**；绞龙置于管中，从料斗下料；ESP32 开机建 AP 配网 → 连 NTP 取时间 → Web App 经 **MQTT** 下发指令
- **称重闭环：无**
- 原文证据：
  - *"伺服系统连接到分配鱼食的螺旋钻。"*（配图「螺旋钻」「螺旋管」「连接到料斗的螺旋管」）
  - *"到目前为止，我只尝试过薄片，效果很好。我将尝试使用颗粒型鱼食并在此处发布更新。"*
  - **未来计划（关键）**：*"未来的更新包括安全性（如前所述），以及**一种测量料斗上剩余食物的方法**。"* → 即**作者尚未实现余料称重**
- 可借鉴点：**"料斗 + 螺旋管 + 绞龙"是与鱼塘投饵机最同构的机械结构**；作者明确把"测量料斗剩余食物"列为待办，说明这是公认缺口；薄片料可行、颗粒料待验证的结论对选料有参考价值。

### 26. 启明云端 / 乐鑫代理：ESP32-S3 + 步进电机，定时定量自动投喂
- 链接：https://www.wireless-tag.com/article-item-325.html （已 fetch 全文）｜同文转载：https://m.elecfans.com/article/7479973.html
- 平台：厂商博客（深圳市启明云端，乐鑫代理商），2025-12-08
- 技术方案（原文材料清单）：*"1 块 ESP32-S3 开发板 / 165×55×10mm 面包板 / 15cm 杜邦线 / **3D 打印鱼食投喂器结构件** / **步进电机** / **步进电机驱动板**"*；主控为自研 WT9932S3-NANO（ESP32-S3R8）
- **定量方式：按步进电机转数**——原文：*"组装完成后加入鱼粮，**测试定量转动两圈时鱼粮的自动投放效果**"*
- **称重闭环：无**
- 开源情况：*"本期代码还是全开源！后台私信 **ESP32NANO智能桌面生态鱼缸** 自动获取鱼缸项目源码百度网盘链接"* → **代码未直接给链接，需私信获取，非完全公开**
- 可借鉴点：**"转 N 圈 = 定量"是工业投饵机的通用标定思路**（步进电机步数 → 体积），但同样需要称重做标定验证；3D 打印结构件 + 面包板原型流程可复现。

### 27. CSDN：基于 Arduino 的自动喂鱼器 DIY：从硬件搭建到编程控制
- 链接：https://blog.csdn.net/weixin_33958381/article/details/161562824 （已 fetch 正文，后半为付费墙）
- 平台：CSDN 博客（375 阅读，7 赞，7 收藏，发布 2026-08-17）
- 技术方案：**Arduino Uno + SG90 9g 舵机**；**"漏斗 + 伺服摆臂"闸门式**结构；纸板/泡沫/漏斗搭建；`Servo` 库 + `delay` 定时
- **称重闭环：无**（且是**纯延时轮询**，原文：*"在循环中，程序不断地（实际上是通过 `delay` 函数）等待一个预设的时长，比如24小时"*）
- 原文中的关键定量说明：*"我们只需要让它转动一个固定角度（比如90度），就能完成一次'打开-关闭'的动作，确保每次动作的一致性，从而**控制每次下料的量基本固定**"*
- 电源告警（实用）：*"伺服电机在启动和堵转时瞬时电流较大（可达500-700mA），如果使用电脑USB口供电，可能会因电流不足导致舵机抖动或Arduino板复位"*
- 局限性自述：*"不适合粉末状或极细颗粒的饲料，容易受潮结块的影响"*
- 可借鉴点：**"漏斗 + 摆臂闸门"是最简结构，但下料量与料位强相关**；`delay(24h)` 是非阻塞缺失的反面教材；舵机堵转电流 500–700 mA 对电源设计（鱼塘需长距离供电）是关键数据。

### 28. 立创开源硬件平台（oshwhub）两个项目
- https://oshwhub.com/billyvon/automatic-fish-feeder —— 标题「自动喂鱼器」
- https://oshwhub.com/sxh123/30-yuan-to-make-a-rice-fish-tank —— 标题「30元做一个米家鱼缸喂食器」
- **⚠️ 诚实说明：两页均 fetch 返回 HTTP 200，但正文由 JS 渲染，我只看到标题，未看到原理图/方案/参数。因此不报告任何技术细节。** 仅确认这两个项目页面存在且标题如上；若要细节需人工打开浏览器查看或找 oshwhub 的 API。

### 29. DFRobot 创客社区：行空板 M10 扩展板 · 智控鱼缸
- 链接：https://mc.dfrobot.com.cn/article-317732.html （已 fetch 全文）
- 平台：DFRobot 创客社区（作者「潜川创客」，2025-07-05，340 阅读）
- 技术方案：**行空板 M10（UNIHIKER）+ M10 电机 IO 扩展板 + 电池扩展板**；DS18B20 防水温度、WS2812 RGB、370 真空泵、中英文语音合成；**Mind+ / Python（pinpong 库）**
- 喂食实现：舵机接口驱动自动喂食器（正文提及 *"配合舵机接口，还能实现自动喂食器的精准投喂"*），但**公布的代码只有水温/光照/增氧/红外遥控，没有喂食与称重逻辑**
- **称重闭环：无**
- 许可：**"本项目采用 None（不开放任何权利，保留所有权利）"** → **非开源**
- 可借鉴点：**行空板（Python + 图形化）做鱼塘本地 HMI 门槛极低**；但该项目喂食部分未落地，参考价值主要在传感器/人机交互层。

### 30. B站视频（已确认存在）
- https://www.bilibili.com/video/BV1Sw4m117XV —— 标题「ESP32+MG995舵机做一个户外自动喂鱼装置。」（对应 GitHub 项目 sunhanaix/FeedFish，见第 4 条）

---

## 六、学术文献

### 31. IEEE：An IoT-Based Automated Feed Dispensing System for Pond-Scale Aquaculture
- 链接：https://xplorestaging.ieee.org/document/11291573 （检索结果标题）
- **⚠️ 诚实说明：我 fetch 了该页面，HTTP 200，但返回内容只有 IEEE 账号/购买/帮助等模板文字，没有摘要、方法、参数。** 另尝试 `https://doi.org/10.1109/11291573` → 返回 **"DOI Not Found"**。
- 因此：**仅确认存在这篇题为 "An IoT-Based Automated Feed Dispensing System for Pond-Scale Aquaculture" 的会议论文，标题与池塘级水产养殖投饵直接相关；但摘要、传感器配置、精度数据均未能验证，不做任何断言。** 建议通过学校/机构 IEEE 订阅查阅。
- 若需要：可考虑在 IEEE Xplore 主站 https://ieeexplore.ieee.org/document/11291573 重试（我此次抓取走的是 staging 域名）。

### 32. 其他论文
- 检索到 `https://jurnal.unsil.ac.id/index.php/jeee/article/download/15028/4142`（ISSN 2720-989X），但 **fetch 失败：unsupported content type "application/pdf"**，未获取内容 → **不报告细节**。
- 与「load cell 做投料量闭环」直接对应的鱼类论文：**未找到可靠来源**。宠物称重的开源实现（第 13–19 条）是当前可核实的最接近实践。

---

## 七、明确"未找到可靠来源"的项

| 检索目标 | 结论 |
|---|---|
| GitHub `fish feeder load cell` 仓库 | **total_count: 0**（GitHub 搜索 API 实际返回） |
| 鱼类（非宠物）喂食器的**称重闭环**开源实现 | **未找到可靠来源** |
| ESPHome 现成 `feeder` 自定义组件 | **未找到**（只有成品设备适配页 + 社区 GPIO 拼装配置） |
| ArduPilot 喂食器组件 | **未找到**（仅通用 servo/gripper 文档） |
| Instructables 自动喂鱼器正文 | **未能读取**：https://www.instructables.com/How-to-Make-Arduino-Powered-Fish-Feeder/ 与 https://www.instructables.com/Arduino-Automatic-Fish-Feeder/ 均返回 HTTP 200 但**只有标题**（JS 渲染），无步骤/参数 → 不报告细节 |
| load cell 投料闭环的**鱼类论文** | **未找到可靠来源** |
| 立创开源（oshwhub）项目技术细节 | 页面存在但正文 JS 渲染，**未看到方案细节** |

---

## 八、给鱼塘场景的落地建议（基于以上证据）

1. **执行器选型**：首选**步进电机 + 绞龙（auger）**（第 9、12、25、26 条均验证此路线）。理由是容积式计量天然可标定，且第 12 条虽暴露了开环缺陷，但结构本身被验证可用。避免 360° 连续舵机（第 4 条实测无法定位），避免纯 `delay` 定时（第 27 条）。
2. **称重闭环设计**：借鉴 **bakeromso/petfeeder** 的「tick 走一步 / raw 读秤」标定接口（第 13 条），叠加 **snake-overlord** 的「HX711 重量 + VL53L0X 余料高度」双传感器（第 16 条）。目标控制律：`走一步 → 读秤 → 累加 → 到目标重量停`。
3. **数据层**：直接对标 **10Kang/AquaFeeder**（第 20 条）——把投料重量上云，算 **FCR**；这与鱼塘的养殖效益指标直接对齐。
4. **可靠性红线（血泪教训）**：参考第 22 条 HA 社区案例 —— ① `restore_mode: ALWAYS_OFF`，避免上电即投料；② 不要用 GPIO0 等启动敏感脚做投料触发；③ **本地存 5+ 个投喂时段做兜底**，不依赖云端；④ 断电恢复后禁止补投。
5. **户外防护**：参考第 4 条 —— 防雨盒 + 热熔胶密封 + 防潮裙边，且饲料受潮会堵死出料口，必须做**防潮 + 堵料检测**（可用第 22 条的缺料红外传感器思路反向做堵料检测）。
