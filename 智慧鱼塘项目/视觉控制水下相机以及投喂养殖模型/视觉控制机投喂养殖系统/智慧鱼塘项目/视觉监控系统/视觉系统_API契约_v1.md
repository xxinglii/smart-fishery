---
作者: DeepSeek
日期: 2026-09-19
状态: v1 契约（网页端与固件端共同遵守）
关联: `采购清单_鱼塘视觉系统_v1.md` · `yutang-vision-console/`（前端）· `yutang-vision-firmware/`（固件）
---

# 鱼塘视觉系统 · Web↔固件 API 契约 v1

> **一条铁律**：网页端只认这个契约，固件端只实现这个契约。
> 前端在没有真机时走 **MOCK 模式**（`data.js` 里的假数据），两种模式的**数据结构必须完全一致**，
> 这样"换后端"只是把 `API_BASE` 从 `mock` 改成 `http://树莓派IP:8080`。

## 0. 约定

- 基址：`http://<树莓派IP>:8080`
- 全部 `GET` 返回 JSON；`POST/PUT` 请求体 JSON，返回 `{"ok": true, ...}` 或 `{"ok": false, "error": "..."}`
- 时间戳：**Unix 秒（整数）**，前端负责本地化显示
- 实时推送：**SSE**（`text/event-stream`），不用 WebSocket（4G 下更省、易穿透）
- 静态资源：`GET /` 直接返回网页端（同一套文件），所以现场只跑一个服务

---

## 1. 健康与状态

### `GET /api/v1/health`
```json
{
  "ok": true,
  "version": "1.0.0",
  "uptime_s": 84213,
  "mode": "live",              // live | mock
  "pi": { "cpu_pct": 21.4, "mem_pct": 38.0, "temp_c": 47.2, "disk_free_gb": 41.2 },
  "net": { "type": "4g", "rssi_dbm": -71, "carrier": "中国移动",
           "uplink_kbps": 1840, "month_bytes": 3221225472, "month_quota_bytes": 10737418240 },
  "storage": { "recording": true, "days_kept": 14, "bytes_per_day": 17179869184 },
  "services": [ { "name": "rtsp-ingest", "ok": true }, { "name": "detector", "ok": true } ]
}
```

## 2. 相机

### `GET /api/v1/cameras`
```json
[{
  "id": "cam-pano", "name": "全景位 · 塘东北角", "role": "panorama",
  "model": "DS-2CD3T86FWDV3-I3S", "ip": "192.168.1.64",
  "rtsp": "rtsp://admin:***@192.168.1.64:554/Streaming/Channels/101",
  "onvif": true, "online": true,
  "resolution": "3840x2160", "fps": 20, "bitrate_kbps": 4096,
  "ir_m": 30, "ptz": null,
  "snapshot_url": "/api/v1/cameras/cam-pano/snapshot"
},{
  "id": "cam-detail", "name": "细节位 · 塘西南角", "role": "detail",
  "model": "DS-2DC4423IW-D", "ip": "192.168.1.65",
  "rtsp": "rtsp://admin:***@192.168.1.65:554/Streaming/Channels/101",
  "onvif": true, "online": true,
  "resolution": "2560x1440", "fps": 25, "bitrate_kbps": 4096,
  "ir_m": 100,
  "ptz": { "pan": 132.5, "tilt": -18.0, "zoom": 3.2, "zoom_max": 23,
           "moving": false, "preset_id": 2 },
  "snapshot_url": "/api/v1/cameras/cam-detail/snapshot"
}]
```

### `GET /api/v1/cameras/{id}/snapshot` → `image/jpeg`（**注意：4G 下这是主要手段**）

### `POST /api/v1/cameras/{id}/ptz`
```json
{ "action": "move",   "dx": -0.2, "dy": 0.0, "zoom": 0.0 }   // dx/dy ∈ [-1,1]，相对步进
{ "action": "goto",   "preset_id": 3 }
{ "action": "save",   "preset_id": 3, "name": "投料点" }
{ "action": "home" }
{ "action": "patrol", "on": true, "preset_ids": [1,2,3], "dwell_s": 30 }
```
返回 `{ "ok": true, "ptz": { ...同 cameras[].ptz... } }`

### `GET /api/v1/presets?camera_id=cam-detail`
```json
[ { "id": 1, "name": "投料点", "camera_id": "cam-detail", "pan": 118.0, "tilt": -22.0, "zoom": 6.0 },
  { "id": 2, "name": "塘中央", "camera_id": "cam-detail", "pan": 168.0, "tilt": -9.0, "zoom": 1.0 },
  { "id": 3, "name": "进水口", "camera_id": "cam-detail", "pan": 205.0, "tilt": -14.0, "zoom": 4.0 } ]
```

## 3. 事件

### `GET /api/v1/events?since=<ts>&type=<t>&limit=200`
```json
[{
  "id": "ev-20260919-0007",
  "ts": 1789001234,
  "camera_id": "cam-pano",
  "type": "splash_activity",       // splash_activity | surface_aggregation | person | offline | tamper | motion
  "severity": "info",              // info | notice | warn | critical
  "confidence": 0.82,
  "title": "摄食水花强度短时上升",
  "detail": "V-Value 1.9× 基线，持续 42 s；区域：投料点 20 m 半径",
  "metric": { "v_value": 0.41, "baseline": 0.216, "ratio": 1.9, "duration_s": 42 },
  "snapshot_url": "/api/v1/events/ev-20260919-0007/snapshot",
  "clip_url": "/api/v1/events/ev-20260919-0007/clip",
  "acked": false,
  "evidence": "C"                  // A 实测 / B 经验 / C 演示，沿用本项目证据等级
}]
```

### `POST /api/v1/events/{id}/ack` → `{"ok": true}`
### `GET /api/v1/events/{id}/snapshot` → `image/jpeg`
### `GET /api/v1/events/{id}/clip` → `video/mp4`（可选；4G 下建议只给 snapshot）

### `GET /api/v1/stream/events` （SSE）
```
event: event
data: { ...单个 event 对象... }
```

## 4. 指标曲线

### `GET /api/v1/metrics/splash?camera_id=cam-pano&window=24h&step=300`
```json
{ "window": "24h", "step": 300,
  "series": [ { "ts": 1788912000, "v_value": 0.12, "baseline": 0.20, "thr": 0.40 } ],
  "feed_windows": [ { "start": "06:30", "end": "07:10" }, { "start": "16:30", "end": "17:20" } ] }
```

## 5. 抓图墙 / 回看

### `GET /api/v1/snapshots?date=2026-09-19&camera_id=cam-pano&limit=500`
```json
[ { "ts": 1789000000, "camera_id": "cam-pano", "url": "/api/v1/snapshots/1789000000.jpg",
    "trigger": "interval" } ]   // interval | event | manual
```

## 6. 配置

### `GET /api/v1/config` / `PUT /api/v1/config`
```json
{
  "feed_windows": [ { "start": "06:30", "end": "07:10" }, { "start": "16:30", "end": "17:20" } ],
  "thresholds": { "splash_ratio": 1.6, "aggregation_area_pct": 4.0, "person_confidence": 0.6 },
  "capture": { "interval_s": 60, "on_event": true, "jpeg_quality": 85, "max_width": 1920 },
  "upload": { "policy": "thumbs_only", "max_kbps": 512, "quota_gb_month": 10 },
  "record": { "local_full_stream": true, "keep_days": 14 },
  "patrol": { "on": true, "preset_ids": [1,2,3], "dwell_s": 30 }
}
```

## 7. 日志

### `GET /api/v1/logs?limit=200`
```json
[ { "ts": 1789001234, "level": "warn", "src": "rtsp-ingest",
    "msg": "cam-detail 重连成功（第 2 次）" } ]
```

---

## 8. 固件侧必须实现的检测（v1 范围）

| 事件类型 | 判据（v1 可落地版） | 说明 |
|---|---|---|
| `splash_activity` | 帧差/光流在投料区 ROI 内的**运动像素占比**，相对基线的比值 ≥ `thresholds.splash_ratio` | 对应方案二调研的 **V-Value**（强信号，96.53% 论文准确率） |
| `surface_aggregation` | 暗斑连通域面积占比 ≥ `aggregation_area_pct`，持续 ≥ N 帧 | 浮头/聚集的粗略代理 |
| `person` | 立杆侧警戒区内检出人形（可先用 OpenCV HOG / MobileNet-SSD；**不必上 YOLO**） | 防偷捕 |
| `offline` | RTSP 连续失败 ≥ 30 s | 设备看护 |
| `tamper` | 画面整体亮度/方差突变（遮挡、喷水、移位） | 防破坏 |

> **明确不做**（有项目内证据否决）：数鱼、数饲料颗粒、估重、估生物量。
> 前端也不提供这些页面——**能力边界要写在界面上，不是写在说明书里**。

---

📌 痕迹 | @DeepSeek · 2026-09-19 · 新建：Web 与固件共用的 API 契约 v1（8 组端点 + 5 类事件判据）
