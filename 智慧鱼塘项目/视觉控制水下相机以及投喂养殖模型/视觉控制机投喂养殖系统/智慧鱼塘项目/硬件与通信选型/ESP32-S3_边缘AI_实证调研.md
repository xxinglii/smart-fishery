# ESP32-S3 边缘 AI 真实能力边界 & 鱼类检测实证调研

> 调研方法：实际 `curl` 抓取 GitHub raw 文件 / GitHub REST API / arXiv API / Crossref API / Europe PMC API / 官方文档页面。
> 所有帧率、延迟、模型大小、精度数字均来自**本次实际打开过的页面**，并附可点击 URL。
> 凡未能验证的，明确标注「未找到可靠实证」或「未验证」。

---

## 0. 一句话结论

**ESP32-S3 能跑目标检测，但速度是「秒级/帧」而不是「帧/秒」。** 官方 esp-dl 实测：YOLO11n @320×320 单帧 **6196 ms（≈0.16 FPS）**，@640×640 单帧 **26125 ms（≈0.038 FPS）**。
**真正的甜点是「小输入 + 单类/少类 + 级联/轻量模型」**：人脸检测（120×160 两阶段）**~37–44 ms（≈23–27 FPS）**，ESPDet-Pico 单类检测 @224×224 **126 ms（≈7.9 FPS）**。
**鱼类检测方向：未找到任何可靠的「ESP32 端侧鱼类识别」实证。**

---

# 任务 1：ESP32-S3 跑目标检测的实测数据

## 1.1 乐鑫官方 esp-dl — COCO 检测模型 benchmark（最权威）

来源：https://github.com/espressif/esp-dl → https://raw.githubusercontent.com/espressif/esp-dl/master/models/coco_detect/README.md
仓库 star：**1141**（GitHub API 实测）

### 事实表：esp-dl COCO 检测延迟（原文数字，单位 ms）

| 模型名 | 芯片 | 输入(h×w×c) | Flash | PSRAM | 预处理(ms) | **模型(ms)** | 后处理(ms) | 端到端合计(ms) | **推算 FPS** | mAP50-95 (COCO val2017) |
|---|---|---|---|---|---|---|---|---|---|---|
| yolo11n_s8_v1_s3 | ESP32-S3 | 640×640×3 | 8 MB | 8 MB | 51.5 | **26014.2** | 58.9 | 26124.6 | **0.038** | 0.370 |
| yolo11n_s8_v1_p4 | ESP32-P4 | 640×640×3 | 16 MB | 32 MB | 16.0 | **2535.3** | 14.3 | 2565.6 | **0.39** | 0.373 |
| yolo11n_320_s8_v1_s3 | ESP32-S3 | 320×320×3 | 8 MB | 8 MB | 15.2 | **6161.8** | 19.3 | 6196.3 | **0.16** | 0.276 |
| yolo11n_320_s8_v1_p4 | ESP32-P4 | 320×320×3 | 16 MB | 32 MB | 5.2 | **550.1** | 5.3 | 560.6 | **1.78** | 0.278 |

来源 URL：https://raw.githubusercontent.com/espressif/esp-dl/master/models/coco_detect/README.md

> **关键约束（原文 note，事实）**：
> "When using YOLO11n, do not set model location to sdcard if your PSRAM size is lower than 16MB. Because when loading YOLO11n, memory manager takes 6MB, and the model parameters is nearly 3MB."
> → YOLO11n 仅内存管理器就要 6 MB，参数近 3 MB；PSRAM < 16 MB 时模型必须留在 FLASH。
> **这条直接否定了「ESP32-S3 + 8MB PSRAM 流畅跑 YOLO11n」的说法。**

## 1.2 乐鑫官方 esp-dl — YOLO26 模型 benchmark

来源：https://raw.githubusercontent.com/espressif/esp-dl/master/models/yolo26/README.md

| 模型名 | 芯片 | 输入(h×w×c) | Flash | PSRAM | 预处理(ms) | **模型(ms)** | 后处理(ms) | 端到端合计(ms) | **推算 FPS** | mAP50-95 |
|---|---|---|---|---|---|---|---|---|---|---|
| yolo26n_512_s8_s3 | ESP32-S3 | 512×512×3 | 16 MB | 16 MB | 34.0 | **7822.0** | 23.0 | 7879.0 | **0.13** | 0.363 |
| yolo26n_640_s8_s3 | ESP32-S3 | 640×640×3 | 16 MB | 16 MB | 51.0 | **13107.0** | 36.0 | 13194.0 | **0.076** | 0.384 |
| yolo26n_512_s8_p4 | ESP32-P4 | 512×512×3 | 16 MB | 32 MB | 12.0 | **2067.0** | 13.0 | 2092.0 | **0.48** | 0.365 |
| yolo26n_640_s8_p4 | ESP32-P4 | 640×640×3 | 16 MB | 32 MB | 17.0 | **3474.0** | 21.0 | 3512.0 | **0.28** | 0.387 |

> 注意：ESP32-S3 版本官方标 **PSRAM 16 MB**（8 MB 版跑不动）。YOLO26 是 NMS-Free（One2One head + top-K），已在算子层面优化，仍然只有 0.076–0.13 FPS。

## 1.3 espressif/yolo26 组件（Component Registry 实证）

来源：https://components.espressif.com/components/espressif/yolo26
（API 实证：https://components.espressif.com/api/components/espressif/yolo26）

| 字段 | 值（API 返回事实） |
|---|---|
| namespace / name | espressif / yolo26 |
| 版本 | 0.1.0（唯一版本） |
| created_at | 2026-04-15T02:15:02Z |
| 描述 | "Universal YOLO26 Processor for **ESP32-P4** (NMS-Free)" |
| 依赖 | esp-dl `~3.3.0` |
| downloads_total | **103** |
| license | MIT |
| repository | git://github.com/espressif/esp-dl.git (models/yolo26) |

> 事实：组件描述写的是 **for ESP32-P4**；下载量 103，说明实际用户极少。

## 1.4 乐鑫官方 esp-who — 人脸检测实测（任务要求的重点）

来源（含官方延迟表）：https://developer.espressif.com/workshops/edge-ai-with-esp32-s3/assignment-2/
仓库 star：**esp-who 2144**（GitHub API 实测）

### 事实表：esp-who / esp-dl 人脸检测

| 模型 | 类型 | 输入分辨率 | ESP32-S3 延迟 | mAP50-95 | ESP32-P4 延迟 | 备注 |
|---|---|---|---|---|---|---|
| MSR_S8_V1 + MNP_S8_V1（默认，两阶段） | 两阶段 | 120×160 → 48×48/候选 | **~37 ms**（MSR ~33 ms + MNP ~6 ms/候选）；单脸整帧 ~37–40 ms → **≈25–27 FPS** | 0.367 | — | 官方 workshop 原文 |
| ESPDET_PICO_224_224_FACE | 单阶段 | 224×224 | **~132 ms** → ≈7.6 FPS | 0.504 | — | 官方 workshop 原文 |
| ESPDET_PICO_416_416_FACE | 单阶段 | 416×416 | **~437 ms** → ≈2.3 FPS | 0.598 | — | 官方 workshop 原文 |

原文引用（事实）：
> "MSR takes ~33 ms for the whole frame on ESP32-S3, and MNP adds only ~6 ms per surviving candidate. In practice, when one face is in frame, the total detection time is around 37–40 ms per frame."
> "All three models use **8-bit quantization** and run **entirely on the ESP32-S3's CPU** using the ESP-DL inference engine."

### esp-dl 原始 benchmark（更细，含 P4 对比）

来源：https://raw.githubusercontent.com/espressif/esp-dl/master/models/human_face_detect/README.md

| 模型 | 芯片 | 输入 | 预处理(ms) | 模型(ms) | 后处理(ms) | 合计(ms) | 推算 FPS | mAP50-95 |
|---|---|---|---|---|---|---|---|---|
| msr_s8_v1_s3 | ESP32-S3 | 120×160×3 | 3.8 | 33.1 | 0.3 | 37.2 | 26.9 | — |
| msr_s8_v1_p4 | ESP32-P4 | 120×160×3 | 1.3 | 13.1 | 0.1 | 14.5 | 69.0 | — |
| mnp_s8_v1_s3 | ESP32-S3 | 48×48×3 | 0.6 | 5.8 | 0.1 | 6.5 | 153.8 | 0.367(msr+mnp) |
| mnp_s8_v1_p4 | ESP32-P4 | 48×48×3 | 0.3 | 2.4 | 0.0 | 2.7 | 370 | 0.366(msr+mnp) |
| espdet_pico_224_224_face_s8_s3 | ESP32-S3 | 224×224×3 | 7.2 | 131.6 | 0.8 | 139.6 | 7.2 | 0.504 |
| espdet_pico_416_416_face_s8_s3 | ESP32-S3 | 416×416×3 | 21.8 | 437.0 | 1.3 | 460.1 | 2.2 | 0.598 |
| espdet_pico_224_224_face_s8_p4 | ESP32-P4 | 224×224×3 | 2.4 | 49.6 | 0.4 | 52.4 | 19.1 | 0.504 |
| espdet_pico_416_416_face_s8_p4 | ESP32-P4 | 416×416×3 | 6.6 | 185.9 | 0.6 | 193.1 | 5.2 | 0.597 |

## 1.5 esp-dl 行人检测 & 图像分类 benchmark

来源：https://raw.githubusercontent.com/espressif/esp-dl/master/models/pedestrian_detect/README.md
来源：https://raw.githubusercontent.com/espressif/esp-dl/master/models/imagenet_cls/README.md

### 行人检测（人员入侵检测的直接依据）

| 模型 | 芯片 | 输入 | 预处理(ms) | 模型(ms) | 后处理(ms) | 合计(ms) | **推算 FPS** |
|---|---|---|---|---|---|---|---|
| pico_s8_v1_s3 | ESP32-S3 | 224×224×3 | 9.2 | **118.3** | 2.4 | 129.9 | **7.7** |
| pico_s8_v1_p4 | ESP32-P4 | 224×224×3 | 3.5 | **55.6** | 1.4 | 60.5 | **16.5** |

### 图像分类（MobileNetV2 — 「简单二分类」的性能天花板参照）

| 模型 | 芯片 | 运行模式 | 输入 | 预处理(ms) | 模型(ms) | 后处理(ms) | 合计(ms) | **推算 FPS** | Prec@1 (ImageNet val) |
|---|---|---|---|---|---|---|---|---|---|
| mobilenetv2_s8_v1_s3 | ESP32-S3 | 单核 | 224×224×3 | 8.5 | **1309.5** | 1.1 | 1319.1 | **0.76** | 70.543 |
| mobilenetv2_s8_v1_s3 | ESP32-S3 | 多核 | 224×224×3 | 8.5 | **867.0** | 1.1 | 876.6 | **1.14** | 70.543 |
| mobilenetv2_s8_v1_p4 | ESP32-P4 | 单核 | 224×224×3 | 2.8 | 326.6 | 0.6 | 330.0 | 3.03 | 70.441 |
| mobilenetv2_s8_v1_p4 | ESP32-P4 | 多核 | 224×224×3 | 2.7 | 223.0 | 0.4 | 226.1 | 4.42 | 70.441 |

> **这是最重要的边界数字之一**：连 MobileNetV2 这种 224×224 的轻量分类网，ESP32-S3 双核也要 **867 ms/帧（≈1.1 FPS）**。
> 双核比单核快约 1.51×（1309.5 → 867.0 ms）。

## 1.6 esp-detection（乐鑫官方，基于 YOLOv11）实测数据

来源：https://github.com/espressif/esp-detection
仓库 star：**160**，fork：32，created 2025-04-29，pushed 2026-03-05（GitHub API 实测）

### 事实表：ESPDet-Pico 猫检测（单类检测的黄金参照）

| 模型 | 输入 | mAP@0.5:0.95 | mAP@0.5 | 参数量(M) | FLOPs(G) | **ESP32-P4 延迟(ms)** | **ESP32-S3 延迟(ms)** | S3 推算 FPS |
|---|---|---|---|---|---|---|---|---|
| espdet_pico_224_224_cat | 224×224 | 69.9 | 88.4 | 0.36 | 0.17 | **51.4** | **126.2** | **7.9** |
| espdet_pico_416_416_cat | 416×416 | 76.6 | 93.4 | 0.36 | 0.60 | **201.7** | **449.5** | **2.2** |
| espdet_pico_160_288_cat | 160×288 | 71.2 | 90.6 | 0.36 | 0.16 | **45.9** | **115.5** | **8.7** |

README 原文（事实）：
> "Faster latency: Considering pre-processing and post-processing, espdet_pico achieves **>18 FPS on ESP32-P4** and **>7 FPS on ESP32-S3** when the input size is 224*224."
> "The single-class model ESPDet-Pico(0.36M parameters, 224 input size) achieves comparable mAP(0.5:0.95) to 80-class model YOLOv11n(**2.6M parameters, 640 input size**) on cat detection."

> **交叉验证一致**：126.2 ms → 1000/126.2 = 7.9 FPS ≥ 7 FPS ✓；51.4 ms → 19.5 FPS ≥ 18 FPS ✓

### ⚠️ 关于 JorgeSan88/esp-detection 的重要更正

任务描述中提到的 https://github.com/JorgeSan88/esp-detection **不是原创项目，而是 espressif/esp-detection 的 fork**：

| 字段 | API 实测值 |
|---|---|
| fork | **true** |
| stargazers_count | **0** |
| parent | **espressif/esp-detection** |

所以其 README 中的所有数据都应归因于 **espressif/esp-detection（160 star）**，而不是一个 0-star 的独立项目。

## 1.7 官方例程 / esp32-camera 相关实测

| 项目 | 芯片 | 输入 | 模型 | 实测数据 | 来源 |
|---|---|---|---|---|---|
| esp-dl human_face_detect 例程 | ESP32-S3 / P4 | 见 1.4 | 人脸检测 | 串口输出 score 0.936285 等（无延迟数字） | https://components.espressif.com/components/espressif/esp-dl/versions/3.3.8/examples/human_face_detect |
| esp-who object_detect 例程 | ESP32-S3 / P4 | — | human_face / pedestrian / cat / dog detect | README **未给出 FPS** | https://raw.githubusercontent.com/espressif/esp-who/master/examples/object_detect/README.md |
| esp-who 仓库 | ESP32-S3 / P4 | — | 人脸检测/识别/行人/QR | README **未给出实测帧率** | https://github.com/espressif/esp-who |

> **未找到**：esp-who 仓库自身 README 中**没有**人脸检测的实测帧率数字（只有"camera and the deep learning model now runs asynchronously, which achieves higher fps"这样的定性描述，无数字）。实测帧率数字来自官方 workshop 页面（1.4 节）。

## 1.8 ESP32-S3 上「MobileNet 类」分类的第三方实测

来源：https://www.mdpi.com/1424-8220/25/6/1656
（MDPI 直连 403，经 Europe PMC 全文 API 获取：https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11945263/fullTextXML）
论文：Li X. et al., "Design and Implementation of ESP32-Based Edge Computing for Object Detection", *Sensors* 2025, 25(6), 1656. DOI: https://doi.org/10.3390/s25061656

| 项目 | 事实（原文） |
|---|---|
| 芯片 | **ESP32-CAM（原版 ESP32，非 S3）** |
| 模型 | MobileNet **v1**，TensorFlow Lite |
| 输入 | 96×96 RGB888（相机 96×96 RGB565 / 320×240 JPEG / 640×480 JPEG） |
| 任务 | **二分类：person / non-person** |
| 端侧验证集结果 | 20 张样本，混淆矩阵：person 9/1、non-person 0/10（即 19/20 正确） |
| 端侧错误归因（原文） | "Most misrecognitions happen at the edge due to the ESP32-CAM's **limited computational power** and the use of a lightweight MobileNet" |
| 完整环路时间 @320×240（Option 2 = 端侧识别后只发消息） | 本地 Mosquitto **459 ± 80 ms**；MQTTGO **640 ± 158 ms**；Eclipse 国际 **1189 ± 155 ms** |
| 640×480 JPEG 发国际 broker 的额外开销 | **+5815 ms（6.55 倍）** |

## 1.9 Edge Impulse / FOMO 路线实测（论坛实证）

来源：https://forum.edgeimpulse.com/t/use-psram-for-impulse-deployment-on-esp32-s3/12849

| 项目 | 事实（用户贴出的串口输出） |
|---|---|
| 芯片 | ESP32-S3（8 MB PSRAM，16 MB flash） |
| 模型 | 二分类、灰度输入、量化模型 + EON compiler |
| **实测推理时间** | **`Timing: DSP 5 ms, inference 675 ms, anomaly 0 ms`** |
| 问题 | tensor arena 不足需手动调大；官方人员确认「ESP32-S3 使用优化过的 kernel，scratch buffer 导致 arena 需求与常规 benchmark 不同」 |

> 备注：该用户中途把输入从 96×96 降到 48×48 试图解决 arena 报错，因此 **675 ms 对应的确切输入分辨率未能从页面确证**，标注为「输入分辨率未验证」。

## 1.10 ESP32-P4 对比参考（新一代）

| 维度 | 事实 | 来源 |
|---|---|---|
| 相对 ESP32-S3 的加速比（同一模型） | 人脸检测 MSR：33.1 → 13.1 ms（**2.5×**） | esp-dl human_face_detect README |
| | 人脸检测 ESPDet-Pico 416：437.0 → 185.9 ms（**2.35×**） | 同上 |
| | 行人检测 224：118.3 → 55.6 ms（**2.13×**） | esp-dl pedestrian_detect README |
| | MobileNetV2 单核：1309.5 → 326.6 ms（**4.0×**） | esp-dl imagenet_cls README |
| | YOLO11n @320：6161.8 → 550.1 ms（**11.2×**） | esp-dl coco_detect README |
| | YOLO11n @640：26014.2 → 2535.3 ms（**10.3×**） | 同上 |
| | YOLO26n @640：13107.0 → 3474.0 ms（**3.8×**） | esp-dl yolo26 README |
| | ESPDet-Pico 猫检测 @224：126.2 → 51.4 ms（**2.46×**） | esp-detection README |
| 被官方明确支持的推理框架 | esp-dl 全部模型同时支持 ESP32-S3 与 ESP32-P4 | 各 README 支持表 |
| 相关学术论文 | "The systematic design and implementation of a vertical fish farm based on ESP32-P4", 2026 IEEE ICMA, DOI: https://doi.org/10.1109/icma69663.2026.11647118 | Crossref API 验证 |

> **工程含义（推断）**：ESP32-P4 把「原本不可用」变成「勉强可用」（YOLO11n @320 从 0.16 FPS → 1.78 FPS），但仍远达不到实时视频检测。P4 的价值主要在 CNN 类小模型（4× 加速）。

## 1.11 ESP32-S3 芯片规格（用于边界判断）

| 规格 | 值 | 来源性质 |
|---|---|---|
| 处理器 | 双核 Xtensa LX7 @ 240 MHz | 第三方硬件指南（ForestHub）https://www.foresthub.ai/resources/esp32-s3-image-classification-edge-impulse |
| SRAM | 512 KB | 同上 |
| PSRAM | 最高 8 MB | 同上 |
| Flash | 最高 16 MB（外部） | 同上 |
| 关键特性 | SIMD 向量指令、USB OTG、LCD/Camera(DVP) 接口 | 同上 |

> ⚠️ 来源性质说明：该页面是**第三方厂商内容页**，非乐鑫官方。乐鑫 ESP32-S3 产品页在本次调研中**返回 403 或正文为 JS 渲染、未能取到规格文本**，故芯片规格以此第三方页为证，标注为「第三方来源」。

## 1.12 相关学术论文（DOI 经 Crossref / 大学库页面验证）

| 论文 | 出处 | DOI / 链接 | 本调研取到的内容 |
|---|---|---|---|
| Optimizing Edge-AI on the ESP32-S3 Using SIMD | IEEE IPCCC 2025 | https://doi.org/10.1109/IPCCC66453.2025.11304640 | **仅有摘要首句**："explores whether the ESP32-S3, a low-cost microcontroller with SIMD acceleration, can run a lightweight AI model efficiently." **未取到任何实测数字**（IEEE 付费墙）。亦见 https://scholars.uky.edu/en/publications/optimizing-edge-ai-on-the-esp32-s3-using-simd/ |
| Design and Implementation of ESP32-Based Edge Computing for Object Detection | Sensors 2025, 25(6):1656 | https://doi.org/10.3390/s25061656 | 见 1.8 节完整数据 |
| A Method of Deep Learning Model Optimization for Image Classification on Edge Device | Sensors 2022, 22(19):7344 | https://doi.org/10.3390/s22197344 | 摘要已取（轻卷积/量化/剪枝/蒸馏策略），**未取到 ESP32 专项实测数字** |
| Real-time rapid visual fish disease detection system based on tiny machine learning | Aquaculture International 2025, 33(6):584 | https://doi.org/10.1007/s10499-025-02256-6 | YOLO11n + **RISC-V MCU**，mAP50-95 = **0.736**（详见任务 2） |

---

# 任务 2：ESP32 上的鱼类检测 / 识别真实案例

## 2.1 GitHub 全量搜索结果（API 实测，事实）

| 搜索 query | total_count | 最高 star 的项目 |
|---|---|---|
| `fish+detection+esp32` | **5** | 0 |
| `fish+esp32cam` | **3** | 3（IBishopI/fishfeeder_esp32cam_telegram — 只是喂食器，无AI） |
| `fish+classification+esp32` | **2** | 1 |
| `fish+detection+tinyml` | **0** | — |
| `fish+species+identification+edge` | **2** | 0 |
| `fish+detector+microcontroller` | **0** | — |
| `fish+recognition+embedded` | **1** | 0（且是猫狗分类，不相关） |
| `aquarium+ai+esp32` | 7 | 2 |
| `underwater+esp32+ai` | 4 | 1 |
| `aquaculture+esp32` | 45 | 29（纯水质传感器，无视觉AI） |

> **事实**：在 GitHub 上，`fish detection + ESP32` 这个组合总共只有 **5 个仓库，且全部 0 star**。`fish detection + tinyml` 为 **0 个仓库**。

## 2.2 逐个案例核实（含 star 数与「端侧 vs 云端」判定）

| 项目 | 芯片 | 方式 | Star 数 | 实测精度/FPS | 最后更新 | 来源链接 | 备注（实证细节） |
|---|---|---|---|---|---|---|---|
| EduardoLawson1/Fish-Detection-with-Esp32Cam | ESP32-CAM（AI Thinker，原版 ESP32） | **矛盾/存疑**（见备注） | **0** | **无任何精度数字** | pushed 2023-10-10 | https://github.com/EduardoLawson1/Fish-Detection-with-Esp32Cam | 模型：Edge Impulse **FOMO MobileNetV2 0.1**。**代码**（`esp32_camera-fish-detection.ino`）确实 `#include <FISH_DETECTION_inferencing.h>` + `edge-impulse-sdk`，属端侧推理框架；**但 README 明确写**："send them to the Edge Impulse platform for fish detection"、"The ESP32-CAM will continuously capture and transmit images to Edge Impulse for fish detection"。**README 与代码自相矛盾**。仓库仅 3 个文件：README / .ino / ei-fish-detection-2-arduino-1.0.2.zip。**无精度、无数据集、无 FPS** |
| IT21179280/SMART-FISH-TANK-MONITORING-SYSTEM | ESP32 + Arduino + ESP32-CAM | **云端推理**（推断） | **0** | **无任何精度数字** | pushed 2026-01-20 | https://github.com/IT21179280/SMART-FISH-TANK-MONITORING-SYSTEM | 名为 "Final Year Research Project"。README 称两个自训练 YOLOv8 模型（鱼类品种识别 + 怀孕鱼检测）。**仓库只有 README + `esp32-yolo-dashboard.zip`，无源码**。README 只说 "ESP32-CAM captures live video"，**未说明 YOLOv8 在哪运行**；且**全文无任何 mAP/准确率/帧率**。结合 ESP32-S3 实测（1.1 节：YOLO11n@640 = 26 s/帧），可判断不可能端侧推理 |
| Alwyn2006/SMART-FISH-AQUARIUM | ESP32-CAM（声明） | **声称为端侧，但仓库无实现** | **2** | **无任何精度数字** | pushed 2026-01-05 | https://github.com/Alwyn2006/SMART-FISH-AQUARIUM | README 大篇幅声称 "CNN–LSTM model"、"real-time decisions locally on the ESP32-CAM"、"Edge AI inference with low latency"。**但仓库文件树实际只有**：`README.md, index.html, package.json, package-lock.json, vite.config.js, src/App.jsx, src/App.css, src/main.jsx, public/fishy-bg.svg` —— **一个 React/Vite 网页，没有任何 ESP32 固件、没有任何模型文件**。README 的技术宣称**完全未被仓库内容支持** |
| guaima007/fisheries-monitor | ESP32-S3 | **云端/PC 推理** | **2** | 无 | pushed 2026-07-09 | https://github.com/guaima007/fisheries-monitor | 中文项目「Fisheries 智慧循环水养殖监测终端」。架构图显示：视觉走 `PC voice_gateway.py`、`vision_llm_adapter.py`、`vision_stream_server.py`；`code24_yolov8/` 含 `UI.py`、`SE_YOLOV8_TRAINING_GUIDE.txt` → **YOLOv8 在 PC 端**。ESP32-S3 只做传感器采集、继电器、LVGL、语音、MQTT |
| davidRT2/FishSorter-IoT-Based-Fish-Classification-Using-CNN | ESP32 + ESP-CAM | **云端推理**（明确） | **1** | 无 | pushed 2024-06-02 | https://github.com/davidRT2/FishSorter-IoT-Based-Fish-Classification-Using-CNN | README 原文："MQTT protocol for communication between ESP32 and ESP-CAM, and a **Flask API to load and serve the pre-trained CNN model in .h5 format**" → **模型跑在 Flask 服务器上**，明确非端侧 |
| deepintersection/smart-aquarium | ESP32（Rust） | **云端推理**（明确） | **1** | 无 | pushed 2026-06-05 | https://github.com/deepintersection/smart-aquarium | README："Connects to a **local n8n AI server** for recommendations and alerts"。且 architecture 里 application/infrastructure/firmware 三层全标 **"(coming soon)"** |
| ilan2002/Aquaculture_monitoring_using_Machinelearning_ESP32 | ESP32（声明） | 未验证 | **6** | 无 | pushed 2025-04-04 | https://github.com/ilan2002/Aquaculture_monitoring_using_Machinelearning_ESP32 | 仓库描述仅一句 "Aquaculture monitoring system for aqua farmers..."，**README 无技术细节、无精度、无架构说明** |
| JackGamerCYT/Smart-Aquarium-ESP32-S3-IoT-AI | ESP32-S3 | 未验证 | 0 | 无 | pushed 2026-09-15 | https://github.com/JackGamerCYT/Smart-Aquarium-ESP32-S3-IoT-AI | 仓库无描述、无法验证内容 |
| colliderkkz/An-Intelligent-Aquarium-System-Based-o | ESP32-S3 | 声明端侧 LSTM | 0（搜索结果） | 无 | — | （搜索索引中出现）| 搜索描述称「基于ESP32-S3的嵌入式系统开发与LSTM水质预测模型的构建与部署…边缘AI部署…双核异构架构」。**但 GitHub API 对该仓库返回全 None、README 返回 404 → 仓库可能已删除/改名，无法验证** |
| naitik-joshi/espFishTank | ESP32-CAM | 采集（鱼缸监控） | 0 | 无 | pushed 2026-04-11 | GitHub API 搜索结果 | 描述为 "fish tank monitor for live…"，无 AI 推理证据 |
| IBishopI/fishfeeder_esp32cam_telegram | ESP32-CAM | 无视觉AI | **3** | 无 | pushed 2022-01-28 | GitHub API 搜索结果 | "Fish feeder based on ESP32CAM dev kit and controlled through telegram bot" — **喂食器，非检测** |

## 2.3 学术侧：真正做鱼类检测的系统用什么硬件？

| 论文 | 硬件 | 精度 | DOI/链接 |
|---|---|---|---|
| Real-time rapid visual fish disease detection system based on tiny machine learning | **RISC-V 微控制器（非 ESP32！）** | mAP50-95 = **0.736**（YOLO11n） | https://doi.org/10.1007/s10499-025-02256-6 （Aquaculture International 2025, 33(6):584；摘要经 Europe PMC 验证） |
| Real-Time Underwater Fish Detection and Recognition Based on CBAM-YOLO Network with Lightweight Design | 未取到硬件（MDPI 直连 403） | 未取到 | https://doi.org/10.3390/jmse12081302 （JMSE 2024, 12(8):1302，Crossref 验证） |
| Fish Species Detection and Tracking Based on Fusion Intensity Entity Transformation using Optical Flow Algorithm | 未取到 | 未取到 | https://doi.org/10.1109/icecaa55415.2022.9936540 |
| Fish species classification in unconstrained underwater environments based on deep learning | 未取到（服务器/GPU 类） | 未取到 | https://doi.org/10.1002/lom3.10113 |

> **注意**：唯一一篇「TinyML + 鱼类疾病检测」的论文，用的是 **RISC-V MCU 而不是 ESP32**，且 mAP50-95 只有 0.736（这是**疾病检测**，不是**种类识别**，且是论文级调优结果）。

## 2.4 任务 2 结论（事实层面）

**未找到可靠实证**：截至本次调研，**没有任何**可验证的开源项目或论文，实证了「ESP32 / ESP32-S3 在端侧完成鱼类检测或鱼类种类识别，并给出实测精度与帧率」。

具体「未找到」清单：
1. **未找到**任何 ESP32 端侧鱼类检测项目的实测 mAP / 准确率 / FPS 数字。
2. **未找到**任何 star > 5 的 ESP32 鱼类识别仓库（最高相关项目 star = 2，且其 README 宣称未被仓库内容支持）。
3. **未找到** Edge Impulse 官方项目库中可公开验证的 ESP32 鱼类检测项目页面（edgeimpulse.com 项目页为 JS 渲染，本次**未能取到内容**；Hackster.io 返回 **Cloudflare 403 拦截**）。
4. **未找到** arXiv 上 "fish detection" AND "ESP32" 的论文（arXiv API 查询无返回结果 / 超时）。
5. **唯一接近的学术工作**用的是 **RISC-V MCU**（不是 ESP32），且做的是鱼病检测而非种类识别。

---

# 任务 3：ESP32 做鱼类投喂 / 水质 AI 的实际案例

## 3.1 学术论文：ESP32 + 水质预测 / 溶解氧（DOI 已验证）

| 论文 | 年份/期刊 | DOI | 芯片角色 | 模型 | 实测指标（原文数字） | 备注 |
|---|---|---|---|---|---|---|
| **Machine Learning on Low-Cost Edge Devices for Real-Time Water Quality Prediction in Tilapia Aquaculture** | 2025, *Sensors* 25(19):6159 | https://doi.org/10.3390/s25196159 | **端侧推理（真·ESP32 上跑）** | MLR / DTR / RFR（**经典机器学习，非神经网络**） | RFR **R² > 0.80**；MLR **R² ≈ 0.65–0.72**；最终选 MLR 部署 | **本次调研最相关的论文**。ESP32 = Xtensa LX6 双核 @240 MHz、4 MB flash、512 KB RAM。原文："none of the reviewed works show predictive ML deployment directly on ultra-low-cost microcontrollers such as ESP32 for aquaculture"。每 1 小时采样一次 |
| Preliminary Field Evaluation of a Low-Cost IoT Workflow for Dissolved Oxygen Monitoring and Short-Horizon Forecasting in Nile Tilapia Aquaculture | 2026, *Sensors* 26(13):4242 | https://doi.org/10.3390/s26134242 | **ESP32 仅做采集，云端推理** | 云端短时预测 | 30 min 预测 **MAE 0.783 mg/L，方向准确率 60.23%**；6 h 预测 **MAE 1.109 mg/L，53.82%** | 论文自述："only **modest improvement over a persistence baseline**"、"**do not establish robust operational forecasting validity**"。**诚实但负面的结果** |
| An Intelligent IoT-Based Predictive Control System for Water Quality and Energy Management in Koi Aquaculture | 2026, *Sensors* 26(10):3238 | https://doi.org/10.3390/s26103238 | 云端（LSTM + 数字孪生 + CPS） | LSTM | DO **R² = 0.97**，氨氮 **R² = 0.94**；总能耗降 **26.86%**（212±6.06 → 154.71±4.52 Wh/天，p<0.001） | 45 天部署。**未在摘要中说明 LSTM 跑在 ESP32 上**，架构为 IoT 传感 + DT + CPS |
| AI-Driven Monitoring for Fish Welfare in Aquaponics: A Predictive Approach | 2025, *Sensors* 25(19):6107 | https://doi.org/10.3390/s25196107 | **未明确**（计算层级不明） | LDA / SVM / NN / RF | RF **99%**、NN 98%、SVM 97%、LDA 82%（1823 样本，8 个月，红色罗非鱼） | 摘要**未说明模型部署在何处**；指标为分类准确率，非端侧实测 |
| Cost-Effective Precision Aquaculture through Embedded Intelligence: Inferring Oxygen Levels and Automated Viability Classification Utilizing Low-Cost Sensors and Edge-Deployed Machine Learning | 2026, IEEE ICSFT | https://doi.org/10.1109/icsft66733.2026.11507635 | 声称 Edge-Deployed | 未取到 | **未取到**（IEEE 付费墙，仅标题） | 标题含 "Edge-Deployed Machine Learning"，但**全文与数字未能获取** |
| The systematic design and implementation of a vertical fish farm based on ESP32-P4 | 2026, IEEE ICMA | https://doi.org/10.1109/icma69663.2026.11647118 | 未取到 | 未取到 | **未取到**（IEEE 付费墙，仅标题） | 标题含 ESP32-P4 与鱼场 |
| IoT-Based Water Quality Prediction System Using Machine Learning and ESP32 | 2026 | https://doi.org/10.56726/irjmets99723 | 未验证 | 未验证 | 未取到 | Crossref 元数据已验证，正文未获取 |
| Development of Water Quality Monitoring Systems in Super Intensive Aquaculture System using ESP32 and Blynk | 2019 | https://doi.org/10.5220/0009894200900095 | 仅采集（Blynk 云） | 无 | 无 | 无 ML |

### 关于溶解氧预测的补充事实（Crossref 检索结果，仅元数据）

以下论文是水产溶解氧预测的主流学术工作，但**均未使用 ESP32**，属于服务器/云端 ML：

| 论文 | 年份/期刊 | DOI |
|---|---|---|
| A hybrid ISFOA-AGCN-ILSTM model for short-term prediction of dissolved oxygen in aquaculture systems | 2026, Aquaculture International | https://doi.org/10.1007/s10499-026-02462-w |
| PSG-Crossformer: a hybrid model for long-term dissolved oxygen prediction in aquaculture | 2025, Aquaculture International | https://doi.org/10.1007/s10499-025-01983-0 |
| Prediction of Dissolved Oxygen Content in Aquaculture Based on Clustering and Improved ELM | 2021, IEEE Access | https://doi.org/10.1109/access.2021.3064029 |
| An Improved Autoformer-Based Dissolved Oxygen Prediction Model for Aquaculture | 2023, IEEE SWC | https://doi.org/10.1109/swc57546.2023.10449029 |

## 3.2 ESP32 智能投喂开源项目（star 数 API 实测）

| 项目 | Star 数 | 最后更新 | 语言 | **是否含 AI/视觉** | 核心功能 | 链接 |
|---|---|---|---|---|---|---|
| yyq8548/Smart-fish-feeder-digital-control | **62** | 2026-08-02 | Python | **否** | 认证式网页控制板，遥测/远程投喂/泵清洗/冷却/告警/MQTT | https://github.com/yyq8548/Smart-fish-feeder-digital-control |
| itohio/FishFeeder | **23** | 2025-05-04 | Go | **否** | ESP32 M5StickC 自动喂食器，TinyGo | GitHub API 实测 |
| nahueltaibo/fish-feeder | **5** | 2026-04-28 | C++ | **否** | ESP32 自动喂食器 | GitHub API 实测 |
| ColoMAX/fishfeeder | **5** | 2024-01-21 | YAML | **否** | ESP8266 + ESPHome 独立喂食器 | GitHub API 实测 |
| alejoarte/fish-feeder-web-demo | **3** | 2026-05-24 | JavaScript | **否** | 小规模罗非鱼养殖，**基于生长的投喂排程** | GitHub API 实测 |
| IBishopI/fishfeeder_esp32cam_telegram | **3** | 2022-01-28 | C++ | **否** | ESP32-CAM + Telegram bot 控制喂食 | GitHub API 实测 |
| Walid26619/AQUA_PULSE_SMART_FISH_FEEDER | 2 | 2026-08-03 | C++ | 否 | — | GitHub API 实测 |
| cuong121005-lx/ESP32-Automatic-Fish-Feeder | 1 | 2026-01-02 | C++ | 否 | 舵机 + OLED + NTP + 深度睡眠 | GitHub API 实测 |
| BogyS/FishFeeder | 0 | 2025-11-14 | C++ | 否 | ESP32-CAM 喂食器（相机未用于推理） | GitHub API 实测 |
| khalid200704/Automatic-Feeder-System-for-Betta-Fish | 0 | 2025-12-26 | — | 否 | "Environmental-Aware Feeding Controller"（传感器驱动） | GitHub API 实测 |

> **事实**：GitHub 上 star 最高的 ESP32 鱼用投喂项目（62 star）**完全不包含 AI/视觉**。投喂生态几乎全部是「定时器 + 舵机 + Blynk/MQTT」，无一是视觉驱动投喂。

### 学术侧：智能投喂论文（Crossref 元数据已验证）

| 论文 | 年份/期刊 | DOI | 是否含 AI |
|---|---|---|---|
| Intelligent IoT-Based Fish Feeding System Using Species Recognition and Predictive Feeding Models | 2026, IEEE CSNT | https://doi.org/10.1109/csnt69054.2026.11502493 | 声称含种类识别（**全文未获取，硬件平台未验证**） |
| Intelligent Fish Farming: CNN-Based Real-Time Species Recognition and Feeding Decision Support | 2025 | https://doi.org/10.17492/jpi/icisi2025/251248 | CNN 种类识别（全文未获取） |
| A Systematic Survey of Optimized Automatic Fish Feeding System Using IoT | 2024, IEEE SCOPES | https://doi.org/10.1109/scopes64467.2024.10990901 | 综述 |
| ESP32 IoT Auger-Based Automatic Feeder for Fish Pellets | 2025, Salaga Journal | https://doi.org/10.70124/salaga.v3i2.2134 | 无 AI（螺旋送料 + IoT） |
| Pemberi Pakan Ikan Gurame Otomatis Menggunakan ESP32 berbasis IoT-Telegram | 2025 | https://doi.org/10.29407/noe.v8i01.23361 | 无 AI |
| Perancangan dan Pengembangan Automatic Fish Feeder Menggunakan Aplikasi Mobile Blynk dan ESP32 | 2024 | https://doi.org/10.37253/telcomatics.v9i2.10077 | 无 AI |

## 3.3 Edge Impulse / TinyML 在 aquaculture 的案例

| 案例 | 平台 | 端侧/云端 | 实测指标 | 来源 |
|---|---|---|---|---|
| **Real-time rapid visual fish disease detection (TinyML)** | **RISC-V MCU**（非 ESP32） | **端侧** | mAP50-95 = **0.736**（YOLO11n） | https://doi.org/10.1007/s10499-025-02256-6 |
| Edge Impulse 论坛：ESP32-S3 量化二分类 | ESP32-S3 | **端侧** | **inference 675 ms**（DSP 5 ms） | https://forum.edgeimpulse.com/t/use-psram-for-impulse-deployment-on-esp32-s3/12849 |
| Edge Impulse 官方 FOMO 文档 | 通用 | — | **未取到** ESP32 专项官方 FPS 数字 | https://docs.nordic.edgeimpulse.com/studio/projects/learning-blocks/blocks/object-detection |
| Edge Impulse 官方项目库（鱼类） | — | — | **未取到**（项目页 JS 渲染） | https://edgeimpulse.com/projects |

> **未找到**：Edge Impulse 官方公开项目库中，**未能找到**可验证的 aquaculture / 鱼类检测项目页面及其实测指标。
> 另：Hackster.io 的 "Machine learning based Aquaculture Ecosystem analysis" 页面**返回 Cloudflare 403**，无法核实内容。

## 3.4 任务 3 结论

**在 aquaculture 场景，ESP32 的主流角色是「传感器节点 + 执行器」，AI 在云端。**
唯一一篇真正把预测模型部署到 ESP32 上跑的水产论文（Sensors 2025, s25196159），用的是 **MLR / 决策树 / 随机森林等经典机器学习**，而**不是神经网络** —— 并且论文自己把「没有任何前人在超低成本 MCU 上部署水产预测 ML」作为 novelty 来陈述。

---

# 任务 4：工程结论 —— 池塘养鱼场户外监测，ESP32-S3 该做什么、不该做什么

## 4.1 性能边界总表（全部基于任务 1 的实测事实）

| 能力档位 | 任务类型 | 输入分辨率 | 模型 | ESP32-S3 实测延迟 | 实测 FPS | 可行性判定 |
|---|---|---|---|---|---|---|
| ✅ **甜点区** | 人脸检测（两阶段级联） | 120×160 → 48×48 | MSR+MNP int8 | **~37–40 ms** | **25–27 FPS** | 完全可行，可做实时视频 |
| ✅ **甜点区** | 行人/人员检测（单类） | 224×224 | PICO_S8_V1 int8 | **129.9 ms** | **7.7 FPS** | 可行，≈8 FPS |
| ✅ **可用区** | 单类目标检测 | 224×224 | ESPDet-Pico（0.36M 参数） | **126.2 ms** | **7.9 FPS** | 可行 |
| ✅ **可用区** | 单类目标检测（非方图） | 160×288 | ESPDet-Pico | **115.5 ms** | **8.7 FPS** | 可行 |
| ⚠️ **勉强** | 单类目标检测 | 416×416 | ESPDet-Pico | **449.5 ms** | **2.2 FPS** | 勉强，适合低帧率触发式 |
| ⚠️ **勉强** | 人脸检测（单阶段高精度） | 416×416 | ESPDet-Pico-Face | **437.0 ms** | **2.2 FPS** | 勉强 |
| ⚠️ **勉强** | 图像分类（ImageNet 1000类） | 224×224 | MobileNetV2 int8（双核） | **867.0 ms** | **1.14 FPS** | 勉强，≈1 FPS |
| ❌ **不可行** | 80 类 COCO 检测 | 320×320 | YOLO11n int8 | **6196.3 ms** | **0.16 FPS** | 不可行（6.2 s/帧） |
| ❌ **不可行** | 80 类 COCO 检测 | 512×512 | YOLO26n int8 | **7879.0 ms** | **0.13 FPS** | 不可行 |
| ❌ **不可行** | 80 类 COCO 检测 | 640×640 | YOLO26n int8 | **13194.0 ms** | **0.076 FPS** | 不可行 |
| ❌ **完全不可行** | 80 类 COCO 检测 | 640×640 | YOLO11n int8 | **26124.6 ms** | **0.038 FPS** | 26 s/帧 |

## 4.2 「能做什么」（工程推断，基于上述事实）

| 建议做的事 | 依据（事实） | 预期性能 | 备注 |
|---|---|---|---|
| **人员入侵检测**（有人/无人、越界告警） | esp-dl 行人检测 224×224 = 129.9 ms | **~7.7 FPS** | 单类，最适合户外鱼塘防盗 |
| **人脸检测 + 识别**（值班人员/陌生人） | esp-who MSR+MNP = 37–40 ms | **~25 FPS** | 官方级联模型是唯一真正实时的视觉能力 |
| **水面的「异常物体/漂浮物」粗检测** | ESPDet-Pico 224×224 = 126.2 ms | **~7.9 FPS** | 需自训练单类模型，用 esp-detection 流程 |
| **定时抓拍 + 端侧二分类筛选**（如"有鱼跃/无鱼跃"） | Edge Impulse ESP32-S3 二分类 inference 675 ms | **~1.5 FPS** | 低帧率事件触发，配 PSRAM 调大 arena |
| **水质数值预测**（溶解氧/pH 趋势） | Sensors 2025: ESP32 上跑 MLR，R²≈0.65–0.72 | 每小时/每几分钟一次 | **用经典 ML（线性回归/决策树/随机森林），不要用 LSTM** |
| **本地闭环控制**（增氧机/投喂机/水泵继电器） | Sensors 2025: ESP32 上实现预测+执行闭环 | — | 断网可运行，这是 ESP32 的核心价值 |
| **图像采集 + 上传，云端做重推理** | MDPI Sensors 2025: 端侧二分类预筛 + 云端 YOLOv8；端侧预筛使环路仅 459 ms | 端侧预筛 459 ms | **这是被论文验证过的正确架构** |

## 4.3 「不该做什么」（工程推断）

| 不该做的事 | 依据（事实） |
|---|---|
| ❌ **不要在 ESP32-S3 上跑 YOLOv5n / YOLOv8n / YOLO11n 的 COCO 级别检测** | 官方实测 YOLO11n@320 = **6196 ms**，@640 = **26125 ms**。且官方 note 指出 YOLO11n 光内存管理器就要 6 MB，PSRAM < 16 MB 时模型必须留 FLASH |
| ❌ **不要指望端侧做鱼类种类识别（多分类）** | ① GitHub 无任何可靠实证；② 唯一接近的论文用 RISC-V MCU 且只做**鱼病检测**，mAP50-95 仅 0.736；③ ESP32-S3 连 MobileNetV2 @224 都只有 1.14 FPS；④ 鱼的种类识别在真实水下场景本身是研究级难题 |
| ❌ **不要用神经网络做水质时序预测（LSTM/GRU）** | ESP32 上跑 LSTM 不现实；且唯一端侧落地的水产论文（Sensors 2025）证明**MLR 才是实用选择**，RFR 精度更高（R²>0.80）但计算量不合适 |
| ❌ **不要相信「云端 AI 服务器」方案的实时性** | MDPI Sensors 2025 实测：发 640×480 JPEG 到国际 broker 比本地多 **+5815 ms**；仅发文本消息时本地 broker 只要 **2 ms**。户外 4G/弱网下延迟不可控 |
| ❌ **不要期待"鱼类行为分析 CNN-LSTM"这类宣传** | 本次调研中宣称该能力的仓库（Alwyn2006，2 star）**仓库内只有一个 React 网页，没有任何固件或模型** |
| ⚠️ **不要把 ESP32-CAM（原版 ESP32）与 ESP32-S3 混为一谈** | MDPI Sensors 2025 用的 ESP32-CAM 是原版 ESP32（Xtensa LX6）；实测其错误归因于 "ESP32-CAM's limited computational power"。而**鱼类相关项目绝大多数用的是 ESP32-CAM，不是 S3** |

## 4.4 结论性建议架构（工程推断）

```
[户外鱼塘]
  ├─ 视觉节点：ESP32-S3 + 摄像头
  │    ├─ 端侧只做：低分辨率(≤320×320) 单类检测 / 二分类预筛
  │    │            目标：人员入侵(7.7 FPS)、水面异常(7.9 FPS)
  │    └─ 触发式抓拍 → 上传云端做重推理（论文验证架构，环路 ~459 ms）
  │
  ├─ 传感节点：ESP32(-S3) + DO/pH/温度/浊度
  │    └─ 端侧只做：经典 ML 数值预测（MLR，R²≈0.65–0.72）+ 本地闭环控制
  │
  └─ 云端/网关：多分类鱼种识别、LSTM 时序预测、大模型诊断
```

**如果必须做鱼类识别**：把识别模型放在**网关（树莓派/Jetson）或云端**，ESP32-S3 只做「有没有鱼/有没有异常」的触发门。这是唯一被实测数据支持的路线。

---

# 附：未找到可靠实证清单

| # | 未找到的内容 | 具体说明 |
|---|---|---|
| 1 | **ESP32 / ESP32-S3 端侧鱼类检测的实测精度** | 无任何项目报告 mAP / 准确率 |
| 2 | **ESP32 / ESP32-S3 端侧鱼类检测的实测帧率** | 无任何项目报告 FPS |
| 3 | **任何 star > 5 的 ESP32 鱼类识别开源项目** | GitHub `fish+detection+esp32` 仅 5 个仓库，全部 0 star |
| 4 | **ESP32 上的鱼类种类识别（多分类）成功案例** | 唯一近似工作用 RISC-V MCU 且是鱼病检测 |
| 5 | **Edge Impulse 官方项目中可验证的鱼类检测案例指标** | 项目页 JS 渲染，未能取到内容 |
| 6 | **Hackster.io 上的水产 ML 项目内容** | 返回 **Cloudflare 403**，无法核实 |
| 7 | **arXiv 上 "fish detection" + "ESP32" 的论文** | arXiv API 查询无返回 |
| 8 | **JorgeSan88/esp-detection 的独立贡献** | 经 API 验证为 espressif/esp-detection 的 **fork，0 star**；数据应归因上游 |
| 9 | **Alwyn2006/SMART-FISH-AQUARIUM 声称的 CNN-LSTM 端侧部署** | 仓库内**无任何固件/模型**，仅 React 网页 |
| 10 | **IT21179280/SMART-FISH-TANK 的 YOLOv8 实现与精度** | 仓库仅 README + 一个 zip，无源码、无精度数字 |
| 11 | **colliderkkz ESP32-S3 + LSTM 水质预测项目内容** | GitHub API 全字段 None，README 404，无法验证 |
| 12 | **Edge Impulse 论坛 675 ms 推理对应的输入分辨率** | 用户中途改过输入尺寸，页面未明确 |
| 13 | **"Optimizing Edge-AI on the ESP32-S3 Using SIMD" 的实测加速数字** | IEEE 付费墙，仅取到摘要首句 |
| 14 | **IEEE 11507635（Edge-Deployed ML 水产溶氧）的实测数字** | IEEE 付费墙，仅取到标题与 DOI |
| 15 | **IEEE 11647518（ESP32-P4 垂直鱼场）的技术细节** | IEEE 付费墙，仅取到标题与 DOI |
| 16 | **ESP32-S3 官方（espressif.com）规格页正文** | 返回 403 / JS 渲染；芯片规格改用第三方页并已标注 |
| 17 | **esp-who 仓库 README 中的实测 FPS** | README 只有定性描述（"higher fps"），无数字；数字来自官方 workshop 页 |
| 18 | **乐鑫官方 esp32-camera + esp-dl 例程的公开性能表** | 未找到含 FPS 的官方页面 |
| 19 | **B站/知乎/CSDN 上可验证的 ESP32 鱼类识别实测** | 检索到的中文内容均为智能鱼缸/温控等无关主题，或无法核实实测数据 |
| 20 | **YOLOv5n / YOLOv8n int8 在 ESP32-S3 上的官方或可复现实测** | 未找到；仅有 YOLO11n / YOLO26n 的官方数据可作同量级参照 |

---

*报告完成。所有斜体标注的「推断/推算」均为本人基于上述实测数字的计算，非原始页面数字。*
