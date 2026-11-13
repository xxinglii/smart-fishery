#!/usr/bin/env python3
"""生成展示图：原图 + 二值掩膜 + 检测结果 三合一"""
import cv2
import numpy as np
from pathlib import Path

showcase_frames = {
    '351': 'dataset/raw_frames/351_frame_0002.jpg',
    '352': 'dataset/raw_frames/352_frame_0005.jpg',
    '353': 'dataset/raw_frames/353_frame_0005.jpg',
    '882': 'dataset/raw_frames/882_frame_0005.jpg',
}

output_dir = Path("output/comparison")
output_dir.mkdir(parents=True, exist_ok=True)

for vid, frame_path in showcase_frames.items():
    img = cv2.imread(frame_path)
    mask = cv2.imread(f"dataset/binary_masks/{Path(frame_path).stem}_mask.png", cv2.IMREAD_GRAYSCALE)
    vis = cv2.imread(f"output/visualizations/{Path(frame_path).stem}_vis.jpg")
    
    if img is None or mask is None or vis is None:
        print(f"[跳过] {vid}: 缺少图像文件")
        continue
    
    h, w = img.shape[:2]
    
    # 调整大小统一
    target_h = 400
    scale = target_h / h
    target_w = int(w * scale)
    
    img_resized = cv2.resize(img, (target_w, target_h))
    mask_resized = cv2.resize(mask, (target_w, target_h))
    vis_resized = cv2.resize(vis, (target_w, target_h))
    
    # 二值图转3通道
    mask_color = cv2.cvtColor(mask_resized, cv2.COLOR_GRAY2BGR)
    
    # 添加标签
    labels = ["Original", "Binary Mask", "Detection Result"]
    for i, (im, label) in enumerate(zip([img_resized, mask_color, vis_resized], labels)):
        cv2.putText(im, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    
    combined = np.hstack([img_resized, mask_color, vis_resized])
    out_path = output_dir / f"showcase_{vid}.jpg"
    cv2.imwrite(str(out_path), combined)
    print(f"[{vid}] 展示图已保存: {out_path}")

print("\n所有展示图生成完成!")
