# 中国池塘养鱼场户外 ESP32 物联网监测系统：主控板 / 摄像头 / GPS 可采购清单

> 调研时间：2026 年初｜调研方式：web_search + web_fetch + curl 实际打开页面取数
> **所有价格均来自实际打开的页面，未做任何估算填充。**查不到的写「需询价确认」。
> 美元价按 ≈7.1 折算人民币仅作量级参考，已在表中标明「$」原价。

## 可信度分级

| 级别 | 含义 | 本次用到的来源 |
|---|---|---|
| **A 级** | 元器件商城/厂商官方在售页面，价格可复现 | 立创商城 item.szlcsc.com、LCSC 国际站、DFRobot 创客商城、Waveshare 官网、Seeed 官网、u-blox 官网、和芯星通官网 |
| **B 级** | B2B 供应商挂牌参考价 | 供应商网 gys.cn、千寻位置代理商页面 |
| **C 级** | 电商内容营销文章，非商品列表页 | shuma.taobao.com |
| **D 级** | 仅在他人页面推荐位出现，原页未打开 | 仅作线索 |
| **抓取失败** | 403 / 登录墙 / JS 渲染 | 淘宝、天猫、1688、京东、DigiKey.cn、Mouser.cn、waveshare.net、Amazon |

---

# A. ESP32-S3 开发板（带 PSRAM）

## A.1 候选清单（按档次）

| 型号 | 档次 | 关键参数 | 参考价格(¥) | 来源链接 | 备注 |
|---|---|---|---|---|---|
| **立创·ESP32S3R8N8**（LCKFB-ESP32S3R8N8） | 🟢 入门 | ESP32-S3-WROOM-1 **N8R8**（8MB Flash + **8MB PSRAM OPI**），双核 LX7 240MHz | **¥27.12 起**（库存 **1048**） | [立创商城](https://item.szlcsc.com/product/jpg_22034693.html) | **本次调研性价比最高、现货最足**。国产开发板，无摄像头接口（需自行飞线/DVP 排针）。适合做传感器节点 |
| **ESP32-S3-WROOM-1-N16R8**（模组，非开发板） | 🟢 入门 | 16MB Flash + **8MB PSRAM OPI**，240MHz | **¥20.81 起**（库存 **16614**） | [立创商城](https://item.szlcsc.com/product/jpg_3198300.html) | 自绘底板选它。现货极充足。对比 N8R2（¥18.51，2MB PSRAM，库存 13146）与 N16R2（¥21.21，库存 2161） |
| **DFRobot FireBeetle 2 ESP32-S3（N16R8，带摄像头）** DFR0975 | 🟡 标准 | 16MB Flash + **8MB PSRAM**，**板载 OV2640 摄像头接口**，AXP313A 电源管理 | **¥125.00** | [DFRobot 创客商城](https://mall.dfrobot.com.cn/goods-3680.html) | **带摄像头 + 锂电管理 + 低功耗，最适合鱼塘节点**。同系列外置天线版 **¥129.00**（[goods-3681](https://mall.dfrobot.com.cn/goods-3681.html)）；无摄像头 N4 版 **¥69.00**（[goods-3927](https://mall.dfrobot.com.cn/goods-3927.html)） |
| **Waveshare ESP32-S3-DEV-KIT-N8R8** | 🟡 标准 | ESP32-S3-WROOM-1 **N8R8**，240MHz 双核，USB Type-C | **US$9.99**（原价 $15.99）≈¥71 | [Waveshare 官网](https://www.waveshare.com/esp32-s3-dev-kit-n8r8.htm) | 加焊排针版在 Sunsky 标 **¥71.67**（[sunsky 页面](https://www.sunsky-online.com/p/TBD0426281902/Waveshare-ESP32-S3-%E5%BE%AE%E6%8E%A7%E5%88%B6%E5%99%A82.4GHz-Wi-Fi%E5%BC%80%E5%8F%91%E6%9D%BFESP32-S3-WROOM-1-N8R8%E6%A8%A1%E7%BB%84-%E5%8A%A0%E7%84%8A%E6%8E%92%E9%92%88%E7%89%88.htm?lang=zh_CN) 与 $9.99 折算价一致 ✓。**中文站 waveshare.net 被 WAF 拦截，人民币价需询价确认** |
| **Seeed XIAO ESP32-S3 Sense**（113991115） | 🟡 标准 | ESP32-S3R8 **8MB PSRAM** + 8MB Flash，**板载 OV2640 摄像头 + 数字麦克风 + microSD**，拇指大小（21×17.5mm） | 立创 **¥118.09 起**（库存 189）<br>Seeed 官方 **US$13.90** | [立创商城](https://item.szlcsc.com/product/jpg_21669416.html)｜[Seeed 官网](https://www.seeedstudio.com/XIAO-ESP32S3-Sense-p-5639.html) | **最小体积带摄像头方案**。立创价明显高于官方美元价折算（≈¥99），建议对比后再下单 |
| **Seeed XIAO ESP32-S3 Plus**（102010671） | 🟡 标准 | ESP32-S3，8MB PSRAM 级，**无摄像头**，更多 GPIO/外设 | 立创 **¥60.44 起**（库存 194） | [立创商城](https://item.szlcsc.com/product/jpg_50238314.html) | Sense 的无摄像头版 |
| **乐鑫官方 ESP32-S3-DevKitC-1-N8** | 🔵 工业/官方参考 | ESP32-S3-WROOM-1-N8（8MB Flash，**无 PSRAM**），官方参考设计，双 USB-C | 立创 **¥90.82 起**（**库存 0**） | [立创商城](https://item.szlcsc.com/product/jpg_21776890.html) | ⚠️ **N8 无 PSRAM，不能跑摄像头与 AI**。LCSC 国际站（C20438410）1 片 **$36.19**、200 片 $14.44、392 片 $13.96，且 `isPreSale:true`、库存 0（[LCSC 国际站](https://www.lcsc.com/product-detail/C20438410.html)） |
| **乐鑫官方 ESP32-S3-EYE** | 🔵 工业/官方 | ESP32-S3-WROOM-1-N8R8 + **OV2640** + LCD + 麦克风 + IMU + SD | 立创 **¥309.92 起**（**库存 0**） | [立创商城](https://item.szlcsc.com/product/jpg_6661850.html) | 官方 AI 视觉评估板。LCSC 国际站 C5736267 交叉验证：1 片 **$122.74**、240 片 **$48.97**，Out of Stock（[LCSC](https://www.lcsc.com/product-detail/C5736267.html)）。**小批量零售价极不稳定，¥310 与 $122 差 2.8 倍** |
| **立创·实战派 ESP32-S3 开发板**（LCKFB-SZPI-ESP32-S3-VA） | 🟡 标准 | ESP32-S3 + 多外设教学板 | **¥148.00 起**（库存 29） | [立创商城](https://item.szlcsc.com/product/jpg_43285221.html) | 教学向，外设丰富 |

## A.2 档次划分结论

| 档次 | 推荐 | 理由 |
|---|---|---|
| **入门（自研底板）** | ESP32-S3-WROOM-1-N16R8 模组 ¥20.81 + 自绘 PCB | 现货 16614，单价最低，PSRAM 8MB OPI 满足 AI 最低要求 |
| **入门（现成板）** | 立创·ESP32S3R8N8 ¥27.12 | 现货 1048，即插即用 |
| **标准（带摄像头，本项目首选）** | DFRobot FireBeetle 2 ESP32-S3 N16R8 ¥125 | 板载摄像头接口 + 锂电管理（AXP313A）+ 官方中文文档 + Edge Impulse 现成教程 |
| **标准（超小体积）** | Seeed XIAO ESP32-S3 Sense $13.90 / ¥118.09 | 21×17.5mm，集成摄像头+麦克风+SD |
| **工业/官方参考** | ESP32-S3-EYE ¥309.92 / ESP32-S3-DevKitC-1-N8 ¥90.82 | **两者立创库存均为 0**，采购周期不可控；DevKitC-1-N8 还无 PSRAM |

## A.3 ESP32-S3 的 AI 指令集（向量指令）与框架支持 —— 官方原文

| 事实 | 官方原文 | 来源 |
|---|---|---|
| S3 有向量指令 | "ESP32-S3 has additional support for **vector instructions** in the MCU, which provides acceleration for neural network computing and signal processing workloads. Developers can take advantage of these vector instructions through **ESP-DSP and ESP-NN** libraries" | [Espressif ESP32-S3 产品页](https://www.espressif.com/en/products/socs/esp32-s3) |
| 指令集叫 **PIE** | "adding **128-bit SIMD vector instructions** to the Xtensa LX7 core (see the TRM Chapter **Processor Instruction Extensions (PIE)**)" | [Espressif Edge-AI Workshop](https://developer.espressif.com/workshops/edge-ai-with-esp32-s3/introduction/) |
| 加速比 | "128-bit SIMD vector instructions: hardware-accelerated INT8 neural network operations with **~18x speedup over unoptimized code**" | 同上 |
| 芯片分级 | ESP32-S3 = **PIE V1**；ESP32-P4 / ESP32-S31 = **PIE V2**；ESP32/C2/C3/C5/C6/S2 = **无 PIE**，算子全 C 实现，"significantly slower" | [esp-dl operator_support_state.md](https://raw.githubusercontent.com/espressif/esp-dl/master/operator_support_state.md) |
| 量化支持 | ESP-DL 支持 **w8a8 / w16a16 / w8a16 混合量化**；w8a16 自 ESP-DL v3.3.11 全面支持 | [esp-dl README](https://raw.githubusercontent.com/espressif/esp-dl/master/README.md) |
| 算子 | 已实现并测试 **64 个 ONNX 对齐算子**，推荐 opset 18 | [operator_support_state.md](https://raw.githubusercontent.com/espressif/esp-dl/master/operator_support_state.md) |
| 双核调度 | 自动双核调度，目前 **Conv2D 与 DepthwiseConv2D 支持双核** | [esp-dl README](https://raw.githubusercontent.com/espressif/esp-dl/master/README.md) |

> **工程结论**：ESP32-S3 的「AI 能力」本质是 **128-bit SIMD (PIE V1) + INT8 量化**，不是 NPU。它对 TFLite Micro / ESP-DL 的支持是真实的，但速度上限见 D 节——**这是「秒/帧」级别的硬件，不是「帧/秒」**。

---

# B. 摄像头方案

## B.1 ESP32-CAM 与 ESP32-S3-CAM

| 型号 | 关键参数 | 参考价格(¥) | 来源链接 | 备注 |
|---|---|---|---|---|
| **ESP32-CAM（安信可 Ai-Thinker，C277946）** | ESP32（LX6 双核，**非 S3**）+ OV2640 200万 | **¥45.76 起**（**库存 0**） | [立创商城](https://item.szlcsc.com/product/jpg_265266.html) | 页面参数栏「参数完善中」，**PSRAM 配置需下单前确认** |
| **Ai-Thinker ESP32-CAM WiFi BT BLE（C17333398）** | 含 2MP 摄像头套装 | **¥80.21 起**（**库存 0**） | [立创商城](https://item.szlcsc.com/product/jpg_18462560.html) | 同上，PSRAM 未标注 |
| 淘宝/拼多多/天猫 ESP32-CAM | — | **需询价确认** | — | item.taobao.com / world.taobao.com / detail.1688.com 全部登录墙；item.jd.com 反爬 |
| **乐鑫 ESP32-S3-EYE** | S3 + OV2640 + LCD + 麦克风 + IMU | **¥309.92 起**（库存 0） | [立创商城](https://item.szlcsc.com/product/jpg_6661850.html) | 见 A 节 |
| **Waveshare ESP32-S3-CAM（OV5640/OV3660 可选）** | 8MB PSRAM + 16MB Flash，可选 OV5640/OV3660/GC2145/GC0308，集成音频输入输出 | **US$16.99**（原价 $19.99）≈¥121 | [Waveshare 官网](https://www.waveshare.com/esp32-s3-cam-ov5640.htm) | 中文站被 WAF 拦截 |
| **Freenove ESP32-S3 CAM Board Kit（fnk0085）** | 8MB PSRAM，OV2640，含 1GB SD 卡 | **$19.99**（8MB Flash）/ **$21.99**（16MB）≈¥142 / ¥156 | [Freenove 官方店](https://store.freenove.com/products/fnk0085) | 教程完整，性价比高 |
| **Freenove Development Kit（fnk0086）** | 完整学习套件 | **$59.99** ≈¥426 | [Freenove 官方店](https://store.freenove.com/products/fnk0086) | — |
| DigiKey / Mouser 中国 | — | **需询价确认** | — | digikey.cn / mouser.cn 均 403 |

## B.2 OV2640 vs OV5640 在 ESP32 上的实际可用性（官方数据）

**① esp32-camera 官方支持表**（[README](https://raw.githubusercontent.com/espressif/esp32-camera/master/README.md)，仓库 **2785 ★**）：

| 传感器 | 最大分辨率 | 输出格式 | 靶面 |
|---|---|---|---|
| **OV2640** | 1600×1200（200万） | YUV(422/420)/YCbCr422、RGB565/555、8-bit 压缩、8/10-bit Raw | 1/4" |
| OV3660 | 2048×1536（300万） | raw RGB、RGB565/555/444、CCIR656、YCbCr422、压缩 | 1/5" |
| **OV5640** | 2592×1944（500万） | RAW RGB、RGB565/555/444、CCIR656、YUV422/420、YCbCr422、压缩 | 1/4" |

**② 官方硬约束（README 原文）**：
> "Except when using CIF or lower resolution with JPEG, the driver **requires PSRAM** to be installed and activated."
> → **无 PSRAM 时 JPEG 只能到 CIF（352×288）**。这是 PSRAM 成为硬门槛的官方依据。

**③ OV5640 自动对焦官方支持**（README「Autofocus (OV5640)」节）：esp32-camera 提供 `esp_camera_af.h`，需 menuconfig 打开 `Enable autofocus (OV5640)`；非 OV5640 返回 `ESP_ERR_NOT_SUPPORTED`；AF 依赖通过 SCCB 加载内部固件 blob → **必须是带 AF 马达的镜头模组才可用**。

**④ 乐鑫官方 Techpedia 的口径**（[DVP/MIPI-CSI 摄像头方案](https://docs.espressif.com/projects/esp-techpedia/zh_CN/latest/esp-friends/solution-introduction/camera/dvp-mipi-csi-camera-solution.html)）：
- JPEG sensor 建议最大 **不超过 500 万像素**；非 JPEG（YUV/RGB）**不超过 100 万像素**
- 超过 1024×720 尽量用支持 JPEG 的 sensor
- 官方实测：**ESP32-S3 + OV5640（DVP）JPEG 1600×1200 @ 25 fps**；720p MJPEG 网络流约 20 fps
- **ESP32-S3 没有硬件编解码**，靠 TinyJPEG 软件编码
- Sensor 初始化耗时：OV2640 JPEG 200ms / OV5640 JPEG 240ms / OV3660 JPEG 604ms
- ESP32-S3 的 CAM DVP 接口速率是 ESP32 的 **2~3 倍**

> **选型结论**：本项目 **OV2640 足够**。OV5640 只有搭配 AF 马达镜头模组才有额外价值（自动对焦），否则在 25fps + 软件编码约束下只剩分辨率优势，而 D 节会说明 ESP32-S3 根本处理不了 500 万像素的 AI 推理。

## B.3 水下相机方案

| 方案 | 关键参数 | 价格 | 来源链接 | 备注 |
|---|---|---|---|---|
| 威海至帆 ZF-USB-01A10 | **防水 100 米**，1080P，铝合金硬质氧化 | **面议（需询价）** | [中国制造网](https://cn.made-in-china.com/gongying/zhifankeji518-keuxvjLgnRld.html) | — |
| **Blue Robotics exploreHD（BR-103870）** | **耐压 400 米**，1080p USB，**标配仅 1 米线** + WetLink Penetrator | **$325.00** ≈¥2308 | [Blue Robotics](https://bluerobotics.com/store/sensors-cameras/cameras/deepwater-exploration-explorehd-usb-camera/) | 注意「400m 耐压」但「标配 1m 线」——线长才是实际约束 |
| **Charpie 水下开源视觉 AI 摄像机** | RPi Camera V2 NoIR / IMX219 8MP，以太网，12VDC 15W，**标配 2m 线可定制至 70m**，耐深 300m/1000m | **¥4,200–¥11,200** | [Charpie 官网](https://www.charpie.cn/product/rpi/) | 真正的「水下 AI 相机」价位锚点 |
| Charpie ROV 海峡 HX-300-B | 整套 ROV | **¥38,800–¥58,800** | 同上 | — |
| Charpie 360° 全景云台 / 30 倍变焦 / 双目 AI / 500m 便携 | — | **¥7,200–10,200 / ¥14,400–21,400 / ¥14,400–21,400 / ¥9,000–16,000** | 同上 | — |
| **DJI Osmo Action 5 Pro 标准套装** | 官方商城 | **¥2,098**（原价 ¥2,198） | [DJI 官方](https://www.dji.com/cn/osmo-action-5-pro) | 运动相机，非工业水下 |
| GoPro HERO13 Black 中国价 | — | **需询价确认** | — | gopro.com/zh/cn 商品页纯 JS 渲染，HTML 内无 price 字段 |
| 伴车安 探鱼器 TY121-30米 | 红外夜视，**不支持远程** | **¥855.40** | [苏宁易购](https://m.suning.com/itemcanshu/0000000000/000000012446746380.html) | 只能「偶尔看一眼」 |
| 伴车安 探鱼器 TY118-40米 | — | **¥596.70** | 同上 | — |
| 池王 可视锚竿全套 | 4.3" 屏 + 10000 轮 + 浑浊水高清 | **¥890** | [什么值得买](https://wiki.smzdm.com/p/w71wg7d/) | — |

### 浑水成像的关键事实（决定「能不能看见鱼」）

> 舟山网 2025-12-16 报道（[来源](https://www.wifizs.cn/zs/202512/t20251216_6535908.shtml)）：渊视科技总经理卢泽宇表示——**「传统水下相机在浊度约 30 NTU 的水域中，有效视距通常仅约 10 厘米」**；其 AI 去浑浊浑水相机把视距提升至 2 倍以上，**单台售价 10 万元**。

**其他硬限制**：
- **USB 2.0 最大电缆长度 5 米，且不建议用延长架**（[Oracle Solaris 文档引 usb.org FAQ](https://docs.oracle.com/cd/E19253-01/819-7062/devusbover-15/index.html)）
- DVP 是**板级并行信号**，物理上拉不长；整机厂长线一律改以太网/同轴
- 探鱼器「红外 LED 阵列补光」说法仅来自淘宝种草笔记（营销内容，低可信度）

---

# C. 定位 GPS 模块

## C.1 ATGM336H（中科微，国产）

| 型号 | 关键参数 | 参考价格(¥) | 来源链接 | 备注 |
|---|---|---|---|---|
| **ATGM336H-5N31**（C90770） | BDS+GPS（**无 GLONASS**）；UART+I2C；2.7–3.6V；**25mA@3.3V**；灵敏度 −148dBm；水平精度 **2.5m**；**冷启动 35s**；−40~+85℃ | **¥11.15**（库存 **11937**） | [立创商城](https://item.szlcsc.com/91958.html) | 页面原文：「支持精确秒脉冲输出，脉冲上升沿与时间对齐」「支持有源天线与无源天线」「支持 A-GNSS」。**是 SMD 贴片模块（10.1×9.7mm），非带天线 breakout** |
| **ATGM336H-5N71**（C2940946） | **GLONASS+BDS+GPS 三模**；UART；30mA@3.3V；2.5m；冷启动 32s | **¥15.45**（库存 89） | [立创商城](https://item.szlcsc.com/3308275.html) | 后缀 71 = 加 GLONASS，贵 ¥4.3 |
| **ATGM336H-6N-22**（C22381737） | **单北斗**，第六代 SOC **AT6668B**，北斗二号/三号 B1I+B1C；42mA@3.3V；精度 **2m**；**冷启动 23s**；50 通道；**最大 10Hz**；待机 <10µA | **¥13.57**（库存 922） | [立创商城](https://item.szlcsc.com/23918559.html) | 新一代，冷启动最快、精度最好，但**只收北斗** |
| ATGM336H-5N31（国际站） | 同 5N31 | **US$1.8312** | [LCSC 国际站](https://www.lcsc.com/product-detail/C90770.html) | 交叉验证 |

**AT6558R 芯片（模块的芯片基础）**：
- 「高性能 BDS/GNSS 多模卫星导航接收机 SOC 单芯片，片上集成射频前端、数字基带处理器、32 位 RISC CPU、电源管理」（[世强](https://www.sekorm.com/doc/1000692.html)）
- BDS/GPS 双模连续运行 **~23mA@3.3V**，待机 **~8µA**，RTC/备份电源可低至 1.4V，**有源天线检测与保护**（[世强](https://www.sekorm.com/pnPs/579742842.html)）
- ⚠️ **坑**：市售 ATGM336H 实测自报 `IC=AT6558F-5N-32-1C580900`（**是 AT6558F 不是 AT6558R**）。中科微同时有 AT6558R/F/RS/AT6668B 多个变体，**以立创页面「GNSS类型」为准**（[来源](https://nthpulse.net/writings/gps_receiver_notes/)）

## C.2 u-blox NEO-6M / NEO-M8N

### ⚠️ 官方生命周期状态（本次最重要的采购结论）

| 型号 | 官方状态 | 原文 | 来源 |
|---|---|---|---|
| **NEO-6G / NEO-6M / NEO-6Q** | **EOL（停产）** | "The NEO-6M GPS module with crystal and ROM has reached **End-of-Life**." / "**This product is no longer available**" | [u-blox NEO-6 系列](https://www.u-blox.com/en/product/neo-6-series) |
| **NEO-M8N-0** | **NRND（不推荐新设计）** | 产品变体表标注 NRND，官方建议替代 `NEO-M8M-0` | [u-blox NEO-M8 系列](https://www.u-blox.com/en/product/neo-m8-series) |
| **NEO-M8M-0** | 官方推荐 | "For new designs, we recommend: NEO-M8M-0" | 同上 |

**NEO-M8 相对 NEO-6 的官方改进**：并发接收最多 **3 个 GNSS**（GPS/Galileo/GLONASS/BeiDou）；导航灵敏度 **−167 dBm**（NEO-6 为 −161 dBm 级）；**高级干扰与欺骗检测**；向下兼容 NEO-7/NEO-6；NEO-M8N 为 TCXO+SAW+LNA 版，NEO-M8M 为 ROM+crystal 版（无 SAW/LNA、无数据记录、无 Flash）。

| 型号 | 关键参数 | 参考价格(¥) | 来源链接 | 备注 |
|---|---|---|---|---|
| **NEO-M8N-0**（C6330769） | Galileo+GLONASS+GPS+BeiDou；UART/I2C/USB/SPI；−167dBm | **¥362.70**（库存仅 **17**） | [立创商城](https://item.szlcsc.com/7278948.html) | 芯片级模块立创现货价，库存极低，偏高 |
| GY-NEO6MV2 / GY-GPS6MV2 breakout | NEO-6M + 陶瓷天线 + EEPROM | **¥18**（**C/D 级线索**） | 原页未打开 | 仅量级参考。NEO-6M 已 EOL，此价位几乎必然是拆机/仿冒件 |
| NEO-M8N breakout（淘宝） | — | **需询价确认** | — | 淘宝登录墙；京东搜索页纯 JS |

### 假货/翻新辨别（本次证据最扎实的部分）

**证据 1：AT6558 冒充 u-blox NEO-6M（拆解级证据）** — [jgohyeah.github.io](https://jgohyeah.github.io/electronics/2026/01/16/counterfeit-gps.html)（2026-01-16）

| 判据 | 具体内容 |
|---|---|
| 结论 | 网购「u-blox NEO-6M breakout」实测 "were in fact counterfeits **based on the AT6558 chip with a u-blox label stuck on**" |
| **特征故障** | "the modules would only start up and send data out their serial ports **with the antenna disconnected**. With the antenna attached, the module would enter a reset state"——**接天线就复位** |
| 根因 | breakout 把 pin 8 (NC) 与 pin 9 (VCC_RF) 短接（符合 NEO-6M 手册）；但 AT6558 要求 pin 8 悬空。天线放大器负载拉低 pin 9 → 连带拉低 pin 8 → 模块被钉在复位态 |
| 修复后缺陷 | **完全无法通过串口配置**：锁死 1Hz、9600 波特率、默认无过滤 NMEA |
| 作者结论 | "**Do not use this in mission critical applications!!!**" |

**证据 2：u-center 报文级辨别法（可直接照做）** — [nthpulse.net](https://nthpulse.net/writings/gps_receiver_notes/)（2025-04-08）

| 判据 | 假货 GY-NEO6MV2 | 正品 NEO-6M |
|---|---|---|
| **最关键：报文前缀** | **`$GNTXT`** | `$GPTXT` |
| 开机报文 | 只有两条且**无厂商标识** | `$GPTXT,01,01,02,u-blox ag - www.u-blox.com*50`<br>`$GPTXT,01,01,02,HW UBX-G60xx 00040007 FF7FFFFFp*53`<br>`$GPTXT,01,01,02,ROM CORE 6.02 (36023) Oct 15 2009 16:52:08*56` |
| 配置响应 | "**no response to any config message sent to them**" | u-center 改波特率/报文/PPS **立即生效** |
| PPS 引脚 | **排针上无 PPS** | 有 PPS |
| 回收件识别 | — | "the chip on the NEO-6M module was **relabelled, with a new label placed over the original**, and that the metal shielding is aged" |

**证据 3**：u-blox 官方论坛帖存在但正文不可读（Salesforce SPA，JS 渲染）——[PSA: fake u-blox modules](https://portal.u-blox.com/s/question/0D52p00008HKEEECA5/psa-fake-ublox-modules-and-potential-ways-to-identify-them)、[real u-blox or fake chinese?](https://portal.u-blox.com/s/question/0D52p00008HKmpICAT/real-ublox-or-fake-chinese-)。**仅能证明帖子存在，正文未读取**。

## C.3 和芯星通 UM980 与低成本 RTK

| 型号 | 关键参数 | 参考价格(¥) | 来源链接 | 备注 |
|---|---|---|---|---|
| **和芯星通 UM980** | BDS/GPS/GLONASS/Galileo/QZSS **全系统全频** RTK | **需询价确认** | [和芯星通官网](https://www.unicorecomm.com/products/detail/27) | 官网只列规格不公开价格；立创无此型号；淘宝需登录 |
| UM980 评估板（UM980eb） | 官方 EVK | **需询价确认** | 同上 | 同类还有 HPL EVK 5.0 KIT、UM981eb、UM982eb、UM960eb、UT986eb |
| **UM982 模块** | 双天线 RTK 定位+定向 | **需询价确认** | [和芯星通 UM982](https://www.unicorecomm.com/products/detail/26) | 同样不公开价格 |
| ATK-UM982（正点原子） | 双天线定位定向 | **需询价确认** | — | 未抓到价格页 |
| **u-blox ZED-F9P-04B**（C5120257） | 全星座；−167dBm；冷启动 25s；**85mA@3V** | **¥519.24**（库存 **188**） | [立创商城](https://item.szlcsc.com/5705597.html) | **A 级：裸模块立创现货价，本价位段最可信报价** |
| u-blox ZED-F9P-15B（C20626405） | 同上 | **¥1173.00**（库存仅 1） | [立创商城](https://item.szlcsc.com/22035756.html) | 零星现货，不具代表性 |
| Waveshare ZED-F9P GPS-RTK HAT | 树莓派扩展板，厘米级 | **US$239.99** ≈¥1704 | [Waveshare](https://www.waveshare.com/zed-f9p-gps-rtk-hat.htm) | 整板成品价 |
| **Quectel LC29H EA 版**（C28453488） | 全星座；**16mA@3.3V**；−165dBm；冷启动 29s | **¥165.42**（库存仅 14） | [立创商城](https://item.szlcsc.com/30184217.html) | — |
| **Quectel LC29H BS 版**（C21385845） | UART/SPI/I2C；23mA；−165dBm | **¥55.00**（库存仅 8） | [立创商城](https://item.szlcsc.com/22805586.html) | 低成本单频版。⚠️ EA/DA/BA/AA 版本差异**未核实** |
| **DFRobot GNSS-RTK 套件（4G CORS 版）** | 成品 RTK 移动站，走 4G 连 CORS | **¥799.00** | [DFRobot](https://www.dfrobot.com.cn/goods-4254.html) | **可直接对比的成品系统价** |
| **DFRobot GNSS-RTK 套件（基站+移动站 LoRa 版）** | 自建基站 + 移动站，用移远 LC29H | **¥1200.00** | [DFRobot](https://www.dfrobot.com.cn/goods-4180.html) | **无需 CORS 账号**，适合无网/无 CORS 覆盖的鱼塘 |

**RTK 的配套成本（关键）**：

| 配套 | 价格 | 来源 |
|---|---|---|
| **千寻位置「千寻知寸」CORS 账号（厘米级）** | **400 元/月；3600 元/年**；免费试用 1 天 | [千寻位置代理商页面](http://m.csqlch.com/News_Show.php?theId=712)（B 级） |

> **结论性事实**：RTK 成本大头**不是模块而是差分源**。千寻 CORS 一年 3600 元 ≈ **7 个 ZED-F9P 裸模块**（¥519）。

## C.4 户外防雷/浪涌配套（鱼塘必备）

| 型号 | 关键参数 | 参考价格(¥) | 来源链接 | 备注 |
|---|---|---|---|---|
| **沃盾 OD-TK-SMA 天馈信号避雷器** | SMA 接口，内置**可更换放电管**；IP20；接地电阻 ≤4Ω；−40~+70℃ | **¥198.00**（1–9 件）<br>**¥185.00**（≥10 件） | [供应商网](https://sz2001.gys.cn/supply/4811350430.html) | B 级，「价格为商家提供的参考价」 |
| **沃盾 OD-DGX-24mA 信号防雷器** | 4–20mA / RS485 链路 | **¥225.00** | 同上 | — |
| **单相 220V 防雷箱 OD-D40KA** | 带雷击计数器 + 劣化窗口 | **¥180.00** | 同上 | 塘口配电箱进线 |
| DEHN DG MOD 385 | 德国进口可插拔 | **¥1220.00** | 同上 | 养殖场景性价比低 |
| TNC-JK 纯铜天馈防雷器 | TNC 接口，GPS/北斗授时防雷 | **¥38**（**C 级线索**） | [淘宝数码网文章](https://shuma.taobao.com/topic/qitapeijian_9/72618f241cc90d6d532390e4bd8a45f2) | ⚠️ 内容营销文章，参数无法核实 |

## C.5 工程判断：固定塘口场景 GPS 是否必要？

### 事实（附来源）

| # | 事实 | 来源 |
|---|---|---|
| F1 | u-blox 官方将 NEO-6 全系标为 **EOL**、NEO-M8N-0 标为 **NRND** | [neo-6](https://www.u-blox.com/en/product/neo-6-series)、[neo-m8](https://www.u-blox.com/en/product/neo-m8-series) |
| F2 | ¥18 价位 GY-NEO6MV2 被**广泛仿冒**，假货对配置报文无响应、无 PPS 引脚 | [nthpulse.net](https://nthpulse.net/writings/gps_receiver_notes/)、[jgohyeah](https://jgohyeah.github.io/electronics/2026/01/16/counterfeit-gps.html) |
| F3 | ATGM336H 模块级价格低至 **¥11.15**（立创现货，库存 11937），支持精确秒脉冲输出 | [立创](https://item.szlcsc.com/91958.html) |
| F4 | DFRobot 在售「GNSS 北斗授时&定位模块」**¥149**、普通 GNSS 定位模块 **¥120** | [goods-3899](https://www.dfrobot.com.cn/goods-3899.html)、[goods-3652](https://www.dfrobot.com.cn/goods-3652.html) |
| F5 | 千寻知寸厘米级 CORS 差分 **400 元/月、3600 元/年** | [代理商页面](http://m.csqlch.com/News_Show.php?theId=712) |
| F6 | AT6558R 待机 ~8µA、RTC 备电可低至 1.4V、有源天线检测与保护 | [世强](https://www.sekorm.com/pnPs/579742842.html) |

### 工程推断（明确标注：以下是分析，不是检索结论）

**（1）固定式塘口监测站：GPS 的真实价值排序**

| 用途 | 价值 | 判断 |
|---|---|---|
| **时间同步（1PPS 授时）** | 中低 | 有 4G/WiFi 时 **NTP 完全够用**（溶氧/温度/pH 是分钟级采样）。GPS 授时的边际价值只在**断网自主守时**和**多站点严格同刻采样**时体现。1PPS 的纳秒精度对养鱼毫无意义 |
| **防盗/位移告警** | **中高** | 固定站被移动/被盗是真实风险（太阳能板、电池、ESP32 都有残值）。**¥11 的 ATGM336H 就能提供这个能力，是最划算的 GPS 用途**：坐标偏移 >N 米即告警 |
| **多塘口资产台账** | 中 | 安装时自动记录坐标，免手工录入和录错。但预置坐标也能做到，边际收益低 |
| **替代方案** | — | **预置坐标 + NTP + RTC（如 DS3231）兜底**，零 BOM 增量。WiFi 定位在中国农村鱼塘**基本不可用**（无指纹库覆盖） |

**（2）分场景建议**

| 场景 | 建议 | 理由 |
|---|---|---|
| **固定塘口（有 4G/WiFi）** | **不装 GPS**，用 NTP + RTC | 省 ¥11–15/站，省一根天线、一个防雷器、一条馈线，减少一个户外故障点 |
| **固定塘口（无网、纯 LoRa 自组网）** | **装 ATGM336H**（¥11.15） | 此时 GPS 是唯一可得时间源，LoRa 网关也常需 GPS 授时对齐时隙。**这是 GPS 最不可替代的场景** |
| **有防盗顾虑的站点** | **装 ATGM336H** | ¥11 买一个位移告警能力 |
| **增氧机船 / 投饵船（移动设备）** | **必须装 GPS** | 需要位置反馈做返航、路径跟踪、防丢失。ATGM336H-5N71（¥15.45）或 6N-22（¥13.57）即可；自动循迹才考虑 RTK（¥799 起） |
| **水下机器人** | **GPS 无效，需换方案** | GPS L 波段在水下急剧衰减。需改惯性导航（IMU）、DVL、声学定位或视觉/激光 SLAM。**本次未检索到可引用的量化衰减数据，此条为工程常识推断** |

**（3）户外雷击风险 —— 本次调研中我认为最被低估的风险点**

- **风险机制（推断）**：GPS 有源天线装在立杆顶端，馈线拉 3–10m 到地面机箱。这条馈线是**把雷击浪涌直接引进 ESP32 的现成通道**；若天线放大器由模块 VCC_RF 供电（ATGM336H 支持有源天线），雷击还会顺电源轨打穿模块。鱼塘周边开阔水面 + 空旷，是雷击高发环境。
- **建议做法（推断）**：
  1. 天线馈线加装**同轴防雷器**（SMA/TNC，GDT 式）并**可靠接地**——¥185–198 级即可
  2. 电源进线加防雷（OD-D40KA ¥180，带雷击计数器，便于事后判断）
  3. RS485/网口加信号防雷（OD-DGX-24mA ¥225）
  4. **等电位接地**：防雷器外壳必须通过金属支架接到机柜地，**悬空安装时屏蔽层反而变成接收天线**
- **更省事的替代思路（推断）**：若只为防盗和时间，**GPS 模块直接装在机箱内、顶部开窗贴陶瓷天线**，彻底取消长馈线就不需要天馈防雷器。代价是金属机箱屏蔽导致精度下降。**这个取舍值得实测验证。**
- ⚠️ **未完成**：未检索到 GB 50057《建筑物防雷设计规范》条款原文，也未找到养殖场雷击风险统计数据。

> **一句话**：固定塘口用 **ATGM336H-5N31（¥11.15，立创现货 11937）** 做防盗位移告警 + 断网授时即可。**不要碰 ¥10–20 的「NEO-6M」**（官方已 EOL，市面几乎全是 AT6558 冒充或拆机件，假货完全无法用 u-center 配置）。RTK 对鱼塘是过度设计，且真正成本在千寻 CORS 年费 ¥3600。**最该花钱的地方是防雷。**

---

# D. ESP32 边缘 AI 的真实能力边界（实证）

## D.1 ESP32-S3 跑目标检测的官方实测数据

### ① ESP-DL 官方 COCO 检测模型 benchmark —— 最硬的数据

来源：[esp-dl models/coco_detect/README.md](https://raw.githubusercontent.com/espressif/esp-dl/master/models/coco_detect/README.md)（仓库 **1141 ★**）

| 模型 | 芯片 | 输入 | Flash | PSRAM | 预处理(ms) | **模型推理(ms)** | 后处理(ms) | **合计(ms)** | **推算 FPS** | mAP50-95 |
|---|---|---|---|---|---|---|---|---|---|---|
| yolo11n_s8_v1 | **ESP32-S3** | 640×640 | 8MB | 8MB | 51.5 | **26014.2** | 58.9 | **26124.6** | **0.038** | 0.370 |
| yolo11n_s8_v1 | ESP32-P4 | 640×640 | 16MB | 32MB | 16.0 | 2535.3 | 14.3 | 2565.6 | 0.39 | 0.373 |
| yolo11n_320_s8_v1 | **ESP32-S3** | 320×320 | 8MB | 8MB | 15.2 | **6161.8** | 19.3 | **6196.3** | **0.16** | 0.276 |
| yolo11n_320_s8_v1 | ESP32-P4 | 320×320 | 16MB | 32MB | 5.2 | 550.1 | 5.3 | 560.6 | 1.78 | 0.278 |

> **直接回答「ESP32-S3 @240MHz + 8MB PSRAM 能跑多大模型？多少 FPS？」**
> **能跑 YOLO11n，但速度是 0.038–0.16 FPS，即 6–26 秒一帧。**这不是「慢」，是**不可用**。
> **官方硬约束**：YOLO11n 内存管理器占 6MB + 参数近 3MB，**PSRAM < 16MB 时模型必须放 FLASH**——8MB PSRAM 版跑不动常规加载方式。

### ② esp-detection（乐鑫官方 YOLOv11，[仓库 160 ★](https://github.com/espressif/esp-detection)，创建 2025-04-29）

来源：[esp-detection README](https://raw.githubusercontent.com/espressif/esp-detection/main/README.md)

| 模型 | 输入 | 参数量 | ESP32-P4(ms) | **ESP32-S3(ms)** | **S3 FPS** | mAP50-95 |
|---|---|---|---|---|---|---|
| espdet_pico_224_224_cat | 224×224 | **0.36M** | 51.4 | **126.2** | **7.9** | 69.9 |
| espdet_pico_416_416_cat | 416×416 | 0.36M | 201.7 | 449.5 | 2.2 | 76.6 |
| espdet_pico_160_288_cat | 160×288 | 0.36M | 45.9 | 115.5 | 8.7 | 71.2 |

README 原文："espdet_pico achieves **>18 FPS on ESP32-P4 and >7 FPS on ESP32-S3** when the input size is 224*224"——与表格交叉验证一致 ✓。
对比：**YOLOv11n 是 2.6M 参数 / 640 输入，espdet_pico 是 0.36M 参数 / 224 输入，差 7 倍参数量、8 倍像素量。**

> ⚠️ **重要更正**：`JorgeSan88/esp-detection`（搜索容易命中的那个）经 GitHub API 验证是 **espressif/esp-detection 的 fork，star = 0**。数据应归因上游官方仓库。

### ③ 人脸 / 行人 / 分类 —— ESP32-S3 真正「能用」的区间

来源：[esp-dl human_face_detect/README.md](https://raw.githubusercontent.com/espressif/esp-dl/master/models/human_face_detect/README.md) + [Espressif Edge-AI Workshop](https://developer.espressif.com/workshops/edge-ai-with-esp32-s3/)

| 模型 | 芯片 | 输入 | 预处理 | 模型(ms) | 后处理 | 合计(ms) | **FPS** | mAP50-95 |
|---|---|---|---|---|---|---|---|---|
| **msr_s8_v1（人脸粗定位）** | **S3** | 120×160 | 3.8 | 33.1 | 0.3 | **37.2** | **26.9** | — |
| msr_s8_v1 | P4 | 120×160 | 1.3 | 13.1 | 0.1 | 14.5 | 69.0 | — |
| mnp_s8_v1（人脸关键点） | S3 | 48×48 | 0.6 | 5.8 | 0.1 | 6.5 | 153.8 | 0.367 |
| espdet_pico_224_224_face | **S3** | 224×224 | 7.2 | 131.6 | 0.8 | **139.6** | **7.2** | 0.504 |
| espdet_pico_416_416_face | S3 | 416×416 | 21.8 | 437.0 | 1.3 | 460.1 | 2.2 | 0.598 |
| espdet_pico_224_224_face | P4 | 224×224 | 2.4 | 49.6 | 0.4 | 52.4 | 19.1 | 0.504 |
| **行人 pico_s8_v1** | **S3** | 224×224 | 9.2 | 118.3 | 2.4 | **129.9** | **7.7** | — |
| 行人 pico_s8_v1 | P4 | 224×224 | 3.5 | 55.6 | 1.4 | 60.5 | 16.5 | — |
| **MobileNetV2 分类（双核）** | **S3** | 224×224 | 8.5 | **867.0** | 1.1 | **876.6** | **1.14** | Prec@1 70.543 |
| MobileNetV2 分类（单核） | S3 | 224×224 | 8.5 | 1309.5 | 1.1 | 1319.1 | 0.76 | 70.543 |

> **最重要的边界数字**：连 MobileNetV2 这种轻量分类网，ESP32-S3 双核也要 **867 ms/帧（≈1.1 FPS）**。这直接否定了「端侧鱼种多分类」的可行性。

官方 workshop 原文："MSR takes ~33ms... MNP adds only ~6ms per candidate... **total ~37–40 ms per frame**"，全部 8-bit 量化、纯 CPU 跑。

### ④ ESP32-P4 对比（同模型加速比）

| 模型 | S3(ms) | P4(ms) | 加速比 |
|---|---|---|---|
| 人脸 MSR | 33.1 | 13.1 | 2.5× |
| MobileNetV2 | 1309.5 | 326.6 | 4.0× |
| **YOLO11n@320** | 6161.8 | 550.1 | **11.2×** |
| YOLO26n@640 | 13107 | 3474 | 3.8× |

Espressif 官方口径：P4 "delivers roughly **2.7-3x faster inference** than the ESP32-S3 for typical vision models"（[来源](https://developer.espressif.com/workshops/edge-ai-with-esp32-s3/introduction/)）。
**P4 把「不可用」变成「勉强可用」，但仍不是实时视频。**

### ⑤ YOLO26（更新一代，NMS-Free）

来源：[esp-dl models/yolo26/README.md](https://raw.githubusercontent.com/espressif/esp-dl/master/models/yolo26/README.md)

| 模型 | 芯片 | 输入 | Flash | PSRAM | 合计(ms) | **FPS** | mAP50-95 |
|---|---|---|---|---|---|---|---|
| yolo26n_512_s8_s3 | **ESP32-S3** | 512×512 | 16MB | **16MB** | 7879.0 | **0.13** | 0.363 |
| yolo26n_640_s8_s3 | **ESP32-S3** | 640×640 | 16MB | **16MB** | 13194.0 | **0.076** | 0.384 |
| yolo26n_512_s8_p4 | ESP32-P4 | 512×512 | 16MB | 32MB | 2092.0 | 0.48 | 0.365 |
| yolo26n_640_s8_p4 | ESP32-P4 | 640×640 | 16MB | 32MB | 3512.0 | 0.28 | 0.387 |

- **ESP32-S3 版官方标 PSRAM 需求 16MB**——已超出 ESP32-S3 的 8MB PSRAM 上限，实际上 S3 跑 yolo26n 必须全部走 FLASH
- 组件 [espressif/yolo26](https://components.espressif.com/components/espressif/yolo26)：v0.1.0（2026-04-15 创建），描述为 "Universal YOLO26 Processor for **ESP32-P4** (NMS-Free)"，**下载量仅 103**

### ⑥ 第三方独立实测佐证

| 来源 | 配置 | 实测结果 |
|---|---|---|
| **MDPI Sensors 2025, 25(6):1656**（[DOI](https://doi.org/10.3390/s25061656)） | ESP32-CAM（**原版 ESP32，非 S3**）+ MobileNet **v1** TFLite @96×96，**二分类** person/non-person | 完整环路 @320×240 本地 broker **459±80 ms**；640×480 JPEG 发国际 broker **+5815 ms（6.55×）**。原文错误归因 "limited computational power"。20 样本验证 19/20 |
| [Edge Impulse 论坛](https://forum.edgeimpulse.com/t/use-psram-for-impulse-deployment-on-esp32-s3/12849) | ESP32-S3 量化二分类，串口原文 | **"DSP 5 ms, inference 675 ms"**（输入分辨率未验证）。官方人员确认 S3 用优化 kernel，arena 需求与常规 benchmark 不同 |

## D.2 有没有人真的在 ESP32 上做鱼类检测/识别？—— **未找到可靠实证**

**GitHub API 全量搜索**（实测 total_count）：

| 搜索 query | total_count | 最高 star |
|---|---|---|
| `fish+detection+esp32` | **5** | **0** |
| `fish+detection+tinyml` | **0** | — |
| `fish+detector+microcontroller` | **0** | — |
| `fish+classification+esp32` | 2 | 1 |
| `fish+species+identification+edge` | 2 | 0 |
| `fish+esp32cam` | 3 | 3（喂食器，无 AI） |
| `fish+recognition+embedded` | 1 | 0（猫狗分类，不相关） |
| `aquaculture+esp32` | 45 | 29（纯传感器，无视觉 AI） |

| 项目 | 推理位置 | Star | 实测精度 | 关键实证 |
|---|---|---|---|---|
| [EduardoLawson1/Fish-Detection-with-Esp32Cam](https://github.com/EduardoLawson1/Fish-Detection-with-Esp32Cam) | **矛盾/存疑** | **0** | **无** | .ino 确含 Edge Impulse 端侧 SDK（FOMO MobileNetV2 0.1），**但 README 明写** "send them to the Edge Impulse platform for fish detection" —— 自相矛盾。仅 3 个文件，无精度/数据集/FPS |
| [IT21179280/SMART-FISH-TANK-MONITORING-SYSTEM](https://github.com/IT21179280/SMART-FISH-TANK-MONITORING-SYSTEM) | **PC/云端** | **0** | **无** | 仓库仅 README + 一个 zip，**无源码**；技术栈明写 "Python – Model training, **inference** & backend processing" + YOLOv8。**ESP32-CAM 只做采集推流**。全文无 mAP/准确率/帧率 |
| [Alwyn2006/SMART-FISH-AQUARIUM](https://github.com/Alwyn2006/SMART-FISH-AQUARIUM) | **声称端侧，实无实现** | **2** | **无** | README 大肆宣称 "CNN-LSTM"、"locally on ESP32-CAM"，**但文件树只有 React/Vite 网页**（App.jsx/package.json），**零固件零模型** |
| guaima007/fisheries-monitor | **PC/云端** | 2 | 无 | YOLOv8 在 PC 端（code24_yolov8/UI.py、vision_stream_server.py）；ESP32-S3 只做传感/继电器/LVGL |
| davidRT2/FishSorter | **云端（明确）** | 1 | 无 | README 原文：Flask API 加载 .h5 模型 |
| deepintersection/smart-aquarium | **云端（明确）** | 1 | 无 | "Connects to a local **n8n AI server**"；三层架构全标 "(coming soon)" |
| ilan2002/Aquaculture_monitoring_using_Machinelearning_ESP32 | 未验证 | 6 | 无 | README 仅一句描述，无技术细节 |

**学术侧**：唯一近似工作是 *Real-time rapid visual fish disease detection system based on tiny machine learning*（[DOI 10.1007/s10499-025-02256-6](https://doi.org/10.1007/s10499-025-02256-6)，Aquaculture International 2025, 33(6):584），硬件是 **RISC-V 微控制器（不是 ESP32）**，且做的是**鱼病检测而非种类识别**，mAP50-95 = **0.736**。

**真正做鱼类检测的系统用什么硬件**（说明「鱼类检测」本身在 MCU 上就极难）：

| 论文 | 硬件 | 精度 | DOI |
|---|---|---|---|
| Real-time rapid visual fish disease detection based on TinyML | **RISC-V MCU（非 ESP32）** | mAP50-95 = **0.736** | [10.1007/s10499-025-02256-6](https://doi.org/10.1007/s10499-025-02256-6) |
| Real-Time Underwater Fish Detection (CBAM-YOLO) | 未取到（MDPI 403） | 未取到 | [10.3390/jmse12081302](https://doi.org/10.3390/jmse12081302) |
| Fish Species Detection and Tracking (Optical Flow) | 未取到 | 未取到 | [10.1109/icecaa55415.2022.9936540](https://doi.org/10.1109/icecaa55415.2022.9936540) |
| Fish species classification in unconstrained underwater environments | 未取到 | 未取到 | [10.1002/lom3.10113](https://doi.org/10.1002/lom3.10113) |
| Optimizing Edge-AI on the ESP32-S3 Using SIMD | ESP32-S3 | **仅摘要，无实测数字**（付费墙） | [10.1109/IPCCC66453.2025.11304640](https://doi.org/10.1109/IPCCC66453.2025.11304640) |
| The systematic design and implementation of a vertical fish farm based on ESP32-P4 | ESP32-P4 | **未取到**（付费墙） | [10.1109/icma69663.2026.11647118](https://doi.org/10.1109/icma69663.2026.11647118) |

> ## ❗ D.2 结论：**未找到可靠实证**
> **没有任何可验证的项目或论文，实证了「ESP32/ESP32-S3 端侧完成鱼类检测或种类识别，并给出实测精度与帧率」。**
> 现有「ESP32 鱼类识别」项目要么 star = 0、要么只做采集推流而推理在 PC/云端、要么只有 README 没有固件。
> 尝试过但失败的检索途径：Edge Impulse 项目页（JS 渲染）、Hackster.io（Cloudflare 403）、arXiv "fish detection" + ESP32（无返回）、IEEE Xplore（付费墙）。

## D.3 ESP32 做鱼类投喂/水质 AI 的实际案例

**最重要论文**：*Machine Learning on Low-Cost Edge Devices for Real-Time Water Quality Prediction in Tilapia Aquaculture*，Sensors 2025, 25(19):6159，[DOI 10.3390/s25196159](https://doi.org/10.3390/s25196159)｜[PMC 全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC12526668/)

- **真·ESP32 端侧推理**，但用的是 **MLR / DTR / RFR 经典机器学习，不是神经网络**
- RFR 精度最高（**R² > 0.80**），但最终选 **MLR** 部署（R² ≈ 0.65–0.72），理由是计算效率与离线可用性
- 系统集成感知 + 预测 + 执行，**断网也能自主调节溶解氧与 pH**；现场验证能在 1 小时内稳定 pH
- 原文自述："**none of the reviewed works show predictive ML deployment directly on ultra-low-cost microcontrollers such as ESP32 for aquaculture**"

| 论文 | 芯片角色 | 指标 |
|---|---|---|
| s25196159 Tilapia（[DOI](https://doi.org/10.3390/s25196159)） | **端侧（经典 ML）** | RFR R²>0.80；MLR R²≈0.65–0.72 |
| s26134242 DO 预测 | **仅采集，云端推理** | 30min MAE 0.783 mg/L、方向准确率 60.23%；6h 1.109、53.82%。**原文自述「仅比 persistence 基线略好」「不构成稳健预测有效性」** |
| s26103238 Koi LSTM | 云端 | DO R²=0.97、氨氮 0.94；能耗 −26.86% |
| s25196107 Aquaponics | 未明确 | RF 99% / NN 98% / SVM 97% / LDA 82% |

**投喂开源项目**：star 最高的 [yyq8548/Smart-fish-feeder-digital-control](https://github.com/yyq8548/Smart-fish-feeder-digital-control)（**62 ★**）**完全无 AI/视觉**；itohio/FishFeeder 23 ★（TinyGo 喂食器）；其余均 ≤5 ★，全部是「定时器 + 舵机 + Blynk/MQTT」。**无一是视觉驱动投喂。**

> **结论**：ESP32 在水产中的主流角色是**传感器节点 + 执行器，AI 在云端**。

## D.4 工程结论：ESP32-S3 该做什么、不该做什么

| ✅ 能做（有官方实测支撑） | ❌ 不该做（有实测反证） |
|---|---|
| 人员入侵检测（224×224，**7.7 FPS**） | ❌ YOLOv5n / v8n / 11n COCO 检测（**6.2–26 秒/帧**） |
| 人脸检测与识别（37–40ms，**≈25 FPS**） | ❌ **鱼类种类识别**（GitHub 零实证 + MobileNetV2 分类也只有 1.14 FPS） |
| 水面异常物单类检测（224×224，**7.9 FPS**） | ❌ LSTM / GRU 水质时序预测（算力不够） |
| 端侧二分类预筛 + 云端重推理（459ms 环路，论文验证） | ❌ 依赖云端 AI 的实时性（+5815ms） |
| 水质**经典 ML** 数值预测（MLR，R²≈0.65–0.72，论文验证） | ❌ 相信「CNN-LSTM 端侧」类宣传（无实证） |
| 本地闭环控制（断网可用，论文验证） | ❌ 把 ESP32-CAM（原版 LX6）与 ESP32-S3 混为一谈（鱼类项目绝大多数用 ESP32-CAM） |

**建议架构**：
> **ESP32-S3 只做低分辨率（≤320×320）单类检测 / 二分类预筛与触发抓拍**；鱼种识别、LSTM 时序预测、大模型诊断放**网关（树莓派 / Jetson）或云端**；水质用**经典 ML**；**保留本地闭环控制以应对断网**。

---

# E. 开源参考项目（GitHub，star 数已用 GitHub API 实测）

> 所有 star 数于本次调研时通过 `api.github.com/repos/...` 实测，非凭印象。

## E.1 直接可参考的鱼塘/水质项目

| 项目 | Star | 创建 / 最后更新 | 内容 | 链接 |
|---|---|---|---|---|
| **mzakharo/tubby** | **117 ★** | 2023-02-12 / 2025-05-03 | Hot Tub & Pool Water Quality Sensor — ESP32 水质传感（温度/pH/ORP），**本项目最接近的工程参考** | https://github.com/mzakharo/tubby |
| **yyq8548/Smart-fish-feeder-digital-control** | **62 ★** | 2026-07-02 / 2026-08-02 | ESP32 智能投喂数字控制板：浏览器↔物理喂食器，实时遥测、远程投喂、泵清洗、冷却控制、告警、**MQTT 安全命令跟踪**。**无视觉/AI** | https://github.com/yyq8548/Smart-fish-feeder-digital-control |
| **pkErbynn/IoT-WQMS** | **29 ★** | 2019-03-18 / 2023-07-21 | 面向**养鱼户**的水质监测与告警系统，测理化参数 | https://github.com/pkErbynn/IoT-WQMS |
| pcboy/hydroponics-controller | 21 ★ | 2020-04-10 / 2020-08-20 | ESP32 + 继电器 + 水泵 + TDS 传感器（水培，逻辑可迁移） | https://github.com/pcboy/hydroponics-controller |
| ilan2002/Aquaculture_monitoring_using_Machinelearning_ESP32 | 6 ★ | 2023-07-26 / 2025-04-04 | 水产养殖监测 + 机器学习，避免鱼群死亡 | https://github.com/ilan2002/Aquaculture_monitoring_using_Machinelearning_ESP32 |
| caseyWebb/mayfly | 5 ★ | — / 2023-06-02 | ESP32 水产与水文环境监测 | https://github.com/caseyWebb/mayfly |
| ALNezar/FishMaster | 8 ★ | — | ESP32 + MQTT + Spring Boot + PostgreSQL + React 水族监测 | https://github.com/ALNezar/FishMaster |

## E.2 边缘 AI / 摄像头框架（必读）

| 项目 | Star | 说明 | 链接 |
|---|---|---|---|
| **espressif/esp32-camera** | **2785 ★** | 官方摄像头驱动，OV2640/OV3660/OV5640 支持表与 PSRAM 约束的权威来源。最后更新 2026-09-14 | https://github.com/espressif/esp32-camera |
| **espressif/esp-who** | **2144 ★** | 人脸检测/识别/行人检测框架，支持 ESP32-S3-EYE 与 ESP32-P4 | https://github.com/espressif/esp-who |
| **espressif/esp-dl** | **1141 ★** | 深度学习推理库，PIE SIMD 加速、w8a8/w16a16/w8a16 混合量化、64 个算子。**D 节所有帧率数据的来源** | https://github.com/espressif/esp-dl |
| **espressif/esp-detection** | **160 ★** | 官方轻量目标检测（基于 Ultralytics YOLOv11），espdet_pico 0.36M 参数，S3 @224×224 = 7.9 FPS | https://github.com/espressif/esp-detection |
| alankrantas/edge-impulse-esp32-cam-image-classification | 64 ★ | ESP32-CAM + TFT 上的 MobileNet v1 实时图像分类（TinyML） | https://github.com/alankrantas/edge-impulse-esp32-cam-image-classification |

## E.3 官方动手教程（中文/英文）

| 资源 | 说明 | 链接 |
|---|---|---|
| Espressif Edge-AI with ESP32-S3 Workshop | 官方 7 节课工作坊，人脸检测→人脸识别→原始帧→手势识别→YOLO11 目标检测→ESP-PPQ 量化部署，约 180 分钟 | https://developer.espressif.com/workshops/edge-ai-with-esp32-s3/ |
| DFRobot《低成本+低门槛玩转 ESP32 边缘 AI 视觉相机》 | 中文实战：FireBeetle 2 ESP32-S3 + 3D 打印外壳 + Edge Impulse 数据采集与端侧推理闭环 | https://mc.dfrobot.com.cn/thread-324435-1-1.html |

---

# F. 未找到可靠来源清单

| # | 缺失项 | 尝试过的途径 | 状态 |
|---|---|---|---|
| 1 | **淘宝/天猫/拼多多/1688 的任何 ESP32 硬件价格** | item.taobao.com、world.taobao.com、detail.1688.com、s.taobao.com 全部登录墙（HTTP 200 但仅 4.7KB 壳页）；search.jd.com 纯 JS 渲染 | **需询价确认** |
| 2 | **微雪（Waveshare）中文站人民币价格** | waveshare.net 被阿里云 WAF 拦截 curl；web_fetch 返回空 | **需询价确认**（仅有国际站美元价） |
| 3 | DigiKey.cn / Mouser.cn 中国价 | 均 403（JS 挑战 / Access denied） | **需询价确认** |
| 4 | GoPro HERO13 Black 中国官方价 | gopro.com/zh/cn 商品页纯 JS 渲染，HTML 内无 price 字段 | **需询价确认** |
| 5 | ESP32-CAM 4MB PSRAM 版独立报价 | 立创参数栏「参数完善中」，未标注 PSRAM | **需询价确认** |
| 6 | OV5640 在 S3 上完整的分辨率-帧率对应表 | 官方只公布 1600×1200@25fps 一行 | **仅有单点数据** |
| 7 | 威海至帆 ZF-USB-01A10 水下相机报价 | 中国制造网标注「面议」 | **需询价确认** |
| 8 | 淘宝「水下摄像头 鱼塘」类目价格区间 | 淘宝登录墙 | **需询价确认** |
| 9 | 系统性「浊度 NTU vs 可视距离」实测曲线 | 仅检索到单一报道中的单点（30 NTU ≈ 10cm） | **仅有单点数据** |
| 10 | **UM980 模块 / UM980eb 评估板人民币价格** | 和芯星通官网只列规格不公开价；立创无此型号；淘宝需登录 | **需询价确认** |
| 11 | **UM982 模块 / UM982eb / ATK-UM982 价格** | 同上 | **需询价确认** |
| 12 | NEO-6M / GY-GPS6MV2 正规渠道在售价 | 淘宝登录墙、京东 JS、hqchip 登录墙、1688 登录墙、ickey JS | **需询价确认**（仅 C 级「¥18」线索） |
| 13 | NEO-M8N breakout 板（GY-GPSV3 等）零售价 | 同上 | **需询价确认** |
| 14 | ATGM336H breakout 板（带陶瓷天线成品板）淘宝实价 | 淘宝登录墙 | **需询价确认**（仅 C 级「¥28.8」线索） |
| 15 | ZED-F9P 淘宝实价 | 淘宝登录墙 | **需询价确认**。C 级线索称「¥142.5」，**与立创 ¥519.24 差 3.6 倍，判断极可能是仿冒/拆机件，不可采信** |
| 16 | LC29H EA/DA/BA/AA 各版本功能差异 | 立创页面未区分标注；未找到 Quectel 官方对比页 | **未核实** |
| 17 | u-blox 官方论坛帖正文 | 两个帖子均为 Salesforce SPA，curl/web_fetch 只能取到空壳 | **仅能证明帖子存在** |
| 18 | GB 50057《建筑物防雷设计规范》条款原文 | 未检索 | **未完成** |
| 19 | 养殖场雷击风险统计数据 | 未检索 | **未完成** |
| 20 | 水下 GPS 信号衰减量化数据 | 未检索 | **未完成** |
| 21 | **ESP32/S3 端侧鱼类检测的实测精度与帧率** | GitHub API 全量搜索、Edge Impulse、Hackster.io(403)、arXiv、IEEE(付费墙) | **未找到可靠实证** |
| 22 | star > 5 的「ESP32 端侧鱼类识别」开源项目 | GitHub API 搜索 total_count=5 且全部 0 star | **不存在** |
| 23 | YOLOv5n / YOLOv8n 在 ESP32-S3 上的可复现实测 | 未找到独立可复现测试 | **仅有 YOLO11n/YOLO26n 官方数据** |
| 24 | esp-who README 内的实测 FPS 表 | 现版本 README 已无帧率表 | **无官方帧率**（改用 esp-dl benchmark 替代） |

---

# G. 推荐 BOM（基于以上实证）

| 部件 | 推荐型号 | 单价(¥) | 理由 |
|---|---|---|---|
| 主控 | **DFRobot FireBeetle 2 ESP32-S3 N16R8（DFR0975）** | 125.00 | 16MB Flash + 8MB PSRAM，板载摄像头接口，AXP313A 锂电管理（适配太阳能+电池），官方中文文档 |
| 主控（备选） | 立创·ESP32S3R8N8 | 27.12 | 现货 1048，成本敏感节点 |
| 摄像头 | 板载 **OV2640**（FireBeetle 2 已含） | 0（已含） | 1600×1200 JPEG 对 224×224 AI 输入绰绰有余；OV5640 仅 AF 镜头模组才有额外价值 |
| GPS | **ATGM336H-5N31**（可选） | 11.15 | 现货 11937；仅用于防盗位移告警与断网授时 |
| 天馈防雷 | 沃盾 OD-TK-SMA | 185–198 | 若装 GPS 天线则**必配**，并可靠接地 |
| 电源防雷 | 沃盾 OD-D40KA | 180.00 | 塘口配电箱进线 |
| 信号防雷 | 沃盾 OD-DGX-24mA | 225.00 | RS485 / 4–20mA 传感器链路 |
| **合计（单站，含 GPS 与全套防雷）** | | **≈ ¥726–739** | |
| **合计（单站，不含 GPS、只留电源防雷）** | | **≈ ¥332** | |

**不该买的**：
- ❌ ¥10–20 的「u-blox NEO-6M」模块（官方 EOL，市面几乎全是 AT6558 冒充或拆机件）
- ❌ RTK（ZED-F9P ¥519 / UM980 询价 / DFRobot ¥799）——固定塘口用不上，且 CORS 年费 ¥3600
- ❌ 把 ESP32 下水（DVP 排线拉不长、USB 2.0 上限 5m、30 NTU 浑水视距仅约 10cm）
- ❌ 指望 ESP32-S3 做鱼类种类识别（无任何实证；MobileNetV2 分类都只有 1.14 FPS）
