#!/bin/bash
# 批量下载 SD 卡本地录像（替代 Windows 客户端 / 手动导出）
#
# 用法:
#   ./download-recordings.sh            下载昨天的录像
#   ./download-recordings.sh 2026-09-05 下载指定日期
#
# 原理: 查询当天录像片段列表 → 逐段取回放流地址(type=2 本地录像, flv) → ffmpeg 落盘
# 前置: 好友已完成设备托管授权（见 延时方案.md 第七节），并填好 CONFIG。
# 注意: 本脚本在拿到真实凭证前未实测；若某步报错，把屏幕输出贴出来即可定位。
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"

# ================== CONFIG ==================
APP_KEY=""
APP_SECRET=""
DEVICE_SERIAL=""    # 大写
CHANNEL_NO="1"
OUT_DIR="$DIR/录像下载"
BASE="https://open.ezviz.com"
# ============================================

DAY="${1:-$(date -v-1d +%F)}"     # macOS 语法；Linux 改用 $(date -d "yesterday" +%F)
START="$DAY 00:00:00"
END="$DAY 23:59:59"
mkdir -p "$OUT_DIR"
TOKEN_CACHE="$OUT_DIR/.token.json"

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
TOK=$(token)

# ① 先确认这一天有录像
HAS=$(curl -s -X POST "$BASE/api/lapp/device/video/local/time" \
  -d "accessToken=$TOK&deviceSerial=$DEVICE_SERIAL&channelNo=$CHANNEL_NO&startTime=$START&endTime=$END")
echo "$HAS" | grep -q '"hasVideo":true' || { echo "$DAY 没有本地录像（或接口返回异常）: $HAS"; exit 0; }
echo "$DAY 有本地录像，查询片段…"

# ② 查片段列表（起止须在同一天内/24小时内），输出: 开始\t结束\t时长秒
SEGS=$(curl -s "$BASE/api/v3/das/device/local/video/query" \
  --data-urlencode "accessToken=$TOK" \
  --data-urlencode "deviceSerial=$DEVICE_SERIAL" \
  --data-urlencode "channelNo=$CHANNEL_NO" \
  --data-urlencode "startTime=$START" \
  --data-urlencode "endTime=$END" \
  -G)
echo "$SEGS" > "$OUT_DIR/.segments_$DAY.json"   # 留底，便于排查

echo "$SEGS" | python3 -c "
import json,sys,datetime
j=json.load(sys.stdin)
data=j.get('data') or j.get('videos') or []
if isinstance(data,dict): data=data.get('videoList') or data.get('list') or []
def norm(t):
    if isinstance(t,(int,float)): return int(t)          # 毫秒时间戳
    for f in ('%Y-%m-%d %H:%M:%S','%Y-%m-%dT%H:%M:%S'):
        try: return int(datetime.datetime.strptime(t,f).timestamp()*1000)
        except ValueError: pass
    raise SystemExit('无法解析时间格式: %r，请查看 .segments_%s.json' % (t,'$DAY'))
for seg in data:
    s=norm(seg.get('startTime') or seg.get('beginTime') or seg.get('start_time'))
    e=norm(seg.get('endTime') or seg.get('stopTime') or seg.get('end_time'))
    if e<=s: continue
    print('%s\t%s\t%d' % (datetime.datetime.fromtimestamp(s/1000).strftime('%F %T'),
                          datetime.datetime.fromtimestamp(e/1000).strftime('%F %T'), (e-s)//1000))
" > "$OUT_DIR/.list_$DAY.tsv" || { echo "片段解析失败，原始数据在 $OUT_DIR/.segments_$DAY.json"; exit 1; }

N=$(wc -l < "$OUT_DIR/.list_$DAY.tsv" | tr -d ' ')
[ "$N" -eq 0 ] && { echo "未解析到片段（原始数据已留存，可贴出来分析）"; exit 0; }
echo "共 $N 个片段，开始下载…"

# ③ 逐段: 取回放地址 → ffmpeg 落盘
I=0
while IFS=$'\t' read -r S E DUR; do
  I=$((I+1))
  OUT=$(printf "%s/%s_%s_%03d.mp4" "$OUT_DIR" "$DEVICE_SERIAL" "$DAY" "$I")
  [ -f "$OUT" ] && { echo "跳过已存在: $OUT"; continue; }
  URL=$(curl -s -X POST "$BASE/api/lapp/v2/live/address/get" \
    -d "accessToken=$TOK&deviceSerial=$DEVICE_SERIAL&channelNo=$CHANNEL_NO&protocol=4&type=2&startTime=$S&stopTime=$E" \
    | tee "$OUT_DIR/.addr_$I.json" \
    | python3 -c "
import json,sys
j=json.load(sys.stdin)
if str(j.get('code'))!='200': sys.exit('回放地址获取失败(第 $I 段): '+str(j))
print(j['data']['url'])")
  [ -z "${URL:-}" ] && { echo "第 $I 段取地址失败"; continue; }
  echo "[$I/$N] ${DUR}s  $S"
  ffmpeg -hide_banner -loglevel warning -y -i "$URL" -t "$DUR" -c copy "$OUT" \
    || { rm -f "$OUT"; echo "第 $I 段下载失败"; }
done < "$OUT_DIR/.list_$DAY.tsv"
rm -f "$OUT_DIR/.addr_"*.json
echo "完成，文件在: $OUT_DIR"
