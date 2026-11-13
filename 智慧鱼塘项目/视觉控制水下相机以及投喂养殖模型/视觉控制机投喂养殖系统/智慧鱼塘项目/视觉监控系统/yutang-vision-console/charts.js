/* ============================================================================
   charts.js · 零依赖 Canvas 图表
   风格与界面一致：近黑底、单像素网格、琥珀主色、等宽数字
   ========================================================================== */

const Charts = (() => {

  function setup(canvas, h){
    const dpr = Math.min(2, window.devicePixelRatio||1);
    const r = canvas.getBoundingClientRect();
    const w = Math.max(120, Math.round(r.width || canvas.parentElement?.clientWidth || 480));
    const hh = Math.max(60, Math.round(h || r.height || 160));
    canvas.width = Math.round(w*dpr); canvas.height = Math.round(hh*dpr);
    const ctx = canvas.getContext('2d');
    ctx.setTransform(dpr,0,0,dpr,0,0);
    ctx.clearRect(0,0,w,hh);
    return {ctx,w,h:hh};
  }

  const C = {
    grid:'rgba(255,255,255,.055)', axis:'#5C6675', ink:'#B7C0CD',
    amber:'#FFB020', red:'#FF4D4D', green:'#35E08A', blue:'#5AA9E6', dim:'#8A94A6'
  };

  function niceMax(v){ const p=Math.pow(10,Math.floor(Math.log10(v||1))); const n=v/p; return (n<=1?1:n<=2?2:n<=5?5:10)*p; }

  /* ---------------- V-Value 曲线（含基线、阈值、投喂时段） ---------------- */
  function splash(canvas, data, opts={}){
    const {ctx,w,h} = setup(canvas, opts.height||210);
    const pad = {l:44,r:14,t:16,b:26};
    const S = data.series || [];
    if(!S.length){ ctx.fillStyle=C.axis; ctx.fillText('无数据',pad.l,40); return; }
    const x0=pad.l, x1=w-pad.r, y0=pad.t, y1=h-pad.b;
    const t0=S[0].ts, t1=S[S.length-1].ts;
    const vmax = niceMax(Math.max(...S.map(s=>Math.max(s.v_value, s.thr||0)))*1.15);
    const X = ts => x0 + (ts-t0)/(t1-t0||1)*(x1-x0);
    const Y = v => y1 - (v/vmax)*(y1-y0);

    // 投喂时段底纹
    const dayStart = Math.floor(Date.now()/1000) - (Math.floor(Date.now()/1000)%86400);
    (data.feed_windows||[]).forEach(fw=>{
      for(let d=0;d<2;d++){
        const [sh,sm]=fw.start.split(':').map(Number), [eh,em]=fw.end.split(':').map(Number);
        const a=dayStart-d*86400+sh*3600+sm*60, b=dayStart-d*86400+eh*3600+em*60;
        if(b<t0||a>t1) return;
        ctx.fillStyle='rgba(255,176,32,.07)';
        ctx.fillRect(X(Math.max(a,t0)), y0, Math.max(1,X(Math.min(b,t1))-X(Math.max(a,t0))), y1-y0);
      }
    });

    // 网格
    ctx.strokeStyle=C.grid; ctx.lineWidth=1;
    for(let i=0;i<=4;i++){ const y=y0+(y1-y0)*i/4;
      ctx.beginPath(); ctx.moveTo(x0,y); ctx.lineTo(x1,y); ctx.stroke(); }
    // Y 轴刻度
    ctx.fillStyle=C.axis; ctx.font='10px "JetBrains Mono",monospace'; ctx.textAlign='right';
    for(let i=0;i<=4;i++){ const v=vmax*(1-i/4); ctx.fillText(v.toFixed(2), x0-7, y0+(y1-y0)*i/4+3.5); }
    ctx.textAlign='left';

    // 阈值线
    const thr = S[0].thr;
    if(thr){ ctx.save(); ctx.setLineDash([5,4]); ctx.strokeStyle='rgba(255,77,77,.75)';
      ctx.beginPath(); ctx.moveTo(x0,Y(thr)); ctx.lineTo(x1,Y(thr)); ctx.stroke(); ctx.restore();
      ctx.fillStyle='rgba(255,77,77,.9)'; ctx.fillText('阈值', x1-30, Y(thr)-5); }

    // 基线（虚线）
    if(S[0].baseline!=null){
      ctx.save(); ctx.setLineDash([2,4]); ctx.strokeStyle='rgba(138,148,166,.6)';
      ctx.beginPath();
      S.forEach((s,i)=>{ const x=X(s.ts),y=Y(s.baseline); i?ctx.lineTo(x,y):ctx.moveTo(x,y); });
      ctx.stroke(); ctx.restore();
    }

    // 曲线 + 面积
    const prog = opts.progress!=null?opts.progress:1;
    const upto = Math.max(2, Math.floor(S.length*prog));
    const grad = ctx.createLinearGradient(0,y0,0,y1);
    grad.addColorStop(0,'rgba(255,176,32,.34)'); grad.addColorStop(1,'rgba(255,176,32,0)');
    ctx.beginPath(); ctx.moveTo(X(S[0].ts), y1);
    for(let i=0;i<upto;i++) ctx.lineTo(X(S[i].ts), Y(S[i].v_value));
    ctx.lineTo(X(S[upto-1].ts), y1); ctx.closePath(); ctx.fillStyle=grad; ctx.fill();

    ctx.beginPath();
    for(let i=0;i<upto;i++){ const x=X(S[i].ts), y=Y(S[i].v_value); i?ctx.lineTo(x,y):ctx.moveTo(x,y); }
    ctx.strokeStyle=C.amber; ctx.lineWidth=1.6; ctx.stroke();

    // 超阈值点
    ctx.fillStyle=C.red;
    for(let i=0;i<upto;i++) if(thr && S[i].v_value>=thr){
      ctx.beginPath(); ctx.arc(X(S[i].ts),Y(S[i].v_value),2.6,0,6.2832); ctx.fill();
    }
    // X 轴刻度
    ctx.fillStyle=C.axis;
    for(let i=0;i<=4;i++){
      const ts=t0+(t1-t0)*i/4, d=new Date(ts*1000);
      ctx.fillText(`${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`,
                   Math.min(x1-26, Math.max(x0, X(ts)-13)), h-8);
    }
    // 图例
    ctx.fillStyle=C.amber; ctx.fillText('V-Value', x0+2, y0-4);
    ctx.fillStyle=C.dim;   ctx.fillText('· 基线', x0+56, y0-4);
  }

  /* ---------------- 迷你火花线 ---------------- */
  function spark(canvas, values, opts={}){
    const {ctx,w,h} = setup(canvas, opts.height||44);
    if(!values||values.length<2) return;
    const vmin=Math.min(...values), vmax=Math.max(...values)||1;
    const X=i=>i/(values.length-1)*(w-2)+1;
    const Y=v=>h-3-((v-vmin)/((vmax-vmin)||1))*(h-8);
    ctx.beginPath(); ctx.moveTo(X(0),h);
    values.forEach((v,i)=>ctx.lineTo(X(i),Y(v)));
    ctx.lineTo(X(values.length-1),h); ctx.closePath();
    ctx.fillStyle=opts.fill||'rgba(255,176,32,.14)'; ctx.fill();
    ctx.beginPath(); values.forEach((v,i)=>i?ctx.lineTo(X(i),Y(v)):ctx.moveTo(X(i),Y(v)));
    ctx.strokeStyle=opts.color||C.amber; ctx.lineWidth=1.3; ctx.stroke();
  }

  /* ---------------- 横向条形 ---------------- */
  function hbars(canvas, items, opts={}){
    const rowH = opts.rowH||26;
    const {ctx,w,h} = setup(canvas, items.length*rowH + 8);
    const max = Math.max(...items.map(i=>i.value), 1);
    const labelW = opts.labelW||112;
    ctx.font='12px "Noto Sans SC",sans-serif';
    items.forEach((it,i)=>{
      const y = i*rowH+4;
      ctx.fillStyle=C.ink; ctx.textAlign='left';
      ctx.fillText(it.label, 0, y+13);
      const bx=labelW, bw=Math.max(2,(w-labelW-52)*(it.value/max));
      ctx.fillStyle='#1B2029'; ctx.fillRect(bx,y+4,w-labelW-52,11);
      ctx.fillStyle=it.color||C.amber; ctx.fillRect(bx,y+4,bw,11);
      ctx.fillStyle=C.dim; ctx.textAlign='right';
      ctx.font='11px "JetBrains Mono",monospace';
      ctx.fillText(it.text!=null?it.text:String(it.value), w, y+14);
      ctx.textAlign='left'; ctx.font='12px "Noto Sans SC",sans-serif';
    });
  }

  /* ---------------- 底部 24h 事件轴 ---------------- */
  function timeline(canvas, events, opts={}){
    const dpr = Math.min(2, window.devicePixelRatio||1);
    const r = canvas.getBoundingClientRect();
    const w = Math.max(200, Math.round(r.width || 600)), h = 46;
    canvas.width=w*dpr; canvas.height=h*dpr;
    const ctx=canvas.getContext('2d'); ctx.setTransform(dpr,0,0,dpr,0,0); ctx.clearRect(0,0,w,h);

    const t1=Math.floor(Date.now()/1000), t0=t1-86400;
    const X=ts=>((ts-t0)/86400)*w;
    // 小时刻度
    ctx.strokeStyle=C.grid; ctx.fillStyle=C.axis; ctx.font='9px "JetBrains Mono",monospace';
    const d0=new Date(t0*1000);
    for(let i=0;i<=24;i+=3){
      const ts=t0+i*3600, x=X(ts);
      ctx.beginPath(); ctx.moveTo(x,26); ctx.lineTo(x,38); ctx.stroke();
      const d=new Date(ts*1000);
      ctx.fillText(`${String(d.getHours()).padStart(2,'0')}`, x+2, 20);
    }
    ctx.strokeStyle='rgba(255,255,255,.09)';
    ctx.beginPath(); ctx.moveTo(0,32); ctx.lineTo(w,32); ctx.stroke();

    const col={info:C.blue,notice:C.amber,warn:'#FF8A3D',critical:C.red};
    events.filter(e=>e.ts>=t0).forEach(e=>{
      const x=X(e.ts), c=col[e.severity]||C.blue;
      const big = e.severity==='critical'||e.severity==='warn';
      ctx.beginPath(); ctx.arc(x,32,big?4:2.6,0,6.2832); ctx.fillStyle=c; ctx.fill();
      if(big){ ctx.beginPath(); ctx.moveTo(x,28); ctx.lineTo(x,10); ctx.strokeStyle=c; ctx.globalAlpha=.5; ctx.stroke(); ctx.globalAlpha=1; }
    });
    // 现在
    ctx.fillStyle=C.amber; ctx.fillRect(w-1.5,8,1.5,30);
  }

  /* ---------------- 抓图缩略（合成） ---------------- */
  function tile(canvas, seed, opts={}){
    const dpr=1;
    const r=canvas.getBoundingClientRect();
    const w=Math.max(80,Math.round(r.width||132)), h=Math.round(w*9/16);
    canvas.width=w*dpr; canvas.height=h*dpr;
    const ctx=canvas.getContext('2d');
    let s=seed>>>0; const rand=()=>((s=(s*1664525+1013904223)>>>0)/4294967296);
    const night = opts.night!=null?opts.night:(rand()>.55);
    const g=ctx.createLinearGradient(0,0,0,h);
    if(night){ g.addColorStop(0,'#0A1512'); g.addColorStop(1,'#050A09'); }
    else     { g.addColorStop(0,'#16323C'); g.addColorStop(1,'#0A171E'); }
    ctx.fillStyle=g; ctx.fillRect(0,0,w,h);
    ctx.strokeStyle = night?'rgba(120,220,190,.14)':'rgba(190,235,255,.16)';
    for(let i=0;i<14;i++){
      const y=h*(0.12+rand()*0.86);
      ctx.beginPath();
      for(let x=0;x<=w;x+=8) ctx.lineTo(x, y+Math.sin(x/9+i)*1.6);
      ctx.stroke();
    }
    if(!night) for(let i=0;i<26;i++){
      ctx.fillStyle=`rgba(255,243,208,${0.08+rand()*0.3})`;
      ctx.fillRect(rand()*w, h*(0.15+rand()*0.8), 1.6, 0.9);
    }
    if(opts.splash){
      ctx.strokeStyle = night?'rgba(190,255,225,.5)':'rgba(235,250,255,.6)';
      const cx=w*(0.3+rand()*0.4), cy=h*(0.4+rand()*0.4);
      for(let k=1;k<=3;k++){ ctx.beginPath(); ctx.arc(cx,cy,k*2.6+rand()*2,0,6.2832); ctx.stroke(); }
    }
    if(opts.person){
      ctx.fillStyle='rgba(255,176,32,.85)';
      const cx=w*(0.35+rand()*0.3), cy=h*0.62;
      ctx.fillRect(cx-1.4, cy-7, 2.8, 9);
      ctx.beginPath(); ctx.arc(cx, cy-9, 1.8, 0, 6.2832); ctx.fill();
      ctx.strokeStyle='rgba(255,176,32,.5)'; ctx.strokeRect(cx-8,cy-14,16,20);
    }
    ctx.font='8px "JetBrains Mono",monospace';
    ctx.fillStyle='rgba(255,255,255,.62)';
    const d=new Date((opts.ts||Date.now()/1000)*1000);
    ctx.fillText(`${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`, 3, h-3.5);
  }

  /* ---------------- 圆环量表 ---------------- */
  function ring(canvas, pct, opts={}){
    const {ctx,w,h}=setup(canvas, opts.height||104);
    const cx=w/2, cy=h/2, R=Math.min(w,h)/2-8;
    ctx.beginPath(); ctx.arc(cx,cy,R,0,6.2832);
    ctx.strokeStyle='#1B2029'; ctx.lineWidth=7; ctx.stroke();
    ctx.beginPath(); ctx.arc(cx,cy,R,-Math.PI/2,-Math.PI/2+6.2832*(pct/100));
    ctx.strokeStyle=opts.color||C.amber; ctx.lineWidth=7; ctx.lineCap='round'; ctx.stroke();
    ctx.fillStyle=C.ink; ctx.font='700 17px "JetBrains Mono",monospace'; ctx.textAlign='center';
    ctx.fillText(`${Math.round(pct)}%`, cx, cy+6);
    if(opts.label){ ctx.fillStyle=C.axis; ctx.font='10px "Noto Sans SC",sans-serif'; ctx.fillText(opts.label, cx, cy+22); }
  }

  return {splash, spark, hbars, timeline, tile, ring};
})();

if (typeof module !== 'undefined') module.exports = Charts;
