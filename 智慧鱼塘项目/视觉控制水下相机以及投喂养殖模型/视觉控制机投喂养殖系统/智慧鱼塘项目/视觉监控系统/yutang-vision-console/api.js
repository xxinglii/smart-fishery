/* ============================================================================
   api.js · 唯一的数据出入口
   MODE=mock  → 走 data.js 的模拟数据（本原型默认）
   MODE=live  → 走真机 http://<树莓派IP>:8080/api/v1/...
   两者返回结构完全一致（见《视觉系统_API契约_v1.md》）
   ========================================================================== */

const API = (() => {

  const HAS_DOM = typeof document !== 'undefined';
  let MODE = (HAS_DOM && document.body && document.body.dataset.mode) || 'mock';
  let BASE = (HAS_DOM && (localStorage.getItem('yutang.apiBase')||'')) || 'http://192.168.1.50:8080';
  let mockAcked = new Set();

  const qs = o => Object.entries(o||{})
    .filter(([,v])=>v!==undefined && v!==null && v!=='')
    .map(([k,v])=>`${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join('&');

  async function call(path, opts){
    const url = `${BASE}/api/v1${path}`;
    const r = await fetch(url, Object.assign({headers:{'Content-Type':'application/json'}}, opts));
    if(!r.ok) throw new Error(`${r.status} ${r.statusText} @ ${path}`);
    return r.json();
  }

  function delay(ms){return new Promise(res=>setTimeout(res,ms))}

  /* ---------------- mock 实现 ---------------- */
  const mock = {
    health:      async()=>{ await delay(40); return Data.health(); },
    cameras:     async()=>{ await delay(40); return Data.CAMERAS.map(c=>({...c})); },
    presets:     async(id)=>{ await delay(30); return Data.PRESETS.filter(p=>!id||p.camera_id===id); },
    ptz:         async(id,body)=>{
      await delay(60);
      const cam = Data.CAMERAS.find(c=>c.id===id);
      if(!cam || !cam.ptz) return {ok:false,error:'该相机无云台'};
      if(body.action==='goto'){
        const p = Data.PRESETS.find(p=>p.id===body.preset_id);
        if(p){ cam.ptz.pan=p.pan; cam.ptz.tilt=p.tilt; cam.ptz.zoom=p.zoom; cam.ptz.preset_id=p.id; }
      }else if(body.action==='move'){
        cam.ptz.pan   = +(cam.ptz.pan   + (body.dx||0)*12).toFixed(1);
        cam.ptz.tilt  = Math.max(-90,Math.min(0, cam.ptz.tilt + (body.dy||0)*6));
        cam.ptz.zoom  = Math.max(1,Math.min(cam.ptz.zoom_max, +(cam.ptz.zoom + (body.zoom||0)*1.5).toFixed(1)));
      }else if(body.action==='home'){ cam.ptz.pan=0; cam.ptz.tilt=-10; cam.ptz.zoom=1; }
      else if(body.action==='save'){
        const ex = Data.PRESETS.find(p=>p.id===body.preset_id);
        const rec = {id:body.preset_id,name:body.name||`预置位 ${body.preset_id}`,camera_id:id,
                     pan:cam.ptz.pan,tilt:cam.ptz.tilt,zoom:cam.ptz.zoom};
        if(ex) Object.assign(ex,rec); else Data.PRESETS.push(rec);
      }
      return {ok:true, ptz:{...cam.ptz}};
    },
    events:      async(q={})=>{
      await delay(60);
      let evs = Data.events(q.limit||120);
      if(q.type) evs = evs.filter(e=>e.type===q.type);
      if(q.since) evs = evs.filter(e=>e.ts>=+q.since);
      return evs.map(e=>({...e, acked:e.acked||mockAcked.has(e.id)}));
    },
    ack:         async(id)=>{ await delay(30); mockAcked.add(id); return {ok:true}; },
    splash:      async(q={})=>{ await delay(60);
      const h = q.window==='6h'?6:(q.window==='1h'?1:24);
      return Data.splashSeries(h, q.step||300); },
    snapshots:   async(q={})=>{ await delay(50); return Data.snapshots(q.date,q.camera_id,q.limit||48); },
    config:      async()=>{ await delay(30); return JSON.parse(JSON.stringify(Data.CONFIG)); },
    putConfig:   async(cfg)=>{ await delay(50); Object.assign(Data.CONFIG,cfg); return {ok:true}; },
    logs:        async(q={})=>{ await delay(40); return Data.logs(q.limit||80); }
  };

  /* ---------------- live 实现 ---------------- */
  const live = {
    health:     ()=>call('/health'),
    cameras:    ()=>call('/cameras'),
    presets:    id=>call(`/presets?${qs({camera_id:id})}`),
    ptz:        (id,body)=>call(`/cameras/${id}/ptz`,{method:'POST',body:JSON.stringify(body)}),
    events:     q=>call(`/events?${qs(q)}`),
    ack:        id=>call(`/events/${id}/ack`,{method:'POST'}),
    splash:     q=>call(`/metrics/splash?${qs(q)}`),
    snapshots:  q=>call(`/snapshots?${qs(q)}`),
    config:     ()=>call('/config'),
    putConfig:  cfg=>call('/config',{method:'PUT',body:JSON.stringify(cfg)}),
    logs:       q=>call(`/logs?${qs(q)}`)
  };

  const impl = ()=> MODE==='live' ? live : mock;

  /* ---------------- 实时订阅 ----------------
     live: SSE   mock: 本地定时器造事件（用于演示"事件自己冒出来"）           */
  const listeners = new Set();
  let sse=null, mockTimer=null, seq=0;

  function emit(ev){ listeners.forEach(fn=>{ try{fn(ev)}catch(e){console.warn(e)} }); }

  function startMockTicker(){
    if(mockTimer) return;
    mockTimer = setInterval(()=>{
      const r = Math.random();
      let type='motion', sev='info';
      if(r>.72){ type='splash_activity'; sev='info'; }
      else if(r>.88){ type='surface_aggregation'; sev='notice'; }
      else if(r>.96){ type='person'; sev='warn'; }
      else return;
      const d = Data.EVENT_TYPES[type];
      const ratio = +(1.5+Math.random()*1.6).toFixed(2);
      seq++;
      emit({
        id:`ev-live-${Date.now()}-${seq}`, ts:Math.floor(Date.now()/1000),
        camera_id: Math.random()>.5?'cam-pano':'cam-detail',
        type, severity:sev, confidence:+(0.6+Math.random()*0.35).toFixed(2),
        title:d.label + (type==='splash_activity'?'强度上升':''),
        detail: type==='splash_activity'
          ? `V-Value ${ratio}× 基线，持续 ${Math.floor(20+Math.random()*90)} s；区域：投料点 20 m 半径`
          : d.note,
        metric: type==='splash_activity'?{v_value:+(0.216*ratio).toFixed(3),baseline:0.216,ratio,duration_s:Math.floor(20+Math.random()*90)}:null,
        snapshot_url:null, clip_url:null, acked:false, evidence:d.evidence
      });
    }, 11000);
  }

  function subscribe(cb){
    listeners.add(cb);
    if(MODE==='live'){
      if(!sse){
        sse = new EventSource(`${BASE}/api/v1/stream/events`);
        sse.addEventListener('event', e=>{ try{ emit(JSON.parse(e.data)) }catch(err){ console.warn(err) } });
        sse.onerror = ()=>{ /* EventSource 自带重连 */ };
      }
    } else startMockTicker();
    return ()=>{ listeners.delete(cb); };
  }

  return {
    get mode(){return MODE},
    setMode(m){ MODE=m; if(HAS_DOM && document.body) document.body.dataset.mode=m;
      if(m==='mock') startMockTicker(); },
    get base(){return BASE},
    setBase(u){ BASE=u; if(HAS_DOM) try{ localStorage.setItem('yutang.apiBase',u); }catch(e){} },
    subscribe,
    health:     (...a)=>impl().health(...a),
    cameras:    (...a)=>impl().cameras(...a),
    presets:    (...a)=>impl().presets(...a),
    ptz:        (...a)=>impl().ptz(...a),
    events:     (...a)=>impl().events(...a),
    ack:        (...a)=>impl().ack(...a),
    splash:     (...a)=>impl().splash(...a),
    snapshots:  (...a)=>impl().snapshots(...a),
    getConfig:  (...a)=>impl().config(...a),
    putConfig:  (...a)=>impl().putConfig(...a),
    logs:       (...a)=>impl().logs(...a)
  };
})();

if (typeof module !== 'undefined') module.exports = API;
