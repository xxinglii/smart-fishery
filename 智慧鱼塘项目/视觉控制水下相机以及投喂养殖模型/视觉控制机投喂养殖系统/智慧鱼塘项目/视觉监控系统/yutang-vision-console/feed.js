/* ============================================================================
   feed.js · 合成"实时画面"渲染器
   原型里没有真视频流，所以用 Canvas 合成一路**看起来像那么回事**的水面：
   风纹、日光碎斑、投喂时段的抢食水花、夜间红外噪点与暗角。
   这不是为了好看——是为了让"水花能不能被看见"这件事在界面上可判断。
   ========================================================================== */

const Feed = (() => {

  const instances = [];
  let raf = null, last = 0;

  const NIGHT_START = 19, NIGHT_END  = 6;

  function isNight(){ const h=new Date().getHours(); return h>=NIGHT_START || h<NIGHT_END; }

  function isFeedTime(){
    const d=new Date(), m=d.getHours()*60+d.getMinutes();
    return Data.FEED_WINDOWS.some(w=>{
      const [sh,sm]=w.start.split(':').map(Number), [eh,em]=w.end.split(':').map(Number);
      return m>=sh*60+sm-6 && m<=eh*60+em+34;   // 投喂前后各留一点余量
    });
  }

  /* ---------- 单个实例 ---------- */
  function create(canvas, opts={}){
    const ctx = canvas.getContext('2d');
    const inst = {
      canvas, ctx, opts,
      w:0, h:0, dpr:1,
      t: Math.random()*1000,
      ripples: [],
      sparks: [],
      splashes: [],
      noise: null,
      camDrift: opts.role==='detail' ? Math.random()*Math.PI*2 : 0,
      quality: opts.quality || (canvas.clientWidth>360 ? 'high':'low'),
      alive: true
    };

    function resize(){
      const r = canvas.getBoundingClientRect();
      const dpr = Math.min(2, window.devicePixelRatio||1);
      inst.w = Math.max(80, Math.round(r.width)); inst.h = Math.max(45, Math.round(r.height)); inst.dpr = dpr;
      canvas.width = Math.round(inst.w*dpr); canvas.height = Math.round(inst.h*dpr);
      ctx.setTransform(dpr,0,0,dpr,0,0);
      seed();
    }

    function seed(){
      const n = inst.quality==='high' ? Math.round(inst.w/7) : Math.round(inst.w/16);
      inst.ripples = Array.from({length:n},(_,i)=>({
        y: (i+0.5)/n,                 // 归一化纵向位置
        amp: 0.004 + Math.random()*0.012,
        ph: Math.random()*Math.PI*2,
        sp: 0.25 + Math.random()*0.85,
        a: 0.05 + Math.random()*0.13
      }));
      const sn = inst.quality==='high' ? 90 : 26;
      inst.sparks = Array.from({length:sn},()=>({
        x:Math.random(), y:Math.random(), r:Math.random()*0.9+0.3, ph:Math.random()*6.28
      }));
      const nw = Math.round(inst.w/3), nh = Math.round(inst.h/3);
      const img = ctx.createImageData(nw, nh);
      for(let i=0;i<img.data.length;i+=4){
        const v = 150 + Math.random()*105;
        img.data[i]=img.data[i+1]=img.data[i+2]=v; img.data[i+3]=22;
      }
      inst.noise = {img, nw, nh};
    }

    function spawnSplash(){
      const fw = 0.5 + (opts.splashZone!=null?opts.splashZone:0.34);
      inst.splashes.push({
        x: fw + (Math.random()-0.5)*0.34,
        y: 0.46 + Math.random()*0.30,
        r: 1.5, max: 12 + Math.random()*34,
        life: 1, rate: 0.9 + Math.random()*1.4
      });
    }

    function draw(dt){
      const {w,h} = inst, night = isNight(), feed = isFeedTime();
      inst.t += dt;

      // 云台缓慢巡航（细节位）：整体画面轻微横移
      if(opts.role==='detail'){
        inst.camDrift += dt*0.045;
      }
      const drift = opts.role==='detail' ? Math.sin(inst.camDrift)*0.035 : 0;

      // ---- 底色：深水
      const g = ctx.createLinearGradient(0,0,0,h);
      if(night){ g.addColorStop(0,'#0A1512'); g.addColorStop(0.55,'#08110F'); g.addColorStop(1,'#050A09'); }
      else     { g.addColorStop(0,'#16323C'); g.addColorStop(0.5,'#102630'); g.addColorStop(1,'#0A171E'); }
      ctx.fillStyle=g; ctx.fillRect(0,0,w,h);

      // ---- 远景塘埂（上缘）
      ctx.fillStyle = night ? '#0C1412' : '#0E2028';
      ctx.fillRect(0,0,w,h*0.075);
      ctx.fillStyle = night ? '#132019' : '#16303A';
      ctx.fillRect(0,h*0.062,w,2);

      // ---- 水面波纹
      ctx.save();
      ctx.lineWidth = inst.quality==='high' ? 1 : 1.4;
      inst.ripples.forEach((r,i)=>{
        const y = h*(0.10 + r.y*0.88);
        const amp = h*r.amp*(feed?1.5:1);
        ctx.beginPath();
        const steps = inst.quality==='high'? 34 : 16;
        for(let s=0;s<=steps;s++){
          const x = (s/steps)*w;
          const yy = y + Math.sin(x/w*7.4 + inst.t*r.sp + r.ph)*amp
                       + Math.sin(x/w*3.1 - inst.t*r.sp*0.6 + i)*amp*0.6;
          s?ctx.lineTo(x,yy):ctx.moveTo(x,yy);
        }
        const a = r.a * (night?0.55:1) * (feed?1.25:1);
        ctx.strokeStyle = night ? `rgba(120,220,190,${a*0.5})` : `rgba(190,235,255,${a})`;
        ctx.stroke();
      });
      ctx.restore();

      // ---- 日光碎斑（白天才有）
      if(!night){
        ctx.save();
        inst.sparks.forEach(s=>{
          const tw = 0.35 + 0.65*Math.abs(Math.sin(inst.t*1.7 + s.ph));
          const x = ((s.x + drift + 1)%1)*w, y = h*(0.14 + s.y*0.82);
          ctx.globalAlpha = 0.10 + 0.30*tw;
          ctx.fillStyle = '#FFF3D0';
          ctx.fillRect(x, y, s.r*2.2, s.r*0.8);
        });
        ctx.restore();
      }

      // ---- 抢食水花
      if(feed && Math.random() < (inst.quality==='high'?0.09:0.04)) spawnSplash();
      if(!feed && Math.random() < 0.006) spawnSplash();
      ctx.save();
      inst.splashes = inst.splashes.filter(s=>s.life>0);
      inst.splashes.forEach(s=>{
        s.r += s.rate*dt*26; s.life -= dt*0.65;
        const a = Math.max(0,s.life)*0.85;
        ctx.beginPath(); ctx.arc(s.x*w, s.y*h, s.r, 0, 6.2832);
        ctx.strokeStyle = night ? `rgba(190,255,225,${a*0.6})` : `rgba(235,250,255,${a})`;
        ctx.lineWidth = 1.3; ctx.stroke();
        ctx.beginPath(); ctx.arc(s.x*w, s.y*h, s.r*0.45, 0, 6.2832);
        ctx.fillStyle = night ? `rgba(210,255,235,${a*0.28})` : `rgba(255,255,255,${a*0.42})`;
        ctx.fill();
      });
      ctx.restore();

      // ---- 漂浮物/暗斑（浮头代理）
      ctx.save();
      ctx.globalAlpha = 0.5;
      for(let i=0;i<3;i++){
        const px = ((i*0.31 + 0.12 + drift*2 + 1)%1)*w;
        const py = h*(0.34 + i*0.19);
        ctx.beginPath();
        ctx.ellipse(px, py, w*0.022, h*0.012, 0, 0, 6.2832);
        ctx.fillStyle = night ? 'rgba(10,26,20,.85)' : 'rgba(6,18,24,.75)';
        ctx.fill();
      }
      ctx.restore();

      // ---- 夜间红外噪点 + 暗角
      if(night && inst.noise){
        const {img,nw,nh} = inst.noise;
        ctx.save(); ctx.globalAlpha = 0.30 + 0.12*Math.sin(inst.t*8);
        ctx.drawImage(canvasFrom(img,nw,nh,inst), 0,0,w,h);
        ctx.restore();
        const vg = ctx.createRadialGradient(w/2,h/2,h*0.25,w/2,h/2,h*0.95);
        vg.addColorStop(0,'rgba(0,0,0,0)'); vg.addColorStop(1,'rgba(0,0,0,.62)');
        ctx.fillStyle=vg; ctx.fillRect(0,0,w,h);
      }

      // ---- 十字准星（全景位才有）
      if(opts.role==='panorama' && inst.quality==='high'){
        ctx.save(); ctx.globalAlpha=.28; ctx.strokeStyle='#FFB020'; ctx.lineWidth=1;
        ctx.beginPath();
        ctx.moveTo(w/2-9,h/2); ctx.lineTo(w/2-3,h/2);
        ctx.moveTo(w/2+3,h/2); ctx.lineTo(w/2+9,h/2);
        ctx.moveTo(w/2,h/2-9); ctx.lineTo(w/2,h/2-3);
        ctx.moveTo(w/2,h/2+3); ctx.lineTo(w/2,h/2+9);
        ctx.stroke(); ctx.restore();
      }
    }

    // 噪点缓存（每实例一份，避免每帧重建）
    const noiseCache = new WeakMap();
    function canvasFrom(img,nw,nh,inst){
      let c = noiseCache.get(inst);
      if(!c){ c=document.createElement('canvas'); c.width=nw; c.height=nh;
              c.getContext('2d').putImageData(img,0,0); noiseCache.set(inst,c); }
      return c;
    }

    inst.resize = resize;
    inst.draw = draw;
    inst.destroy = ()=>{ inst.alive=false; const i=instances.indexOf(inst); if(i>=0) instances.splice(i,1); };
    return inst;
  }

  /* ---------- 全局循环 ---------- */
  function loop(ts){
    const dt = Math.min(0.05, (ts-last)/1000 || 0.016); last = ts;
    if(!document.hidden) instances.forEach(i=>{ if(i.alive) i.draw(dt); });
    raf = requestAnimationFrame(loop);
  }

  let ro = null;
  function mount(canvas, opts={}){
    const inst = create(canvas, opts);
    inst.resize();
    instances.push(inst);
    if(!raf) raf = requestAnimationFrame(loop);
    if(!ro && window.ResizeObserver){
      ro = new ResizeObserver(()=>instances.forEach(i=>i.resize()));
      instances.forEach(i=>ro.observe(i.canvas));
    }else if(ro){ ro.observe(canvas); }
    return inst;
  }

  function unmountAll(){ instances.slice().forEach(i=>i.destroy()); }

  return { mount, unmountAll, isNight, isFeedTime, get count(){return instances.length} };
})();

if (typeof module !== 'undefined') module.exports = Feed;
