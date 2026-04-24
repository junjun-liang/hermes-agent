---
name: segment-anything
description: 使用 Meta 的 SAM（Segment Anything Model）进行图像分割、对象检测和掩码生成。用于交互式分割、自动掩码、零样本分割和图像注释。支持 SAM、SAM 2 和 MobileSAM。
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [segment-anything, torch, torchvision, opencv-python, matplotlib]
metadata:
  hermes:
    tags: [Computer Vision, Segmentation, SAM, Segment Anything, Meta AI, Object Detection, Mask Generation, Zero-Shot]

---

# SAM - Segment Anything Model

## 何时使用此技能

当需要以下情况时使用 SAM：
- **交互式图像分割**（点击/框选选择对象）
- **自动对象检测和掩码生成**
- **零样本分割**（无需训练数据）
- **图像注释和标签**
- **构建基于分割的应用**（视频分析、医学图像）
- **需要快速原型分割模型**

**创建者**：Meta AI | **GitHub Stars**：45,000+ | **版本**：SAM、SAM 2（视频）

## 安装

```bash
# 基本 SAM
pip install segment-anything

# 或从源代码
git clone https://github.com/facebookresearch/segment-anything
cd segment-anything
pip install -e .

# SAM 2（带视频支持）
pip install git+https://github.com/facebookresearch/segment-anything-2.git
```

## 快速开始

### 基本图像分割

```python
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator
import cv2
import matplotlib.pyplot as plt
import numpy as np

# 加载模型
sam_checkpoint = "sam_vit_h_4b8939.pth"
model_type = "vit_h"
sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
sam.to("cuda")

# 加载图像
image = cv2.imread("image.jpg")
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# 自动生成所有对象的掩码
mask_generator = SamAutomaticMaskGenerator(sam)
masks = mask_generator.generate(image)

print(f"发现 {len(masks)} 个对象")

# 可视化
plt.figure(figsize=(10, 10))
plt.imshow(image)
for mask in masks:
    m = mask['segmentation']
    plt.imshow(m, alpha=0.5)
plt.axis('off')
plt.savefig("segmentation_result.png")
```

### 交互式分割（点/框）

```python
from segment_anything import sam_model_registry, SamPredictor
import cv2
import numpy as np

# 加载模型和预测器
sam = sam_model_registry["vit_h"](checkpoint="sam_vit_h_4b8939.pth")
sam.to("cuda")
predictor = SamPredictor(sam)

# 加载图像
image = cv2.imread("image.jpg")
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
predictor.set_image(image)

# 使用点分割
input_point = np.array([[500, 375]])  # 点击坐标
input_label = np.array([1])  # 1 = 前景，0 = 背景

masks, scores, logits = predictor.predict(
    point_coords=input_point,
    point_labels=input_label,
    multimask_output=True
)

# masks: [3, H, W] - 3 个候选掩码
# scores: [3] - 每个掩码的质量分数
# logits: [3, H, W] - 原始 logits

# 选择最佳掩码
best_mask = masks[np.argmax(scores)]
print(f"最佳掩码分数: {np.max(scores):.3f}")

# 可视化
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 10))
plt.imshow(image)
plt.imshow(best_mask, alpha=0.5)
plt.scatter(input_point[:, 0], input_point[:, 1], c='r', marker='o')
plt.axis('off')
plt.savefig("point_segmentation.png")
```

### 带框的分割

```python
# 使用边界框
input_box = np.array([200, 200, 600, 500])  # [x1, y1, x2, y2]

masks, scores, logits = predictor.predict(
    box=input_box,
    multimask_output=False
)

mask = masks[0]  # 单个掩码
```

## 模型比较

| 模型 | 大小 | VRAM | 速度 | 质量 | 用途 |
|--------|-------|---------|---------|---------|----------|
| **ViT-H (huge)** | ~2.4GB | 12GB | 慢 | 最佳 | 最高质量 |
| **ViT-L (large)** | ~1.2GB | 8GB | 中 | 好 | **推荐** |
| **ViT-B (base)** | ~375MB | 4GB | 快 | 基础 | 资源受限 |
| **MobileSAM** | ~40MB | 1GB | 最快 | 可接受 | 移动端/边缘 |

## 常见模式

### 模式 1：自动对象检测

```python
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator
import cv2
import json

# 加载模型
sam = sam_model_registry["vit_l"](checkpoint="sam_vit_l_0b3195.pth")
sam.to("cuda")

# 自动掩码生成器
mask_generator = SamAutomaticMaskGenerator(
    model=sam,
    points_per_side=32,        # 每侧采样点数（更多 = 更详细）
    pred_iou_thresh=0.88,      # IoU 阈值过滤
    stability_score_thresh=0.95, # 稳定性阈值
    crop_n_layers=1,           # 裁剪层数
    crop_n_points_downscale_factor=2,
    min_mask_region_area=100   # 最小区域（像素）
)

# 生成掩码
image = cv2.imread("image.jpg")
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
masks = mask_generator.generate(image)

# 处理结果
for i, mask in enumerate(masks):
    area = mask['area']
    bbox = mask['bbox']  # [x, y, w, h]
    stability = mask['stability_score']

    print(f"对象 {i}: 面积={area}, 边界框={bbox}, 稳定性={stability:.3f}")

    # 保存掩码
    cv2.imwrite(f"mask_{i:03d}.png", mask['segmentation'] * 255)
```

### 模式 2：对象计数

```python
def count_objects(image_path, sam):
    """计算图像中对象的数量。"""
    mask_generator = SamAutomaticMaskGenerator(sam)
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    masks = mask_generator.generate(image)

    # 按面积过滤小对象
    large_masks = [m for m in masks if m['area'] > 1000]

    return len(large_masks), masks

# 使用
sam = sam_model_registry["vit_l"](checkpoint="sam_vit_l_0b3195.pth")
sam.to("cuda")

count, masks = count_objects("birds.jpg")
print(f"发现 {count} 个对象")
```

### 模式 3：对象裁剪

```python
def extract_objects(image_path, output_dir="objects/"):
    """从图像中提取所有对象为单独图像。"""
    import os
    os.makedirs(output_dir, exist_ok=True)

    sam = sam_model_registry["vit_l"](checkpoint="sam_vit_l_0b3195.pth")
    sam.to("cuda")
    mask_generator = SamAutomaticMaskGenerator(sam)

    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    masks = mask_generator.generate(image_rgb)

    extracted = []
    for i, mask_data in enumerate(masks):
        mask = mask_data['segmentation']
        bbox = mask_data['bbox']

        # 应用掩码
        masked_image = np.zeros_like(image)
        masked_image[mask] = image[mask]

        # 裁剪到边界框
        x, y, w, h = [int(v) for v in bbox]
        cropped = masked_image[y:y+h, x:x+w]

        if cropped.size > 0:
            filepath = os.path.join(output_dir, f"object_{i:03d}.png")
            cv2.imwrite(filepath, cropped)
            extracted.append(filepath)

    print(f"已提取 {len(extracted)} 个对象到 {output_dir}")
    return extracted
```

### 模式 4：视频分割（SAM 2）

```python
# 使用 SAM 2 进行视频分割
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor
import cv2

# 加载 SAM 2
sam2 = build_sam2("sam2_hiera_large.yaml", "sam2_hiera_large.pt")
predictor = SAM2ImagePredictor(sam2)

# 视频帧处理
cap = cv2.VideoCapture("video.mp4")
frame_count = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    predictor.set_image(frame_rgb)

    # 为第一帧提供提示词
    if frame_count == 0:
        masks, scores, logits = predictor.predict(
            point_coords=np.array([[300, 200]]),
            point_labels=np.array([1])
        )

    frame_count += 1
    if frame_count > 30:  # 测试 30 帧
        break
```

## SAM 2 新特性

### 视频对象跟踪

```python
from sam2.sam2_video_predictor import SAM2VideoPredictor

# 加载视频预测器
predictor = SAM2VideoPredictor.build_model(
    "sam2_hiera_large.yaml",
    "sam2_hiera_large.pt"
)

# 初始化视频
video_handle = predictor.init_state("video.mp4")

# 添加提示词（第一帧）
_, out_obj_ids, out_mask_logits = predictor.add_new_points(
    video_handle,
    frame_idx=0,
    obj_ids=[1, 2],
    points=[[[300, 200]], [[500, 400]]],
    labels=[[1], [1]]  # 1 = 前景
)

# 传播到其他帧
for frame_idx, image_np in enumerate(video_frames[1:], 1):
    _, out_obj_ids, out_mask_logits = predictor.track(video_handle)
    # out_mask_logits 包含当前帧的掩码
```

## 故障排除

### 内存问题

```python
# 使用更小的模型
sam = sam_model_registry["vit_b"](checkpoint="sam_vit_b_01ec64.pth")

# 或 MobileSAM
from mobile_sam import sam_model_registry, SamPredictor
sam = sam_model_registry["vit_t"](checkpoint="mobile_sam.pt")

# 减少掩码生成器中的点
mask_generator = SamAutomaticMaskGenerator(
    sam,
    points_per_side=16  # 从 32 减少
)
```

### 质量差

```python
# 使用更大的模型
sam = sam_model_registry["vit_h"](checkpoint="sam_vit_h_4b8939.pth")

# 增加采样点
mask_generator = SamAutomaticMaskGenerator(
    sam,
    points_per_side=64,        # 更多点
    pred_iou_thresh=0.8,       # 降低阈值以捕获更多对象
    stability_score_thresh=0.9  # 降低稳定性
)
```

### 合并多个点/框

```python
# 使用多个点
input_point = np.array([
    [200, 300],  # 点 1
    [400, 500],  # 点 2
    [600, 200]   # 点 3
])
input_label = np.array([1, 1, 0])  # 前景, 前景, 背景

masks, scores, logits = predictor.predict(
    point_coords=input_point,
    point_labels=input_label,
    multimask_output=True
)
```

## 集成示例

### 带 Gradio

```python
import gradio as gr
from segment_anything import sam_model_registry, SamPredictor
import numpy as np
import cv2

# 加载模型
sam = sam_model_registry["vit_l"](checkpoint="sam_vit_l_0b3195.pth")
sam.to("cuda")
predictor = SamPredictor(sam)

def segment(image, click_points):
    """根据点击分割图像。"""
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    predictor.set_image(image_rgb)

    if click_points:
        points = np.array(click_points)
        labels = np.ones(len(points))

        masks, scores, _ = predictor.predict(
            point_coords=points,
            point_labels=labels,
            multimask_output=True
        )

        mask = masks[np.argmax(scores)]
        # 应用掩码
        result = image.copy()
        result[mask == 0] = 0
        return result
    return image

demo = gr.Interface(
    fn=segment,
    inputs=[
        gr.Image(type="numpy"),
        gr.JSON(label="点击点")
    ],
    outputs=gr.Image()
)
demo.launch()
```

### 带 FastAPI

```python
from fastapi import FastAPI, File, UploadFile
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator
import cv2
import numpy as np

app = FastAPI()

# 加载模型
sam = sam_model_registry["vit_l"](checkpoint="sam_vit_l_0b3195.pth")
sam.to("cuda")
mask_generator = SamAutomaticMaskGenerator(sam)

@app.post("/segment")
async def segment_image(file: UploadFile = File(...)):
    # 读取图像
    content = await file.read()
    image = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # 生成掩码
    masks = mask_generator.generate(image_rgb)

    # 返回结果
    return {
        "num_objects": len(masks),
        "objects": [
            {
                "area": int(m['area']),
                "bbox": [float(v) for v in m['bbox']],
                "stability": float(m['stability_score'])
            }
            for m in masks
        ]
    }
```

## 硬件要求

- **GPU**：CUDA 11.7+ 推荐（可在 CPU 上运行，非常慢）
- **VRAM**：
  - ViT-B：~4GB
  - ViT-L：~8GB
  - ViT-H：~12GB
  - MobileSAM：~1GB
- **RAM**：16GB+ 推荐
- **存储**：每个模型 40MB-2.4GB

## 资源

- **SAM GitHub**：https://github.com/facebookresearch/segment-anything（45k+ stars）
- **SAM 2 GitHub**：https://github.com/facebookresearch/segment-anything-2
- **演示**：https://segment-anything.com/demo
- **论文**："Segment Anything"（ICCV 2023）
- **模型下载**：https://github.com/facebookresearch/segment-anything#model-checkpoints
