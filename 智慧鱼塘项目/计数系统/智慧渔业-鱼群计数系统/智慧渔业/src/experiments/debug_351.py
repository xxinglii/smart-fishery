#!/usr/bin/env python3
"""调试351视频的二值化效果"""
import cv2
import numpy as np
from pathlib import Path

img = cv2.imread("dataset/raw_frames/351_frame_0002.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
h, w = gray.shape

print(f"图像尺寸: {w}x{h}")
print(f"灰度范围: {gray.min()} - {gray.max()}")
print(f"灰度均值: {gray.mean():.1f}")
print(f"灰度中位数: {np.median(gray):.1f}")

# 检查各通道
b, g, r = cv2.split(img)
print(f"\nB通道均值: {b.mean():.1f}, G通道均值: {g.mean():.1f}, R通道均值: {r.mean():.1f}")

# 尝试不同的预处理和二值化
results = []

# 1. 原始gray otsu
_, otsu1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
results.append(("gray_otsu_inv", otsu1))

# 2. 高斯模糊后 otsu
blur = cv2.GaussianBlur(gray, (7,7), 0)
_, otsu2 = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
results.append(("blur7_otsu_inv", otsu2))

# 3. 对比度增强 (CLAHE)
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
enhanced = clahe.apply(gray)
_, otsu3 = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
results.append(("clahe_otsu_inv", otsu3))

# 4. Top-hat变换增强小目标
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
_, otsu4 = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
results.append(("tophat_otsu_inv", otsu4))

# 5. Black-hat变换增强暗目标（鱼群）
blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
_, bh_thresh = cv2.threshold(blackhat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
results.append(("blackhat_otsu", bh_thresh))

# 6. 拉普拉斯增强边缘
laplacian = cv2.Laplacian(gray, cv2.CV_64F)
laplacian = np.uint8(np.absolute(laplacian))
_, lap_thresh = cv2.threshold(laplacian, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
results.append(("laplacian_otsu", lap_thresh))

# 7. 双边滤波 + otsu
bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
_, otsu5 = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
results.append(("bilateral_otsu_inv", otsu5))

# 8. 局部对比度归一化
gray_float = gray.astype(np.float32)
local_mean = cv2.blur(gray_float, (31, 31))
local_std = cv2.blur((gray_float - local_mean)**2, (31, 31))**0.5
local_std = np.maximum(local_std, 1.0)
normalized = ((gray_float - local_mean) / local_std * 30 + 128).clip(0, 255).astype(np.uint8)
_, otsu6 = cv2.threshold(normalized, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
results.append(("local_norm_otsu_inv", otsu6))

# 9. 尝试用局部标准差来找纹理区域
local_std_u8 = np.clip(local_std * 5, 0, 255).astype(np.uint8)
_, std_thresh = cv2.threshold(local_std_u8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
results.append(("local_std_otsu", std_thresh))

# 评估每种方法的前景占比和连通域数
print(f"\n{'='*70}")
print(f"{'方法':25s} | {'前景占比':>10s} | {'连通域数':>10s}")
print(f"{'='*70}")

vis_dir = Path("output/debug/351")
vis_dir.mkdir(parents=True, exist_ok=True)

for name, binary in results:
    fg = cv2.countNonZero(binary)
    ratio = fg / (h * w)
    
    # 形态学优化
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_open)
    
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(opened, connectivity=8)
    count = sum(1 for i in range(1, num_labels) if 15 < stats[i, cv2.CC_STAT_AREA] < 5000)
    
    print(f"{name:25s} | {ratio:>9.2%} | {count:>10d}")
    
    # 保存可视化
    mask_3ch = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    vis = np.hstack([img, mask_3ch])
    cv2.putText(vis, f"{name} ratio:{ratio:.2%} cnt:{count}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    cv2.imwrite(str(vis_dir / f"{name}.jpg"), vis)

print(f"\n调试结果已保存至 {vis_dir}")
