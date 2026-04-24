---
name: clip-vision-model
description: 带 CLIP（对比语言-图像预训练）进行图像-文本嵌入、零样本图像分类和图像相似性搜索。OpenAI 的多模态模型将图像和文本映射到共享嵌入空间。
version: 1.0.0
author: Orchestra Research
license: MIT
dependencies: [torch, torchvision, transformers, open-clip-torch]
metadata:
  hermes:
    tags: [Vision, CLIP, Embeddings, Image Classification, Multimodal, Zero-Shot, OpenAI, Image Search]

---

# CLIP - 对比语言-图像预训练

## 何时使用此技能

当需要以下情况时使用 CLIP：
- **零样本图像分类**（无训练数据）
- **图像-文本嵌入**用于相似性搜索
- **多模态搜索**（"查找红狗的照片"）
- **图像-文本相似度计算**
- **构建带自然语言查询的图像搜索引擎**
- **视觉特征提取**用于下游任务

**创建者**：OpenAI | **论文**：2021 | **GitHub Stars**：11,000+ (open_clip)

## 安装

```bash
# OpenAI 官方 CLIP
pip install openai-clip  # 或
pip install git+https://github.com/openai/CLIP.git

# 或 OpenCLIP（推荐，更多模型）
pip install open-clip-torch
```

## 快速开始

### 使用 OpenCLIP

```python
import open_clip
import torch
from PIL import Image

# 加载模型
model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")

# 加载图像
image = preprocess(Image.open("image.jpg")).unsqueeze(0)
text = open_clip.tokenize(["一只狗的照片", "一只猫的照片", "一辆车的照片"])

# 获取嵌入
with torch.no_grad():
    image_features = model.encode_image(image)
    text_features = model.encode_text(text)

    # 计算相似度
    image_features /= image_features.norm(dim=-1, keepdim=True)
    text_features /= text_features.norm(dim=-1, keepdim=True)

    similarity = (image_features @ text_features.T).softmax(dim=-1)

print(similarity)  # [概率 狗, 概率 猫, 概率 车]
```

### 零样本分类

```python
import open_clip
import torch
from PIL import Image

model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")

# 图像
image = preprocess(Image.open("image.jpg")).unsqueeze(0)

# 候选类别
classes = ["猫", "狗", "鸟", "汽车"]
text = open_clip.tokenize([f"一只{c}的照片" for c in classes])

# 预测
with torch.no_grad():
    image_features = model.encode_image(image)
    text_features = model.encode_text(text)

    image_features /= image_features.norm(dim=-1, keepdim=True)
    text_features /= text_features.norm(dim=-1, keepdim=True)

    probs = (image_features @ text_features.T).softmax(dim=-1)

predicted_class = classes[probs[0].argmax().item()]
print(f"预测: {predicted_class}")
```

## 核心概念

### 1. 多模态嵌入

CLIP 将图像和文本映射到共享嵌入空间：

```python
# 图像 → 512 维向量
image_embedding = model.encode_image(image)  # 形状：[1, 512]

# 文本 → 512 维向量
text_embedding = model.encode_text(text)     # 形状：[1, 512]

# 余弦相似度衡量相关性
similarity = torch.cosine_similarity(image_embedding, text_embedding)
```

**关键点：**
- 图像和文本嵌入维度相同
- 余弦相似度衡量语义相关性
- 训练了 4 亿对（图像，文本）

### 2. 零样本能力

无需训练数据 — CLIP 使用提示词模板进行分类：

```python
def zero_shot_classify(image, classes, model, preprocess):
    """无训练数据分类。"""
    # 模板提示词
    prompts = [f"一只{c}的照片" for c in classes]
    text = open_clip.tokenize(prompts)

    with torch.no_grad():
        image_features = model.encode_image(preprocess(image).unsqueeze(0))
        text_features = model.encode_text(text)

        image_features /= image_features.norm(dim=-1, keepdim=True)
        text_features /= text_features.norm(dim=-1, keepdim=True)

        probs = (image_features @ text_features.T).softmax(dim=-1)

    return {cls: float(prob) for cls, prob in zip(classes, probs[0])}

# 使用
classes = ["猫", "狗", "鸟", "汽车", "花"]
result = zero_shot_classify(image, classes, model, preprocess)
print(result)  # {'猫': 0.6, '狗': 0.3, ...}
```

### 3. 模型选择

| 模型 | 参数 | 速度 | 质量 | ImageNet 准确率 | 用途 |
|--------|---------|---------|---------|--------------|----------|
| ViT-B-32 | ~150M | 最快 | 基础 | 67.1% | 快速原型 |
| ViT-B-16 | ~150M | 快 | 好 | 68.9% | **推荐** |
| ViT-L-14 | ~370M | 中 | 更好 | 75.5% | 高质量 |
| ViT-H-14 | ~960M | 慢 | 最佳 | 78.0% | 最高质量 |
| ViT-g-14 | ~1.8B | 最慢 | 优秀 | 80.1% | 最大模型 |

### 4. 预训练变体

```python
# OpenAI 原始预训练（推荐用于通用用途）
model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")

# LAION-2B 预训练（可能更适合艺术/创意图像）
model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k")

# DataComp 预训练（针对数据集优化的最新模型）
model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="datacomp_xl_s13b_b90k")
```

## 常见模式

### 模式 1：图像搜索引擎

```python
import open_clip
import torch
from PIL import Image
import os
import json

class ImageSearchEngine:
    def __init__(self, model_name="ViT-B-32", pretrained="openai"):
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(model_name, pretrained=pretrained)
        self.image_features = {}

    def index(self, image_dir):
        """将目录中的所有图像编入索引。"""
        for filename in os.listdir(image_dir):
            if filename.endswith(('.jpg', '.png', '.jpeg')):
                filepath = os.path.join(image_dir, filename)
                image = self.preprocess(Image.open(filepath)).unsqueeze(0)

                with torch.no_grad():
                    features = self.model.encode_image(image)
                    features /= features.norm(dim=-1, keepdim=True)

                self.image_features[filepath] = features

        print(f"已索引 {len(self.image_features)} 张图像")

    def search(self, query, top_k=5):
        """按文本查询搜索图像。"""
        text = open_clip.tokenize([query])

        with torch.no_grad():
            query_features = self.model.encode_text(text)
            query_features /= query_features.norm(dim=-1, keepdim=True)

            # 计算与所有图像的相似度
            scores = []
            for filepath, image_features in self.image_features.items():
                sim = (query_features @ image_features.T).item()
                scores.append((filepath, sim))

            # 返回 top_k
            scores.sort(key=lambda x: x[1], reverse=True)
            return scores[:top_k]

# 使用
engine = ImageSearchEngine()
engine.index("images/")

results = engine.search("日落时的红狗")
for filepath, score in results:
    print(f"{filepath}: {score:.3f}")
```

### 模式 2：图像相似性

```python
import open_clip
import torch
from PIL import Image

model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")

def image_similarity(img1_path, img2_path):
    """计算两张图像的语义相似度。"""
    img1 = preprocess(Image.open(img1_path)).unsqueeze(0)
    img2 = preprocess(Image.open(img2_path)).unsqueeze(0)

    with torch.no_grad():
        features1 = model.encode_image(img1)
        features2 = model.encode_image(img2)

        features1 /= features1.norm(dim=-1, keepdim=True)
        features2 /= features2.norm(dim=-1, keepdim=True)

        sim = (features1 @ features2.T).item()

    return sim

sim = image_similarity("photo1.jpg", "photo2.jpg")
print(f"相似度: {sim:.3f}")  # 接近 1 = 相似，接近 0 = 不同
```

### 模式 3：多模态聚类

```python
import open_clip
import torch
from PIL import Image
from sklearn.cluster import KMeans

model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32")

# 编码多张图像
images = []
for filename in os.listdir("photos/"):
    if filename.endswith(('.jpg', '.png')):
        img = preprocess(Image.open(f"photos/{filename}")).unsqueeze(0)
        with torch.no_grad():
            features = model.encode_image(img)
            features /= features.norm(dim=-1, keepdim=True)
            images.append(features.squeeze(0))

# 聚类
features = torch.stack(images).numpy()
kmeans = KMeans(n_clusters=5).fit(features)

# 输出
for i, label in enumerate(kmeans.labels_):
    print(f"图像 {i}: 类别 {label}")
```

### 模式 4：内容过滤

```python
def filter_safe_images(images, model, preprocess, threshold=0.3):
    """过滤掉可能不安全的图像。"""
    # NSFW 描述
    nsfw_descriptions = [
        "explicit content",
        "nsfw material",
        "adult content"
    ]
    text = open_clip.tokenize(nsfw_descriptions)

    safe_images = []
    for img in images:
        image = preprocess(img).unsqueeze(0)
        with torch.no_grad():
            image_features = model.encode_image(image)
            text_features = model.encode_text(text)

            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)

            nsfw_scores = (image_features @ text_features.T).max().item()

        if nsfw_scores < threshold:
            safe_images.append(img)

    return safe_images
```

## 最佳实践

### 1. 使用具体的提示词模板

```python
# ❌ 坏：通用
classes = ["猫", "狗"]
text = open_clip.tokenize(classes)

# ✅ 好：具体
classes = ["一只猫的照片", "一只狗的照片"]
text = open_clip.tokenize(classes)

# ✅ 更好：多个模板
templates = [
    "一只{}的照片",
    "{}的照片",
    "{}的图片"
]
prompts = [template.format(c) for c in classes for template in templates]
text = open_clip.tokenize(prompts)
# 平均多个提示词的嵌入
```

### 2. 归一化嵌入

```python
# ✅ 始终在比较之前归一化
image_features /= image_features.norm(dim=-1, keepdim=True)
text_features /= text_features.norm(dim=-1, keepdim=True)
similarity = (image_features @ text_features.T)  # 余弦相似度
```

### 3. 批处理

```python
# 一次编码多张图像
images = torch.stack([preprocess(Image.open(f)) for f in filenames])
with torch.no_grad():
    features = model.encode_image(images)  # 批量处理
```

### 4. 缓存嵌入

```python
import hashlib
import pickle

def cache_embedding(filepath, model, preprocess, cache_dir=".cache"):
    """缓存图像嵌入。"""
    os.makedirs(cache_dir, exist_ok=True)

    # 基于文件内容的哈希
    with open(filepath, "rb") as f:
        file_hash = hashlib.md5(f.read()).hexdigest()

    cache_path = os.path.join(cache_dir, f"{file_hash}.pt")

    if os.path.exists(cache_path):
        return torch.load(cache_path)

    # 计算并缓存
    image = preprocess(Image.open(filepath)).unsqueeze(0)
    with torch.no_grad():
        features = model.encode_image(image)
        features /= features.norm(dim=-1, keepdim=True)

    torch.save(features, cache_path)
    return features
```

## 与替代方案比较

| 模型 | 模态 | 零样本 | 速度 | 质量 | 用途 |
|---------|---------|---------|---------|---------|----------|
| **CLIP** | 图像+文本 | ✅ 是 | 快 | 好 | 通用分类 |
| **BLIP** | 图像+文本 | ⚠️ 有限 | 中 | 更好 | 图像字幕 |
| **DINOv2** | 仅图像 | ❌ 否 | 快 | 更好 | 视觉特征 |
| **SigLIP** | 图像+文本 | ✅ 是 | 中 | 最佳 | 最先进 |
| **EVA-CLIP** | 图像+文本 | ✅ 是 | 中 | 优秀 | 高性能 |

**何时选择 CLIP：**
- 零样本图像分类
- 图像-文本相似性
- 多模态搜索
- 快速原型

**何时选择替代方案：**
- SigLIP：需要最先进准确度
- DINOv2：仅需要视觉特征
- BLIP：需要图像字幕生成

## 资源

- **OpenAI 论文**：https://arxiv.org/abs/2103.00020
- **OpenCLIP**：https://github.com/mlfoundations/open_clip（11k+ stars）
- **演示**：https://huggingface.co/spaces/openai/clip-interrogator
- **模型**：https://huggingface.co/openai/clip-vit-{base,large}-patch{16,32}
