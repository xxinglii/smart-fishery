/* ============================================================================
   data.js · 领域模型 + 模拟数据源
   铁律：这里产出的对象结构必须与《视觉系统_API契约_v1.md》完全一致。
        换真机时只需要把 api.js 的 mode 从 mock 切成 live。
   ========================================================================== */

const Data = (() => {

  /* ---------- 可复现随机 ---------- */
  function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}
  const rnd = mulberry32(20260919);
  const R = (a,b)=>a+(b-a)*rnd();
  const RI = (a,b)=>Math.floor(R(a,b+1));
  const pick = arr=>arr[Math.floor(rnd()*arr.length)];
  const now = ()=>Math.floor(Date.now()/1000);

  /* ---------- 场景与常量 ---------- */
  const SITE = {
    name:'1 号塘 · 草鱼主养',
    location:'塘口东北角立杆 6 m',
    reservoir:{
      note:'两台相机 + 一台树莓派 + PoE 交换机；塘边有市电、无宽带，走 4G CPE',
    }
  };

  // 投喂时段（对应 config.feed_windows）
  const FEED_WINDOWS = [{start:'06:30',end:'07:10'},{start:'16:30',end:'17:20'}];

  /* ---------- 相机（契约 §2） ---------- */
  const CAMERAS = [
    {
      id:'cam-pano', name:'全景位 · 塘东北角', role:'panorama',
      model:'DS-2CD3T86FWDV3-I3S', lens:'6 mm', ip:'192.168.1.64',
      rtsp:'rtsp://admin:***@192.168.1.64:554/Streaming/Channels/101',
      onvif:true, online:true, resolution:'3840x2160', fps:20, bitrate_kbps:4096,
      ir_m:30, ptz:null, snapshot_url:'/api/v1/cameras/cam-pano/snapshot',
      cover:'塘面 60° 视场 · 约 90 m 宽水面'
    },
    {
      id:'cam-detail', name:'细节位 · 塘西南角', role:'detail',
      model:'DS-2DC4423IW-D', lens:'4.5–103.5 mm（23×）', ip:'192.168.1.65',
      rtsp:'rtsp://admin:***@192.168.1.65:554/Streaming/Channels/101',
      onvif:true, online:true, resolution:'2560x1440', fps:25, bitrate_kbps:4096,
      ir_m:100,
      ptz:{pan:132.5,tilt:-18.0,zoom:3.2,zoom_max:23,moving:false,preset_id:1},
      snapshot_url:'/api/v1/cameras/cam-detail/snapshot',
      cover:'巡航 3 个预置位 · 长焦端 100 m 处约 2 mm/px'
    }
  ];

  /* ---------- 预置位（契约 §2） ---------- */
  const PRESETS = [
    {id:1,name:'投料点',camera_id:'cam-detail',pan:118.0,tilt:-22.0,zoom:6.0},
    {id:2,name:'塘中央',camera_id:'cam-detail',pan:168.0,tilt:-9.0,zoom:1.0},
    {id:3,name:'进水口',camera_id:'cam-detail',pan:205.0,tilt:-14.0,zoom:4.0},
    {id:4,name:'对岸东南角',camera_id:'cam-detail',pan:236.0,tilt:-6.5,zoom:2.0}
  ];

  /* ---------- 配置（契约 §6） ---------- */
  const CONFIG = {
    feed_windows:FEED_WINDOWS,
    thresholds:{splash_ratio:1.6,aggregation_area_pct:4.0,person_confidence:0.6},
    capture:{interval_s:60,on_event:true,jpeg_quality:85,max_width:1920},
    upload:{policy:'thumbs_only',max_kbps:512,quota_gb_month:10},
    record:{local_full_stream:true,keep_days:14},
    patrol:{on:true,preset_ids:[1,2,3],dwell_s:30}
  };

  /* ---------- 事件类型字典 ---------- */
  const EVENT_TYPES = {
    splash_activity:    {label:'摄食水花',   icon:'≈', evidence:'B', note:'帧差/光流运动占比相对基线的比值（V-Value）'},
    surface_aggregation:{label:'水面聚集',   icon:'◍', evidence:'C', note:'暗斑连通域面积占比，浮头/聚集的粗代理'},
    person:             {label:'人形入侵',   icon:'☗', evidence:'B', note:'警戒区内人形检测，用于防偷捕'},
    offline:            {label:'设备离线',   icon:'✕', evidence:'A', note:'RTSP 连续失败 ≥30 s'},
    tamper:             {label:'画面异常',   icon:'⚠', evidence:'A', note:'亮度/方差突变：遮挡、喷水、移位'},
    motion:             {label:'运动',       icon:'↯', evidence:'C', note:'未分类运动'}
  };

  /* ---------- 事件流（契约 §3） ---------- */
  function mkEvent(i, ts, type, severity, o={}){
    const t = EVENT_TYPES[type];
    return Object.assign({
      id:`ev-${String(ts)}-${String(i).padStart(4,'0')}`,
      ts, camera_id:o.camera_id||'cam-pano', type, severity,
      confidence:o.confidence!=null?o.confidence:+R(.55,.95).toFixed(2),
      title:o.title||t.label, detail:o.detail||'',
      metric:o.metric||null,
      snapshot_url:`/api/v1/events/ev-${ts}-${String(i).padStart(4,'0')}/snapshot`,
      clip_url:null, acked:!!o.acked, evidence:o.evidence||t.evidence
    }, {});
  }

  function events(limit=120){
    const t0 = now(), out=[];
    // 今天两个投喂时段前后的水花事件是主角
    const dayStart = t0 - (t0 % 86400);
    let i=1;
    for(let d=0; d<2; d++){
      const base = dayStart - d*86400;
      FEED_WINDOWS.forEach((w,wi)=>{
        const [sh,sm]=w.start.split(':').map(Number);
        const ws = base + sh*3600 + sm*60;
        // 投喂开始后 2–9 分钟，2–3 条水花事件
        const n = RI(2,3);
        for(let k=0;k<n;k++){
          const ts = ws + RI(120,540);
          if(ts>t0) continue;
          const ratio = +R(1.62,2.9).toFixed(2);
          out.push(mkEvent(i++, ts, 'splash_activity', ratio>2.4?'notice':'info', {
            camera_id:'cam-pano',
            title:'摄食水花强度上升',
            detail:`V-Value ${ratio}× 基线，持续 ${RI(28,140)} s；区域：投料点 20 m 半径`,
            metric:{v_value:+(0.216*ratio).toFixed(3), baseline:0.216, ratio, duration_s:RI(28,140)},
            confidence:+R(.72,.94).toFixed(2)
          }));
        }
        // 偶发：投喂后聚集
        if(rnd()>.45){
          const ts = ws + RI(600,1500);
          if(ts<=t0) out.push(mkEvent(i++, ts, 'surface_aggregation','notice',{
            camera_id:'cam-pano', title:'水面暗斑聚集',
            detail:`暗斑面积占比 ${R(4.2,7.8).toFixed(1)}%，持续 ${RI(3,9)} 分钟`,
            metric:{area_pct:+R(4.2,7.8).toFixed(1), duration_s:RI(180,540)},
            evidence:'C'
          }));
        }
      });
      // 夜间人形（防偷捕）
      const nightTs = base + RI(0,4)*3600 + RI(0,3500);
      if(nightTs<=t0 && rnd()>.35){
        out.push(mkEvent(i++, nightTs, 'person', rnd()>.7?'warn':'notice', {
          camera_id:'cam-detail', title:'警戒区检出人形',
          detail:`置信度 ${R(.62,.93).toFixed(2)}；方位 ${RI(80,260)}°；已联动球机跟踪`,
          confidence:+R(.62,.93).toFixed(2), evidence:'B'
        }));
      }
      // 偶发离线/画面异常
      if(rnd()>.6) out.push(mkEvent(i++, base+RI(1000,80000),'offline', pick(['warn','critical']),{
        camera_id:pick(['cam-pano','cam-detail']), title:'相机离线',
        detail:`RTSP 断流 ${RI(35,420)} s，已自动重连成功`, evidence:'A'
      }));
      if(rnd()>.75) out.push(mkEvent(i++, base+RI(1000,80000),'tamper','warn',{
        camera_id:'cam-pano', title:'画面方差突变',
        detail:'疑似镜头遮挡或强光直射，请核查', evidence:'A'
      }));
    }
    return out.sort((a,b)=>b.ts-a.ts).slice(0,limit);
  }

  /* ---------- 水花曲线（契约 §4） ---------- */
  function splashSeries(windowH=24, stepS=300){
    const t1 = now(), t0 = t1 - windowH*3600, series=[];
    const dayStart = t1 - (t1%86400);
    const feedSet = [];
    for(let d=0;d<2;d++){
      FEED_WINDOWS.forEach(w=>{
        const [sh,sm]=w.start.split(':').map(Number);
        feedSet.push(dayStart - d*86400 + sh*3600 + sm*60);
      });
    }
    for(let ts=t0; ts<=t1; ts+=stepS){
      const hour = new Date(ts*1000).getHours();
      const base = 0.18 + 0.05*Math.sin((hour-6)/24*Math.PI*2);
      let v = base + R(-0.03,0.03);
      // 投喂后 30 分钟内的抬升
      feedSet.forEach(fs=>{
        const dt = ts - fs;
        if(dt>0 && dt<1800) v += 0.42*Math.exp(-dt/600);
      });
      series.push({
        ts,
        v_value:+Math.max(0.02,v).toFixed(3),
        baseline:+base.toFixed(3),
        thr:0.40
      });
    }
    return {window:`${windowH}h`, step:stepS, series, feed_windows:FEED_WINDOWS};
  }

  /* ---------- 健康（契约 §1） ---------- */
  function health(){
    const mb = 3.0*1024*1024*1024/1024*1024*1024; // 3 GB
    return {
      ok:true, version:'1.0.0', uptime_s:84213+RI(0,9000), mode:'mock',
      pi:{cpu_pct:+R(14,38).toFixed(1), mem_pct:+R(26,52).toFixed(1), temp_c:+R(41,58).toFixed(1), disk_free_gb:+R(28,52).toFixed(1)},
      net:{type:'4g',rssi_dbm:RI(-83,-63),carrier:'中国移动',uplink_kbps:RI(900,3200),
           month_bytes:Math.round(3.1*1024*1024*1024), month_quota_bytes:10*1024*1024*1024},
      storage:{recording:true,days_kept:14,bytes_per_day:Math.round(16.4*1024*1024*1024)},
      services:[{name:'rtsp-ingest',ok:true},{name:'detector',ok:true},{name:'onvif-ptz',ok:true},{name:'uploader',ok:true}]
    };
  }

  /* ---------- 日志（契约 §7） ---------- */
  function logs(limit=80){
    const t0=now(), pool=[
      ['info','rtsp-ingest','cam-pano 关键帧正常，码率 4.1 Mbps'],
      ['info','detector','ROI 基线已更新（24 h 滑动窗口）'],
      ['warn','rtsp-ingest','cam-detail 断流，退避重连 2 s'],
      ['info','rtsp-ingest','cam-detail 重连成功（第 2 次）'],
      ['info','onvif-ptz','巡航：切到预置位 1 投料点'],
      ['warn','uploader','4G 上行 620 kbps，低优先级抓图已延后'],
      ['info','store','清理 30 天前抓图 1,284 张，释放 2.1 GB'],
      ['info','detector','splash_activity ratio=1.94 → 已上报'],
      ['error','rtsp-ingest','cam-pano 连续失败 32 s → 触发 offline 事件'],
      ['info','store','SQLite WAL checkpoint 完成']
    ];
    const out=[];let t=t0;
    for(let i=0;i<limit;i++){
      const p=pool[RI(0,pool.length-1)];
      out.push({ts:t,level:p[0],src:p[1],msg:p[2]});
      t -= RI(60,900);
    }
    return out;
  }

  /* ---------- 抓图墙（契约 §5） ---------- */
  function snapshots(date, camera_id, limit=48){
    const day = date ? new Date(date+'T00:00:00') : new Date();
    const base = Math.floor(day.getTime()/1000);
    const out=[];
    for(let i=0;i<limit;i++){
      const ts = base + i*1800 + RI(-90,90);
      if(ts>now()) break;
      out.push({ts,camera_id:camera_id||'cam-pano',
        url:`/api/v1/snapshots/${ts}.jpg`,
        trigger: rnd()>.86?'event':(rnd()>.9?'manual':'interval')});
    }
    return out;
  }

  /* ---------- 派生指标（给总览页用，非契约端点） ---------- */
  function summarize(evs){
    const today = now() - (now()%86400);
    const t = evs.filter(e=>e.ts>=today);
    return {
      total:t.length,
      unacked:t.filter(e=>!e.acked).length,
      splash:t.filter(e=>e.type==='splash_activity').length,
      person:t.filter(e=>e.type==='person').length,
      critical:t.filter(e=>e.severity==='critical').length
    };
  }

  return {SITE,FEED_WINDOWS,CAMERAS,PRESETS,CONFIG,EVENT_TYPES,
          events, splashSeries, health, logs, snapshots, summarize,
          now, rnd, R, RI, pick};
})();

if (typeof module !== 'undefined') module.exports = Data;
