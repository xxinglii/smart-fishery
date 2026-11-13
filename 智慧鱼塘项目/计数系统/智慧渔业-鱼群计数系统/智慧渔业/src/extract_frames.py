#!/usr/bin/env python3
"""
从视频中按固定时间间隔抽取帧，构建数据集
"""
import cv2
import os
from pathlib import Path

# 配置（路径均相对于项目根目录，请在项目根目录下运行）
VIDEO_DIR = Path("videos")
VIDEOS = {
    "351": "351_1745153922.mp4",
    "352": "352_1745153929.mp4",
    "353": "353_1745153937.mp4",
    "882": "882bcccf7eb3f027a0ae325cad5d7686.mp4",
}
INTERVAL_SEC = 2  # 每2秒抽一帧
OUTPUT_DIR = Path("dataset/raw_frames")


def extract_frames(video_path: str, prefix: str, interval_sec: int, output_dir: Path):
    """从视频中按interval_sec间隔抽帧"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[错误] 无法打开视频: {video_path}")
        return 0

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    frame_interval = int(fps * interval_sec)

    print(f"[{prefix}] 视频: {video_path}")
    print(f"[{prefix}] 分辨率: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
    print(f"[{prefix}] FPS: {fps:.2f}, 总帧数: {total_frames}, 时长: {duration:.1f}s")
    print(f"[{prefix}] 每 {interval_sec}s 抽一帧 (间隔 {frame_interval} 帧)")

    count = 0
    saved = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if count % frame_interval == 0:
            out_name = output_dir / f"{prefix}_frame_{saved:04d}.jpg"
            cv2.imwrite(str(out_name), frame)
            saved += 1
        count += 1

    cap.release()
    print(f"[{prefix}] 成功抽取 {saved} 帧\n")
    return saved


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    for prefix, video_name in VIDEOS.items():
        video_path = VIDEO_DIR / video_name
        if not video_path.exists():
            print(f"[跳过] 文件不存在: {video_path}")
            continue
        n = extract_frames(str(video_path), prefix, INTERVAL_SEC, OUTPUT_DIR)
        total += n
    print(f"=" * 50)
    print(f"数据集构建完成，共抽取 {total} 帧，保存至 {OUTPUT_DIR}")
