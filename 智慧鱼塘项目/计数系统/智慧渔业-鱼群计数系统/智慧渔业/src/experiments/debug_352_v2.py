#!/usr/bin/env python3
import cv2
import numpy as np
from pathlib import Path

img = cv2.imread("dataset/raw_frames/352_frame_0005.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
h, w = gray.shape

vis_dir = Path("output/debug/352_v2")
vis_dir.mkdir(parents=True, exist_ok=True)

results = []

# 策略：Top-hat 检测亮斑 + 多种参数
for kernel_size in [15, 21, 31, 41]:
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)
    
    for thresh_pct in [30, 50, 70]:
        # 使用top-hat结果中的百分位阈值
        thresh_val = np.percentile(tophat, thresh_pct)
        _, binary = cv2.threshold(tophat, thresh_val, 255, cv2.THRESH_BINARY)
        
        # 形态学
        opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, np.ones((3,3), np.uint8))
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((7,7), np.uint8))
        
        num_labels, _, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
        count = sum(1 for i in range(1, num_labels) if 30 < stats[i, cv2.CC_STAT_AREA] < 5000)
        fg = cv2.countNonZero(closed)
        ratio = fg / (h * w)
        
        name = f"tophat_k{kernel_size}_p{thresh_pct}"
        results.append((name, count, ratio, closed))
        print(f"{name:25s} | ratio:{ratio:>6.2%} | count:{count:>3d}")

# 策略：固定阈值 + 边缘约束（排除岸边）
# 创建ROI掩膜（排除上方1/5和右侧1/4——岸边区域）
roi_mask = np.ones((h, w), dtype=np.uint8) * 255
roi_mask[:h//5, :] = 0
roi_mask[:, -w//4:] = 0

for thresh in [145, 150, 155, 160, 165]:
    _, binary = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY)
    binary = cv2.bitwise_and(binary, roi_mask)
    
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, np.ones((3,3), np.uint8))
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, np.ones((9,9), np.uint8))
    
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
    count = sum(1 for i in range(1, num_labels) if 50 < stats[i, cv2.CC_STAT_AREA] < 5000)
    fg = cv2.countNonZero(closed)
    ratio = fg / (h * w)
    
    name = f"fixed_{thresh}_roi"
    results.append((name, count, ratio, closed))
    print(f"{name:25s} | ratio:{ratio:>6.2%} | count:{count:>3d}")

# 策略：差分方法（利用帧间差异检测运动鱼群）
img2 = cv2.imread("dataset/raw_frames/352_frame_0006.jpg", cv2.IMREAD_GRAYSCALE)
if img2 is not None:
    diff = cv2.absdiff(gray, img2)
    _, diff_bin = cv2.threshold(diff, 15, 255, cv2.THRESH_BINARY)
    diff_closed = cv2.morphologyEx(diff_bin, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8))
    num_labels, _, stats, _ = cv2.connectedComponentsWithStats(diff_closed, connectivity=8)
    count = sum(1 for i in range(1, num_labels) if 20 < stats[i, cv2.CC_STAT_AREA] < 5000)
    fg = cv2.countNonZero(diff_closed)
    ratio = fg / (h * w)
    results.append(("frame_diff", count, ratio, diff_closed))
    print(f"{'frame_diff':25s} | ratio:{ratio:>6.2%} | count:{count:>3d}")

# 保存可视化
for name, count, ratio, binary in results:
    mask_3ch = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
    vis = np.hstack([img, mask_3ch])
    cv2.putText(vis, f"{name} ratio:{ratio:.2%} cnt:{count}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    cv2.imwrite(str(vis_dir / f"{name}.jpg"), vis)

print(f"\n结果保存至 {vis_dir}")
