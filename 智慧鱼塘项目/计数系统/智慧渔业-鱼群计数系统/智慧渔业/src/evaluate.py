#!/usr/bin/env python3
"""
性能评估脚本 - 对比算法计数与人工标注的ground truth
"""
import json
import math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def load_results():
    """加载算法计数结果和人工标注"""
    with open("output/count_results.json", 'r') as f:
        algo_results = json.load(f)
    
    with open("dataset/annotations/ground_truth.json", 'r') as f:
        gt_data = json.load(f)
    
    return algo_results, gt_data['annotations']


def evaluate():
    algo_results, gt_annotations = load_results()
    
    # 构建帧名到算法结果的映射
    algo_map = {r['frame']: r for r in algo_results}
    
    # 逐帧对比
    comparisons = []
    video_errors = {}
    
    print("=" * 90)
    print(f"{'帧名':35s} | {'视频':>5s} | {'GT':>6s} | {'算法':>6s} | {'绝对误差':>8s} | {'相对误差':>8s}")
    print("=" * 90)
    
    for ann in gt_annotations:
        frame = ann['frame']
        video = ann['video']
        gt_count = ann['manual_count']
        
        if frame not in algo_map:
            continue
        
        algo_count = algo_map[frame]['count']
        abs_error = abs(algo_count - gt_count)
        rel_error = abs_error / gt_count if gt_count > 0 else 0
        
        comparisons.append({
            'frame': frame,
            'video': video,
            'gt': gt_count,
            'algo': algo_count,
            'abs_error': abs_error,
            'rel_error': rel_error,
            'confidence': ann.get('confidence', 'medium')
        })
        
        if video not in video_errors:
            video_errors[video] = []
        video_errors[video].append((abs_error, rel_error))
        
        conf_mark = "★" if ann.get('confidence') == 'high' else " "
        print(f"{frame:35s} | {video:>5s} | {gt_count:>6d} | {algo_count:>6d} | {abs_error:>8d} | {rel_error:>7.1%} {conf_mark}")
    
    print("=" * 90)
    
    # 整体指标
    all_abs_errors = [c['abs_error'] for c in comparisons]
    all_rel_errors = [c['rel_error'] for c in comparisons]
    mae = sum(all_abs_errors) / len(all_abs_errors)
    rmse = math.sqrt(sum(e**2 for e in all_abs_errors) / len(all_abs_errors))
    mre = sum(all_rel_errors) / len(all_rel_errors)
    
    print(f"\n{'='*60}")
    print("整体性能指标")
    print(f"{'='*60}")
    print(f"  评估帧数: {len(comparisons)}")
    print(f"  MAE  (平均绝对误差): {mae:>8.1f}")
    print(f"  RMSE (均方根误差)  : {rmse:>8.1f}")
    print(f"  MRE  (平均相对误差): {mre:>7.1%}")
    print(f"{'='*60}")
    
    # 按视频分组指标
    print(f"\n各视频分组指标:")
    print(f"{'='*60}")
    for video in sorted(video_errors.keys()):
        errors = video_errors[video]
        abs_errs = [e[0] for e in errors]
        rel_errs = [e[1] for e in errors]
        v_mae = sum(abs_errs) / len(abs_errs)
        v_rmse = math.sqrt(sum(e**2 for e in abs_errs) / len(abs_errs))
        v_mre = sum(rel_errs) / len(rel_errs)
        print(f"  [{video}] 帧数:{len(errors):2d} | MAE:{v_mae:>8.1f} | RMSE:{v_rmse:>8.1f} | MRE:{v_mre:>6.1%}")
    print(f"{'='*60}")
    
    # 生成对比图
    plot_comparison(comparisons, video_errors)
    
    # 保存详细报告
    save_report(comparisons, mae, rmse, mre, video_errors)


def plot_comparison(comparisons, video_errors):
    """生成可视化对比图"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 图1: 每帧GT vs Algo散点图
    ax1 = axes[0, 0]
    gt_vals = [c['gt'] for c in comparisons]
    algo_vals = [c['algo'] for c in comparisons]
    colors = {'351': 'red', '352': 'blue', '353': 'green', '882': 'orange'}
    for c in comparisons:
        ax1.scatter(c['gt'], c['algo'], c=colors.get(c['video'], 'gray'), 
                   alpha=0.7, s=80, edgecolors='black', linewidth=0.5)
    
    max_val = max(max(gt_vals), max(algo_vals)) * 1.1
    ax1.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, label='y=x (完美预测)')
    ax1.set_xlabel('Ground Truth Count')
    ax1.set_ylabel('Algorithm Count')
    ax1.set_title('GT vs Algorithm Prediction')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 图2: 各视频相对误差柱状图
    ax2 = axes[0, 1]
    videos = sorted(video_errors.keys())
    mre_by_video = [sum(e[1] for e in video_errors[v]) / len(video_errors[v]) for v in videos]
    bars = ax2.bar(videos, mre_by_video, color=[colors.get(v, 'gray') for v in videos], edgecolor='black')
    ax2.set_ylabel('Mean Relative Error')
    ax2.set_title('Mean Relative Error by Video')
    ax2.set_ylim(0, max(mre_by_video) * 1.3)
    for bar, val in zip(bars, mre_by_video):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                f'{val:.1%}', ha='center', va='bottom', fontsize=11)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 图3: 绝对误差分布
    ax3 = axes[1, 0]
    abs_errors = [c['abs_error'] for c in comparisons]
    ax3.hist(abs_errors, bins=15, color='steelblue', edgecolor='black', alpha=0.7)
    ax3.set_xlabel('Absolute Error')
    ax3.set_ylabel('Frequency')
    ax3.set_title('Absolute Error Distribution')
    ax3.axvline(np.mean(abs_errors), color='red', linestyle='--', label=f'MAE={np.mean(abs_errors):.1f}')
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 图4: 各帧详细对比
    ax4 = axes[1, 1]
    x_pos = np.arange(len(comparisons))
    width = 0.35
    gt_heights = [c['gt'] for c in comparisons]
    algo_heights = [c['algo'] for c in comparisons]
    
    bar_colors_gt = [colors.get(c['video'], 'gray') for c in comparisons]
    bar_colors_algo = [colors.get(c['video'], 'gray') for c in comparisons]
    
    ax4.bar(x_pos - width/2, gt_heights, width, label='GT', alpha=0.7, color='lightgray', edgecolor='black')
    ax4.bar(x_pos + width/2, algo_heights, width, label='Algo', alpha=0.7, color='steelblue', edgecolor='black')
    
    # 标注视频分组
    for i, c in enumerate(comparisons):
        ax4.text(i, max(gt_heights[i], algo_heights[i]) * 1.05, c['video'], 
                ha='center', fontsize=7, color=colors.get(c['video'], 'gray'))
    
    ax4.set_xlabel('Frame Index')
    ax4.set_ylabel('Count')
    ax4.set_title('Per-Frame GT vs Algorithm')
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels([f"F{i+1}" for i in range(len(comparisons))], fontsize=8)
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    out_path = Path("output/comparison/evaluation_plots.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    print(f"\n评估图表已保存至: {out_path}")
    plt.close()


def save_report(comparisons, mae, rmse, mre, video_errors):
    """保存文本报告"""
    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("智慧渔业 - 鱼群二值化计数算法性能评估报告")
    report_lines.append("=" * 70)
    report_lines.append("")
    report_lines.append(f"评估时间: 2026-04-26")
    report_lines.append(f"评估帧数: {len(comparisons)}")
    report_lines.append("")
    report_lines.append("-" * 70)
    report_lines.append("整体性能指标")
    report_lines.append("-" * 70)
    report_lines.append(f"  MAE  (平均绝对误差): {mae:>10.2f}")
    report_lines.append(f"  RMSE (均方根误差)  : {rmse:>10.2f}")
    report_lines.append(f"  MRE  (平均相对误差): {mre:>9.2%}")
    report_lines.append("")
    report_lines.append("-" * 70)
    report_lines.append("各视频分组指标")
    report_lines.append("-" * 70)
    for video in sorted(video_errors.keys()):
        errors = video_errors[video]
        abs_errs = [e[0] for e in errors]
        rel_errs = [e[1] for e in errors]
        v_mae = sum(abs_errs) / len(abs_errs)
        v_rmse = math.sqrt(sum(e**2 for e in abs_errs) / len(abs_errs))
        v_mre = sum(rel_errs) / len(rel_errs)
        report_lines.append(f"  [{video}] 评估帧数:{len(errors):2d} | "
                           f"MAE:{v_mae:>8.1f} | RMSE:{v_rmse:>8.1f} | MRE:{v_mre:>7.1%}")
    report_lines.append("")
    report_lines.append("-" * 70)
    report_lines.append("逐帧详细对比")
    report_lines.append("-" * 70)
    report_lines.append(f"{'帧名':35s} | {'视频':>5s} | {'GT':>6s} | {'算法':>6s} | {'绝对误差':>8s} | {'相对误差':>8s}")
    report_lines.append("-" * 70)
    for c in comparisons:
        report_lines.append(
            f"{c['frame']:35s} | {c['video']:>5s} | {c['gt']:>6d} | "
            f"{c['algo']:>6d} | {c['abs_error']:>8d} | {c['rel_error']:>7.1%}"
        )
    report_lines.append("")
    report_lines.append("-" * 70)
    report_lines.append("算法策略说明")
    report_lines.append("-" * 70)
    report_lines.append("  [351] 高密度深色鱼群 -> CLAHE增强 + 固定阈值二值化 + 密度估计法")
    report_lines.append("  [352] 高空浅色圆斑   -> CLAHE增强 + 固定阈值155 + ROI掩膜 + 连通域计数")
    report_lines.append("  [353] 极密集鱼群     -> CLAHE增强 + 固定阈值二值化 + 密度估计法")
    report_lines.append("  [882] 个体较清晰     -> Otsu二值化 + 形态学优化 + 连通域计数")
    report_lines.append("")
    report_lines.append("=" * 70)
    
    report_text = "\n".join(report_lines)
    report_path = Path("output/report.txt")
    with open(report_path, 'w') as f:
        f.write(report_text)
    
    print(f"评估报告已保存至: {report_path}")
    print("\n" + report_text)


if __name__ == "__main__":
    evaluate()
