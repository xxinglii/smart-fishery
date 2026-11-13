/* ============================================================================
   selftest.js · 无头冒烟测试（node selftest.js）
   两件事：
   ① 8 个视图在完整 state 下都能渲染出 HTML，且不含 undefined / NaN / [object Object]
   ② 模拟数据 100% 符合《视觉系统_API契约_v1.md》的字段与枚举
   ========================================================================== */

const path = require('path');
const Data = require(path.join(__dirname,'data.js'));
// 浏览器里这些脚本共享全局作用域；node 里需要显式挂上去，app.js 才能找到它们
global.Data = Data;
global.API  = require(path.join(__dirname,'api.js'));
global.Feed = require(path.join(__dirname,'feed.js'));
global.Charts = require(path.join(__dirname,'charts.js'));
const App  = require(path.join(__dirname,'app.js'));

let pass=0, fail=0;
const rows=[];
function ok(name, cond, detail){
  if(cond){ pass++; rows.push(['PASS',name,detail||'']); }
  else    { fail++; rows.push(['FAIL',name,detail||'']); }
}
function section(t){ rows.push(['----',t,'']); }

/* ---------------- 构造完整 state ---------------- */
const S = App.initialState();
S.cameras   = Data.CAMERAS.map(c=>({...c}));
S.presets   = Data.PRESETS.slice();
S.events    = Data.events(120);
S.health    = Data.health();
S.config    = Data.CONFIG;
S.splash    = Data.splashSeries(24,300);
S.snapshots = Data.snapshots('2026-09-19','cam-pano',48);
S.logs      = Data.logs(40);
S.camId     = 'cam-pano';

/* ---------------- ① 视图渲染 ---------------- */
section('视图渲染（8 个）');
const BAD = [/undefined/, /NaN/, /\[object Object\]/, />null</];
Object.keys(App.VIEWS).forEach(name=>{
  let html='';
  try{ html = App.VIEWS[name](S); }
  catch(e){ ok(`view:${name}` , false, 'throw: '+e.message); return; }
  const hit = BAD.find(re=>re.test(html));
  ok(`view:${name}`, !hit && html.length>400,
     hit? `包含 ${hit}` : `${html.length} 字符`);
});

/* 空数据也不能崩 */
section('边界：空数据');
const EMPTY = Object.assign({}, S, {events:[], snapshots:[], logs:[], cameras:[], presets:[], splash:{series:[],feed_windows:[]}});
Object.keys(App.VIEWS).forEach(name=>{
  let html='';
  try{ html = App.VIEWS[name](EMPTY); }
  catch(e){ ok(`empty:${name}`, false, 'throw: '+e.message); return; }
  const hit = BAD.find(re=>re.test(html));
  ok(`empty:${name}`, !hit, hit? `包含 ${hit}` : 'ok');
});

/* ---------------- ② 契约一致性 ---------------- */
section('契约 §1 health');
const h = Data.health();
ok('health.ok 布尔', typeof h.ok==='boolean');
ok('health.uptime_s 整数', Number.isInteger(h.uptime_s));
ok('health.pi 四项', ['cpu_pct','mem_pct','temp_c','disk_free_gb'].every(k=>typeof h.pi[k]==='number'));
ok('health.net 字段', ['type','rssi_dbm','carrier','uplink_kbps','month_bytes','month_quota_bytes'].every(k=>k in h.net));
ok('health.storage 字段', ['recording','days_kept','bytes_per_day'].every(k=>k in h.storage));
ok('health.services 数组', Array.isArray(h.services) && h.services.every(s=>typeof s.name==='string' && typeof s.ok==='boolean'));

section('契约 §2 cameras / presets / ptz');
const cams = Data.CAMERAS;
ok('相机 ≥2 台', cams.length>=2);
ok('字段齐全', cams.every(c=>['id','name','role','model','ip','rtsp','onvif','online','resolution','fps','bitrate_kbps','ir_m'].every(k=>k in c)));
ok('role 枚举', cams.every(c=>['panorama','detail'].includes(c.role)));
ok('rtsp 协议头', cams.every(c=>/^rtsp:\/\//.test(c.rtsp)));
ok('rtsp 已脱敏', cams.every(c=>!/(admin:)(?!\*\*\*)/.test(c.rtsp)));
ok('有且仅有一台带云台', cams.filter(c=>c.ptz).length===1);
const pt = cams.find(c=>c.ptz).ptz;
ok('ptz 字段', ['pan','tilt','zoom','zoom_max','moving','preset_id'].every(k=>k in pt));
ok('预置位归属正确', Data.PRESETS.every(p=>p.camera_id==='cam-detail'));
ok('预置位坐标合法', Data.PRESETS.every(p=>Number.isFinite(p.pan)&&p.tilt<=0&&p.zoom>=1));

section('契约 §3 events');
const evs = Data.events(200);
const TYPES=['splash_activity','surface_aggregation','person','offline','tamper','motion'];
const SEVS=['info','notice','warn','critical'];
ok('事件非空', evs.length>0);
ok('类型枚举合法', evs.every(e=>TYPES.includes(e.type)));
ok('严重度枚举合法', evs.every(e=>SEVS.includes(e.severity)));
ok('置信度 ∈ [0,1]', evs.every(e=>e.confidence>=0 && e.confidence<=1));
ok('证据等级 ∈ {A,B,C}', evs.every(e=>['A','B','C'].includes(e.evidence)));
ok('id 唯一', new Set(evs.map(e=>e.id)).size===evs.length);
ok('ts 为 Unix 秒', evs.every(e=>Number.isInteger(e.ts) && e.ts>1.7e9 && e.ts<2.0e9));
ok('按时间倒序', evs.every((e,i)=>i===0||evs[i-1].ts>=e.ts));
ok('splash 事件带 metric.ratio', evs.filter(e=>e.type==='splash_activity').every(e=>e.metric && typeof e.metric.ratio==='number'));
ok('snapshot_url 指向 API', evs.every(e=>e.snapshot_url.startsWith('/api/v1/events/')));

section('契约 §4 metrics / §5 snapshots / §6 config / §7 logs');
const sp = Data.splashSeries(24,300);
ok('series 非空', sp.series.length>0);
ok('series 字段', sp.series.every(p=>['ts','v_value','baseline','thr'].every(k=>typeof p[k]==='number')));
ok('v_value > 0', sp.series.every(p=>p.v_value>0));
ok('feed_windows 有 HH:MM', sp.feed_windows.every(w=>/^\d{2}:\d{2}$/.test(w.start)&&/^\d{2}:\d{2}$/.test(w.end)));
ok('投喂窗口内确有抬升', (()=>{
  const max=Math.max(...sp.series.map(p=>p.v_value));
  const base=Math.max(...sp.series.map(p=>p.baseline));
  return max > base*1.15;
})(), '峰值需显著高于基线');

const sn = Data.snapshots('2026-09-19','cam-pano',20);
ok('抓图字段齐全', sn.every(s=>['ts','camera_id','url','trigger'].every(k=>k in s)));
ok('抓图 trigger 枚举', sn.every(s=>['interval','event','manual'].includes(s.trigger)));
ok('抓图 url 指向 API', sn.every(s=>s.url.startsWith('/api/v1/snapshots/')));
const cfg = Data.CONFIG;
ok('config 六段', ['feed_windows','thresholds','capture','upload','record','patrol'].every(k=>k in cfg));
ok('阈值合理', cfg.thresholds.splash_ratio>1 && cfg.thresholds.aggregation_area_pct>0 && cfg.thresholds.person_confidence<1);
ok('上传策略枚举', ['thumbs_only','events_only','full'].includes(cfg.upload.policy));
ok('日志级别枚举', Data.logs(30).every(l=>['info','warn','error'].includes(l.level)));

section('派生一致性');
const sum = Data.summarize(evs);
ok('summarize 与事件流一致', sum.total===evs.filter(e=>e.ts>=Math.floor(Date.now()/1000)-86400).length);
ok('未确认数 ≤ 总数', sum.unacked<=sum.total);

/* ---------------- 输出 ---------------- */
const w = Math.max(...rows.map(r=>r[1].length)) + 2;
console.log('\n塘口视觉监控台 · 自检\n' + '─'.repeat(w+22));
rows.forEach(r=>{
  if(r[0]==='----'){ console.log(`\n▌ ${r[1]}`); return; }
  const mark = r[0]==='PASS' ? '✔' : '✘';
  console.log(`  ${mark} ${r[1].padEnd(w)} ${r[2]}`);
});
console.log('─'.repeat(w+22));
console.log(`  通过 ${pass} · 失败 ${fail}\n`);
process.exit(fail?1:0);
