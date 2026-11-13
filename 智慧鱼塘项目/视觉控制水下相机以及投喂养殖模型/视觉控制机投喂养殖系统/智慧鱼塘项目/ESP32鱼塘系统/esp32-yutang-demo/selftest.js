/* 无头冒烟测试：用最小的 DOM 桩跑通全部 8 个视图，
   并检查输出 HTML 中是否混入 undefined / NaN（模板 bug 的典型症状）。
   运行：node selftest.js                                            */
const fs = require('fs');
const path = require('path');
const here = __dirname;

/* ---------- 极简 DOM / Canvas 桩 ---------- */
const stub = new Proxy(function () {}, {
  get(t, k) {
    if (k === 'width' || k === 'height') return 120;
    if (k === 'length') return 0;
    if (k === Symbol.toPrimitive || k === 'toString') return () => '';
    if (k === 'textContent' || k === 'innerHTML') return '';
    if (k === 'dataset') return {};
    return stub;
  },
  set() { return true; },
  apply() { return stub; },
  has() { return true; },
});

global.window = { devicePixelRatio: 2, addEventListener() {}, scrollTo() {}, innerWidth: 1440, innerHeight: 900 };
global.document = {
  querySelector: () => stub, querySelectorAll: () => [],
  createElement: () => stub, body: stub, addEventListener() {},
};
global.requestAnimationFrame = (fn) => fn();
global.setInterval = () => 0;
global.setTimeout = (fn) => 0;

/* ---------- 载入源码（剥掉 app.js 末尾的启动语句） ---------- */
const dataSrc = fs.readFileSync(path.join(here, 'data.js'), 'utf8');
let appSrc = fs.readFileSync(path.join(here, 'app.js'), 'utf8');
const cut = appSrc.indexOf('/* ---------- 启动 ---------- */');
if (cut > -1) appSrc = appSrc.slice(0, cut);
// tooltip / 导航 等副作用代码块也一并剥掉
appSrc = appSrc.replace(/const tip = document\.createElement[\s\S]*?\}\);\n/, '');

const chartsSrc = fs.readFileSync(path.join(here, 'charts.js'), 'utf8');

const mod = {};
const factory = new Function('module', 'exports', `
${dataSrc}
${chartsSrc}
${appSrc}
module.exports = { RENDERERS, VIEWS, SCENARIOS, buildDecisionChain, makeSeries, currentEnv, state };
`);
factory(mod, mod.exports);
const { RENDERERS, VIEWS, SCENARIOS, state } = mod.exports;

/* ---------- 跑 ---------- */
let fail = 0;
const badPatterns = [
  [/undefined/, 'undefined'],
  [/NaN/, 'NaN'],
  [/\[object Object\]/, '[object Object]'],
  [/\$\{/, '未求值的模板占位'],
];

console.log('视图冒烟测试 · ' + VIEWS.length + ' 个视图 × ' + Object.keys(SCENARIOS).length + ' 个情景\n');

for (const v of VIEWS) {
  for (const k of Object.keys(SCENARIOS)) {
    state.view = v.k; state.scn = k; state.override = null; state.confirmed = false;
    let html = '';
    try {
      html = RENDERERS[v.k]();
    } catch (e) {
      console.log(`  ✗ ${v.cn.padEnd(8)} / ${k.padEnd(8)} 抛异常: ${e.message}`);
      fail++; continue;
    }
    const hits = badPatterns.filter(([re]) => re.test(html)).map(([, n]) => n);
    const size = (html.length / 1024).toFixed(1);
    if (hits.length) {
      console.log(`  ✗ ${v.cn.padEnd(8)} / ${k.padEnd(8)} ${size}KB  含: ${hits.join(', ')}`);
      const m = html.match(/.{0,70}(undefined|NaN|\[object Object\]).{0,70}/);
      if (m) console.log(`      … ${m[0].replace(/\s+/g, ' ')}`);
      fail++;
    } else {
      console.log(`  ✓ ${v.cn.padEnd(8)} / ${k.padEnd(8)} ${size}KB`);
    }
  }
}

/* ---------- 决策链自洽性断言 ---------- */
console.log('\n决策链自洽性检查');
for (const k of Object.keys(SCENARIOS)) {
  const d = mod.exports.buildDecisionChain(SCENARIOS[k]);
  const chk = [
    ['建议下限 ≤ 上限', d.finalLo <= d.finalHi + 1e-9],
    ['推荐落在区间内', d.recommend >= d.finalLo - 1e-9 && d.recommend <= d.finalHi + 1e-9],
    ['上限未超硬封顶', d.finalHi <= d.hardCap + 1e-9],
    ['钳制系数 ∈ [0,1]', d.clampFactor >= 0 && d.clampFactor <= 1 + 1e-9],
    ['缺氧情景必须归零', k !== 'hypoxia' || d.finalHi === 0],
    ['非缺氧情景不得归零', k === 'hypoxia' || d.finalHi > 0],
    ['高温情景只减不增', k !== 'heat' || d.clampFactor < 1],
    ['常态情景不钳制', k !== 'normal' || d.clampFactor === 1],
  ];
  const bad = chk.filter(([, ok]) => !ok).map(([n]) => n);
  console.log(`  ${bad.length ? '✗' : '✓'} ${k.padEnd(8)} ${bad.length ? '违反: ' + bad.join(' / ') : '全部通过'}`);
  if (bad.length) fail++;
}

/* ---------- 序列与极值一致性 ---------- */
console.log('\n传感序列与情景极值一致性');
for (const k of Object.keys(SCENARIOS)) {
  const s = SCENARIOS[k], ser = mod.exports.makeSeries(s);
  const dMin = Math.min(...ser.do_), dMax = Math.max(...ser.do_);
  const tMin = Math.min(...ser.temp), tMax = Math.max(...ser.temp);
  const okDO = Math.abs(dMin - s.env.doMin) < 0.25 && Math.abs(dMax - s.env.doMax) < 0.25;
  const okT = Math.abs(tMin - s.env.tempMin) < 0.25 && Math.abs(tMax - s.env.tempMax) < 0.25;
  console.log(`  ${okDO && okT ? '✓' : '✗'} ${k.padEnd(8)} DO ${dMin.toFixed(2)}–${dMax.toFixed(2)} (目标 ${s.env.doMin}–${s.env.doMax}) · T ${tMin.toFixed(1)}–${tMax.toFixed(1)} (目标 ${s.env.tempMin}–${s.env.tempMax})`);
  if (!okDO || !okT) fail++;
}

console.log(`\n${fail === 0 ? '✅ 全部通过' : '❌ ' + fail + ' 项失败'}`);
process.exit(fail === 0 ? 0 : 1);
