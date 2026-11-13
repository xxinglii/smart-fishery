# C 类 · 全景枪球联动摄像机 官方规格调研

调研日期：2026-09-19 ｜ 目标市场：中国大陆

**方法论与可信度声明**

- 本文件只记录**实际抓取到的页面内容**或**实际看到的搜索快照**。凡来源未写明的字段一律标注「官方未标注」，不做任何估算或跨型号推断。
- 抓取工具：`web_fetch` + `curl`（完整 HTML）。**海康威视官网 www.hikvision.com 对 `curl` 返回 JS 反爬挑战页（29,184 字节固定长度），对 `web_fetch` 返回可读标题但正文被导航菜单挤占截断**，因此海康数据主要来自：行业媒体参数页（dav01.com）、经销商复刻的官方规格表（jdzj.com）、政府采购中标公告（ccgp.gov.cn，逐字引用官方参数）。
- 大华中国官网技术参数为 AJAX 动态加载，已定位接口 `https://www.dahuatech.com/ajax/product_new/<pid>/2` 并成功取得完整官方参数表。
- **PDF 处理**：`web_fetch` 无法读 PDF，但本环境 `curl` 可下载 PDF 且已装 PyMuPDF，**可本地抽取 PDF 全文**。本文件中来自招标/中标文件 PDF 与厂商规格书 PDF 的参数即由此取得，并已注明来源。
- **海康官网破解**：`hikvision.com/cn` 详情页对 `curl` 返回 JS 反爬挑战页、对 `web_fetch` 因导航超长而正文截断；改用**本机 Playwright + Chrome for Testing 无头渲染**后，成功取得**官网逐字参数表**（见 H3 节 `DS-2SK8C144MH-D/AR(25F1)(P3)`）。这是本文件中证据等级最高的一条。
- **大华中国官网**另有两条独立通道：① 产品页 `/product/info/<pid>.html`；② AJAX 参数接口 `https://www.dahuatech.com/ajax/product_new/<pid>/2`（tab 1=产品概述，2=技术参数，3=尺寸图，4=订货型号）。品类列表页如多摄联动 `/product/lists/2124.html?area=2400`、全景系列 `/product/lists/13.html?area=1655`。
- **宇视中国官网产品页只有卖点、没有规格表**（已对 3 个在售型号页面 grep `焦距/IP6/ONVIF/RTSP/宽动态/28181/变倍` 全部 0 命中），大陆机型的这些字段属实「官方未标注」；已附国际版同架构机型的官方完整规格表作为替代证据并明确标注型号不等同。
- 宇视中国官网产品页只有卖点文案，**不含完整规格表**；其规格以卖点原文为准。
- 价格为**采购/中标单价**或官方渠道标价，均附 URL；无法核验者写「需询价」。

---

## 一、总表

> **术语说明（重要，避免误判）**：海康威视**中文**参数表**从不出现字面 "ONVIF"**，一律写「**开放型网络视频接口**」——这是 ONVIF 在海康中文体系里的官方译名；其国际版规格书则字面写 `ONVIF Profile G/S/T`。大华中文参数表直接写 `ONVIF`（如 `ONVIF（Profile S & Profile G & Profile T）`），TP-LINK 与宇视国际版亦字面写 `ONVIF`。**本表中海康型号的「ONVIF ✔」即依据「开放型网络视频接口」判定。**
> 海康型号的协议三项判据为：`支持协议` 行含 **RTSP** + `接口协议` 行含「**开放型网络视频接口**」与「**GB/T28181协议**」。

| 品牌 | 型号 | 分辨率（全景+细节） | 传感器 / 焦距 | 全景水平视场角 | 红外 / 补光 | 宽动态 | 防护等级 | 光学变倍（细节） | RTSP / ONVIF / GB28181 依据 | 参考价 | 来源 URL |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 海康威视 | **iDS-2SE7C124IW-DB(32X/F1)(S5)**（星光全景枪球） | 全景 400 万（2560×1440）+ 细节 200 万（1920×1080） | 该页未列传感器；焦距【全景】4 mm；【细节】5.9~188.8 mm | **79°**（垂直 42.4°） | 红外：【全景】30 m；【细节】150 m；报警灯 30 m。无暖光/全彩标注 | **120 dB 超宽动态** | **IP66**（来自海康**官方合作伙伴门户** `IP66，抗干扰能力强…符合GB/T17626.2/3/4/5/6四级标准`）；dav01 参数页未列 | **32 倍** | **三者均有**。支持协议行含 `RTSP`；接口协议行含 `开放型网络视频接口`、`GB/T28181协议` | 需询价（页面标「厂家报价：面议」） | https://www.dav01.com/product/2025/05/p364898-parameter.html ｜ IP66 依据 https://partners.hikvision.com/product/detail/3b9b3c1a |
| 海康威视 | **iDS-2SE7C144IW-DB(32X/F1)(S5)**（星光全景枪球；**与用户点名的 iDS-2SE7C144MW-DB 同族**） | 全景 **400 万**（2560×1440）+ 细节 **400 万**（2560×1440） | 该表未列传感器/焦距 → 官方未标注 | 该表未列 → 官方未标注 | 红外：【全景】30 m；【细节】150 m；报警灯 30 m | **120 dB 超宽动态** | 该表未列 → 官方未标注 | **32 倍**（数字 16 倍） | 协议行同 `iDS-2SE7C124IW-DB`：支持协议含 `RTSP`，接口协议含 `开放型网络视频接口`、`GB/T28181协议` | 需询价 | https://www.dav01.com/product/2025/05/p364900-parameter.html |
| 海康威视 | **DS-2SK8C144IMX-D/AR(32xF1)(B)**（双 400 万单枪版 32 倍臻全彩枪球） | 400 万 + 400 万 | 【全景】1/1.8″ +【细节】1/1.8″。焦距【全景】4 mm；【细节】6.0~192 mm | **90°**（垂直 44.7°；细节 56.6°~2.2°） | 全景暖白光 30 米；细节暖白光 50 米 + 红外 250 米（全彩） | **120 dB** | **IP67**（`IP67;6000V 防雷…`） | **32 倍** | 该表未列协议行 → 官方未标注 | **7,500 元/台** | http://www.ccgp-hebei.gov.cn/ContractAnncFiles/fecc84ae-f61f-ddb7-0838-26e865c9a7d5.pdf |
| 海康威视 | **DS-2SK8C246IMXR-D/AR(25xF0)(B)**（400 万+600 万 25 倍拼接臻全彩枪球） | 全景 **600 万**（3680×1656）+ 细节 **400 万**（2560×1440） | 【全景】1/1.8″（2 镜头 2×F1.0）+【细节】1/1.8″。焦距【全景】2.8 mm；【细节】6.0~150 mm | **190°±5°**（垂直 80°±5°） | 全景暖白光 30 米；细节暖白光 50 米 + 红外 200 米 | 全景数字宽动态；**细节 120 dB** | **IP67** | **25 倍** | 接口协议行含 `开放型网络视频接口`、`GB/T28181协议`；支持协议行含 `RTSP` | **8,800 元/台** | http://www.nzjc.com/supplys/15_5_38076893.html ｜ http://www.ccgp-hebei.gov.cn/ContractAnncFiles/fecc84ae-f61f-ddb7-0838-26e865c9a7d5.pdf |
| 海康威视 | **iDS-2SE7C184IMX-D(23xF1)**（800 万臻全彩全景智能枪球一体机） | 全景 400 万（2560×1440）+ 细节 **800 万**（3840×2160） | 【全景】1/1.8″ progressive scan CMOS；【细节】1/2.8″ progressive scan CMOS。焦距【全景】4 mm；【细节】5.9~135.7 mm | **88.7°**（垂直 44.7°、对角 105°） | 【全景】白光 30 m（暖白全彩）；【细节】红外 150 m，波长 850 nm | 真宽动态（**未标 dB**） | **IP66** | **23 倍** | 该页未列 → 官方未标注（同系列协议证据见上一行 iDS-2SE7C124IW-DB） | 需询价（页面 ¥1.00 为占位价） | https://m.jdzj.com/jiankongshexiangji/2-815863.html |
| 海康威视 | **iDS-2SE7C144MW-DB/ZS(32xF0)(P3)**（400 万全彩枪球一体化摄像机） | 全景 **400 万**（2560×1440）+ 细节 **400 万**（2560×1440） | 【全景】1/1.8″ CMOS；【细节】1/2.8″ CMOS。焦距【全景】2.8 mm；【细节】32 倍光学变焦 | 官方未标注（该段未给视场角） | 细节红外 150 m、白光 30 m；全景白光 30 m；报警灯【细节】白光 150 m | 官方未标注（该段未列） | **IP66** | **32 倍**（16 倍数字变倍） | 该段未列协议行 → 官方未标注（同系列证据见 iDS-2SE7C124IW-DB 行） | **5,500 元/台**（中标单价） | http://ggzyjy.zibo.gov.cn:9181/TPFrame/rest/igetattach/getattach?AttachGuid=ec490cbe-d6e1-49b8-b085-d646e73b0c1a （PDF 第 314 页） |
| 海康威视 | **(i)DS-2SK8C2ABCDE-XYZ/VWS**（中标公告掩码型号；400 万+600 万 25 倍拼接枪球一体化摄像机） | 全景 **600 万**（3680×1656）+ 细节 **400 万**（2560×1440） | 【全景】1/1.8″ CMOS；【细节】1/1.8″ CMOS。焦距【全景】2.8 mm；【细节】25 倍光学变焦 | **190°**（全景采用 2 个 F1.0 大光圈全彩镜头拼接输出） | 补光灯距离：【全景】30 米；【细节】250 米 | 官方未标注（该段未列） | 该段未列 IP → 官方未标注（另列「支持 GB35114 安全加密」） | **25 倍** | 该段未列协议行 → 官方未标注 | **7,900 元/台**（中标单价） | http://ggzyjy.zibo.gov.cn:9181/TPFrame/rest/igetattach/getattach?AttachGuid=ec490cbe-d6e1-49b8-b085-d646e73b0c1a （PDF 第 305、317 页） |
| 海康威视（**国际版型号**，经销商规格书） | **DS-2SE7C425MWG-EB/26(F0)(O-STD)**（对应国内命名 iDS-2SE7C425MWG-EB/26(F0)） | 最大图像分辨率 3632×1632（规格书写 `Auflösungsstandard: 6 MP`）；细节通道未分列 | 芯片尺寸写 `1/2,5", 1/2,8"`。焦距【全景】2,8 mm 定焦（`Objektiv Typ: Festbrennweite`） | **180° ±10°**（垂直 80° ±5°） | `Beleuchtung: Infrarot, Weißlicht`（红外+白光，**距离未标**） | **120 dB, D-WDR** | **IP66** | **25×**（数字 16×） | **三者不完全**：`ONVIF Profile G, ONVIF Profile S, ONVIF Profile T` ✔；网络协议含 `RTSP` ✔；**GB28181 未列出** | 需询价 | https://www.videor.com/de/generate/datasheet/render/product_sku/239024/ |
| 海康威视 | **DS-2SK8C144MH-D/AR(25F1)(P3)**（臻全彩枪球一体机；官网「加入配单」正式型号） | 官方描述「400 万+400 万单枪版黑光臻全彩枪球一体机」（官网该页未单列分辨率表） | 【全景】1/1.8″ progressive scan CMOS；【细节】1/1.8″ progressive scan CMOS。焦距官网该页未列 → 官方未标注 | **90°**（官网原文「全景采用1个 F1.0大光圈全彩镜头，可输出90°大场景画面」） | 补光灯距离：`【全景】30 m；【细节】250 m`；白光照射距离 `30 m` | **`支持120 dB超宽动态`** | 官网该页未列 → 官方未标注 | **【细节】25 倍** | **RTSP ✔ / ONVIF ✔ / GB28181 ✔**。支持协议含 `RTSP`；接口协议含 `开放型网络视频接口`、`GB/T28181协议` | 需询价 | https://www.hikvision.com/cn/products/pdplist/56646/ （经 Playwright + Chrome 渲染取得的官网逐字参数表） |
| 海康威视 | **iDS-2DC7C144MW-D(20X/F1)(S5)(B)**（全彩全景智能枪球一体机） | 全景 **400 万**（2560×1440）+ 细节 **400 万**（2560×1440） | 焦距【全景】4 mm；【细节】4.8~96 mm，20 倍光学变倍 | **88.7°** | 官方规格书未列补光距离 → 官方未标注 | **120 dB 超宽动态** | **IP66** | **20 倍** | **三者齐全**：支持协议含 `RTSP，RTCP，RTP`；接口协议含 `开放型网络视频接口`、`GB/T28181协议`、`支持视图库` | 需询价 | http://www.gzdcaf.com/Uploads/2022/03/03/1646275754156875.pdf （官方规格书 PDF，本地 PyMuPDF 抽取） |
| 海康威视 | **DS-2DC7X144DMW(25xF1)**（**7 寸全景枪球**，官网「经销球机」子系列） | 全景 **400 万**（2560×1440）+ 细节 **400 万**（2560×1440） | 【全景】1/1.8″ 逐行扫描 CMOS；【细节】1/2.8″ 逐行扫描 CMOS。焦距【全景】4 mm；【细节】4.8~120 mm | **88.7°**（垂直 44.7°、对角 107.5°） | 补光灯距离：`【全景】：白光30m 【细节】：红外100m，白光60m`；类型`【全景】：白光 【细节】：红外，白光`（**全景为白光臻全彩**） | `支持真宽动态`（**无 dB**） | 官网写 `防暴雨级，符合GB/T 17626.5 认证标准`，**未标 IP 等级** | **25 倍** | **三者齐全（官网原文，且为最新 GB28181-2022）**：网络协议含 `RTSP`；接口协议 `ISAPI，开放型网络视频接口，GB28181-2022，ISUP（5.0），SDK` | 需询价 | https://www.hikvision.com/cn/products/pdplist/181857/ |
| 海康威视 | **DS-2DC7X144DW(40xF1)**（7 寸全景枪球，40 倍） | 全景 **400 万** + 细节 **400 万** | 【全景】1/1.8″ 逐行扫描 CMOS；【细节】1/2.8″ 逐行扫描 CMOS。焦距【全景】4 mm；【细节】5.5~220 mm | **89.3°**（垂直 48.1°、对角 106.5°） | `【全景】：红外30m，白光30m 【细节】：红外100m，白光60m`；类型`【全景】：红外，白光` | 未取得逐字行 → 官方未标注 | 未取得逐字行 → 官方未标注 | **40 倍** | **三者齐全**：网络协议与接口协议两行与 `DS-2DC7X144DMW(25xF1)` **完全相同** | 需询价 | https://www.hikvision.com/cn/products/pdplist/181858/ |
| 海康威视 | **DS-2DC7X144DMW-B(25xF1)**（7 寸全景枪球，带麦克风/喇叭） | 全景 **400 万**（2560×1440）+ 细节 **400 万**（2560×1440） | 【全景】1/1.8″；【细节】1/2.8″。焦距【全景】4 mm；【细节】4.8~120 mm | **88.7°** | 同 `DS-2DC7X144DMW(25xF1)` | `支持真宽动态`（无 dB） | 未取得逐字行 | **25 倍** | **三者齐全**：协议两行与 `DS-2DC7X144DMW(25xF1)` 完全相同 | 需询价 | https://www.hikvision.com/cn/products/pdplist/181859/ |
| 海康威视 | **DS-2SK8C144MH-DFW/SP(25C0)(T5)**（周界版黑光&臻全彩枪球一体机；页面 `DS-2SK8C144MH-D(25C0)(T5)`） | 400 万 + 400 万（官网文案） | 双 1/1.8＂。焦距官网该页未列 → 官方未标注 | 官网该页未列 → 官方未标注 | `补光灯类型 【全景】白光；【细节】混合补光`；`补光灯距离 【全景】全彩30 m；【细节】250 m` | **`支持120 dB超宽动态`** | 官网该页未列 → 官方未标注 | `【全景】4倍；【细节】25倍` | **三者齐全**：支持协议含 `RTSP`（并多出 `WebSocket，WebSockets`）；接口协议含 `开放型网络视频接口`、`GB/T28181协议` | 需询价 | https://www.hikvision.com/cn/products/pdplist/60392/ |
| 海康威视 | **(i)DS-2SK8C1ABCDE-XYZ/VWS**（中标公告掩码型号；25 倍单枪版臻全彩枪球，400 万+400 万） | 全景 400 万 + 细节 400 万 | 【全景】1/1.8″ Progressive Scan CMOS；【细节】1/1.8″ Progressive Scan CMOS。焦距【全景】4 mm；【细节】5.9~147.5 mm | **90°** | 【全景】暖白光补光 30 m；【细节】高效红外阵列 200 m | 官方未标注（该段未列） | **IP67** | **25 倍** | 该段未列协议行 → 官方未标注 | **13,300 元/台**（中标单价） | http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202311/t20231122_21124051.htm |
| 海康威视 | **DS-2SK8C246IMX-DFW/AR/ZS/SP(40xF0)**（600 万臻全彩拼接枪球一体机；页面 `DS-2SK8C246IMX-D/AR/ZS`） | 官网文案「海康威视 600 万臻全彩拼接枪球一体机」 | 双 1/1.8＂。焦距官网该页未列 → 官方未标注 | **190°**（`全景采用2个F1.0大光圈全彩镜头，可输出190°大场景拼接画面`） | 官网该页未列于本次摘录 | 官网该页未列于本次摘录 | 官网该页未列于本次摘录 | 40 倍（型号含 `40xF0`） | 官网该页未列于本次摘录 → 官方未标注 | 需询价 | https://www.hikvision.com/cn/products/pdplist/67995/ |
| 海康威视 | **DS-2SK7P2ABCDEFG-XYZL/VWL**（中标公告掩码型号；标准版全局 Pro，三镜头：全景+细节+球机） | 三路均 400 万（2560×1440） | 三路均 1/1.8″ progressive scan CMOS。焦距【全景】定焦 6 mm；【细节】变焦 8~32 mm；【球机】变焦 13~52 mm | **55°**（垂直 29°、对角 65°） | 暖白补光：【全景】50 m 监控；【细节】20 m 人脸；【球机】20 m 人脸 | **120 dB 超宽动态** | **IP66** | 【细节】4×；【球机】4× | 该段未列协议行 → 官方未标注 | 需询价（中标公告未给单价） | http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202311/t20231122_21124051.htm |
| 大华 | **DH-SDT-7C1425-6P-GBZJ-AD3EKV**（7C 双拼-合智能 600 万超星光网络球机） | 全景 **600 万** + 细节 400 万 | 【全景】1/1.8 英寸 CMOS；【细节】1/2.8 英寸 CMOS。焦距/视场角：中文技术参数表未列 → 官方未标注 | 官方未标注 | 【全景】30 m（白光）；【细节】白光 100 m / 红外 200 m；补光类型【细节】柔光双色 | 「宽动态：全景：支持 细节：支持」（**未标 dB**） | **IP66**；TVS 6000 V | **25 倍** | 网络协议行含 `RTSP`；**ONVIF 未列出** → 仅 RTSP 有官方依据 | 需询价 | https://www.dahuatech.com/product/info/13652.html |
| 大华 | **DH-SDT-7C1424-4F-ZB-AD3E-0400**（400 万+400 万枪球） | 全景 **400 万**（2560×1440）+ 细节 **400 万**（2560×1440） | 全景 1/1.8 英寸 CMOS（4 mm，F1.0）；细节 1/2.8 英寸 CMOS（4.8~115 mm，F1.6~F3.6） | **95°**（垂直 52.5°、对角 116°；细节水平 53.1°~3.4°） | `全景：30m（白光）；细节：150m（红外）`；补光类型「红外+白光」 | 官方未标注（该表无宽动态行） | **IP66**；TVS 6000V | **24 倍** | 参数表无「接入标准/网络协议」行 → **官方未标注**（概述仅写「支持国密算法SM1…SM4，支持GB35114 A级」） | 需询价 | https://www.dahuatech.com/product/info/13683.html ｜ 参数接口 https://www.dahuatech.com/ajax/product_new/13683/2 |
| 大华 | **DH-SDT-7C1432-4F-ZB-AD6E**（400 万全彩全景枪球，32 倍） | 全景 **400 万**（2688×1520）+ 细节 **400 万**（2560×1440） | 全景 1/1.8 英寸 CMOS（4 mm）；细节 1/1.8 英寸 CMOS | 官方未标注 | 全景：红外/白光，**红外 600 米**；细节：**暖白光**，白光 300 米、红外 600 米 | **全景 106 dB；细节 120 dB** | **IP67**；DC36V/POE；除雾支持 | **32 倍** | 参数表无该行 → **官方未标注** | 需询价 | https://www.dahuatech.com/product/info/13813.html ｜ 参数接口 https://www.dahuatech.com/ajax/product_new/13813/2 |
| 大华 | **DH-SDT-6P425-4Z4/2-FAZF-D3EKV**（400 万三目枪球网络摄像机） | 400 万（2688×1520）；品名「400W 三目枪球」 | 1/1.8″，双 sensor 架构。焦距：该行只写「焦距: 25 倍光学变倍」，**无 mm 值 → 官方未标注** | 官方未标注 | 补光类型「红外」；补光距离 **100 米**；**无全彩/暖光标注** | **120 dB** | **IP67** | **25 倍** | 参数表无「网络协议/接入标准」行 → **官方未标注** | 需询价 | https://www.dahuatech.com/product/info/13819.html ｜ 参数接口 https://www.dahuatech.com/ajax/product_new/13819/2 |
| 大华 | **DH-SDT-7C1223-4F-ZB-AD3-0400**（23 倍 400 万+200 万枪球；**政府招标文件来源**） | 400 万 + 200 万 | 官方未标注（该件未列传感器） | **79°**（垂直 42.4°） | `红外照射距离: 【全景】30 m，【细节】150 m` | **`宽动态: 120dB 超宽动态`** | **IP66** | **23 倍** | 该件未列协议行 → 官方未标注 | **5,500.00 元/台** | https://zfcg.ggzyjy.weihai.cn/gcfile/downALoad?attachId=b28f5183fd264300b94ba11d4fc180db&lock=c3482849c69a8a541bb0cd9662051be7 （第 20 页，供应商「浙江大华技术股份有限公司」） |
| 大华 | **DH-SDT-8C1425-6P-GAZJ-D3EFHV**（8C 双拼-合智能 600 万超星光网络球机） | 全景 **600 万** + 细节 400 万 | 【全景】1/1.8 英寸 CMOS；【细节】1/1.8 英寸 CMOS。焦距/视场角 → 官方未标注 | 官方未标注 | 【全景】30 m（白光）；【细节】白光 30 m / **红外 250 m**；【细节】红外+柔光双色 | 「支持」（**未标 dB**） | **IP67**；TVS 6000 V | **25 倍** | 网络协议行含 `RTSP`；**ONVIF 未列出** | 需询价 | https://www.dahuatech.com/product/info/13651.html |
| 大华（**仅国际版型号**） | **SDT4E425-8P-GB-APV1**（8+4MP 25x TiOC Network Panoramic PTZ Camera） | Overview 800 万（4096×1860）+ Detail 400 万（2560×1440） | Overview 1/2.7″ CMOS；Detail 1/2.8″ CMOS。焦距 Overview 2.8 mm；Detail 5~125 mm | **H: 180°**（V: 86°） | Overview 30 m IR + 30 m 白光；Detail 100 m IR + 50 m 白光；Detail 2× 暖光灯 | Overview DWDR；**Detail 120 dB** | **IP66**；TVS 6000 V | **25×** | 有明确行：`Interoperability: ONVIF (Profile S & Profile G & Profile T & Profile M);CGI;SDK;P2P`；`Network Protocol` 行含 `RTSP`；**GB/T28181 未列出** | 需询价 | https://www.dahuasecurity.com/products/network-products/ptz-cameras/x-spans-series/distribution/sdt4e425-8p-gb-apv1 |
| 大华（**仅国际版型号**） | **SDT5X405-4F-QA-0600**（4MP Starlight+ IR WizMind Network Dual-PTZ Camera） | Panorama 400 万（2688×1520）+ Detail 400 万（2688×1520） | Panorama 1/1.8″ CMOS；Detail 1/1.8″ CMOS。焦距 Panorama 6 mm；Detail 10~50 mm | **H: 57°**（V: 31°；D: 66°） | Panorama 30 m 白光（4 颗白光灯）；Detail 100 m IR（4 颗红外灯） | **Panorama 120 dB** | **IP67**；TVS 8000 V | **5×** | 有明确行：`CGI; ONVIF Profile S&G&T; GB/T28181`；`Network Protocol` 行含 `RTSP` | 需询价 | https://www.dahuasecurity.com/products/PTZ-Cameras/WizMind-Series/SDT/4MP/SDT5X405-4F-QA-0600 |
| 宇视 | **IPC-E98244-FW@X33-E2-VH1**（400 万+400 万超星光级全景拼接枪球一体化联动网络摄像机） | 全景 3840×1080@30fps + 细节 2688×1520@30fps（官方表述为 400 万+400 万） | 采用 1/1.8″ 高灵敏度 CMOS 传感器（官方未分通道标注）；焦距官方未标注 | **水平 190°±5°**、垂直 55° | 全光谱补光方案：**全景通道 30 米暖光补光；细节通道 250 米红外补光** | 官方未标注 | 官方未标注 | 官方未标注 | 官网产品页无规格表亦无协议行 → 官方未标注（详见下方「缺口」） | 需询价 | https://cn.uniview.com/Products/Professional/Camera/5/ |
| 大华 | **DH-PSDW81243S-A270-D425-G**（大华哈勃守望者摄像机，全景+细节双通道） | 通道 1（全景）**1200 万** + 通道 2（细节）**400 万** | 通道 1（全景）1/2.8 英寸 CMOS；通道 2（细节）1/1.8 英寸 CMOS。焦距：通道 1 **2.8 mm 定焦**（F1.0）；通道 2 **5.3~134 mm 电动变焦**（F1.6~F4.0） | 官方未标注（该参数表未列视场角） | 最大补光距离：`通道1（全景）：不支持；通道2（细节）：100m（红外）` | **通道 1：120 dB；通道 2：120 dB** | **IP67** | 电动变焦（表中未给倍率数字） | **三者齐全**：`接入标准：ONVIF（Profile S & Profile G & Profile T）；CGI；GB/T28181-2022（双国标）；GB/35114A`；网络协议含 `RTSP` | 需询价 | https://www.dahuatech.com/product/info/14042.html ｜ 参数接口 https://www.dahuatech.com/ajax/product_new/14042/2 |
| 大华 | **DH-PSDW8638S-B360**（高清 600 万像素全景特写网络摄像机，「守望者」外观） | 表中像素行写 `800万`，最大分辨率 `1920×1080×4`（4 路 1080p 拼接输出） | 1/2.7 英寸 CMOS。焦距：全景 2 mm；细节 2.7~13.5 mm | 官方未标注（该参数表未列视场角） | 该参数接口返回的表中**无补光距离行** → 官方未标注 | 官方未标注（该表未列宽动态行） | 官方未标注（该表未列防护等级行） | 细节 2.7~13.5 mm（表中未给倍率数字） | **三者齐全**：`接入标准：ONVIF；GB/T28181；CGI`；网络协议含 `RTSP` | 需询价 | https://www.dahuatech.com/product/info/4491.html ｜ 参数接口 https://www.dahuatech.com/ajax/product_new/4491/2 |
| 宇视 | **IPC-E98344-IR@L-X40-E8-W-VH3**（32MP+8MP 天宫全景联动一体机） | 全景 **3200 万**（11520×2700@30fps）+ 细节 **800 万**（3264×2448@30fps） | 官方未标注（官网产品页无规格表） | **360°**（官方原文「可输出水平360°全景画面」） | 官方未标注 | 官方未标注 | 官方未标注 | 官方未标注 | 官方未标注（该页无协议行） | 需询价。可核验中标价 **27,295 元/台** | https://cn.uniview.com/Products/Professional/Camera/18/ ｜ 价格 https://zcy-gov-open-doc.oss-cn-north-2-gov-1.aliyuncs.com/1024FPA/330299/10009100229/202512/a6332d6f-f2e9-4724-9b43-e2b43066a609.pdf |
| 宇视 | **HIC93441-IR@X4-F40-VH1**（双 400 万超星光深度智能一体化联动网络摄像机） | 全景 400 万（2688×1520）+ 细节 400 万（2688×1520） | 「全景和细节通道均采用 1/1.8″ 高灵敏度 CMOS 传感器」；焦距官方未标注 | 官方未标注 | 官方未标注 | **120 dB 光学宽动态**（官方原文「120dB光学宽动态，根据环境亮度自动切换」） | 官方未标注 | 官方未标注 | 官方未标注（该页无协议行） | 需询价 | https://cn.uniview.com/Products/Professional/Camera/15/ |
| 宇视（**国际版**） | **IPC98344ER-GX42-E8-W-VH3**（大陆 E98344 系列的国际版，**不等同**：国际版细节 4MP/GX42，大陆 X40/细节 8MP） | 全景 3200 万 + 细节 400 万 | 1/1.8″ CMOS；全景 2 mm；细节 6.0~252.0 mm | **H 360° / V 110°**（细节 59.47°–2.20°） | IR 500 m | 全景 N/A；**细节 120 dB** | **IP67 (IEC 60529) / IK10** | **42×** | `Protocols: SSH, IGMP, RTP, RTCP, SMTP, IPv4, IPv6, ICMP, ARP, TCP, UDP, DHCP, PPPoE, RTSP, RTMP, DNS, DDNS, NTP, UPnP, HTTP, 802.1x, SNMP, QoS, SSL/TLS, HTTPS, FTP`；`Compatible Integration: ONVIF (Profile S, Profile G, Profile T, Profile M), API, SDK`；**GB28181 命中 0** | 需询价 | https://global.uniview.com/Products/PTZ_Cameras/Pro_Series/Pro_Series/IPC98344ER-GX42-E8-W-VH3/ |
| 宇视（**国际版**） | **IPC94144SR-X25-F40C**（4MP+4MP 双通道 MultiView 球机，架构最接近 E98244 但**不是同一型号**） | 400 万 + 400 万（均 2688×1520） | 1/2.7″ CMOS；焦距 4.0 mm / 4.8~120 mm | **H 91.3°**（细节 55.46°–3.09°） | 官方未标注于本次摘录 | **120 dB** | **IP66** | **25×** | `ONVIF(Profile S,G,T,M)+API+SDK`；Protocols 含 `RTSP`；**GB28181 未声明** | 需询价 | https://global.uniview.com/Products/PTZ_Cameras/Prime_Series/Prime_Series/IPC94144SR-X25-F40C/ |
| TP-LINK | **TL-IPC679V-A4**（全景拼接三目室外枪球联动摄像机） | 枪机（全景双目拼接）400 万（3488×1088）+ 球机（特写）300 万（2304×1296） | 双通道均 1/3.0 英寸 CMOS；枪机焦距 2.8 mm+2.8 mm；球机 8 mm | 官方未标注 | 枪机 2 颗红外灯 + 2 颗暖光灯；照明模式含红外/全彩/移动侦测全彩；**距离官方未标注** | 官方未标注 | **IP66** | 定焦（无光学变倍） | 规格表有 `接口协议：ONVIF` 与含 `RTSP` 的支持协议行；**GB28181 未列出** | **¥549.00**（官方商城） | https://www.tp-link.com.cn/product_3466.html?v=specification ｜ https://mail.tp-linkshop.com.cn/Products/Details/2797 |
| TP-LINK | **TL-IPC54L4V-WD20**（全景 400 万双目拼接 / 细节 400 万三目变焦枪球联动） | 枪机（全景）400 万（3840*1024）+ 球机（特写）400 万（2560*1440） | 枪机 1/2.8 英寸 CMOS 星光级；球机传感器尺寸官方未标注。焦距：枪机 4 mm 定焦；球机写「20 倍光学混合变焦」（无毫米数） | **169°**（垂直 44°，4mm 机型） | 枪机全彩 / 移动侦测全彩，默认全彩；灯数与距离官方未标注 | 官方未标注 | **IP66** | 球机 20 倍光学混合变焦 | 规格表有 `接口协议：ONVIF` 与含 `RTSP` 的支持协议行；**GB28181 未列出** | 需询价 | https://www.tp-link.com.cn/product_3186.html?v=specification |
| TP-LINK | **TL-IPC55T2**（全景特写无线网络摄像机） | 全景 500 万（1726×1726）+ 特写 200 万（1920×1080） | 全景 1/2.7 英寸 CMOS；特写 1/2.9 英寸 CMOS。焦距：全景 1.1 mm；特写 6 mm | **180°**（来自产品描述页，规格表无「可视角度」行） | 规格表无补光行；卖点仅「支持红外夜视」。**红外距离/暖光官方未标注** | 官方未标注 | 官方未标注（室内机） | 定焦（特写 6 mm 定焦） | 支持协议行含 `RTSP`；**ONVIF 未列出；GB28181 未列出** | **¥499.00**（官方商城） | https://www.tp-link.com.cn/product_1605.html?v=specification ｜ https://mail.tp-linkshop.com.cn/Products/Details/2804 |
| TP-LINK | **TL-IPC48DW 双摄版**（800 万双摄无线云台网络摄像机） | 3840×2160（800 万）；规格表**未分列**广角云台镜头与固定镜头各自参数 | 1/2.7 英寸 CMOS；2.8 mm；F1.6 | 官方未标注 | 卖点「红外夜视、日夜全彩、人形侦测全彩」→ 有全彩；距离官方未标注 | 卖点「支持数字宽动态」（**无 dB**） | 官方未标注（室内机） | 定焦 | **三者齐全**：`支持协议：TCP/IP，ICMP，HTTP，DHCP，DNS，DDNS，RTP，RTSP，RTCP，NTP，GB28181,ONVIF,802.11 b/g/n/ac/ax` | **¥489.00**（官方商城） | https://www.tp-link.com.cn/product_4335.html?v=specification ｜ https://mail.tp-linkshop.com.cn/Products/Details/2930 |

> TP-LINK 另有 **TL-IPC564VEP-W2.8**（600 万双目超广角，双目拼接单路输出，水平 180°/垂直 50°，IP66，ONVIF+RTSP，无 GB28181，¥479.00）与 **TL-IPC689V双目广角版**（双目拼接单路 2560*1440，单镜头水平视场角 76°/总水平视场角 126°，IP66，¥299.00）等型号。「双目**拼接**」类产品只有**一路输出**、不构成「全景+细节」双通道，本表不计为主力行。完整 TP-LINK 清单见同目录 `TP-LINK_双摄全景_规格调研.md`。

---

## 二、逐型号备注与协议依据原文

### H1. 海康威视 iDS-2SE7C124IW-DB(32X/F1)(S5)（星光全景枪球）

来源：数字音视工程网（DAV01）产品参数页，完整复刻海康官方规格表。
URL: https://www.dav01.com/product/2025/05/p364898-parameter.html

**RTSP / ONVIF / GB28181 证据（表格逐字行）**

> **支持协议**：`IPv4/IPv6,HTTP,HTTPS,802.1x,Qos,FTP,SMTP,UPnP,SNMP,DNS,DDNS,NTP,RTSP,RTCP,RTP,TCP/IP,UDP,IGMP,ICMP,DHCP,PPPoE,Bonjour;WebSocket;WebSockets`

> **接口协议**：`软件集成的开放式API,开放型网络视频接口,ISAPI,海康SDK,第三方管理平台接入,GB/T28181协议,支持视图库,支持萤石接入,ISUP`

页面顶部产品简介同句复述：

> 「支持海康SDK、开放型网络视频接口、ISAPI、GB/T28181、ISUP、萤石」

即：**RTSP 有、ONVIF（「开放型网络视频接口」为海康对 ONVIF 的中文官方表述）有、GB/T28181 有**。

**其他关键逐字行**

> 焦距：`【全景】4mm；【细节】5.9~188.8 mm，32倍光学变倍`
> 视场角：`【全景】水平视场角：79°，垂直视场角：42.4°` ／ `【细节】60.2°~2.3°（广角~望远）`
> 红外照射距离：`【全景】30m，【细节】150 m`；报警灯 `30 m`
> 宽动态：`120dB超宽动态`
> 最大图像尺寸：`【全景】2560 ×1440，【细节】1920 ×1080`
> 最大光圈数：`【全景】F1.6；【细节】F1.5`

**缺口**：该页「一般规范」段落未列 IP 防护等级行 → 记为**官方未标注**；亦未列传感器尺寸行。

---

### H1b. 海康威视 iDS-2SE7C144IW-DB(32X/F1)(S5)（星光全景枪球，400 万+400 万）

URL: https://www.dav01.com/product/2025/05/p364900-parameter.html

**逐字行**

> `最大图像尺寸 | 【全景】2560 ×1440，【细节】2560 ×1440`
> 红外照射距离 `【全景】30m，【细节】150 m`；报警灯 `30 m`
> 宽动态 `120dB超宽动态`；光学变倍 `32倍`；数字变倍 `16倍`
> 支持协议 / 接口协议两行同 `iDS-2SE7C124IW-DB`（含 `RTSP`、`开放型网络视频接口`、`GB/T28181协议`）

**⚠️ 该表未列传感器尺寸、焦距、视场角、IP 等级 → 官方未标注。**

> 这是与用户点名的 `iDS-2SE7C144MW-DB` **同族且同为 400 万+400 万**的型号（`IW`/`MW` 为镜头/补光配置差异）。

---

### H1c. 海康威视 星光全景枪球 的**停产状态**与 IP 等级（官方合作伙伴门户证据）

海康**官方合作伙伴门户**产品页（`web_fetch`/`curl` 实测 HTTP 200）：
URL: https://partners.hikvision.com/product/detail/3b9b3c1a

页面结构化字段逐字：

> `model: iDS-2SE7C124IW-/S5`
> `modelName: 星光全景枪球`
> `pathName: 前端产品//球型网络摄像机//DE球机//全景枪球`
> `IP66，抗干扰能力强，适用于严酷的电磁环境，符合GB/T17626.2/3/4/5/6四级标准`
> `marketingStatus: 停产`

⚠️ **重要冲突**：海康官方门户把 `iDS-2SE7C124IW-/S5` 标为 **`停产`**，而 dav01 参数页标「(在产)」。**采购决策应以官方门户的「停产」为准**；若项目需要该系列，建议改用 `iDS-2SE7C144IW-DB(32X/F1)(S5)` 等在产型号并向海康确认供货状态。

---

### H1d. 海康威视 DS-2SK8C 系列（河北政采 + 经销商，含价格）

来源：河北省政府采购合同公告 PDF 与经销商参数页。

**`DS-2SK8C144IMX-D/AR(32xF1)(B)`**（双 400 万单枪版 32 倍臻全彩枪球）— 逐字：

> `焦距：【全景】4mm；【细节】6.0~192mm`
> `视场角：【全景】水平视场角：90°，垂直视场角：44.7°；【细节】56.6~2.2 度`
> `防护：IP67;6000V 防雷…`
> 补光：全景暖白光 30 米；细节暖白光 50 米 + 红外 250 米
> 价格：**7,500 元/台**
> URL: http://www.ccgp-hebei.gov.cn/ContractAnncFiles/fecc84ae-f61f-ddb7-0838-26e865c9a7d5.pdf

**`DS-2SK8C246IMXR-D/AR(25xF0)(B)`**（400 万+600 万 25 倍拼接臻全彩枪球）— 逐字：

> 传感器：全景 1/1.8″（2 镜头 2×F1.0）+ 细节 1/1.8″
> `焦距：全景 2.8mm + 细节 6.0~150mm`
> 全景水平视场角 **190°±5°**（垂直 80°±5°）
> 补光：全景暖白光 30 米；细节暖白光 50 米 + 红外 200 米；防护 **IP67**
> 接口协议：`ISUP,软件集成的开放式API,ISAPI,海康SDK,E家协议,开放型网络视频接口,GB/T28181协议,萤石,视图库`
> 价格：**8,800 元/台**
> URL: http://www.nzjc.com/supplys/15_5_38076893.html ｜ 河北政采 PDF 同上

**`DS-2SK8C246IMX-D/AR(40F0)`**（400 万+600 万 40 倍）— 逐字：

> 焦距：全景 2.8 mm + 细节 6.0~240 mm；光学变倍 **40 倍**
> 视场角：全景 190°±5°（垂直 80°±5°）；细节 59°~2°
> 分辨率：3680×1656 + 2560×1440；防护 **IP67**；补光：全景 30 米 / 细节 250 米 + 白光 30 m
> 价格：需询价（另有招标 PDF 记 `DS-2SK8C144IMX-D/AR(40F1)(P3)` 为 7,250 元/台，但该件未列焦距/视场角）
> URL: https://xa.zol.com.cn/html/netfixing/video/hq/39/391089.shtml

---

### H1e. 海康威视 iDS-2SE7C124IW-DB/GLT（23 倍 + 4G 版，**非 32X**，传感器与 32X 版不同）

> 传感器 全景 1/2.8″ + 细节 1/2.8″｜焦距 全景 4 mm + 细节 4.8~110 mm｜视场角 全景水平 79°，细节 57.6°~2.7°
> 分辨率 2560×1440 + 1920×1080｜宽动态 120 dB｜红外 30 m/150 m｜IP 官方未标注｜价格电议
> URL: https://m.hi1718.com/product/2021915102343665.html

> ⚠️ 注意：**32X 版与 GLT 23X 版的传感器尺寸不同**（GLT 为 1/2.8″+1/2.8″），**不可互相套用**。用户所写 `iDS-2SE7C124IW-DB(32X/F1)(S5)` 的传感器尺寸本次**仍未取得** → 官方未标注。

---

### H3d. 海康威视 **7 寸全景枪球** 官方子系列（3 个型号，全部官网原文）— **直接对应本次调研需求**

海康官网「经销球机」分类下明确存在「7寸全景枪球」子系列。三个型号的**网络协议 / 接口协议两行完全相同**：

> **网络协议**：`TCP/IP，ICMP，HTTP，HTTPS，FTP，DHCP，DNS，DDNS，RTP，RTSP，RTCP，PPPoE，NTP，UPnP，SMTP，SNMP，IGMP，QoS，IPv4，IPv6，UDP，SSL/TLS，WebSocket，WebSockets，802.1X`
> **接口协议**：`ISAPI，开放型网络视频接口，GB28181-2022，ISUP（5.0），SDK`

→ **RTSP ✔ / ONVIF（「开放型网络视频接口」）✔ / GB28181-2022 ✔**，且是**最新的 2022 版国标**——本文件中协议证据最新的一条。

**`DS-2DC7X144DMW(25xF1)`** — https://www.hikvision.com/cn/products/pdplist/181857/

> `最大分辨率 【全景】2560 ×1440，【细节】2560 ×1440`（**400 万+400 万**）
> `【全景】1/1.8＂ 逐行扫描CMOS,【细节】1/2.8" 逐行扫描CMOS`
> `焦距 【全景】4mm；【细节】4.8 mm~120 mm`；`光学变倍 25倍`
> `视场角 【全景】 水平视场角：88.7° 垂直视场角：44.7° 对角视场角：107.5°`
> `补光灯距离 【全景】：白光30m 【细节】：红外100m，白光60m`；`补光灯类型 【全景】：白光 【细节】：红外，白光` → **全景为白光臻全彩**
> `宽动态 支持真宽动态`（**无 dB 值 → 官方未标注 dB**）
> `防护 防暴雨级，符合GB/T 17626.5 认证标准` → ⚠️ **官网未标注 IP 等级**
> 其他：尺寸 241.8×216.4×333.6 mm；4 KG；DC36V；最大功耗 24W；支持双 mic、编码画中画、512GB MicroSD

**`DS-2DC7X144DW(40xF1)`** — https://www.hikvision.com/cn/products/pdplist/181858/

> 官网文案：`全景400万 F1.0大光圈单目臻全彩，细节球机400万40倍，采用双镜头设计，兼顾全景细节`
> `焦距 【全景】4mm；【细节】5.5-220mm`；`光学变倍 40倍`
> `视场角 【全景】 水平视场角：89.3° 垂直视场角：48.1° 对角视场角：106.5°`
> `【全景】：红外30m，白光30m`；`【细节】：红外100m，白光60m`
> ⚠️ 该页**未展开宽动态与防护子行** → 官方未标注。

**`DS-2DC7X144DMW-B(25xF1)`** — https://www.hikvision.com/cn/products/pdplist/181859/

> 规格与 `DS-2DC7X144DMW(25xF1)` 相同；差异为官网文案 `支持麦克风和喇叭，支持语音对讲`。

---

### H3e. 海康威视 DS-2SK8C144MH-D(25C0)(T5) / DS-2SK8C246IMX-D/AR/ZS（官网其余型号）

**`DS-2SK8C144MH-D(25C0)(T5)`**（周界版黑光&臻全彩枪球一体机，配单型号 `DS-2SK8C144MH-DFW/SP(25C0)(T5)`）— https://www.hikvision.com/cn/products/pdplist/60392/

> `光学变倍 【全景】4倍；【细节】25倍`
> `补光灯类型 【全景】白光；【细节】混合补光`；`补光灯距离 【全景】全彩30 m；【细节】250 m`
> `宽动态 支持120 dB超宽动态`；传感器双 1/1.8＂
> **协议逐字行比 56646 多出 WebSocket**：`支持协议 …NTP，RTSP，RTCP，RTP…，Bonjour，WebSocket，WebSockets` / `接口协议 ISUP，软件集成的开放式API，ISAPI，海康SDK，E家协议，开放型网络视频接口，GB/T28181协议，萤石，视图库`
> ⚠️ 分辨率/焦距/视场角/IP 官网该页同样未列。

**`DS-2SK8C246IMX-D/AR/ZS`**（臻全彩枪球一体机，配单型号 `DS-2SK8C246IMX-DFW/AR/ZS/SP(40xF0)`）— https://www.hikvision.com/cn/products/pdplist/67995/

> 官网文案：`海康威视600万臻全彩拼接枪球一体机`、`全景采用2个F1.0大光圈全彩镜头，可输出190°大场景拼接画面`；双 1/1.8＂

---

### H2. 海康威视 iDS-2SE7C184IMX-D(23xF1)（800 万臻全彩全景智能枪球一体机）

来源：机电之家网（经销商「上海亿赞电子科技有限公司」）复刻的官方规格表；发布时间 2026-09-18，为近期在售。
URL: https://m.jdzj.com/jiankongshexiangji/2-815863.html

**规格表逐字**

> 传感器类型：`【全景】1/1.8＂ progressive scan CMOS,【细节】1/2.8" progressive scan CMOS`
> 焦距：`【全景】4 mm；【细节】5.9 mm~135.7 mm，23倍光学变倍`
> 视场角：`【全景】水平视场角：88.7° 垂直视场角：44.7° 对角视场角：105° 【细节】水平视场角：60.2° to 3.4°`
> 补光灯距离：`【全景】白光30 m 【细节】红外150 m`；红外波长范围 `850 nm`
> 主码流帧率分辨率：`【全景】50 Hz：25 fps（2560 × 1440…）`；`【细节】50 Hz：25 fps（3840 × 2160，2560 × 1440…）`
> 宽动态：`真宽动态`
> 防护：`IP66;抗干扰能力强，适用于严酷的电磁环境，符合GB/T17626.2/3/4/5/6四级标准`

**RTSP / ONVIF / GB28181**：该复刻页**未列**协议行 → 记 **官方未标注（本页）**。同系列（iDS-2SE7C）在中标公告中的官方表述为「支持海康 SDK、开放型网络视频接口、ISAPI、GB/T28181 和 ISUP 接入」，但那句中标的型号是 `(i)DS-2DF7C4ABCD-XYZL/VWS`（单镜头泛智能球），**不能直接套用到本型号**，故本行如实标注未列。

**价格**：页面标价 ¥1.00 属经销商占位价，**不可采信 → 需询价**。

**交叉验证：「7寸全景800W枪球 / 臻全彩全景智能枪球」＝本型号（证据链）**

浙江省政府采购 PDF（2024-10，108 页）第 43–44 页的采购清单条目「15 臻全彩全景枪球 / **7寸全景800W枪球** / 臻全彩全景智能枪球」给出的完整参数为：

> 「补光灯距离：【全景】白光30 m 【细节】红外150 m 红外波长范围：850 nm」
> 「主码流帧率分辨率：【全景】50 Hz：25 fps（2560 × 1440…）**【细节】50 Hz：25 fps（3840 × 2160，2560 × 1440…）**」
> 「宽动态：真宽动态」
> 「防护：IP66;抗干扰能力强…符合GB/T17626.2/3/4/5/6 四级标准」
> 「尺寸：222.3 × 252.6 × 398.5 mm 重量：6 kg 除雾：加热玻璃除雾」

该段参数与 jdzj.com 上 `iDS-2SE7C184IMX-D(23xF1)` 的官方规格表**逐项一致**（补光 30 m/150 m、850 nm、真宽动态、IP66、尺寸 222.3×252.6×398.5 mm、重量 6 kg、加热玻璃除雾）。因此可判定：**用户询问的「7寸全景800W枪球 / 臻全彩全景智能枪球」对应型号即 iDS-2SE7C184IMX-D(23xF1)**；「800W」指的是**细节通道** 3840×2160，全景通道为 2560×1440（400 万）。
URL: https://zcy-gov-open-doc.oss-cn-north-2-gov-1.aliyuncs.com/1023FP/undefined/330106/10008018904/202410/b38cea83-bc1c-432b-8a7c-7970c8e39cd9.pdf

**协议缺口（重要）**：该 PDF 段落与 jdzj 页面**都没有列出 RTSP/ONVIF/GB28181 行** → 本型号协议支持记为 **官方未标注（已核查的两个来源均未列）**。另：海康官网「联动系列」11 个型号与「经销球机」25 个型号列表中**均无该型号**，故其是否仍在产**未能证实**。

**⚠️ 来源冲突（不可择一断言）**：`iDS-2SE7C184IMX-D(23xF1)` 的**细节传感器尺寸与宽动态**在两份经销商复刻页中互相矛盾：

| 字段 | jdzj.com | gys.cn |
|---|---|---|
| 细节传感器 | `1/2.8" progressive scan CMOS` | `1/1.8＂ progressive scan CMOS` |
| 宽动态 | `真宽动态` | `120dB超宽动态` |

→ **本表按 jdzj.com 记录，但该两项存在冲突，采购前须向海康确认。**

**❌ 「全景 800 万」不存在**：本次调研**没有任何来源**支持「800 万像素落在全景通道」。三个独立来源（jdzj.com、jiankongqicai.com、浙江政采 PDF）一致显示 800 万属**细节**通道，全景为 2560×1440（400 万）。全网已见的海康全景通道最高为 **400 万单目**或 **600 万双目拼接**（3632×1632 / 3680×1656）。

同一 PDF 第 37 页另有一条海康「**低功耗全景枪球**」条目（23 倍光学变倍、细节红外 150 m/白光 30 m、全景 30 m、IP66、支持 4G），但**该清单未给出型号号**，故不作为独立型号收录。

---

### H2b. 海康威视 iDS-2SE7C144MW-DB/ZS(32xF0)(P3)（400 万全彩枪球一体化摄像机）

来源：淄博市公共资源交易平台招标/中标文件 PDF，第 314 页，**逐字抄录官方参数并附中标单价**。
URL: http://ggzyjy.zibo.gov.cn:9181/TPFrame/rest/igetattach/getattach?AttachGuid=ec490cbe-d6e1-49b8-b085-d646e73b0c1a
（本地 `curl` 下载后以 PyMuPDF 抽取，共 548 页）

**逐字参数（PDF 原文）**

> 规格型号：`iDS-2SE7C144MW-DB/ZS(32xF0)(P3)`
> 「1.400 万全彩枪球一体化摄像机」
> 「8.支持高效补光阵列，细节红外照射距离150m，白光30m，全景白光照射距离30m；」
> 「9.IP66 防护等级；」
> 「10.传感器类型：【全景】1/1.8" CMOS,【细节】1/2.8" CMOS；」
> 「12.焦距：【全景】2.8mm；【细节】32 倍光学变焦；」
> 「13.白光照射距离：【细节】30m；【全景】30m；红外照射距离：【细节】150m；报警灯：【细节】白光150m；」
> 「14.分辨率：【全景】2560×1440，【细节】2560×1440；」
> 「15.视频压缩标准：H.265、H.264、MJPEG。」

**价格证据**：单价 `5500.00` 元，数量 5，总价 `27500.00` 元。

**同类佐证（第二个独立来源）**：佛山市公安局三水分局南山大道电子监控设备采购项目结果公告中出现型号 `iDS-2SE7C144MW-DB/ZS(32xF1)(P3)`（末位 F1 而非 F0，为不同配置后缀），描述为「1．内置2个镜头，可以输出两路视频图像，1路全景视频图像、1路细节视频图像； 2．内置2颗GPU芯片」。
URL: https://gdgpo.czt.gd.gov.cn/maincms-web/noticeGd?type=notice&id=e5767bd8-db88-11ee-bf98-f4b78dd1d78b&channel=fca71be5-fc
（该页面为 JS 渲染，正文未能完整抓取，仅搜索快照可见上述句子。）

> ⚠️ 后缀差异说明：`(32xF0)` 与 `(32xF1)` 是同一基础型号的不同配置/固件后缀，**采购时须以合同确认的完整后缀为准**。用户点名的 `iDS-2SE7C144MW-DB(32X/F1)(S5)` 属同一型号族，本次**未取得该精确后缀的规格页**。

---

### H2c. 海康威视 (i)DS-2SK8C2ABCDE-XYZ/VWS（400 万+600 万 25 倍拼接枪球一体化摄像机）

同一 PDF 来源的第 305 页与第 317 页。URL 同上。

> ⚠️ 型号中的 `ABCDE-XYZ` 为招标文件掩码写法，非可直接采购的完整型号。

**逐字参数（PDF 第 317 页，较完整）**

> 规格型号：`(i)DS-2SK8C2ABCDE-XYZ/VWS`
> 「1.400 万+600 万25 倍拼接枪球一体化摄像机；」
> 「2.全景采用2 个F1.0 大光圈全彩镜头，输出190°大场景拼接画面；」
> 「11.传感器类型：【全景】1/1.8＂CMOS,【细节】1/1.8＂CMOS；」
> 「13.焦距：【全景】2.8mm；【细节】25 倍光学变焦；」
> 「14.补光灯距离：【全景】30 米；【细节】250 米；」
> 「15.分辨率：【全景】3680×1656,【细节】2560×1440；」
> 「10.支持GB35114 安全加密；」

PDF 第 305 页的简版另加：

> 「1.摄像机内置3 个镜头，可输出一路全景视频和一路细节视频，其中全景内置2 个镜头，细节内置1 个镜头；」
> 「2.全景内置2 个镜头，光圈F1.0，具有1/1.8 靶面尺寸，内置4 颗补光灯；」

**价格证据**：第 305 页单价 `7900.00` 元 × 2 台；第 317 页单价 `7900.00` 元 × 15 台。报价一致，可采信。

---

### H2d. 海康威视 DS-2SE7C425MWG-EB/26(F0)(O-STD)（**国际版**，经销商规格书）

来源：德国经销商 VIDEOR E. Hartig GmbH 生成的产品规格书 PDF（页脚标注 © September 2026）。
URL: https://www.videor.com/de/generate/datasheet/render/product_sku/239024/
（本环境 `curl` 下载 + PyMuPDF 抽取，共 3 页）

> ⚠️ 这是**经销商根据官方数据生成的规格书**，非海康官网页面；且为**国际版型号**。海康官网对应页面 https://www.hikvision.com/pl/products/IP-Products/PTZ-Cameras/Pro-Series/ds-2se7c425mwg-eb-26-f0-/ 与 https://www.hikvision.com/en/products/IP-Products/PTZ-Cameras/Pro-Series/ds-2se7c425mwg-eb-26-f0-/ 均可访问（HTTP 200），但**正文为 JS 渲染，未能取到规格**。

**规格书逐字（德文原文 + 中文对照）**

> `Auflösungsstandard: 6 MP` ／ `Bildauflösung max.: 3632x1632` —— 最大图像分辨率 3632×1632
> `Chipgröße: 1/2,5", 1/2,8"` —— 芯片尺寸 1/2.5″、1/2.8″
> `Bildwinkel horizontal: 180° ±10°` ／ `Bildwinkel vertikal: 80° ±5°` —— 水平视场角 180°±10°，垂直 80°±5°
> `Brennweite: 2,8 mm` ／ `Objektiv Typ: Festbrennweite` —— 焦距 2.8 mm，定焦
> `Zoomfaktor (optisch): 25` ／ `Zoomfaktor (digital): 16` —— 光学变倍 25×，数字 16×
> `Beleuchtung: Infrarot, Weißlicht` —— 补光：红外 + 白光
> `Wide Dynamic Range (WDR): 120dB, D-WDR`
> `Schutzart: IP66` ／ `Zertifizierungen: IP66,ONVIF,HTTPS,802.1X`
> **ONVIF**：`ONVIF Profile G, ONVIF Profile S, ONVIF Profile T`
> **Netzwerkprotokolle**：`DHCP, DNS, FTP, HTTP, HTTPS, NTP, RTP, RTSP, TCP, TCP-IP, und weitere`
> `Kameratyp: Domekamera, Multidirektional Kamera mit PTZ` —— 多方向 PTZ 摄像机
> `Leistungsaufnahme: 60 W`；`Temperaturbereich (Betrieb): -30 °C bis +65 °C`；`Power over Ethernet: HiPoE`；`Stromversorgung: 24VAC`

结论：**RTSP ✔ / ONVIF（Profile G、S、T）✔ / GB28181 未列出**；IP66、WDR 120 dB、全景水平 180°±10°、光学变倍 25×。
用户点名的国内写法 `iDS-2SE7C425MWG-EB/26(F0)` **本次未取得中国区官方页面**，仅验证到国际版 `DS-2SE7C425MWG-EB/26(F0)` 的经销商规格书。

---

### H3. 海康威视 DS-2SK8C144MH-D/AR(25F1)(P3)（臻全彩枪球一体机）— **官网原文已取得**

官网详情页 URL: https://www.hikvision.com/cn/products/pdplist/56646/
**取得方式**：本机 Playwright + Chrome for Testing 渲染 `hikvision.com/cn` 详情页（该站对 `curl` 返回 JS 反爬挑战页、对 `web_fetch` 因导航超长而正文截断，**只有无头浏览器能拿到官网逐字参数表**）。

**官网逐字参数**

> 页面标题：「臻全彩枪球一体机 DS-2SK8C144MH」
> 「加入配单」正式型号：**`DS-2SK8C144MH-D/AR(25F1)(P3)`**
> 官方描述：「海康威视400万+400万单枪版黑光臻全彩枪球一体机，采用双镜头设计，兼顾全景细节」
> 「全景采用1个 F1.0大光圈全彩镜头，可输出90°大场景画面」
> 传感器：`【全景】1/1.8＂ progressive scan CMOS,【细节】1/1.8＂ progressive scan CMOS`
> 光学变倍：`【细节】25倍`
> 补光灯距离：`【全景】30 m；【细节】250 m`；白光照射距离 `30 m`
> 宽动态：`支持120 dB超宽动态`

**RTSP / ONVIF / GB28181 证据（官网逐字行）**

> **支持协议**：`IPv4/IPv6，HTTP，HTTPS，802.1x，Qos，FTP，SMTP，UPnP，SNMP，DNS，DDNS，NTP，RTSP，RTCP，RTP，TCP/IP，UDP，IGMP，ICMP，DHCP，PPPoE，Bonjour`
> **接口协议**：`ISUP，软件集成的开放式API，ISAPI，海康SDK，E家协议，开放型网络视频接口，GB/T28181协议，萤石，视图库`

→ **RTSP ✔ / ONVIF（「开放型网络视频接口」）✔ / GB/T28181 ✔ 三者齐全，且为本文件中海康型号证据最强的一条（官网原文，非经销商复刻）。**

**该官网页的缺口**：未列出**分辨率明细、焦距、视场角、IP 防护等级** → 这四项记为「官方未标注」。

> ✅ **独立复核**：本报告作者用同一 Playwright 方案**独立重跑了一次** `https://www.hikvision.com/cn/products/pdplist/56646/`，逐字比对一致，并补到官网页的其余行：
> `数字变倍：【全景】不支持；【细节】16倍` ｜ `光学透雾：不支持` ｜ `垂直范围：【全景】7°~17°；【细节】-20~90°`
> `最大取流路数：20路` ｜ `用户管理：32个` ｜ `SD卡扩展：…最大支持256 GB` ｜ `报警：7路报警输入；2路报警输出`
> `工作温湿度：范围：-40 °C~70 °C；湿度小于95%` ｜ `除雾：支持` ｜ `尺寸：Ø242.6 mm × 423.6 mm` ｜ `重量：7.5 kg`
> **官网页确实没有「防护等级」行、没有「最大图像尺寸」行、没有「焦距」行、没有「视场角」行**（已翻到页面末尾「一般规范」分类确认）。
> 官网页同时提供该型号彩页下载 `DS-2SK8C144MH(彩页-M).pdf`（本次未下载核验）。

**同系列已枚举到的其他官网型号**（由同一 Playwright 渲染在官网「联动系列」下取得，id 为 pdplist 编号，**规格未逐一核验**）：
`DS-2SK8C144MH-D(25C0)(T5)`=/60392/ ｜ `DS-2SK8C144MH-D/SP/GLT/DG`=/58198/ ｜ `DS-2SK8C246IMX-D/AR/ZS`=/67995/ ｜ `DS-2SK8C284IMX-D/AR/5G`=/63997/ ｜ `DS-2SK8C144IMX-D(32C4)(T5)`=/60398/ ｜ `DS-2SK8C246IMX/LM`=/169498/ ｜ `DS-2SK8C144IMXS/LM`=/169572/

---

### H3b. 海康威视 iDS-2DC7C144MW-D(20X/F1)(S5)(B)（全彩全景智能枪球一体机）

来源：海康官方规格书 PDF，本地 `curl` 下载 + PyMuPDF 抽取。
URL: http://www.gzdcaf.com/Uploads/2022/03/03/1646275754156875.pdf

**逐字参数**

> 型号：`iDS-2DC7C144MW-D(20X/F1)(S5)(B)`
> 分辨率：全景 2560×1440（400 万）+ 细节 2560×1440（400 万）
> 焦距：`【全景】4 mm`；`【细节】4.8~96 mm，20倍光学变倍`
> 视场角：`【全景】水平视场角：88.7°`
> 宽动态：`120 dB超宽动态`
> 防护：`IP66`

**RTSP / ONVIF / GB28181 证据（规格书逐字行）**

> **支持协议**：含 `RTSP，RTCP，RTP`
> **接口协议**：`软件集成的开放式API，开放型网络视频接口，ISAPI，海康SDK，GB/T28181协议，支持视图库`

→ **三者齐全**，且证据来自**厂商官方规格书 PDF**（非经销商复刻）。

这是本文件里**唯一同时具备「官方规格书来源 + 全景水平视场角 + IP 等级 + 120 dB + 4/4 MP 双通道」**的海康型号，工程选型时可信度最高。

---

### H3c. 海康威视 DS-2SK8C144MH（臻全彩枪球一体机）— 旧记录（已被 H3 取代）

> 早期仅能读到页面标题「臻全彩枪球一体机 DS-2SK8C144MH」；后经 Playwright 渲染取得官网完整参数表，正式型号为 **`DS-2SK8C144MH-D/AR(25F1)(P3)`**，详见上方 H3 节。

---

### H4. 海康威视 (i)DS-2SK8C1ABCDE-XYZ/VWS（25 倍单枪版臻全彩枪球，400 万+400 万）

来源：中国政府采购网《肇庆市公安局"双反"一体化监测平台建设结果公告》（2023-11-22）主要标的信息，逐字引用官方参数。
URL: http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202311/t20231122_21124051.htm

> ⚠️ 型号中的 `ABCDE-XYZ` 是**招标文件的掩码写法**，不是可直接采购的完整型号；采购时需向海康索取对应实配型号。本行数据本身为官方参数字符串的逐字摘录。

**逐字参数**

> 「25倍单枪版臻全彩枪球 海康威视400万+400万单枪版臻全彩枪球一体机 全景采用1个F1.0大光圈全彩镜头，可输出90°大场景画面」
> 「细节采用高效红外阵列补光，照射距离最远可达200m 全景采用暖白光补光，补光距离30m」
> 「支持点击全景画面联动特写镜头，手动跟踪运动目标」
> 「IP67; 6000V 防雷、防浪涌、防突波，符合GB/T17626.2/3/4/5/6四级标准」
> 传感器类型：`【全景】1/1.8"" Progressive Scan CMOS，【细节】1/1.8"" Progressive Scan CMOS`
> 光学变倍：`【细节】25倍`
> 焦距：`【全景】4 mm；【细节】5.9~147.5 mm`
> 视场角：`【全景】90；【细节】59.8°~2.7°`
> 补光灯距离：`【全景】30 m；【细节】200 m`

**价格证据**：主要标的信息给单价 `13,300.00` 元、数量 3、总价 `39,900.00` 元。

**RTSP / ONVIF / GB28181**：该段参数未列协议行 → **官方未标注**。同公告中另一海康型号的协议原文可作为海康产品线的表述习惯参考（**不可外推**）：

> 「支持海康SDK、开放型网络视频接口、ISAPI、GB/T28181和ISUP接入」

---

### H5. 海康威视 DS-2SK7P2ABCDEFG-XYZL/VWL（标准版全局 Pro，三镜头）

同一中标公告来源：http://www.ccgp.gov.cn/cggg/dfgg/zbgg/202311/t20231122_21124051.htm

> ⚠️ 同为掩码型号。该机为**三镜头**（全景 + 细节 + 球机），严格说是"多摄联动"而非双镜头枪球。

**逐字参数**

> 「海康全局Pro摄像机集合定点看全景、细节看固定区域、球机联动的优势，采用一体化设计，内置3镜头。全景镜头、细节和球机传感器均采用1/1.8＂ CMOS,全景镜头采用6mm定焦镜头，细节镜头采用8-32mm变焦镜头，球机镜头采用13-52mm变焦镜头。」
> 焦距：`【全景】定焦6 mm 【细节】变焦8~32 mm，4×光学变倍 【球机】变焦13~52 mm，4×光学变倍`
> 视场角：`【全景】水平：55°，垂直：29°，对角线：65°`
> 补光灯距离：`暖白补光 【全景】50 m监控 【细节】20 m人脸 【球机】20 m人脸`
> 宽动态：`120 dB超宽动态`；防护：`IP66`

---

### D1. 大华 DH-SDT-7C1425-6P-GBZJ-AD3EKV

中文官网产品页：https://www.dahuatech.com/product/info/13652.html
**官方技术参数接口**（页面 JS 中 `var url = "https://www.dahuatech.com/ajax/product_new"; var pid = 13652;`，tab id 2 = 技术参数）：
https://www.dahuatech.com/ajax/product_new/13652/2

**RTSP / ONVIF / GB28181 证据（参数表逐字行）**

> **网络协议**：`HTTP；HTTPS；TCP/IP；IPv4；RTSP；UDP；SMTP；NTP；DHCP；DNS；DDNS；IPv6；802.1x；SSL；QoS；FTP；UPnP；ICMP；SNMP；IGMP；ARP；RTCP；RTP；PPPoE；RTMP；Bonjour；SMB；NFS`

**该表没有 ONVIF 行，也没有 GB/T28181 行** → 本型号仅 **RTSP 有官方依据**，ONVIF/GB28181 记为「官方未标注（中文站参数表未列）」。

**其他关键逐字行**

> 传感器类型：`全景：1/1.8英寸CMOS；细节：1/2.8英寸CMOS`
> 像素：`全景：600万；细节：400万`
> 最大补光距离：`全景：30m（白光）；细节：白光100m（白光）；红外200m（红外）`
> 补光类型：`全景：白光；细节：柔光双色`
> 光学变倍：`25倍`
> 宽动态：`全景：支持 细节：支持`
> 防护等级：`IP66；TVS 6000V防雷、防浪涌和防突波保护`
> 联动态：`全景周界联动细节跟踪（接力跟踪）`

**缺口**：中文参数表「镜头」分类下**只有光学变倍，没有焦距与视场角** → 官方未标注。

---

### D2. 大华 DH-SDT-7C1223-6P-GBZJ-AD3EKV

产品页：https://www.dahuatech.com/product/info/13653.html ｜ 参数接口：https://www.dahuatech.com/ajax/product_new/13653/2

> 传感器类型：`全景：1/1.8英寸CMOS；细节：1/2.8英寸CMOS`
> 像素：`全景：600万；细节：200万`
> 最大补光距离：`全景：30m（白光）；细节：白光100m（白光）；红外200m（红外）`
> 光学变倍：`23倍` ｜ 宽动态：`全景：支持 细节：支持` ｜ 防护等级：`IP66；TVS 6000V…`
> **网络协议**（同上，含 `RTSP`，**无 ONVIF / GB28181 行**）

---

### D3. 大华 DH-SDT-8C1425-6P-GAZJ-D3EFHV

产品页：https://www.dahuatech.com/product/info/13651.html ｜ 参数接口：https://www.dahuatech.com/ajax/product_new/13651/2

> 传感器类型：`全景：1/1.8英寸CMOS；细节：1/1.8英寸CMOS`
> 像素：`全景：600万；细节：400万`
> 最大补光距离：`全景：30m（白光）；细节：白光30m（白光）；红外250m（红外）`
> 补光类型：`全景：白光；细节：红外+柔光双色` ｜ 雨刷功能：`雨刷`
> 光学变倍：`全景：NA；细节：25倍`
> 云台旋转范围：`全景：水平不可调，垂直：5°～+24°（电动） 细节：水平：0°～360°连续旋转…`
> 防护等级：`IP67；TVS 6000V防雷、防浪涌和防突波保护`
> **网络协议**（含 `RTSP`，**无 ONVIF / GB28181 行**）

---

### D4. 大华 SDT4E425-8P-GB-APV1（**国际版**；国内对应系列需另行确认）

URL: https://www.dahuasecurity.com/products/network-products/ptz-cameras/x-spans-series/distribution/sdt4e425-8p-gb-apv1

**RTSP / ONVIF / GB28181 证据（规格表逐字行）**

> **Network Protocol**：`HTTP; HTTPS; TCP/IP; IPv4; RTSP; UDP; SMTP; NTP; DHCP; DNS; DDNS; IPv6; 802.1x; SSL; QoS; FTP; UPnP; ICMP; SNMP; IGMP; ARP; RTCP; RTP; PPPoE; RTMP; Bonjour; NFS`
> **Interoperability**：`ONVIF (Profile S & Profile G & Profile T & Profile M);CGI;SDK;P2P`

→ **RTSP ✔ / ONVIF ✔（Profile S,G,T,M）/ GB28181 未列出**。

**其他关键逐字行**

> Image Sensor：`Overview channel: 1/2.7" CMOS; Detail channel: 1/2.8" CMOS`
> Pixel：`Overview channel: 8 MP; Detail channel: 4 MP`
> Max. Resolution：`Overview channel: 4096 (H) × 1860 (V); Detail channel: 2560 (H) × 1440 (V)`
> Illumination Distance：`Overview channel: 30 m (IR); 30 m (white light); Detail channel: 100 m (IR); 50 m (white light)`
> Focal Length：`Overview channel: 2.8 mm; Detail channel: 5 mm–125 mm`
> Field of View：`Overview channel: H: 180°; V: 86°; Detail channel: H: 51.9°–3.0°; V: 39.7°–2.2°; D: 63.1°–3.7°`
> Optical Zoom：`Overview channel: NA; Detail channel: 25×`
> WDR：`Overview channel: DWDR; Detail channel: 120 dB`
> Protection：`IP66; TVS 6000 V lightning proof; surge protection; voltage transient protection`

---

### D5. 大华 SDT5X405-4F-QA-0600（**国际版**）

URL: https://www.dahuasecurity.com/products/PTZ-Cameras/WizMind-Series/SDT/4MP/SDT5X405-4F-QA-0600

**RTSP / ONVIF / GB28181 证据（规格表逐字行）**

> **Network Protocol**：`TCP; FTP; RTMP; IPv6; IPv4; DNS; RTCP; PPPoE; NTP; RTP; 802.1x; HTTPS; SNMP; DDNS; UPnP; ICMP; UDP; IGMP; HTTP; DHCP; SMTP; SNMP v1/v2c/v3 (MIB-2); QoS; RTSP; ARP`
> **Interoperability**：`CGI; ONVIF Profile S&G&T; GB/T28181`

→ **RTSP ✔ / ONVIF ✔ / GB28181 ✔ 三者齐全。**

**其他关键逐字行**

> Image Sensor：`Panorama: 1/1.8" CMOS  Detail: 1/1.8" CMOS`
> Pixel：`Panorama: 4 MP  Detail: 4 MP`
> Illumination Distance：`Panorama (white light): 30 m … Detail (IR light): 100 m`
> Focal Length：`Panorama: 6 mm  Detail: 10 mm–50 mm`
> Field of View：`Panorama: H: 57°; V: 31°; D: 66°  Detail: H: 45°–10°; V: 26°–5.7°; D: 51°–11.5°`
> Optical Zoom：`5×` ｜ WDR：`Panorama: 120 dB`
> Protection：`IP67; TVS 8000 V lightning protection; surge protection; voltage transient protection`

---

### D8. 大华中国大陆新增 4 个官方机型（均取自 `dahuatech.com/ajax/product_new/<pid>/2`）

**`DH-SDT-7C1424-4F-ZB-AD3E-0400`**（https://www.dahuatech.com/product/info/13683.html）逐字：

> 分辨率：全景 400 万（2560×1440）+ 细节 400 万（2560×1440）
> 传感器：全景 `1/1.8英寸CMOS`；细节 `1/2.8英寸CMOS`
> 焦距：`全景 4mm；细节 4.8mm～115m`（**原文单位写作「115m」，疑为官方笔误，引用时请原样标注**）
> 光圈：`全景 F1.0；细节 F1.6-F3.6`
> 视场角：`全景：水平95°，垂直52.5°，对角116°；细节：水平53.1°~3.4°`
> 补光：`全景：30m（白光）；细节：150m（红外）`；补光类型「红外+白光」
> 防护：`IP66`；TVS 6000V；「符合GB/T 17626.5 4级标准」
> 光学变倍：**细节 24 倍**
> ⚠️ **参数表无「网络协议」行、无「接入标准」行 → ONVIF / GB28181 / RTSP 全部官方未标注。**

**`DH-SDT-7C1432-4F-ZB-AD6E`**（https://www.dahuatech.com/product/info/13813.html）逐字：

> 全景通道：400W（2688×1520），1/1.8 英寸 CMOS，**WDR 106 dB**，焦距 4 mm，补光红外/白光，**红外 600 米**
> 细节通道：400W（2560×1440），1/1.8″ CMOS，**WDR 120 dB**，**32 倍光学变倍**，补光类型**暖白光**，**白光 300 米、红外 600 米**
> 防护：**IP67**；DC36V/POE；除雾支持；云台水平 0°~360°（连续旋转），垂直 -35°~90°，0.1°/s~500°/s
> ⚠️ 该表无协议行 → 官方未标注。

**`DH-SDT-6P425-4Z4/2-FAZF-D3EKV`**（https://www.dahuatech.com/product/info/13819.html）逐字：

> 品名「400W 三目枪球网络摄像机」；400W 像素（2688×1520）
> 传感器尺寸 `1/1.8＂`，**双 sensor 架构**（原文如此）
> 镜头行只写「焦距: 25 倍光学变倍」，**无 mm 值** → 焦距官方未标注
> 补光：`补光类型: 红外`、`补光距离: 100米` → **无全彩/暖光标注**
> **WDR 120dB**；**IP67**；**25 倍**
> ⚠️ 该表无协议行 → 官方未标注。

**`DH-SD-8S1440-4F-HNF-GAGS-A1D3E`**（https://www.dahuatech.com/product/info/13865.html）

> 全景通道 **800W（3840×2160）**，传感器 1/1.2 英寸；细节通道 **400 万（2688×1520）**，传感器 1/1.8 英寸
> 焦距行只给下限：「定焦镜头≥4mm，变焦镜头不低于40倍光学变焦」→ **无精确 mm 值**
> **WDR 120dB**；补光红外+白光（红外 ≥200 米、白光 ≥80 米）；**IP67**；-45℃~70℃
> ⚠️ 该表无协议行 → 官方未标注。**「不低于/≥」的措辞提示该页可能存在招标口径混入，引用需谨慎。**

**`DH-SDT-7C1223-4F-ZB-AD3-0400`**（**政府招标文件来源，本文件中大华唯一有「全景水平视场角 + 价格」双重可验证数据的机型**）

来源：威海市政府采购文件 PDF 第 20 页，供应商「浙江大华技术股份有限公司」。
URL: https://zfcg.ggzyjy.weihai.cn/gcfile/downALoad?attachId=b28f5183fd264300b94ba11d4fc180db&lock=c3482849c69a8a541bb0cd9662051be7

> `宽动态: 120dB 超宽动态`
> `23 倍光学变倍视场角: 【全景】水平视场角：79°，垂直视场角：42.4°`
> `红外照射距离: 【全景】30 m，【细节】150 m`
> `防护: IP66`
> 单价 **5500.00 元**

---

### D9. 大华国际版型号（**仅国际版**，供对照）

| 型号 | 关键规格 | 协议逐字 | URL |
|---|---|---|---|
| `SDT5X425-4Z4-FAJG-2812`（X-Spans Project，**SDT5X 系列**） | 全景 4MP 1/1.8″ 2.8–12 mm（4×）；细节 4MP 1/1.8″ 5.4–135 mm（25×）；`Panorama: H: 99.2°–45.8°`；`WDR Panoramic: 120dB Detail: 120dB`；`Panorama (white light): 30 m` / `Detail (IR light): 100 m`；`IP67; IK10; TVS 8000 V` | `Interoperability \| ONVIF;CGI`（网络协议行含 `RTSP`）；**无 GB28181** | https://previous.dahuasecurity.com/products/All-Products/PTZ-Cameras/X-Spans-Series/Project/SDT5X425-4Z4-FAJG-2812 |
| `SDT4E425-4F-MB-AGQ-PV1-EAU`（**SDT4E 系列**） | 全景 4MP 1/1.8″ 4 mm F1.0；细节 4MP 1/2.8″ 5–125 mm；`Field of View: Overview channel: H: 95°`；`WDR: Overview channel: 150 dB / Detail channel: 120 dB`；补光 `30 m (Warm light)` / `100 m (IR); 100 m (Warm light)`；`IP67` | `Interoperability \| CGI;SDK;P2P` → **无 ONVIF、无 GB28181**（网络协议行含 RTSP） | https://www.dahuasecurity.com/products/network-products/ptz-cameras/x-spans-series/distribution/sdt4e425-4f-mb-agq-pv1-eau=s2 |
| `DH-SDT4E425-4F-GB-A-PV1`（大华法国官方 datasheet PDF，本地 PyMuPDF 抽取） | 全景 4MP 1/2.8″ F1.0 2,8 mm；细节 4MP 1/2.8″ STARVIS 5–125 mm F1.6–F3.6，25×；`Champ de vision: Panorama: H: 101°. V: 53°. D: 120°.`；`WDR 120 dB`；`Protection (IP66, TVS 6 000 V)` | `Interopérabilité \| ONVIF (Profils S, G et T) ; CGI ; SDK`（网络协议行含 `RTSP`）；**无 GB28181** | https://france.dahuatech.com/upload/202312/19/202312191905290881.pdf |
| `IPC-PFW8840-A180`（国际版官方 datasheet PDF） | 1/2.8″ **4 × 2 MP** CMOS，4096×1800；2.8 mm F1.6 定焦；`По горизонтали: 180°; По вертикали: 90°`；补光 30 m IR；WDR 仅 `DWDR`（**无 dB**）；`Защита IP67, IK10` | `Совместимость \| ONVIF (Profile S/Profile G/Profile T); CGI; P2P; Milestone; Genetec`；网络协议行含 `RTSP`；**无 GB28181**。**无细节通道**，是纯 180° 拼接全景多摄，**不是枪球联动** | https://www.dahuasecurity.com/asset/upload/uploads/soft/20200831/DH-IPC-PFW8840-A180_datasheet_20200805_rus.pdf |
| `IPC-PFW83242-A180-S2`（国际版，32MP 180° 全景） | 1/1.8″ CMOS，8192×3840（32MP，8×4MP）；2.8 mm F1.6；`Field of View: H: 180°; V: 100°`；补光 30 m IR（8 颗）；WDR 仅 `DWDR`；`Protection: IK10; IP67` | `Interoperability \| ONVIF (Profile S/Profile G/Profile T); CGI`；网络协议行含 `RTSP`；**无 GB28181**。**无细节通道** | https://previous.dahuasecurity.com/products/All-Products/Network-Cameras/WizMind-Panoramic-Series/Multi-Sensor-180-Series/IPC-PFW83242-A180-S2=S2 |

---

### U1. 宇视 IPC-E98244-FW@X33-E2-VH1

URL: https://cn.uniview.com/Products/Professional/Camera/5/
页面标题即型号名，副标题「400万+400万超星光级全景拼接枪球一体化联动网络摄像机」。

**官方产品特点逐字（该页只有卖点，无完整规格表）**

> 「宇视全景双拼枪球一体机，采用三镜头设计，兼顾全景细节」
> 「采用1/1.8" 高灵敏度CMOS传感器，满足超星光级监控需求，夜间图像清晰度高」
> 「全景采用前沿拼接技术，可输出水平190°±5°、垂直55°大场景拼接画面」
> 「全景支持最大3840×1080@30fps高清画面输出，细节支持最大2688×1520@30fps高清画面输出」
> 「支持单IP双通道，可同时预览全景和细节实况画面」
> 「支持全景通道触发区域入侵、越界检测、进入区域、离开区域规则后自动联动细节通道摄像机进行机非人目标跟踪、抓拍」
> 「支持接管跟踪，当跟踪的目标离开全景通道后，细节通道摄像机继续对目标进行跟踪，扩大跟踪范围」
> 「全光谱补光方案，全景通道支持30米暖光补光，细节通道支持250米红外补光」

**RTSP / ONVIF / GB28181**：该页**没有参数表、也没有协议行** → 记 **官方未标注（宇视中国官网产品页未列）**。宇视完整协议表见其产品手册（PDF），本环境 `web_fetch` 无法读取 PDF，故未取到一手证据。

**缺口**：焦距、光学变倍、宽动态、防护等级在官网产品页均未标注。

**价格证据（第三方可核验）**：内蒙古自治区乌兰监狱监控摄像机电子反拍项目采购公告（2025-11-26）列「宇视/Uniview IPC-E98244-FW@X33-E2-VHI 400万/2688×1520/30m」8 台，限价 **8,600.00 元/台**。
URL: https://www.yfbzb.com/inviteBid/detail/20251126_556842932.html
（注意：该文件型号写作 `VHI`，疑为 `VH1` 录入差异。）

---

### U2. 宇视 IPC-E98344-IR@L-X40-E8-W-VH3（32MP+8MP 天宫全景联动一体机）

URL: https://cn.uniview.com/Products/Professional/Camera/18/

**官方产品特点逐字**

> 「全景采用前沿拼接技术，可输出水平360°全景画面」
> 「全景支持最大11520*2700@30fps高清画面输出，细节支持最大3264*2448@30fps高清画面输出」
> 单 IP 双通道；动态拼接（可实时自动调整）；雨刷；联动声光告警

**协议**：该页无协议行 → **官方未标注**。

**价格证据**：政府采购开标一览表列「高位监控摄像机 宇视 `IPC-E98344-IR` 9 台 27,295 元」。
URL: https://zcy-gov-open-doc.oss-cn-north-2-gov-1.aliyuncs.com/1024FPA/330299/10009100229/202512/a6332d6f-f2e9-4724-9b43-e2b43066a609.pdf

**⚠️ 已发现的参数冲突（须向厂商确认）**：官网 `11520×2700 / 3264×2448` ↔ 采购文件抄录 `8192×1800 / 2688×1520` ↔ 国际版 `32MP / 4MP`；采购文件的「细节焦距 6.0–150.0 mm」与型号中的 `X40`（40 倍）数学上不自洽。**采购前务必确认子型号与版本。**

---

### U3. 宇视 HIC93441-IR@X4-F40-VH1（双 400 万超星光深度智能一体化联动网络摄像机）

URL: https://cn.uniview.com/Products/Professional/Camera/15/

**官方产品特点逐字**

> 「全景和细节通道均采用1/1.8"高灵敏度CMOS传感器，满足超星光级监控需求」
> 「**120dB光学宽动态**，根据环境亮度自动切换，满足高反差场景监控需求」
> 分辨率：全景 400 万 2688×1520 + 细节 400 万 2688×1520

**协议**：该页无协议行 → **官方未标注**。

**替代证据（国际版，型号不等同）**：`IPC98344ER-GX42-E8-W-VH3` 与 `IPC94144SR-X25-F40C` 的官方完整规格表见总表；其中 GB28181 在两份国际版官方文件中**命中 0，未声明**。

**宇视 GB28181 的边界说明**：大陆机型**无型号级 GB28181 证据**。唯一可核验的是宇视中国官网**通用**《网络摄像机 用户手册 V3.04》(2023-09) 逐字：

> 「通过GB/T28181 协议接入 1. 选择[配置>网络>平台接入]…3.''协议类型''选择''GB/T28181''。」
> 「每台设备最多被2 个平台管理，被2 个平台管理时，平台2 只可选择GB/T28181 协议。」

URL: https://cn.uniview.com/res/202309/14/20230914_1638820_网络摄像机用户手册-V3.04_809884_194214_0.pdf
**这只能证明宇视产品线支持 GB/T28181，不能证明具体型号支持。**

**已排除的渠道（证明「查不到」属实）**：宇视中国站彩页 PDF 穷举 40 种路径组合全部 404；sitemap 中的 PDF 主机 `cms-cn.uniview.com` 已 NXDOMAIN；中国官网手册下载中心全部 PDF 逐条核对后**无任何 E98 / HIC93441 专业产品手册**；站内搜索接口仅索引 `Case` 单一索引；`/Products/Professional/Camera/1..26/` 已全部枚举，枪球/全景/联动类即上述 3 个型号。

---

### D6. 大华 DH-PSDW81243S-A270-D425-G（哈勃守望者，全景+细节双通道）

URL: https://www.dahuatech.com/product/info/14042.html ｜ 参数接口：https://www.dahuatech.com/ajax/product_new/14042/2

**RTSP / ONVIF / GB28181 证据（参数表逐字行）**

> **接入标准**：`ONVIF（Profile S & Profile G & Profile T）；CGI；GB/T28181-2022（双国标）；GB/35114A`
> **网络协议**：`HTTP；HTTPS；TCP；ARP；RTSP；RTP；UDP；RTCP；SMTP；FTP；DHCP；DNS；DDNS；PPPoE；IPv4/v6；SNMP；QoS；UPnP；NTP`

→ **三者齐全（ONVIF + RTSP + GB/T28181-2022）**，且为大华中国官网原文。

**其他关键逐字行**

> 传感器类型：`通道1（全景）：1/2.8英寸CMOS；通道2（细节）：1/1.8英寸CMOS`
> 像素：`通道1（全景）：1200万；通道2（细节）：400万`
> 镜头焦距：`通道1（全景）：2.8mm；通道2（细节）：5.3mm～134mm`
> 镜头光圈：`通道1（全景）：F1.0；通道2（细节）：F1.6～F4.0`
> 最大补光距离：`通道1（全景）：不支持；通道2（细节）：100m（红外）`
> 宽动态：`通道1（全景）：120dB；通道2（细节）：120dB`
> 防护等级：`IP67`
> 工作温度：`-40℃～+60℃`

**缺口**：该参数表**未列视场角** → 全景水平视场角官方未标注。

---

### D7. 大华 DH-PSDW8638S-B360（高清 600 万像素全景特写网络摄像机）

URL: https://www.dahuatech.com/product/info/4491.html ｜ 参数接口：https://www.dahuatech.com/ajax/product_new/4491/2

**RTSP / ONVIF / GB28181 证据（参数表逐字行）**

> **接入标准**：`ONVIF；GB/T28181；CGI`
> **网络协议**：`HTTP；HTTPS；TCP；ARP；RTSP；RTP；UDP；RTCP；SMTP；FTP；DHCP；DNS；DDNS；PPPoE；IPv4/v6；SNMP；QoS；UPnP；NTP`

→ **三者齐全。**

**其他关键逐字行**

> 外观：`守望者` ｜ 传感器类型：`1/2.7英寸CMOS`
> 像素：`800万` ｜ 最大分辨率：`1920×1080×4`
> 镜头焦距：`全景：2mm；细节：2.7mm～13.5mm`
> 最低照度：`0.002lux（彩色模式）；0.0002lux（黑白模式）`

**缺口**：该参数接口返回的表**无补光距离行、无宽动态行、无防护等级行、无视场角行** → 均记「官方未标注」。

---

### T1–T4. TP-LINK

TP-LINK 数据由并列调研线程从 tp-link.com.cn 规格参数页（HTML，可完整抓取）核验，完整清单见同目录 `TP-LINK_双摄全景_规格调研.md`。

**TL-IPC679V-A4**（https://www.tp-link.com.cn/product_3466.html?v=specification）协议逐字行：

> `接口协议：ONVIF`
> `支持协议：TCP/IP，ICMP，HTTP，DHCP，DNS，DDNS，RTP，RTSP，RTCP，PPPoE，NTP，UPnP`

→ ONVIF ✔ / RTSP ✔ / **GB28181 未列出**。

**TL-IPC54L4V-WD20**（https://www.tp-link.com.cn/product_3186.html?v=specification）协议逐字行同 679V-A4 句式（ONVIF 行 + RTSP 行，无 GB28181）。
视场角逐字：`水平：169°（4mm机型）` ／ `垂直：44°（4mm机型）`。

**TL-IPC55T2**（https://www.tp-link.com.cn/product_1605.html?v=specification）协议逐字行：

> `支持协议：TCP/IP，ICMP，HTTP，DHCP，DNS，DDNS，RTP，RTSP，RTCP，NTP，UPnP，802.11n，802.11g，802.11b`

→ RTSP ✔；**ONVIF 未列出；GB28181 未列出**（该表亦无「接口协议：ONVIF」行）。
全景 FOV 来自产品描述页原句：「鱼眼镜头水平、垂直可视角度为180°」。

**TL-IPC48DW 双摄版**（https://www.tp-link.com.cn/product_4335.html?v=specification）——本批中**唯一**规格表明列 GB28181 的双摄机型：

> `支持协议：TCP/IP，ICMP，HTTP，DHCP，DNS，DDNS，RTP，RTSP，RTCP，NTP，GB28181,ONVIF,802.11 b/g/n/ac/ax`

---

## 三、横向结论

1. **协议支持（最重要的选型结论）**——本文件中**同时具备 RTSP + ONVIF + GB28181 官方逐字证据**的型号共 10 个：

   | 型号 | 证据强度 | 关键逐字 |
   |---|---|---|
   | 海康 `DS-2DC7X144DMW(25xF1)` **7寸全景枪球** | ★★★ **官网原文**（Playwright 渲染） | `ISAPI，开放型网络视频接口，GB28181-2022，ISUP（5.0），SDK` + `RTSP` —— **国标为最新 2022 版** |
   | 海康 `DS-2DC7X144DW(40xF1)` **7寸全景枪球 40 倍** | ★★★ **官网原文** | 同上两行**完全相同** |
   | 海康 `DS-2DC7X144DMW-B(25xF1)` **7寸全景枪球** | ★★★ **官网原文** | 同上两行**完全相同** |
   | 海康 `DS-2SK8C144MH-D/AR(25F1)(P3)` | ★★★ **官网原文**（已独立复跑验证） | `开放型网络视频接口`、`GB/T28181协议`、`RTSP` |
   | 海康 `DS-2SK8C144MH-D(25C0)(T5)` | ★★★ **官网原文** | 同上，另含 `WebSocket，WebSockets` |
   | 海康 `iDS-2DC7C144MW-D(20X/F1)(S5)(B)` | ★★★ **厂商规格书 PDF** | `开放型网络视频接口`、`GB/T28181协议`、`RTSP，RTCP，RTP` |
   | 海康 `iDS-2SE7C124IW-DB(32X/F1)(S5)` | ★★ 行业媒体复刻官方表 | `开放型网络视频接口`、`GB/T28181协议`、`RTSP` |
   | 大华 `DH-PSDW81243S-A270-D425-G` | ★★★ **大华中国官网参数表** | `ONVIF（Profile S & Profile G & Profile T）…GB/T28181-2022（双国标）`、`RTSP` |
   | 大华 `DH-PSDW8638S-B360` | ★★★ **大华中国官网参数表** | `ONVIF；GB/T28181；CGI`、`RTSP` |
   | TP-LINK `TL-IPC48DW 双摄版` | ★★★ TP-LINK 官网规格表 | `…RTSP，RTCP，NTP，GB28181,ONVIF,…` |
   | 大华 `SDT5X405-4F-QA-0600`（**国际版**） | ★★★ 大华国际官网参数表 | `CGI; ONVIF Profile S&G&T; GB/T28181`、`RTSP` |

   > **首选推荐**：若「全景+细节双通道 + 400 万+400 万 + RTSP/ONVIF/GB28181-2022 三者齐全 + 官网可查」是硬指标，**海康 `DS-2DC7X144DMW(25xF1)` 是本次调研中唯一全部满足且证据等级最高（官网原文）的型号**。

2. **大华：中国区机型协议信息普遍缺失，且「PSDW 全景」系列明显优于「SDT 枪球」系列**——
   - `DH-PSDW81243S-A270-D425-G`、`DH-PSDW8638S-B360`（中国官网）**明确列出** `ONVIF（Profile S & Profile G & Profile T）` / `ONVIF；GB/T28181` 与 `RTSP`。
   - 而中国区 SDT 机型中，`DH-SDT-7C1223-6P / 7C1425-6P / 8C1425-6P` 的「网络协议」行**只列 RTSP，无 ONVIF 行、无 GB28181 行**；`DH-SDT-7C1424-4F-ZB-AD3E-0400`、`DH-SDT-7C1432-4F-ZB-AD6E`、`DH-SDT-6P425-4Z4/2-FAZF-D3EKV`、`DH-SD-8S1440-4F-HNF-GAGS-A1D3E` 甚至连**「网络协议」行都没有** → 协议全部「官方未标注」。
   - ⚠️ **不可用国际版页面替中国区机型断言 ONVIF/GB28181**：国际版 `SDT5X425` 为 `ONVIF;CGI`、`SDT4E425-4F-MB-AGQ-PV1-EAU` 为 `CGI;SDK;P2P`（**连 ONVIF 都没有**）、法国版 `DH-SDT4E425-4F-GB-A-PV1` 为 `ONVIF (Profils S, G et T)`，**三者均无 GB28181**。
   - **结论：若项目强制 GB28181 且要大华枪球形态，务必先向大华中国区索取该具体型号的中文协议清单。**

3. **防护等级**：全景枪球主流 **IP66**（海康 `iDS-2SE7C184IMX-D`、`iDS-2DC7C144MW-D`、大华 7C/8C 双拼、大华 `SDT4E425`、宇视国际版 `IPC94144SR`、TP-LINK 室外机）；**IP67** 见于海康 25 倍臻全彩枪球 `(i)DS-2SK8C1…`、大华 `SDT5X405`、大华 `DH-PSDW81243S-A270-D425-G`、宇视国际版 `IPC98344ER`（IP67/IK10）。TP-LINK 室内机（`55T2`、`48DW`）规格表**无防护等级行**。

4. **宽动态**：海康给 dB 值最干脆（`120dB超宽动态`）；大华分两类——`PSDW` 系列给 `120dB`（双通道都标），`SDT` 双拼中文表只写「支持」不给数值；国际站常**仅细节通道**给 `120 dB`、全景通道为 `DWDR`；**TP-LINK 全系规格表无宽动态行**。

5. **全景视场角差异极大，是选型分水岭**：
   - **单镜头广角全景**：55°~90°（海康 `DS-2SK8C144MH-D` 90°、`iDS-2SE7C184IMX-D` 88.7°、`iDS-2DC7C144MW-D` 88.7°；大华 `SDT5X405` 仅 57°；海康 `DS-2SK7P2` 仅 55°）
   - **双目/多目拼接全景**：169°~360°（大华 `SDT4E425` 180°、宇视 `IPC-E98244` 190°±5°、宇视 `IPC-E98344` 360°、宇视国际版 `IPC98344ER` 360°、TP-LINK 双目拼接机 169°~180°）
   - ⚠️ **TP-LINK 的「双目拼接」类产品只有一路输出、不构成「全景+细节」双通道**，与真正的枪球联动不是一类设备。

6. **价格**（可验证的采购价/官方标价，均已附 URL）：
   - 海康 `(i)DS-2SK8C1ABCDE-XYZ/VWS` **13,300 元/台**（中国政府采购网中标公告）
   - 海康 `(i)DS-2SK8C2ABCDE-XYZ/VWS` **7,900 元/台**（淄博招标文件，两处报价一致）
   - 海康 `iDS-2SE7C144MW-DB/ZS(32xF0)(P3)` **5,500 元/台**（淄博招标文件）
   - 宇视 `IPC-E98244-FW@X33-E2-VH1` 限价 **8,600 元/台**（内蒙古乌兰监狱反拍公告）
   - 宇视 `IPC-E98344-IR` 中标 **27,295 元/台**（政府采购开标一览表）
   - TP-LINK 官方商城标价：`TL-IPC679V-A4` **¥549**、`TL-IPC55T2` **¥499**、`TL-IPC48DW双摄版` **¥489**
   - 其余工程机型（海康 SK8C 系列其余后缀、大华全系、宇视 HIC93441）官网均无公开报价 → **需询价**

---

## 四、未验证 / 存疑（务必人工复核）

| 项 | 状态 |
|---|---|
| 海康官网 `www.hikvision.com/cn` 正文 | ⚠️ **已部分解决**：`curl` 被 JS 反爬拦截、`web_fetch` 正文被导航截断，但改用**本机 Playwright + Chrome for Testing 无头渲染**后已成功取得 `DS-2SK8C144MH` 官网逐字参数表。其余海康官网详情页仍建议用同一方法复核 |
| 海康 `DS-2SK8C144MH-D/AR(25F1)(P3)` 的分辨率明细/焦距/视场角/IP 等级 | 官网该页**未列** → 官方未标注（须向海康索取完整规格书） |
| 海康 `iDS-2SE7C144MW-DB` | ✅ **已取得**：`iDS-2SE7C144MW-DB/ZS(32xF0)(P3)` 完整参数 + 中标单价 5,500 元/台（淄博招标 PDF 第 314 页）。但用户所写的精确后缀 `(32X/F1)(S5)` 未单独验证 |
| 海康 `iDS-2SE7C425MWG-EB/26(F0)` | ⚠️ **仅验证到国际版** `DS-2SE7C425MWG-EB/26(F0)` 的德国经销商规格书（IP66/120dB/180°±10°/25×/ONVIF Profile G,S,T/RTSP）；**中国区型号未取得官方页面** |
| 海康 `iDS-2SE7C184IMX-D(23xF1)` 的协议行 | 经销商复刻页**与**浙江政采 PDF 均未列，且该 PDF/jdzj 均**未列 IP 之外的分辨率以外协议** → 官方未标注 |
| 宇视 `IPC-E98244-FW@X33-E2-VH1` / `IPC-E98344` / `HIC93441` 的焦距/变倍/WDR/IP/协议 | 官网产品页无规格表 → 官方未标注；宇视中国站彩页 PDF 与手册中心已穷举核查，**确无专业产品规格书** |
| 大华中文站 7C/8C 双拼机的焦距与视场角；`DH-PSDW81243S-A270-D425-G` 的视场角；`DH-PSDW8638S-B360` 的补光/WDR/IP | 中文参数表未列 → 官方未标注 |
| 大华 `DH-SDT4E423-4F-ZB`（用户点名） | ❌ **经 4 组检索变体（`"SDT4E423-4F-ZB"` / `"DH-SDT4E423"` / `大华 4E423 枪球 4F-ZB` / `dahua "SDT4E423"`）0 命中，大华官网任何页面均无此字符串。判定：无官方依据，疑为型号讹传**（真实族名为 `SDT4E425-4F-…`，**425 不是 423**）。**建议不要写入采购清单。** |
| `DH-IPC-PFW` 系列 | ⚠️ **该命名在中国大陆不存在**：已对 dahuatech.com **28 个品类全量扫描**（area=2399/2400/2406/2401/2416/2402/2403/2417/2404/2405/2407/2408/15/1655/1654/16/1667/20/2077/22/1480/1478/1479/1045/1046/1047/1048/1481），`IPC-PFW` 出现 **0 次**；中国区全景多摄统一用 `DH-PSDW*`。`IPC-PFW*` 仅存在于大华国际站（已收录 `IPC-PFW8840-A180`、`IPC-PFW83242-A180-S2` 等，且**均无细节通道、不是枪球联动**） |
| 大华 `SDT4E` / `SDT5X` 中国区型号 | **中国区无任何 SDT4E / SDT5X 型号**；SDT6 系列在中国区以 `DH-SDT-6P425-4Z4/2-FAZF-D3EKV` 存在。`SDT4E425-4F-MB-AGQ-PV1-EAU`、`SDT5X425-4Z4-FAJG-2812` 等**仅验证到国际版** |
| 海康 `iDS-2SE7C124IW-DB(32X/F1)(S5)` 的传感器尺寸与 IP 等级 | 所抓参数页未列 → 官方未标注 |
| 海康 `DS-2SK8C144MH-D(25C0)(T5)`、`DS-2SK8C246IMX-D/AR/ZS` 等官网其余 6 个型号 | 已从官网「联动系列」枚举到型号与 pdplist id，但**规格未逐一核验** |
| 宇视 `IPC-E98344` 的参数冲突 | 官网 `11520×2700 / 3264×2448` ↔ 采购文件 `8192×1800 / 2688×1520` ↔ 国际版 `32MP / 4MP`；采购文件「6.0–150.0mm」与型号 `X40`（40 倍）不自洽 → **需向厂商确认子型号/版本** |
| 芜湖/郑州/马鞍山等招标 PDF 中的「结构化枪球一体摄像机」「全彩枪球摄像头」「双拼全景摄像头」 | 这些是**采购方写的要求条款**，清单中**未给品牌型号**（如马鞍山件要求「3 个镜头、全景 2 个 F1.0、190° 拼接、拼接分辨率 800w:5120*1440、细节 400W:2688x1520、IP66、支持 GB/T28181-2022、GA/T1400、GB/35114 A 级」），**不可当作型号规格引用** |
| `(i)DS-2SK8C1ABCDE-XYZ/VWS`、`(i)DS-2SK8C2ABCDE-XYZ/VWS`、`DS-2SK7P2ABCDEFG-XYZL/VWL` | 均为**招标掩码型号**，`ABCDE-XYZ` 不是可采购的完整型号；数据本身逐字可靠，但下单前须向海康索取实配型号 |
| 宇视 GB28181 | 大陆机型**无型号级证据**；仅有通用《网络摄像机用户手册 V3.04》证明产品线支持，不能证明具体型号 |
| 宇视国际版全系 GB28181 | 两份国际版官方规格表（`IPC98344ER`、`IPC94144SR`）中 **GB28181 命中 0** → 未声明 |

> 本文件所有数值均可在上述 URL 中逐字复核。任何未在上文出现的型号、参数或 URL 均属未验证信息，请勿引用。
