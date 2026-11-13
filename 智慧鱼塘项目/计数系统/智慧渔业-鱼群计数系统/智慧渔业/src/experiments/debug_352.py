#!/usr/bin/env python3
"""调试352视频的二值化效果"""
import cv2
import numpy as np
from pathlib import Path

img = cv2.imread("dataset/raw_frames/352_frame_0005.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
h, w = gray.shape

b, g, r = cv2.split(img)
print(f"B均值: {b.mean():.1f}, G均值: {g.mean():.1f}, R均值: {r.mean():.1f}")

results = []

# 1. 原始gray otsu (inverse=False，因为鱼群是浅色)
_, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
results.append(("otsu", otsu))

# 2. 高斯模糊后 otsu
blur = cv2.GaussianBlur(gray, (9,9), 0)
_, otsu2 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
results.append(("blur_otsu", otsu2))

# 3. 绿色通道 otsu
_, g_otsu = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
results.append(("green_otsu", g_otsu))

# 4. CLAHE + otsu
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
enhanced = clahe.apply(gray)
_, otsu3 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
results.append(("clahe_otsu", otsu3))

# 5. 自适应阈值（检测局部亮点）
adapt = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                               cv2.THRESH_BINARY, 25, -5)
results.append(("adapt_gauss", adapt))

# 6. Top-hat 检测亮斑
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
_, tophat_thresh = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
results.append(("tophat_otsu", tophat_thresh))

# 7. 局部对比度归一化 + 阈值
gray_f = gray.astype(np.float32)
local_mean = cv2.blur(gray_f, (51, 51))
local_std = np.sqrt(cv2.blur((gray_f - local_mean)**2, (51, 51)))
local_std = np.maximum(local_std, 1.0)
norm = ((gray_f - local_mean) / local_std * 40 + 128).clip(0, 255).astype(np.uint8)
_, norm_otsu = cv2.threshold(norm, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
results.append(("local_norm_otsu", norm_otsu))

# 8. 固定阈值（尝试不同值）
for t in [140, 150, 160]:
    _, fixed = cv2.threshold(gray, t, 255, cv2.THRESH_BINARY)
    results.append((f"fixed_{t}", fixed))

# 9. HSV V通道
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
v = cv2.split(hsv)[2]
_, v_otsu = cv2.threshold(v, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
results.append(("hsv_v_otsu", v_otsu))

# 评估
print(f"\n{'='*70}")
print(f"{'方法':25s} | {'前景占比':>10s} | {'连通域数':>10s}")
print(f"{'='*70}")

vis_dir = Path("output/debug/352")
vis_dir.mkdir(parents=True, exist_ok=True)

for name, binary in results:
    fg = cv2.countNonZero(binary)
    ratio = fg / (h * w)
    
    # 形态学优化
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_open)
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7,7))
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_close)
    
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
    count = sum(1 for i in range(1, num_labels) if 20 < stats[i, cv2.CC_STAT_AREA] < 3000)
    
    print(f"{name:25s} | {ratio:>9.2%} | {count:>10d}")
    
    mask_3ch = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    vis = np.hstack([img, mask_3ch])
    cv2.putText(vis, f"{name} ratio:{ratio:.2%} cnt:{count}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    cv2.imwrite(str(vis_dir / f"{name}.jpg"), vis)

print(f"\n调试结果已保存至 {vis_dir}")
