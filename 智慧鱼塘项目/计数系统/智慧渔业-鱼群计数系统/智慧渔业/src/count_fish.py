#!/usr/bin/env python3
"""
鱼群计数主程序 - 针对不同视频类型采用不同策略
"""
import cv2
import numpy as np
from pathlib import Path
import json
from typing import Dict, List, Tuple


# ============ 视频专属参数配置 ============

VIDEO_CONFIGS = {
    '351': {
        'description': '低高度俯视，极密集深色鱼群，白色绳索',
        'preprocess': 'clahe',
        'binarize': 'fixed_inv',
        'fixed_thresh': 90,
        'blur': 3,
        'open_kernel': (3, 3),
        'close_kernel': (5, 5),
        'remove_lines': True,
        'line_thickness': 5,
        'count_method': 'density',
        'avg_fish_area': 25,      # 351鱼群很小，单鱼面积约25像素
        'min_area': 10,
        'max_area': 3000,
    },
    '352': {
        'description': '高高度航拍，浅色圆斑鱼群',
        'preprocess': 'clahe',
        'binarize': 'fixed',
        'fixed_thresh': 155,
        'blur': 7,
        'open_kernel': (3, 3),
        'close_kernel': (9, 9),
        'remove_lines': False,
        'count_method': 'connected',
        'min_area': 40,
        'max_area': 3000,
        'roi_exclude_top': 0.15,
        'roi_exclude_right': 0.2,
    },
    '353': {
        'description': '低高度俯视，极密集鱼群',
        'preprocess': 'clahe',
        'binarize': 'fixed_inv',
        'fixed_thresh': 95,
        'blur': 3,
        'open_kernel': (3, 3),
        'close_kernel': (5, 5),
        'remove_lines': True,
        'line_thickness': 5,
        'count_method': 'density',
        'avg_fish_area': 20,
        'min_area': 10,
        'max_area': 3000,
    },
    '882': {
        'description': '低高度，鱼群个体较清晰',
        'preprocess': 'blur',
        'binarize': 'otsu_inv',
        'blur': 5,
        'open_kernel': (3, 3),
        'close_kernel': (5, 5),
        'remove_lines': True,
        'line_thickness': 4,
        'count_method': 'connected',
        'min_area': 15,
        'max_area': 3000,
    },
}


# ============ 核心处理函数 ============

def apply_preprocess(gray: np.ndarray, method: str, blur_ksize: int = 5) -> np.ndarray:
    """应用预处理"""
    if method == 'clahe':
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gray)
    elif method == 'blur':
        if blur_ksize % 2 == 0:
            blur_ksize += 1
        return cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)
    elif method == 'blackhat':
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        return cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
    else:
        return gray


def apply_binarize(gray: np.ndarray, method: str, fixed_thresh: int = 128) -> np.ndarray:
    """应用二值化"""
    if method == 'otsu_inv':
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    elif method == 'otsu':
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif method == 'fixed_inv':
        _, binary = cv2.threshold(gray, fixed_thresh, 255, cv2.THRESH_BINARY_INV)
    elif method == 'fixed':
        _, binary = cv2.threshold(gray, fixed_thresh, 255, cv2.THRESH_BINARY)
    else:
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return binary


def remove_lines_morph(binary: np.ndarray, thickness: int = 3) -> np.ndarray:
    """形态学去线"""
    cleaned = binary.copy()
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (35, 1))
    h_lines = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, h_kernel)
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 35))
    v_lines = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, v_kernel)
    d1 = np.eye(15, dtype=np.uint8)
    d_lines1 = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, d1)
    d2 = np.fliplr(np.eye(15, dtype=np.uint8))
    d_lines2 = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, d2)
    
    lines_mask = cv2.bitwise_or(h_lines, v_lines)
    lines_mask = cv2.bitwise_or(lines_mask, d_lines1)
    lines_mask = cv2.bitwise_or(lines_mask, d_lines2)
    lines_mask = cv2.dilate(lines_mask, np.ones((thickness, thickness), np.uint8))
    cleaned = cv2.bitwise_and(cleaned, cv2.bitwise_not(lines_mask))
    return cleaned


def morphological_optimize(binary: np.ndarray, open_k: Tuple[int, int], close_k: Tuple[int, int]) -> np.ndarray:
    """形态学优化"""
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, open_k)
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_open)
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, close_k)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_close)
    return closed


def count_connected(binary: np.ndarray, min_area: int, max_area: int) -> Tuple[int, List]:
    """连通域计数"""
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
    count = 0
    components = []
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if min_area <= area <= max_area:
            count += 1
            components.append({
                'area': area,
                'centroid': (int(centroids[i][0]), int(centroids[i][1])),
                'bbox': (stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP],
                         stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT])
            })
    return count, components


def count_density(binary: np.ndarray, avg_fish_area: float) -> int:
    """密度估计"""
    fg_pixels = cv2.countNonZero(binary)
    return max(0, int(fg_pixels / avg_fish_area))


def process_frame(img_bgr: np.ndarray, video_type: str) -> Dict:
    """处理单帧"""
    cfg = VIDEO_CONFIGS.get(video_type, VIDEO_CONFIGS['882'])
    h, w = img_bgr.shape[:2]
    
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # 1. 预处理
    processed = apply_preprocess(gray, cfg['preprocess'], cfg.get('blur', 5))
    
    # 2. 二值化
    binary = apply_binarize(processed, cfg['binarize'], cfg.get('fixed_thresh', 128))
    
    # 3. 形态学优化
    binary_opt = morphological_optimize(binary, cfg['open_kernel'], cfg['close_kernel'])
    
    # 4. 去线
    if cfg.get('remove_lines', False):
        binary_clean = remove_lines_morph(binary_opt, cfg.get('line_thickness', 3))
    else:
        binary_clean = binary_opt
    
    # 5. ROI掩膜（排除边缘区域如岸边）
    roi_mask = np.ones((h, w), dtype=np.uint8) * 255
    if cfg.get('roi_exclude_top', 0) > 0:
        roi_mask[:int(h * cfg['roi_exclude_top']), :] = 0
    if cfg.get('roi_exclude_bottom', 0) > 0:
        roi_mask[-int(h * cfg['roi_exclude_bottom']):, :] = 0
    if cfg.get('roi_exclude_left', 0) > 0:
        roi_mask[:, :int(w * cfg['roi_exclude_left'])] = 0
    if cfg.get('roi_exclude_right', 0) > 0:
        roi_mask[:, -int(w * cfg['roi_exclude_right']):] = 0
    binary_clean = cv2.bitwise_and(binary_clean, roi_mask)
    
    # 6. 计数
    fg_pixels = cv2.countNonZero(binary_clean)
    fg_ratio = fg_pixels / (h * w)
    
    if cfg['count_method'] == 'density':
        count = count_density(binary_clean, cfg['avg_fish_area'])
        components = []
    else:
        count, components = count_connected(binary_clean, cfg['min_area'], cfg['max_area'])
    
    return {
        'count': count,
        'method': cfg['count_method'],
        'fg_pixels': fg_pixels,
        'fg_ratio': fg_ratio,
        'binary_mask': binary_clean,
        'components': components,
        'config': cfg,
    }


def visualize_result(img_bgr: np.ndarray, result: Dict) -> np.ndarray:
    """生成可视化结果图"""
    vis = img_bgr.copy()
    h, w = vis.shape[:2]
    
    if result['method'] == 'connected':
        for comp in result['components']:
            cx, cy = comp['centroid']
            cv2.circle(vis, (cx, cy), 3, (0, 255, 0), -1)
            x, y, bw, bh = comp['bbox']
            cv2.rectangle(vis, (x, y), (x+bw, y+bh), (0, 255, 0), 1)
    else:
        # 密度模式下，在二值图前景位置采样显示
        coords = np.column_stack(np.where(result['binary_mask'] > 0))
        if len(coords) > 0:
            step = max(1, len(coords) // min(800, len(coords)))
            for i in range(0, len(coords), step):
                y, x = coords[i]
                cv2.circle(vis, (x, y), 1, (0, 255, 0), -1)
    
    # 信息栏
    info = f"Count: {result['count']} | Method: {result['method']} | FG: {result['fg_ratio']:.2%}"
    cv2.rectangle(vis, (0, 0), (w, 40), (0, 0, 0), -1)
    cv2.putText(vis, info, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    return vis


# ============ 批处理入口 ============

def process_all_frames():
    """处理数据集中所有帧"""
    frame_dir = Path("dataset/raw_frames")
    vis_dir = Path("output/visualizations")
    mask_dir = Path("dataset/binary_masks")
    vis_dir.mkdir(parents=True, exist_ok=True)
    mask_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    frame_files = sorted(frame_dir.glob("*.jpg"))
    
    print(f"共 {len(frame_files)} 帧待处理...")
    print("=" * 80)
    
    for frame_path in frame_files:
        img = cv2.imread(str(frame_path))
        if img is None:
            continue
        
        prefix = frame_path.stem.split('_')[0]
        result = process_frame(img, prefix)
        
        # 保存二值掩膜
        mask_path = mask_dir / f"{frame_path.stem}_mask.png"
        cv2.imwrite(str(mask_path), result['binary_mask'])
        
        # 保存可视化
        vis = visualize_result(img, result)
        vis_path = vis_dir / f"{frame_path.stem}_vis.jpg"
        cv2.imwrite(str(vis_path), vis)
        
        results.append({
            'frame': frame_path.name,
            'video': prefix,
            'count': result['count'],
            'method': result['method'],
            'fg_ratio': round(result['fg_ratio'], 4),
            'fg_pixels': int(result['fg_pixels']),
        })
        
        print(f"[{prefix}] {frame_path.name:35s} -> Count: {result['count']:6d} | "
              f"FG: {result['fg_ratio']:.2%} | Method: {result['method']}")
    
    # 保存JSON结果
    with open("output/count_results.json", 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("=" * 80)
    print(f"处理完成！结果保存至 output/count_results.json")
    print(f"可视化图像保存至 {vis_dir}")
    print(f"二值掩膜保存至 {mask_dir}")
    
    # 统计每个视频的平均计数
    from collections import defaultdict
    video_stats = defaultdict(list)
    for r in results:
        video_stats[r['video']].append(r['count'])
    
    print("\n各视频平均计数统计:")
    for vid, counts in sorted(video_stats.items()):
        avg = sum(counts) / len(counts)
        print(f"  [{vid}] 帧数: {len(counts):2d} | 平均计数: {avg:8.1f} | 范围: {min(counts)}-{max(counts)}")
    
    return results


if __name__ == "__main__":
    process_all_frames()
