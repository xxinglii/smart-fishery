# 鱼群计数前端 - 产品需求文档

## Overview
- **Summary**: 开发一个基于浏览器的鱼群计数前端应用，通过上传图片进行二值化处理并自动计数鱼群数量。
- **Purpose**: 提供一个直观、易用的工具，帮助用户快速分析鱼群图像并获得准确的计数结果。
- **Target Users**: 渔业研究人员、水产养殖户、海洋生物学家等需要进行鱼群数量分析的专业人士。

## Goals
- 实现图片上传功能，支持从本地选择鱼群图像
- 提供多种二值化方法（Otsu、自适应阈值等）
- 实现鱼群自动计数功能
- 显示原始图像和二值化处理结果的对比
- 提供计数结果的显示和导出功能
- 优化用户界面，确保操作简单直观

## Non-Goals (Out of Scope)
- 不支持视频实时处理
- 不包含后端服务器处理
- 不提供复杂的图像分割算法
- 不支持批量处理多张图片

## Background & Context
- 项目基于现有的鱼群图像数据集（dataset/raw_frames/）
- 参考了现有的二值化处理代码（src/binarize.py）
- 目标是创建一个纯前端解决方案，无需后端服务器支持

## Functional Requirements
- **FR-1**: 图片上传功能，支持从本地文件系统选择鱼群图像
- **FR-2**: 提供多种二值化方法选择（Otsu阈值、自适应高斯阈值、自适应均值阈值、固定阈值）
- **FR-3**: 实时显示原始图像和二值化处理后的图像
- **FR-4**: 自动检测并计数二值化图像中的鱼群数量
- **FR-5**: 显示计数结果，并支持结果的复制和导出
- **FR-6**: 提供图像缩放和查看功能

## Non-Functional Requirements
- **NFR-1**: 响应式设计，适配不同屏幕尺寸
- **NFR-2**: 处理速度快，二值化和计数操作应在3秒内完成
- **NFR-3**: 界面美观，操作直观，适合非技术用户使用
- **NFR-4**: 支持主流浏览器（Chrome、Firefox、Safari、Edge）

## Constraints
- **Technical**: 纯前端实现，使用HTML5、CSS3和JavaScript
- **Business**: 无特殊商业限制
- **Dependencies**: 使用Canvas API进行图像处理，无需外部库

## Assumptions
- 用户上传的图像为清晰的鱼群照片
- 鱼群在图像中表现为明显的暗色区域
- 图像背景相对均匀，便于二值化处理

## Acceptance Criteria

### AC-1: 图片上传功能
- **Given**: 用户打开应用
- **When**: 用户点击上传按钮并选择本地鱼群图像
- **Then**: 应用成功加载并显示图像
- **Verification**: `human-judgment`

### AC-2: 二值化处理
- **Given**: 用户已上传图像
- **When**: 用户选择二值化方法并调整参数
- **Then**: 应用实时显示二值化处理结果
- **Verification**: `human-judgment`

### AC-3: 鱼群计数
- **Given**: 图像已完成二值化处理
- **When**: 应用自动进行计数或用户点击计数按钮
- **Then**: 应用显示准确的鱼群数量
- **Verification**: `human-judgment`

### AC-4: 结果显示与导出
- **Given**: 计数完成
- **When**: 用户查看计数结果
- **Then**: 结果清晰显示，并可复制或导出
- **Verification**: `human-judgment`

### AC-5: 界面响应性
- **Given**: 用户在不同设备上访问应用
- **When**: 用户操作界面元素
- **Then**: 界面响应迅速，布局适应不同屏幕尺寸
- **Verification**: `human-judgment`

## Open Questions
- [ ] 如何处理不同光照条件下的图像？
- [ ] 如何优化计数算法以提高准确性？
- [ ] 是否需要支持不同类型的鱼群图像？