#!/usr/bin/env python3
"""
鱼群二值化计数核心算法
支持两种模式：连通域计数（低密度）和密度估计（高密度）
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, List


# ============ 预处理模块 ============

def preprocess(gray: np.ndarray, blur_ksize: int = 5) -> np.ndarray:
    """灰度图预处理：高斯模糊降噪"""
    if blur_ksize % 2 == 0:
        blur_ksize += 1
    blurred = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)
    return blurred


def remove_lines_morph(binary_mask: np.ndarray, line_thickness: int = 3) -> np.ndarray:
    """
    用形态学开运算去除线状干扰（绳索）
    使用多种方向的线状结构元素
    """
    cleaned = binary_mask.copy()
    
    # 水平线
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (31, 1))
    h_lines = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, h_kernel)
    # 垂直线
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 31))
    v_lines = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, v_kernel)
    # 对角线
    d_kernel1 = np.eye(15, dtype=np.uint8)
    d_lines1 = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, d_kernel1)
    d_kernel2 = np.fliplr(np.eye(15, dtype=np.uint8))
    d_lines2 = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, d_kernel2)
    
    lines_mask = cv2.bitwise_or(h_lines, v_lines)
    lines_mask = cv2.bitwise_or(lines_mask, d_lines1)
    lines_mask = cv2.bitwise_or(lines_mask, d_lines2)
    
    # 膨胀线条掩膜后再去除
    lines_mask = cv2.dilate(lines_mask, np.ones((line_thickness, line_thickness), np.uint8))
    cleaned = cv2.bitwise_and(cleaned, cv2.bitwise_not(lines_mask))
    return cleaned


def create_roi_mask(shape: Tuple[int, int], exclude_top_ratio: float = 0.0, 
                    exclude_bottom_ratio: float = 0.0) -> np.ndarray:
    """创建ROI掩膜，可排除图像上下边缘（如岸边）"""
    h, w = shape
    mask = np.ones((h, w), dtype=np.uint8) * 255
    top_h = int(h * exclude_top_ratio)
    bottom_h = int(h * exclude_bottom_ratio)
    if top_h > 0:
        mask[:top_h, :] = 0
    if bottom_h > 0:
        mask[-bottom_h:, :] = 0
    return mask


# ============ 二值化模块 ============

def binarize_otsu(gray: np.ndarray, inverse: bool = True) -> np.ndarray:
    """Otsu自动阈值二值化"""
    flag = cv2.THRESH_BINARY_INV if inverse else cv2.THRESH_BINARY
    _, binary = cv2.threshold(gray, 0, 255, flag + cv2.THRESH_OTSU)
    return binary


def binarize_adaptive(gray: np.ndarray, block_size: int = 15, c: int = 5, 
                      inverse: bool = True) -> np.ndarray:
    """自适应高斯阈值二值化"""
    if block_size % 2 == 0:
        block_size += 1
    method = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
    flag = cv2.THRESH_BINARY_INV if inverse else cv2.THRESH_BINARY
    binary = cv2.adaptiveThreshold(gray, 255, method, flag, block_size, c)
    return binary


def binarize_fixed(gray: np.ndarray, thresh: int, inverse: bool = True) -> np.ndarray:
    """固定阈值二值化"""
    flag = cv2.THRESH_BINARY_INV if inverse else cv2.THRESH_BINARY
    _, binary = cv2.threshold(gray, thresh, 255, flag)
    return binary


def binarize_multi_channel(img_bgr: np.ndarray, channel: str = 'green', 
                           inverse: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """
    基于特定颜色通道的二值化
    channel: 'green', 'blue', 'red', 'value', 'saturation'
    """
    if channel == 'green':
        ch = cv2.split(img_bgr)[1]
    elif channel == 'blue':
        ch = cv2.split(img_bgr)[0]
    elif channel == 'red':
        ch = cv2.split(img_bgr)[2]
    elif channel in ('value', 'saturation', 'hue'):
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        if channel == 'hue':
            ch = cv2.split(hsv)[0]
        elif channel == 'saturation':
            ch = cv2.split(hsv)[1]
        else:
            ch = cv2.split(hsv)[2]
    else:
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        ch = gray
    
    ch_blur = cv2.GaussianBlur(ch, (5, 5), 0)
    binary = binarize_otsu(ch_blur, inverse=inverse)
    return binary, ch


# ============ 形态学优化 ============

def morphological_optimize(binary: np.ndarray, 
                           open_kernel: Tuple[int, int] = (3, 3),
                           close_kernel: Tuple[int, int] = (5, 5)) -> np.ndarray:
    """形态学优化：开运算去噪 -> 闭运算连接"""
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, open_kernel)
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_open)
    
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, close_kernel)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_close)
    return closed


# ============ 计数方法 ============

def count_connected_components(binary: np.ndarray, 
                               min_area: int = 10, 
                               max_area: int = 5000) -> Tuple[int, np.ndarray, List]:
    """
    连通域计数，返回 (数量, 标签图, 有效组件列表)
    每个组件为 dict: {'area': int, 'centroid': (x,y), 'bbox': (x,y,w,h)}
    """
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
    
    count = 0
    valid_components = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if min_area <= area <= max_area:
            count += 1
            x = stats[i, cv2.CC_STAT_LEFT]
            y = stats[i, cv2.CC_STAT_TOP]
            w = stats[i, cv2.CC_STAT_WIDTH]
            h = stats[i, cv2.CC_STAT_HEIGHT]
            valid_components.append({
                'area': area,
                'centroid': (int(centroids[i][0]), int(centroids[i][1])),
                'bbox': (x, y, w, h)
            })
    
    return count, labels, valid_components


def count_contours(binary: np.ndarray, min_area: int = 10, max_area: int = 5000) -> Tuple[int, List]:
    """轮廓检测计数"""
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    count = 0
    valid_contours = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if min_area <= area <= max_area:
            count += 1
            valid_contours.append(cnt)
    return count, valid_contours


def density_estimate(binary: np.ndarray, avg_fish_area: float = 80.0) -> int:
    """
    密度估计法：总前景像素面积 / 单鱼平均面积
    适用于高密度、鱼群粘连无法个体区分的场景
    """
    foreground_pixels = cv2.countNonZero(binary)
    estimated_count = int(foreground_pixels / avg_fish_area)
    return max(0, estimated_count)


# ============ 主流程 ============

def count_fish_in_frame(img_bgr: np.ndarray, 
                        strategy: str = 'auto',
                        video_type: str = 'default',
                        return_vis: bool = False) -> Dict:
    """
    对单帧图像进行鱼群计数
    
    Args:
        img_bgr: 输入BGR图像
        strategy: 'connected' 连通域计数, 'density' 密度估计, 'auto' 自动选择
        video_type: 视频类型标识，用于选择预设参数
        return_vis: 是否返回可视化图像
    
    Returns:
        dict 包含 count, method, binary_mask, vis_img(可选), components等
    """
    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # 根据视频类型选择参数
    params = {
        'default': {
            'binarize': lambda g, img: binarize_otsu(g, inverse=True),
            'blur': 5,
            'open_kernel': (3, 3),
            'close_kernel': (5, 5),
            'min_area': 10,
            'max_area': 3000,
            'avg_fish_area': 80,
            'density_thresh': 0.3,  # 前景占比超过此值时切换为密度估计
        },
        '351': {
            'binarize': lambda g, img: binarize_multi_channel(img, 'green', inverse=True)[0],
            'blur': 5,
            'open_kernel': (3, 3),
            'close_kernel': (7, 7),
            'min_area': 20,
            'max_area': 5000,
            'avg_fish_area': 100,
            'density_thresh': 0.15,
        },
        '352': {
            'binarize': lambda g, img: binarize_otsu(g, inverse=False),  # 352是浅色圆斑
            'blur': 7,
            'open_kernel': (3, 3),
            'close_kernel': (7, 7),
            'min_area': 30,
            'max_area': 2000,
            'avg_fish_area': 120,
            'density_thresh': 0.2,
        },
        '353': {
            'binarize': lambda g, img: binarize_multi_channel(img, 'green', inverse=True)[0],
            'blur': 5,
            'open_kernel': (3, 3),
            'close_kernel': (5, 5),
            'min_area': 15,
            'max_area': 5000,
            'avg_fish_area': 90,
            'density_thresh': 0.15,
        },
        '882': {
            'binarize': lambda g, img: binarize_otsu(g, inverse=True),
            'blur': 5,
            'open_kernel': (3, 3),
            'close_kernel': (5, 5),
            'min_area': 15,
            'max_area': 3000,
            'avg_fish_area': 70,
            'density_thresh': 0.25,
        },
    }
    
    p = params.get(video_type, params['default'])
    
    # 1. 预处理
    blurred = preprocess(gray, p['blur'])
    
    # 2. 二值化
    binary = p['binarize'](blurred, img_bgr)
    
    # 3. 形态学优化
    binary_opt = morphological_optimize(binary, p['open_kernel'], p['close_kernel'])
    
    # 4. 去除线状干扰
    binary_clean = remove_lines_morph(binary_opt, line_thickness=4)
    
    # 5. 计算前景占比，决定计数策略
    fg_ratio = cv2.countNonZero(binary_clean) / (h * w)
    
    if strategy == 'auto':
        if fg_ratio > p['density_thresh']:
            strategy = 'density'
        else:
            strategy = 'connected'
    
    # 6. 计数
    result = {
        'fg_ratio': fg_ratio,
        'strategy': strategy,
        'binary_mask': binary_clean,
    }
    
    if strategy == 'density':
        count = density_estimate(binary_clean, p['avg_fish_area'])
        result['count'] = count
        result['method'] = 'density_estimate'
    else:
        count_cc, labels, components = count_connected_components(
            binary_clean, p['min_area'], p['max_area'])
        result['count'] = count_cc
        result['method'] = 'connected_components'
        result['components'] = components
        result['labels'] = labels
    
    # 7. 可视化
    if return_vis:
        vis = img_bgr.copy()
        if strategy == 'connected' and 'components' in result:
            for comp in result['components']:
                cx, cy = comp['centroid']
                cv2.circle(vis, (cx, cy), 3, (0, 255, 0), -1)
                x, y, bw, bh = comp['bbox']
                cv2.rectangle(vis, (x, y), (x+bw, y+bh), (0, 255, 0), 1)
        else:
            # 密度估计模式下，在前景区域随机撒点示意
            coords = np.column_stack(np.where(binary_clean > 0))
            if len(coords) > 0:
                step = max(1, len(coords) // 500)
                for i in range(0, len(coords), step):
                    y, x = coords[i]
                    cv2.circle(vis, (x, y), 2, (0, 255, 0), -1)
        
        # 在图像上添加计数信息
        info_text = f"Count: {result['count']} | Method: {result['method']} | FG: {fg_ratio:.2%}"
        cv2.putText(vis, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        result['vis'] = vis
    
    return result


if __name__ == "__main__":
    # 简单测试
    import glob
    
    test_frames = glob.glob("dataset/raw_frames/*.jpg")
    print(f"测试 {len(test_frames)} 帧图像...")
    
    for frame_path in sorted(test_frames)[:5]:
        img = cv2.imread(frame_path)
        fname = Path(frame_path).stem
        prefix = fname.split('_')[0]
        
        result = count_fish_in_frame(img, strategy='auto', video_type=prefix, return_vis=True)
        print(f"{fname:30s} -> 计数: {result['count']:5d} | 方法: {result['method']:20s} | 前景占比: {result['fg_ratio']:.2%}")
        
        # 保存可视化（写入独立目录，避免覆盖主程序 output/visualizations 的结果）
        out_path = Path("output/debug/binarize") / f"{fname}_vis.jpg"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), result['vis'])
