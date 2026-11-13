/* ============================================================
   塘口仪表台 · 轻量 Canvas 图表引擎
   零依赖，支持 HiDPI，带绘制入场动画
   ============================================================ */

const PALETTE = {
  signal: '#5BE9A6', amber: '#FFB454', alarm: '#FF5F45',
  cyan: '#45D6E8', lead: '#7C93FF', violet: '#C08BFF',
  foam: '#E6F2ED', mist: '#7C948D', edge: '#1B3830', silt: '#0C1C19',
};

function setupCanvas(cv) {
  const dpr = Math.min(window.devicePixelRatio || 1, 2.5);
  const r = cv.getBoundingClientRect();
  const w = Math.max(r.width, 10), h = Math.max(r.height, 10);
  cv.width = Math.round(w * dpr);
  cv.height = Math.round(h * dpr);
  const ctx = cv.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  return { ctx, w, h };
}

function grid(ctx, w, h, pad, rows = 4, cols = 6) {
  ctx.save();
  ctx.strokeStyle = 'rgba(91,233,166,0.07)';
  ctx.lineWidth = 1;
  for (let i = 0; i <= rows; i++) {
    const y = pad.t + ((h - pad.t - pad.b) * i) / rows;
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(w - pad.r, y); ctx.stroke();
  }
  for (let i = 0; i <= cols; i++) {
    const x = pad.l + ((w - pad.l - pad.r) * i) / cols;
    ctx.beginPath(); ctx.moveTo(x, pad.t); ctx.lineTo(x, h - pad.b); ctx.stroke();
  }
  ctx.restore();
}

/** 多序列折线图，支持阈值带与危险区 */
function lineChart(cv, x, series, opts = {}) {
  const { ctx, w, h } = setupCanvas(cv);
  const pad = opts.pad || { t: 18, r: 46, b: 26, l: 44 };
  const iw = w - pad.l - pad.r, ih = h - pad.t - pad.b;
  const all = series.flatMap((s) => s.data);
  let lo = opts.min !== undefined ? opts.min : Math.min(...all);
  let hi = opts.max !== undefined ? opts.max : Math.max(...all);
  const span = hi - lo || 1; lo -= span * 0.12; hi += span * 0.12;

  const X = (v) => pad.l + ((v - x[0]) / (x[x.length - 1] - x[0] || 1)) * iw;
  const Y = (v) => pad.t + ih - ((v - lo) / (hi - lo)) * ih;

  // 危险区
  (opts.zones || []).forEach((z) => {
    ctx.fillStyle = z.color;
    const y1 = Y(Math.min(z.to, hi)), y2 = Y(Math.max(z.from, lo));
    ctx.fillRect(pad.l, y1, iw, y2 - y1);
  });

  grid(ctx, w, h, pad, 4, 6);

  // 阈值线
  (opts.thresholds || []).forEach((t) => {
    const y = Y(t.v); if (y < pad.t || y > h - pad.b) return;
    ctx.save();
    ctx.strokeStyle = t.color; ctx.lineWidth = 1.2; ctx.setLineDash([5, 4]);
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(w - pad.r, y); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = t.color; ctx.font = '500 9.5px "JetBrains Mono", monospace';
    ctx.textAlign = 'left'; ctx.fillText(t.label, w - pad.r + 5, y + 3.5);
    ctx.restore();
  });

  // 轴标签
  ctx.save();
  ctx.fillStyle = PALETTE.mist; ctx.font = '500 9.5px "JetBrains Mono", monospace';
  ctx.textAlign = 'right';
  for (let i = 0; i <= 4; i++) {
    const v = lo + ((hi - lo) * (4 - i)) / 4;
    ctx.fillText(v.toFixed(opts.decimals ?? 1), pad.l - 7, pad.t + (ih * i) / 4 + 3.5);
  }
  ctx.textAlign = 'center';
  for (let i = 0; i <= 6; i++) {
    const v = x[0] + ((x[x.length - 1] - x[0]) * i) / 6;
    ctx.fillText(`${Math.round(v)}:00`, pad.l + (iw * i) / 6, h - pad.b + 15);
  }
  ctx.restore();

  // 序列
  series.forEach((s, si) => {
    ctx.save();
    ctx.beginPath();
    s.data.forEach((v, i) => (i ? ctx.lineTo(X(x[i]), Y(v)) : ctx.moveTo(X(x[i]), Y(v))));
    ctx.strokeStyle = s.color; ctx.lineWidth = s.width || 1.9;
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    if (s.dash) ctx.setLineDash(s.dash);
    ctx.shadowColor = s.color; ctx.shadowBlur = s.glow === false ? 0 : 9;
    ctx.stroke();
    ctx.restore();

    if (s.fill) {
      const g = ctx.createLinearGradient(0, pad.t, 0, h - pad.b);
      g.addColorStop(0, s.color + '38'); g.addColorStop(1, s.color + '00');
      ctx.save();
      ctx.beginPath();
      s.data.forEach((v, i) => (i ? ctx.lineTo(X(x[i]), Y(v)) : ctx.moveTo(X(x[i]), Y(v))));
      ctx.lineTo(X(x[x.length - 1]), h - pad.b); ctx.lineTo(X(x[0]), h - pad.b); ctx.closePath();
      ctx.fillStyle = g; ctx.fill(); ctx.restore();
    }
  });
}

/** 迷你火花线 */
function sparkline(cv, data, color, opts = {}) {
  const { ctx, w, h } = setupCanvas(cv);
  const lo = Math.min(...data), hi = Math.max(...data), span = hi - lo || 1;
  const X = (i) => (i / (data.length - 1)) * w;
  const Y = (v) => h - 3 - ((v - lo) / span) * (h - 6);

  if (opts.fill !== false) {
    const g = ctx.createLinearGradient(0, 0, 0, h);
    g.addColorStop(0, color + '45'); g.addColorStop(1, color + '00');
    ctx.beginPath();
    data.forEach((v, i) => (i ? ctx.lineTo(X(i), Y(v)) : ctx.moveTo(X(i), Y(v))));
    ctx.lineTo(w, h); ctx.lineTo(0, h); ctx.closePath();
    ctx.fillStyle = g; ctx.fill();
  }
  ctx.beginPath();
  data.forEach((v, i) => (i ? ctx.lineTo(X(i), Y(v)) : ctx.moveTo(X(i), Y(v))));
  ctx.strokeStyle = color; ctx.lineWidth = 1.6; ctx.lineJoin = 'round';
  ctx.shadowColor = color; ctx.shadowBlur = 6; ctx.stroke(); ctx.shadowBlur = 0;

  const lx = X(data.length - 1), ly = Y(data[data.length - 1]);
  ctx.beginPath(); ctx.arc(lx - 1, ly, 2.4, 0, 7); ctx.fillStyle = color; ctx.fill();
}

/** 带不确定度的区间条（不是点估计——这是本项目的界面语言） */
function bandBar(cv, lo, mid, hi, opts = {}) {
  const { ctx, w, h } = setupCanvas(cv);
  const y = h / 2, full = opts.scaleMax || hi * 1.05;
  const X = (v) => (v / full) * (w - 8) + 4;
  ctx.save();
  ctx.strokeStyle = 'rgba(124,148,141,0.22)'; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(4, y); ctx.lineTo(w - 4, y); ctx.stroke();

  const g = ctx.createLinearGradient(X(lo), 0, X(hi), 0);
  g.addColorStop(0, (opts.color || PALETTE.signal) + '30');
  g.addColorStop(1, (opts.color || PALETTE.signal) + '70');
  ctx.fillStyle = g;
  const bw = Math.max(X(hi) - X(lo), 3);
  ctx.beginPath();
  if (ctx.roundRect) ctx.roundRect(X(lo), y - 7, bw, 14, 4); else ctx.rect(X(lo), y - 7, bw, 14);
  ctx.fill();

  ctx.strokeStyle = opts.color || PALETTE.signal; ctx.lineWidth = 1.5;
  [lo, hi].forEach((v) => { ctx.beginPath(); ctx.moveTo(X(v), y - 11); ctx.lineTo(X(v), y + 11); ctx.stroke(); });

  ctx.fillStyle = PALETTE.foam;
  ctx.beginPath(); ctx.arc(X(mid), y, 4.2, 0, 7); ctx.fill();
  ctx.strokeStyle = '#050D0C'; ctx.lineWidth = 2; ctx.stroke();
  ctx.restore();
}

/** 误差传播瀑布图 */
function waterfall(cv, steps) {
  const { ctx, w, h } = setupCanvas(cv);
  const pad = { t: 14, r: 12, b: 44, l: 12 };
  const iw = w - pad.l - pad.r, ih = h - pad.t - pad.b;
  const N = steps.length, gap = 10, bw = (iw - gap * (N - 1)) / N;

  const total = steps[steps.length - 1].value;
  const maxV = Math.max(...steps.map((s) => s.value), total * 1.15);

  steps.forEach((s, i) => {
    const x = pad.l + i * (bw + gap);
    const isTotal = i === N - 1;
    const barH = (s.value / maxV) * ih;
    const y = pad.t + ih - barH;

    const g = ctx.createLinearGradient(0, y, 0, pad.t + ih);
    const base = isTotal ? PALETTE.amber : s.color || PALETTE.cyan;
    g.addColorStop(0, base + 'E6'); g.addColorStop(1, base + '18');
    ctx.fillStyle = g;
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(x, y, bw, barH, 3); else ctx.rect(x, y, bw, barH);
    ctx.fill();

    // 不确定度须
    if (s.lo !== undefined) {
      const yl = pad.t + ih - (s.lo / maxV) * ih, yh = pad.t + ih - (s.hi / maxV) * ih;
      ctx.save();
      ctx.strokeStyle = base + 'AA'; ctx.lineWidth = 1.4;
      ctx.beginPath(); ctx.moveTo(x + bw / 2, yh); ctx.lineTo(x + bw / 2, yl); ctx.stroke();
      [yl, yh].forEach((yy) => { ctx.beginPath(); ctx.moveTo(x + bw / 2 - 5, yy); ctx.lineTo(x + bw / 2 + 5, yy); ctx.stroke(); });
      ctx.restore();
    }

    ctx.fillStyle = isTotal ? PALETTE.amber : PALETTE.foam;
    ctx.font = `600 ${isTotal ? 11 : 10}px "JetBrains Mono", monospace`;
    ctx.textAlign = 'center';
    ctx.fillText(s.value >= 1000 ? Math.round(s.value).toLocaleString() : s.value.toFixed(0), x + bw / 2, y - 6);

    ctx.save();
    ctx.translate(x + bw / 2, pad.t + ih + 8);
    ctx.fillStyle = PALETTE.mist; ctx.font = '500 9px "Noto Sans SC", sans-serif';
    ctx.textAlign = 'right';
    const label = s.label.length > 7 ? s.label.slice(0, 7) : s.label;
    ctx.rotate(-0.55);
    ctx.fillText(label, 0, 0);
    ctx.restore();
  });
}

/** 环形仪表 */
function gauge(cv, pct, opts = {}) {
  const { ctx, w, h } = setupCanvas(cv);
  const cx = w / 2, cy = h * 0.62, r = Math.min(w, h) * 0.42;
  const a0 = Math.PI * 0.82, a1 = Math.PI * 2.18;
  const color = opts.color || PALETTE.signal;

  ctx.save();
  ctx.lineCap = 'round';
  ctx.strokeStyle = 'rgba(124,148,141,0.18)'; ctx.lineWidth = 8;
  ctx.beginPath(); ctx.arc(cx, cy, r, a0, a1); ctx.stroke();

  const ang = a0 + (a1 - a0) * Math.max(0, Math.min(1, pct));
  const g = ctx.createLinearGradient(cx - r, 0, cx + r, 0);
  g.addColorStop(0, color + '66'); g.addColorStop(1, color);
  ctx.strokeStyle = g; ctx.lineWidth = 8;
  ctx.shadowColor = color; ctx.shadowBlur = 12;
  ctx.beginPath(); ctx.arc(cx, cy, r, a0, ang); ctx.stroke();
  ctx.shadowBlur = 0;

  ctx.beginPath(); ctx.arc(cx + Math.cos(ang) * r, cy + Math.sin(ang) * r, 3.6, 0, 7);
  ctx.fillStyle = color; ctx.fill();

  ctx.textAlign = 'center';
  ctx.fillStyle = PALETTE.foam;
  ctx.font = '700 20px "JetBrains Mono", monospace';
  ctx.fillText(opts.value ?? Math.round(pct * 100) + '%', cx, cy - 1);
  ctx.fillStyle = PALETTE.mist;
  ctx.font = '500 9.5px "Noto Sans SC", sans-serif';
  ctx.fillText(opts.label || '', cx, cy + 15);
  ctx.restore();
}

/** 横向对比条 */
function hbar(cv, items) {
  const { ctx, w, h } = setupCanvas(cv);
  const rowH = h / items.length;
  const maxV = Math.max(...items.map((i) => i.value));
  items.forEach((it, i) => {
    const y = i * rowH + rowH / 2;
    const bw = (it.value / maxV) * (w - 150);
    const g = ctx.createLinearGradient(60, 0, 60 + bw, 0);
    g.addColorStop(0, (it.color || PALETTE.cyan) + '44');
    g.addColorStop(1, (it.color || PALETTE.cyan) + 'CC');
    ctx.fillStyle = g;
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(60, y - 7, Math.max(bw, 2), 14, 3); else ctx.rect(60, y - 7, Math.max(bw, 2), 14);
    ctx.fill();

    ctx.fillStyle = PALETTE.mist; ctx.font = '500 10px "Noto Sans SC", sans-serif';
    ctx.textAlign = 'right'; ctx.fillText(it.label, 52, y + 3.5);
    ctx.fillStyle = PALETTE.foam; ctx.font = '600 10.5px "JetBrains Mono", monospace';
    ctx.textAlign = 'left'; ctx.fillText(it.display, 60 + bw + 8, y + 3.5);
  });
}
