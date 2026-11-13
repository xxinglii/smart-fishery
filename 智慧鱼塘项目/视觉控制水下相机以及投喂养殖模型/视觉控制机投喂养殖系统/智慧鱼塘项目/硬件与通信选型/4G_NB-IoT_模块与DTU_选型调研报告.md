# 中国户外池塘 ESP32 物联网监测系统 —— 4G Cat-1 / Cat-4 / NB-IoT 通信模块与 DTU 选型调研报告

> 调研时间：2026 年（报告内所有链接均为本次调研实际抓取或搜索结果中出现的页面）
> 调研方式：web_search + web_fetch 真实联网检索，覆盖中文与英文来源
> **价格声明：本报告只记录「实际抓取到的页面文本中出现的价格」。凡是抓不到明码标价的，一律标注「需询价确认」，绝不做估算填充。**

---

## 0. 结论速览（TL;DR）

| 结论 | 说明 |
|---|---|
| **量产、无语音/无定位需求 → 合宙 Air780E / Air780EX** | 16×18×2.3mm LGA，AT + LuatOS 双开发方式，低功耗模式 <0.5mA，官方文章显示累计出货 2000 万+。Air780EX 为 LCC 邮票孔版本，**手工焊接友好**，适合小批量自制 |
| **需要 GPS/北斗 → Air780EG** | Cat.1 + GNSS 二合一 |
| **不想画板 → 有人 USR-DR154（Cat-1 导轨式 DTU）** | 官方商城目录价 **¥98 起**（同系列 DR154=RS485 / DR152=RS232），5~16V 供电，平均功耗 0.8W。是本项目「省掉 PCB + 焊接 + 调试工时」的最优解 |
| **需要 Modbus RTU 转 JSON / 边缘计算 → USR-G780 V2（¥338）** | 支持 Modbus RTU 透传上报，官方 FAQ 有现成示例 |
| **绝对不要选 NB-IoT 做新项目** | 2024 年 NB-IoT 模组全球出货同比 **−34%**，Cat 1 bis 同比 **+100%**；NB-IoT 基站约 90 万 vs LTE 约 600 万；且**未找到中国运营商"停止新开通 NB-IoT"的官方公告**（详见 §C） |
| **Air724UG 停产传闻 → 未找到官方 EOL 公告** | 官方资料页仍在维护，官方选型文章截至 2026-03 仍推荐它做语音方案。但已不在合宙主推之列，**新项目不建议选**（详见 §A.1） |

---

## A. 4G Cat-1 裸模块（需自己画板 / 焊接）

### A.1 合宙 Luat 系列

#### A.1.1 Air724UG 生命周期状态（重点核实项）

**调研结论：未找到合宙官方发布的 Air724UG 停产（EOL）/ 停止供货公告。**

我实际核查到的证据：

| 证据 | 内容 | 来源 |
|---|---|---|
| ① 官方资料站仍在线维护 | 合宙模组资料中心 `docs.openluat.com/air724ug/` 打开正常，Air724UG 简介页、LuatOS 固件版本页均在 | [docs.openluat.com/air724ug/](https://docs.openluat.com/air724ug/)、[Air724UG LuatOS 固件版本](https://docs.openluat.com/air724ug/luatos/firmware/) |
| ② 官方选型文章仍推荐 | 合宙官方发布的《选型 4G-Cat.1 模组 Air780E，必须要说的注意事项！》（2026-03-05 同步更新）原文：**"Air780E 不支持 TTS 语音播放，也不支持 VoLTE 语音通话，需要支持这两个功能的应用推荐选择合宙 Air724UG"** | [CSDN 合宙官方文章](https://blog.csdn.net/weixin_60538941/article/details/142750027) |
| ③ 市场仍在流通 | 2026-01-11 淘宝数码网文章：**"Air724UG 合宙 Cat1 4G 模块核心板以 83 元的定价切入市场"** | [淘宝数码网 Air724UG 深度拆解](https://shuma.taobao.com/topic/GSM_1089/966e214ebca08e167af45170630f50b5.html) |
| ④ 但已不在主推序列 | 合宙 2026 年《产品选型指南》主推为 **Air878X 工业模组、Air8201 超低功耗定位模组、Air780EHM、Air8000 SoC** 等，Air724UG 未出现在主推位 | [合宙产品选型指南（文字版）](https://docs.openluat.com/SelectionGuide/SelectionGuide/) |

> ⚠️ **工程建议**：**新项目不要选 Air724UG**。它不在合宙当前主推序列，长期供货风险高。若确需语音（TTS/VoLTE），应向合宙销售书面确认生命周期；否则改用 Air780E / Air780EX。

#### A.1.2 合宙模组参数与价格

| 型号 | 关键参数 | 参考价格(¥) | 来源链接 | 备注 |
|---|---|---|---|---|
| **Air724UG** | Cat-1；支持 TTS 语音播放 + VoLTE 通话；LuatOS / AT | **核心板 ¥83**（第三方文章表述） | [淘宝数码网（2026-01-11）](https://shuma.taobao.com/topic/GSM_1089/966e214ebca08e167af45170630f50b5.html) | 生命周期**未确认**，见 §A.1.1；裸模块单价需询价确认 |
| **Air780E** | Cat-1；**16×18×2.3mm，LGA**；AT + LuatOS 双支持；TCP/UDP、TCP-SSL/TCP-TLS、MQTT、HTTP、WEBSOCKET、NTP；**不支持 TTS/VoLTE**；频段 FDD B1/3/5/8、TDD B34/38/39/40/41；**低功耗模式 <0.5mA**；支持 常规/低功耗/**PSM+** 三种功耗模式；累计出货 2000 万+ | **需询价确认**（未抓到官方明码标价） | [合宙官方选型文章](https://blog.csdn.net/weixin_60538941/article/details/142750027)、[docs.openluat.com/air780e/](https://docs.openluat.com/air780e/) | 官方明确：AT 和 LuatOS 均可实现数据透传；支持 FOTA（差分升级） |
| **Air780EX** | 与 Air780E **封装尺寸完全相同**；**LCC 邮票孔封装，比 LGA 更方便手动焊接**；软件与 Air780E 完全通用；管脚较少且排布略有不同 | **需询价确认** | [合宙官方选型文章](https://blog.csdn.net/weixin_60538941/article/details/142750027) | ⭐ **小批量自制/手焊首选** |
| **Air780EG** | Cat.1 + GNSS 二合一，支持**北斗/GPS 双模卫星定位** | **需询价确认** | [合宙官方微信公众号新品发布](https://mp.weixin.qq.com/s?__biz=MzIwNjgzNDQ5NA==&mid=2247512649&idx=1&sn=2cb9c1883eaf3074e95cd9586cd3729c) | 户外池塘若需定位/防拆，选它 |
| **Air780EP** | 与 Air780E **封装尺寸完全相同**；AT 指令与 Air780E **可完全互替**；功耗表现有差异；LuatOS 二次开发时个别功能/管脚有区别 | **需询价确认** | [合宙官方选型文章](https://blog.csdn.net/weixin_60538941/article/details/142750027) | 官方表述："Air780EP 在功耗和成本方面取得显著优势"（[合宙 CSDN 博客](https://blog.csdn.net/LuatOS/article/details/144718711)） |
| **Air780EPS** | 与 Air780E 同封装；AT 指令可完全互替；**合宙现有模组中低功耗表现最好** | **需询价确认** | [合宙官方选型文章](https://blog.csdn.net/weixin_60538941/article/details/142750027)、[Air780EPS 产品手册](http://docs.openluat.com/air780eps/product/) | ⭐ 电池/太阳能供电场景优先 |
| **Air780EQ** | 与 Air780E 同封装；AT 可完全互替 | **需询价确认** | [合宙官方选型文章](https://blog.csdn.net/weixin_60538941/article/details/142750027) | — |
| **Air780EHM** | 4G Cat-1；LuatOS 二次开发；**16×18×2.3mm，LGA 封装**；8+8 管脚 | **需询价确认** | [合宙产品选型指南](https://docs.openluat.com/SelectionGuide/SelectionGuide/) | 选型指南中标注为「二次开发/通用封装」 |

**关于 PSM / 低功耗的官方口径**（来源：[合宙官方选型文章](https://blog.csdn.net/weixin_60538941/article/details/142750027)）：
> "合宙 4G-Cat.1 模组支持三种功耗模式：**常规模式、低功耗模式、PSM+模式**，可按实际开发需求选择。"
> "Air780E 功耗表现在合宙现有模组中排名中等，**低功耗模式下低于 0.5mA**；低功耗表现最好的模组型号是合宙 **Air780EPS**。"

---

### A.2 移远 Quectel 系列

| 型号 | 关键参数 | 参考价格(¥) | 来源链接 | 备注 |
|---|---|---|---|---|
| **EC200U-CN**（料号 EC200UCNLA-N05-SGNSA） | **LTE Cat 1**；最大下行 **10 Mbps** / 上行 **5 Mbps**；封装 **SMD 31×28mm**（LCC）；工作电压 **3.3~4.3V**；**消耗电流 12uA**（立创参数表）；工作温度 −35~+75℃；接口 PCM/I2C/UART/SPI/USB/ADC；支持 CMUX、音频回放录制 | **需询价确认**（立创商城商品页未显示价格，需登录） | [立创商城 EC200UCNLA-N05-SGNSA](https://item.szlcsc.com/3211414.html) | 封装兼容 EC25/EC21/EC20 R2.1/EC20-CN/EC200T/EC200S/EG25-G/EG21-G/UC200T，支持标准 Mini PCIe 封装 |
| **EC200A** | **LTE Cat 4** 无线通信模块，3GPP Rel.…（立创品牌页描述截断） | **需询价确认** | [立创商城 Quectel 品牌页](https://list.szlcsc.com/brand/1030.html) | — |
| **EC800M**（料号 EC800MCNGB-I05-SGNSA） | 移远 Cat-1 系列（立创归入"射频模块"类目） | **需询价确认** | [立创商城 EC800MCNGB-I05-SGNSA](https://item.szlcsc.com/20529910.html) | — |
| **EC200N-CN**（料号 EC200NCNLA-N05-SNNSA） | LTE Cat 1；封装 **29×32×2mm**（淘宝数码网文章描述） | **需询价确认** | [嘉立创 SMT 商城 EC200N](https://www.jlc-smt.com/lcsc/detail/C2874887.html)、[淘宝数码网 EC200N 介绍](https://shuma.taobao.com/topic/GSM_1089/f11cdc63c8376ef2f59a22f51994d473.html) | 有 GNSS 版本料号 EC200NCNLA-N05-MN0CA（[实物图页](https://item.szlcsc.com/product/jpg_5746134.html)） |
| **EC200U-GNSS 版本** | 移远 EC200U 系列存在 GNSS 料号（如 EC200UCNLA-N05-**SGNSA** 中 "GNSS" 后缀即代表带 GNSS） | **需询价确认** | [立创商城 EC200UCNLA-N05-SGNSA](https://item.szlcsc.com/3211414.html) | 建议向移远/代理确认具体 GNSS 料号 |
| **（价格锚点）龙尚 A7690C-LNXY** | LTE Cat 1；LGA+LCC；**15.7×17.6×2.3mm**；上行最大 5Mbps / 下行最大 10Mbps；3.4~4.2V | **¥20.0000** | [世强硬创平台 A7670C 系列页](https://www.sekorm.com/ai/doc/3957144.html) | ⭐ 这是本次调研中**唯一抓到的 Cat-1 bis 级模组明码标价**，可作为国产 Cat-1 模组价格锚点（移远同类料号零售价通常在同一量级，但**不能直接等价**） |

**移远重要产品变更通知（PCN）**：移远 2025-11-24 发布 PCN202511040006，宣布**不再支持 AT+QSCLKEX 命令**，受影响产品含 EC200A / EC200S / EC200U / EC600N-CN / EG800W-CN / EG800Z / EM05 / EC300F 等。
来源：[世强 PCN 中文版](https://www.sekorm.com/doc/588030475.html) / [英文版](https://www.sekorm.com/doc/588030474.html)

---

### A.3 SIMCom 芯讯通系列

| 型号 | 关键参数 | 参考价格(¥) | 来源链接 | 备注 |
|---|---|---|---|---|
| **SIM7600CE**（Cat-4） | SMT 封装；支持 LTE-TDD/LTE-FDD/HSPA+/TD-SCDMA/EVDO 及 GSM/GPRS/EDGE；**LTE CAT4，下行 150Mbps** | **需询价确认** | [立创商城 SIM7600CE-T](https://item.szlcsc.com/537393.html)、[立创商城 SIM7600CE-L1S 类目页](https://list.szlcsc.com/catalog/11222.html) | — |
| **SIM7600CE-CNSE（4G DONGLE 成品）** | Cat-4 全网通 USB 上网棒，中国频段 | **$45.99**（≈¥330，汇率 7.2 仅供参考）**🚫 DISCONTINUED（已停产）** | [Waveshare 官方产品页](https://www.waveshare.com/SIM7600CE-CNSE-4G-DONGLE.htm) | ⭐ WaveShare 页面原文："**The module of this product has been discontinued, it is recommended to purchase the alternative solution**" |
| **SIM7600G-H** | Cat-4；全球频段；GNSS 定位；下行 150Mbps / 上行 50Mbps；支持 4G/3G/GSM/GPRS/GNSS | **需询价确认** | [M.2 R2 版本 Digi-Key 页面](https://punchouttest.digikey.cn/zh/products/detail/simcom-wireless-solutions-limited/SIM7600G-H-M2-R2/15841455)、[Waveshare SIM7600G-H 4G HAT](https://www.waveshare.com/product/sim7600g-h-4g-hat.htm) | — |
| **A7670C** | **LTE Cat 1**；**LGA+LCC，24×24×2.4mm**（重约 2.8g）；3.4~4.2V；−40~+85℃；下行 10Mbps / 上行 5Mbps；频段 B34/38/39/40/41 + B1/3/5/8；内置 TCP/IP、IPv4/IPv6、MultiPDP、FOTA、LBS、TLS；UART/SPI/I2C/GPIO | **需询价确认**（世强平台显示"价格："为空） | [世强 A7670C 页面](https://www.sekorm.com/ai/doc/3957144.html)、[立创商城 A7670C-MASL](https://item.szlcsc.com/3121754.html) | 生命周期标注 **有效(ACTIVE)**；世强可查料号 A7670C-LANV / A7670C-LANY |
| **A7670E** | Cat-1；LTE-FDD B1/B3/B5/B7/B8/B20 + GSM 900/1800 | **需询价确认** | [LCSC A7670E-LASE](https://www.lcsc.com/product-detail/C5362211.html) | — |
| **A7670G** | LTE Cat 1；LTE-FDD/TDD/GSM/GPRS/EDGE；3.4~4.2V；−40~+85℃；生命周期 **ACTIVE** | **需询价确认** | [世强 A7670G 页面](https://www.sekorm.com/ai/doc/3957144.html) | — |
| **A7690C-LNXY** | LTE Cat 1；LGA+LCC；**15.7×17.6×2.3mm**；上行最大 5Mbps / 下行最大 10Mbps；3.4~4.2V | **¥20.0000** | [世强 A7690C-LNXY](https://www.sekorm.com/product/514793760.html) | 同上，作为价格锚点 |

---

## B. Cat-1 DTU 成品（重点章节 —— 省去画板）

### B.1 有人物联网 USR（官方商城 shop.usr.cn，最权威）

以下价格**全部来自有人物联网官方商城页面导航中的目录价**（页面显示格式为"XX.00 元"），抓取时间：2026 年。

| 型号 | 关键参数 | 参考价格(¥) | 来源链接 | 备注 |
|---|---|---|---|---|
| **USR-DR154 / USR-DR152** | 官方定位：**"口红 DTU / 超小体积导轨式 DTU"**；集成 SIM 卡；**蓝牙配置**；导轨 + 挂耳安装；工作电压 **5~16V**；工作温度 **−25~+75℃**；**平均功耗 0.8W**；生命周期 **ACTIVE** | **¥98.00 起**（官网目录价）<br>世强渠道挂牌 **¥135.7143** | [有人官方商城 Cat-1 DTU](https://shop.usr.cn/cat1-dtu/4glte.html)、[世强 USR-DR154 页](https://www.sekorm.com/ai/doc/520698989.html) | ⭐ **本项目首选**。DR154 = RS485 版本，DR152 = RS232 版本；DR150/DR154-N41/DR152-N41 为同系列料号 |
| **USR-G770** | "4G 边缘 DTU" | **¥138.00** | [有人官方商城 USR-G770](https://shop.usr.cn/cat1-dtu/banjin.html) | — |
| **USR-G771** | Cat-1 终端 | **¥168.00** | [有人官方商城 Cat-1 DTU 分类](https://shop.usr.cn/cat1-dtu/4glte.html) | — |
| **USR-DR502 / USR-DR512** | 导轨式 Cat-1 DTU | **¥168.00** | [有人官方商城](https://shop.usr.cn/cat1-dtu/4glte.html) | — |
| **USR-G780s** | **4G 定位版 DTU**（第二代 Smart DTU）；工作电压 **9~36V**；**平均电流 81mA@12V**（≈0.97W）；工作温度 −25~+75℃；生命周期 **ACTIVE**；支持链接 MQTT 服务器；支持 GNSS 定位上报 | **¥238.00**（官网目录价）<br>世强渠道挂牌 **¥274.2858** | [有人官方商城](https://shop.usr.cn/cat1-dtu/4glte.html)、[世强 USR-G780S 页](https://www.sekorm.com/ai/doc/520698989.html)、[官方 FAQ：G780s 链接 MQTT](https://www.usr.cn/Faq/1630.html)、[官方 FAQ：G780s GNSS 定位](https://www.usr.cn/Faq/1687.html) | ⭐ 需要定位功能时的 DTU 方案 |
| **USR-G780 V2** | "边缘采集 4G DTU"；**支持 Modbus RTU 透传上报（JSON）** | **¥338.00** | [有人官方商城](https://shop.usr.cn/cat1-dtu/4glte.html)、[官方 FAQ：G780 V2 Modbus RTU 透传上报示例](https://www.usr.cn/Faq/2125.html) | ⭐ 本项目**推荐**：Modbus RTU → JSON 上报有官方现成示例 |
| **USR-M100** | 边缘计算网关 | **¥388.00** | [有人官方商城](https://shop.usr.cn/cat1-dtu/4glte.html) | — |
| **USR-N720-C1** | 边缘数采网关（4G 版） | **¥398.00** | [有人官方商城](https://shop.usr.cn/cat1-dtu/4glte.html) | 多路采集场景 |
| **USR-G781** | "带网口的 4G DTU" | **¥468.00** | [有人官方商城](https://shop.usr.cn/cat1-dtu/4glte.html) | 需要以太网口时选它 |
| **USR-G776** | 第二代 4G DTU；9~36V；**72mA@12V**；待机平均 65mA@12V；−25~75℃；生命周期 ACTIVE | 世强渠道挂牌 **¥285.7143** | [世强 USR-G776 页](https://www.sekorm.com/ai/doc/520698989.html) | 官网商城当前目录未列出 |
| **USR-DR404** | 🚫 **未在有人官方商城当前目录中找到该型号** | **需询价确认 / 可能已停产** | [有人官方商城 4G DTU 全类目](https://shop.usr.cn/cat1-dtu/4glte.html) | 未找到可靠来源证实其生命周期状态 |

**有人官方促销信息**：有人物联网官网新闻《有人全系 4G CAT.1 DTU 送 8 年流量》——[https://www.usr.cn/News/1908.html](https://www.usr.cn/News/1908.html)
（注：该新闻页本次抓取返回 HTTP 500，但链接来自搜索引擎真实索引，建议自行打开核对活动有效期。）

**有人 USR-G780s/G771/DR5X2/DR15X 系列产品规格书（数据手册）**：[世强 USB-G780s 规格书 PDF 下载页](https://www.sekorm.com/doc/520698989.html)
> 规格书原文摘要："设备出厂即**赠送每月 100M 流量**，支持通过手机扫码进行快速添加与配置，并可利用有人云实现在线参数定制。"

---

### B.2 亿佰特 Ebyte

| 型号 | 关键参数 | 参考价格(¥) | 来源链接 | 备注 |
|---|---|---|---|---|
| **E840-DTU(4G-01)** | 4G DTU，RS485/232 透传，全网通 CAT1，支持 MQTT / Modbus 网关 | **需询价确认**（京东商品页未渲染价格；官网产品页无标价） | [京东商品页](https://ic-item.jd.com/10091360631652.html)、[亿佰特官网 4G DTU 类目](https://www.ebyte.com/product/4G-DTU.html) | 亿佰特官网商城（ebyte.com）不公布价格，仅提供「样品购买」跳转天猫 |
| **E840-DTU(EA01)** | 亿佰特 4G DTU 系列 | **需询价确认** | [亿佰特 4G DTU 类目](https://www.ebyte.com/product/4G-DTU.html)、[ebyteiot.com 搜索 "E840-DTU"（5 个结果）](https://ebyteiot.com/search?q=E840-DTU) | — |
| **E840-TTL(4G02-DNE)** | 4G 模块 DTU，TTL 接口，兼容 GPRS/3G，全网通，**支持 MQTT** | **需询价确认** | [京东商品页](https://ic-item.jd.com/69259760486.html) | 裸板 TTL 版本 |
| **亿佰特 RS485 嵌入式全网通 DTU 网关 LTE** | 引线式电源，RS485 | **需询价确认** | [京东商品页](https://ic-item.jd.com/10022890784715.html) | — |

> 📌 **亿佰特渠道说明**：亿佰特官网（ebyte.com）产品页只给参数不给价格，购买统一跳转天猫旗舰店；国际站 ebyteiot.com 为 Shopify 商城（美元计价，本次抓取搜索结果页返回 5 条 E840-DTU 结果但未渲染价格明细）。**结论：亿佰特全系 DTU 需要到店询价。**

---

### B.3 其他品牌 DTU

| 型号 | 关键参数 | 参考价格(¥) | 来源链接 | 备注 |
|---|---|---|---|---|
| **塔石 TAS-LTE-211 / TAS-LTE-212 / TAS-LTE-360 系列** | 4G 导轨式 DTU，支持移动 2G/4G，4G LTE 高速传输 | **需询价确认** | [塔石官网 4G 导轨式 DTU](https://www.tastek.cn/product/163777)、[塔石 TAS-LTE-360/363/364/393/395](https://www.tastek.cn/product/163775) | 塔石官网不公布价格 |
| **正点原子 ATK-M751 / ATK-M751C（Cat1 DTU）** | 全网通 4G，RS232/485 串口数据透传 | **需询价确认**（官方仅给淘宝店链接） | [正点原子资料中心 ATK-M751](http://openedv.com/blog/docs/modules/iot/atk-dtuone.html)、[采购公告提及 ATK-M751C](https://wap.qianlima.com/zb/detail/20241204_468544795.html) | 官方购买渠道：`openedv.taobao.com` |
| **正点原子 D40 Mini 4G Cat1 DTU** | 4G Cat1 数传，Mini 尺寸 | **需询价确认** | [正点原子 D40 Mini 文档](http://www.openedv.com/docs/industry/1-iot/DTU/Mini_D43.html) | — |
| **（价格锚点）艾莫迅 4G DTU 透传模块** | RS485/232 转 4G，支持标准 AT 指令和 TCP/UDP 透传，适配 PLC | **¥129**（第三方文章表述） | [淘宝数码网（2026-07-04）](https://shuma.taobao.com/topic/GSM_1089/a6c5b7b1bce9b57c5dd64284e6bf978f.html) | 白牌/小品牌，仅作低价区间参考 |
| **银尔达 Air724 系列 DTU / RTU** | RTU 全网通基站定位，4 路继电器控制核心板 | **需询价确认** | [淘宝数码网相关文章](https://shuma.taobao.com/topic/GSM_1089/ec27e0c1fc2082003473ce2ee7ba2712.html) | 银尔达基于合宙 Air724/Air780 平台的成品板 |

---

### B.4 ⭐ 裸模块方案 vs DTU 成品方案 —— 总成本对比

> **成本口径说明**：下表「DTU 价格」为**实际抓取到的官方目录价**；「隐形成本」为工程经验估值，**已在表中明确标注为估算**，不属于检索所得的价格数据。

以**单节点**（1 个池塘监测点）为单位，按 **10 台小批量**估算：

| 成本项 | 方案 1：Air780EX 裸模块自研 | 方案 2：USR-DR154 成品 DTU |
|---|---|---|
| 通信模块/整机 | Air780E/EX 模块：**需询价确认**（参考同级别 Cat-1 bis 模组锚点 ¥20.00） | **¥98.00**（官方目录价，含外壳/SIM 卡座/端子/天线座） |
| 天线 + IPEX 转接 + 4G 胶棒天线 | 约 ¥10~25（估算） | 通常**随机附带**（需向卖家确认） |
| SIM 卡座 + 电源电路（DCDC/LDO + 大电容） | 约 ¥8~20（估算） | 已集成 |
| RS485 收发器（如 SP3485/MAX485）+ 防雷 TVS | 约 ¥5~15（估算） | 已集成 |
| ESD/浪涌防护、看门狗、电平转换 | 约 ¥10~20（估算） | 已集成（厂商标称"内置独立硬件看门狗，提高防护等级"） |
| **PCB 打样**（嘉立创 5 片 2 层，含运费） | 约 ¥30~80（估算） | ¥0 |
| **SMT 贴片/焊接**（LGA 封装需钢网+回流焊） | 约 ¥100~300 起（估算，含钢网） | ¥0 |
| **硬件调试工时**（射频匹配、天线调谐、电源纹波、EMC） | **约 3~10 人天**（估算） | ¥0 |
| **软件/固件工时**（AT 指令集成 / LuatOS 开发、MQTT 对接、Modbus） | 约 3~10 人天（估算） | 约 0.5~2 人天（现成配置工具，[Modbus RTU→JSON 有官方示例](https://www.usr.cn/Faq/2125.html)） |
| **小批量 10 台合计硬件 BOM** | 约 ¥28~50/台（估算，仅物料） | **¥98/台**（明码标价） |
| **项目一次性工程投入** | **约 ¥250~600 + 6~20 人天**（估算） | **≈ ¥0 + 0.5~2 人天** |
| 量产 1000 台时单台物料 | 显著更低（估算 ¥25~45） | ¥98（可能有批量折扣，需询价） |
| **适用结论** | 仅当**量产 ≥ 数百台**且团队有射频/EMC 能力时才划算 | ⭐ **本项目的正确选择**：户外池塘场景节点数少（个位数~几十），DTU 溢价（约 ¥50~70/台）远低于自研的一次性工程投入 |

**关键工程判断**：
- 本项目是 **ESP32 + 传感器 + 户外池塘**，节点数少、环境恶劣（潮湿、雷击、温差）。**DTU 的工业级防护、宽压供电、现成外壳和防水设计，其价值远超 ¥98 的标价。**
- 自研方案的**真正成本不是 BOM，而是射频调试 + EMC + 防水外壳模具**。用小批量节点数去摊这部分成本，单位成本会高得离谱。
- **推荐架构**：`ESP32（本地采集/控制）+ RS485/Modbus → USR-DR154（¥98，RS485 版）→ MQTT/HTTP → 云平台`
  - 若传感器是 Modbus RTU 且希望云端直接拿到 JSON → 换 **USR-G780 V2（¥338）**，官方有 [Modbus RTU 透传上报示例](https://www.usr.cn/Faq/2125.html)
  - 若需要定位/防拆 → **USR-G780s（¥238）**

---

## C. NB-IoT

### C.1 模组价格与生命周期

| 型号 | 关键参数 | 参考价格(¥) | 来源链接 | 备注 |
|---|---|---|---|---|
| **移远 BC26** | NB-IoT（LTE Cat NB1/Cat NB2 多频段）；尺寸紧凑、功耗超低 | **需询价确认** | [世强 BC26 数据手册页](https://www.sekorm.com/doc/2181757.html) | 与 BC260Y-CN / BC28 / BC25 有**兼容设计手册**：BC260Y-CN&BC2x&M26 兼容设计手册（2020-09-08），说明移远把 BC260Y 作为 BC26 的延续型号 |
| **移远 BC260Y-CN** | NB-IoT；尺寸紧凑、功耗超低；支持中国电信 IoT/AEP 平台、中国联通雁飞·格物 DMP 平台 | **需询价确认** | [世强 BC260Y-CN 数据手册](https://www.sekorm.com/doc/3570339.html)、[立创商城 BC260YCNFA-I03-CNASA](https://item.szlcsc.com/6127547.html)、[云汉芯城 BC260YCNFA](https://www.ickey.cn/detail/1003001025189310/BC260YCNFA-I03-CNASA.html) | 生命周期状态：**未找到官方停产公告**；BC26 与 BC260Y 的区别见 [CSDN 对比文](https://blog.csdn.net/zhengmilian5572/article/details/125097924) |
| **移远 BC28** | NB-IoT；与 BC26/BC260Y/BC25 封装兼容 | **需询价确认** | [立创商城 BC28CNVBA-I01-CNASA](https://item.szlcsc.com/product/jpg_5771529.html)、[世强 BC260Y 兼容设计手册](https://www.sekorm.com/doc/595853703.html) | 有 BC28-F 版本（支持联通雁飞平台）、BC28（宽压）版本 |
| **移远 BC25 / BC25B5 / BC95-CNV** | NB-IoT 系列 | **需询价确认** | [立创商城（BC25PB-04-BT 等相似推荐）](https://item.szlcsc.com/3211414.html) | — |
| **有人 USR-NB73（WH-NB73-B5）** | NB-IoT 模块，**DIP-24 封装** | **需询价确认** | [深圳沅竞成 WH-NB73-B5](https://www.szyjc.com/product/C009338786)、[有人官网 NB-IoT 模块页（抓取返回 500）](https://www.usr.cn/Product/211.html) | — |
| **有人 USR-NB75（WH-NB75-BA）** | NB-IoT 模块，**DIP-24 封装**，由 USR（有人物联网）设计生产 | **需询价确认** | [深圳沅竞成 WH-NB75-BA](https://www.szyjc.com/product/C010169363) | 页面标注"可查看实时库存、阶梯价格、发货交期"，但价格需登录 |

**NB-IoT 模组停产结论**：**未找到移远 BC26 / BC260Y / BC28 的官方 EOL 公告。** 但见 §C.2 的市场数据——整个 NB-IoT 品类出货量正在快速萎缩。

---

### C.2 ⚠️ NB-IoT 在中国的实际可用性（2024–2026 权威佐证）

#### C.2.1 市场数据：NB-IoT 正在被 Cat 1 bis 取代

| 数据点 | 数值 | 来源 |
|---|---|---|
| 2024 年全球蜂窝物联网模组出货 | 同比 **+10%** | Counterpoint Research |
| **2024 年 Cat 1 bis 出货** | 同比 **+100%**（增长最快品类） | Counterpoint Research |
| **2024 年 NB-IoT 出货** | 同比 **−34%** | Counterpoint Research |
| 2024 年标准 Cat 1 出货 | 同比 **−51%** | Counterpoint Research |
| 2023 年 NB-IoT 出货 | 从接近 **1 亿片** 骤降至 **7000 万片**（因 2500 万件智能门磁应用消失） | 物联传媒/智能通信定位圈 |
| 2024 年 NB-IoT 出货继续下滑原因 | ① 水表/燃气表智能化需求放缓；② **烟雾报警器市场逐步切换到 Cat.1** | 物联传媒/智能通信定位圈 |
| 2025 年预测 | NB-IoT 年出货量**继续下降**，最终稳定在 **5000 万片** 水平，主要靠智能水表/燃气表 | 物联传媒/智能通信定位圈 |
| 2025 Q3 | Cat 1 bis 在模组出货量中占比**接近 50%** | Counterpoint Research |
| 2025 全年预测 | LTE Cat.1 bis 将占全球蜂窝物联网模组出货量的 **63%**（TSR 预测） | TSR |
| 2025 年中国市场 | Cat 1 bis 占蜂窝模组市场 **36%** 份额 | 行业白皮书引用 |

**来源链接**：
- [EET China《Cat1bis 同比增长 100%！中国厂商霸榜全球前五》（2025-03-04，转载 Counterpoint 报告）](https://www.eet-china.com/mp/a386391.html)
- [物联网世界《NB-IoT 退网可能性引发热议！》（物联传媒/智能通信定位圈）](https://mobile.iotworld.com.cn/View.aspx/News-528181f8268980f2)
- [CSDN AI 硬件创业社区《Cat.1 bis 迎来黄金时代！替代传统 Cat.1 与 NB-IoT 的蜂窝物联网新悍将硬核实测》（2026-06-16）](https://aiot.csdn.net/6a7b0142662f9a54cb9b3a27.html)
- [EET China《这 4 家国产通信模组厂商，霸占 65% 全球市场！》](https://www.eet-china.com/mp/a496804.html)
- [物联网世界同文](https://mobile.iotworld.com.cn/View.aspx/News-52931d01a505a82a)
- [iot101《Cat 1 bis 和 RedCap/eRedCap，蜂窝物联网的分化升级路径》](https://www.iot101.com/news/10452.html)

#### C.2.2 网络覆盖：NB-IoT 基站数量远少于 LTE

> 原文引用（[物联网世界](https://mobile.iotworld.com.cn/View.aspx/News-528181f8268980f2)）：
> "**运营商 NB-IoT 基站数大约为 90 万，与 LTE 现网 600 万基站数差距甚大**，意味着在网络覆盖方面具有显著差距，并且 **NB-IoT 很难有机会继续大范围扩大网络覆盖**。"

这一点对**户外池塘**场景尤其致命：池塘通常位于城郊/农村，LTE 覆盖本就偏弱，NB-IoT 的覆盖差距会更明显。

#### C.2.3 资费：NB-IoT 已低到"几毛钱/年"

> 原文引用（[物联网世界](https://mobile.iotworld.com.cn/View.aspx/News-528181f8268980f2)）：
> "NB-IoT 接入终端产生的数据流量极少，每一连接直接带来的连接收入并不高。正如现在，**单个 NB 模组每年的资费只有几毛钱了**。"

**对照：4G Cat.1 物联网卡年费**
| 项目 | 数值 | 来源 |
|---|---|---|
| 联网门锁 4G Cat.1 物联网卡年费 | **约 ¥10/锁/年** | [KEENZY 中科易安《门锁流量费怎么算：4G Cat.1 年费构成与成本测算》（2026-04-29）](https://www.zhongkeyian.com/insights/blog/lock-4g-sim-cost-analysis) |
| 典型门锁日均流量 | 约 1.6 KB/天；年均约 576 KB | 同上 |
| 5000 把锁 3 年 TCO 中流量费占比 | 约 8%~12% | 同上 |
| 有人 DTU 出厂赠送流量 | **每月 100M**（随设备赠送） | [世强 USR-G780s 系列规格书](https://www.sekorm.com/doc/520698989.html) |

#### C.2.4 运营商频谱动向（2025）

| 事件 | 内容 | 来源 |
|---|---|---|
| 中国移动申请重耕 2G/3G/4G 频段用于 5G（2025-01） | **B8 频段（2×15MHz）**：目前 4G 用 2×10MHz、2G 用 2×4MHz、**NB-IoT 仅占 2×1MHz**；2025 年 2G 退网后空出的 2×4MHz 拟用于 5G（申请重耕的重头戏） | [新浪财经（2025-01-07）](https://finance.sina.cn/2025-01-07/detail-ineeeant1419103.d.html)、[通信人家园论坛讨论](http://www.txrjy.com/forum.php?mod=viewthread&tid=1366530) |
| 政策仍支持 NB-IoT | 2024 年工信部《关于推进移动物联网"万物智联"发展的通知》提出，**到 2027 年 5G NB-IoT 网络将实现重点场景深度覆盖** | [物联网世界](https://mobile.iotworld.com.cn/View.aspx/News-528181f8268980f2) |
| 海思新一代 NB-IoT | 2024 年海思发布新一代 NB-IoT 解决方案，与利尔达、中移物联、九联科技、杭州佰鹿及金卡智能、威星智能开启 NB-IoT 模组 & OpenCPU 合作 | 同上 |
| 海外反面案例 | **AT&T 已停止销售 NB-IoT 数据套餐和认证 NB-IoT 设备，着手在美国全面停用其 NB-IoT 网络**，寻求 5G RedCap 等替代方案 | [EET China / Counterpoint](https://www.eet-china.com/mp/a386391.html) |

#### C.2.5 🚫 关于"是否已停止新开通 NB-IoT"—— 诚实结论

> **本次调研未找到任何中国三大运营商"停止新开通 NB-IoT 业务"的官方公告、招标公告或权威媒体报道。**
> 相反，**2024 年工信部文件仍在规划 NB-IoT 到 2027 年的发展**。
> 因此：**"中国运营商已停止新开通 NB-IoT"这一说法，本次调研无法证实，不应作为选型依据。**
> 但**已被证实**的是：NB-IoT **模组出货量大幅萎缩（2024 年 −34%）**、**基站数仅为 LTE 的 1/6.7**、**应用场景快速被 Cat 1 bis 蚕食**。这三点已足以否掉 NB-IoT 用于本项目。

#### C.2.6 NB-IoT 技术劣势

| 维度 | NB-IoT | Cat-1 / Cat-1 bis | 来源 |
|---|---|---|---|
| 设计定位 | 静止/极低速终端，**不支持移动性/小区切换** | 支持移动性与切换 | 3GPP Cat-NB 规范（通用工程共识） |
| 语音 | **不支持** | Cat-1 部分型号支持 VoLTE（如 Air724UG） | [合宙官方选型文章](https://blog.csdn.net/weixin_60538941/article/details/142750027) |
| 时延 | 报告中引述为 **10~30 秒** | 引述为 **1~3 秒** | ⚠️ 来源为[淘宝数码网技术文](https://shuma.taobao.com/topic/GSM_1089/966e214ebca08e167af45170630f50b5.html)，**属二手来源，数值仅供量级参考** |
| 穿透/覆盖 | 密集金属环境穿透损耗比 Cat1 高 3~5dB；基站数 90 万 vs LTE 600 万 | LTE 600 万基站 | ⚠️ 穿透损耗来源同上（二手）；基站数来源为[物联网世界](https://mobile.iotworld.com.cn/View.aspx/News-528181f8268980f2)（权威） |
| 传输速率 | Cat-NB2 理论上行约 159 kbps / 下行约 127 kbps | 下行 10 Mbps / 上行 5 Mbps | 3GPP 规范（通用工程共识） |
| 运营商配置 | 通常需 APN/白名单报备（**本次未找到权威来源，需向运营商确认**） | 标准 4G 卡即插即用 | — |

---

## D. 工程结论素材：五种通信方式对比

> ⚠️ **数据来源标注规则**：标 ✅ 的为本次抓取到的有来源数据；标 🔶 的为**工程经验估值/通用规范值**，已在单元格内注明，不作为检索结论。

| 对比维度 | **4G Cat-1 / Cat-1 bis** | **4G Cat-4** | **NB-IoT** | **LoRa** | **WiFi (ESP32 内置)** |
|---|---|---|---|---|---|
| **模组成本** | ✅ 锚点：龙尚 A7690C-LNXY **¥20.00**（[世强](https://www.sekorm.com/product/514793760.html)）<br>合宙 Air780E/Air780EX：需询价 | ✅ SIM7600CE-CNSE 上网棒 **$45.99 且已停产**（[Waveshare](https://www.waveshare.com/SIM7600CE-CNSE-4G-DONGLE.htm)）；裸模块需询价 | 需询价（BC26/BC260Y/BC28 均未抓到明码标价） | ✅ 立创商城有 LoRa 模块专区（SX1278 等），价格见 [list.szlcsc.com/catalog/11223.html](https://list.szlcsc.com/catalog/11223.html) | ✅ **¥0**（ESP32 内置 WiFi，无额外模组成本） |
| **成品 DTU/网关成本** | ✅ **USR-DR154 ¥98 起**（[官方商城](https://shop.usr.cn/cat1-dtu/4glte.html)）；USR-G780 V2 ¥338（Modbus→JSON） | ✅ USR-G781（带网口）**¥468**（[官方商城](https://shop.usr.cn/cat1-dtu/4glte.html)） | ✅ 有人 USR-NB73/NB75 需询价 | ✅ DFRobot LoRaWAN 室内网关（915MHz，8 通道，覆盖达 4 公里）—— [DFRobot 商城](https://mall.dfrobot.com.cn/goods-4246.html)（价格未抓到） | ✅ 户外 AP：有人 AP520X/AP530X 户外 WiFi6 AX3000 双频 AP **¥998**（[官方商城](https://shop.usr.cn/cat1-dtu/4glte.html)） |
| **年流量费** | ✅ **约 ¥10/年/设备**（[中科易安 2026-04](https://www.zhongkeyian.com/insights/blog/lock-4g-sim-cost-analysis)）；有人 DTU 出厂送 **100M/月**（[规格书](https://www.sekorm.com/doc/520698989.html)） | 与 Cat-1 同量级（同为 4G 物联网卡，🔶 需按运营商套餐确认） | ✅ **"只有几毛钱/年"**（[物联网世界](https://mobile.iotworld.com.cn/View.aspx/News-528181f8268980f2)） | ✅ **¥0**（自建网关，走自有以太网） | ✅ **¥0**（走自有/免费 WiFi） |
| **峰值功耗** | 🔶 发射峰值典型 **~2A @ 5V**（合宙 Air724UG 相关文章提及"5V 供电下仍能稳定输出 **2A 峰值电流**"，[来源](https://shuma.taobao.com/topic/GSM_1089/966e214ebca08e167af45170630f50b5.html)，属二手来源） | 🔶 高于 Cat-1（多天线/更高带宽），需查具体模组手册 | 🔶 低于 Cat-1 | 🔶 发射约 100~120mA @ +20dBm（通用规范值） | 🔶 发射峰值约 240mA（ESP32 通用规范值，本次未找到抓取来源） |
| **平均功耗** | ✅ **USR-DR154 平均功耗 0.8W**（[世强](https://www.sekorm.com/ai/doc/520698989.html)）<br>✅ **USR-G780S 平均电流 81mA@12V ≈ 0.97W**（同上）<br>✅ Air780E **低功耗模式 <0.5mA**，Air780EPS 更低（[合宙官方](https://blog.csdn.net/weixin_60538941/article/details/142750027)）<br>✅ Cat-1 bis PSM 典型电流 **2.2µA**（移远 EG916Q-GL，[CSDN](https://aiot.csdn.net/6a7b0142662f9a54cb9b3a27.html)） | 高于 Cat-1 | ✅ 极低（NB-IoT 核心卖点） | 🔶 极低（适合电池供电） | 🔶 高（WiFi 保持连接功耗大，不适合电池长期供电） |
| **覆盖范围** | ✅ 复用现有 4G LTE 全网（**LTE 基站约 600 万**，[物联网世界](https://mobile.iotworld.com.cn/View.aspx/News-528181f8268980f2)） | ✅ 同 4G LTE 覆盖 | ✅ **NB-IoT 基站约 90 万**，覆盖显著劣于 LTE，且难以再扩大（同上） | ✅ DFRobot LoRaWAN 室内网关标称**覆盖达 4 公里**（[DFRobot](https://mall.dfrobot.com.cn/goods-4246.html)）；LoRa 适合自建局域网 | 🔶 视 AP 而定，户外 AP 标称可达数百米~公里级（需实地勘测） |
| **单次可传数据量** | ✅ 下行 10Mbps / 上行 5Mbps（Cat-1/Cat-1 bis 规范，[合宙](https://blog.csdn.net/weixin_60538941/article/details/142750027)、[CSDN](https://aiot.csdn.net/6a7b0142662f9a54cb9b3a27.html)） | ✅ 下行 150Mbps / 上行 50Mbps（SIM7600 系列，[Waveshare](https://www.waveshare.com/product/sim7600g-h-4g-hat.htm)） | 🔶 单次载荷极小（数十字节级），受限于 ~20kbps 级带宽与运营商 MTU 限制 | 🔶 受限于空中速率与占空比（通常 ≤51 字节/包） | ✅ 数 Mbps 级 |
| **是否需要自建网关** | ✅ **不需要** | ✅ **不需要** | ✅ **不需要** | ✅ **需要**（LoRaWAN 网关；DFRobot 室内网关型号见上） | ✅ **需要**（AP / 路由器 + 供电 + 回传网络） |
| **移动性支持** | ✅ 支持（4G 原生） | ✅ 支持 | 🔶 不支持/极弱（NB-IoT 设计为静止终端） | 🔶 支持低速移动 | 🔶 支持（有漫游，但切换体验一般） |
| **语音支持** | ✅ Air724UG 支持 TTS + VoLTE（[合宙](https://blog.csdn.net/weixin_60538941/article/details/142750027)） | 🔶 部分型号支持 | ✅ **不支持** | ✅ 不支持 | 🔶 不支持（需额外 VoIP 方案） |
| **生命周期风险** | ✅ 低（Cat 1 bis 2025 年占全球出货 **63%**，[CSDN/TSR](https://aiot.csdn.net/6a7b0142662f9a54cb9b3a27.html)） | 中（Cat-4 出货下滑，标准 Cat 1 2024 年 **−51%**，[EET China](https://www.eet-china.com/mp/a386391.html)） | ✅ **高**：2024 年出货 **−34%**，2023 年从 1 亿片跌到 7000 万片（同上 + [物联网世界](https://mobile.iotworld.com.cn/View.aspx/News-528181f8268980f2)） | 低（自建网络，不受运营商影响） | 低 |

### D.1 本项目（户外池塘 ESP32 监测）推荐矩阵

| 场景 | 推荐方案 | 成本 | 理由 |
|---|---|---|---|
| **有市电/太阳能，节点数 1~20，需云端 MQTT/HTTP** | ⭐ **ESP32 + USR-DR154（RS485 版，¥98）** | 约 ¥98/点 | 免画板、免射频调试、工业级防护、送流量 |
| **传感器为 Modbus RTU，希望云端直接收 JSON** | ⭐ **ESP32 + USR-G780 V2（¥338）** | 约 ¥338/点 | 官方现成 Modbus RTU→JSON 示例 |
| **需要设备定位/防拆报警** | **ESP32 + USR-G780s（¥238）** | 约 ¥238/点 | 内置 GNSS |
| **池塘紧邻房屋，已有 WiFi 覆盖** | **ESP32 内置 WiFi（¥0 通信成本）** | ¥0 | 最省钱，但户外 WiFi 覆盖/稳定性需实测 |
| **多个池塘分散在 1~5 km 内，无蜂窝信号** | **ESP32 + LoRa + 1 个 LoRaWAN 网关** | 模块 + 网关 | 无年费，但需自建网关与供电 |
| **NB-IoT** | ❌ **不推荐** | — | 出货量崩塌、基站覆盖仅 LTE 的 1/6.7、不支持移动性、生态快速萎缩 |

---

## E. ⚠️ 未找到可靠来源 / 需询价确认清单

### E.1 完全未找到价格（必须询价）

| 项目 | 情况说明 |
|---|---|
| 合宙 Air780E / Air780EX / Air780EG / Air780EP / Air780EPS / Air780EQ / Air780EHM **裸模块价格** | 合宙官网、docs.openluat.com、立创商城均未渲染出明码标价；仅有淘宝商品页链接，需登录 |
| **合宙 Air724UG 裸模块价格** | 仅找到「核心板 ¥83」的第三方文章表述，裸模块单价需询价 |
| 移远 **EC200U-CN / EC200A / EC800M / EC200N / EC200U-GNSS** 价格 | 立创商城商品页需登录才显示价格；世强平台该系列"价格："字段为空 |
| SIMCom **SIM7600CE / SIM7600G-H / A7670C / A7670E** 价格 | 世强平台对应料号"价格："字段为空；立创商城需登录 |
| 移远 **BC26 / BC260Y-CN / BC28 / BC25** 价格 | 同上 |
| 有人 **USR-NB73 / USR-NB75** 价格 | 有人官方商城当前导航未列出 NB-IoT 产品线；深圳沅竞成页面价格需登录 |
| **亿佰特 E840-DTU(4G-01) / E840-DTU(EA01) / E840-TTL(4G02-DNE)** 价格 | 亿佰特官网只给参数不给价格；京东商品页未渲染价格 |
| **塔石 TAS-LTE-211 / TAS-LTE-212 / TAS-LTE-360 系列** 价格 | 塔石官网不公布价格 |
| **正点原子 ATK-M751 / ATK-M751C / D40 Mini 4G Cat1 DTU** 价格 | 官方只提供淘宝店链接，未在文档中给价格 |
| **银尔达 Air724 系列 DTU / RTU** 价格 | 仅找到淘宝内容页，无明码标价 |
| **DFRobot LoRaWAN 室内网关（915MHz）** 价格 | 商品页存在（[mall.dfrobot.com.cn/goods-4246.html](https://mall.dfrobot.com.cn/goods-4246.html)），本次未抓到价格文本 |

### E.2 关键事实未找到权威来源

| 事项 | 结论 |
|---|---|
| **合宙 Air724UG 是否已停产（EOL）** | ❌ **未找到合宙官方停产公告**。官方资料页仍在维护，官方选型文章（2026-03 更新）仍推荐其做语音方案。**建议直接向合宙销售确认。** |
| **移远 BC26 / BC28 是否已停产** | ❌ 未找到官方 EOL 公告。移远发布过 BC260Y-CN 与 BC2x/M26 的**兼容设计手册**，暗示 BC260Y 为延续型号，但不等于 BC26 已停产 |
| **中国运营商是否已停止新开通 NB-IoT 业务** | ❌ **未找到任何官方公告或权威报道**。反而找到 2024 年工信部文件仍在规划 5G NB-IoT 到 2027 年的深度覆盖。**该说法不应作为选型依据。** |
| **NB-IoT 是否需要运营商白名单/APN 报备、是否需要企业资质开卡** | ❌ 本次未找到权威来源，需向运营商政企客户经理确认 |
| **中国移动/电信/联通 NB-IoT 具体资费套餐页面** | ❌ 未找到公开的官方资费页面。仅找到行业文章的定性描述（"几毛钱/年"） |
| **有人 USR-DR404 生命周期状态** | ❌ 有人官方商城当前 Cat-1 DTU 目录中**未列出 USR-DR404**。未找到停产公告，需询价/确认 |
| **有人 USR-DR154 是否随机附带天线** | ❌ 官方页面未明确说明，建议下单前确认 |
| **有人"全系 4G CAT.1 DTU 送 8 年流量"活动的有效期与细则** | ⚠️ 官网新闻页 [usr.cn/News/1908.html](https://www.usr.cn/News/1908.html) 本次抓取返回 **HTTP 500**，活动细节需自行打开或咨询客服核对 |
| **ESP32 WiFi 模式的具体功耗数值** | ❌ 本次未抓取到权威来源，报告中标为 🔶 估算值 |
| **NB-IoT vs Cat-1 的时延（10~30s vs 1~3s）与穿透损耗（3~5dB）具体数值** | ⚠️ 来源为淘宝数码网技术文章（二手来源），**仅供量级参考**，建议以 3GPP 规范或模组厂商白皮书复核 |

### E.3 抓取失败 / 无法访问的页面（供后续核查）

| URL | 状态 |
|---|---|
| [https://www.usr.cn/Product/211.html](https://www.usr.cn/Product/211.html)（有人 NB-IoT 模块） | HTTP 500 |
| [https://www.usr.cn/Product/313.html](https://www.usr.cn/Product/313.html)（USR-DR154/DR152 产品页） | HTTP 500 |
| [https://www.usr.cn/News/1908.html](https://www.usr.cn/News/1908.html)（送 8 年流量新闻） | HTTP 500 |
| [https://www.hqchip.com/item/2500387595.html](https://www.hqchip.com/item/2500387595.html)（华秋商城 正点原子 GPRS DTU） | HTTP 404 / 跨域重定向 |
| [https://www.findic.com/search?q=EC200U](https://www.findic.com/search?q=EC200U) | 人机验证拦截 |
| [https://www.ickey.cn/detail/1003001025189310/BC260YCNFA-I03-CNASA.html](https://www.ickey.cn/detail/1003001025189310/BC260YCNFA-I03-CNASA.html)（云汉芯城 BC260Y） | 需登录/人机验证 |
| 立创商城 `item.szlcsc.com` 各商品页 | 价格区需登录才渲染 |
| `www.lcsc.com`（国际站）各商品页 | 价格区需登录才渲染 |

---

## F. 主要来源汇总（可点击）

**模块厂商官方 / 权威文档**
- 合宙模组资料中心：[Air724UG 简介](https://docs.openluat.com/air724ug/) · [Air780E 资料](https://docs.openluat.com/air780e/) · [Air780EPS 产品手册](http://docs.openluat.com/air780eps/product/) · [产品选型指南](https://docs.openluat.com/SelectionGuide/SelectionGuide/) · [合宙公告](https://docs.openluat.com/hezhou_publish/) · [合宙官网](https://www.openluat.com/)
- 合宙官方选型文章：[《选型 4G-Cat.1 模组 Air780E，必须要说的注意事项！》](https://blog.csdn.net/weixin_60538941/article/details/142750027)
- 有人物联网官方商城：[Cat-1 DTU 分类页](https://shop.usr.cn/cat1-dtu/4glte.html) · [4G DTU/USR-G770](https://shop.usr.cn/cat1-dtu/banjin.html) · [有人官网 4G DTU](https://www.usr.cn/Product/176.html) · [G780 V2 Modbus RTU→JSON FAQ](https://www.usr.cn/Faq/2125.html) · [G780s MQTT FAQ](https://www.usr.cn/Faq/1630.html)
- 亿佰特官网：[4G DTU 类目](https://www.ebyte.com/product/4G-DTU.html) · [4G 模组类目](https://www.ebyte.com/product/4G-cat1.html) · [NB-IoT 模组类目](https://www.ebyte.com/product/nbiot.html) · [国际站](https://ebyteiot.com/)
- 塔石官网：[4G 导轨式 DTU](https://www.tastek.cn/product/163777) · [TAS-LTE-360 系列](https://www.tastek.cn/product/163775)
- 正点原子资料中心：[ATK-M751 4G DTU](http://openedv.com/blog/docs/modules/iot/atk-dtuone.html) · [D40 Mini 4G Cat1 DTU](http://www.openedv.com/docs/industry/1-iot/DTU/Mini_D43.html)

**元器件商城（价格/参数）**
- 立创商城：[EC200UCNLA-N05-SGNSA](https://item.szlcsc.com/3211414.html) · [EC800MCNGB-I05-SGNSA](https://item.szlcsc.com/20529910.html) · [A7670C-MASL](https://item.szlcsc.com/3121754.html) · [SIM7600CE-T](https://item.szlcsc.com/537393.html) · [BC260YCNFA-I03-CNASA](https://item.szlcsc.com/6127547.html) · [Quectel 品牌页](https://list.szlcsc.com/brand/1030.html) · [2G/3G/4G/5G 模块类目](https://list.szlcsc.com/catalog/11222.html) · [LoRa 模块类目](https://list.szlcsc.com/catalog/11223.html)
- 世强硬创平台（有 ¥ 报价）：[USR-G780S / DR154 / G776 页](https://www.sekorm.com/ai/doc/520698989.html) · [A7670C/A7670G/A7690C 页](https://www.sekorm.com/ai/doc/3957144.html) · [USR-G780S 购买](https://www.sekorm.com/product/506635010.html) · [USR-DR154 购买](https://www.sekorm.com/product/506634830.html) · [A7690C-LNXY 购买](https://www.sekorm.com/product/514793760.html)
- LCSC 国际站：[A7670E-LASE](https://www.lcsc.com/product-detail/C5362211.html) · [SIM7600CE-L](https://www.lcsc.com/product-detail/C133203.html)
- Waveshare：[SIM7600CE-CNSE 4G DONGLE（已停产）](https://www.waveshare.com/SIM7600CE-CNSE-4G-DONGLE.htm) · [SIM7600G-H 4G HAT](https://www.waveshare.com/product/sim7600g-h-4g-hat.htm)
- 深圳沅竞成：[WH-NB75-BA](https://www.szyjc.com/product/C010169363) · [WH-NB73-B5](https://www.szyjc.com/product/C009338786)
- DFRobot：[LoRaWAN 室内网关（915MHz）](https://mall.dfrobot.com.cn/goods-4246.html)

**行业/市场数据**
- [EET China《Cat1bis 同比增长 100%！中国厂商霸榜全球前五》（Counterpoint 数据，2025-03-04）](https://www.eet-china.com/mp/a386391.html)
- [物联网世界《NB-IoT 退网可能性引发热议！》](https://mobile.iotworld.com.cn/View.aspx/News-528181f8268980f2)
- [CSDN AI 硬件创业社区《Cat.1 bis 迎来黄金时代！》（2026-06-16）](https://aiot.csdn.net/6a7b0142662f9a54cb9b3a27.html)
- [新浪财经《移动此次申请重耕 2G/3G/4G 频段用于 5G》（2025-01-07）](https://finance.sina.cn/2025-01-07/detail-ineeeant1419103.d.html)
- [EET China《这 4 家国产通信模组厂商，霸占 65% 全球市场！》](https://www.eet-china.com/mp/a496804.html)
- [iot101《Cat 1 bis 和 RedCap/eRedCap，蜂窝物联网的分化升级路径》](https://www.iot101.com/news/10452.html)
- [中科易安《门锁流量费怎么算：4G Cat.1 年费构成与成本测算》（2026-04-29）](https://www.zhongkeyian.com/insights/blog/lock-4g-sim-cost-analysis)
- [淘宝数码网《百元级 Cat1 模块真能撑起中国物联网的下沉市场？Air724UG 深度拆解》（2026-01-11）](https://shuma.taobao.com/topic/GSM_1089/966e214ebca08e167af45170630f50b5.html)

---

*报告完 · 所有价格均来自实际抓取的页面文本；未抓到的均已标注「需询价确认」。*
