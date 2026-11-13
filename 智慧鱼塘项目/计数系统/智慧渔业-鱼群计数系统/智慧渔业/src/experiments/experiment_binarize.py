#!/usr/bin/env python3
"""
二值化策略实验脚本 - 为不同视频找到最佳参数
"""
import cv2
import numpy as np
from pathlib import Path

# 每种视频选一个典型帧进行实验
TEST_FRAMES = {
    "351": "dataset/raw_frames/351_frame_0002.jpg",  # 密集深色鱼群
    "352": "dataset/raw_frames/352_frame_0005.jpg",  # 高空浅色圆斑
    "353": "dataset/raw_frames/353_frame_0005.jpg",  # 极密集鱼群
    "882": "dataset/raw_frames/882_frame_0005.jpg",  # 个体较清晰
}
OUTPUT_DIR = Path("output/debug/experiment")


def remove_lines_hough(binary_mask, original_gray):
    """尝试用霍夫变换检测并移除直线（绳索）"""
    lines = cv2.HoughLinesP(binary_mask, 1, np.pi/180, threshold=50, minLineLength=80, maxLineGap=5)
    cleaned = binary_mask.copy()
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(cleaned, (x1, y1), (x2, y2), 0, 3)
    return cleaned


def remove_lines_morph(binary_mask):
    """用形态学开运算中的线状结构元素去除细线"""
    # 水平线
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    h_lines = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, h_kernel)
    # 垂直线
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
    v_lines = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, v_kernel)
    # 对角线（近似）
    d_kernel = np.eye(15, dtype=np.uint8)
    d_lines = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, d_kernel)
    d_kernel2 = np.fliplr(np.eye(15, dtype=np.uint8))
    d_lines2 = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, d_kernel2)
    
    lines_mask = cv2.bitwise_or(h_lines, v_lines)
    lines_mask = cv2.bitwise_or(lines_mask, d_lines)
    lines_mask = cv2.bitwise_or(lines_mask, d_lines2)
    
    cleaned = cv2.bitwise_and(binary_mask, cv2.bitwise_not(lines_mask))
    return cleaned


def experiment_for_frame(prefix, frame_path):
    """对单帧测试多种二值化策略"""
    print(f"\n{'='*60}")
    print(f"实验对象: [{prefix}] {frame_path}")
    print(f"{'='*60}")
    
    img = cv2.imread(str(frame_path))
    if img is None:
        print(f"[错误] 无法读取图像: {frame_path}")
        return
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    
    # 预处理 - 轻微降噪
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    strategies = []
    
    # --- 策略1: Otsu全局阈值 ---
    _, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    strategies.append(("otsu_inv", otsu))
    
    _, otsu2 = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    strategies.append(("otsu", otsu2))
    
    # --- 策略2: 自适应阈值 ---
    adapt_gauss = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                        cv2.THRESH_BINARY_INV, 15, 5)
    strategies.append(("adapt_gauss_inv", adapt_gauss))
    
    adapt_mean = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                       cv2.THRESH_BINARY_INV, 15, 5)
    strategies.append(("adapt_mean_inv", adapt_mean))
    
    # --- 策略3: 固定阈值（尝试不同阈值） ---
    for thresh in [80, 100, 120]:
        _, fixed = cv2.threshold(blurred, thresh, 255, cv2.THRESH_BINARY_INV)
        strategies.append((f"fixed_{thresh}_inv", fixed))
        _, fixed2 = cv2.threshold(blurred, thresh, 255, cv2.THRESH_BINARY)
        strategies.append((f"fixed_{thresh}", fixed2))
    
    # --- 策略4: 绿色通道分离（针对水面场景） ---
    b, g, r = cv2.split(img)
    green_blur = cv2.GaussianBlur(g, (5, 5), 0)
    _, green_otsu = cv2.threshold(green_blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    strategies.append(("green_otsu_inv", green_otsu))
    
    # --- 策略5: HSV空间 ---
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h_channel, s_channel, v_channel = cv2.split(hsv)
    _, v_otsu = cv2.threshold(v_channel, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    strategies.append(("hsv_v_otsu_inv", v_otsu))
    
    # 对每种策略做形态学优化并计数
    results = []
    for name, binary in strategies:
        # 形态学: 开运算去噪 -> 闭运算连接
        kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_open)
        
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_close)
        
        # 尝试移除线状干扰
        cleaned = remove_lines_morph(closed)
        
        # 连通域计数（过滤小区域）
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(cleaned, connectivity=8)
        min_area = 15   # 最小面积过滤
        max_area = 3000 # 最大面积过滤（排除大块误检）
        count = 0
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if min_area < area < max_area:
                count += 1
        
        results.append((name, count, cleaned))
        print(f"  {name:20s} -> 计数: {count:4d}")
    
    # 保存可视化结果（前5个策略）
    vis_dir = OUTPUT_DIR / prefix
    vis_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存原图
    cv2.imwrite(str(vis_dir / "00_original.jpg"), img)
    cv2.imwrite(str(vis_dir / "01_gray.jpg"), gray)
    
    for i, (name, count, mask) in enumerate(results[:8]):
        # 可视化：原图上叠加检测到的轮廓
        vis = img.copy()
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 15 < area < 3000:
                cv2.drawContours(vis, [cnt], -1, (0, 255, 0), 1)
        
        # 合并显示: 原图 + 二值图 + 可视化
        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        combined = np.hstack([img, mask_3ch, vis])
        
        out_path = vis_dir / f"{i+2:02d}_{name}_cnt{count}.jpg"
        cv2.imwrite(str(out_path), combined)
    
    print(f"  可视化结果已保存至: {vis_dir}")


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for prefix, frame_path in TEST_FRAMES.items():
        experiment_for_frame(prefix, frame_path)
    
    print(f"\n{'='*60}")
    print("实验完成！请查看 output/debug/experiment/ 目录下各视频的二值化效果")
    print("="*60)
