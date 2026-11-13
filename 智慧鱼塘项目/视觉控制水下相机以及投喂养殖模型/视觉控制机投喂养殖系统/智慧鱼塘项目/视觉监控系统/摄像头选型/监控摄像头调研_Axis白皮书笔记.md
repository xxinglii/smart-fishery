# Axis《基于 IEC 62676-4:2014 标准的像素密度》白皮书 — 原始数值提取笔记

> 调研目的：提取 Axis Communications 白皮书 *Pixel density based on IEC 62676-4:2014*
> （亦名 *Pixel density and DORI*）中 DORI / 像素密度阈值的**精确原文数值**，
> 并给出 100 m 处 1.7 m × 0.3 m 目标在各档位所需的像素密度与水平像素数。
>
> 调研方式：直接下载并解析 Axis 官方 PDF 原文（PyMuPDF 提取文本），**不是二手转述**。
> 调研日期：本次会话。

---

## 0. 一句话结论（先看这里）

1. **目标白皮书里只有 4 档，不是 5 档。** 原文表格为
   `Detection 25 px/m`、`Observation 63 px/m`、`Recognition 125 px/m`、`Identification 250 px/m`。
2. **该白皮书中不存在 "Monitor" 档，也不存在任何 `12.5 px/m` 的数值。**
   对全文做过字符串检索：`12.5` 在白皮书（中/英/日/葡）中命中 **0 次**。
   —— 任务书里 "Axis 通常用 Monitor/Detect/Observe/Recognise/Identify 五档、
   Monitor = 12.5 px/m" 这一前提，**未能从 Axis 官方文档中得到证实**。
3. `12.5` 与 `Monitor` 这两个概念在 Axis 的**另一份更老的文章**里确实出现过，但含义完全不同：
   - `12.5` 是 **px/inch（每英寸像素）**，用于"挑战性条件下的人脸辨认"，不是 px/m；
   - `Monitor` 是 **人体高度占画面百分比 = 5%** 的档位（模拟时代遗留），不是 px/m 档位。
   详见 §4。
4. Axis 在 **IEC 62676-4:2025 版**白皮书中把档位扩展到了 **7 档**：
   `20 / 40 / 80 / 125 / 250 / 500 / 1500 px/m`（Overview…Scrutinize）。同样没有 Monitor、没有 12.5。
5. 注意一个**易踩的坑**：中文版把 `Recognition` 译作「**识别**」，把 `Identification` 译作「**验证**」，
   与中文安防行业习惯（识别≈Identify）正好错位。做中文标书时务必按原文对齐。

---

## 1. 主表：档位 → 像素密度 → 来源 URL

### 1.1 目标文档（IEC 62676-4:2014 版，4 档）

**我实际读取的原文 URL（HTTP 200，已下载并解析成功）：**

- 中文版（任务指定目标文档）：
  <https://whitepapers.axis.com/download/wp_pixel_density_and_dori_t10176489_zh_2501.pdf>
- 英文版：
  <https://whitepapers.axis.com/download/wp_pixel_density_based_on_iec_62676_4_2014_t10176489_2510.pdf>

| 档位（英） | 档位（中文原文） | px/face | **px/m** | px/ft | 来源 |
|---|---|---|---|---|---|
| Detection | 侦测 | 4 像素/面部 | **25** | 8 | 中文版 p.2、p.5 表格3.1；英文版 Table 3.1 |
| Observation | 观察 | 10 像素/面部 | **63** | 20（精确 19） | 同上 |
| Recognition | 识别 | 20 像素/面部 | **125** | 40（精确 38） | 同上 |
| Identification | 验证 | 40 像素/面部 | **250** | 80（精确 76） | 同上 |

> ⚠️ **注意是 63 而不是 62.5。** Axis 白皮书原文写的就是 `63 px/m`。
> IEC 标准原表用 62.5 px/m，Axis 在转换时取整成了 63。这个差异是原文差异，不是笔误。

**原文脚注（英文版 Table 3.1 下方星号）：**
> "IEC 62676-4:2014 lists the values in px/m. For markets that measure in feet instead of meters,
> we convert the standardized values to px/ft. Axis product datasheets list accurately converted
> values (19, 38, and 76 px/ft), and use them for distance calculations. In practice, however,
> the more rounded values (20, 40, and 80 px/ft) are often used."

**原文人脸宽度假设（§3.1）：**
> "based on the assumption that an average human face has a width of 16 cm, or 6 5/16 inches."
> （中文版：「假设平均人脸宽度为16厘米或6 5/16英寸」）

**原文关于 40 px 的建议：**
> "It is usually recommended, for example in IEC 62676-4:2014, to have at least 40 pixels across
> the width of a human face to enable identification."
> （中文版：「如果是辨认用途，通常建议（比如在IEC 62676-4:2014中）让人脸宽度包含至少40个像素。」）

### 1.2 各档位的官方定义（Table 2.1 原文）

中文版表格 2.1「视频监控中的常见运行需求」（原文照录）：

| 运行需求 | 图像细致度（原文） |
|---|---|
| **侦测** Detection | 能够确定是否存在某个个体。 |
| **观察** Observation | 能够确定存在多少人，且能够看到个体的特征细节，比如有辨识性的服装。 |
| **识别** Recognition | 观看者能够确定所显示的个体是否与曾经所看到的某个个体相同。 |
| **验证** Identification | 能够验证个体身份。 |

英文版 Table 2.1（原文照录）：

| Operational requirement | Level of detail |
|---|---|
| Detection | It is possible to determine whether or not any individual is present. |
| Observation | It is possible to determine how many people are present and to see characteristic details of individuals, such as distinctive clothing. |
| Recognition | It is possible for a viewer to determine whether or not an individual shown is the same as someone they have seen before. |
| Identification | It is possible to identify an individual. |

**原文配图说明（Figure 2.1）：**
> "The person closest to the camera is close enough for identification. The person in the middle
> can be recognized, while the person farthest away can only be detected."

### 1.3 「目标占屏幕高度 X%」——白皮书里**没有**这个表

任务书要求提取「target covers X% of screen height」的数值。**本白皮书中不存在这样的表格，标为「未核实」。**

白皮书中与之**相关但不等价**的两处原文：

1. **像素计数器示例（Figure 4.2，p.8 / 中文版 p.7）：**
   > 英文：「The tool shows that we have 258 pixels across the frame, which means that Validate is
   > possible (requiring at least 80 pixels across the face).」
   > 中文：「此工具显示，边框范围内有258个像素，这就意味着，可以达到验证目的（其要求人脸至少包含80个像素）。」

   ⚠️ **此处与 Table 3.1 自相矛盾**：Table 3.1 说 Identification 只需 40 px/face，
   但 Figure 4.2 的图注说需要 80 px/face。
   （80 px/face 对应的是 Axis 老文章里"挑战性条件"下的 500 px/m = 5 px/cm 口径，见 §4。）
   **引用时请以 Table 3.1 为准，并对这个内部不一致保持警惕。**

2. **显示器分辨率免责声明（原文）：**
   > "if an external display is used to monitor the scene, the ability to detect, observe,
   > recognize, or identify individuals depends highly on the screen resolution of that display."

---

## 2. 100 m 处、目标 1.7 m（高）× 0.3 m（宽）的计算

> **重要声明：本节全部为我自己按白皮书阈值做的算术推算，白皮书中没有这张表。**
> 白皮书只给了 px/m 阈值与 16 cm 人脸宽度假设，不含 1.7 m / 0.3 m 目标的规定。

### 2.1 目标上的像素数（只要目标本身成像，像素数就这么多）

公式：`目标横向像素 = 像素密度 × 0.3 m`；`目标纵向像素 = 像素密度 × 1.7 m`

| 档位 | 阈值 px/m | 0.3 m 宽度上像素数 | 1.7 m 高度上像素数 |
|---|---|---|---|
| 侦测 Detection | 25 | **7.5 px** | **42.5 px** |
| 观察 Observation | 63 | **18.9 px** | **107.1 px** |
| 识别 Recognition | 125 | **37.5 px** | **212.5 px** |
| 验证 Identification | 250 | **75.0 px** | **425.0 px** |

（对照：白皮书的 16 cm 人脸 → 250 × 0.16 = 40 px，与"40 px/face"自洽；
125 × 0.16 = 20 px，与"20 px/face"自洽。✓）

**"总共需要多少水平像素"必须先确定画面覆盖宽度**，因为
`水平分辨率 H = 像素密度(px/m) × 该距离处的画面宽度 W(m)`。

- 若画面宽度恰好只框住目标本身（W = 0.3 m）：
  `H ≥ 7.5 / 18.9 / 37.5 / 75 px` —— 数值极小但需要超长焦
  （该处 HFOV = 2·atan(0.15/100) ≈ **0.172°**）。
- 更实用的反推：**给定水平分辨率，100 m 处能覆盖的最大画面宽度**

| 摄像机水平分辨率 | 侦测 25 | 观察 63 | 识别 125 | 验证 250 |
|---|---|---|---|---|
| 1920 px（1080p / 2 MP） | 76.8 m | 30.5 m | 15.4 m | **7.7 m** |
| 2560 px（4 MP，2560×1440） | 102.4 m | 40.6 m | 20.5 m | **10.2 m** |
| 3840 px（4K / 8 MP） | 153.6 m | 61.0 m | 30.7 m | **15.4 m** |

- 另一种常见口径：**让 1.7 m 的人正好占满画面高度**（16:9 → 画面宽 3.02 m），
  则所需水平分辨率：

| 档位 | px/m | 所需水平分辨率 |
|---|---|---|
| 侦测 | 25 | 76 px |
| 观察 | 63 | 190 px |
| 识别 | 125 | 378 px |
| 验证 | 250 | 756 px |

- 需要的镜头焦距（近似 `f = 像素密度 × 像元尺寸 × 距离`，
  以 1/2.8" 2 MP、像元 2.92 µm 为例，d = 100 m）：

| 档位 | px/m | 所需焦距（约） |
|---|---|---|
| 侦测 | 25 | 7.3 mm |
| 观察 | 63 | 18.4 mm |
| 识别 | 125 | 36.5 mm |
| 验证 | 250 | 72.9 mm |

### 2.2 2025 版 7 档下的同样计算（供参考）

| 档位 | px/m | 0.3 m 上像素 | 1.7 m 上像素 | 1920px 覆盖宽度上限 | 所需焦距(1/2.8",100m) |
|---|---|---|---|---|---|
| Overview | 20 | 6.0 | 34.0 | 96.0 m | 5.8 mm |
| Outline | 40 | 12.0 | 68.0 | 48.0 m | 11.7 mm |
| Discern | 80 | 24.0 | 136.0 | 24.0 m | 23.3 mm |
| Perceive | 125 | 37.5 | 212.5 | 15.4 m | 36.5 mm |
| Characterize | 250 | 75.0 | 425.0 | 7.7 m | 72.9 mm |
| Validate | 500 | 150.0 | 850.0 | 3.8 m | 145.8 mm |
| Scrutinize | 1500 | 450.0 | 2550.0 | 1.3 m | 437.5 mm |

---

## 3. Axis IEC 62676-4:2025 版白皮书（7 档，供对照）

**我实际读取的原文 URL（HTTP 200，已下载解析成功）：**
<https://whitepapers.axis.com/download/wp_pixel_density_based_on_iec_62676_4_2025_t10228570_2512.pdf>

Table 3.1 原文数值：

| Operational requirement | px/face | **px/m** |
|---|---|---|
| Overview | 3 | 20 |
| Outline | 6 | 40 |
| Discern | 12 | 80 |
| Perceive | 20 | 125 |
| Characterize | 40 | 250 |
| Validate | 80 | 500 |
| Scrutinize | 240 | 1500 |

原文分类（§3.2）：
- **Low Pixel Density Object (LPDO)**：Overview, Outline, Discern → 20/40/80
- **High Pixel Density Object (HPDO)**：Perceive, Characterize, Validate, Scrutinize → 125/250/500/1500

原文定义（Table 2.1）：
- Overview：确认物体是否在移动
- Outline：勾勒物体轮廓并判断移动方向
- Discern：探测物体及其运动，分辨人/车/动物
- Perceive：感知物体及运动，但不分辨性别、看不到特征
- Characterize：通过人员类型、步态、行为辨认个体；也能刻画车型与类别
- Validate：核验已知人员、追溯行为、提取车牌号
- Scrutinize：高置信度确认个人身份、识别车辆型号年份、读取车牌

⚠️ 该文档又称 "It can also characterize vehicle type"；且 §1.1 明确列出 2025 版改动包括
"Representation of pixel density and monitor resolutions with numbers" —— 这里的 "monitor"
指的是**显示器**分辨率，与所谓 "Monitor 档位" 无关。

---

## 4. 关于「Monitor 档」与「12.5」的溯源（关键澄清）

任务书假设 Axis 有 Monitor 档 = 12.5 px/m。**这个说法在本白皮书中不成立。**
我在 Axis 另一份更老的文章中找到了这两个元素的真正出处：

**我实际读取的原文 URL（HTTP 200，已下载解析成功）：**
<https://www.axis.com/files/feature_articles/ar_perfect_pixel_count_55971_en_1402_lo.pdf>
（文章名 *Perfect Pixel Count — Meeting your operational requirements*，8 页）

### 4.1 "Monitor" 的真实出处：人体高度百分比，不是 px/m

该文章 Figure 2（模拟时代 → IP 的换算表）行标题为：
`Identify / Recognize / Observe / Detect / Monitor`，
列为 `PAL / 1080p / 720p / WSVGA / SVGA / VGA / 2CIF / CIF / QCIF`，
单元格数值是**人体高度占画面的百分比**：

- Identify = 100%（1080p 列 = 38）
- Recognize = 50%（1080p = 19）
- Observe = 25%（1080p = 10）
- Detect = 10%（1080p = 4）
- **Monitor = 5%（1080p = 2）**
- 出处脚注：`Figure 1. (UK Home Office Scientific Development Branch, 2009)`

👉 **Monitor 在这里是「人体高度占画面 5%」，是一个百分比档位，与 px/m 无关。**
   且该表出自英国 Home Office，不是 IEC 62676-4。

### 4.2 "12.5" 的真实出处：px/inch，不是 px/m

同文章 Figure 3 / Figure 4 表格（原文照录）：

| Operational requirement | Horizontal pixels/Face | Pixels/cm | **Pixels/inch** |
|---|---|---|---|
| Identification (challenging conditions) | 80 px/face | 5 px/cm | **12.5 px/in** |
| Identification (good conditions) | 40 px/face | 2.5 px/cm | 6.3 px/in |
| Recognition | 20 px/face | 1.25 px/cm | 3.2 px/in |
| Detection | 4 px/face | 0.25 px/cm | 0.6 px/in |

👉 12.5 = **px/inch**（每英寸 12.5 像素），对应 5 px/cm = **500 px/m**。
   把 "12.5" 读成 "12.5 px/m" 是单位误读。

### 4.3 结论

- **「Axis 的 Monitor 档 = 12.5 px/m」：未核实（在 Axis 官方文档中找不到依据）。**
- Axis 白皮书（2014 版）= 4 档；Axis 白皮书（2025 版）= 7 档。两版都没有 Monitor 档。

---

## 5. 次要来源（二手转引，仅作旁证）

**成功读取的二手来源：** <https://cctvplanner.io/hi/en-62676-4-calculator>（HTTP 200，网页正文）
其正文写：`25 px/m 处 Detection、62.5 px/m 处 Observation、125 px/m 处 Recognition、250 px/m 处 Identification`。
并列出 2025 版 OODPCVS 七档：`Overview 20 / Outline 40 / Discern 80 / Perceive 125 / Characterize 250 / Validate 500 / Scrutinise 1500 px/m`。

> ⚠️ 注意：该站写 **62.5**，而 **Axis 白皮书原文写 63**。两者不一致时以 Axis 原文（63）为准。

**未能读取的二手来源：**
- <https://www.use-ip.co.uk/axis-p1275-mk-ii.html> —— 返回 **HTTP 403**（Cloudflare 人机验证），未取到内容。

---

## 6. URL 抓取成功 / 失败清单（如实记录）

### ✅ 成功抓取并解析出正文（curl + PyMuPDF 文本提取）

| URL | 结果 |
|---|---|
| `https://whitepapers.axis.com/download/wp_pixel_density_and_dori_t10176489_zh_2501.pdf` | ✅ **200**，3,892,003 bytes，8 页（**中文主文档**，T10176489_ZH/ZH/M5.2/2604，4月2026） |
| `https://whitepapers.axis.com/download/wp_pixel_density_based_on_iec_62676_4_2014_t10176489_2510.pdf` | ✅ **200**，3,817,802 bytes，10 页（**英文主文档**） |
| `https://whitepapers.axis.com/download/wp_pixel_density_and_dori_t10176489_2501.pdf` | ✅ **200**，3,817,802 bytes，10 页；MD5 与上一份完全相同（`1e1f443d…94eb`），即同一文件 |
| `https://whitepapers.axis.com/download/wp_pixel_density_based_on_iec_62676_4_2025_t10228570_2512.pdf` | ✅ **200**，3,824,720 bytes，10 页（2025 版，7 档） |
| `https://www.axis.com/dam/public/31/fc/6c/pixel-density-pt-BR-405581.pdf` | ✅ **200**，2,866,679 bytes，12 页（葡萄牙语，*Densidade de pixels e DORI*，5月2023） |
| `https://www.axis.com/dam/public/01/0d/e3/pixel-density-ja-JP-405578.pdf` | ✅ **200**，3,424,756 bytes，12 页（日语，*ピクセル密度とDORI*，5月2023） |
| `https://www.axis.com/files/feature_articles/ar_perfect_pixel_count_55971_en_1402_lo.pdf` | ✅ **200**，203,154 bytes，8 页（老文章，Monitor/12.5 的真正出处） |
| `https://cctvplanner.io/hi/en-62676-4-calculator` | ✅ **200**（经 `web_fetch`，二手网页） |

### ❌ 抓取失败

| URL / 方式 | 失败原因 |
|---|---|
| `web_fetch` → `https://whitepapers.axis.com/en/pixel-density-based-on-iec-62676-4-2014` | `TypeError: fetch failed` |
| `web_fetch` → `https://whitepapers.axis.com/zh-hans/pixel-density-based-on-iec-62676-4-2014` | `TypeError: fetch failed` |
| `web_fetch` → `https://whitepapers.axis.com/zh-hans/pixel-density-and-dori` | `TypeError: fetch failed` |
| `web_fetch` → `https://www.axis.com/support/technical-notes/pixel-density` | `TypeError: fetch failed` |
| `web_fetch` → `https://www.axis.com/dam/public/01/0d/e3/pixel-density-ja-JP-405578.pdf` | `unsupported content type "application/pdf"` |
| `web_fetch` → `https://r.jina.ai/https://whitepapers.axis.com/zh-hans/...` | `TypeError: fetch failed`（代理同样不通） |
| `web_fetch` → `https://www.use-ip.co.uk/axis-p1275-mk-ii.html` | **HTTP 403**（Cloudflare 拦截，仅得到 "Just a moment..."） |
| `curl` → `https://whitepapers.axis.com/zh-cn/pixel-density-based-on-iec-62676-4-2025`（HTML 版） | 30 s 超时，0 字节 |
| `curl` → `https://whitepapers.axis.com/en/pixel-density-based-on-iec-62676-4-2014`（HTML 版） | **异常**：HTTP 200 / 119,402 bytes，但返回的是一个**无关的中文海康产品页**（数字音视工程网），内容不可信，已弃用 |
| `curl` 首次尝试中文 PDF（60 s） | 超时截断，PyMuPDF 打开为 0 页 |

> 说明：`whitepapers.axis.com` 解析到 Fastly（151.101.89.117），网络时延极不稳定。
> 最终通过**加长超时（240–900 s）+ 多次重试**的 curl 直连方式成功拿到全部 Axis 原文 PDF。
> **`web_fetch` 工具对该域名全线不可用，PDF 直链一律被拒（application/pdf）。**

---

## 7. 引用原文时的注意事项

1. **63 而非 62.5**：Axis 白皮书原文是 `63 px/m`（IEC 标准表为 62.5）。中文标书若写 62.5，
   严格说引的是 IEC 标准而非 Axis 白皮书；写 63 才是 Axis 原文。
2. **中文术语错位**：中文版 `Recognition → 识别`、`Identification → 验证`。
   行业习惯常把 Identify 叫「识别」，直接套用会串档，务必注明英文原词。
3. **白皮书内部不一致**：Table 3.1 说 Identification = 40 px/face，
   但 Figure 4.2 图注说 "requiring at least 80 pixels across the face"。建议以 Table 3.1 为准。
4. **白皮书适用范围**：原文明确「valid in situations where visual video images are interpreted by
   human operators」——对**视频分析/算法**场景与**热成像**场景，定义不同，不能直接套用。
5. **外部显示器**：原文提示 DORI 能力高度依赖显示器分辨率。
6. **单位**：本文所有 px/ft 换算，Axis 明确说产品数据表用精确值（19/38/76），
   实际工程中惯用取整值（20/40/80）。
