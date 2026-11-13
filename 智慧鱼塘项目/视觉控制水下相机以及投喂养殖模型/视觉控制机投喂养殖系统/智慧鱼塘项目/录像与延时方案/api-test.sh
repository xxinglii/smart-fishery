#!/bin/bash
# 萤石开放平台 API 快速验证（鱼塘延时项目）
# 用法：先把下面三个变量填好，再依次执行各函数；不要把本文件分享给他人（含密钥）。
set -u

APP_KEY="填你的AppKey"
APP_SECRET="填你的AppSecret"
DEVICE_SERIAL="填设备序列号"
CHANNEL_NO="1"

BASE="https://open.ezviz.com"
TOKEN_FILE="/tmp/ys7_token.json"

get_token() {
  curl -s -X POST "$BASE/api/lapp/token/get" \
    -d "appKey=$APP_KEY&appSecret=$APP_SECRET" | tee "$TOKEN_FILE"
  echo
}

token() { python3 -c "import json;print(json.load(open('$TOKEN_FILE'))['data']['accessToken'])"; }

# ① 抓图（测试延时 API）
capture() {
  curl -s -X POST "$BASE/api/lapp/device/capture" \
    -d "accessToken=$(token)&deviceSerial=$DEVICE_SERIAL&channelNo=$CHANNEL_NO"
  echo
}

# ② 最近 24 小时告警（含事件现场图 alarmPicUrl）
alarms() {
  END=$(python3 -c "import time;print(int(time.time()*1000))")
  START=$((END - 86400000))
  curl -s -X POST "$BASE/api/lapp/alarm/device/callAlarmList" \
    -d "accessToken=$(token)&deviceSerial=$DEVICE_SERIAL&startTime=$START&endTime=$END&status=2&pageStart=0&pageSize=5"
  echo
}

case "${1:-}" in
  token)   get_token ;;
  capture) capture ;;
  alarms)  alarms ;;
  *) echo "用法: $0 token|capture|alarms" ;;
esac
