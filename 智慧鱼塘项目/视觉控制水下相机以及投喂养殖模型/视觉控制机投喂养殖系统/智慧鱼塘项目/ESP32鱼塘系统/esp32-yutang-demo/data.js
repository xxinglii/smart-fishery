/* ============================================================
   塘口仪表台 · 领域模型与模拟数据
   ------------------------------------------------------------
   ⚠️ 本文件全部为【演示用模拟数据】，非真实塘口数据。
      真实部署时，这些值应由 ESP32 节点经 MQTT 上报，
      或由用户在「台账」界面录入。
   ============================================================ */

/* ---------- 塘口基础档案 ---------- */
const POND = {
  id: 'TANG-A1',
  name: '1 号塘 · 草鱼主养',
  areaMu: 8,               // 亩
  avgDepthM: 1.8,          // 平均水深 m
  volumeM3: 8 * 666.67 * 1.8,
  species: '草鱼（主养）+ 鲢鳙（配养）',
  gps: { lat: 30.5928, lng: 114.3055, accM: 2.4 },
  stockDate: '2026-04-10',
  stockedFry: 8000,
  fryWeightG: 150,
};

/* ---------- 证据分级（本项目的核心文化：每个数字都要能溯源） ---------- */
const GRADE = {
  A: { label: 'A', name: '实测/同行评议', desc: '本塘实测，或有同行评议论文、政府/行业标准支持' },
  B: { label: 'B', name: '经验值/待校准', desc: '传统经验值或行业惯例，尚未用本塘数据校准' },
  C: { label: 'C', name: '推断/演示值', desc: '本原型为演示目的生成的模拟值，不可用于生产决策' },
};

/* ---------- 情景：同一套模型，三种环境，看安全钳制怎么动 ----------
   注意 env 里存的是【日最高水温】与【夜最低溶氧】——不是"当前值"。
   决策用的正是这两个极值：白天做决策，风险在夜里；用"当前值"会系统性低估风险。 */
const SCENARIOS = {
  normal: {
    key: 'normal',
    name: '常态日',
    tag: '常规投喂',
    tone: 'ok',
    desc: '日最高水温 28.6 ℃、夜最低溶氧 5.9 mg/L、气压正常。安全门全开，输出即模型基线。',
    env: { tempMax: 28.6, tempMin: 25.2, doMax: 9.6, doMin: 5.9, ph: 7.62, turbidityNtu: 38, airHpa: 1011, weather: '多云' },
    clampNotes: [],
    judge: '全部安全门通过，未触发任何钳制。此时的建议区间宽度，完全由"存塘量不知道"造成。',
  },
  heat: {
    key: 'heat',
    name: '高温闷热日',
    tag: '只减不增',
    tone: 'warn',
    desc: '日最高水温 33.4 ℃ 越限、气压 1002 hPa 偏低、预报雷阵雨。两条安全规则叠加，输出被压到基线的 66%。',
    env: { tempMax: 33.4, tempMin: 29.4, doMax: 8.4, doMin: 5.6, ph: 7.88, turbidityNtu: 52, airHpa: 1002, weather: '闷热 · 雷阵雨' },
    clampNotes: [
      { rule: '日最高水温 33.4 ℃ > 32 ℃', action: '只减不增 ×0.75', detail: '高温下鱼体代谢耗氧升高、水体饱和溶氧下降，过量投喂是泛塘的直接诱因。此时系统拒绝任何上调——即使模型说该加。' },
      { rule: '气压 1002 hPa 偏低 + 预报雷阵雨', action: '再 ×0.88', detail: '气压是比水温更早的泛塘前兆。溶氧风险窗口在后半夜，而雷阵雨会进一步压低气压。' },
      { rule: '两条规则叠加', action: '合计 ×0.66', detail: '规则是相乘的，且只往一个方向走——只会更保守，不会相互抵消。这是"非对称"的工程含义。' },
    ],
    judge: '系统拒绝上调建议量，并在模型基线基础上主动下调约 34%。',
  },
  hypoxia: {
    key: 'hypoxia',
    name: '缺氧预警',
    tag: '建议停喂',
    tone: 'alarm',
    desc: '夜最低溶氧 2.4 mg/L 跌破 3 mg/L 硬阈值。触发停喂并联动增氧机。',
    env: { tempMax: 31.0, tempMin: 27.6, doMax: 5.6, doMin: 2.4, ph: 7.4, turbidityNtu: 61, airHpa: 1004, weather: '阴 · 无风' },
    clampNotes: [
      { rule: '夜最低溶氧 2.4 mg/L < 3 mg/L', action: '硬开关 → 停喂 ×0', detail: '此时投喂会进一步抬高耗氧，属自催化灾难路径：残饵 → 耗氧 + 氨氮飙升 → 水质崩溃 → 缺氧泛塘。' },
      { rule: '无风 + 阴天', action: '加剧项', detail: '无风意味着水面复氧差，阴天意味着藻类光合产氧低。这两个条件叠加是泛塘的典型气象组合。' },
      { rule: '联动增氧机', action: '自动执行', detail: '系统唯一会不经确认自动执行的两件事：停喂、开增氧机。方向都是"保命"而非"增产"。' },
    ],
    judge: '硬开关触发，投喂建议归零。这是全系统优先级最高的一条规则，不允许人工绕过。',
  },
};

/** 按当前钟点取"此刻"的环境读数（决策仍用日最高/夜最低这两个极值） */
function currentEnv(scn) {
  const h = new Date().getHours() + new Date().getMinutes() / 60;
  const e = scn.env;
  const tMean = (e.tempMax + e.tempMin) / 2, tAmp = (e.tempMax - e.tempMin) / 2;
  const dMean = (e.doMax + e.doMin) / 2, dAmp = (e.doMax - e.doMin) / 2;
  return {
    temp: +(tMean + tAmp * Math.cos(((h - 15) / 24) * 2 * Math.PI)).toFixed(1),
    do_: +(dMean + dAmp * Math.cos(((h - 17) / 24) * 2 * Math.PI)).toFixed(2),
    ph: +(e.ph + 0.28 * Math.sin(((h - 14) / 24) * 2 * Math.PI)).toFixed(2),
    turb: e.turbidityNtu,
  };
}

/* ---------- 投喂决策链：每一步都带不确定度与证据等级 ----------
   分层原则（避免重复计数）：
     · 模型层 —— 生物量 × 投饲率 × 代谢温度因子 f_T。这是生物学模型，连续、可解释。
     · 规则层 —— 安全门（溶氧硬开关 / 高温只减不增 / 闷热低压 / 观察带）。
                 这是工程规则，非对称、可审计、可被人工推翻。
   两层分开，是为了让"模型说该喂多少"和"规则说今天不许喂"能分别被质疑。 */
function buildDecisionChain(scn) {
  const N = 7450, Nlo = 5210, Nhi = 8940;          // 存塘尾数（台账推算）
  const w = 0.585, wlo = 0.512, whi = 0.664;        // 抽样均重 kg
  const Blo = Nlo * wlo, Bhi = Nhi * whi, Bmid = N * w;
  const rBase = 0.022;                              // 基础投饲率 2.2 %BW/day
  const meals = 3;
  const T = scn.env.tempMax, DO = scn.env.doMin, hPa = scn.env.airHpa;

  /* --- 模型层：代谢温度因子（单峰曲线，峰值 26 ℃） --- */
  const fT = (() => {
    if (T <= 10) return 0;
    if (T <= 15) return 0.25 + ((T - 10) / 5) * 0.30;
    if (T <= 20) return 0.55 + ((T - 15) / 5) * 0.25;
    if (T <= 26) return 0.80 + ((T - 20) / 6) * 0.20;
    if (T <= 30) return 1.00 - ((T - 26) / 4) * 0.05;
    if (T <= 34) return 0.95 - ((T - 30) / 4) * 0.35;
    return 0.45;
  })();

  /* --- 规则层：安全钳制（逐条相乘，取最严） --- */
  const rules = [];
  let clamp = 1.0;

  if (DO < 3) {
    clamp = 0; rules.push({ rule: `溶氧 ${DO} mg/L < 3`, factor: 0, kind: 'alarm' });
  } else if (DO < 5) {
    clamp *= 0.5; rules.push({ rule: `溶氧 ${DO} mg/L < 5`, factor: 0.5, kind: 'alarm' });
  } else if (DO < 5.5) {
    clamp *= 0.92; rules.push({ rule: `溶氧 ${DO} mg/L 落入观察带 5–5.5`, factor: 0.92, kind: 'warn' });
  }
  if (clamp > 0 && T > 32) {
    clamp *= 0.75; rules.push({ rule: `水温 ${T} ℃ > 32 ℃`, factor: 0.75, kind: 'warn' });
  }
  if (clamp > 0 && (hPa < 1005 || scn.env.weather.includes('雷'))) {
    clamp *= 0.88; rules.push({ rule: `气压 ${hPa} hPa 偏低 / 闷热雷雨`, factor: 0.88, kind: 'warn' });
  }

  const wDayMid = Bmid * rBase * fT;
  const wDayLo = Blo * rBase * fT;
  const wDayHi = Bhi * rBase * fT;

  // 非对称：只减不增 → 上限不得高于人工历史上限的 110%
  const histMaxPerMeal = 34;                        // 人工历史单餐上限 kg
  const hardCap = histMaxPerMeal * 1.1;

  let finalHi = (wDayHi * clamp) / meals;
  let capped = false;
  if (finalHi > hardCap) { finalHi = hardCap; capped = true; }
  // 保守默认：宁可低估（只压下限，区间因此天然是"向下偏"的）
  const finalLo = ((wDayLo * clamp) / meals) * 0.82;
  const recommend = clamp === 0 ? 0 : Math.min(finalHi * 0.9, (finalLo + finalHi) / 2);

  return {
    params: [
      { key: '存塘尾数 N', value: '7,450 尾', range: '5,210 – 8,940 尾', grade: 'B',
        how: '放养 8,000 尾 − 累计死亡 310 − 出塘 240，无干塘复核',
        note: '唯一初始条件的推算值。FAO 实测：即使样本量达标，拉网均重与干塘真值仍差 8–19%。' },
      { key: '抽样均重 w', value: '585 g/尾', range: '512 – 664 g', grade: 'A',
        how: '2026-09-08 打网抽样 n = 42，电子秤逐尾称重',
        note: '本塘实测。样本量偏小，n < 100 时置信区间偏宽——这是可接受的，带宽区间的真数据好过带窄区间的假数据。' },
      { key: '生物量 B = N × w', value: '4,358 kg', range: '2,668 – 5,936 kg', grade: 'B',
        how: '两项相乘，误差按区间端点相乘传播（保守）',
        note: '⚠️ 误差漏斗的源头。下游一切建议的宽度都由这一行决定——上下相差 2.2 倍。' },
      { key: '基础投饲率 r', value: '2.2 %BW/d', range: '1.8 – 2.6 %', grade: 'B',
        how: '对标 T/SCFA 0011—2023 矩阵，按水温插值',
        note: '该标准为黄河鲤鱼，非草鱼；数值已按草鱼精养经验下调。SC/T 1016.1~.7-1995（唯一规定过投饲率数字的行业标准）已全部废止。' },
      { key: '模型层 · 代谢温度因子 f_T', value: fT.toFixed(2), range: '单峰，峰值 26 ℃', grade: 'B',
        how: `实测 ${T} ℃ → 单峰曲线取值`,
        note: '这是生物学模型项（代谢速率随温度变化），与下面的"安全规则"是两回事——分开是为了能分别被质疑。曲线形状为本原型设定，待本塘标定。' },
      { key: '模型层 · 日投饲量', value: `${(wDayMid).toFixed(1)} kg/d`, range: `${wDayLo.toFixed(0)} – ${wDayHi.toFixed(0)} kg/d`, grade: 'B',
        how: `B × r × f_T = 4,358 × 2.2% × ${fT.toFixed(2)}`,
        note: '此时尚未施加任何安全规则——它是"模型认为该喂多少"，不是"今天允许喂多少"。' },
    ],
    rules,
    Bmid, Blo, Bhi, wDayMid, wDayLo, wDayHi, fT,
    meals, hardCap, capped,
    baselinePerMeal: wDayMid / meals,
    clampFactor: clamp,
    finalLo, finalHi, recommend,
  };
}

/* ---------- 传感器时序（模拟 24 小时，与情景极值严格自洽） ---------- */
function makeSeries(scn) {
  const out = { t: [], temp: [], do_: [], ph: [], turb: [], activity: [] };
  const e = scn.env;
  const tMean = (e.tempMax + e.tempMin) / 2, tAmp = (e.tempMax - e.tempMin) / 2;
  const dMean = (e.doMax + e.doMin) / 2, dAmp = (e.doMax - e.doMin) / 2;
  let seed = 42;
  const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; };

  for (let h = 0; h <= 24; h += 0.5) {
    out.t.push(h);
    // 水温：午后 15 时达峰，凌晨 3 时谷值
    out.temp.push(+(tMean + tAmp * Math.cos(((h - 15) / 24) * 2 * Math.PI) + (rnd() - 0.5) * 0.10).toFixed(2));
    // 溶氧：与水温反相位，17 时达峰 / 5 时触底
    out.do_.push(+Math.max(0.3, dMean + dAmp * Math.cos(((h - 17) / 24) * 2 * Math.PI) + (rnd() - 0.5) * 0.13).toFixed(2));
    out.ph.push(+(e.ph + 0.28 * Math.sin(((h - 14) / 24) * 2 * Math.PI) + (rnd() - 0.5) * 0.03).toFixed(2));
    out.turb.push(+(e.turbidityNtu + 7 * Math.sin(((h - 16) / 24) * 2 * Math.PI) + (rnd() - 0.5) * 2.4).toFixed(1));
    // 摄食活动指数：投喂时刻的脉冲
    let act = 8 + rnd() * 6;
    const peak = scn.key === 'hypoxia' ? 22 : scn.key === 'heat' ? 44 : 62;
    [7, 12.5, 17.5].forEach((m) => { const dd = Math.abs(h - m); if (dd < 1.6) act += (1.6 - dd) * peak; });
    out.activity.push(+Math.min(100, act).toFixed(1));
  }
  return out;
}

/* ---------- 台账 ---------- */
const LEDGER = {
  batches: [
    { id: 'B-2026-01', species: '草鱼', date: '2026-04-10', qty: 8000, specG: 150, source: '自繁', status: '在塘' },
    { id: 'B-2026-02', species: '鲢鳙', date: '2026-04-18', qty: 1200, specG: 90, source: '外购', status: '在塘' },
    { id: 'B-2025-03', species: '草鱼', date: '2025-04-02', qty: 6500, specG: 140, source: '自繁', status: '已清塘' },
  ],
  mortalities: [
    { date: '2026-05-22', qty: 96, kg: 41, cause: '运输应激' },
    { date: '2026-06-30', qty: 74, kg: 38, cause: '缺氧（未开增氧机）' },
    { date: '2026-07-19', qty: 82, kg: 46, cause: '细菌性烂鳃' },
    { date: '2026-08-27', qty: 58, kg: 35, cause: '不明（零星）' },
  ],
  harvests: [
    { date: '2026-08-15', qty: 240, kg: 138, specG: 575, pricePerKg: 13.6, buyer: '本地批发' },
  ],
  samplings: [
    { date: '2026-06-12', n: 30, avgG: 268, minG: 201, maxG: 340 },
    { date: '2026-07-10', n: 36, avgG: 391, minG: 298, maxG: 486 },
    { date: '2026-08-05', n: 40, avgG: 498, minG: 388, maxG: 621 },
    { date: '2026-09-08', n: 42, avgG: 585, minG: 462, maxG: 728 },
  ],
  feedings: [
    { date: '2026-09-09', meal: '早 06:40', targetKg: 31.5, actualKg: 31.0, tempC: 26.1, doMin: 6.3, intakeMin: 22, leftover: '无' },
    { date: '2026-09-09', meal: '午 12:30', targetKg: 31.5, actualKg: 32.4, tempC: 28.9, doMin: 6.3, intakeMin: 25, leftover: '无' },
    { date: '2026-09-09', meal: '晚 17:30', targetKg: 30.0, actualKg: 29.6, tempC: 27.4, doMin: 6.3, intakeMin: 24, leftover: '少量' },
    { date: '2026-09-10', meal: '早 06:40', targetKg: 32.0, actualKg: 32.1, tempC: 26.8, doMin: 6.0, intakeMin: 27, leftover: '无' },
    { date: '2026-09-10', meal: '午 12:30', targetKg: 32.0, actualKg: 33.0, tempC: 30.2, doMin: 6.0, intakeMin: 31, leftover: '无' },
    { date: '2026-09-10', meal: '晚 17:30', targetKg: 30.5, actualKg: 30.2, tempC: 28.6, doMin: 6.0, intakeMin: 33, leftover: '明显' },
  ],
};

/* ---------- ESP32 节点网络 ---------- */
const NODES = [
  { id: 'N01', role: '岸边主控 / 网关', board: 'DFRobot FireBeetle 2 ESP32-S3', fw: 'v0.9.3', batt: 87, solar: true, rssi: -61, link: '4G Cat-1 (USR-DR154)', lastSeen: '2 秒前', status: 'ok', sensors: ['SHT31 气温/湿度', 'BMP280 气压', '翻斗式雨量计'] },
  { id: 'N02', role: '水温链（表 0.3m / 半深 / 离底 0.3m）', board: 'ESP32-C3-MINI-1', fw: 'v0.9.1', batt: 74, solar: true, rssi: -68, link: 'LoRa 433 MHz (SX1262)', lastSeen: '38 秒前', status: 'ok', sensors: ['DS18B20 ×3（不锈钢防水封装）'], warn: '下层比表层低 3.8 ℃ —— 分层已形成，底部缺氧风险' },
  { id: 'N03', role: '溶氧 · pH · ORP', board: 'ESP32-S3 + RS485 收发', fw: 'v0.9.3', batt: 81, solar: true, rssi: -72, link: 'LoRa 433 MHz (SX1262)', lastSeen: '41 秒前', status: 'ok', sensors: ['荧光法 DO 探头（RS485 Modbus, IP68）', '工业 pH 电极 + 变送', 'ORP 电极'] },
  { id: 'N04', role: '投料点摄像头 · 触发抓拍', board: 'ESP32-S3-CAM (OV5640)', fw: 'v0.8.7', batt: 63, solar: true, rssi: -58, link: 'WiFi → N01', lastSeen: '5 秒前', status: 'warn', sensors: ['OV5640 500 万像素', '补光 LED（黄昏定时）'], warn: '镜头污损自检告警 · 上次清洁 11 天前 —— USGS 建议富营养温水体每 3 天维护' },
  { id: 'N05', role: '投饵机执行端', board: 'ESP32-C3 + 光耦继电器', fw: 'v0.9.3', batt: null, solar: false, rssi: -74, link: 'LoRa 433 MHz (SX1262)', lastSeen: '3 秒前', status: 'ok', sensors: ['光耦继电器（上电默认断开）', '霍尔电流互感器（"真在转"反馈）', '独立硬件最大时长封顶'] },
  { id: 'N06', role: '增氧机联动', board: 'ESP32-C3 + 固态继电器', fw: 'v0.9.0', batt: null, solar: false, rssi: -70, link: 'LoRa 433 MHz (SX1262)', lastSeen: '7 秒前', status: 'ok', sensors: ['固态继电器 40 A', '电流反馈（判断是否真在转）'] },
  { id: 'N07', role: '（进阶档）声呐 / 声光融合', board: '边缘计算盒 / 工控机', fw: 'n/a', batt: null, solar: false, rssi: -66, link: '以太网 / 4G', lastSeen: '未部署', status: 'idle', sensors: ['成像声呐阵列（参考华中农大 84.5% 方案）'], warn: '仅在"必须定量"时立项：预算与工程量是标准档的数倍，且需接受 8–15% 相对误差' },
];

/* ---------- 视觉模块：能做与不能做 ---------- */
const VISION = {
  intensity: [
    { meal: '早 06:40', level: '强', score: 0.86, conf: 0.93, intakeMin: 22, note: '水面破碎波密集，光流强度 V=0.71' },
    { meal: '午 12:30', level: '强', score: 0.81, conf: 0.90, intakeMin: 25, note: '高光斑块面积占比 6.4%' },
    { meal: '晚 17:30', level: '中', score: 0.58, conf: 0.88, intakeMin: 33, note: '摄食响应区间比早餐缩短 21%，纹理熵下降' },
  ],
  canDo: [
    { k: '摄食强度分级（强/中/弱/无）', v: '✅ 可做', why: '光流运动强度 + 水面纹理，二分类测试集 95.83%、96.53%（清水 RAS 场景）' },
    { k: '食欲衰退趋势 → 提前停投', v: '✅ 可做', why: '这是本模块唯一进入决策链的用途：反馈层的末梢' },
    { k: '浮头 / 死鱼漂浮 / 水色突变 告警', v: '✅ 可做', why: '定性事件识别，不涉及计量' },
    { k: '镜头污损自检', v: '✅ 已内置', why: '清晰度指标低于阈值即告警——污损是历史系统误分类的首要人为原因（约占 24%）' },
  ],
  cannotDo: [
    { k: '数出鱼的尾数', v: '❌ 不可做', why: '鱼在水面下 20–50 cm，本塘透明度仅约 38 cm。定量闭环：20–40 cm 透明度 ≈ 29–45 NTU（USGS 回归 SDD=3.390×NTU^−0.637），而 30 NTU 时普通水下相机有效视距只有约 10 cm。后向散射会饱和成"面纱光"——远处不是变暗而是变成均匀亮场，场景对比度不再存在。信息物理上已不在图像里，增强算法救不回来。' },
    { k: '用摄像头把鱼"看清"', v: '❌ 公开成绩单 mAP 38.93%', why: 'DePondFi\'23 挑战赛（NCVPRIPG 2023）的目标原文就是"克服低能见度与浊度变化"，60 人注册、15 队提交，冠军 DETECTRON 的 mAP 仅 38.93%，后续 36.65% / 31.63% / 29.06%。对比：鱼苗导槽场景误差 3–4%、金枪鱼聚集分箱 98%。"池塘"是公认的开放难题。' },
    { k: '测体长 / 测体重', v: '❌ 不可做', why: '单目无尺度基准、无双目标定、无测距；像素无法反推真实体长。' },
    { k: '数残饵颗粒', v: '❌ 几何否决', why: '5 m 高 / 90° 视场 / 1920 px → 地面采样距离 5.2 mm/px；3 mm 颗粒仅占 0.6 像素，而颗粒检测的经验门槛是 >30 像素。' },
    { k: '水下相机长期值守', v: '❌ 维护不可行', why: 'USGS TM1-D3 官方文件：营养富集且温度中高的站点"可能需要每三天维护一次"——中国南方精养土塘正是这一档。PLOS ONE 2022（13 万张图）实测：最短 1 个月内鱼类识别即不可行，中位耐久 2 个月；加防污船底漆未能阻止镜头在 2–3 月内被完全遮挡。另：蓝宝石只解决耐刮擦，不防污。"蓝宝石防污"在文献中不成立。' },
    { k: '用投喂量反推存塘量（自校准）', v: '❌ 正反馈发散', why: '过量投喂被读成"鱼变多了" → 下次投更多 → 误差单向累积。机制上是"没有量测输出的开环积分器"，属控制理论推断，未找到形式化定理（已标注）。' },
    { k: '数鳙鱼/鲢鱼为主的塘（声学也不行）', v: '❌ TS–体长关系不成立', why: '鲤科 b₂₀ 一般在 −60 ~ −69 dB（鲫 −64.7~−65.8、鳊 −65.4~−66.5），但鲢鱼无显著关系（P = 0.37）。南方土塘主养鱼种恰在这个盲区。' },
  ],
  geometry: { camH: 5.0, fovDeg: 90, pxWidth: 1920, pelletMM: 3, thresholdPx: 30 },

  /* 如果坚持要定量：三条路径与它们的真实代价（全部带来源） */
  ifMustQuantify: [
    { p: '路径 A', n: '声光融合走航', acc: '85% – 92%', err: '相对误差 8% – 15%', src: '中国水科院淡水渔业研究中心，2026-07-14 官方发布；江苏宜兴鳊、鲫规模化基地验证', grade: 'B',
      note: '目前中国土塘场景最乐观的可溯源数字。但注意三件事：① 用词是"体量与密度的综合评估"，不是逐尾计数；② 只在鳊、鲫两个鱼种上验证；③ 机构自报，未见同行评议论文与第三方复现。' },
    { p: '路径 B', n: '成像声呐定点阵列', acc: '84.5%', err: '相对误差 15.5%', src: '高鑫等《基于动态声呐成像抗噪感知的池塘鱼群生物量统计方法研究》，水生生物学报 2026, 50(7): 072614', grade: 'A',
      note: '真实的透明度 12–15 cm 浑浊池塘全塘计数。论文原话："传统基于光学图像的机器视觉方法在此场景下难以奏效——即便辅以图像增强技术，鱼体目标仍难以稳定显现。"' },
    { p: '路径 C', n: '抽样称重 + 一次排干真值标定', acc: '生物量层面 ±5% 级', err: '尾数层面远大于此', src: 'Aunsmo 2013, Aquaculture 396-399:113-118（挪威 3 大生产商 240 个网箱）', grade: 'A',
      note: '最便宜，也是工业界实际做法。但有一个反直觉发现：网箱级平均绝对生物量误差 5.1%，是因为尾数误差与均重误差反向关联、互相补偿。一旦你只要尾数，补偿消失，误差立刻暴露——这是"数鱼"比"估生物量"难得多的深层原因。' },
  ],

  /* 为什么 ESP32 不能自己跑鱼类识别 —— 乐鑫官方 benchmark */
  edgeAI: {
    bench: [
      { m: 'yolo11n @320（目标检测）', v: '6,196 ms/帧', fps: '0.16 FPS' },
      { m: 'yolo11n @640（目标检测）', v: '26,000 ms/帧', fps: '0.04 FPS' },
      { m: 'MobileNetV2（分类）', v: '877 ms/帧', fps: '1.14 FPS' },
      { m: '行人检测 @224（单类）', v: '~128 ms/帧', fps: '7.7 – 7.9 FPS' },
      { m: '人脸检测（单类，小模型）', v: '~37 ms/帧', fps: '26.9 FPS' },
    ],
    src: '乐鑫官方 esp-dl COCO benchmark（esp-dl/models/coco_detect/README.md）',
    zeroEvidence: 'GitHub API 全量检索：fish + detection + esp32 → total_count = 5，全部 0 star；fish + detection + tinyml 与 fish + detector + microcontroller → 均为 0。现有项目要么只做采集推流（推理在 PC/云端），要么 README 宣称端侧 CNN-LSTM 而仓库里只有一个 React 网页、零固件。唯一近似的学术工作（TinyML 鱼病检测，Aquaculture International 2025）用的还是 RISC-V MCU，不是 ESP32。',
    architecture: '正确分工：ESP32-S3 只做"在正确时刻拍下正确的照片并上传"+ 低分辨率单类触发；AI 推理放云端；水质预测用经典 ML（Sensors 2025 有真·ESP32 端侧多元线性回归部署，R² ≈ 0.65–0.72）。',
  },
};

/* ---------- 证据台账 ---------- */
const EVIDENCE = [
  { claim: '不用任何视觉信号，仅「溶氧 + 水温 + 体重」的池塘精准投喂系统已让饵料系数降低 11.73%', grade: 'A', src: '赵思琪等《池塘水产养殖精准投喂系统研制与试验》，农业工程学报 2023, 39(22)', url: 'http://www.tcsae.org/article/doi/10.11975/j.issn.1002-6819.202305105', use: '支撑"传感器路线优先于摄像头路线"' },
  { claim: 'FAO 官方原话：「至今没有人找到令人满意的存塘量评估方法」', grade: 'A', src: 'FAO 水产养殖技术报告', url: '', use: '⭐ 工业界的做法是绕开存塘量问题，不是硬解它' },
  { claim: '挪威 240 个网箱实测：生物量误差 5.1%，但尾数误差与均重误差反向关联、互相补偿', grade: 'A', src: 'Aunsmo et al. 2013, Aquaculture 396-399:113-118', url: '', use: '⭐ 解释"为什么数鱼比估生物量难得多"——只要尾数，补偿就消失' },
  { claim: '中国水科院淡水中心：声光融合在真实土塘对鳊、鲫"体量与密度"评估准确率 85%–92%', grade: 'B', src: '淡水渔业研究中心官方发布，2026-07-14', url: 'https://www.cafs.ac.cn/info/1024/96852.htm', use: '目前土塘场景最乐观的可溯源数字；⚠️ 机构自报、未同行评议、非逐尾计数' },
  { claim: '华中农大在透明度 12–15 cm 池塘用成像声呐实现全塘计数 84.5%', grade: 'A', src: '高鑫等，水生生物学报 2026, 50(7): 072614（国家重点研发计划 2023YFD2400501）', url: '', use: '国内最权威的浑浊池塘计数实测' },
  { claim: '纯光学在池塘场景的公开最好成绩是 mAP 38.93%', grade: 'A', src: 'DePondFi\'23 挑战赛（NCVPRIPG 2023），15 支队伍提交', url: '', use: '判定"摄像头数鱼"不可行' },
  { claim: '单目远距摄像头数 3 mm 颗粒在几何上不成立（0.6 px vs 30 px 门槛）', grade: 'A', src: 'Parsonage & Petrell 2003, Aquacultural Engineering；几何测算见本项目报告附录 A', url: 'https://doi.org/10.1016/S0144-8609(03)00049-9', use: '否决"数残饵颗粒"' },
  { claim: '残饵检测的历史系统误分类中约 24% 来自相机维护不良（污损）', grade: 'A', src: 'Parsonage & Petrell 2003 同文', url: 'https://doi.org/10.1016/S0144-8609(03)00049-9', use: '镜头污损自检的必要性' },
  { claim: 'USGS 官方：营养富集且温度中高的水体，水下镜头可能需要每三天维护一次', grade: 'A', src: 'USGS TM1-D3 技术文件', url: '', use: '否决"水下相机长期值守"——南方精养土塘正在这一档' },
  { claim: '13 万张图像实测：最短 1 个月内鱼类识别即不可行，中位耐久 2 个月', grade: 'A', src: 'PLOS ONE 2022 生物污损长期观测', url: '', use: '同上；且加防污船底漆未能阻止镜头被完全遮挡' },
  { claim: '「蓝宝石防污」在文献中不成立——蓝宝石只解决耐刮擦（Mohs 9）', grade: 'A', src: '生物污损专题调研（多来源交叉）', url: '', use: '避免为伪需求多付钱' },
  { claim: '红外对射计数器即便装在鱼道里，中等通过率下仍低估 56–84%', grade: 'A', src: 'Baumgartner et al. 2012, J. Appl. Ichthyology 28(4):531-536', url: 'https://doi.org/10.1111/j.1439-0426.2012.01947.x', use: '否决红外光幕路线；开放土塘连安装条件都不具备' },
  { claim: '分裂波束声学的表面死区约 1.9–2.2 m，会吃掉整个 2 m 水柱', grade: 'A', src: '水声学专题调研（多来源交叉）', url: '', use: '否决垂直波束在浅塘的可用性' },
  { claim: '鲢鱼的 TS–体长关系不成立（P = 0.37）', grade: 'A', src: '目标强度专题调研', url: '', use: '⚠️ 南方土塘主养鱼种恰在声学盲区' },
  { claim: '溶氧曲线反推生物量不可辨识：鱼仅占总耗氧约 7%，浮游生物/细菌占 70–80%，底泥 SOD 有 16 倍跨度', grade: 'A', src: '池塘溶解氧收支专题调研', url: '', use: '否决"用溶氧反推存塘量"' },
  { claim: '标记重捕法经排干校验，偏差最大达 41%；鳗鲡塘系统性高估约 20%', grade: 'A', src: '池塘鱼类数量估计专题调研', url: '', use: '抽样推算只能给宽区间，不能给"计数"' },
  { claim: '华中农大王春芳团队专利原文自述：避开"水下声、光、电"方案，因"电气稳定性差、受混浊度影响大"', grade: 'A', src: '授权发明专利 ZL202110654210.2 说明书', url: '', use: '⭐ 该团队是设计阶段就排除光学，不是失败后才转向' },
  { claim: '乐鑫官方 esp-dl benchmark：yolo11n@320 在 ESP32-S3 上 6,196 ms/帧（0.16 FPS）；@640 为 26 秒/帧', grade: 'A', src: 'esp-dl/models/coco_detect/README.md', url: 'https://raw.githubusercontent.com/espressif/esp-dl/master/models/coco_detect/README.md', use: '⭐ 判定"ESP32 自己跑鱼类识别"不可行' },
  { claim: 'GitHub 全量检索 fish + detection + esp32 → 仅 5 个仓库，全部 0 star', grade: 'A', src: 'GitHub Search API', url: '', use: '"ESP32 做鱼类识别"零实证，写成红线' },
  { claim: '现有投饲设备缺少称量功能，投饲量控制不精准、难以集成管控', grade: 'A', src: '唐荣等，农业工程学报 2021, 37(9):289-296，中国水科院渔机所', url: 'https://search.napstic.cn/literature/periodical/010nygcxb202109033', use: '执行端定量精度是误差漏斗最窄处' },
  { claim: '人工标注的"摄食强度"标签本身噪声很大：比自动标注训练的模型低 13.13–18.46 个百分点', grade: 'A', src: 'Animals 2026, 16(5):720', url: '', use: '⚠️ 提醒：不要轻信用人工标签训练的视觉模型' },
  { claim: '抛撒均匀性实测水面覆盖率仅 18%–80%', grade: 'A', src: 'Aquacultural Engineering 2012，气动+旋转撒料器海水网箱实测', url: 'https://fmiri.ac.cn/info/1026/17494.htm', use: '称重只管"离仓质量对"，不管"落塘分布对"' },
  { claim: 'FAO 实测：即使样本量充分，拉网均重与干塘真值仍差 8–19%', grade: 'A', src: 'FAO 渔业技术报告', url: '', use: '存塘量误差 ±20–50% 的来源' },
  { claim: 'SC/T 1016.1~.7-1995（唯一规定过投饲率数字的行业标准）已全部废止', grade: 'A', src: '标准废止公告', url: '', use: '投饲率表只能对标 T/SCFA 0011—2023，且非本品种' },
  { claim: '雷击是水产养殖自动化系统损坏的主要原因之一（有中文核心期刊依据与真实事故案例）', grade: 'A', src: '王鹏祥等，渔业现代化 2009；另附西安、汕头两起真实事故报道', url: '', use: '防雷 SPD 是必需项，不是可选项；成本仅占潜在损失的 1%' },
  { claim: '池塘下层水温可比上层低 3–5 ℃ 或更多，极易造成底部缺氧（实测剖面 1m=4.90 / 2m=1.23 / 3m=1.05 mg/L）', grade: 'A', src: '邹城市农业农村局公开技术文件 + 剖面实测', url: '', use: '水温必须是三点链（表层 / 半深 / 离底），不是单点' },
  { claim: '30 NTU 浊度下普通水下相机有效视距仅约 10 cm', grade: 'B', src: '厂商实测报道，2025-12', url: '', use: '与 USGS 透明度回归互为印证' },
  { claim: '溶氧 < 5 mg/L 减半、< 3 mg/L 停喂', grade: 'B', name: '待校准', src: '传统经验值，本项目采用，须用本塘溶氧日变化曲线校准', url: '', use: '安全门阈值——**标注为待实测回填**' },
  { claim: '执行端标定 CV ≤ 10% 即可终身不上称重', grade: 'B', name: '工程判据', src: '本项目 B4 协议 v1.1；10% 是性价比截止线，不是精度目标', url: '', use: '标定 vs 称重闭环的裁决线' },
  { claim: 'GB 11607-89 规定非离子氨 ≤ 0.020 mg/L，且非离子氨占比随 pH 与水温剧变（pH 8.0+28 ℃ 约 5%，pH 8.5 超 10%）', grade: 'A', src: 'GB 11607-89 渔业水质标准', url: '', use: '零成本替代：用连续 pH + 水温把偶测总氨氮换算成非离子氨判越线，省下 ¥2,400+ 的在线氨氮' },
];

/* ---------- 红线 ---------- */
const REDLINES = [
  { t: 'LLM 不进数值决策回路', d: '所有参与决策的数字由确定性模块产生。LLM 只做录入、翻译、解释——它无权生成任何数字。', why: '单塘一年一个批次，十年十条样本，微调只会得到"自信的胡说机器"。' },
  { t: '不做无人确认的自动投喂决策', d: '建议必须经人工在界面确认后才下发执行。系统可自动执行"停喂"，但不可自动执行"加喂"。', why: '风险不对称——投喂不足是温和的错，投喂过量可能一夜死塘。' },
  { t: '不给点估计', d: '所有预测输出必须是区间 + 显式假设。界面上的每个区间都标出它为什么这么宽。', why: '不可辨识系统的点输出会伪装成"知道"，比"不知道"更危险。' },
  { t: '硬件层独立封顶', d: '投喂时段存在设备本地 NVS，断电恢复禁止补投，上电继电器默认断开，独立硬件最大时长封顶。', why: '真实事故教训：控制器掉线 → 倒光整仓料。' },
  { t: '空白就是空白', d: '没有可靠来源的数值，界面显示"无数据"，不许用近似品种的通用值填充。', why: '一旦系统开始"合理推测"，它就变成了一个自信的胡说机器。' },
  { t: 'ESP32 不做端侧鱼类识别', d: 'ESP32-S3 只做"在正确时刻拍下正确的照片并上传"+ 低分辨率单类触发。AI 推理放云端；水质预测用经典 ML。', why: '乐鑫官方 benchmark：yolo11n@320 = 6,196 ms/帧。GitHub 全量检索 fish+detection+esp32 仅 5 个仓库、全部 0 star——零实证。' },
  { t: '摄像头不做计数', d: '视觉模块的输出只有三类：摄食强度分级、异常事件告警、镜头污损自检。不得输出尾数、体长、体重或残饵粒数。', why: '纯光学在池塘的公开最好成绩 mAP 38.93%；声光融合的中国最好成绩 85–92%，且是"体量/密度"而非逐尾。' },
  { t: '验收指标不写"省料 X%"', d: '单塘没有对照组，这个数字在数学上无法测量。正确指标：记录完整率 → 建议采纳率 → 区间命中率 → 防死鱼成功次数。', why: '敢承诺"省料 X%"的一定在编。' },
];

/* ---------- 硬件 BOM（三档 · 价格均来自公开标价，需询价项已标注） ----------
   ⚠️ 价格口径：均为公开可查的页面标价（工业 B2B 口径）。
      淘宝/1688/京东详情页在本环境有登录墙，个人小批量实际到手价可能高 20–100%。 */
const BOM = {
  tiers: [
    { key: 'entry', name: '入门档', price: '≈ ¥640', for: '先把水温看上，不装在线溶氧。保住「表底温差 ≥ 3 ℃ 分层告警」这个零成本能力', items: [
      { n: '立创 ESP32-S3 N8R8 开发板', qty: 1, p: '¥27', note: '8MB Flash + 8MB PSRAM。注意：PSRAM 是为将来留的余量，不是为跑模型' },
      { n: '防水 DS18B20 探头（不锈钢封装）', qty: 2, p: '¥50 / 2 支', note: '⚠️ 假货率极高：eBay/AliExpress 探头几乎全假。用 ROM 码鉴别——真品为 28-xx-…-00-00-xx 之外的正常序列' },
      { n: '有人 USR-DR154 4G Cat-1 DTU', qty: 1, p: '¥98', note: '官方商城实价。RS485/TTL 转 4G，省掉自己调 PPP 的坑' },
      { n: '移动物联网卡 100 MB/年', qty: 1, p: '¥30 / 年', note: '⚠️ 机卡绑定：开发期换板子会触发停机，电信每月仅 2 次解绑额度。先定死硬件再激活卡' },
      { n: '光耦隔离继电器模块', qty: 1, p: '¥14', note: '控制增氧机；上电默认断开' },
      { n: '磷酸铁锂 6 Ah + 10 W 太阳能板 + CN3722 MPPT', qty: 1, p: '≈ ¥120', note: 'CN3722（¥3.06）是少数明确支持 LiFePO4 的 MPPT 充电 IC' },
      { n: 'IP67 防水盒 + PG7 接头 + 干燥剂', qty: 1, p: '≈ ¥60', note: '进水是户外电子设备第一大死因；真正路径是进出口与凝露' },
      { n: '两级防雷 SPD（电源 + 信号）', qty: 1, p: '≈ ¥55', note: '邦华 LT-MD/24 ¥25.5 + ZGS-V485 ¥25。西安雷击致增氧机停、死鱼 6000 斤损失约 3 万元' },
      { n: '手工检测：pH 试纸 / 氨氮比色管 / 透明度盘（萨氏盘）', qty: 1, p: '≈ ¥85', note: '⭐ 最划算的一笔：手工氨氮比在线氨氮省 ¥2,400+，而在线款在本场景根本不可用（见下方"坑"）' },
      { n: '合计', qty: null, p: '≈ ¥640', note: '不含投饵机。定位是"先有数据"，不是"先有自动化"' },
    ] },
    { key: 'std', name: '标准档 ⭐ 推荐', price: '≈ ¥2,950', for: '完整监测 + 投喂决策 + 执行端联动。超预算的主因只有一个：溶氧探头', items: [
      { n: 'DFRobot FireBeetle 2 ESP32-S3（岸边主控 N01）', qty: 1, p: '¥125', note: '比立创板贵但引脚与电源设计更规整，长期户外部署省心' },
      { n: 'ESP32-C3-MINI-1 模块 + 底板（传感节点 ×3）', qty: 3, p: '≈ ¥90', note: '低功耗节点，深睡电流 ~5 µA' },
      { n: '防水 DS18B20 ×3（表层 0.3 m / 半深 / 离底 0.3 m）', qty: 1, p: '¥75', note: '⭐ 必须三点，不是单点。实测剖面 1m=4.90 / 2m=1.23 / 3m=1.05 mg/L；下层水温可低 3–5 ℃' },
      { n: '工业荧光法溶氧探头（RS485 Modbus，IP68）', qty: 1, p: '¥1,000 – 5,000', note: '⭐ 全系统性价比最高、也最贵的一项。可选：中科智感 ESIN-N（¥1,000–5,000）、联测（¥1,500–3,000）。⚠️ 具体型号单价需询价' },
      { n: '工业 pH 电极 + RS485 变送（如 ES3300i 级）', qty: 1, p: '≈ ¥400', note: '电极是耗材，寿命 6–18 个月。它的第二个用途：把偶测总氨氮换算成非离子氨' },
      { n: 'ORP 电极（RS485，如 ES4100i 级）', qty: 1, p: '≈ ¥360', note: '溶氧的间接交叉校验信号' },
      { n: 'SHT31 温湿度 + BMP280 气压', qty: 1, p: '≈ ¥35', note: '气压是比水温更早的泛塘前兆——它值得一个独立传感器' },
      { n: '翻斗式雨量计（干簧管输出）', qty: 1, p: '¥60 – 150', note: '降雨后水质与投喂量的修正输入' },
      { n: '4G Cat-1 通信（DTU ¥98 + 卡 ¥30/年）', qty: 1, p: '¥128 首年', note: '⚠️ 必须用 MQTT 长连接。HTTP 短连接 + TLS 全握手年流量 702 MB，是 MQTT（40 MB）的 15.6 倍' },
      { n: 'LoRa 模块 433 MHz（SX1262）', qty: 2, p: '≈ ¥160', note: '⚠️ 别买 915 MHz——在中国不合法。433 MHz 限 10 dBm，市面 18–30 dBm 模块全部超限' },
      { n: '磷酸铁锂 12 V 12 Ah + 20 W 单晶板 + 带 LiFePO4 档的 MPPT', qty: 1, p: '≈ ¥290 – 450', note: '标准场景日耗电约 376 mAh（5 分钟上报 + 荧光法溶氧）。⚠️ 铅酸控制器充 LiFePO4 会死在"均充档"（14.8–15.5 V 远超 14.6 V 上限）——多花 ¥60 买带 LiFePO4 档的，不能省' },
      { n: 'DC-DC 降压 SY8205FCC', qty: 2, p: '≈ ¥3', note: '⚠️ 别用 LM2596：静态电流 5 mA（= ESP32 工作电流的 38%）、非同步、150 kHz 慢环路，面对 ESP32-S3 的 27 倍电流阶跃必然跌落' },
      { n: '两级防雷 SPD 全套（电源 + 信号 + 天线馈线）', qty: 1, p: '≈ ¥400', note: '含立杆馈线防雷器。必须单点接地 + 引线 ≤ 0.5 m——这是 SPD 失效的第一原因' },
      { n: '摄像头：ESP32-S3-CAM（OV5640）', qty: 1, p: '≈ ¥100', note: '⚠️ 只做"投喂时段触发抓拍 + 上传"，不做端侧推理（见下方"坑 2"）。定位是水面以上定点监测' },
      { n: 'IP68 防水盒、M12 接头、三防漆、防鼠咬波纹管、遮阳罩', qty: 1, p: '≈ ¥250', note: '夏季盒内温度可比气温高 20 ℃，遮阳是必须的' },
      { n: '合计', qty: null, p: '≈ ¥2,950', note: '要压到 ¥2,000：① 选溶氧价格区间下限型号（需询价）；② 或暂不装溶氧，用 ORP + 底层水温间接预警' },
    ] },
    { key: 'pro', name: '进阶档', price: '≈ ¥9,190（可按优先级砍到 ¥4,400–6,000）', for: '在标准档基础上加双点溶氧、EC、GPS 与冗余', items: [
      { n: '标准档全套', qty: 1, p: '≈ ¥2,950', note: '作为基础' },
      { n: '第二个溶氧探头（表层 + 底层双点）', qty: 1, p: '≈ ¥1,500', note: '⚠️ 第一个该砍的就是它——除非你做分层观测研究' },
      { n: 'EC / 电导率（RS485）', qty: 1, p: '≈ ¥800', note: '⚠️ 第二个该砍的。淡水池塘 EC 的决策价值很低，本来就不推荐' },
      { n: 'pH 升级 + 氨氮在线', qty: 1, p: '≈ ¥2,200', note: '⛔ 强烈建议砍掉，改手工。最便宜的在线氨氮数字传感器 ¥2,400，分析仪整机最低 ¥4 万；且 SEN0711 标 ±3%FS，0–100 mg/L 量程下 = ±3 mg/L，而池塘决策区间是 0.1–2 mg/L——该区间不可用' },
      { n: 'GPS 模块（ATGM336H）', qty: 1, p: '¥11', note: '⚠️ 对固定塘口几乎没用——塘不会移动。价值仅是资产登记与多塘口区分。⚠️ 别买 NEO-6M：u-blox 官方已 EOL，市面几乎全是 AT6558 冒充（假货开机报 $GNTXT 而非 $GPTXT，接天线就复位）' },
      { n: 'NB-IoT 冗余上行', qty: 1, p: '≈ ¥50 – 110', note: '双通道防单一网络故障' },
      { n: '便携溶氧仪（交叉校验用）', qty: 1, p: '¥200 – 500', note: '在线探头会漂移，你必须有第二把尺子' },
      { n: '料台（料罾）+ 近距相机 + 定时刮板', qty: 1, p: '¥300 – 700', note: '⭐ 唯一被验证可行的"残饵"视觉路线：相机看托盘，不看鱼。文献 MAE 2.0 粒' },
      { n: '小量程称量桶（增量法，HX711 + 5 kg 传感器）', qty: 1, p: '¥120 – 300', note: '⚠️ 仅在 B4 标定 CV > 10% 时才上。整仓称重是算术陷阱' },
      { n: '立杆、地笼、注塑外壳、遮阳罩', qty: 1, p: '¥400 – 900', note: '' },
      { n: '合计（未砍）', qty: null, p: '≈ ¥9,190', note: '⚠️ 如实标注：这一档会显著超过 ¥6,000' },
      { n: '合计（按优先级砍后）', qty: null, p: '≈ ¥4,400 – 6,000', note: '砍序：② 第二溶氧 → ③ EC → ④ 氨氮改手工 → ⑤ GPS' },
    ] },
  ],
  wires: [
    { n: 'DS18B20 三线防水电缆（屏蔽，1 mm²）', p: '¥4 – 8 / 米', note: '1-Wire 总线，长线需 4.7 kΩ 上拉' },
    { n: 'RS485 屏蔽双绞线（2×0.75 mm²）', p: '¥3 – 6 / 米', note: '溶氧/pH/ORP 探头；总线两端 120 Ω 终端电阻' },
    { n: '太阳能板专用光伏线（2.5 mm²）', p: '¥5 – 9 / 米', note: '' },
    { n: 'PG7 / M12 防水接头、热缩管、防水胶泥', p: '¥30 – 80 / 套', note: '每个开孔都要用接头，盒内放干燥剂' },
    { n: '防鼠咬波纹管（金属或尼龙）', p: '¥3 – 6 / 米', note: '塘边鼠害与鸟类啄线是真实问题' },
    { n: '⚠️ 12 V 直流严禁长距离走线', p: '—', note: '水下探头到主控的距离：PoE ≤ 100 m、USB ≤ 5 m。超过就地变送成 RS485' },
  ],
};

/* ---------- 分阶段路线 ---------- */
const ROADMAP = [
  { p: 'P0', days: '第 1 周', cost: '0 元', title: '现场摸底与品种确认',
    do: ['填写 A7 现场信息清单（面积/水深/品种/放养量/历史投喂/死亡记录）', '确认主养品种——投饲率表与生长模型全部是品种专属的', '用手机在同机位拍 3 天投喂时段视频，做"照片质量门"评估'],
    stop: '品种未定 → 一切数字都是空转，不许开工下一步' },
  { p: 'P1', days: '第 2–4 周', cost: '480 – 720 元', title: '传感底座：先把水温与溶氧看上',
    do: ['搭建入门档：ESP32-S3 + 三层水温 + 溶氧探头', '用便携溶氧仪做交叉校验，建立本塘溶氧日变化曲线', '连续采集 2 周，回填安全门阈值（5/3 mg/L 是经验值，必须校准）'],
    stop: '溶氧探头未校准 → 安全门不可信，不许接执行器' },
  { p: 'P2', days: '第 5–8 周', cost: '1,600 – 2,700 元（补齐标准档）', title: '决策链闭环：投喂建议 + 人工确认 + 执行',
    do: ['上线投喂决策模块：生物量 × 投饲率 × 环境修正 → 区间建议', '做 B4 执行端标定（3×3×3：粒径 × 料位 × 电压，每格 20 次重复）', '接光耦继电器控制投饵机，人工确认后下发', '接电流互感器做"真在转"反馈'],
    stop: 'B4 未标定 → 投饵机只能手控，系统只出建议不出执行' },
  { p: 'P3', days: '第 9–16 周', cost: '500 – 1,300 元', title: '视觉旁路 + 台账数字化',
    do: ['接入投料点相机，做「摄食强度分级 → 食欲衰退提前停投」', '镜头污损自检告警', '台账数字化：批次 / 投喂 / 死亡 / 出塘，完整率目标 ≥ 95%'],
    stop: '照片质量门不过 → 视觉模块整体降级为"看塘直播"，不影响主链' },
  { p: 'P4', days: '第 2 季起', cost: '视实测而定', title: '（可选）料台近距视觉 / 称量桶 / 产量区间',
    do: ['若 B4 判据 CV > 10%，上小量程称量桶（增量法）', '若需要残饵判据，上料台近距相机（MAE 2.0 粒），不是塘面全景', '积累满一个养殖季后，做积温-生长外推的产量区间'],
    stop: '无回测不上线；区间命中率未达标不扩产' },
];
