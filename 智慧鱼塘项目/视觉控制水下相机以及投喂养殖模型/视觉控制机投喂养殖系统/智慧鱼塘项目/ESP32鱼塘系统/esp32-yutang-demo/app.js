/* ============================================================
   塘口仪表台 · 应用层
   ============================================================ */

const state = {
  view: 'overview',
  scn: 'heat',
  override: null,
  confirmed: false,
  showRaw: false,
};

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const num = (v, d = 0) => Number(v).toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d });
const scn = () => SCENARIOS[state.scn];
const dec = () => buildDecisionChain(scn());

const VIEWS = [
  { k: 'overview', cn: '总览', en: 'Overview', ic: '◈' },
  { k: 'feeding', cn: '投喂决策', en: 'Feeding', ic: '▤' },
  { k: 'water', cn: '水质监测', en: 'Water', ic: '∿' },
  { k: 'vision', cn: '视觉分析', en: 'Vision', ic: '◉' },
  { k: 'ledger', cn: '鱼群与台账', en: 'Ledger', ic: '▦' },
  { k: 'devices', cn: '设备网络', en: 'Devices', ic: '⬡' },
  { k: 'evidence', cn: '证据与红线', en: 'Evidence', ic: '⊘' },
  { k: 'build', cn: '搭建路线与 BOM', en: 'Build', ic: '⚒' },
];

/* ---------- 工具 ---------- */
function gradeChip(g) {
  const d = GRADE[g];
  return `<sup class="grade ${g}" data-tip="<b>证据等级 ${g} · ${d.name}</b><br>${d.desc}">${g}</sup>`;
}

function scnCls() { return scn().tone === 'ok' ? '' : scn().tone === 'warn' ? 'warn' : 'alarm'; }

function verdictFor() {
  const d = dec();
  if (d.clampFactor === 0) return { lo: 0, hi: 0, rec: 0, text: '停喂' };
  return { lo: d.finalLo, hi: d.finalHi, rec: d.recommend, text: null };
}

/* ============================================================
   视图 1 · 总览
   ============================================================ */
function viewOverview() {
  const s = scn(), d = dec(), v = verdictFor();
  const series = makeSeries(s);
  const cls = scnCls();
  const now = currentEnv(s);

  const doNow = now.do_, doMin = s.env.doMin;
  const doState = doMin < 3 ? 'alarm' : doMin < 5.5 ? 'warn' : 'ok';

  return `
  <div class="scn-bar">
    ${Object.values(SCENARIOS).map((x) => `
      <button class="scn ${x.key === state.scn ? 'on ' + (x.tone === 'ok' ? '' : x.tone) : ''}" data-scn="${x.key}">
        <div class="n"><span class="dot ${x.tone}"></span>${x.name}</div>
        <div class="d">${x.desc}</div>
      </button>`).join('')}
  </div>

  <div class="verdict ${cls}">
    <div>
      <div class="eyebrow">今日投喂建议 · 区间非点值</div>
      ${v.text
        ? `<div class="rng">${v.text}<span class="u">全部餐次</span></div>
           <div class="pick">溶氧硬开关触发 —— 系统唯一会<b>自动执行</b>的动作就是"不投"。</div>`
        : `<div class="rng">${v.lo.toFixed(1)} – ${v.hi.toFixed(1)}<span class="u">kg / 餐 × ${d.meals} 餐</span></div>
           <div class="pick">推荐落点 <b>${v.rec.toFixed(1)} kg</b>　·　全日合计 <b>${(v.lo * d.meals).toFixed(0)} – ${(v.hi * d.meals).toFixed(0)} kg</b>　·　需人工确认后下发${gradeChip('C')}</div>`}
      <div class="why">${s.judge}</div>
    </div>
    <div>
      <canvas class="chart chart-160" id="cv-verify"></canvas>
      <div class="legend">
        <span><i style="background:${PALETTE.signal}"></i>基线（生物量 × 投饲率）</span>
        <span><i style="background:${cls === 'alarm' ? PALETTE.alarm : cls === 'warn' ? PALETTE.amber : PALETTE.signal}"></i>安全钳制后</span>
      </div>
    </div>
  </div>

  <div class="grid g4" style="margin-top:16px">
    <div class="card tight">
      <div class="kpi-label">存塘尾数 N</div>
      <div class="readout mid">7,450<span class="u">尾</span></div>
      <div class="range-txt">区间 5,210 – 8,940</div>
      <canvas class="spark" id="sp-n"></canvas>
      <div class="kpi-sub">台账推算，非实测${gradeChip('B')}<br>误差 ±20–50% —— 这是误差漏斗的源头</div>
    </div>
    <div class="card tight">
      <div class="kpi-label">生物量 B = N × w</div>
      <div class="readout mid">${num(d.Bmid)}<span class="u">kg</span></div>
      <div class="range-txt">区间 ${num(d.Blo)} – ${num(d.Bhi)}</div>
      <div class="kpi-sub">下游一切建议的宽度都由这一行决定${gradeChip('B')}</div>
    </div>
    <div class="card tight">
      <div class="kpi-label">水温 · 此刻</div>
      <div class="readout mid" style="color:${s.env.tempMax > 32 ? PALETTE.amber : PALETTE.foam}">${now.temp}<span class="u">℃</span></div>
      <div class="range-txt">日最高 ${s.env.tempMax} · 修正 f_T = ${d.fT.toFixed(2)}</div>
      <canvas class="spark" id="sp-t"></canvas>
      <div class="kpi-sub">三层水温链：表 / 中 / 底${gradeChip('A')}<br>决策用的是<b style="color:var(--mist)">日最高</b>，不是此刻值</div>
    </div>
    <div class="card tight">
      <div class="kpi-label">溶氧 · 此刻</div>
      <div class="readout mid" style="color:${doState === 'alarm' ? PALETTE.alarm : doState === 'warn' ? PALETTE.amber : PALETTE.signal}">${doNow}<span class="u">mg/L</span></div>
      <div class="range-txt">夜最低 ${doMin} · 硬阈值 5 / 3</div>
      <canvas class="spark" id="sp-do"></canvas>
      <div class="kpi-sub">⭐ 全系统性价比最高的一笔投入${gradeChip('B')}<br>决策用的是<b style="color:var(--mist)">夜最低</b>，不是此刻值</div>
    </div>
  </div>

  <div class="grid g2" style="margin-top:14px">
    <div class="card">
      <div class="card-h"><h3>溶氧日变化曲线 · 24 小时</h3><span class="en">DO / 24h</span></div>
      <canvas class="chart chart-200" id="cv-do"></canvas>
      <div class="note" style="margin-top:12px">
        溶氧在<b style="color:var(--foam)">凌晨 5–7 点触底</b>——这正是泛塘的时间窗口。
        系统按"夜最低值"而非"当前值"做安全判定，因为决策发生在白天，而风险发生在夜里。
      </div>
    </div>

    <div class="card">
      <div class="card-h"><h3>塘口与节点布设</h3><span class="en">Pond · Nodes</span></div>
      <div class="mapwrap">${pondSVG()}</div>
      <div class="legend" style="margin-top:12px">
        <span><i style="background:${PALETTE.signal}"></i>正常</span>
        <span><i style="background:${PALETTE.amber}"></i>告警</span>
        <span><i style="background:${PALETTE.cyan}"></i>投料点</span>
      </div>
      <div class="kpi-sub" style="margin-top:10px">
        GPS 定位 ${POND.gps.lat.toFixed(4)}°N ${POND.gps.lng.toFixed(4)}°E · 精度 ±${POND.gps.accM} m${gradeChip('A')}
        <br><span style="color:var(--dim)">固定塘口场景下 GPS 的作用是<b style="color:var(--mist)">资产登记与多塘口区分</b>，不是决策输入。</span>
      </div>
    </div>
  </div>

  <div class="grid g3" style="margin-top:14px">
    ${[
      { t: '主动作是"减"，不是"加"', d: '系统可以自动执行"停喂"，但任何"加喂"都必须经人工确认。风险不对称：投喂不足是温和的错，投喂过量可能一夜死塘。', c: 'signal' },
      { t: '每个数字都带等级标', d: 'A = 本塘实测/同行评议，B = 经验值待校准，C = 演示值。悬停任意角标看它的来源与局限。', c: 'cyan' },
      { t: '空白就是空白', d: '没有可靠来源的数值，界面显示"无数据"。不许用近似品种的通用值填充——一旦开始合理推测，系统就变成了自信的胡说机器。', c: 'amber' },
    ].map((x) => `
      <div class="card tight">
        <div class="kpi-label" style="color:var(--${x.c})">${x.t}</div>
        <div class="kpi-sub" style="margin-top:0">${x.d}</div>
      </div>`).join('')}
  </div>`;
}

function pondSVG() {
  const nodes = [
    { x: 74, y: 40, l: 'N01', s: 'ok' }, { x: 168, y: 118, l: 'N02', s: 'ok' },
    { x: 262, y: 52, l: 'N03', s: 'ok' }, { x: 318, y: 132, l: 'N04', s: 'warn' },
    { x: 130, y: 172, l: 'N05', s: 'ok' }, { x: 240, y: 196, l: 'N06', s: 'ok' },
  ];
  const col = { ok: PALETTE.signal, warn: PALETTE.amber };
  return `
  <svg viewBox="0 0 400 240" style="display:block;width:100%;height:auto">
    <defs>
      <linearGradient id="wg" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#123832"/><stop offset="100%" stop-color="#07130F"/>
      </linearGradient>
      <pattern id="rip" width="26" height="26" patternUnits="userSpaceOnUse">
        <path d="M0 13 Q6.5 8 13 13 T26 13" fill="none" stroke="rgba(91,233,166,.07)" stroke-width="1"/>
      </pattern>
    </defs>
    <rect x="18" y="26" width="330" height="192" rx="30" fill="url(#wg)" stroke="rgba(91,233,166,.22)"/>
    <rect x="18" y="26" width="330" height="192" rx="30" fill="url(#rip)"/>
    <!-- 投料点扇形 -->
    <path d="M318 132 L228 96 A118 118 0 0 1 246 178 Z" fill="rgba(69,214,232,.14)" stroke="rgba(69,214,232,.4)" stroke-dasharray="4 3"/>
    <text x="300" y="152" fill="${PALETTE.cyan}" font-family="JetBrains Mono" font-size="8">抛撒扇面</text>
    <!-- 岸线设备屋 -->
    <rect x="24" y="32" width="42" height="26" rx="3" fill="rgba(255,180,84,.12)" stroke="rgba(255,180,84,.4)"/>
    <text x="45" y="49" fill="${PALETTE.amber}" font-family="JetBrains Mono" font-size="7.5" text-anchor="middle">设备屋</text>
    <line x1="66" y1="45" x2="358" y2="45" stroke="rgba(124,148,141,.25)" stroke-dasharray="3 4"/>
    <text x="212" y="41" fill="${PALETTE.dim || '#4E6560'}" font-family="Noto Sans SC" font-size="7.5" text-anchor="middle">岸线 · 太阳能板朝南 30°</text>
    ${nodes.map((n) => `
      <g>
        <circle cx="${n.x}" cy="${n.y}" r="11" fill="${col[n.s]}22" stroke="${col[n.s]}" stroke-width="1.2"/>
        <circle cx="${n.x}" cy="${n.y}" r="3.2" fill="${col[n.s]}"/>
        <text x="${n.x}" y="${n.y + 22}" fill="${col[n.s]}" font-family="JetBrains Mono" font-size="8" text-anchor="middle">${n.l}</text>
      </g>`).join('')}
    <!-- 无线链路 -->
    ${[[74, 40, 168, 118], [74, 40, 262, 52], [74, 40, 130, 172], [74, 40, 240, 196], [262, 52, 318, 132]].map(([a, b, c, dd]) =>
      `<line x1="${a}" y1="${b}" x2="${c}" y2="${dd}" stroke="rgba(91,233,166,.2)" stroke-width=".9" stroke-dasharray="2 4"/>`).join('')}
    <!-- 采样点 -->
    <circle cx="150" cy="150" r="4" fill="none" stroke="rgba(192,139,255,.7)" stroke-dasharray="2 2"/>
    <text x="150" y="141" fill="${PALETTE.violet}" font-family="JetBrains Mono" font-size="7" text-anchor="middle">打网点</text>
    <text x="200" y="212" fill="#4E6560" font-family="JetBrains Mono" font-size="7.5" text-anchor="middle">8 亩 · 平均水深 1.8 m · 约 ${num(POND.volumeM3 / 1000, 0)} 千 m³</text>
  </svg>`;
}

/* ============================================================
   视图 2 · 投喂决策
   ============================================================ */
function viewFeeding() {
  const s = scn(), d = dec(), v = verdictFor();
  const cls = scnCls();
  const step = state.override ?? (v.text ? 0 : v.rec);

  return `
  <div class="sect-title">投喂决策链</div>
  <div class="sect-desc">
    决策不是"算一个数"，而是<b style="color:var(--foam)">六个环节的串联，每一环都放大误差，最后一环用非对称钳制收口</b>。
    下面每一步都给出：值 · 区间 · 怎么来的 · 有什么局限。点任意角标看证据等级。
  </div>

  <div class="grid g2" style="align-items:start">
    <div class="card">
      <div class="card-h"><h3>决策链 · 逐环拆解</h3><span class="en">Chain</span></div>
      <div class="chain">
        ${d.params.map((p, i) => `
          <div class="step">
            <div class="idx">${String(i + 1).padStart(2, '0')}</div>
            <div>
              <div class="k">${p.key}${gradeChip(p.grade)}</div>
              <div class="v">${p.value}${p.range !== '—' ? ` <span class="range-txt">区间 ${p.range}</span>` : ''}</div>
              <div class="how">${p.how}</div>
              <div class="note">${p.note}</div>
            </div>
          </div>`).join('')}
        <div class="step">
          <div class="idx">07</div>
          <div>
            <div class="k">安全钳制（非对称）${gradeChip('B')}</div>
            <div class="v">× ${d.clampFactor.toFixed(2)}
              <span class="range-txt">${d.clampFactor === 1 ? '未触发' : d.clampFactor === 0 ? '硬开关' : '主动下调'}</span></div>
            <div class="how">溶氧 / 水温 / 天气三条规则取最严者</div>
          </div>
        </div>
        <div class="step">
          <div class="idx">08</div>
          <div>
            <div class="k">人工历史上限封顶${gradeChip('B')}</div>
            <div class="v">${d.hardCap.toFixed(1)} kg/餐
              <span class="range-txt">= 历史最大 ${(d.hardCap / 1.1).toFixed(0)} kg × 110%${d.capped ? ' · 已生效' : ''}</span></div>
            <div class="how">任何情况下不得超过人工历史上限的 110%</div>
          </div>
        </div>
        <div class="step">
          <div class="idx">09</div>
          <div>
            <div class="k">保守默认（宁可低估）${gradeChip('B')}</div>
            <div class="v">× 0.82</div>
            <div class="how">数据缺失或不确时一律向下取。杂交黄颡鱼春季投喂率压到 0.5% 后，存活率 90.00% → 99.44%</div>
          </div>
        </div>
      </div>
    </div>

    <div style="display:flex;flex-direction:column;gap:14px">
      <div class="verdict ${cls}" style="grid-template-columns:1fr;padding:20px 22px">
        <div>
          <div class="eyebrow">${s.name} · 最终建议</div>
          ${v.text
            ? `<div class="rng">停喂</div>`
            : `<div class="rng">${v.lo.toFixed(1)} – ${v.hi.toFixed(1)}<span class="u">kg / 餐</span></div>`}
          <div class="pick">
            基线（钳制前）<b>${d.baselinePerMeal.toFixed(1)} kg/餐</b>　→　钳制系数 <b>${d.clampFactor.toFixed(2)}</b>
            ${d.clampFactor !== 1 ? `　→　变化 <b style="color:${cls === 'alarm' ? 'var(--alarm)' : 'var(--amber)'}">${(((d.clampFactor - 1) * 100)).toFixed(0)}%</b>` : ''}
          </div>
          <div class="why">${s.judge}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-h"><h3>触发规则</h3><span class="en">Clamps</span></div>
        ${s.clampNotes.length ? s.clampNotes.map((c) => `
          <div class="rule">
            <span class="tag ${s.tone === 'alarm' ? 'alarm' : 'amber'}">${c.action}</span>
            <div class="body">
              <div class="t">${c.rule}</div>
              <div class="d">${c.detail}</div>
            </div>
            <span></span>
          </div>`).join('')
          : `<div class="rule"><span class="tag signal">通过</span><div class="body"><div class="t">全部安全门通过</div><div class="d">溶氧 ≥ 5.5 mg/L、水温 ≤ 30 ℃、无天气预警。基线即为建议。</div></div><span></span></div>`}
        <div class="note" style="margin-top:14px">
          <b style="color:var(--foam)">不对称风险原则</b>：投喂不足只是"长得慢"（温和的错）；投喂过量可能"一夜死塘"（致命的错）。
          且过量投喂是自催化灾难：残饵 → 耗氧 + 氨氮飙升 → 水质崩溃 → 缺氧泛塘。
        </div>
      </div>

      <div class="card">
        <div class="card-h"><h3>执行端 · 人工确认</h3><span class="en">Human-in-the-loop</span></div>
        <div class="readout mid" style="text-align:center;margin:6px 0 2px" id="ov-val">${step.toFixed(1)}<span class="u">kg / 餐</span></div>
        <input type="range" id="ov" min="0" max="${Math.ceil(v.hi || 40)}" step="0.5" value="${step.toFixed(1)}"
               ${v.text ? 'disabled' : ''}>
        <div style="display:flex;justify-content:space-between" class="range-txt">
          <span>0</span><span>建议上限 ${v.hi.toFixed(1)}</span><span>${Math.ceil(v.hi || 40)} kg</span>
        </div>
        <div class="kpi-sub" id="ov-hint" style="margin-top:12px">
          ${v.text ? '硬开关触发期间，滑块被禁用——这是系统唯一不允许人工绕过的规则。'
                   : '你可以在区间外调整，但超出建议上限的操作会被记录，并作为下一轮评估的输入。人工修改本身就是最有价值的学习信号。'}
        </div>
        <div style="display:flex;gap:10px;margin-top:16px">
          <button class="btn" id="btn-confirm" ${v.text ? 'disabled' : ''}>${state.confirmed ? '已下发 · 可重发' : '人工确认并下发'}</button>
          <button class="btn ghost" id="btn-reset">复位</button>
        </div>
        <div id="exec-log" style="margin-top:14px"></div>
      </div>
    </div>
  </div>

  <div class="card" style="margin-top:14px">
    <div class="card-h"><h3>执行端标定表（B4 协议 · 示意）</h3><span class="en">Calibration</span></div>
    <div class="sect-desc" style="margin-bottom:14px;font-size:12px">
      <b style="color:var(--foam)">"开 T 秒 = 投出固定重量"在真实设备上不成立</b>，开环误差量级 ±5%–20%，
      主导项是<b style="color:var(--foam)">启停瞬态 5–18%</b> 与 <b style="color:var(--foam)">1 秒时间量化 4–9%</b>，
      不是稳态容积误差 2–5%。标定判据：<b style="color:var(--signal)">全表 CV ≤ 10% 且死区稳定 → 终身不上称重</b>。
      10% 不是精度目标，是性价比截止线。
    </div>
    <div class="tbl-wrap"><table class="tbl">
      <thead><tr><th>粒径档</th><th>料位</th><th>电压</th><th>出料速率 g/s</th><th>CV</th><th>启动死区 s</th><th>20 次重复</th><th>判据</th></tr></thead>
      <tbody>
      ${[
        ['标称 2.0 mm', '高', '额定', '42.6', '4.1%', '0.62', '✅', 'pass'],
        ['标称 2.0 mm', '中', '额定', '40.9', '5.3%', '0.71', '✅', 'pass'],
        ['标称 2.0 mm', '低', '额定', '38.2', '6.8%', '0.94', '✅', 'pass'],
        ['标称 3.0 mm', '高', '额定', '44.1', '3.9%', '0.55', '✅', 'pass'],
        ['标称 3.0 mm', '中', '−10%', '38.7', '7.4%', '0.88', '✅', 'pass'],
        ['标称 3.0 mm', '低', '−10%', '34.4', '11.2%', '1.31', '⚠️', 'fail'],
        ['实测筛分 4.0 mm', '中', '额定', '46.3', '9.6%', '0.66', '✅', 'pass'],
        ['实测筛分 4.0 mm', '低', '−10%', '36.1', '13.7%', '1.52', '❌', 'fail'],
      ].map((r) => `<tr>
        <td class="num">${r[0]}</td><td>${r[1]}</td><td class="num">${r[2]}</td>
        <td class="num">${r[3]}</td><td class="num" style="color:${parseFloat(r[4]) > 10 ? 'var(--alarm)' : 'var(--signal)'}">${r[4]}</td>
        <td class="num">${r[5]}</td><td>${r[6]}</td>
        <td><span class="chip ${r[7] === 'pass' ? 'ok' : 'alarm'}">${r[7] === 'pass' ? '通过' : '超判据'}</span></td>
      </tr>`).join('')}
      <tr style="background:rgba(255,95,69,.05)">
        <td colspan="8" style="color:var(--alarm);font-size:11.5px">
          ⚠️ 2 / 8 组合 CV &gt; 10% —— 按 B4 协议，<b>低料位 + 欠压</b> 区间需上小量程称量桶（增量法），
          或在操作手册中禁止该工况投喂。整仓称重是算术陷阱：100 kg 料仓 + 3000 分度 → 投 500 g 一次分辨率 ±6.6%，比开环还差。
        </td>
      </tr>
      </tbody>
    </table></div>
  </div>`;
}

/* ============================================================
   视图 3 · 水质监测
   ============================================================ */
function viewWater() {
  const s = scn(), series = makeSeries(s), now = currentEnv(s);
  const doState = s.env.doMin < 3 ? 'alarm' : s.env.doMin < 5.5 ? 'warn' : 'ok';
  const alerts = [
    s.env.doMin < 3 && { lvl: 'alarm', t: '溶氧跌破硬阈值', d: `夜最低 ${s.env.doMin} mg/L < 3 mg/L。已自动停喂并联动增氧机。`, time: '05:10' },
    s.env.doMin < 5.5 && s.env.doMin >= 3 && { lvl: 'warn', t: '溶氧进入观察带', d: `夜最低 ${s.env.doMin} mg/L，高于硬阈值但风险窗口在后半夜。建议提前 1 小时开增氧机。`, time: '05:10' },
    s.env.tempMax > 32 && { lvl: 'warn', t: '水温越限', d: `日最高 ${s.env.tempMax} ℃ > 32 ℃。已触发"只减不增"钳制。`, time: '15:05' },
    s.env.airHpa < 1005 && { lvl: 'warn', t: '气压偏低 · 闷热', d: `${s.env.airHpa} hPa，气压是比水温更早的泛塘前兆。`, time: '13:40' },
    { lvl: 'warn', t: 'N04 镜头污损', d: '清晰度指标低于阈值，上次清洁 11 天前。历史系统中 24% 的误分类来自相机维护不良。', time: '08:12' },
    { lvl: 'info', t: '采样偏差提示', d: '本塘浊度 38 NTU，视觉模块今日置信度已自动下调。', time: '06:00' },
  ].filter(Boolean);

  return `
  <div class="sect-title">水质监测</div>
  <div class="sect-desc">
    溶氧是<b style="color:var(--foam)">防死变量</b>，比增产变量重要得多。这一页的所有阈值都来自 ESP32 传感节点，
    并以"夜最低值"而非"当前值"参与决策——因为决策发生在白天，而风险发生在夜里。
  </div>

  <div class="banner">
    <span class="icon">⚠</span>
    <span class="txt">
      <b>阈值待校准声明：</b>溶氧 5 / 3 mg/L 是传统经验值，尚未用本塘数据校准。
      P1 阶段的核心任务就是用便携溶氧仪人工"四测定"（水温 / 透明度 / pH / 溶氧）连续跑两周，
      建立本塘溶氧日变化曲线，再回填这两个数。在那之前，安全门只能算"保守可用"。
    </span>
  </div>

  <div class="grid g4">
    ${[
      { l: '溶解氧 · 此刻', v: now.do_, u: 'mg/L', st: doState, sub: `夜最低 ${s.env.doMin} · 日峰值 ${s.env.doMax}`, key: 'do' },
      { l: '水温 · 此刻', v: now.temp, u: '℃', st: s.env.tempMax > 32 ? 'warn' : 'ok', sub: `日最高 ${s.env.tempMax} · 日最低 ${s.env.tempMin}`, key: 'temp' },
      { l: 'pH', v: now.ph, u: '', st: 'ok', sub: '日较差正常范围 0.3–0.6' },
      { l: '浊度', v: now.turb, u: 'NTU', st: s.env.turbidityNtu > 50 ? 'warn' : 'ok', sub: `透明度约 ${(400 / s.env.turbidityNtu).toFixed(0)} cm` },
    ].map((x) => `
      <div class="card tight">
        <div class="kpi-label">${x.l}</div>
        <div class="readout mid" style="color:${x.st === 'alarm' ? 'var(--alarm)' : x.st === 'warn' ? 'var(--amber)' : 'var(--foam)'}">
          ${x.v}<span class="u">${x.u}</span></div>
        <div class="range-txt">${x.sub}</div>
        ${x.key ? `<canvas class="spark" id="wsp-${x.key}"></canvas>` : ''}
      </div>`).join('')}
  </div>

  <div class="grid g2" style="margin-top:14px;align-items:start">
    <div class="card" style="grid-column:span 2">
      <div class="card-h"><h3>溶氧 · 水温 · 24 小时联动</h3><span class="en">DO / Temp</span></div>
      <canvas class="chart chart-240" id="cv-main"></canvas>
      <div class="legend">
        <span><i style="background:${PALETTE.cyan}"></i>溶解氧 mg/L</span>
        <span><i style="background:${PALETTE.amber}"></i>水温 ℃</span>
        <span><i style="background:rgba(255,95,69,.5)"></i>缺氧风险区 &lt; 3</span>
        <span><i style="background:rgba(255,180,84,.4)"></i>观察带 3–5</span>
      </div>
      <div class="note" style="margin-top:14px">
        <b style="color:var(--foam)">读法：</b>溶氧曲线与水温曲线相位相反——水温午后达峰，溶氧凌晨触底。
        这个"反相位"是藻类光合作用与呼吸作用的直接结果，也是为什么<b style="color:var(--foam)">只看白天溶氧会严重低估夜间风险</b>。
      </div>
    </div>

    <div class="card">
      <div class="card-h"><h3>pH · 浊度</h3><span class="en">pH / Turbidity</span></div>
      <canvas class="chart chart-200" id="cv-ph"></canvas>
      <div class="legend">
        <span><i style="background:${PALETTE.violet}"></i>pH</span>
        <span><i style="background:${PALETTE.lead}"></i>浊度 NTU</span>
      </div>
      <div class="note" style="margin-top:12px">
        浊度不只是水质指标——它是<b style="color:var(--foam)">"视觉模块今天是否可信"的开关</b>。
        浊度越高，摄像头能拿到的信息越少，系统会自动下调视觉结论的权重。
      </div>
    </div>

    <div class="card">
      <div class="card-h"><h3>告警列表</h3><span class="en">Alerts</span></div>
      ${alerts.map((a) => `
        <div class="rule">
          <span class="tag ${a.lvl === 'alarm' ? 'alarm' : a.lvl === 'warn' ? 'amber' : 'signal'}">${a.lvl === 'alarm' ? '严重' : a.lvl === 'warn' ? '关注' : '信息'}</span>
          <div class="body"><div class="t">${a.t}</div><div class="d">${a.d}</div></div>
          <span class="range-txt">${a.time}</span>
        </div>`).join('')}
    </div>
  </div>

  <div class="card" style="margin-top:14px">
    <div class="card-h"><h3>为什么溶氧必须是在线探头，而不是便携仪</h3><span class="en">Why online</span></div>
    <div class="grid g3" style="gap:18px">
      <div>
        <div class="kpi-label" style="color:var(--signal)">风险窗口在后半夜</div>
        <div class="kpi-sub" style="margin-top:0">溶氧最低点出现在凌晨 5–7 点。人工"四测定"不可能每天这时候到塘边，而泛塘恰恰发生在这个窗口。</div>
      </div>
      <div>
        <div class="kpi-label" style="color:var(--amber)">但一期先用便携仪</div>
        <div class="kpi-sub" style="margin-top:0">在线荧光法探头 900–1,600 元，且要处理校准与生物污损。先用便携仪（200–500 元）跑两周把阈值和曲线搞明白，再决定买不买。</div>
      </div>
      <div>
        <div class="kpi-label" style="color:var(--cyan)">两条曲线必须能对上</div>
        <div class="kpi-sub" style="margin-top:0">上线后依然要每周用便携仪交叉校验一次。在线探头会漂移，你必须有第二把尺子——否则"传感器说没事"就成了新的盲区。</div>
      </div>
    </div>
  </div>`;
}

/* ============================================================
   视图 4 · 视觉分析
   ============================================================ */
function viewVision() {
  const g = VISION.geometry;
  const gsd = (2 * g.camH * Math.tan((g.fovDeg / 2) * Math.PI / 180) * 1000) / g.pxWidth;
  const px = g.pelletMM / gsd;

  return `
  <div class="sect-title">视觉分析 · 以及它做不到什么</div>
  <div class="sect-desc">
    这一页故意把<b style="color:var(--alarm)">"不能做"放在"能做"前面</b>。摄像头是全项目唯一没有对照验证的一条链路，
    却是最容易被当成"AI 亮点"先做的一条。先把边界画清楚，再谈它能贡献什么。
  </div>

  <div class="grid g2" style="align-items:start">
    <div class="card" style="border-color:rgba(255,95,69,.28)">
      <div class="card-h"><h3 style="color:var(--alarm)">❌ 明确不做</h3><span class="en">Cannot do</span></div>
      ${VISION.cannotDo.map((x) => `
        <div class="verdict-item cant-v">
          <div class="v">${x.v}</div>
          <div><div class="k">${x.k}</div><div class="w">${x.why}</div></div>
        </div>`).join('')}
    </div>

    <div class="card" style="border-color:var(--edge-2)">
      <div class="card-h"><h3 style="color:var(--signal)">✅ 可做 · 且这是它唯一进入决策链的用途</h3><span class="en">Can do</span></div>
      ${VISION.canDo.map((x) => `
        <div class="verdict-item can-v">
          <div class="v">${x.v}</div>
          <div><div class="k">${x.k}</div><div class="w">${x.why}</div></div>
        </div>`).join('')}
    </div>
  </div>

  <div class="card" style="margin-top:14px;background:linear-gradient(160deg,rgba(37,18,16,.5),rgba(8,21,19,.5));border-color:rgba(255,95,69,.22)">
    <div class="card-h"><h3>"数残饵颗粒"的几何否决 · 现场演算</h3><span class="en">Geometry</span></div>
    <div class="grid g4" style="margin-bottom:16px">
      ${[
        { l: '相机高度', v: g.camH, u: 'm' },
        { l: '水平视场角', v: g.fovDeg, u: '°' },
        { l: '画面宽度', v: g.pxWidth, u: 'px' },
        { l: '地面采样距离', v: gsd.toFixed(2), u: 'mm/px', hl: true },
      ].map((x) => `
        <div>
          <div class="kpi-label">${x.l}</div>
          <div class="readout mid" style="color:${x.hl ? 'var(--amber)' : 'var(--foam)'}">${x.v}<span class="u">${x.u}</span></div>
        </div>`).join('')}
    </div>
    <div class="quote">
      一粒 ${g.pelletMM} mm 的饲料在画面上占 <b style="color:var(--alarm)">${px.toFixed(2)} 个像素</b>，
      而颗粒检测的经验门槛是 <b style="color:var(--foam)">&gt; ${g.thresholdPx} 像素</b>。
      相差约 <b style="color:var(--alarm)">${Math.round(g.thresholdPx / px)} 倍</b>。
    </div>
    <div class="note" style="margin-top:14px">
      要让 3 mm 颗粒达到 30 像素，镜头只能覆盖 <b style="color:var(--foam)">约 1 米宽</b>的水面——
      那是料台近距拍摄，不是塘面全景。已发表的残饵检测高精度（mAP@0.5 95.7%）用的都是<b style="color:var(--foam)">水下近距相机</b>。
      <br><br>
      <b style="color:var(--amber)">所以本系统对残饵的判据是：</b>投喂后人工食台剩料计时（1 分钟/餐，吃食 3h 正常 / 2h 不足 / 4h 过多），
      或进阶档的<b style="color:var(--foam)">料台 + 近距相机</b>（文献 MAE 2.0 粒）。<b style="color:var(--alarm)">不是塘面全景相机。</b>
    </div>
  </div>

  <div class="card" style="margin-top:14px">
    <div class="card-h"><h3>如果坚持要定量：三条路径与它们的真实代价</h3><span class="en">If you must quantify</span></div>
    <div class="sect-desc" style="font-size:12.5px">
      下面三条是<b style="color:var(--foam)">目前有可溯源证据</b>的定量路径。注意它们的共同点：
      精度最好的也只有 85–92%，且给的是<b style="color:var(--foam)">"体量/密度"而非逐尾计数</b>。
      「±10% 绝对尾数」在 2025–2026 年的技术条件下不可达。
    </div>
    <div class="grid g3" style="align-items:stretch">
      ${VISION.ifMustQuantify.map((x) => `
        <div class="card tight" style="background:rgba(12,28,25,.55)">
          <div class="kpi-label" style="color:var(--cyan)">${x.p}</div>
          <div style="font-family:var(--serif);font-weight:700;font-size:15px;margin-bottom:8px">${x.n}</div>
          <div class="readout mid" style="color:var(--amber)">${x.acc}</div>
          <div class="range-txt" style="margin-bottom:9px">${x.err}</div>
          <div class="kpi-sub" style="margin-top:0">${x.note}</div>
          <div class="kpi-sub" style="margin-top:9px;padding-top:9px;border-top:1px dashed var(--edge);color:var(--dim)">
            ${x.src}${gradeChip(x.grade)}</div>
        </div>`).join('')}
    </div>
  </div>

  <div class="card" style="margin-top:14px;border-color:rgba(192,139,255,.25)">
    <div class="card-h"><h3 style="color:var(--violet)">⛔ 为什么 ESP32 不能自己跑鱼类识别</h3><span class="en">Edge AI limits</span></div>
    <div class="grid g2" style="align-items:start">
      <div>
        <div class="kpi-label">乐鑫官方 esp-dl benchmark（ESP32-S3）${gradeChip('A')}</div>
        <table class="tbl" style="margin-top:8px">
          <thead><tr><th>模型</th><th>单帧耗时</th><th>帧率</th></tr></thead>
          <tbody>${VISION.edgeAI.bench.map((b) => {
            const slow = parseFloat(b.fps) < 2;
            return `<tr>
              <td class="em">${b.m}</td>
              <td class="num">${b.v}</td>
              <td class="num" style="color:${slow ? 'var(--alarm)' : 'var(--signal)'}">${b.fps}</td>
            </tr>`;
          }).join('')}</tbody>
        </table>
        <div class="range-txt" style="margin-top:8px">${VISION.edgeAI.src}</div>
        <div class="note" style="margin-top:12px">
          连 <b style="color:var(--foam)">MobileNetV2 分类</b>都只有 1.14 FPS。
          S3 真正能用的是<b style="color:var(--signal)">人脸检测 26.9 FPS、单类目标 @224 约 7.8 FPS</b>——
          也就是"有没有鱼"这个量级，不是"有几条鱼"。
        </div>
      </div>
      <div>
        <div class="kpi-label" style="color:var(--alarm)">"ESP32 做鱼类识别"零实证${gradeChip('A')}</div>
        <div class="kpi-sub" style="margin-top:0">${VISION.edgeAI.zeroEvidence}</div>
        <div class="banner" style="margin-top:14px;margin-bottom:0">
          <span class="icon">▸</span>
          <span class="txt">${VISION.edgeAI.architecture}</span>
        </div>
      </div>
    </div>
  </div>

  <div class="grid g2" style="margin-top:14px;align-items:start">
    <div class="card">
      <div class="card-h"><h3>摄食强度分级 · 今日三餐饮</h3><span class="en">Intensity</span></div>
      <table class="tbl">
        <thead><tr><th>餐次</th><th>分级</th><th>分数</th><th>置信度</th><th>吃食时长</th></tr></thead>
        <tbody>
        ${VISION.intensity.map((r) => {
          const c = r.score > 0.75 ? PALETTE.signal : r.score > 0.5 ? PALETTE.amber : PALETTE.alarm;
          return `<tr>
            <td class="num">${r.meal}</td>
            <td><span class="chip ${r.score > 0.75 ? 'ok' : 'warn'}">${r.level}</span></td>
            <td class="num" style="color:${c}">${r.score.toFixed(2)}</td>
            <td class="num">${(r.conf * 100).toFixed(0)}%</td>
            <td class="num">${r.intakeMin} min</td>
          </tr>`;
        }).join('')}
        </tbody>
      </table>
      <div style="margin-top:14px">
        ${VISION.intensity.map((r) => `<div class="note" style="margin-bottom:8px"><b style="color:var(--foam)">${r.meal}</b> — ${r.note}</div>`).join('')}
      </div>
    </div>

    <div class="card">
      <div class="card-h"><h3>它的输出如何进入决策</h3><span class="en">In the loop</span></div>
      <canvas class="chart chart-200" id="cv-act"></canvas>
      <div class="legend">
        <span><i style="background:${PALETTE.signal}"></i>摄食活动指数</span>
        <span><i style="background:${PALETTE.mist}"></i>投喂时刻</span>
      </div>
      <div class="note" style="margin-top:14px">
        判据是<b style="color:var(--foam)">响应区间的长度变化</b>，不是绝对强度。
        今天晚餐的摄食响应区间比早餐缩短 21%——这是"食欲衰退趋势"信号，
        系统据此把当日剩余餐次的目标量下调，并提示次日复核。
      </div>
      <div class="banner red" style="margin-top:16px;margin-bottom:0">
        <span class="icon">⛔</span>
        <span class="txt">
          <b>视觉模块永远不能单独决定加量。</b>它只能"叫停"或"下调"。
          视觉误判以"以为还在吃"的假阳性为主，因此必须保留量控上限 + 溶氧硬开关兜底。
          另外——用<b>人工观察</b>标注训练的摄食强度模型，比用光流自动标注训练的模型低 13.13–18.46 个百分点。
          <b>你打算标的数据，本身可能就不可靠。</b>
        </span>
      </div>
    </div>
  </div>`;
}

/* ============================================================
   视图 5 · 鱼群与台账
   ============================================================ */
function viewLedger() {
  const d = dec();
  const steps = [
    { label: '放养尾数', value: POND.stockedFry, color: PALETTE.mist },
    { label: '死亡 −', value: 310, color: PALETTE.alarm },
    { label: '出塘 −', value: 240, color: PALETTE.amber },
    { label: '估算 N', value: 7450, lo: 5210, hi: 8940, color: PALETTE.cyan },
    { label: '× 均重', value: 4358, lo: 2668, hi: 5936, color: PALETTE.lead },
    { label: '生物量 kg', value: 4358, lo: 2668, hi: 5936, color: PALETTE.amber },
  ];

  return `
  <div class="sect-title">鱼群与台账</div>
  <div class="sect-desc">
    <b style="color:var(--foam)">四本账是地基，传感器是辅助。</b>
    批次台账、投喂记录、死亡记录、出塘记录——这四项都是<b style="color:var(--signal)">零硬件成本的"记录习惯"问题，不是技术问题</b>。
    真正的瓶颈不是模型，是数据采集纪律。
  </div>

  <div class="banner red">
    <span class="icon">⛔</span>
    <span class="txt">
      <b>为什么这一页不能显示一个精确的尾数：</b>这是"状态不可辨识"问题。
      系统看到"7,450 尾 / 均重 585 g"，可能来自 <b>30 天前放养 8,000 尾 150 g 苗、成活率 96%</b>，
      也可能来自 <b>45 天前放养 9,200 尾 110 g 苗、成活率 83%</b>——两者的下月产出规格分布完全不同，
      但系统看到的输入一模一样。不可辨识系统的点输出，<b>比"不知道"更危险，因为它伪装成知道。</b>
    </span>
  </div>

  <div class="grid g2" style="align-items:start">
    <div class="card">
      <div class="card-h"><h3>生物量推算 · 误差传播</h3><span class="en">Uncertainty</span></div>
      <canvas class="chart chart-240" id="cv-wf"></canvas>
      <div class="note" style="margin-top:14px">
        从"放养 8,000 尾"到"生物量 4,358 kg"，中间每一步都在放大误差，
        最终区间是 <b style="color:var(--amber)">2,668 – 5,936 kg</b>——<b style="color:var(--foam)">上下相差 2.2 倍</b>。
        这不是系统做得不好，这是池塘养殖在缺少干塘复核时的<b style="color:var(--foam)">物理上限</b>。
        FAO 实测：即使样本量达叉尾鮰 ≥100 尾 / 罗非鱼 ≥300 尾，拉网均重与干塘真值仍差 8–19%。
      </div>
    </div>

    <div class="card">
      <div class="card-h"><h3>抽样记录 · 唯一的实测锚点</h3><span class="en">Sampling</span></div>
      <table class="tbl">
        <thead><tr><th>日期</th><th>样本数</th><th>均重 g</th><th>范围 g</th><th>区间半宽</th></tr></thead>
        <tbody>
        ${LEDGER.samplings.map((s) => {
          const hw = ((s.maxG - s.minG) / 2 / s.avgG * 100).toFixed(0);
          return `<tr>
            <td class="num">${s.date}</td>
            <td class="num">${s.n}</td>
            <td class="num" style="color:var(--signal)">${s.avgG}</td>
            <td class="num">${s.minG} – ${s.maxG}</td>
            <td class="num">±${hw}%</td>
          </tr>`;
        }).join('')}
        </tbody>
      </table>
      <canvas class="chart chart-160" id="cv-grow" style="margin-top:12px"></canvas>
      <div class="note" style="margin-top:10px">
        每 15–20 天打网抽 30–50 尾称重（照抄 T/SCFA 0011 §7.3 调度周期）。
        样本量偏小时置信区间会明显变宽，这是可接受的——<b style="color:var(--foam)">带宽区间的真数据，好过带窄区间的假数据</b>。
      </div>
    </div>
  </div>

  <div class="grid g2" style="margin-top:14px;align-items:start">
    <div class="card">
      <div class="card-h"><h3>批次台账</h3><span class="en">Batches</span></div>
      <table class="tbl">
        <thead><tr><th>批次</th><th>品种</th><th>放养日</th><th>尾数</th><th>规格 g</th><th>状态</th></tr></thead>
        <tbody>${LEDGER.batches.map((b) => `<tr>
          <td class="num">${b.id}</td><td class="em">${b.species}</td><td class="num">${b.date}</td>
          <td class="num">${num(b.qty)}</td><td class="num">${b.specG}</td>
          <td><span class="chip ${b.status === '在塘' ? 'ok' : ''}">${b.status}</span></td>
        </tr>`).join('')}</tbody>
      </table>

      <div class="card-h" style="margin-top:22px"><h3>死亡记录</h3><span class="en">Mortality</span></div>
      <table class="tbl">
        <thead><tr><th>日期</th><th>尾数</th><th>估算 kg</th><th>原因</th></tr></thead>
        <tbody>${LEDGER.mortalities.map((m) => `<tr>
          <td class="num">${m.date}</td><td class="num">${m.qty}</td><td class="num">${m.kg}</td><td>${m.cause}</td>
        </tr>`).join('')}</tbody>
      </table>
      <div class="note" style="margin-top:12px">
        <b style="color:var(--amber)">不记录死亡，生物量会单向高估。</b>
        标准公式自带这一项：Y1 = mb × (Dsk × S − Y2)，其中 Y2 = 吃食鱼累计死亡质量。哪怕粗略摊销也比忽略好。
      </div>
    </div>

    <div class="card">
      <div class="card-h"><h3>投喂记录</h3><span class="en">Feeding log</span></div>
      <div class="tbl-wrap"><table class="tbl">
        <thead><tr><th>日期</th><th>餐次</th><th>目标 kg</th><th>实际 kg</th><th>水温</th><th>吃食 min</th><th>剩料</th></tr></thead>
        <tbody>${LEDGER.feedings.map((f) => `<tr>
          <td class="num">${f.date.slice(5)}</td><td>${f.meal}</td>
          <td class="num">${f.targetKg}</td>
          <td class="num" style="color:${Math.abs(f.actualKg - f.targetKg) > 1.5 ? 'var(--amber)' : 'var(--signal)'}">${f.actualKg}</td>
          <td class="num">${f.tempC}</td>
          <td class="num" style="color:${f.intakeMin > 30 ? 'var(--amber)' : 'var(--foam)'}">${f.intakeMin}</td>
          <td>${f.leftover === '无' ? '<span class="chip ok">无</span>' : `<span class="chip warn">${f.leftover}</span>`}</td>
        </tr>`).join('')}</tbody>
      </table></div>
      <div class="note" style="margin-top:12px">
        注意 9-10 晚餐：吃食时长 33 分钟（显著长于早餐 27 分钟）、剩料明显。
        这正是视觉模块捕获的"食欲衰退趋势"——系统次日即下调了目标量。
        <b style="color:var(--foam)">两个独立信号互相印证，比任何单一信号都可靠。</b>
      </div>

      <div class="card-h" style="margin-top:22px"><h3>出塘 / 销售</h3><span class="en">Harvest</span></div>
      <table class="tbl">
        <thead><tr><th>日期</th><th>尾数</th><th>kg</th><th>均重 g</th><th>单价 元/kg</th><th>去向</th></tr></thead>
        <tbody>${LEDGER.harvests.map((h) => `<tr>
          <td class="num">${h.date}</td><td class="num">${h.qty}</td><td class="num">${h.kg}</td>
          <td class="num">${h.specG}</td><td class="num" style="color:var(--signal)">${h.pricePerKg}</td><td>${h.buyer}</td>
        </tr>`).join('')}</tbody>
      </table>
      <div class="note" style="margin-top:12px">
        出塘记录是<b style="color:var(--signal)">唯一的 ground truth</b>。
        没有它，二期的一切模型都无法回测——而"没有 backtest 不上线"是全项目的上线门槛。
      </div>
    </div>
  </div>`;
}

/* ============================================================
   视图 6 · 设备网络
   ============================================================ */
function viewDevices() {
  return `
  <div class="sect-title">设备网络</div>
  <div class="sect-desc">
    六个 ESP32 节点，三种链路（LoRa / WiFi / 4G）。设计原则是
    <b style="color:var(--foam)">"投喂时段存设备本地、不依赖任何在线服务"</b>——
    真实事故教训是"控制器掉线 → 倒光整仓料"。
  </div>

  <div class="grid g3">
    ${NODES.map((n) => `
      <div class="node">
        <div class="hd">
          <span class="id">${n.id}</span>
          <span class="role">${n.role}</span>
          <span class="dot ${n.status}" style="margin-left:auto"></span>
        </div>
        <div class="board">${n.board} · fw ${n.fw}</div>
        <div class="meta">
          <span class="chip ${n.link.includes('4G') ? 'info' : ''}">${n.link}</span>
          <span class="chip">RSSI ${n.rssi} dBm</span>
          <span class="chip">${n.lastSeen}</span>
          ${n.solar ? '<span class="chip ok">太阳能</span>' : '<span class="chip">市电</span>'}
        </div>
        <ul>${n.sensors.map((s) => `<li>${s}</li>`).join('')}</ul>
        ${n.warn ? `<div class="kpi-sub" style="color:var(--amber);margin-top:8px">⚠ ${n.warn}</div>` : ''}
        ${n.batt !== null
          ? `<div class="batt"><i style="width:${n.batt}%;background:${n.batt > 50 ? PALETTE.signal : n.batt > 25 ? PALETTE.amber : PALETTE.alarm}"></i></div>
             <div class="range-txt" style="margin-top:5px">电池 ${n.batt}%</div>`
          : `<div class="range-txt" style="margin-top:8px">市电供电 · 无电池</div>`}
      </div>`).join('')}
  </div>

  <div class="grid g2" style="margin-top:14px;align-items:start">
    <div class="card">
      <div class="card-h"><h3>可靠性四红线 · 硬件层强制</h3><span class="en">Reliability</span></div>
      ${[
        { n: '01', t: '投喂时段存设备本地 NVS', d: '不依赖电脑在线、不依赖云端可达。ESP32 自己看表投喂——网络只是旁路。' },
        { n: '02', t: '上电继电器默认断开', d: '任何复位/上电瞬间，投饵机是"不转"而不是"转"。这条要焊在硬件上，不能靠软件。' },
        { n: '03', t: '断电恢复禁止补投', d: '恢复供电后不追补错过的餐次。宁可少喂一顿，不可一次倒光。' },
        { n: '04', t: '独立硬件最大时长封顶', d: '用一个独立的 RC 定时或硬件看门狗切断回路，防止软件跑飞导致投饵机长转。' },
      ].map((x) => `
        <div class="rule">
          <span class="tag signal">${x.n}</span>
          <div class="body"><div class="t">${x.t}</div><div class="d">${x.d}</div></div>
          <span></span>
        </div>`).join('')}
      <div class="note" style="margin-top:14px">
        另加：<b style="color:var(--foam)">霍尔电流互感器</b>做"真在转"反馈。
        软件以为投了、机器其实没转，是最隐蔽的失效模式——电流反馈是唯一能戳穿它的信号。
      </div>
    </div>

    <div class="card">
      <div class="card-h"><h3>通信与断网策略</h3><span class="en">Connectivity</span></div>
      <table class="tbl">
        <thead><tr><th>链路</th><th>用途</th><th>带宽</th><th>功耗</th><th>断网行为</th></tr></thead>
        <tbody>
          <tr><td class="em">LoRa SX1262</td><td>节点 → 主控</td><td class="num">~5 kbps</td><td class="num">低</td><td>重传 + 序号去重</td></tr>
          <tr><td class="em">WiFi（板载）</td><td>摄像头 → 主控</td><td class="num">高</td><td class="num">高</td><td>仅投喂时段唤醒，断开即停</td></tr>
          <tr><td class="em">4G Cat-1</td><td>主控 → 云</td><td class="num">~10 Mbps</td><td class="num">中</td><td><b style="color:var(--signal)">本地缓存 + 恢复后补传</b></td></tr>
          <tr><td class="em">NB-IoT（冗余）</td><td>告警旁路</td><td class="num">~100 kbps</td><td class="num">极低</td><td>只发关键告警</td></tr>
        </tbody>
      </table>
      <div class="note" style="margin-top:14px">
        <b style="color:var(--foam)">MicroSD 本地缓存</b>是断网时的最后一道保险：
        采样数据先落盘，网络恢复后按序号补传。没有这一步，一次几小时的断网就会在台账上留下一个洞——
        而台账的完整性（目标 ≥ 95%）直接决定二期模型能不能做。
      </div>
      <div class="kpi-sub" style="margin-top:14px">
        流量估算：无视频回传时约 300–500 MB/月，年费约 60–180 元。
        <b style="color:var(--amber)">视频不要走 4G</b>——那一秒就能烧掉一个月流量。
      </div>
    </div>
  </div>

  <div class="card" style="margin-top:14px">
    <div class="card-h"><h3>功耗与供电估算</h3><span class="en">Power budget</span></div>
    <div class="grid g3" style="gap:18px">
      <div>
        <div class="kpi-label" style="color:var(--signal)">节点侧（ESP32-C3 + 深睡）</div>
        <div class="kpi-sub" style="margin-top:0">
          深睡 5 µA · 采样唤醒 80 mA × 3 s，每 5 分钟一次 → 日均 &lt; 2 mAh。
          一块 18650（2,600 mAh）理论可撑数月，实际受自放电与低温影响，按 30–60 天估。
        </div>
      </div>
      <div>
        <div class="kpi-label" style="color:var(--amber)">主控侧（4G 常在线）</div>
        <div class="kpi-sub" style="margin-top:0">
          标准场景实测口径：<b style="color:var(--foam)">日耗电约 376 mAh</b>（5 分钟上报 + 荧光法溶氧）。
          4G Cat-1 空闲 3–8 mA、突发 200–500 mA，是耗电大头。
          ⚠️ 若换极谱式溶氧（需持续极化），跳到 <b style="color:var(--alarm)">3,376 mAh/日（9 倍）</b>，电池要从 6 Ah 涨到 50 Ah。
        </div>
      </div>
      <div>
        <div class="kpi-label" style="color:var(--cyan)">太阳能侧</div>
        <div class="kpi-sub" style="margin-top:0">
          华中地区等效峰值日照约 3.0–3.5 h/天。20 W 板 → 日发电 60–70 Wh，
          扣除 MPPT 与线损（按 0.75 折算）约 45–52 Wh，对应 <b style="color:var(--foam)">≈ 376 mAh @12 V</b>——
          刚好覆盖标准场景。<b style="color:var(--foam)">连续 3 天阴雨是设计工况，不是极端工况</b>，电池容量按这个配（12 Ah LiFePO4）。
        </div>
      </div>
    </div>
    <div class="note" style="margin-top:16px">
      <b style="color:var(--foam)">换算关系（可复算）：</b>12 V × 0.376 Ah = 4.5 Wh/日。
      20 W 板 × 3.2 h × 0.75 = 48 Wh/日 → 约 10 倍余量，足以覆盖连续阴雨。
      若你要加摄像头常开或视频回传，这个余量会立刻被吃掉——所以视频必须只在投喂时段唤醒。
    </div>
  </div>`;
}

/* ============================================================
   视图 7 · 证据与红线
   ============================================================ */
function viewEvidence() {
  return `
  <div class="sect-title">证据与红线</div>
  <div class="sect-desc">
    这一页是整个系统的<b style="color:var(--foam)">诚实层</b>。每个结论都标出来源与可信度，
    每一条红线都写清楚它为什么存在。一个不敢展示自己边界的系统，不值得被信任。
  </div>

  <div class="card" style="margin-bottom:14px">
    <div class="card-h"><h3>证据台账</h3><span class="en">Evidence ledger</span></div>
    <div class="tbl-wrap"><table class="tbl">
      <thead><tr><th style="width:44px">等级</th><th>结论</th><th>来源</th><th>在本系统中的作用</th></tr></thead>
      <tbody>${EVIDENCE.map((e) => `<tr>
        <td><span class="grade ${e.grade}" style="font-size:10px;width:19px;height:19px">${e.grade}</span></td>
        <td style="color:var(--foam)">${e.claim}</td>
        <td>${e.url ? `<a href="${e.url}" target="_blank" rel="noopener" style="color:var(--cyan);text-decoration:none;border-bottom:1px dotted var(--cyan)">${e.src}</a>` : e.src}</td>
        <td>${e.use}</td>
      </tr>`).join('')}</tbody>
    </table></div>
    <div class="legend" style="margin-top:16px">
      <span><span class="grade A" style="font-size:10px;width:19px;height:19px">A</span> 本塘实测 / 同行评议 / 政府文件</span>
      <span><span class="grade B" style="font-size:10px;width:19px;height:19px">B</span> 经验值 / 待本塘校准</span>
      <span><span class="grade C" style="font-size:10px;width:19px;height:19px">C</span> 推断 / 原型演示值</span>
    </div>
  </div>

  <div class="grid g2" style="align-items:start">
    <div>
      <div class="card-h" style="border:none;padding:0;margin-bottom:14px"><h3 style="font-family:var(--serif);font-size:16px">⛔ ${REDLINES.length} 条架构红线</h3></div>
      <div style="display:flex;flex-direction:column;gap:10px">
        ${REDLINES.map((r, i) => `
          <div class="redline">
            <div class="t"><span class="no">R${i + 1}</span>${r.t}</div>
            <div class="d">${r.d}</div>
            <div class="why">${r.why}</div>
          </div>`).join('')}
      </div>
    </div>

    <div>
      <div class="card">
        <div class="card-h"><h3>❓ 明确的空白清单</h3><span class="en">Known unknowns</span></div>
        <div class="sect-desc" style="font-size:12px;margin-bottom:12px">
          以下是本项目<b style="color:var(--foam)">明确未找到可靠来源</b>的条目。
          设计原则：<b style="color:var(--amber)">空白就是空白</b>，宁可显示"无数据"，也不许用近似品种的通用值填充。
        </div>
        ${[
          { k: '草鱼专用"水温 × 规格"投饲率矩阵', s: '❌ 现行标准无一规定数字', e: '只能用 T/SCFA 0011—2023（黄河鲤鱼）对标 + 经验下调' },
          { k: '溶氧 5 / 3 mg/L 阈值的本塘依据', s: '⚠️ 传统经验值', e: 'P1 阶段用便携仪实测回填' },
          { k: '执行端标定 CV ≤ 10% 判据线', s: '⚠️ 工程判断', e: '是性价比截止线，不是精度目标；待 B4 实测裁决' },
          { k: '本塘成活率的权威基准', s: '❌ 无', e: '批次台账需自行积累' },
          { k: '抛撒均匀性的可控手段', s: '⚠️ 实测覆盖率 18–80%', e: '属机器本身特性，在称重闭环之外' },
          { k: '绿浊土塘下的视觉精度', s: '❌ 无任何对照验证', e: '所有视觉结论均来自清水 RAS / 网箱' },
          { k: '氨氮对草鱼的毒性阈值', s: '❌ 未取得', e: '水质告警缺一条阈值' },
        ].map((x) => `
          <div class="rule">
            <span class="tag ${x.s.startsWith('❌') ? 'alarm' : 'amber'}">${x.s.startsWith('❌') ? '空白' : '待校准'}</span>
            <div class="body"><div class="t">${x.k}</div><div class="d">${x.e}</div></div>
            <span></span>
          </div>`).join('')}
      </div>

      <div class="card" style="margin-top:14px">
        <div class="card-h"><h3>验收指标 · 不写"省料 X%"</h3><span class="en">KPIs</span></div>
        <div class="quote">单塘没有对照组，"省料 X%"这个数字<b>在数学上无法测量</b>。敢承诺它的一定在编。</div>
        <div style="margin-top:16px">
          ${[
            { p: 'P1', k: '记录完整率 ≥ 95%', d: '投喂记录完整率——这是唯一可以诚实验收的指标' },
            { p: 'P2', k: '建议采纳率', d: '人工确认环节采纳了多少比例的系统建议' },
            { p: 'P3', k: '区间命中率', d: '实际出塘/投喂结果落在建议区间内的比例' },
            { p: '全程', k: '防死鱼成功次数', d: '⭐ 这是最高价值功能。一次泛塘的损失可以吃掉全年软件收益' },
          ].map((x) => `
            <div class="rule">
              <span class="tag signal">${x.p}</span>
              <div class="body"><div class="t">${x.k}</div><div class="d">${x.d}</div></div>
              <span></span>
            </div>`).join('')}
        </div>
      </div>
    </div>
  </div>

  <div class="card" style="margin-top:14px">
    <div class="card-h"><h3>这个方案是怎么被改出来的</h3><span class="en">Provenance</span></div>
    <div class="sect-desc" style="font-size:12.5px">
      本原型承接自本项目既有的三路调研 + 五轮对抗辩论 + 独立红队评审。以下是被推翻的初始判断——保留它们，
      是为了让后续读者能判断哪些结论经过对抗性检验。
    </div>
    <div class="tbl-wrap"><table class="tbl">
      <thead><tr><th>最初的判断</th><th>收敛后的结论</th><th>推翻它的证据</th></tr></thead>
      <tbody>
        <tr><td>摄像头是核心数据源</td><td style="color:var(--foam)">可用性偏差——最容易采集 ≠ 信息量最大</td><td>这是"在路灯下找钥匙"</td></tr>
        <tr><td>先做智能建议</td><td style="color:var(--foam)">先记一年账，先装溶氧</td><td>缺的不是算法，是本塘基线数据</td></tr>
        <tr><td>"称重闭环性价比最高"</td><td style="color:var(--foam)">机械手段优先于称重；称重只在 CV &gt; 10% 时上</td><td>整仓称重是算术陷阱；增量法才成立</td></tr>
        <tr><td>非光学 = 声学</td><td style="color:var(--foam)">"非光学"只排除了光学，没锁定声学</td><td>压电振动/水压波/电容触觉都满足</td></tr>
        <tr><td>方案二可以并行先做</td><td style="color:var(--foam)">降为旁路，且必须先过"照片质量门"</td><td>连画面都还没拿到过</td></tr>
        <tr><td>LLM 可以辅助决策</td><td style="color:var(--foam)">LLM 无权生成任何数字</td><td>十年十条样本，微调只会得到"自信的胡说机器"</td></tr>
      </tbody>
    </table></div>
    <div class="quote" style="margin-top:18px">
      "这不是数据不够，这是方程无解。"<br>
      <span style="font-size:12px;color:var(--mist)">—— 但方程无解不等于事情不能做。把目标从"AI 预测"降级为"仪表 + 告警 + 区间建议"，
      它立刻就变成一个扎实、可交付、有复利的系统。</span>
    </div>
  </div>`;
}

/* ============================================================
   视图 8 · 搭建路线与 BOM
   ============================================================ */
function viewBuild() {
  return `
  <div class="sect-title">搭建路线与 BOM</div>
  <div class="sect-desc">
    五阶段，总周期约 4 个月。每一阶段都有明确的<b style="color:var(--foam)">准入条件（stop）</b>——
    上一阶段不达标就不许进下一阶段。这不是流程洁癖，是因为在缺少基线数据时叠加更复杂的模块，
    只会让误差更难归因。
  </div>

  <div class="banner">
    <span class="icon">▸</span>
    <span class="txt">
      <b>完整采购清单、接线表、供电计算、烧录与标定步骤</b>见配套文档
      <b style="color:var(--signal)">《ESP32 鱼塘系统 · 硬件选型与搭建手册》</b>（Word）。
      本页只给路线与档位对照。
    </span>
  </div>

  <div class="card">
    <div class="card-h"><h3>实施路线</h3><span class="en">Roadmap</span></div>
    <div class="tl">
      ${ROADMAP.map((r) => `
        <div class="tl-item">
          <div class="tl-hd">
            <span class="p">${r.p}</span>
            <span class="t">${r.title}</span>
            <span class="m">${r.days} · ${r.cost}</span>
          </div>
          <div class="tl-body"><ul>${r.do.map((x) => `<li>${x}</li>`).join('')}</ul></div>
          <div class="tl-stop">🚦 准入条件：${r.stop}</div>
        </div>`).join('')}
    </div>
  </div>

  <div class="grid g3" style="margin-top:14px;align-items:start">
    ${BOM.tiers.map((t) => `
      <div class="tier ${t.key === 'std' ? 'rec' : ''}">
        <div class="tier-hd">
          <div class="n">${t.name}${t.key === 'std' ? ' <span class="chip ok" style="vertical-align:middle">推荐</span>' : ''}</div>
          <div class="p">${t.price}</div>
          <div class="f">${t.for}</div>
        </div>
        <div style="padding:4px 0">
          ${t.items.map((i) => `
            <div style="padding:9px 18px;border-bottom:1px solid var(--edge)">
              <div style="display:flex;justify-content:space-between;gap:12px;align-items:baseline">
                <span style="font-size:11.5px;color:var(--foam);line-height:1.5">${i.n}</span>
                <span class="range-txt" style="white-space:nowrap">${i.p}</span>
              </div>
              ${i.note ? `<div class="kpi-sub" style="margin-top:4px;font-size:10.5px">${i.note}</div>` : ''}
            </div>`).join('')}
        </div>
      </div>`).join('')}
  </div>

  <div class="card" style="margin-top:14px">
    <div class="card-h"><h3>线材与辅料（三档通用）</h3><span class="en">Wiring</span></div>
    <div class="grid g2" style="gap:0 28px">
      ${BOM.wires.map((w) => `
        <div class="rule">
          <span class="tag signal">·</span>
          <div class="body"><div class="t">${w.n}</div>${w.note ? `<div class="d">${w.note}</div>` : ''}</div>
          <span class="range-txt">${w.p}</span>
        </div>`).join('')}
    </div>
  </div>

  <div class="grid g2" style="margin-top:14px;align-items:start">
    <div class="card">
      <div class="card-h"><h3>⚠️ 五个最容易买错 / 装错的地方</h3><span class="en">Pitfalls</span></div>
      <div class="rule">
        <span class="tag alarm">坑 1</span>
        <div class="body"><div class="t">溶氧探头：别买模拟式长期泡塘</div>
          <div class="d">DFRobot Gravity SEN0237 官方实价 <b style="color:var(--foam)">¥1,299</b>，但它是原电池式，<b style="color:var(--alarm)">需每月换膜换电解液</b>，长期泡塘生物附着严重，不适合无人值守。真正的长期监测要用荧光法 RS485 探头（¥1,000–5,000，具体型号需询价）。另一条常被忽略的账：极谱式需持续极化，日耗电从 376 mAh 跳到 <b style="color:var(--alarm)">3,376 mAh（9 倍）</b>，电池容量要跟着从 6 Ah 涨到 50 Ah。</div></div><span></span>
      </div>
      <div class="rule">
        <span class="tag alarm">坑 2</span>
        <div class="body"><div class="t">别指望 ESP32 自己跑鱼类识别模型</div>
          <div class="d">乐鑫官方 benchmark：yolo11n@320 在 S3 上是 <b style="color:var(--alarm)">6,196 ms/帧（0.16 FPS）</b>，@640 是 26 秒/帧。GitHub 全量检索 <code>fish+detection+esp32</code> 只有 5 个仓库、全部 0 star。正确分工：<b style="color:var(--foam)">ESP32 负责"在正确时刻拍下正确的照片并上传"，推理放云端</b>；水质预测用经典 ML（Sensors 2025 有真·ESP32 端侧多元线性回归部署，R² ≈ 0.65–0.72）。</div></div><span></span>
      </div>
      <div class="rule">
        <span class="tag alarm">坑 3</span>
        <div class="body"><div class="t">电源：别用 18650 组，也别用 LM2596 和铅酸控制器</div>
          <div class="d">18650 在夏季盒内高温（可超 60 ℃）下循环寿命骤降 → 用 LiFePO4。LM2596 静态电流 5 mA（= ESP32 工作电流的 38%）、非同步、慢环路，面对 ESP32-S3 的 <b style="color:var(--foam)">27 倍电流阶跃</b>必然跌落 → 换 SY8205FCC（¥1.44）。铅酸控制器充 LiFePO4 的分界线在<b style="color:var(--alarm)">"均充档"</b>：浮充 13.6–13.8 V 两者一致（误导了很多人），但均充 14.8–15.5 V 远超 14.6 V 上限 → 多花 ¥60 买带 LiFePO4 档的，不能省。</div></div><span></span>
      </div>
      <div class="rule">
        <span class="tag alarm">坑 4</span>
        <div class="body"><div class="t">流量卡：先定死硬件，再激活卡</div>
          <div class="d"><b style="color:var(--alarm)">物联网卡机卡绑定</b>——开发期换板子会触发停机，而电信每月只有 2 次解绑额度。另外别用 HTTP 短连接 + TLS 全握手：年流量 <b style="color:var(--foam)">702 MB</b>，是 MQTT 长连接（40 MB）的 15.6 倍。还有：<b style="color:var(--alarm)">915 MHz LoRa 在中国不合法</b>，433 MHz 限 10 dBm，市面 18–30 dBm 模块全部超限。</div></div><span></span>
      </div>
      <div class="rule">
        <span class="tag alarm">坑 5</span>
        <div class="body"><div class="t">防雷不是可选项</div>
          <div class="d">有真实事故：陕西西安雷击断线 → 增氧机停 → <b style="color:var(--alarm)">死鱼 6000 斤、损失约 3 万元</b>；广东汕头 2025-07-29 仍有同类事件。两级防护（电源 SPD ¥25.5 + 信号 SPD ¥25）每节点约 ¥100–210，<b style="color:var(--foam)">不到潜在损失的 1%</b>。⚠️ 必须单点接地 + 引线 ≤ 0.5 m——这是 SPD 失效的第一原因。</div></div><span></span>
      </div>
      <div class="note" style="margin-top:16px">
        还有两条不算"买错"但同样致命：<b style="color:var(--foam)">① 防水不是买个 IP67 盒子就完事</b>——
        真正的进水路径是线缆进出口、凝露、以及盒内外的温差呼吸效应；每个开孔都要用 PG7/M12 接头，盒内放干燥剂。
        <b style="color:var(--foam)">② 假货</b>——eBay/AliExpress 的 DS18B20 探头几乎全假（用 ROM 码鉴别）；
        u-blox NEO-6M 官方已 EOL，市面几乎全是 AT6558 冒充（假货开机报 <code>$GNTXT</code> 而非 <code>$GPTXT</code>，接天线就复位）。
      </div>
    </div>

    <div class="card">
      <div class="card-h"><h3>这套东西到底靠不靠谱 · 分模块打分</h3><span class="en">Honest scorecard</span></div>
      <div class="tbl-wrap"><table class="tbl">
        <thead><tr><th>模块</th><th>靠谱度</th><th>理由</th></tr></thead>
        <tbody>
          <tr><td class="em">水温在线监测</td><td><span class="chip ok">★★★★★</span></td><td>DS18B20 成熟、便宜、防水、十年验证。三点链（表/半深/离底）还能免费拿到"分层告警"能力。零风险。</td></tr>
          <tr><td class="em">溶氧在线监测</td><td><span class="chip ok">★★★★☆</span></td><td>技术成熟，价值最高，维护成本也最高。探头是耗材、需校准，且模拟式不适合无人值守。</td></tr>
          <tr><td class="em">ESP32 做网关/节点</td><td><span class="chip ok">★★★★★</span></td><td>这就是 ESP32 的本职工作。低功耗、WiFi/蓝牙/LoRa 生态成熟、社区庞大。</td></tr>
          <tr><td class="em">4G Cat-1 回传</td><td><span class="chip ok">★★★★☆</span></td><td>DTU ¥98 + 卡 ¥30/年，成熟且便宜。唯一要守的纪律：用 MQTT，别用 HTTP+TLS 短连接。</td></tr>
          <tr><td class="em">投喂量决策模型</td><td><span class="chip warn">★★★☆☆</span></td><td>公式本身是对的（有对照试验支持 FCR −11.73%），但精度天花板 ±30–60% 由存塘量决定，不是模型能改善的。</td></tr>
          <tr><td class="em">执行端定量精度</td><td><span class="chip warn">★★★☆☆</span></td><td>误差漏斗最窄处。开环 ±5–20%，必须做 B4 标定；标不过才上称重。</td></tr>
          <tr><td class="em">GPS 定位</td><td><span class="chip">★☆☆☆☆</span></td><td><b style="color:var(--foam)">对固定塘口几乎没用。</b>塘不会移动。¥11 的模块当"档案字段"可以，别指望它参与决策。且别买 NEO-6M——已 EOL，市面全是冒充。</td></tr>
          <tr><td class="em">摄像头数鱼</td><td><span class="chip alarm">★☆☆☆☆</span></td><td><b style="color:var(--alarm)">不靠谱。</b>纯光学在池塘的公开最好成绩是 mAP 38.93%；加上声学做融合，中国水科院也只做到 85–92%，且是"体量/密度"不是逐尾。不是算法不够好，是物理上拿不到那个信息。</td></tr>
          <tr><td class="em">摄像头判摄食强度</td><td><span class="chip warn">★★★☆☆</span></td><td>清水 RAS 里有 95%+ 的验证，绿浊土塘<b style="color:var(--amber)">零对照验证</b>。定位成"止损开关"可以，定位成"计量仪表"不行。</td></tr>
          <tr><td class="em">ESP32 端侧跑鱼类识别</td><td><span class="chip alarm">★☆☆☆☆</span></td><td><b style="color:var(--alarm)">明确不可行。</b>官方 benchmark：yolo11n@320 = 0.16 FPS。且全网零先例（GitHub 仅 5 个仓库、全 0 star）。</td></tr>
          <tr><td class="em">自动投喂闭环</td><td><span class="chip warn">★★★☆☆</span></td><td>可以做，但必须保留人工确认 + 溶氧硬开关 + 硬件封顶。无人值守的全自动投喂是负期望值的赌博。</td></tr>
        </tbody>
      </table></div>
      <div class="quote" style="margin-top:18px">
        一句话：<b style="color:var(--signal)">用 ESP32 做"传感 + 决策 + 告警"非常靠谱；
        用它（或任何相机）做"数鱼"不靠谱。</b>
        而好消息是——<b>你不需要数清鱼，也能把喂料这件事做好。</b><br>
        <span style="font-size:12px;color:var(--mist)">FAO 的原话是：「至今没有人找到令人满意的存塘量评估方法」。
        工业界的做法是绕开它，不是硬解它。</span>
      </div>
    </div>
  </div>`;
}

/* ============================================================
   渲染与交互
   ============================================================ */
const RENDERERS = {
  overview: viewOverview, feeding: viewFeeding, water: viewWater, vision: viewVision,
  ledger: viewLedger, devices: viewDevices, evidence: viewEvidence, build: viewBuild,
};

function render() {
  const v = VIEWS.find((x) => x.k === state.view);
  $('#view').innerHTML = RENDERERS[state.view]();
  $('#crumb').textContent = `${v.en.toUpperCase()} / ${v.cn}`;
  $$('.nav button').forEach((b) => b.classList.toggle('on', b.dataset.v === state.view));
  requestAnimationFrame(() => { drawCharts(); bindView(); });
}

function drawCharts() {
  const s = scn(), d = dec();
  const series = makeSeries(s);

  // 总览
  if (state.view === 'overview') {
    const v = verdictFor();
    lineChart($('#cv-verify'), [0, 1, 2, 3], [
      { data: [d.baselinePerMeal, d.baselinePerMeal, d.baselinePerMeal, d.baselinePerMeal], color: PALETTE.mist, dash: [4, 3], glow: false },
      { data: v.text ? [0, 0, 0, 0] : [v.lo, v.rec, v.hi, v.rec], color: scnCls() === 'alarm' ? PALETTE.alarm : scnCls() === 'warn' ? PALETTE.amber : PALETTE.signal, fill: true },
    ], { min: 0, max: Math.max(d.baselinePerMeal * 1.3, 10), decimals: 0, pad: { t: 14, r: 34, b: 22, l: 30 } });
    sparkline($('#sp-n'), [6800, 7010, 7180, 7260, 7390, 7450], PALETTE.cyan);
    sparkline($('#sp-t'), series.temp, PALETTE.amber);
    sparkline($('#sp-do'), series.do_, PALETTE.signal);
    lineChart($('#cv-do'), series.t, [
      { data: series.do_, color: PALETTE.signal, fill: true, width: 2.2 },
    ], { min: 0, max: Math.max(10, s.env.doMax + 2), decimals: 1,
         zones: [{ from: 0, to: 3, color: 'rgba(255,95,69,.14)' }, { from: 3, to: 5, color: 'rgba(255,180,84,.09)' }],
         thresholds: [{ v: 5, color: PALETTE.amber, label: '5' }, { v: 3, color: PALETTE.alarm, label: '3' }] });
  }

  // 水质
  if (state.view === 'water') {
    lineChart($('#cv-main'), series.t, [
      { data: series.temp, color: PALETTE.amber, width: 1.7 },
      { data: series.do_, color: PALETTE.cyan, fill: true, width: 2.2 },
    ], { min: 0, max: 36, decimals: 0,
         zones: [{ from: 0, to: 3, color: 'rgba(255,95,69,.13)' }, { from: 3, to: 5, color: 'rgba(255,180,84,.08)' }],
         thresholds: [{ v: 32, color: PALETTE.alarm, label: '32 ℃' }, { v: 5, color: PALETTE.amber, label: '5 mg/L' }] });
    lineChart($('#cv-ph'), series.t, [
      { data: series.turb, color: PALETTE.lead, width: 1.6 },
      { data: series.ph, color: PALETTE.violet, width: 1.8 },
    ], { min: 0, decimals: 1 });
    sparkline($('#wsp-do'), series.do_, PALETTE.cyan);
    sparkline($('#wsp-temp'), series.temp, PALETTE.amber);
  }

  // 视觉
  if (state.view === 'vision') {
    lineChart($('#cv-act'), series.t, [
      { data: series.activity, color: PALETTE.signal, fill: true, width: 2 },
    ], { min: 0, max: 100, decimals: 0,
         thresholds: [{ v: 70, color: PALETTE.signal, label: '强' }, { v: 40, color: PALETTE.amber, label: '中' }, { v: 15, color: PALETTE.alarm, label: '弱' }] });
  }

  // 台账
  if (state.view === 'ledger') {
    waterfall($('#cv-wf'), [
      { label: '放养', value: 8000, color: PALETTE.mist },
      { label: '累计死亡', value: 310, color: PALETTE.alarm },
      { label: '已出塘', value: 240, color: PALETTE.amber },
      { label: '存塘区间', value: 7450, lo: 5210, hi: 8940, color: PALETTE.cyan },
      { label: '生物量', value: 4358, lo: 2668, hi: 5936, color: PALETTE.amber },
    ]);
    lineChart($('#cv-grow'), LEDGER.samplings.map((_, i) => i), [
      { data: LEDGER.samplings.map((x) => x.avgG), color: PALETTE.signal, fill: true, width: 2.2 },
      { data: LEDGER.samplings.map((x) => x.minG), color: PALETTE.mist, dash: [3, 3], width: 1.2, glow: false },
      { data: LEDGER.samplings.map((x) => x.maxG), color: PALETTE.mist, dash: [3, 3], width: 1.2, glow: false },
    ], { min: 0, decimals: 0, pad: { t: 14, r: 40, b: 22, l: 40 } });
  }
}

function bindView() {
  $$('[data-scn]').forEach((b) => b.onclick = () => {
    state.scn = b.dataset.scn; state.override = null; state.confirmed = false; render();
  });

  if (state.view === 'feeding') {
    const ov = $('#ov'), out = $('#ov-val');
    if (ov) ov.oninput = () => {
      state.override = parseFloat(ov.value);
      out.innerHTML = `${state.override.toFixed(1)}<span class="u">kg / 餐</span>`;
      const d = dec(), v = verdictFor();
      const hint = $('#ov-hint');
      if (state.override > v.hi) hint.innerHTML = `<span style="color:var(--amber)">⚠ 超出建议上限 ${(state.override - v.hi).toFixed(1)} kg。此操作会被记录并作为下一轮评估的输入。</span>`;
      else if (state.override < v.lo) hint.innerHTML = `<span style="color:var(--mist)">低于建议下限。投喂不足是温和的错——但连续多餐低估会拖慢生长。</span>`;
      else hint.textContent = '落在建议区间内。这是系统推荐的操作。';
    };
    const bc = $('#btn-confirm');
    if (bc) bc.onclick = () => {
      state.confirmed = true;
      const d = dec(), v = verdictFor();
      const kg = state.override ?? v.rec;
      const RATE = 41.5;   // g/s —— 来自 B4 标定表（标称 3.0 mm / 中料位 / 额定电压）
      const DEAD = 0.66;   // s   —— 启动死区
      const CAP = 180;     // s   —— 硬件层单次开阀封顶
      const need = (kg * 1000) / RATE;
      const cycles = Math.max(1, Math.ceil(need / CAP));
      const per = need / cycles;
      const capped = need > CAP;
      const plan = Array.from({ length: cycles }, (_, i) =>
        (i === cycles - 1 ? need - per * (cycles - 1) : per) + DEAD);
      $('#exec-log').innerHTML = `
        <div class="card tight" style="border-color:var(--edge-2);background:rgba(91,233,166,.06)">
          <div class="kpi-label" style="color:var(--signal)">✓ 已下发至 N05 · ${new Date().toLocaleTimeString('zh-CN')}</div>
          <div class="kpi-sub" style="margin-top:0;color:var(--mist)">
            目标 <b style="color:var(--foam)">${kg.toFixed(1)} kg</b>　→　查 B4 标定表（${RATE} g/s）<br>
            需要开阀 <b style="color:var(--foam)">${need.toFixed(0)} 秒</b>（含死区 ${DEAD} s）
            ${capped ? `　⚠️ 超过硬件单次封顶 ${CAP} 秒 —— 自动拆成 <b style="color:var(--amber)">${cycles} 次</b>` : ''}
          </div>
          <div class="readout" style="margin-top:10px;font-size:13px;line-height:1.95;color:var(--signal)">
            ${plan.map((s, i) => `第 ${i + 1} 次：开阀 ${s.toFixed(1)} 秒`).join('<br>')}
            ${capped ? `<br><span style="color:var(--mist);font-size:11px">每次之间间隔 25 秒，等水面抢食散去再投下一次 —— 避免颗粒集中沉底、局部过喂。</span>` : ''}
          </div>
          <div class="kpi-sub" style="margin-top:12px;padding-top:10px;border-top:1px dashed var(--edge);color:var(--amber)">
            ⚠️ 硬件层封顶已启用：无论软件如何请求，单次开阀不超过 ${CAP} 秒
            （独立 RC 定时 + 硬件看门狗，即使 MCU 死机也生效）。断电恢复不补投，上电继电器默认断开。
          </div>
        </div>`;
      bc.textContent = '已下发 · 可重发';
    };
    const br = $('#btn-reset');
    if (br) br.onclick = () => { state.override = null; state.confirmed = false; render(); };
  }
}

/* ---------- 证据角标 tooltip ---------- */
const tip = document.createElement('div');
tip.id = 'tip';
document.body.appendChild(tip);
document.addEventListener('mouseover', (e) => {
  const t = e.target.closest('[data-tip]');
  if (!t) return;
  tip.innerHTML = t.dataset.tip;
  tip.classList.add('on');
});
document.addEventListener('mousemove', (e) => {
  if (!tip.classList.contains('on')) return;
  const pad = 14;
  let x = e.clientX + pad, y = e.clientY + pad;
  const r = tip.getBoundingClientRect();
  if (x + r.width > innerWidth - 10) x = e.clientX - r.width - pad;
  if (y + r.height > innerHeight - 10) y = e.clientY - r.height - pad;
  tip.style.left = x + 'px'; tip.style.top = y + 'px';
});
document.addEventListener('mouseout', (e) => {
  if (!e.target.closest('[data-tip]')) return;
  tip.classList.remove('on');
});

/* ---------- 导航 ---------- */
function buildNav() {
  $('.nav').innerHTML = VIEWS.map((v) =>
    `<button data-v="${v.k}"><span class="ic">${v.ic}</span><span class="cn">${v.cn}</span><span class="en">${v.en}</span></button>`
  ).join('');
  $$('.nav button').forEach((b) => b.onclick = () => {
    state.view = b.dataset.v;
    $('.rail').classList.remove('open');
    render();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

/* ---------- 时钟 ---------- */
function tick() {
  const t = new Date();
  const el = $('#clock');
  if (el) el.textContent = t.toLocaleTimeString('zh-CN', { hour12: false });
}

/* ---------- 启动 ---------- */
buildNav();
render();
tick(); setInterval(tick, 1000);
window.addEventListener('resize', () => { clearTimeout(window.__rz); window.__rz = setTimeout(drawCharts, 180); });
$('#rail-toggle').onclick = () => $('.rail').classList.toggle('open');
