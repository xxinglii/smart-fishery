#!/bin/bash
# 鱼塘短片段录制器（定时 / 触发 两种模式，支持多路摄像头）
#
# 用法:
#   ./record.sh timed       定时录制（默认 20 秒/路）
#   ./record.sh triggered   触发/关键动作录制（默认 30 秒/路）
# 可选环境变量:
#   JITTER=1800  先随机 sleep 0~1800 秒再录（用于"时不时录一段"，避免整点扎堆）
#
# 前置条件: 设备过户或托管授权完成（见 延时方案.md），并填好下方 CONFIG。
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"

# ================== CONFIG ==================
APP_KEY=""          # 开放平台 AppKey
APP_SECRET=""       # 开放平台 AppSecret
DEVICE_SERIAL=""    # 设备序列号（大写）
CHANNELS="1 2 3 4"  # 要录的通道号，空格分隔；单路填 "1"
LIVE_URL=""         # 可填固定直播地址(仅单路时有效)；留空则每次运行时自动按通道获取(flv)
PROTOCOL="4"        # 4=flv(推荐)  2=hls  3=rtmp  1=ezopen(仅H.265设备,ffmpeg不支持,别用)
QUALITY="2"         # 1=高清 2=流畅（多路务必用流畅，流量×路数）
OUT_DIR="$DIR/录像"
DURATION_TIMED=20
DURATION_TRIGGERED=30
MIN_FREE_GB=5       # 磁盘剩余低于此值时自动删最旧片段
KEEP_DAYS=30
# ============================================

MODE="${1:-timed}"
[ "$MODE" = "triggered" ] && DUR=$DURATION_TRIGGERED || DUR=$DURATION_TIMED
[ "${JITTER:-0}" -gt 0 ] 2>/dev/null && sleep $((RANDOM % JITTER))

mkdir -p "$OUT_DIR"
TOKEN_CACHE="$OUT_DIR/.token.json"
BASE="https://open.ezviz.com"

token() {
  if [ -f "$TOKEN_CACHE" ] && [ "$(python3 -c "import json,time;d=json.load(open('$TOKEN_CACHE'));print('ok' if d.get('expireAt',0)>time.time()+60000 else '')" 2>/dev/null)" = "ok" ]; then
    python3 -c "import json;print(json.load(open('$TOKEN_CACHE'))['accessToken'])"; return
  fi
  curl -s -X POST "$BASE/api/lapp/token/get" -d "appKey=$APP_KEY&appSecret=$APP_SECRET" \
    | python3 -c "
import json,sys,time
j=json.load(sys.stdin)
if str(j.get('code'))!='200': sys.exit('token获取失败: '+str(j))
tok=j['data']['accessToken']; exp=j['data']['expireTime']
json.dump({'accessToken':tok,'expireAt':time.time()*1000+int(exp)}, open('$TOKEN_CACHE','w'))
print(tok)"
}

live_url() {  # $1=通道号 → 输出该通道的 flv 直播地址
  if [ -n "$LIVE_URL" ]; then echo "$LIVE_URL"; return; fi
  local TOK=$1
  curl -s -X POST "$BASE/api/lapp/v2/live/address/get" \
    -d "accessToken=$TOK&deviceSerial=$DEVICE_SERIAL&channelNo=$2&protocol=$PROTOCOL&quality=$QUALITY" \
    | python3 -c "
import json,sys
j=json.load(sys.stdin)
if str(j.get('code'))!='200': sys.exit('直播地址获取失败(ch$2): '+str(j))
print(j['data']['url'])"
}

[ -z "$APP_KEY" ] && [ -z "$LIVE_URL" ] && { echo "请先在脚本里填 APP_KEY/APP_SECRET"; exit 1; }
TOK=$(token)
TS=$(date +%Y%m%d_%H%M%S)
PREFIX=$([ "$MODE" = "triggered" ] && echo "triggered" || echo "timed")

for CH in $CHANNELS; do
  URL=$(live_url "$TOK" "$CH")
  [ -z "$URL" ] && continue
  OUT="$OUT_DIR/${PREFIX}_ch${CH}_${TS}.mp4"
  echo "[$TS] ch$CH 录制 ${DUR}s"
  ffmpeg -hide_banner -loglevel warning -y -i "$URL" -t "$DUR" -c copy "$OUT" \
    || { rm -f "$OUT"; echo "ch$CH 录制失败"; }
done

# 磁盘保护：空间不足删最旧
while [ "$(df -g "$OUT_DIR" | awk 'NR==2{print $4}')" -lt "$MIN_FREE_GB" ]; do
  OLD=$(ls -1 "$OUT_DIR"/*.mp4 2>/dev/null | head -1)
  [ -z "$OLD" ] && break
  rm -f "$OLD"; echo "空间不足，删除最旧: $OLD"
done
# 过期清理
find "$OUT_DIR" -name "*.mp4" -mtime "+$KEEP_DAYS" -delete 2>/dev/null
echo "完成"
