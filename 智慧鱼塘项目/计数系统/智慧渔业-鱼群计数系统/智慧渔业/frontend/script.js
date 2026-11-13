// ═══════════════════════════════════════════════════
// 鱼群计数工具 — 交互脚本（密度估计 + 连通域 + 标记图）
// ═══════════════════════════════════════════════════

let originalImage = null;
let countAnimFrame = null;

// ───────────── 初始化 ─────────────
function init() {
    initParticles();
    bindEvents();
}

function bindEvents() {
    const upload = document.getElementById('imageUpload');
    const zone = document.getElementById('uploadZone');
    const processBtn = document.getElementById('processButton');
    const method = document.getElementById('thresholdMethod');
    const slider = document.getElementById('fixedThreshold');
    const countMode = document.getElementById('countMode');
    const copyBtn = document.getElementById('copyResult');
    const exportBtn = document.getElementById('exportResult');

    // 文件上传
    upload.addEventListener('change', handleImageUpload);

    // 拖拽上传
    zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length) handleFile(files[0]);
    });

    // 方法切换 → 显示/隐藏固定阈值
    method.addEventListener('change', () => {
        document.getElementById('fixedThresholdField').classList.toggle('hidden', method.value !== 'fixed');
    });

    // 计数模式切换 → 显示/隐藏对应参数
    countMode.addEventListener('change', () => {
        const isDensity = countMode.value === 'density';
        document.getElementById('avgFishAreaField').classList.toggle('hidden', !isDensity);
        document.getElementById('minAreaField').classList.toggle('hidden', isDensity);
    });

    // 滑块
    slider.addEventListener('input', () => {
        document.getElementById('fixedThresholdValue').textContent = slider.value;
    });

    // 处理按钮
    processBtn.addEventListener('click', processImage);

    // 复制 & 导出
    copyBtn.addEventListener('click', copyResultToClipboard);
    exportBtn.addEventListener('click', exportResultToFile);
}

// ───────────── 背景粒子 ─────────────
function initParticles() {
    const container = document.getElementById('bgParticles');
    for (let i = 0; i < 16; i++) {
        const p = document.createElement('div');
        p.className = 'particle';
        const size = 2 + Math.random() * 3;
        p.style.cssText = `width:${size}px;height:${size}px;left:${Math.random()*100}%;animation-duration:${12+Math.random()*18}s;animation-delay:${Math.random()*12}s;`;
        container.appendChild(p);
    }
}

// ───────────── 图像上传 ─────────────
function handleImageUpload(e) {
    const file = e.target.files[0];
    if (file) handleFile(file);
}

function handleFile(file) {
    if (!file.type.match('image.*')) {
        showToast('请上传图像文件（JPG/PNG）', 'error');
        return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
            originalImage = img;
            drawOriginalImage();
            document.getElementById('processButton').disabled = false;
            updateBadge('originalBadge', '已加载', true);
            showToast('图像加载成功');
        };
        img.onerror = () => showToast('图像加载失败', 'error');
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function drawOriginalImage() {
    if (!originalImage) return;
    const canvas = document.getElementById('originalCanvas');
    const ctx = canvas.getContext('2d');
    const maxW = 520, maxH = 420;
    const ratio = Math.min(maxW / originalImage.width, maxH / originalImage.height, 1);
    canvas.width = Math.round(originalImage.width * ratio);
    canvas.height = Math.round(originalImage.height * ratio);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(originalImage, 0, 0, canvas.width, canvas.height);
    togglePlaceholder('original', false);
}

// ═══════════════════════════════════════════════════
// 核心处理流程
// ═══════════════════════════════════════════════════
function processImage() {
    if (!originalImage) { console.warn('processImage: no image'); return; }
    const start = performance.now();

    // 读取参数
    const method = document.getElementById('thresholdMethod').value;
    const fixedVal = parseInt(document.getElementById('fixedThreshold').value);
    const invert = document.getElementById('invertBinarize').checked;
    const countMode = document.getElementById('countMode').value;
    const avgArea = parseInt(document.getElementById('avgFishArea').value) || 70;
    const minArea = parseInt(document.getElementById('minArea').value) || 20;
    console.log('[params]', { method, fixedVal, invert, countMode, avgArea, minArea });

    // 1. 转灰度
    const gray = convertToGrayscale(originalImage);
    console.log('[gray]', gray.width, 'x', gray.height);

    // 2. 可选轻模糊（默认 1px，避免抹掉小鱼点）
    const blurRadius = 1;
    const blurred = blurRadius > 0 ? applyFastBlur(gray, blurRadius) : gray;

    // 3. 二值化
    let binary;
    switch (method) {
        case 'otsu': binary = applyOtsuThreshold(blurred, invert); break;
        case 'fixed': binary = applyFixedThreshold(blurred, fixedVal, invert); break;
        default: binary = applyOtsuThreshold(blurred, invert);
    }
    console.log('[binary]', binary.width, 'x', binary.height);

    // 4. 显示二值化结果
    drawToCanvas('binaryCanvas', binary);
    togglePlaceholder('binary', false);
    updateBadge('binaryBadge', '已处理', true);

    // 5. 计数 & 获取打点坐标
    const totalPixels = binary.width * binary.height;
    const fgPixels = countForegroundPixels(binary);
    const fgRatio = (fgPixels / totalPixels * 100).toFixed(2);
    console.log('[fg]', fgPixels, '/', totalPixels, '=', fgRatio + '%');

    let count, points;
    if (countMode === 'density') {
        count = Math.max(0, Math.round(fgPixels / avgArea));
        console.log('[density] count =', count, '(', fgPixels, '/', avgArea, ')');
        const sampleCount = Math.min(count, 1500);
        points = sampleForegroundPoints(binary, sampleCount);
    } else {
        const result = countConnectedComponents(binary, minArea);
        count = result.count;
        points = result.centroids;
        console.log('[connected] count =', count, 'centroids =', points.length);
    }

    // 6. 绘制标记图
    drawMarkedImage(originalImage, points, count);
    togglePlaceholder('mark', false);
    updateBadge('markBadge', `估算 ${count} 条`, true);

    // 7. 更新结果（先直接写入确保显示，再做动画）
    const elapsed = (performance.now() - start).toFixed(1);
    document.getElementById('fishCount').textContent = count;
    document.getElementById('processTime').textContent = elapsed;
    animateCount('fishCount', count);
    animateCount('processTime', parseFloat(elapsed), false);
    showToast(`估算 ${count} 条 | 前景占比 ${fgRatio}%`);
}

// ───────────── 图像处理工具函数 ─────────────
function convertToGrayscale(image) {
    const c = document.createElement('canvas');
    c.width = image.width;
    c.height = image.height;
    const ctx = c.getContext('2d');
    ctx.drawImage(image, 0, 0);
    const d = ctx.getImageData(0, 0, c.width, c.height);
    for (let i = 0; i < d.data.length; i += 4) {
        const g = Math.round(0.299 * d.data[i] + 0.587 * d.data[i + 1] + 0.114 * d.data[i + 2]);
        d.data[i] = d.data[i + 1] = d.data[i + 2] = g;
    }
    ctx.putImageData(d, 0, 0);
    return c;
}

function applyFastBlur(canvas, radius) {
    // 用 CSS filter 在 canvas 上快速实现高斯模糊
    const c = document.createElement('canvas');
    c.width = canvas.width;
    c.height = canvas.height;
    const ctx = c.getContext('2d');
    ctx.filter = `blur(${radius}px)`;
    ctx.drawImage(canvas, 0, 0);
    ctx.filter = 'none';
    return c;
}

function applyFixedThreshold(grayCanvas, thresh, invert) {
    const ctx = grayCanvas.getContext('2d');
    const d = ctx.getImageData(0, 0, grayCanvas.width, grayCanvas.height);
    for (let i = 0; i < d.data.length; i += 4) {
        const isFg = invert ? (d.data[i] < thresh) : (d.data[i] >= thresh);
        const v = isFg ? 255 : 0;
        d.data[i] = d.data[i + 1] = d.data[i + 2] = v;
        d.data[i + 3] = 255;
    }
    return putToCanvas(d, grayCanvas.width, grayCanvas.height);
}

function applyOtsuThreshold(grayCanvas, invert) {
    const ctx = grayCanvas.getContext('2d');
    const d = ctx.getImageData(0, 0, grayCanvas.width, grayCanvas.height);
    const hist = new Array(256).fill(0);
    for (let i = 0; i < d.data.length; i += 4) hist[d.data[i]]++;

    const total = d.data.length / 4;
    let sum = 0;
    for (let i = 0; i < 256; i++) sum += i * hist[i];

    let sumB = 0, wB = 0, wF = 0, varMax = 0, thr = 0;
    for (let i = 0; i < 256; i++) {
        wB += hist[i];
        if (wB === 0) continue;
        wF = total - wB;
        if (wF === 0) break;
        sumB += i * hist[i];
        const mB = sumB / wB, mF = (sum - sumB) / wF;
        const v = wB * wF * (mB - mF) ** 2;
        if (v > varMax) { varMax = v; thr = i; }
    }

    for (let i = 0; i < d.data.length; i += 4) {
        const isFg = invert ? (d.data[i] < thr) : (d.data[i] >= thr);
        const v = isFg ? 255 : 0;
        d.data[i] = d.data[i + 1] = d.data[i + 2] = v;
        d.data[i + 3] = 255;
    }
    return putToCanvas(d, grayCanvas.width, grayCanvas.height);
}

function putToCanvas(data, w, h) {
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    c.getContext('2d').putImageData(data, 0, 0);
    return c;
}

function drawToCanvas(canvasId, srcCanvas) {
    const canvas = document.getElementById(canvasId);
    const ctx = canvas.getContext('2d');
    const maxW = 520, maxH = 280;
    const ratio = Math.min(maxW / srcCanvas.width, maxH / srcCanvas.height, 1);
    canvas.width = Math.round(srcCanvas.width * ratio);
    canvas.height = Math.round(srcCanvas.height * ratio);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(srcCanvas, 0, 0, canvas.width, canvas.height);
}

// ───────────── 前景像素统计 ─────────────
function countForegroundPixels(binaryCanvas) {
    const ctx = binaryCanvas.getContext('2d');
    const d = ctx.getImageData(0, 0, binaryCanvas.width, binaryCanvas.height).data;
    let count = 0;
    for (let i = 0; i < d.length; i += 4) {
        if (d[i] === 255) count++;
    }
    return count;
}

// 在前景区域均匀采样打点坐标
function sampleForegroundPoints(binaryCanvas, maxPoints) {
    const w = binaryCanvas.width, h = binaryCanvas.height;
    const ctx = binaryCanvas.getContext('2d');
    const d = ctx.getImageData(0, 0, w, h).data;
    const points = [];

    // 网格采样，避免聚集
    const gridSize = Math.max(8, Math.floor(Math.sqrt((w * h) / maxPoints)));
    for (let gy = 0; gy < h; gy += gridSize) {
        for (let gx = 0; gx < w; gx += gridSize) {
            let sx = 0, sy = 0, sc = 0;
            for (let y = gy; y < Math.min(gy + gridSize, h); y++) {
                for (let x = gx; x < Math.min(gx + gridSize, w); x++) {
                    if (d[(y * w + x) * 4] === 255) {
                        sx += x; sy += y; sc++;
                    }
                }
            }
            if (sc > 0) {
                points.push({ x: Math.round(sx / sc), y: Math.round(sy / sc) });
            }
        }
    }
    return points;
}

// ───────────── 连通域检测 ─────────────
function countConnectedComponents(binaryCanvas, minArea) {
    const w = binaryCanvas.width, h = binaryCanvas.height;
    const ctx = binaryCanvas.getContext('2d');
    const d = ctx.getImageData(0, 0, w, h).data;
    const visited = new Uint8Array(w * h);
    const centroids = [];
    let count = 0;

    for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
            const idx = y * w + x;
            if (!visited[idx] && d[idx * 4] === 255) {
                const comp = floodFillCollect(x, y, w, h, visited, d);
                if (comp.area >= minArea) {
                    count++;
                    centroids.push({
                        x: Math.round(comp.sumX / comp.area),
                        y: Math.round(comp.sumY / comp.area)
                    });
                }
            }
        }
    }
    return { count, centroids };
}

function floodFillCollect(sx, sy, w, h, visited, data) {
    const stack = [[sx, sy]];
    let area = 0, sumX = 0, sumY = 0;
    while (stack.length) {
        const [x, y] = stack.pop();
        const idx = y * w + x;
        if (x < 0 || x >= w || y < 0 || y >= h || visited[idx] || data[idx * 4] !== 255) continue;
        visited[idx] = 1;
        area++;
        sumX += x;
        sumY += y;
        stack.push([x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]);
    }
    return { area, sumX, sumY };
}

// ───────────── 绘制标记图 ─────────────
function drawMarkedImage(srcImage, points, totalCount) {
    const canvas = document.getElementById('markCanvas');
    const ctx = canvas.getContext('2d');
    const maxW = 520, maxH = 280;
    const ratio = Math.min(maxW / srcImage.width, maxH / srcImage.height, 1);
    const cw = Math.round(srcImage.width * ratio);
    const ch = Math.round(srcImage.height * ratio);
    canvas.width = cw;
    canvas.height = ch;

    // 先画原图（半透明暗化）
    ctx.clearRect(0, 0, cw, ch);
    ctx.globalAlpha = 0.25;
    ctx.drawImage(srcImage, 0, 0, cw, ch);
    ctx.globalAlpha = 1;

    // 根据密度决定点大小：1500+ 用 1px，稀疏用 2-3px
    const density = points.length / (srcImage.width * srcImage.height);
    const r = density > 0.001 ? 1 : (density > 0.0003 ? 1.5 : 2.5);

    // 绘制红点
    const sx = cw / srcImage.width;
    const sy = ch / srcImage.height;
    ctx.fillStyle = '#ff4757';
    for (const p of points) {
        const px = Math.round(p.x * sx);
        const py = Math.round(p.y * sy);
        ctx.fillRect(px - r + 1, py - r + 1, r, r);
    }

    // 数量标签（跟左侧面板同步显示 totalCount）
    const label = `估算: ${totalCount} 条`;
    const labelW = ctx.measureText(label).width + 18;
    ctx.fillStyle = 'rgba(6,14,26,0.82)';
    ctx.fillRect(8, 8, labelW, 26);
    ctx.strokeStyle = 'rgba(255,71,87,0.45)';
    ctx.lineWidth = 1;
    ctx.strokeRect(8, 8, labelW, 26);
    ctx.fillStyle = '#ff4757';
    ctx.font = 'bold 12px "JetBrains Mono", monospace';
    ctx.fillText(label, 15, 25);
}

// ───────────── 结果操作 ─────────────
function copyResultToClipboard() {
    const count = document.getElementById('fishCount').textContent;
    const time = document.getElementById('processTime').textContent;
    navigator.clipboard.writeText(`鱼群数量: ${count}\n处理时间: ${time}ms`).then(() => {
        showToast('结果已复制到剪贴板');
    });
}

function exportResultToFile() {
    const count = document.getElementById('fishCount').textContent;
    const time = document.getElementById('processTime').textContent;
    const blob = new Blob([`鱼群数量: ${count}\n处理时间: ${time}ms`], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = '鱼群计数结果.txt';
    a.click();
    URL.revokeObjectURL(url);
    showToast('结果已导出');
}

// ───────────── UI 辅助 ─────────────
function updateBadge(id, text, ready) {
    const el = document.getElementById(id);
    el.textContent = text;
    el.classList.toggle('ready', ready);
}

function togglePlaceholder(type, show) {
    const ph = document.getElementById(type + 'Placeholder');
    const cv = document.getElementById(type + 'Canvas');
    if (ph) ph.classList.toggle('hidden', !show);
    if (cv) cv.classList.toggle('visible', !show);
}

function animateCount(id, target, useInt = true) {
    const el = document.getElementById(id);
    const start = parseFloat(el.textContent) || 0;
    const diff = target - start;
    const duration = 600;
    const t0 = performance.now();
    if (countAnimFrame) cancelAnimationFrame(countAnimFrame);

    function step(now) {
        const p = Math.min((now - t0) / duration, 1);
        const ease = 1 - Math.pow(1 - p, 3);
        const val = start + diff * ease;
        el.textContent = useInt ? Math.round(val) : val.toFixed(1);
        if (p < 1) countAnimFrame = requestAnimationFrame(step);
    }
    countAnimFrame = requestAnimationFrame(step);
}

function showToast(msg, type = 'success') {
    const toast = document.getElementById('toast');
    const icon = toast.querySelector('.toast-icon');
    const txt = document.getElementById('toastMsg');
    txt.textContent = msg;
    if (type === 'error') {
        icon.textContent = '!';
        icon.style.background = '#f87171';
    } else {
        icon.textContent = '✓';
        icon.style.background = 'var(--success)';
    }
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2500);
}

// ───────────── 启动 ─────────────
window.addEventListener('DOMContentLoaded', init);
