/* ============================================================================
   app.js · 路由 + 视图
   视图一律是**纯函数**：state → HTML 字符串（这样 selftest 能在 node 里直接断言）
   需要 canvas / 事件绑定的部分放在 afterRender()。
   ========================================================================== */

const App = (() => {

  const PAGES = [
    {code:'01', path:'OVERVIEW',    name:'总览',      view:'overview'},
    {code:'02', path:'LIVE',        name:'实时画面',  view:'live'},
    {code:'03', path:'EVENTS',      name:'事件中心',  view:'events'},
    {code:'04', path:'PLAYBACK',    name:'回看',      view:'playback'},
    {code:'05', path:'PTZ',         name:'巡航',      view:'ptz'},
    {code:'06', path:'DEVICES',     name:'设备与网络',view:'devices'},
    {code:'07', path:'SETTINGS',    name:'设置',      view:'settings'},
    {code:'08', path:'INTEGRATION', name:'接入说明',  view:'integration'}
  ];

  /* ---------------- 工具 ---------------- */
  const esc = s => String(s==null?'':s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  const p2 = n => String(n).padStart(2,'0');
  const fmtTime = ts => { const d=new Date(ts*1000); return `${p2(d.getHours())}:${p2(d.getMinutes())}:${p2(d.getSeconds())}`; };
  const fmtHM   = ts => { const d=new Date(ts*1000); return `${p2(d.getHours())}:${p2(d.getMinutes())}`; };
  const fmtDate = ts => { const d=new Date(ts*1000); return `${d.getFullYear()}-${p2(d.getMonth()+1)}-${p2(d.getDate())}`; };
  const fmtBytes= b => { if(b==null) return '—'; const u=['B','KB','MB','GB','TB']; let i=0,v=b;
                         while(v>=1024&&i<u.length-1){v/=1024;i++} return `${v.toFixed(v<10&&i>1?1:0)} ${u[i]}`; };
  const fmtDur  = s => s==null?'—':(s<60?`${s} s`:(s<3600?`${Math.floor(s/60)} min`:`${(s/3600).toFixed(1)} h`));
  const SEV = {info:'提示',notice:'关注',warn:'告警',critical:'严重'};
  const sevClass = s => `sev-${SEV[s]?s:'info'}`;
  const typeLabel = t => (Data.EVENT_TYPES[t]||{label:t}).label;
  const evBadge = lv => `<span class="ev ${esc(lv)}" title="证据等级：A=实测/文献 · B=经验待校准 · C=演示值">${esc(lv)}</span>`;
  const diffMin = ts => Math.round((Date.now()/1000 - ts)/60);

  /* ---------------- 初始状态 ---------------- */
  function initialState(){
    return {
      route:'overview',
      camId:'cam-pano',
      range:'24h',
      evType:'',
      date:fmtDate(Date.now()/1000),
      selectedEvent:null,
      cameras:[], presets:[], events:[], health:null, config:null,
      splash:null, snapshots:[], logs:[], toastSeq:0
    };
  }

  /* ==========================================================================
     视图 01 · 总览
     ========================================================================== */
  function overview(S){
    const h = S.health, sum = Data.summarize(S.events);
    const net = h ? h.net : {}, stor = h ? h.storage : {}, pi = h ? h.pi : {};
    const quotaPct = net.month_quota_bytes ? (net.month_bytes/net.month_quota_bytes*100) : 0;
    const online = S.cameras.filter(c=>c.online).length;

    return `
    <div class="notice">
      <b>能力边界先说清</b>：本系统做的是<b>事件级观察</b>（摄食水花、水面聚集、人形入侵、设备离线）。
      <b>不提供</b>数鱼、数饲料颗粒、估重、生物量反演——这四项在本项目调研中已被几何与实测双重否决。
      每个数字都带证据等级角标 ${evBadge('A')}${evBadge('B')}${evBadge('C')}，鼠标悬停可看含义。
    </div>

    <div class="grid g4" style="margin-top:16px">
      ${kpi('今日事件', sum.total, '条', `未确认 ${sum.unacked} 条`, sum.unacked?'warn':'ok')}
      ${kpi('摄食水花', sum.splash, '次', '投喂时段内检测到的强度上升', 'info')}
      ${kpi('相机在线', `${online}/${S.cameras.length}`, '', online===S.cameras.length?'RTSP 双路正常':'存在离线通道', online===S.cameras.length?'ok':'bad')}
      ${kpi('4G 本月用量', (net.month_bytes/1073741824||0).toFixed(2), 'GB', `配额 ${(net.month_quota_bytes/1073741824||0).toFixed(0)} GB · 上行 ${net.uplink_kbps||0} kbps`, quotaPct>80?'warn':'ok')}
    </div>

    <div class="grid g-live" style="margin-top:16px">
      <section class="panel">
        <div class="panel-hd">
          <h3>SPLASH ACTIVITY</h3><span class="cn">摄食水花强度（V-Value）</span>
          <span class="tag">${esc(S.range)}</span>
          <span class="spacer"></span>
          ${['1h','6h','24h'].map(r=>`<button class="btn sm ${S.range===r?'on':''}" data-range="${r}">${r}</button>`).join('')}
        </div>
        <div class="panel-bd">
          <canvas id="chart-splash" style="width:100%;height:210px"></canvas>
          <div class="hint" style="margin-top:8px">
            橙色 = 实测运动强度；灰虚线 = 24 h 滑动基线；红虚线 = 告警阈值（${S.config?S.config.thresholds.splash_ratio:'1.6'}× 基线）。
            浅黄底纹 = 投喂时段。${evBadge('B')} 判据来自帧差/光流运动占比，对应方案二调研中的 V-Value 信号。
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="panel-hd"><h3>EVENT FEED</h3><span class="cn">最新事件</span>
          <span class="spacer"></span><span class="tag">${S.events.length}</span></div>
        <div class="panel-bd tight">${eventList(S.events.slice(0,7), S)}</div>
      </section>
    </div>

    <div class="grid g2" style="margin-top:16px">
      ${S.cameras.map(c=>camCard(c)).join('')}
    </div>

    <div class="grid g3" style="margin-top:16px">
      <section class="panel"><div class="panel-hd"><h3>EDGE</h3><span class="cn">边缘主机</span></div>
        <div class="panel-bd">
          ${kv('CPU', pi.cpu_pct+' %')}${kv('内存', pi.mem_pct+' %')}
          ${kv('SoC 温度', pi.temp_c+' ℃')}${kv('磁盘可用', pi.disk_free_gb+' GB')}
          ${kv('运行时长', fmtDur(h?h.uptime_s:null))}
          <div class="hint" style="margin-top:8px">树莓派 5 · 拉流 + 检测 + 本网页服务</div>
        </div></section>

      <section class="panel"><div class="panel-hd"><h3>LINK</h3><span class="cn">4G 链路</span></div>
        <div class="panel-bd">
          ${kv('信号强度', (net.rssi_dbm||'—')+' dBm')}${kv('运营商', net.carrier||'—')}
          ${kv('当前上行', (net.uplink_kbps||0)+' kbps')}${kv('本月用量', fmtBytes(net.month_bytes))}
          <div class="bar" style="margin-top:8px"><i class="${quotaPct>80?'bad':'ok'}" style="width:${Math.min(100,quotaPct).toFixed(1)}%"></i></div>
          <div class="hint" style="margin-top:6px">上行仅几 Mbps：<b>本地录全码流，远端只看缩略图与事件</b>。</div>
        </div></section>

      <section class="panel"><div class="panel-hd"><h3>STORAGE</h3><span class="cn">本地录像</span></div>
        <div class="panel-bd">
          ${kv('录像状态', stor.recording?'<span style="color:var(--green)">进行中</span>':'已停止')}
          ${kv('保留天数', (stor.days_kept||'—')+' 天')}
          ${kv('日均占用', fmtBytes(stor.bytes_per_day))}
          ${kv('双机位码率', S.cameras.reduce((a,c)=>a+(c.bitrate_kbps||0),0)+' kbps')}
          <div class="hint" style="margin-top:8px">绕开厂商云：录像在本机，导出不受 5 分钟限制。</div>
        </div></section>
    </div>`;
  }

  const kpi = (k,u,s,cls)=>`
    <div class="kpi ${cls||''}">
      <div class="k">${esc(k)}</div>
      <div class="v">${esc(u)}<span class="u">${esc(s||'')}</span></div>
      <div class="s">&nbsp;</div>
    </div>`;

  const kv = (k,v)=>`<div class="kv"><span class="k">${esc(k)}</span><span class="v">${v}</span></div>`;

  function camCard(c){
    return `
    <section class="panel">
      <div class="panel-hd">
        <span class="led ${c.online?'':'off'}"></span>
        <h3>${c.role==='panorama'?'PANORAMA':'DETAIL'}</h3>
        <span class="cn">${esc(c.name)}</span>
        <span class="spacer"></span>
        <span class="tag">${esc(c.model)}</span>
      </div>
      <div class="panel-bd">
        <div style="display:flex;gap:12px;align-items:flex-start">
          <div class="chan-thumb" style="width:132px;height:74px"><canvas data-thumb="${esc(c.id)}" data-role="${esc(c.role)}"></canvas></div>
          <div style="flex:1;min-width:0">
            ${kv('分辨率', `${esc(c.resolution)} @ ${c.fps} fps`)}
            ${kv('码率', (c.bitrate_kbps/1024).toFixed(1)+' Mbps')}
            ${kv('镜头', esc(c.lens))}
            ${kv('夜视', '红外 '+c.ir_m+' m')}
          </div>
        </div>
        <div class="hint" style="margin-top:8px">${esc(c.cover)}</div>
        <div style="display:flex;gap:8px;margin-top:10px">
          <button class="btn sm" data-goto="live" data-cam="${esc(c.id)}">看实时</button>
          <button class="btn sm ghost" data-goto="playback" data-cam="${esc(c.id)}">回看抓图</button>
        </div>
      </div>
    </section>`;
  }

  /* ==========================================================================
     视图 02 · 实时画面
     ========================================================================== */
  function live(S){
    const cams = S.cameras;
    const cur = cams.find(c=>c.id===S.camId) || cams[0] || {};
    const night = Feed.isNight(), feed = Feed.isFeedTime();
    const ptz = cur.ptz;

    return `
    <div class="grid g-live">
      <div>
        <div class="vidstage" id="stage">
          <canvas id="feed"></canvas>
          <div class="osd">
            <div class="tl">
              <div class="tagline">● LIVE</div>
              <div>${esc(cur.name||'—')}</div>
            </div>
            <div class="tr">
              <div>${esc(cur.resolution||'—')} · ${cur.fps||'—'}fps</div>
              <div>${((cur.bitrate_kbps||0)/1024).toFixed(1)} Mbps · H.265</div>
            </div>
            <div class="bl">${night?'IR 850nm · 红外开启':'自然光 · 宽动态 ON'}</div>
            <div class="br" id="osd-clock">${fmtTime(Date.now()/1000)}<br>${esc(cur.model||'')}</div>
          </div>
        </div>
        <div class="vidbar">
          <button class="btn sm" data-act="snap">⧉ 抓图</button>
          <button class="btn sm" data-act="clip">● 录像 60s</button>
          <button class="btn sm ghost" data-act="full">⤢ 全屏</button>
          <span class="spacer"></span>
          <span class="chip">${feed?'<i class="rec"></i> 投喂窗口内':'非投喂时段'}</span>
          <span class="chip">${night?'夜视':'日间'}</span>
        </div>

        <section class="panel" style="margin-top:16px">
          <div class="panel-hd"><h3>CHANNELS</h3><span class="cn">通道切换</span>
            <span class="spacer"></span><span class="tag">${cams.filter(c=>c.online).length}/${cams.length} ONLINE</span></div>
          <div class="panel-bd" style="display:grid;gap:8px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr))">
            ${cams.map(c=>`
              <div class="chan-item ${c.id===S.camId?'on':''}" data-cam="${esc(c.id)}">
                <div class="chan-thumb"><canvas data-thumb="${esc(c.id)}" data-role="${esc(c.role)}" data-q="low"></canvas></div>
                <div class="chan-meta">
                  <div class="nm"><span class="led ${c.online?'':'off'}"></span> ${esc(c.name)}</div>
                  <div class="sub">${esc(c.model)} · ${esc(c.resolution)}</div>
                </div>
              </div>`).join('')}
          </div>
        </section>
      </div>

      <div>
        <section class="panel">
          <div class="panel-hd"><h3>PTZ</h3><span class="cn">云台</span>
            <span class="spacer"></span><span class="tag" id="ptz-tag">${ptz?`P ${ptz.pan.toFixed(1)}° T ${ptz.tilt.toFixed(1)}° Z ${ptz.zoom.toFixed(1)}×`:'本机无云台'}</span></div>
          <div class="panel-bd">
            ${ptz?`
            <div style="display:flex;gap:14px;align-items:flex-start;flex-wrap:wrap">
              <div class="pad" id="pad">
                <button data-mv="-1,-1">↖</button><button data-mv="0,-1">↑</button><button data-mv="1,-1">↗</button>
                <button data-mv="-1,0">←</button><button class="hub">PTZ</button><button data-mv="1,0">→</button>
                <button data-mv="-1,1">↙</button><button data-mv="0,1">↓</button><button data-mv="1,1">↘</button>
              </div>
              <div style="flex:1;min-width:160px">
                <div class="zoomrow"><span class="mono dim" style="font-size:11px">ZOOM</span>
                  <input type="range" id="zoom" min="1" max="${ptz.zoom_max}" step="0.5" value="${ptz.zoom}">
                  <span class="mono" id="zoomv">${ptz.zoom.toFixed(1)}×</span></div>
                <div style="display:flex;gap:6px;margin-top:10px;flex-wrap:wrap">
                  <button class="btn sm" data-ptz="home">回中位</button>
                  <button class="btn sm ghost" data-ptz="patrol">巡航 ${S.config&&S.config.patrol.on?'开':'关'}</button>
                </div>
                <div class="hint" style="margin-top:10px">
                  ⚠️ 球机视场最窄约 3°，<b>天生不是全景</b>：靠预置位巡航覆盖全塘。
                </div>
              </div>
            </div>`:`<div class="empty">全景位为定焦机，无云台</div>`}
          </div>
        </section>

        <section class="panel">
          <div class="panel-hd"><h3>PRESETS</h3><span class="cn">预置位</span></div>
          <div class="panel-bd">
            <div class="preset-grid">
              ${S.presets.map(p=>`
                <div class="preset ${ptz&&ptz.preset_id===p.id?'on':''}" data-preset="${p.id}">
                  <div class="n">P${p.id}</div><div class="t">${esc(p.name)}</div>
                  <div class="p">${p.pan.toFixed(0)}° / ${p.tilt.toFixed(0)}° / ${p.zoom.toFixed(1)}×</div>
                </div>`).join('')||'<div class="empty">无预置位</div>'}
            </div>
          </div>
        </section>

        <section class="panel">
          <div class="panel-hd"><h3>LIVE EVENTS</h3><span class="cn">实时事件</span>
            <span class="spacer"></span><span class="tag" id="live-count">${S.events.length}</span></div>
          <div class="panel-bd tight"><div class="evlist" id="live-evlist">${eventList(S.events.slice(0,12), S)}</div></div>
        </section>
      </div>
    </div>`;
  }

  /* ==========================================================================
     视图 03 · 事件中心
     ========================================================================== */
  function events(S){
    const list = S.evType ? S.events.filter(e=>e.type===S.evType) : S.events;
    const sel = S.selectedEvent ? list.find(e=>e.id===S.selectedEvent) || S.events.find(e=>e.id===S.selectedEvent) : null;
    const types = Object.keys(Data.EVENT_TYPES);
    return `
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
      <button class="btn sm ${S.evType===''?'on':''}" data-evtype="">全部 <span class="mono">${S.events.length}</span></button>
      ${types.map(t=>{
        const n=S.events.filter(e=>e.type===t).length;
        return `<button class="btn sm ${S.evType===t?'on':''}" data-evtype="${t}">${esc(typeLabel(t))} <span class="mono">${n}</span></button>`;
      }).join('')}
      <span class="spacer"></span>
      <span class="hint">事件均带证据等级与置信度；<b>C 级=演示/未标定</b>，不得当作生产依据。</span>
    </div>

    <div class="grid g-live" style="margin-top:14px">
      <section class="panel">
        <div class="panel-hd"><h3>EVENT LOG</h3><span class="cn">事件列表</span>
          <span class="spacer"></span><span class="tag">${list.length} 条</span></div>
        <div class="panel-bd tight">
          ${list.length?`<table class="tbl">
            <thead><tr><th>时间</th><th>类型</th><th>相机</th><th>摘要</th><th>置信度</th><th>状态</th><th></th></tr></thead>
            <tbody>${list.slice(0,60).map(e=>`
              <tr data-ev="${esc(e.id)}" style="cursor:pointer">
                <td class="num">${fmtHM(e.ts)}</td>
                <td><span class="sev ${sevClass(e.severity)}" style="display:inline-block;width:6px;height:6px;border-radius:50%;margin-right:6px"></span>${esc(typeLabel(e.type))}</td>
                <td class="mono" style="font-size:11.5px">${esc((S.cameras.find(c=>c.id===e.camera_id)||{}).name||e.camera_id)}</td>
                <td>${esc(e.title)}</td>
                <td class="num">${(e.confidence*100).toFixed(0)}%</td>
                <td>${e.acked?'<span class="pill">已确认</span>':'<span class="pill new">待确认</span>'}</td>
                <td>${evBadge(e.evidence)}</td>
              </tr>`).join('')}</tbody></table>`:'<div class="empty">当前筛选下没有事件</div>'}
        </div>
      </section>

      <section class="panel">
        <div class="panel-hd"><h3>DETAIL</h3><span class="cn">事件详情</span></div>
        <div class="panel-bd">
          ${sel?eventDetail(sel,S):'<div class="empty">← 选择左侧一条事件</div>'}
        </div>
      </section>
    </div>`;
  }

  function eventDetail(e,S){
    const cam = S.cameras.find(c=>c.id===e.camera_id)||{};
    const dict = Data.EVENT_TYPES[e.type]||{};
    return `
      <div style="display:flex;gap:8px;align-items:center;margin-bottom:10px">
        <span class="sev ${sevClass(e.severity)}" style="width:4px;height:26px;border-radius:2px;display:inline-block"></span>
        <div><div style="font-weight:700;font-size:15px">${esc(e.title)}</div>
        <div class="mono dim" style="font-size:11.5px">${fmtDate(e.ts)} ${fmtTime(e.ts)} · ${esc(cam.name||e.camera_id)}</div></div>
      </div>
      <div style="aspect-ratio:16/9;border:1px solid var(--line);border-radius:2px;overflow:hidden;background:#000">
        <canvas id="ev-shot" data-ts="${e.ts}" data-type="${esc(e.type)}" style="width:100%;height:100%;display:block"></canvas>
      </div>
      <div style="margin-top:12px">
        ${kv('类型', esc(typeLabel(e.type)))}
        ${kv('严重度', esc(SEV[e.severity]||e.severity))}
        ${kv('置信度', (e.confidence*100).toFixed(0)+' %')}
        ${e.metric&&e.metric.ratio!=null?kv('V-Value 比值', e.metric.ratio+' ×（基线 '+e.metric.baseline+'）'):''}
        ${e.metric&&e.metric.duration_s!=null?kv('持续时长', fmtDur(e.metric.duration_s)):''}
        ${e.metric&&e.metric.area_pct!=null?kv('暗斑面积占比', e.metric.area_pct+' %'):''}
        ${kv('证据等级', evBadge(e.evidence)+' '+esc(dict.note||''))}
      </div>
      <div style="display:flex;gap:8px;margin-top:12px">
        <button class="btn sm primary" data-ack="${esc(e.id)}" ${e.acked?'disabled':''}>${e.acked?'已确认':'确认收到'}</button>
        <button class="btn sm ghost" data-goto="playback">去回看</button>
      </div>
      <div class="hint" style="margin-top:10px">${esc(e.detail||'')}</div>`;
  }

  function eventList(evs,S){
    if(!evs.length) return '<div class="empty">暂无事件</div>';
    return `<div class="evlist">${evs.map(e=>`
      <div class="evrow ${S.selectedEvent===e.id?'sel':''}" data-ev="${esc(e.id)}">
        <span class="sev ${sevClass(e.severity)}"></span>
        <div class="body">
          <div class="t1"><span class="ti">${esc(e.title)}</span><span class="ts">${fmtHM(e.ts)}</span></div>
          <div class="t2">${esc(e.detail||typeLabel(e.type))}</div>
          <div class="t3">
            <span class="pill">${esc(typeLabel(e.type))}</span>
            <span class="pill">置信 ${(e.confidence*100).toFixed(0)}%</span>
            ${e.acked?'':'<span class="pill new">待确认</span>'}
            ${evBadge(e.evidence)}
          </div>
        </div>
      </div>`).join('')}</div>`;
  }

  /* ==========================================================================
     视图 04 · 回看
     ========================================================================== */
  function playback(S){
    const snaps = S.snapshots;
    const evs = S.events.filter(e=>fmtDate(e.ts)===S.date);
    return `
    <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end">
      <div class="field" style="max-width:190px"><label>日期</label>
        <input class="input" type="date" id="pb-date" value="${esc(S.date)}"></div>
      <div class="field" style="max-width:190px"><label>相机</label>
        <select class="select" id="pb-cam">
          ${S.cameras.map(c=>`<option value="${esc(c.id)}" ${c.id===S.camId?'selected':''}>${esc(c.name)}</option>`).join('')}
        </select></div>
      <button class="btn primary" data-act="pb-load">载入</button>
      <span class="spacer"></span>
      <span class="hint">本地 SD/NVR 存全码流；4G 只回传缩略图 —— 导出一段完整录像不受任何云限制。</span>
    </div>

    <div class="grid g-live" style="margin-top:14px">
      <section class="panel">
        <div class="panel-hd"><h3>SNAPSHOT WALL</h3><span class="cn">定时抓图</span>
          <span class="spacer"></span><span class="tag">每 ${S.config?S.config.capture.interval_s:60} s</span>
          <span class="tag">${snaps.length} 张</span></div>
        <div class="panel-bd">
          ${snaps.length?`<div class="wall">${snaps.slice(0,48).map(s=>`
            <figure data-snap="${s.ts}">
              <canvas data-tile="${s.ts}" data-trigger="${esc(s.trigger)}"></canvas>
              <figcaption><span>${fmtHM(s.ts)}</span><span>${s.trigger==='event'?'事件':(s.trigger==='manual'?'手动':'定时')}</span></figcaption>
            </figure>`).join('')}</div>`:'<div class="empty">该日无抓图</div>'}
        </div>
      </section>

      <section class="panel">
        <div class="panel-hd"><h3>ON THIS DAY</h3><span class="cn">当日事件</span>
          <span class="spacer"></span><span class="tag">${evs.length}</span></div>
        <div class="panel-bd tight">${eventList(evs,S)}</div>
      </section>
    </div>`;
  }

  /* ==========================================================================
     视图 05 · 巡航
     ========================================================================== */
  function ptz(S){
    const cfg = S.config||{}, pat = cfg.patrol||{on:false,preset_ids:[],dwell_s:30};
    const cam = S.cameras.find(c=>c.id==='cam-detail')||{};
    return `
    <div class="notice">
      <b>为什么球机需要巡航</b>：23 倍变焦后视场只剩约 3°（100 m 处画面宽不到 6 m），
      所以它<b>不是全景机</b>——靠"预置位 + 定时轮巡"覆盖全塘。全景位由另一台定焦机负责。
    </div>

    <div class="grid g2" style="margin-top:16px">
      <section class="panel">
        <div class="panel-hd"><h3>PATROL PLAN</h3><span class="cn">巡航计划</span>
          <span class="spacer"></span>
          <label class="switch"><input type="checkbox" id="patrol-on" ${pat.on?'checked':''}> 启用</label></div>
        <div class="panel-bd">
          <table class="tbl">
            <thead><tr><th>顺序</th><th>预置位</th><th>角度</th><th>停留</th><th>操作</th></tr></thead>
            <tbody>${(pat.preset_ids||[]).map((id,i)=>{
              const p = S.presets.find(p=>p.id===id); if(!p) return '';
              return `<tr><td class="num">${i+1}</td><td>${esc(p.name)}</td>
                <td class="num">${p.pan.toFixed(0)}° / ${p.tilt.toFixed(0)}° / ${p.zoom.toFixed(1)}×</td>
                <td class="num">${pat.dwell_s} s</td>
                <td><button class="btn sm ghost" data-ptz="goto" data-preset="${p.id}">转过去</button></td></tr>`;
            }).join('')||'<tr><td colspan="5" class="empty">未配置巡航点</td></tr>'}</tbody>
          </table>
          <div style="display:flex;gap:10px;margin-top:12px;align-items:flex-end;flex-wrap:wrap">
            <div class="field" style="max-width:150px"><label>停留（秒）</label>
              <input class="input" id="dwell" type="number" min="5" max="600" value="${pat.dwell_s}"></div>
            <button class="btn primary" data-act="patrol-save">保存巡航</button>
            <span class="hint">整轮一圈 ≈ ${((pat.preset_ids||[]).length*((pat.dwell_s||30)+6))} s</span>
          </div>
        </div>
      </section>

      <section class="panel">
        <div class="panel-hd"><h3>PRESET MANAGER</h3><span class="cn">预置位</span>
          <span class="spacer"></span><span class="tag">${esc(cam.model||'')}</span></div>
        <div class="panel-bd">
          <table class="tbl">
            <thead><tr><th>ID</th><th>名称</th><th>PAN</th><th>TILT</th><th>ZOOM</th><th></th></tr></thead>
            <tbody>${S.presets.map(p=>`<tr>
              <td class="num">P${p.id}</td><td>${esc(p.name)}</td>
              <td class="num">${p.pan.toFixed(0)}°</td><td class="num">${p.tilt.toFixed(0)}°</td><td class="num">${p.zoom.toFixed(1)}×</td>
              <td><button class="btn sm ghost" data-ptz="goto" data-preset="${p.id}">调用</button></td>
            </tr>`).join('')}</tbody>
          </table>
          <div style="display:flex;gap:10px;margin-top:12px;align-items:flex-end;flex-wrap:wrap">
            <div class="field" style="max-width:120px"><label>存到 ID</label>
              <input class="input" id="save-id" type="number" min="1" max="8" value="4"></div>
            <div class="field" style="flex:1;min-width:140px"><label>名称</label>
              <input class="input" id="save-name" placeholder="如：对岸东南角"></div>
            <button class="btn" data-act="preset-save">把当前角度存为预置位</button>
          </div>
        </div>
      </section>
    </div>

    <section class="panel">
      <div class="panel-hd"><h3>WHY IT MATTERS</h3><span class="cn">覆盖逻辑</span></div>
      <div class="panel-bd">
        <div class="grid g3">
          <div>${kv('全景位覆盖','约 84° 视场 / 100 m 处 180 m 宽')}${kv('细节位最广','60.2°（1× 时）')}</div>
          <div>${kv('细节位最窄','3.4°（23× 时）')}${kv('100 m 处最窄画面宽','约 6 m')}</div>
          <div>${kv('巡航一圈','约 '+(S.presets.length*36)+' s')}${kv('建议轮巡','投喂时段改为 15 s 停留')}</div>
        </div>
      </div>
    </section>`;
  }

  /* ==========================================================================
     视图 06 · 设备与网络
     ========================================================================== */
  function devices(S){
    const h=S.health||{}, net=h.net||{}, pi=h.pi||{}, st=h.storage||{};
    return `
    <div class="grid g4">
      ${kpi('边缘主机', (pi.cpu_pct||0).toFixed(0), '% CPU', `内存 ${(pi.mem_pct||0).toFixed(0)}% · ${(pi.temp_c||0).toFixed(0)}℃`, (pi.temp_c>70?'bad':'ok'))}
      ${kpi('4G 信号', net.rssi_dbm||'—', 'dBm', net.carrier||'', (net.rssi_dbm<-85?'warn':'ok'))}
      ${kpi('磁盘可用', (pi.disk_free_gb||0).toFixed(1), 'GB', `保留 ${st.days_kept||'—'} 天`, 'info')}
      ${kpi('服务', (h.services||[]).filter(s=>s.ok).length+'/'+((h.services||[]).length), '', '拉流 · 检测 · 云台 · 上传', 'ok')}
    </div>

    <section class="panel" style="margin-top:16px">
      <div class="panel-hd"><h3>CAMERAS</h3><span class="cn">相机</span></div>
      <div class="panel-bd tight">
        <table class="tbl">
          <thead><tr><th>通道</th><th>型号</th><th>IP</th><th>RTSP</th><th>ONVIF</th><th>分辨率</th><th>码率</th><th>红外</th><th>状态</th></tr></thead>
          <tbody>${S.cameras.map(c=>`<tr>
            <td>${esc(c.name)}</td><td class="mono" style="font-size:11.5px">${esc(c.model)}</td>
            <td class="mono">${esc(c.ip)}</td>
            <td><span class="pill">${c.rtsp.includes('rtsp')?'已配置':'—'}</span></td>
            <td>${c.onvif?'<span class="pill">是</span>':'<span class="pill">否</span>'}</td>
            <td class="mono">${esc(c.resolution)}@${c.fps}</td>
            <td class="num">${(c.bitrate_kbps/1024).toFixed(1)} Mbps</td>
            <td class="num">${c.ir_m} m</td>
            <td><span class="led ${c.online?'':'bad'}"></span> ${c.online?'在线':'离线'}</td>
          </tr>`).join('')}</tbody>
        </table>
      </div>
    </section>

    <div class="grid g2" style="margin-top:16px">
      <section class="panel"><div class="panel-hd"><h3>SERVICES</h3><span class="cn">服务健康</span></div>
        <div class="panel-bd">
          ${(h.services||[]).map(s=>`<div class="kv"><span class="k"><span class="led ${s.ok?'':'bad'}"></span> ${esc(s.name)}</span>
            <span class="v">${s.ok?'<span style="color:var(--green)">RUNNING</span>':'<span style="color:var(--red)">DOWN</span>'}</span></div>`).join('')}
          <div class="hint" style="margin-top:8px">全部由 systemd 托管，掉线自动重启（见固件包 <span class="mono">yutang-vision.service</span>）。</div>
        </div></section>

      <section class="panel"><div class="panel-hd"><h3>BANDWIDTH</h3><span class="cn">带宽策略</span></div>
        <div class="panel-bd">
          ${kv('本地录像','全码流 · 双机位 '+(S.cameras.reduce((a,c)=>a+c.bitrate_kbps,0)/1024).toFixed(1)+' Mbps')}
          ${kv('上行预算', (S.config?S.config.upload.max_kbps:512)+' kbps')}
          ${kv('上传策略', S.config?S.config.upload.policy:'thumbs_only')}
          ${kv('当前上行', (net.uplink_kbps||0)+' kbps')}
          <div class="hint" style="margin-top:8px">4G 上行不够看 4K 主码流：<b>远端只看缩略图 + 事件 + 按需单帧</b>。</div>
        </div></section>
    </div>

    <section class="panel" style="margin-top:16px">
      <div class="panel-hd"><h3>LOG</h3><span class="cn">运行日志</span>
        <span class="spacer"></span><button class="btn sm ghost" data-act="log-refresh">刷新</button></div>
      <div class="panel-bd tight">
        <table class="tbl"><thead><tr><th>时间</th><th>级别</th><th>来源</th><th>消息</th></tr></thead>
        <tbody>${S.logs.slice(0,40).map(l=>`<tr>
          <td class="num">${fmtTime(l.ts)}</td>
          <td><span class="pill" style="${l.level==='error'?'border-color:var(--red);color:var(--red)':(l.level==='warn'?'border-color:var(--amber);color:var(--amber)':'')}">${esc(l.level)}</span></td>
          <td class="mono" style="font-size:11.5px">${esc(l.src)}</td><td>${esc(l.msg)}</td></tr>`).join('')}</tbody></table>
      </div>
    </section>`;
  }

  /* ==========================================================================
     视图 07 · 设置
     ========================================================================== */
  function settings(S){
    const c = S.config||{thresholds:{},capture:{},upload:{},record:{},patrol:{}};
    const fw = (c.feed_windows||[]).map(w=>`${w.start}-${w.end}`).join(', ');
    return `
    <div class="notice">
      改动会通过 <span class="mono">PUT /api/v1/config</span> 落到树莓派上的 config.yaml 并热生效。
      <b>阈值未标定前不要调低</b>——宁可漏报，不要天天误报。
    </div>

    <div class="grid g2" style="margin-top:16px">
      <section class="panel"><div class="panel-hd"><h3>DETECTION</h3><span class="cn">检测阈值</span></div>
        <div class="panel-bd">
          <div class="field" style="margin-bottom:12px"><label>水花强度比值阈值（× 基线）</label>
            <input class="input" id="cfg-splash" type="number" step="0.1" min="1" value="${c.thresholds.splash_ratio}">
            <span class="hint">默认 1.6。低于 1.3 会把风浪误判成抢食。</span></div>
          <div class="field" style="margin-bottom:12px"><label>暗斑面积占比阈值（%）</label>
            <input class="input" id="cfg-area" type="number" step="0.5" min="0.5" value="${c.thresholds.aggregation_area_pct}">
            <span class="hint">浮头/聚集的粗代理，C 级证据，需现场标定。</span></div>
          <div class="field"><label>人形置信度阈值</label>
            <input class="input" id="cfg-person" type="number" step="0.05" min="0.3" max="0.95" value="${c.thresholds.person_confidence}"></div>
        </div></section>

      <section class="panel"><div class="panel-hd"><h3>CAPTURE</h3><span class="cn">抓图与上传</span></div>
        <div class="panel-bd">
          <div class="field" style="margin-bottom:12px"><label>定时抓图间隔（秒）</label>
            <input class="input" id="cfg-interval" type="number" min="10" max="3600" value="${c.capture.interval_s}"></div>
          <div class="field" style="margin-bottom:12px"><label>抓图长边（像素）</label>
            <input class="input" id="cfg-width" type="number" min="640" max="3840" value="${c.capture.max_width}"></div>
          <div class="field" style="margin-bottom:12px"><label>上传策略</label>
            <select class="select" id="cfg-policy">
              <option value="thumbs_only" ${c.upload.policy==='thumbs_only'?'selected':''}>仅缩略图 + 事件（4G 推荐）</option>
              <option value="events_only" ${c.upload.policy==='events_only'?'selected':''}>仅事件抓图</option>
              <option value="full" ${c.upload.policy==='full'?'selected':''}>全量（需大流量套餐）</option>
            </select></div>
          <div class="field"><label>上行带宽上限（kbps）</label>
            <input class="input" id="cfg-kbps" type="number" min="64" max="8192" value="${c.upload.max_kbps}"></div>
        </div></section>

      <section class="panel"><div class="panel-hd"><h3>SCHEDULE</h3><span class="cn">投喂时段</span></div>
        <div class="panel-bd">
          <div class="field" style="margin-bottom:12px"><label>时段（逗号分隔，HH:MM-HH:MM）</label>
            <input class="input" id="cfg-feed" value="${esc(fw)}">
            <span class="hint">投喂时段内水花阈值自动放宽、抓图加密、巡航停留缩短。</span></div>
          <div class="field"><label>本地录像保留（天）</label>
            <input class="input" id="cfg-keep" type="number" min="1" max="90" value="${c.record.keep_days}"></div>
        </div></section>

      <section class="panel"><div class="panel-hd"><h3>CONNECTION</h3><span class="cn">连接与模式</span></div>
        <div class="panel-bd">
          <div class="field" style="margin-bottom:12px"><label>固件服务地址（树莓派）</label>
            <input class="input" id="cfg-base" value="${esc(API.base)}" placeholder="http://192.168.1.50:8080"></div>
          <div style="display:flex;gap:8px;align-items:center;margin-bottom:12px">
            <span class="hint">当前模式：</span>
            <span class="chip">${API.mode==='live'?'LIVE · 真机':'MOCK · 演示数据'}</span>
            <button class="btn sm" data-act="mode-toggle">切到 ${API.mode==='live'?'MOCK':'LIVE'}</button>
          </div>
          <div class="hint">切到 LIVE 前，先在树莓派上跑起固件（见"接入说明"页），并确认浏览器能访问该地址。</div>
        </div></section>
    </div>

    <div style="display:flex;gap:10px;margin-top:16px;align-items:center">
      <button class="btn primary" data-act="cfg-save">保存全部设置</button>
      <button class="btn ghost" data-act="cfg-reload">放弃改动</button>
      <span class="hint" id="cfg-msg"></span>
    </div>`;
  }

  /* ==========================================================================
     视图 08 · 接入说明
     ========================================================================== */
  function integration(S){
    const cam = S.cameras[0]||{};
    return `
    <div class="grid g2">
      <section class="panel">
        <div class="panel-hd"><h3>RTSP</h3><span class="cn">取流地址</span></div>
        <div class="panel-bd">
          <div class="hint" style="margin-bottom:8px">海康通用格式（主码流 / 子码流）：</div>
          <pre class="mono" style="background:#0D1014;border:1px solid var(--line);padding:10px;border-radius:2px;overflow:auto;font-size:12px">rtsp://admin:密码@192.168.1.64:554/Streaming/Channels/101   # 主码流
rtsp://admin:密码@192.168.1.64:554/Streaming/Channels/102   # 子码流（4G 推荐）</pre>
          <div class="hint" style="margin-top:10px">本机验证：</div>
          <pre class="mono" style="background:#0D1014;border:1px solid var(--line);padding:10px;border-radius:2px;overflow:auto;font-size:12px">ffplay -rtsp_transport tcp "rtsp://..."
ffmpeg -rtsp_transport tcp -i "rtsp://..." -frames:v 1 snap.jpg</pre>
        </div></section>

      <section class="panel">
        <div class="panel-hd"><h3>ONVIF</h3><span class="cn">云台控制</span></div>
        <div class="panel-bd">
          <div class="hint" style="margin-bottom:8px">发现设备 + 转到预置位（树莓派上）：</div>
          <pre class="mono" style="background:#0D1014;border:1px solid var(--line);padding:10px;border-radius:2px;overflow:auto;font-size:12px">pip install onvif-zeep
python3 - <<'PY'
from onvif import ONVIFCamera
cam = ONVIFCamera('192.168.1.65', 80, 'admin', '密码')
ptz = cam.create_ptz_service()
cam.create_media_service()          # 必须先建 media，否则有些固件报错
ptz.GotoPreset({'ProfileToken':'Profile_1','PresetToken':'1'})
PY</pre>
          <div class="hint" style="margin-top:10px">海康中文规格表写「<b>开放型网络视频接口</b>」= ONVIF，别因为没有 ONVIF 字样就判它不合格。</div>
        </div></section>
    </div>

    <section class="panel" style="margin-top:16px">
      <div class="panel-hd"><h3>FIRMWARE</h3><span class="cn">固件部署（树莓派 5）</span></div>
      <div class="panel-bd">
        <pre class="mono" style="background:#0D1014;border:1px solid var(--line);padding:12px;border-radius:2px;overflow:auto;font-size:12px"># 1. 拷到树莓派
scp -r yutang-vision-firmware pi@192.168.1.50:~/

# 2. 一键安装（建 venv、装依赖、注册 systemd、开机自启）
cd ~/yutang-vision-firmware && sudo ./install.sh

# 3. 自检（无相机也能跑，先看契约是否满足）
python3 tools/selfcheck.py --simulate

# 4. 状态与日志
systemctl status yutang-vision
journalctl -u yutang-vision -f

# 5. 打开本网页
#    http://192.168.1.50:8080        （把"设置"页的模式切到 LIVE）</pre>
        <div class="hint" style="margin-top:10px">
          固件实现本页用到的全部端点：<span class="mono">/health /cameras /presets /ptz /events /metrics/splash /snapshots /config /logs /stream/events</span>
        </div>
      </div>
    </section>

    <div class="grid g2" style="margin-top:16px">
      <section class="panel"><div class="panel-hd"><h3>API</h3><span class="cn">端点一览</span></div>
        <div class="panel-bd tight">
          <table class="tbl"><thead><tr><th>方法</th><th>路径</th><th>说明</th></tr></thead><tbody>
            ${[['GET','/api/v1/health','主机 / 4G / 存储 / 服务健康'],
               ['GET','/api/v1/cameras','相机列表与状态'],
               ['POST','/api/v1/cameras/{id}/ptz','云台移动 / 预置位 / 巡航'],
               ['GET','/api/v1/presets','预置位列表'],
               ['GET','/api/v1/events','事件查询（since/type/limit）'],
               ['POST','/api/v1/events/{id}/ack','确认事件'],
               ['GET','/api/v1/metrics/splash','V-Value 曲线'],
               ['GET','/api/v1/snapshots','抓图索引'],
               ['GET','/api/v1/config','读取配置'],
               ['PUT','/api/v1/config','写入配置'],
               ['GET','/api/v1/logs','运行日志'],
               ['GET','/api/v1/stream/events','SSE 实时事件']]
              .map(r=>`<tr><td class="mono">${r[0]}</td><td class="mono" style="font-size:11.5px">${esc(r[1])}</td><td>${esc(r[2])}</td></tr>`).join('')}
          </tbody></table>
        </div></section>

      <section class="panel"><div class="panel-hd"><h3>LIMITS</h3><span class="cn">系统不做什么</span></div>
        <div class="panel-bd">
          <div class="notice red" style="margin-bottom:10px"><b>四项明确不做</b>（本项目调研已给出几何与实测否决）</div>
          <table class="tbl"><tbody>
            <tr><td>数鱼 / 逐尾计数</td><td class="dim">纯光学土塘公开最好成绩 mAP 38.93%</td></tr>
            <tr><td>数饲料颗粒</td><td class="dim">3 mm 颗粒在 5 m 高度只占 0.6 像素</td></tr>
            <tr><td>估重 / 生物量反演</td><td class="dim">正反馈发散，需实测锚点</td></tr>
            <tr><td>水下观察</td><td class="dim">30 NTU 浑水有效视距约 10 cm</td></tr>
          </tbody></table>
          <div class="hint" style="margin-top:10px">
            能做的四件事：<b>摄食水花强度趋势</b>、<b>水面聚集/浮头</b>、<b>人形入侵</b>、<b>设备与画面异常</b>。
          </div>
        </div></section>
    </div>`;
  }

  const VIEWS = {overview, live, events, playback, ptz, devices, settings, integration};

  /* ==========================================================================
     渲染与交互（只在浏览器里跑）
     ========================================================================== */
  function renderRail(S){
    const rail = document.getElementById('rail');
    if(!rail) return;
    rail.innerHTML = PAGES.map(p=>{
      const badge = p.view==='events' ? Data.summarize(S.events).unacked : 0;
      return `<a href="#${p.view}" class="${S.route===p.view?'on':''}">
        <span class="code">${p.code}</span>
        <span class="txt">${p.path}</span>
        <span class="cn">${p.name}</span>
        ${badge?`<span class="badge">${badge}</span>`:''}
      </a>`;
    }).join('');
  }

  function renderCrumb(S){
    const p = PAGES.find(x=>x.view===S.route)||PAGES[0];
    const code=document.getElementById('crumb-code'), name=document.getElementById('crumb-name'),
          path=document.getElementById('crumb-path'), note=document.getElementById('crumb-note');
    if(code) code.textContent = p.code;
    if(name) name.textContent = p.name;
    if(path) path.textContent = p.path;
    if(note) note.textContent = NOTES[p.view]||'';
  }

  const NOTES = {
    overview:'外部网页端原型 · 数据为演示值（MOCK）',
    live:'合成画面用于展示"水花可见性"，非真实视频流',
    events:'每条事件都带证据等级与置信度',
    playback:'本地全码流 + 远端缩略图，规避云端导出限制',
    ptz:'球机靠巡航而非视场覆盖全塘',
    devices:'树莓派 / 4G / 存储 / 服务 一屏看全',
    settings:'阈值未标定前不要调低',
    integration:'RTSP · ONVIF · 固件部署 · 能力边界'
  };

  function renderAll(){
    const S = State;
    renderRail(S); renderCrumb(S);
    const v = document.getElementById('view');
    if(!v) return;
    v.innerHTML = (VIEWS[S.route]||overview)(S);
    afterRender(S);
  }

  function afterRender(S){
    // 通道缩略 / 主画面 / 抓图墙
    document.querySelectorAll('canvas[data-thumb]').forEach(cv=>{
      Feed.mount(cv, {role:cv.dataset.role, quality:cv.dataset.q||'low'});
    });
    const feedCv = document.getElementById('feed');
    if(feedCv){
      const cam = S.cameras.find(c=>c.id===S.camId);
      Feed.mount(feedCv, {role:cam?cam.role:'panorama', quality:'high'});
    }
    document.querySelectorAll('canvas[data-tile]').forEach(cv=>{
      const trigger=cv.dataset.trigger;
      Charts.tile(cv, +cv.dataset.tile, {splash:trigger==='event', ts:+cv.dataset.tile});
    });
    // 图表
    const sc = document.getElementById('chart-splash');
    if(sc && S.splash) Charts.splash(sc, S.splash, {height:210});
    // 事件详情里的合成抓图
    const es = document.getElementById('ev-shot');
    if(es) Charts.tile(es, +es.dataset.ts, {splash:es.dataset.type==='splash_activity',
                                           person:es.dataset.type==='person', ts:+es.dataset.ts});
    // 底部事件轴
    const strip = document.getElementById('strip-canvas');
    if(strip) Charts.timeline(strip, S.events);
    bindEvents(S);
  }

  function bindEvents(S){
    const q = (sel,fn)=>document.querySelectorAll(sel).forEach(fn);

    q('[data-range]', el=>el.onclick=async()=>{ State.range=el.dataset.range;
      State.splash = await API.splash({camera_id:State.camId,window:State.range,step:300}); renderAll(); });

    q('[data-goto]', el=>el.onclick=()=>{ if(el.dataset.cam){State.camId=el.dataset.cam} location.hash=el.dataset.goto; });

    q('[data-cam]', el=>el.onclick=()=>{ State.camId=el.dataset.cam; renderAll(); });

    q('[data-ev]', el=>el.onclick=()=>{ State.selectedEvent=el.dataset.ev; renderAll(); });

    q('[data-evtype]', el=>el.onclick=()=>{ State.evType=el.dataset.evtype; renderAll(); });

    q('[data-ack]', el=>el.onclick=async()=>{ await API.ack(el.dataset.ack);
      const e=State.events.find(x=>x.id===el.dataset.ack); if(e) e.acked=true;
      toast('已确认','事件已标记为处理完毕','info'); renderAll(); });

    q('[data-mv]', el=>el.onclick=async()=>{
      const [dx,dy]=el.dataset.mv.split(',').map(Number);
      const r = await API.ptz(State.camId,{action:'move',dx,dy,zoom:0});
      if(r.ok) syncPtz(r.ptz); renderAll();
    });

    q('[data-preset]', el=>el.onclick=async()=>{
      const r = await API.ptz(State.camId,{action:'goto',preset_id:+el.dataset.preset});
      if(r.ok){ syncPtz(r.ptz); toast('已转至预置位',`P${el.dataset.preset}`,'info'); } renderAll();
    });

    q('[data-ptz]', el=>el.onclick=async()=>{
      const a = el.dataset.ptz;
      if(a==='home'){ const r=await API.ptz(State.camId,{action:'home'}); if(r.ok) syncPtz(r.ptz); renderAll(); }
      else if(a==='goto'){ /* 由 data-preset 处理 */ }
      else if(a==='patrol'){ const c=await API.getConfig(); c.patrol.on=!c.patrol.on;
        await API.putConfig(c); State.config=c; toast('巡航',c.patrol.on?'已开启':'已关闭','info'); renderAll(); }
    });

    const zoom = document.getElementById('zoom');
    if(zoom) zoom.oninput = ()=>{ const zv=document.getElementById('zoomv');
      if(zv) zv.textContent = (+zoom.value).toFixed(1)+'×'; };
    if(zoom) zoom.onchange = async()=>{
      const cam=State.cameras.find(c=>c.id===State.camId); if(!cam||!cam.ptz) return;
      const dz = +zoom.value - cam.ptz.zoom;
      const r = await API.ptz(State.camId,{action:'move',dx:0,dy:0,zoom:dz/1.5});
      if(r.ok) syncPtz(r.ptz); renderAll();
    };

    const po=document.getElementById('patrol-on');
    if(po) po.onchange = async()=>{ const c=await API.getConfig(); c.patrol.on=po.checked;
      await API.putConfig(c); State.config=c; toast('巡航',po.checked?'已开启':'已关闭','info'); };

    q('[data-act]', el=>el.onclick=()=>act(el.dataset.act, S));

    const pd=document.getElementById('pb-date'); if(pd) pd.onchange=()=>{ State.date=pd.value; loadPlayback(); };
    const pc=document.getElementById('pb-cam');  if(pc) pc.onchange=()=>{ State.camId=pc.value; loadPlayback(); };

    const zz=document.getElementById('cfg-base'); if(zz) zz.onchange=()=>API.setBase(zz.value);
    q('input[type=range]', el=>{ /* already handled */ });
  }

  function syncPtz(p){ const c=State.cameras.find(x=>x.id===State.camId); if(c&&p) c.ptz=p; }

  async function act(a, S){
    if(a==='snap'){ toast('已抓图','存到树莓派本地，4G 只回传缩略图','info'); }
    else if(a==='clip'){ toast('开始录像','录制 60 s 到本地存储','info'); }
    else if(a==='full'){ const el=document.getElementById('stage'); if(el&&el.requestFullscreen) el.requestFullscreen(); }
    else if(a==='pb-load'){ loadPlayback(); }
    else if(a==='log-refresh'){ State.logs = await API.logs({limit:60}); renderAll(); }
    else if(a==='preset-save'){
      const id=+((document.getElementById('save-id')||{}).value||4);
      const nm=((document.getElementById('save-name')||{}).value||'').trim()||`预置位 ${id}`;
      const r=await API.ptz(State.camId,{action:'save',preset_id:id,name:nm});
      if(r.ok){ State.presets=await API.presets('cam-detail'); toast('已保存',`P${id} ${nm}`,'info'); renderAll(); }
    }
    else if(a==='patrol-save'){
      const dwell=+((document.getElementById('dwell')||{}).value||30);
      const c=await API.getConfig(); c.patrol.dwell_s=dwell; await API.putConfig(c); State.config=c;
      toast('巡航已保存',`停留 ${dwell} s`,'info'); renderAll();
    }
    else if(a==='cfg-save'){
      const gw = ((document.getElementById('cfg-feed')||{}).value||'').split(',').map(s=>s.trim()).filter(Boolean)
        .map(s=>{const [a1,b1]=s.split('-'); return {start:(a1||'').trim(),end:(b1||'').trim()};})
        .filter(w=>/^\d{1,2}:\d{2}$/.test(w.start)&&/^\d{1,2}:\d{2}$/.test(w.end));
      const cfg = {
        feed_windows: gw.length?gw:State.config.feed_windows,
        thresholds:{ splash_ratio:+document.getElementById('cfg-splash').value,
                     aggregation_area_pct:+document.getElementById('cfg-area').value,
                     person_confidence:+document.getElementById('cfg-person').value },
        capture:{ interval_s:+document.getElementById('cfg-interval').value,
                  on_event:true, jpeg_quality:85, max_width:+document.getElementById('cfg-width').value },
        upload:{ policy:document.getElementById('cfg-policy').value, max_kbps:+document.getElementById('cfg-kbps').value,
                 quota_gb_month:State.config.upload.quota_gb_month },
        record:{ local_full_stream:true, keep_days:+document.getElementById('cfg-keep').value },
        patrol: State.config.patrol
      };
      await API.putConfig(cfg); State.config=cfg;
      const m=document.getElementById('cfg-msg'); if(m) m.textContent='✔ 已保存到固件并热生效';
      toast('配置已保存','已 PUT /api/v1/config','info');
    }
    else if(a==='cfg-reload'){ State.config=await API.getConfig(); renderAll(); }
    else if(a==='mode-toggle'){
      if(API.mode==='live'){ API.setMode('mock'); toast('已切换','MOCK · 演示数据','info'); }
      else { API.setMode('live'); toast('已切换','LIVE · 真机（读取失败会报错，属正常）','warn'); }
      await boot(true);
    }
  }

  async function loadPlayback(){
    State.snapshots = await API.snapshots({date:State.date, camera_id:State.camId, limit:48});
    renderAll();
  }

  /* ---------------- toast ---------------- */
  function toast(title, body, sev){
    const wrap=document.getElementById('toast-wrap'); if(!wrap) return;
    const el=document.createElement('div');
    el.className='toast '+(sev||'');
    el.innerHTML=`<div class="tt">${esc(title)}</div><div class="tb">${esc(body||'')}</div>`;
    wrap.appendChild(el);
    setTimeout(()=>{ el.style.transition='opacity .3s'; el.style.opacity='0'; setTimeout(()=>el.remove(),320); }, 4200);
  }

  /* ---------------- 启动 ---------------- */
  const State = initialState();

  async function boot(silent){
    try{
      const [cams,presets,evs,health,cfg,logs] = await Promise.all([
        API.cameras(), API.presets('cam-detail'), API.events({limit:120}),
        API.health(), API.getConfig(), API.logs({limit:60})
      ]);
      State.cameras=cams; State.presets=presets; State.events=evs;
      State.health=health; State.config=cfg; State.logs=logs;
      State.camId = cams.find(c=>c.role==='panorama') ? cams.find(c=>c.role==='panorama').id : (cams[0]||{}).id;
      State.splash = await API.splash({camera_id:State.camId,window:State.range,step:300});
      State.snapshots = await API.snapshots({date:State.date, camera_id:State.camId, limit:48});
      renderAll();
      if(!silent) API.subscribe(onLiveEvent);
    }catch(err){
      console.error(err);
      const v=document.getElementById('view');
      if(v) v.innerHTML = `<div class="notice red"><b>连不上固件服务</b><br>
        ${esc(err.message||err)}<br><br>
        请确认：① 树莓派已跑起 <span class="mono">yutang-vision</span>；
        ② 地址正确（当前 <span class="mono">${esc(API.base)}</span>，可在"设置"页修改）；
        ③ 或把模式切回 <span class="mono">MOCK</span> 继续看原型。</div>
        <div style="margin-top:14px"><button class="btn" data-act="mode-toggle">切回 MOCK</button></div>`;
      const b=v&&v.querySelector('[data-act]'); if(b) b.onclick=()=>{API.setMode('mock'); boot();};
    }
  }

  function onLiveEvent(ev){
    State.events.unshift(ev);
    if(State.events.length>400) State.events.pop();
    const lbl = (Data.EVENT_TYPES[ev.type]||{}).label||ev.type;
    toast(lbl, ev.detail||'', ev.severity);
    // 轻量更新：徽标 + 事件列表 + 底部时间轴（不整页重绘，避免打断视频）
    const S=State;
    renderRail(S);
    const badge=document.querySelector('.rail a.on .badge');
    const lc=document.getElementById('live-count'); if(lc) lc.textContent=S.events.length;
    const le=document.getElementById('live-evlist'); if(le) le.innerHTML=eventList(S.events.slice(0,12),S);
    const strip=document.getElementById('strip-canvas'); if(strip) Charts.timeline(strip,S.events);
    document.querySelectorAll('[data-ev]').forEach(el=>{ if(el.dataset.ev===ev.id) el.onclick=()=>{State.selectedEvent=ev.id;location.hash='events';}; });
  }

  function route(){
    const r=(location.hash||'#overview').slice(1);
    State.route = VIEWS[r]?r:'overview';
    renderAll();
  }

  if(typeof document!=='undefined'){
    window.addEventListener('hashchange',route);
    document.addEventListener('DOMContentLoaded',()=>{
      const clock=document.getElementById('tally-clock');
      setInterval(()=>{
        const t=fmtTime(Date.now()/1000);
        if(clock) clock.textContent=t;
        const oc=document.getElementById('osd-clock');
        if(oc) oc.innerHTML=`${t}<br>${esc((State.cameras.find(c=>c.id===State.camId)||{}).model||'')}`;
      },1000);
      setInterval(()=>{ const strip=document.getElementById('strip-canvas');
        if(strip) Charts.timeline(strip, State.events); }, 60000);
      route(); boot();
    });
  }

  return {PAGES, VIEWS, State, initialState, boot, renderAll, esc, fmtTime, fmtDate, fmtBytes,
          PAGES_LIST:PAGES};
})();

if (typeof module !== 'undefined') module.exports = App;
