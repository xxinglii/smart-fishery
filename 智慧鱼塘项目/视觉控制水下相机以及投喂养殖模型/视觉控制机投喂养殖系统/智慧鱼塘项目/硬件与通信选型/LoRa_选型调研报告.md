# 中国户外池塘 ESP32 IoT 监测系统 —— LoRa 通信方案可采购清单

> 调研时间：2025-2026 年｜货币：人民币 ¥（美元按 1 USD ≈ 7.2 CNY 换算，均保留原始币种）
> 检索方式：web_search + web_fetch 实际联网抓取，**所有价格均附可点击来源 URL**
> 说明：凡是本次未能从可靠来源确认的价格，一律写「需询价确认」，**未编造任何价格**

---

## 目录
1. [芯片对比：SX1276 vs SX1262](#1-芯片对比sx1276-vs-sx1262)
2. [Heltec WiFi LoRa 32 V3 / V2](#2-heltec-wifi-lora-32-v3--v2)
3. [安信可 Ai-Thinker Ra-01 / Ra-01H / Ra-02](#3-安信可-ai-thinker-ra-01--ra-01h--ra-02)
4. [亿佰特 Ebyte E22 / E220 / E32 系列](#4-亿佰特-ebyte-e22--e220--e32-系列)
5. [微雪 Waveshare LoRa 模块](#5-微雪-waveshare-lora-模块)
6. [天线选型与价格](#6-天线选型与价格)
7. [工程问题：距离 / SF / BW / 链路预算](#7-工程问题距离--sf--bw--链路预算)
8. [中国频段法规：433 / 470-510 / 868 / 915 MHz](#8-中国频段法规433--470-510--868--915-mhz)
9. [透传 vs LoRaWAN：网关是否必需？最低成本核算](#9-透传-vs-lorawan网关是否必需最低成本核算)
10. [LoRaWAN 网关价格](#10-lorawan-网关价格)
11. [未找到可靠来源 / 需询价确认清单](#11-未找到可靠来源--需询价确认清单)

---

## 1. 芯片对比：SX1276 vs SX1262

### 1.1 官方产品页 / 数据手册入口（可点击）

| 项目 | 链接 |
|---|---|
| Semtech SX1262 官方产品页 | https://www.semtech.com/products/wireless-rf/lora-connect/sx1262 |
| Semtech SX1262 Datasheet（官方 PDF） | https://semtech.my.salesforce.com/sfc/p/E0000000JelG/a/RQ000008nKCH/hp2iKwMDKWl34g1D3LBf_zC7TGBRIo2ff5LMnS8r19s |
| Semtech SX1276 官方产品页 | https://www.semtech.com/products/wireless-rf/lora-connect/sx1276 |
| Semtech LoRa Connect 全系列 | https://www.semtech.com/products/wireless-rf/lora-connect |
| Semtech 无线 RF 产品总览（含 3 mile / 30 mile 距离宣称） | https://www.semtech.com/products/wireless-rf |
| PCBSync：SX1276 vs SX1262 vs SX1280 对比文章 | https://pcbsync.com/lora-module-comparison/ |
| DigiKey：SX1261 / SX1262 产品highlight | https://www.digikey.hu/hu/product-highlight/s/semtech/sx1261-and-sx1262-lora-transceivers |
| 技象科技：LoRa 最大接收灵敏度 | https://www.techphant.cn/blog/103664.html |
| 技象科技：LoRa 最大发射功率 | https://www.techphant.cn/blog/96072.html |
| 技象科技：LoRa 天线频段范围 | https://www.techphant.cn/blog/105413.html |

### 1.2 关键差异对照表

| 维度 | SX1276（2013 代） | SX1262（2018 代） | 来源 / 说明 |
|---|---|---|---|
| 频段范围 | 137–1020 MHz | 150–960 MHz | Semtech 产品页；[UCT 论文对比表（SX1261/1262/1272/1276 = 150-960MHz）](https://open.uct.ac.za/server/api/core/bitstreams/3665e9e9-f300-496a-af5c-9f642792da17/content) |
| 最大发射功率 | +20 dBm | **+22 dBm** | [Semtech SX1262 产品页标题明确 "+22dBm, global frequency coverage"](https://www.semtech.com/products/wireless-rf/lora-connect/sx1262) |
| 接收灵敏度（SF12 / BW125） | −148 dBm（LnaBoost 开启，datasheet 标称） | −148 dBm（datasheet 标称） | Semtech datasheet（见 1.1 PDF 链接）。⚠️ 本次抓取工具无法解析 PDF，建议以 datasheet 原文复核 |
| 接收电流（RX） | 约 10.8–12 mA 级 | 约 4.6 mA 级（DC-DC 模式） | Semtech datasheet / [PCBSync 对比](https://pcbsync.com/lora-module-comparison/)。⚠️ 同上，以 datasheet 复核 |
| 发射电流（TX @ 最大功率） | 约 120 mA @ +20 dBm | 约 118 mA @ +22 dBm | Semtech datasheet。⚠️ 以 datasheet 复核 |
| 供电架构 | LDO only | **DC-DC + LDO**（低功耗关键） | Semtech 产品页 / DigiKey highlight |
| 是否支持 LoRaWAN | 支持（PHY 层） | 支持（PHY 层） | ⚠️ **重要澄清**：SX1276/SX1262 都只是射频收发器（PHY），LoRaWAN 是跑在 MCU 上的协议栈。**是否"支持 LoRaWAN"取决于 MCU + 协议栈，不取决于芯片本身**。两者都能跑 LoRaWAN。 |
| CAD（信道活动检测） | 支持 | 支持 | [RA-01（SX1278）参数表标注 "信道活动检测(CAD)"](https://www.bomman.com/details/1772120980506005677)；[RA-02 同样标注 CAD](https://www.bomman.com/details/1772120980506005825) |
| 寻址功能 | 无硬件寻址，靠 MCU/协议栈 | 无硬件寻址，靠 MCU/协议栈 | 芯片级均无"节点寻址"硬件；寻址由上层协议（LoRaWAN DevAddr / 自定义包头）实现 |
| 封装代际 | QFN 6×6 mm | **QFN 4×4 mm**（更小） | Semtech 产品页 / DigiKey highlight |
| 新增特性 | — | SF5/SF6、更快 TX/RX 切换、RX Duty Cycle、LoRa Basics Modem 官方支持 | [Semtech LoRa Connect](https://www.semtech.com/products/wireless-rf/lora-connect)；[E22-400M30S 商品页明确写"为支持密集网络推出的全新 SF5 扩频因子"](https://item.szlcsc.com/402603.html) |

### 1.3 厂商模块实测参数（本次真实抓取到的官方/商城参数表）

| 模块 | 芯片 | 发射功率 | 接收灵敏度 | 接收电流 | 发射电流 | 来源 |
|---|---|---|---|---|---|---|
| 亿佰特 E22-400M30S | SX1268 + PA + LNA | 30 dBm | **−151 dBm** | 14 mA | 650 mA | [立创商城商品页](https://item.szlcsc.com/402603.html) |
| 亿佰特 E220-400M22S | LLCC68 | 21.5 dBm | −129 dBm | 6.5 mA | 100 mA | [圣禾堂在线商品页](https://www.bomman.com/details/1772120980506005897) |
| 安信可 RA-02 | SX1278 | 18 dBm | −141 dBm | 12.15 mA | 93/97 mA | [圣禾堂在线商品页](https://www.bomman.com/details/1772120980506005825) |
| 安信可 RA-01 | SX1278 | 18 dBm | −148 dBm | 12.15 mA | 93 mA | [圣禾堂在线商品页](https://www.bomman.com/details/1772120980506005677) |
| 安信可 RA-01H | SX1278 | 20 dBm | −140 dBm | 12.15 mA | 105 mA | [圣禾堂在线商品页](https://www.bomman.com/details/1876116086426157217) |
| Heltec WiFi LoRa 32 V2 | SX1276 | 19±1 dBm | −135 dBm | — | — | [Tindie 商品页](https://www.tindie.com/products/m2m/heltec-wifi-lora-32v2/) |

**选型结论（池塘场景）**：优先 **SX1262 / SX1268**。理由：接收电流低一个数量级（电池/太阳能供电友好）、封装小、官方工具链（LoRa Basics Modem）成熟、且新模组普遍带 PA+LNA（E22-400M30S 灵敏度 −151 dBm，链路预算比 SX1278 高约 10 dB）。

---

## 2. Heltec WiFi LoRa 32 V3 / V2

| 型号 | 关键参数 | 参考价格(¥) | 来源链接 | 备注 |
|---|---|---|---|---|
| **Heltec WiFi LoRa 32 (V3)** | ESP32-S3FN8 + **SX1262** + 0.96" OLED，LoRaWAN / Meshtastic 兼容，CP2102 | **约 ¥288**（原价 HKD 313.53） | [Amazon 商品页](https://www.amazon.com/Heltec-Development-915-MHz-Case/dp/B0DHGZKCL1) | ⚠️ 第三方跨境零售（915MHz 带外壳版），含运费/关税前价格。**官方 heltec.org 人民币标价本次未能抓取到（页面价格由 JS 渲染），建议直接在 heltec.org 下单页或淘宝「Heltec 官方店」询价** |
| Heltec WiFi LoRa 32 (V3) 官方产品页 | 同上（产品资料 / datasheet / 固件） | 需询价确认 | https://heltec.org/project/wifi-lora-32-v3/ | 官方页面，含完整规格与下载 |
| Heltec ESP32+LoRa 全系列 | — | 需询价确认 | https://heltec.org/product-category/lora/lrnode/esp32-lora/ | 官方分类页（价格 JS 渲染） |
| **Heltec WiFi LoRa 32 (V2)** | ESP32 + **SX1276**（863–923MHz）+ 0.96" OLED，CP2102，最大 19±1 dBm，灵敏度 −135 dBm，睡眠 ≤800 µA | **$30.00 ≈ ¥216** | [Tindie – M2M Shop](https://www.tindie.com/products/m2m/heltec-wifi-lora-32v2/) | ⚠️ 该卖家标注 "taking a break until Dec. 31, 2026"（暂停营业），价格仅作历史参考 |
| Heltec V2 官方产品页 | 同上 | 需询价确认 | https://heltec.org/ | 官方站 |

**V2 → V3 关键升级**：MCU 从 ESP32 升到 **ESP32-S3**（支持 AI 指令、USB-OTG），射频从 **SX1276 → SX1262**（RX 电流大降、+22dBm），固件生态从"仅 LoRaWAN 库"扩展到 **Meshtastic 原生支持**。

> ⚠️ **价格确认建议**：Heltec 是中国成都厂商，国内淘宝官方店/立创商城价格通常显著低于跨境零售。本次抓取未能穿透 heltec.org 的 JS 价格渲染与淘宝反爬，**V3 国内人民币实价建议以淘宝「Heltec 官方旗舰店」或立创商城实时报价为准**。

---

## 3. 安信可 Ai-Thinker Ra-01 / Ra-01H / Ra-02

| 型号 | 关键参数 | 参考价格(¥) | 来源链接 | 备注 |
|---|---|---|---|---|
| **Ra-01** | SX1278，433MHz，SPI，18dBm，−148dBm，**弹簧天线**，2.5–3.7V，支持 AFC+CAD，SMD-16P | **1+ ¥47.09**<br>10+ ¥42.17<br>30+ ¥27.04<br>100+ ¥24.53 | [圣禾堂在线（含税阶梯价）](https://www.bomman.com/details/1772120980506005677) | 描述为"配天线（两件套）"。**批量价（100+）比零售低约 48%** |
| **Ra-01H** | SX1278，803–930MHz（高频版），SPI，**20dBm**，−140dBm，3.3V，支持跳频扩频+CAD，SMD-16P | **1+ ¥44.31**<br>10+ ¥43.47<br>18+ ¥31.74 | [圣禾堂在线（含税阶梯价）](https://www.bomman.com/details/1876116086426157217) | 20dBm 版本，注意**在中国 433MHz 频段 20dBm 超出微功率限值**（见第 8 节） |
| **Ra-02** | SX1278，433MHz，SPI，18dBm，−141dBm，**IPEX 接口**，2.5–3.7V，支持 CAD，SMD-16P | **1+ ¥46.36**<br>10+ ¥41.83<br>30+ ¥29.55<br>100+ ¥25.12<br>500+ ¥24.07<br>800+ ¥23.61 | [圣禾堂在线（含税阶梯价）](https://www.bomman.com/details/1772120980506005825) | 库存 2742 pcs。**最适合池塘项目：IPEX 可外接高增益天线** |
| Ra-01 / Ra-02 官方资料 | datasheet / 参考设计 | — | https://docs.ai-thinker.com/ | 安信可官方文档中心 |
| 安信可品牌页（立创商城） | 全系列选型 | 需询价确认 | https://list.szlcsc.com/brand/944.html | 立创价格 JS 渲染，需登录查询 |
| Ra-02（华秋商城） | 同上 | 需询价确认 | https://item.hqchip.com/1001223654.html | 备选采购渠道 |
| Ra-02（云汉芯城） | 同上 | 需询价确认 | https://www.ickey.cn/detail/1003001013489492/RA-02.html | 备选采购渠道 |

**Ra-01 vs Ra-02 怎么选**：Ra-01 自带弹簧天线（省事，但增益低、方向性差）；**Ra-02 用 IPEX 座，可外接吸盘/玻璃钢天线**——户外池塘（发射端在开阔水面、接收端在室内）**强烈建议选 Ra-02 + 外接天线**。

---

## 4. 亿佰特 Ebyte E22 / E220 / E32 系列

| 型号 | 关键参数 | 参考价格(¥) | 来源链接 | 备注 |
|---|---|---|---|---|
| **E22-400M30S** | **SX1268 + PA + LNA**，410–493MHz（433/470），**30 dBm / 1W**，SPI，SMD 38.5×24mm，灵敏度 −151dBm，RX 14mA / TX 650mA，双天线（IPEX + 邮票孔） | **1+ ¥56.25**<br>10+ ¥54.95 | [壹方微芯（含税阶梯价）](https://www.ygchip.com/product/u1t4yc) | 立创商城编号 **C411292**；商品页：https://item.szlcsc.com/402603.html 。官方标称理想距离 **12km** |
| **E220-400M22S** | LLCC68 + PA + LNA，433/470MHz，**21.5dBm**，SPI（LLCC68 为 SPI），SMD 20×14mm，灵敏度 −129dBm，RX 6.5mA / TX 100mA，1.8–3.7V | **1+ ¥24.95**<br>10+ ¥21.32<br>30+ ¥19.15<br>100+ ¥16.96<br>500+ ¥15.95 | [圣禾堂在线（含税阶梯价，库存 706）](https://www.bomman.com/details/1772120980506005897) | 同一型号另一渠道：**1+ ¥23.79 / 10+ ¥20.97 / 30+ ¥19.28 / 100+ ¥17.89 / 500+ ¥16.95 / 1000+ ¥16.52** — [壹方微芯](https://m.ygchip.com/product/23FHzZKR) |
| **E220P-400T22S** | LLCC68 系列（T = UART 透传版本） | **1+ ¥43.70**<br>10+ ¥42.56 | [壹方微芯（含税阶梯价）](https://www.ygchip.com/product/TWSLAGS) | ⚠️ 具体接口形态请下单前与客服确认（T 系列通常为 UART 透传） |
| **E32-433T20D** | SX1278，433MHz，**UART 透传**，20dBm（100mW），DIP 封装 | 需询价确认 | [立创商城商品页](https://item.szlcsc.com/3364203.html)；[RobotShop 商品页（$ 未抓取到）](https://www.robotshop.com/products/ebyte-e32-433t20d-oem-odm-lora-solution-433mhz-uart-wireless-lora-module) | **本次两个渠道都被反爬拦截（Cloudflare / JS 渲染），未取到可靠人民币价格，请勿采信任何其他来源的报价** |
| E22-400M22S 等同系列 | SX1262/SX1268 SPI 模组 | 需询价确认 | https://item.szlcsc.com/402604.html （E22-900M22S 相邻型号） | 立创价格需登录 |
| 亿佰特官方产品线（SX126X） | 全系列选型 | — | https://www.ebyte.com/product/lora-sx126x.html | 官方选型页 |
| 亿佰特 E22 系列资料下载 | datasheet / 配置工具 | — | https://www.ebyte.com/datadown/lora-E22.html | 官方资料 |
| 亿佰特官方商城（海外） | — | 需询价确认 | https://ebyteiot.com/ | 官方英文商城 |

**E22-400M30S 关键提醒**：30dBm（1W）在中国 433MHz 频段**远超微功率限值**（433.05–434.79MHz 限 10mW e.r.p）。若严格遵守 52 号公告，**该型号只能用于 470–510MHz 民用计量仪表场景（限 50mW），或需申请电台执照**。详见第 8 节。

---

## 5. 微雪 Waveshare LoRa 模块

### 5.1 官方定价（美元，waveshare.com 实时抓取）

| 型号 | 关键参数 | 参考价格(¥) | 来源链接 | 备注 |
|---|---|---|---|---|
| **USB to LoRa Data Transfer Module** | **SX1262**，USB 直插，工业/农业数据采集 | **$15.99–17.99 ≈ ¥115–130** | https://www.waveshare.com/product/iot-communication/long-range-wireless/nb-iot-lora/usb-to-lora.htm | ⭐ **最适合池塘项目做"家里那端"**：USB 直插电脑/树莓派，免 MCU |
| **Rail-mount SX1262 LoRa DTU** | SX1262，RS232/RS485/RS422 → LoRa，导轨式 | **$21.99–25.99 ≈ ¥158–187** | https://www.waveshare.com/product/iot-communication/long-range-wireless/nb-iot-lora/sx1262-lora-dtu-lf.htm | 工业级，适合接 RS485 传感器 |
| **RP2040-LoRa Development Board** | RP2040 + **SX1262** | **$12.99–15.99 ≈ ¥94–115** | https://www.waveshare.com/product/iot-communication/long-range-wireless/nb-iot-lora/rp2040-lora.htm | — |
| **ESP32-S3 LoRa Development Board** | ESP32-S3 + **LR1121**（第三代 RF，Sub-GHz + 2.4GHz） | **$14.99–15.99 ≈ ¥108–115** | https://www.waveshare.com/product/iot-communication/long-range-wireless/nb-iot-lora/esp32-s3-lr1121.htm | ⭐ 与本项目 ESP32 技术栈完全一致 |
| Core1121 LF/HF Dual-Band LoRa Module | LR1121，Sub-GHz + 2.4GHz | **$9.99–10.99 ≈ ¥72–79** | https://www.waveshare.com/product/iot-communication/long-range-wireless/nb-iot-lora/core1121-xf.htm | 纯模组 |
| Core2021 LF/HF Dual-Band LoRa Module | LR2021 | **$11.99–12.99 ≈ ¥86–94** | https://www.waveshare.com/product/iot-communication/long-range-wireless/nb-iot-lora/core2021-xf.htm | 最新一代 |
| Waveshare LoRa 全系列分类页 | — | — | https://www.waveshare.com/product/iot-communication/long-range-wireless/nb-iot-lora.htm | 官方分类 |

> 汇率说明：按 1 USD ≈ 7.2 CNY 换算，实际以结算汇率 + 关税为准。

### 5.2 中国零售价

| 型号 | 关键参数 | 参考价格(¥) | 来源链接 | 备注 |
|---|---|---|---|---|
| **Waveshare SX1262 LoRa HAT for Raspberry Pi（868MHz 频段）** | SX1262，树莓派 HAT，UART 控制 | **¥157.72** | [Sunsky-online 商品页](https://www.sunsky-online.com/zh_TW/p/ZY23043811/Waveshare-16806.htm) | ⚠️ **第三方转售站点标价（从商品标题抓取），非微雪官方；建议与微雪淘宝官方店复核** |
| **Waveshare SX1262 868/915M LoRaWAN HAT（带吸盘天线）** | SX1262，LoRaWAN 节点模块，**含吸盘天线** | 需询价确认 | [微雪中文站商品页](https://www.waveshare.net/shop/SX1262-868-915M-LoRaWAN-HAT.htm) | 微雪中文站价格 JS 渲染，本次未抓到。**该套装含天线，性价比需询价对比** |
| Waveshare SX1262 915M LoRa HAT（UART） | SX1262，915MHz | 需询价确认 | [微雪中文站商品页](https://www.waveshare.net/shop/SX1262-915M-LoRa-HAT.htm) | 同上 |
| Waveshare SX130x LoRaWAN Gateway Module（树莓派 Mini-PCIe） | SX1302/SX1303 8 通道网关模块 | 需询价确认 | https://www.waveshare.com/product/iot-communication/long-range-wireless/nb-iot-lora.htm | 自建网关方案 |

---

## 6. 天线选型与价格

### 6.1 天线类型对比（工程建议）

| 类型 | 典型增益 | 优点 | 缺点 | 池塘场景适用性 |
|---|---|---|---|---|
| **弹簧天线（螺旋）** | 2 dBi | 免费随模块附送（Ra-01 自带）、免安装 | 增益低、易受金属/水体影响、无馈线延伸能力 | ⭐ 仅适合原型验证 |
| **胶棒天线（SMA 直插）** | 2–5 dBi | 便宜、即插即用、可换 | 需模块有 SMA 座；直插在模块上，位置受限 | ⭐⭐ 室内接收端可用 |
| **小吸盘 / 磁吸天线** | 3 / 5 / 8 dBi | **带 1–10m 馈线，可把天线吸在铁皮/机箱外**，灵活 | 馈线损耗随长度增加；磁吸底座需金属面 | ⭐⭐⭐ **推荐**：发射端吸在池塘设备箱顶 |
| **玻璃钢全向天线（室外抱杆）** | 5 / 8 / 10 dBi | **防水、防紫外线、可高架**，增益高，是全向天线的户外首选 | 体积大、需抱杆/立杆、需 N 型接头 + 转接 | ⭐⭐⭐⭐ **推荐给"家里"那端**：架在屋顶，显著改善链路 |
| **八木 / 定向天线** | 8–12 dBi | 增益最高、方向性强 | 需精确对准，池塘水位/船扰动会影响 | ⭐⭐ 固定点对点（池塘↔家）可用 |
| **馈线 RG58 / RG174 / LMR400** | −0.5 ~ −3 dB/10m | — | 433MHz 下 RG174 损耗约 1.5–2 dB/10m，RG58 约 1 dB/10m，LMR400 约 0.4 dB/10m | ⭐⭐⭐ **馈线越长越吃亏，优先把天线架高而不是拉长馈线** |

### 6.2 天线价格

| 型号/类型 | 增益 | 关键参数 | 参考价格(¥) | 来源链接 | 备注 |
|---|---|---|---|---|---|
| IPEX4 → SMA 外螺纹内孔 转接线（20cm） | — | 模块 IPEX 转标准 SMA | **¥5.00** | [DFRobot 商品页](https://www.dfrobot.com.cn/goods-3867.html) | ⭐ **Ra-02 / E220 接外置天线必备**，本次唯一抓到的确定价格 |
| 433/470MHz 吸盘天线（14.5cm / 36cm / 铜棒，SMA） | 全向高增益 | 2–50m 馈线可选 | 需询价确认 | [京东商品页（聚鑫阁）](https://item.jd.com/10227527123229.html) | 京东价格 JS 渲染，未抓到 |
| 470-510MHz 吸盘天线 5dBi（高 15cm，10m 线） | 5 dBi | SMA 内针 | 需询价确认 | [京东商品页（正昌立博）](https://item.jd.com/10044275885173.html) | 抄水表同频段 |
| 470MHz 吸盘天线（5dBi / 8dBi / 12dBi，0.5–5m 线） | 5/8/12 dBi | SMA 内针 | 需询价确认 | [京东商品页（丰应子 8dBi）](https://item.jd.com/100066988247.html) | 同店有 5/12dBi 多档 |
| 433-470MHz 吸盘天线 6dBi / 8dBi | 6/8 dBi | SMA 内针 | 需询价确认 | [京东商品页（飙戎 8dBi）](https://item.jd.com/100300843616.html) | — |
| 470MHz 吸盘天线 5dBi（高 14.5cm） | 5 dBi | SMA 内孔 | 需询价确认 | [京东商品页（稔田）](https://item.jd.com/100233238432.html) | — |
| 亿佰特官方 433MHz 天线系列 | 2–8 dBi | 多种形态 | 需询价确认 | https://www.ebyte.com/product/antenna-case7.html | 官方天线选型页 |
| 亿佰特官方 470MHz 天线系列 | 2–8 dBi | 多种形态 | 需询价确认 | https://www.ebyte.com/product/antenna-case8.html | 官方天线选型页 |
| 微雪天线配件 | — | SMA / IPEX | 需询价确认 | https://www.waveshare.com/product/accessories/adapters-cables-antennas/antennas.htm | 官方配件页 |
| Heltec 天线配件 | — | 433/470/868/915MHz | 需询价确认 | https://heltec.org/product-category/module-element/antenna/ | 官方配件页 |

> ⚠️ **天线价格本次未能取得可靠来源**：淘宝/京东/1688 的价格均由 JS 动态渲染，`web_fetch` 无法读取；玻璃钢天线（8dBi 室外全向）在中国电商的实际零售价通常显著高于弹簧/吸盘天线，**请以淘宝/京东实时报价为准，本次不做任何价格推测**。

---

## 7. 工程问题：距离 / SF / BW / 链路预算

### 7.1 距离数据（有来源）

| 场景 | 距离 | 来源 |
|---|---|---|
| 城市环境（urban） | **3 miles ≈ 4.8 km** | [Semtech 官方："a 3-mile range in urban environments and a 30-mile range outdoors"](https://www.semtech.com/products/wireless-rf) |
| 开阔户外（outdoors） | **30 miles ≈ 48 km** | 同上（Semtech 官方营销口径，**理想视距 + 高增益天线 + SF12 条件下**，实际极少达到） |
| E22-400M30S（30dBm） | 理想条件 **12 km** | https://item.szlcsc.com/402603.html （官方商品描述） |
| E220-400M22S（21.5dBm） | 开阔地 **5.5 km**；半开阔农田约 2–3 km（原文"半开阔地（如农田）约2~3km"，注意原文数字排版有误，以官方 datasheet 为准） | https://www.bomman.com/details/1772120980506005897 |
| RA-02（18dBm / SX1278） | 开阔地标称 **10 km** | https://www.bomman.com/details/1772120980506005825 |

**池塘 → 家里 的现实预期**：
- 距离通常 < 2 km，中间有树木、房屋、水面反射
- **SF12 / BW125 / CR4-5 / +20dBm / 两端各 2dBi 天线**：稳定通信 1–3 km 是合理预期
- **关键增益点**：把"家里"那一端的天线架到屋顶（哪怕是 5dBi 胶棒），比换更大功率模块有效得多
- 水面是良好的反射面但也有多径；池塘边设备箱建议天线**垂直极化、尽量离水面 ≥1m**

### 7.2 影响距离的参数

| 参数 | 作用 | 权衡 |
|---|---|---|
| **扩频因子 SF** | SF 越大，灵敏度越高（SF12 比 SF7 高约 12–13 dB），距离越远 | SF 越大，**空中时间越长、功耗越高、数据率越低**。SF12@BW125 单包可达 1–2 秒 |
| **带宽 BW** | BW 越窄，灵敏度越高 | 125 kHz（最常用）→ 250 → 500 kHz（速率高、距离近） |
| **编码率 CR** | CR 4/5 ~ 4/8，纠错能力递增 | CR 越大，开销越大，有效速率越低 |
| **发射功率** | 每 +6 dB ≈ 距离翻倍（自由空间） | 受**中国微功率法规限值**约束（见第 8 节）：433MHz 仅 10mW |
| **天线增益** | 每 +6 dB ≈ 距离翻倍 | 高增益天线方向性更强，需对准 |
| **链路预算** | Link Budget = TX功率 + TX天线增益 − 馈线损耗 + RX天线增益 − RX灵敏度 | 例：**20dBm + 2dBi − 1dB + 2dBi − (−148dBm) = 171 dB** |

**链路预算计算示例（SX1276/SX1262，SF12/BW125）**：
```
TX 功率          +20 dBm
TX 天线增益      + 2 dBi
馈线损耗         − 1 dB
RX 天线增益      + 2 dBi
RX 灵敏度        −(−148 dBm) = +148 dB
─────────────────────────────
链路预算          = 171 dB
```
按自由空间路径损耗公式 `FSPL(dB) = 32.44 + 20log₁₀(f_MHz) + 20log₁₀(d_km)`：
- 433 MHz、1 km → FSPL ≈ 85.2 dB
- 433 MHz、10 km → FSPL ≈ 105.2 dB
- 171 dB 预算理论上可支撑 **>1000 km 视距**（这就是 Semtech "30 miles" 宣称的来源）
- **现实中损失来自**：菲涅尔区遮挡、地面反射、树木/建筑穿透（每堵墙 10–20 dB）、天线失配、水面多径、噪声底抬升
- **经验法则**：郊区/农田实际 ≈ 理论视距的 **1/10 ~ 1/3**；有建筑遮挡时再打 5 折

> 参考来源：[Semtech LoRa 技术页](https://www.semtech.com/lora/what-is-lora)、[Semtech LoRa Calculator](https://www.semtech.com/design-support/lora-calculator)、[PCBSync 模块对比](https://pcbsync.com/lora-module-comparison/)、[The Things Network 文档](https://www.thethingsnetwork.org/docs/)
> ⚠️ 本次未能抓到 TTN 频率参数页（404）；上表 SF/BW 数值为 LoRa 标准参数，建议以 Semtech datasheet 与 LoRa Alliance 规范复核。

---

## 8. 中国频段法规：433 / 470-510 / 868 / 915 MHz

### 8.1 法规原文

| 文件 | 链接 |
|---|---|
| **工信部 2019 年第 52 号公告（全文）** | https://www.miit.gov.cn/zwgk/zcwj/wjfb/gg/art/2020/art_4f2c890530cc4837b2113cf977e249c4.html |
| 52 号公告手机版 | https://wap.miit.gov.cn/jgsj/wgj/wjfb/art/2020/art_792ab84586c34b64bb391eb6496c0953.html |
| **附件《微功率短距离无线电发射设备目录和技术要求》（PDF）** | https://www.miit.gov.cn/cms_files/filemanager/oldfile/miit/n1146295/n1652858/n1652930/n4509607/c7545828/part/7545929.pdf |
| SRRC 认证服务中心：微功率设备技术要求（**具体限值，已抓取**） | https://www.srrc.net.cn/faq/135.html |
| C114 深度解读：无管局微功率设备最新公告 | https://www.c114.com.cn/news/16/a1110180.html |
| 亿佰特：LoRa 模块频段怎么选（433/470/915MHz 使用指南） | https://www.ebyte.com/news/4898.html |
| 中国计量：《微功率短距离无线电发射民用计量仪表技术要求》发布 | http://chinajl.com.cn/shiyanshidongtai/69669.html |

### 8.2 52 号公告核心条款（原文摘录）

- **第一条**：生产或进口列入并符合《目录和技术要求》的设备，**无需取得无线电频率使用许可、无线电台执照、无线电发射设备型号核准**。
- **第二条**：微功率设备**不得对其他合法无线电台（站）产生有害干扰**，也不得提出免受有害干扰的保护要求。
- **第四条**：**使用微功率设备不得擅自改变使用场景、扩大发射频率范围、加大发射功率（包括额外加装射频功率放大器），不得擅自更改发射天线。** ← ⚠️ **这一条对"加 PA 的 1W 模块 + 高增益天线"是明确的红线**
- **第六条**：产品说明书必须注明使用场景、天线类型和性能等 8 项内容。
- **第七条**：**自 2022 年 1 月 1 日起，停止生产或者进口不符合本公告但符合信部无〔2005〕423 号规定的"民用计量仪表"等微功率设备。**

### 8.3 各频段限值对照表（来源：https://www.srrc.net.cn/faq/135.html）

| 应用类别 | 使用频率 | 发射功率限值 | 占用带宽 | 其他限制 |
|---|---|---|---|---|
| **通用无线遥控设备** | 314–316 MHz、430–432 MHz、**433.05–434.79 MHz** | **10 mW (e.r.p)** | ≤ 400 kHz | 不得用于无线控制玩具、模型等 |
| 通用无线遥控设备 | 470–566 MHz、614–698 MHz | **5 mW (e.r.p)** | ≤ 1 MHz | — |
| 通用无线遥控设备 | **868–868.6 MHz** | **5 mW (e.r.p)** | — | 频率容限 100×10⁻⁶；**发射信号占空比不超过 1%** |
| 无线传声器设备 | 470–510 MHz、630–698 MHz | 50 mW (e.r.p) | ≤ 200 kHz | 频率容限 100×10⁻⁶ |
| **民用计量仪表** | **470–510 MHz** | **50 mW (e.r.p)** | ≤ 500 kHz | 功率谱密度：BW≤200kHz 时 50mW/200kHz；BW 200–500kHz 时 10mW/100kHz。**单次发射持续时间 ≤ 1 秒**；频率容限 100×10⁻⁶ |

### 8.4 结论：中国到底该用哪个频段？

| 频段 | 中国合法性 | 结论 |
|---|---|---|
| **433.05–434.79 MHz** | ✅ **合法（通用无线遥控/遥测）** | **限 10 mW (e.r.p) ≈ 10 dBm**。⚠️ **这意味着市面上 20dBm（100mW）的 Ra-01H、30dBm 的 E22-400M30S 在 433MHz 下均超限**。合规做法：软件把发射功率降到 ≤10dBm，且天线增益计入后 ERP 不超 10mW |
| **470–510 MHz** | ⚠️ **仅限"民用计量仪表"等目录内场景** | **限 50 mW (e.r.p) ≈ 17 dBm**，BW ≤500kHz，**单次发射 ≤1 秒**。"民用计量仪表"指水表/电表/气表/热量表等法定计量器具。**普通环境监测（水温、溶氧、pH）严格说不属于该条目**，存在合规灰区。C114 解读提到该频段定位为"居民楼、住宅小区、村庄等小范围室内应用"（[C114](https://www.c114.com.cn/news/16/a1110180.html)，原文页面编码异常但关键结论可辨） |
| **868–868.6 MHz** | ⚠️ **技术上在目录内，但限 5 mW 且占空比 ≤1%** | **5 mW ≈ 7 dBm**，且**发射占空比不超过 1%**（即 100 秒内累计发射 ≤1 秒）。这对 LoRa 数据回传是**极其苛刻**的限制。**结论：868MHz LoRa 模块在中国大陆不适合常规使用**（欧洲 EU868 标准在中国无对应开放频段） |
| **915 MHz（902–928 MHz）** | ❌ **不在微功率设备目录内** | 中国大陆**未开放 902–928MHz 给微功率设备**。915MHz 是美国 FCC 频段，**在中国使用不合法**。AS923 同样不适用。⚠️ 这也是为什么上述 Heltec/Seeed 的"915MHz 版本"在国内购买时需特别警惕 |

### 8.5 对池塘项目的实操建议

1. **首选 433MHz 频段**，但**必须把发射功率限制在 ≤10 dBm (10 mW e.r.p)**，并把天线增益计入 ERP。
2. 若接受合规灰区，可用 **470–510MHz 频段**（限 50mW / 单次 ≤1s），大数据量分片发送、每片 ≤1 秒。
3. **不要购买 868MHz / 915MHz 版本**（除非仅做桌面实验不上空）。
4. **不要加装额外的射频功率放大器**（52 号公告第四条明确禁止）。
5. 天线必须使用**与模块匹配的合规天线**，不得擅自更改（第四条）。
6. 实际功率 10 dBm + SF12 + 2dBi 天线，在池塘↔家 1–2km 场景仍**完全可行**，靠 SF 和天线增益补距离，而不是靠功率。

---

## 9. 透传 vs LoRaWAN：网关是否必需？最低成本核算

### 9.1 结论：一对一透传**不需要** LoRaWAN 网关 ✅

**技术依据**：
- SX1276 / SX1262 是**射频收发器（PHY）**，本身就能做点对点（P2P）通信，[Semtech 明确 LoRa 是 PHY 层技术，LoRaWAN 是上层协议](https://www.semtech.com/lora/what-is-lora)
- LoRaWAN 网关的作用是：把 LoRa 空口数据**汇聚并转发到网络服务器（NS）**，它解决的是"多节点、标准化、漫游、鉴权"的问题
- 一对一透传只需：**A 端模块 → 空口 → B 端模块**，两端配置相同的频率 / SF / BW / 同步字即可
- 厂商透传固件（如亿佰特 E32/E22 T 系列、微雪 USB-to-LoRa）已内置 P2P 透传模式

**什么时候才需要 LoRaWAN 网关**：
- 节点数 > 2 且需要统一管理
- 需要接入标准 LoRaWAN 网络服务器（TTN / ChirpStack / 商业 NS）
- 需要节点鉴权、OTA 升级、漫游、Class A/B/C 调度
- **池塘单点监测（1 个发射端 + 1 个接收端）→ 完全不需要网关**

### 9.2 一对透传最低成本核算

**方案 A：UART 透传模块（免 MCU，最省事）**

| 项目 | 型号 | 单价(¥) | 数量 | 小计(¥) | 来源 |
|---|---|---|---|---|---|
| LoRa 透传模块 | 微雪 USB to LoRa (SX1262) | 115–130（$15.99–17.99） | 2 | 230–260 | https://www.waveshare.com/product/iot-communication/long-range-wireless/nb-iot-lora/usb-to-lora.htm |
| 天线 | 随模块附赠 | 0 | 2 | 0 | — |
| **合计** | | | | **≈ ¥230–260** | 两端都 USB 直插，**完全不需要 USB 转 TTL** |

**方案 B：SPI 模组 + ESP32（本项目既有技术栈，最省钱）**

| 项目 | 型号 | 单价(¥) | 数量 | 小计(¥) | 来源 |
|---|---|---|---|---|---|
| LoRa 模组 | 安信可 Ra-02 (SX1278, IPEX) | 46.36 | 2 | 92.72 | https://www.bomman.com/details/1772120980506005825 |
| — 批量价（100+） | 同上 | 25.12 | 2 | 50.25 | 同上 |
| IPEX→SMA 转接线 | DFRobot | 5.00 | 2 | 10.00 | https://www.dfrobot.com.cn/goods-3867.html |
| 吸盘天线 | — | 需询价确认 | 2 | — | 见第 6 节 |
| **合计（不含天线）** | | | | **≈ ¥102.72**（零售）／**¥60.25**（批量） | |

**方案 C：UART 透传 + 外接天线（平衡方案）**

| 项目 | 型号 | 单价(¥) | 数量 | 小计(¥) | 来源 |
|---|---|---|---|---|---|
| LoRa 透传模块 | E220P-400T22S | 43.70 | 2 | 87.40 | https://www.ygchip.com/product/TWSLAGS |
| USB 转串口 | DFRobot USB to Serial | 40.00 | 1 | 40.00 | https://www.dfrobot.com.cn/goods-242.html |
| IPEX→SMA + 天线 | — | 5.00 + 需询价 | 2 | 10.00+ | https://www.dfrobot.com.cn/goods-3867.html |
| **合计（不含天线）** | | | | **≈ ¥137.40** | |

**最低成本结论**：
- **绝对最低**：2×Ra-02（批量 ¥25.12）≈ **¥50.25 + 天线**，用 ESP32 直接驱动 SPI（本项目已有 ESP32，边际成本几乎为 0）
- **最省事**：2×微雪 USB-to-LoRa ≈ **¥230–260**，插上就能用
- **不需要** LoRaWAN 网关、不需要网络服务器、不需要 LoRa Alliance 认证

---

## 10. LoRaWAN 网关价格

> 说明：Dragino / RAK / Seeed 官方 store 与 RobotShop、DigiKey、Mouser、choovio、eckstein 等主流分销商**全部被 Cloudflare 反爬拦截**（HTTP 403），本次通过中国代理商与 Makerfabs 取得了部分可靠价格。

| 型号 | 关键参数 | 参考价格(¥) | 来源链接 | 备注 |
|---|---|---|---|---|
| **Dragino LPS8v2** | 8 通道 LoRaWAN 室内网关，SX1302，WiFi + Ethernet，可选 4G（EC25） | **¥1482.12** | [深圳凌创辉电子（多能代理商）](https://www.ljq.cc/product/bGpxLTk1MzYxNzY=) | 该报价为 **US915 版本**；国内合规需选 470MHz 版本 |
| **Dragino LPS8 / LPS8N（基础版）** | 8 通道，SX1308/SX1302 | 需询价确认 | [Dragino 官方产品页](https://www.dragino.com/products/lora-lorawan-gateway/item/140-lps8.html) | 官方页只给规格与"Buy"指向分销商，**无官方定价**。京东/淘宝价格 JS 渲染未抓到 |
| Dragino LG308 | 8 通道室内网关，SX1301 + 2×SX1257，10 路并行解调，WiFi/Ethernet，可选 4G | 需询价确认 | https://www.dragino.com/products/lora-lorawan-gateway/item/140-lps8.html | 官方规格页 |
| Dragino 网关选型指南 | — | — | https://www.dragino.com/products/lora-lorawan-gateway.html | 官方分类页 |
| **RAK WisGate Edge Lite 2（RAK7268）** | 8 通道 LoRaWAN 室内网关，WiFi/PoE | **¥1439.93** | [深圳凌创辉电子（锐凌代理商）](https://www.ljq.cc/product/bGpxLTk1MzkxMTk=) | ⭐ 同时支持 4G 的型号为 RAK7268CV2（含 EG95-E LTE），**4G 版价格需询价确认** |
| RAK7268V2 / RAK7248 | WisGate Edge Lite 2 系列 | 需询价确认 | https://store.rakwireless.com/ | 官方 store 被反爬拦截；[DigiKey 型号页（403）](https://www.digikey.com/en/products/detail/rakwireless-technology-limited/RAK7268CV2-EG95E-EU868-W/29287295) |
| **Seeed SenseCAP M2 Multi-Platform LoRaWAN Indoor Gateway（SX1302）** | 8 通道，MT7628 580MHz，128MB RAM / 32MB Flash，WiFi，可选 EU868/US915/AS923/AU915 | **$99.00 ≈ ¥713** | [Makerfabs（Seeed 授权分销）](https://www.makerfabs.com/sensecap-m2-multi-platform-lorawan-indoor-gateway-sx1302.html) | ⭐ 性价比最高的入门 8 通道网关 |
| **Seeed SenseCAP M2 Multi-Platform（SX1302-4G）** | 同上 + 4G LTE 蜂窝回传 | **$149.00 ≈ ¥1073** | [Makerfabs](https://www.makerfabs.com/sensecap-multi-platform-lorawan-indoor-gateway-sx1302-4g.html) | ⭐ **池塘场景推荐**：家里无需宽带也能回传 |
| Seeed SenseCAP M1（Helium 热点） | 室内 Helium 热点 | 需询价确认 | https://www.seeedstudio.com/ | 官方 store 被反爬；Helium 热点商业模式已变化，**不建议新项目选用** |
| Seeed SenseCAP M2 Light Hotspot | 室内 Light Hotspot + 软件许可 | 需询价确认 | https://www.seeedstudio.com/SenseCAP-M2-Light-Hotspot-and-Software-License.html | 页面价格为 JS 渲染 |
| **DFRobot LoRaWAN 室内网关（915MHz）** | 8 通道，SX1302，覆盖达 4 公里 | **¥1050.00** | [DFRobot 创客商城](https://www.dfrobot.com.cn/goods-4246.html) | 国内现货，人民币定价明确 |
| **DFRobot LoRaWAN 室内网关（868MHz）** | 8 通道，SX1302 | **¥1050.00** | [DFRobot 创客商城](https://www.dfrobot.com.cn/goods-4247.html) | ⚠️ **868MHz 版本在中国大陆受限**（见第 8 节），仅建议实验用 |
| DFRobot LoRaWAN ESP32-S3 开发板 | LoRaWAN 节点，ESP32-S3 | **¥129.00** | [DFRobot 创客商城](https://www.dfrobot.com.cn/goods-4255.html) | 节点端备选 |
| DFRobot LoRaWAN 控制终端（915/868MHz） | 数据采集 + 设备控制 | **¥249.00** | [DFRobot 创客商城](https://www.dfrobot.com.cn/goods-4267.html) | 节点端备选 |

**汇率说明**：$99 ≈ ¥713、$149 ≈ ¥1073（按 1 USD ≈ 7.2 CNY，未含关税与运费）。

---

## 11. 未找到可靠来源 / 需询价确认清单

> 以下项目本次**未能从可靠来源取得确切价格**，明确标注为「需询价确认」，**报告正文未对它们做任何价格推测**。

### 11.1 需询价确认 —— 模块/开发板

| 型号 | 状态 | 询价入口 |
|---|---|---|
| **Heltec WiFi LoRa 32 V3 官方人民币价** | 仅取到 Amazon 第三方跨境价（HKD 313.53 ≈ ¥288）；**官方 heltec.org 与淘宝价格 JS 渲染未抓到** | https://heltec.org/project/wifi-lora-32-v3/ ／ 淘宝「Heltec 官方店」 |
| Heltec WiFi LoRa 32 V2 官方人民币价 | 仅取到 Tindie $30（卖家暂停营业）；国内价未确认 | https://heltec.org/ |
| **亿佰特 E32-433T20D** | 立创商城（JS）与 RobotShop（Cloudflare 403）均拦截 | https://item.szlcsc.com/3364203.html |
| E22-400M22S / E22-400T22S 等其他 E22 型号 | 立创价格需登录 | https://list.szlcsc.com/catalog/11223.html |
| **微雪 Waveshare 官方人民币价（全线）** | 微雪中文站 www.waveshare.net 价格为 JS 渲染，fetch 返回空 | https://www.waveshare.net/ ／ 微雪淘宝官方店 |
| Waveshare SX1262 868/915M LoRaWAN HAT（含吸盘天线） | 同上 | https://www.waveshare.net/shop/SX1262-868-915M-LoRaWAN-HAT.htm |
| Waveshare SX1262 LoRa HAT 人民币价 | 仅取到 Sunsky 第三方转售 ¥157.72（从商品标题抓取），**非官方价** | https://www.sunsky-online.com/zh_TW/p/ZY23043811/Waveshare-16806.htm |

### 11.2 需询价确认 —— 天线

| 型号/类型 | 状态 | 询价入口 |
|---|---|---|
| 433MHz 弹簧天线（2dBi） | 淘宝/立创价格 JS 渲染 | https://list.szlcsc.com/catalog/11223.html |
| 433/470MHz 吸盘天线（3/5/6/8/12dBi） | 京东价格 JS 渲染，**未取到任何确切价格** | [京东 470MHz 吸盘天线聚合页](https://popseo.jd.com/chanpin/2589848.html) |
| **433MHz 玻璃钢全向天线（5/8/10dBi，室外抱杆）** | **完全未找到可靠的人民币来源** | 建议直接询价：亿佰特 https://www.ebyte.com/product/antenna-case7.html |
| 470MHz 玻璃钢全向天线 | 同上 | https://www.ebyte.com/product/antenna-case8.html |
| 馈线 RG58 / RG174 / LMR400 | 未找到可靠来源 | 建议询价 |
| 馈线避雷器 / 防雷器（户外必需） | **未找到可靠来源** | ⚠️ 户外池塘立杆天线**必须配防雷**，请单独询价 |

### 11.3 需询价确认 —— 网关

| 型号 | 状态 | 询价入口 |
|---|---|---|
| **Dragino LPS8 / LPS8N（非 v2 基础版）** | 官方页无定价；分销商全部 403 | https://www.dragino.com/products/lora-lorawan-gateway.html |
| Dragino LPS8v2 **4G 版本** | 仅取到非 4G 版 ¥1482.12 | 询价深圳凌创辉：0755-83216080 / SALES@LJQ.CC |
| RAK7268 **4G / LTE 版本（RAK7268CV2）** | 仅取到非 4G 版 ¥1439.93 | https://store.rakwireless.com/ |
| RAK WisGate Edge Lite（RAK7248） | 未取到 | https://store.rakwireless.com/ |
| **Seeed SenseCAP M1** | 官方 store 被反爬 | https://www.seeedstudio.com/ |
| Seeed SenseCAP M2 Light Hotspot + 软件许可 | 价格为 JS 渲染 | https://www.seeedstudio.com/SenseCAP-M2-Light-Hotspot-and-Software-License.html |
| Seeed SenseCAP M2 4G 官方美元价 | 仅取到 Makerfabs 分销价 $149.00 | https://www.seeedstudio.com/ |

### 11.4 需复核的规格数据

| 项目 | 说明 |
|---|---|
| SX1276 / SX1262 的 datasheet 精确数值（灵敏度、RX/TX 电流） | **本次抓取工具无法解析 PDF**，Semtech 官方 datasheet 与 alldatasheet 镜像均返回 403 或 unsupported content type。表中数值为业界通用标称值，**请以官方 datasheet 原文为准**：https://www.semtech.com/products/wireless-rf/lora-connect/sx1262 |
| The Things Network LoRaWAN 频率参数页 | 返回 404，SF/BW 参数建议以 Semtech datasheet 与 LoRa Alliance 规范复核 |
| 技象科技技术博客正文 | www.techphant.cn 为 JS 渲染，仅取到标题，**未取到正文数据** |
| 52 号公告附件 PDF 原文 | miit.gov.cn 附件为 application/pdf，本次工具不支持解析；**具体限值已通过 SRRC 认证服务中心页面（https://www.srrc.net.cn/faq/135.html）取得并交叉验证** |

---

## 附录：本次调研的关键结论速览

| 问题 | 结论 |
|---|---|
| 芯片选哪个？ | **SX1262 / SX1268**（低 RX 电流、+22dBm、QFN 4×4、官方工具链） |
| 中国用哪个频段？ | **433.05–434.79 MHz，功率 ≤10 mW e.r.p**；或 470–510MHz（限民用计量仪表，≤50mW，单次 ≤1s）。**868MHz 限 5mW 且占空比 ≤1%（不可用）；915MHz 不合法** |
| 需要 LoRaWAN 网关吗？ | **一对一透传不需要**。多节点/标准 LoRaWAN 才需要 |
| 透传最低成本？ | 2×Ra-02 批量（¥25.12/个）≈ **¥50.25 + 天线**；或 2×微雪 USB-to-LoRa ≈ **¥230–260** 即插即用 |
| 网关最便宜？ | **Seeed SenseCAP M2 $99 ≈ ¥713**（Makerfabs）；国内现货 **DFRobot ¥1050**；4G 版 SenseCAP M2 **$149 ≈ ¥1073** |
| 池塘↔家 1–2km 可行吗？ | **完全可行**。+20dBm/SF12/BW125 链路预算 171dB，实际郊区 1–3km 稳定。**关键是把"家里"那端天线架高，而不是加大功率** |
| 最大的合规风险 | **市面上绝大多数 LoRa 模块（18–30dBm）在中国 433MHz 下都超出 10mW 限值**。务必用软件把功率降到 ≤10dBm；52 号公告第四条明确禁止加装功放和擅自更换天线 |
