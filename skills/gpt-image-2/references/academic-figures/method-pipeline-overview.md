# 论文方法 Pipeline 总览图模板

本文件用于生成"论文 method 章节首页那张总览图"：

- 顶会论文 method 章节首图（CVPR / NeurIPS / ICLR / ACL / SIGGRAPH 等）
- 系统总览 / pipeline figure
- 综述论文 framework 概念图
- 实验装置 / 数据流总览
- 答辩 PPT 方法概览

特征：

- 横向 3-6 个 stage 块
- 每个 stage 之间有清晰的有向数据流
- 每个 stage 有：阶段名称 + 简化插图 + 输入 / 输出小标
- 整体白底 / 浅灰底，黑色或深灰主线条
- 出版物字体（Helvetica / Inter / Arial），克制的辅助色
- **极简、几何精确、可单色印刷可读**

## 适用范围

- 论文 method overview / framework figure
- 综述论文 pipeline 总览
- 系统总览图（"我们的方法分 4 步：..."）
- 数据流 / 信号流总览
- 实验流程总览

## 何时使用

- 用户提到 "论文 / paper / method / pipeline / framework / overview / 综述 / 顶会 / arXiv"
- 用户希望视觉「极简、白底、黑线、几何精确、像 CVPR 论文那种总览图」
- 用户已有具体的 stage 描述

不要使用：

- 用户要的是「神经网络架构图」（layer 块 + tensor shape）→ 用 `academic-figures/neural-network-architecture.md`
- 用户要的是「概念 / 原理示意图」（自由度高的科学示意）→ 用 `academic-figures/scientific-schematic.md`
- 用户要的是「步骤教程」（插画感、温暖）→ 用 `infographics/step-by-step-infographic.md`
- 用户要的是「工程系统架构图」（暗色 + 半透明色块）→ 用 `technical-diagrams/system-architecture.md`
- 用户要的是「业务流程图」 → 用 `technical-diagrams/flowchart-decision.md`

## 缺失信息优先提问顺序

1. 方法 / 系统的总名称（写在图标题或图注里）
2. 阶段数（建议 3-6 个，超过 6 个考虑分层）
3. 每个阶段的：名称 + 主操作 + 输入 + 输出
4. 数据形态（图像 / 文本 / 点云 / 音频 / 多模态）—— 决定 stage 内的简化插图
5. 是否有跳连 / 反馈环 / 多分支
6. 比例（横向 16:9 或 2:1，符合论文双栏格式）
7. 是否需要英文标签（论文图通常英文）

## 主模板：横向 N 阶段方法 pipeline 图

📖 描述

整张图横向流动：从最左边的输入开始，依次经过 3-6 个矩形 / 圆角矩形阶段块，每个块内有简化插图 + 阶段名 + 输入输出小标，箭头串联，最右边输出结果。整体克制、对齐严格、几何精确。

📝 提示词

```json
{
  "type": "学术论文方法 Pipeline 总览图（method overview figure）",
  "goal": "生成一张可直接放进顶会论文 method 章节首页的 pipeline 总览图，要求极简、白底、几何精确、出版物级可读",
  "canvas": {
    "aspect_ratio": "{argument name=\"aspect_ratio\" default=\"16:9\"}",
    "background": "pure white #FFFFFF or very light gray #FAFAFA",
    "outer_padding": "60px around the diagram",
    "render_quality": "vector-clean look, anti-aliased edges, sharp text"
  },
  "title_caption": {
    "figure_label": "{argument name=\"figure_label\" default=\"Figure 1.\"}",
    "caption": "{argument name=\"caption\" default=\"Overview of our proposed pipeline.\"}",
    "position": "bottom-center, italic serif or compact sans-serif, smaller font size"
  },
  "input": {
    "label": "{argument name=\"input_label\" default=\"Input Image\"}",
    "thumbnail": "{argument name=\"input_thumbnail\" default=\"a small representative thumbnail (e.g. an RGB image, a text snippet, a point cloud)\"}",
    "position": "leftmost, vertically centered"
  },
  "stages": {
    "count": "{argument name=\"stage_count\" default=\"4\"}",
    "items": [
      {
        "id": "S1",
        "name": "{argument name=\"stage_1_name\" default=\"Feature Extractor\"}",
        "icon_or_glyph": "{argument name=\"stage_1_glyph\" default=\"a stack of 3 small horizontal bars representing CNN feature maps\"}",
        "sub_label": "{argument name=\"stage_1_sub\" default=\"ResNet-50\"}"
      },
      {
        "id": "S2",
        "name": "{argument name=\"stage_2_name\" default=\"Multi-scale Encoder\"}",
        "icon_or_glyph": "{argument name=\"stage_2_glyph\" default=\"a small triangle / pyramid representing multi-scale\"}",
        "sub_label": "{argument name=\"stage_2_sub\" default=\"FPN-style\"}"
      },
      {
        "id": "S3",
        "name": "{argument name=\"stage_3_name\" default=\"Cross-attention Decoder\"}",
        "icon_or_glyph": "{argument name=\"stage_3_glyph\" default=\"two interleaved arrows representing cross-attention\"}",
        "sub_label": "{argument name=\"stage_3_sub\" default=\"Transformer\"}"
      },
      {
        "id": "S4",
        "name": "{argument name=\"stage_4_name\" default=\"Prediction Head\"}",
        "icon_or_glyph": "{argument name=\"stage_4_glyph\" default=\"a small grid representing dense prediction\"}",
        "sub_label": "{argument name=\"stage_4_sub\" default=\"MLP × 2\"}"
      }
    ]
  },
  "output": {
    "label": "{argument name=\"output_label\" default=\"Predicted Mask\"}",
    "thumbnail": "{argument name=\"output_thumbnail\" default=\"a small representative output (e.g. a segmentation mask, a 3D model, a generated image)\"}",
    "position": "rightmost, vertically centered"
  },
  "stage_block_style": {
    "shape": "rounded rectangle (corner radius ~6px)",
    "size_per_stage": "around 120px wide × 80px tall, all stages identical size",
    "fill": "very light tint (e.g. #F1F5F9, #ECFEFF, #FEF9C3) — at most 2 different tints used to group stages by category",
    "border": "1.2px solid dark gray #334155",
    "title_text": "stage name in bold sans-serif (Helvetica / Inter / Arial), 11-12pt, top-center inside block",
    "icon_position": "centered inside block, takes ~50% of block height",
    "sub_label_text": "sub-label in italic gray, below stage name"
  },
  "connectors": {
    "style": "thin black arrows (1.2px) with simple triangle arrowheads",
    "rule": "horizontal flow left → right; small label above arrow only when carrying intermediate data type (e.g. 'feature map H/4 × W/4 × 256')",
    "skip_connections": {
      "enabled": "{argument name=\"skip_connections\" default=\"false\"}",
      "rule": "if true, draw curved arrows that arc above the main flow with dashed style, label them 'skip' / 'residual'"
    }
  },
  "extras": {
    "loss_branch": {
      "enabled": "{argument name=\"loss_branch_enabled\" default=\"false\"}",
      "label": "{argument name=\"loss_branch_label\" default=\"L = L_cls + λ L_reg\"}",
      "rule": "if enabled, draw a small dashed branch from output back to a 'Loss' box, formula in italic"
    },
    "color_legend": {
      "enabled": "{argument name=\"color_legend_enabled\" default=\"false\"}",
      "rule": "if multiple stage tints are used, add a tiny legend bottom-right explaining each color group"
    }
  },
  "constraints": {
    "must_keep": [
      "all stage blocks identical size and vertically aligned",
      "white or near-white background, no gradient, no decoration",
      "only sans-serif typography, no script / handwritten / display fonts",
      "color palette ≤ 4 colors total, must remain readable in grayscale print",
      "input thumbnail and output thumbnail same size, both have a thin border",
      "arrows must not overlap stage blocks; labels must not collide with arrows",
      "use English labels by default unless user requested otherwise",
      "the figure should look like it came directly from a CVPR / NeurIPS PDF"
    ],
    "avoid": [
      "3D effects, drop shadows, gradients, glossy fills",
      "cartoon icons, emoji, hand-drawn wobble",
      "saturated colors (no neon, no vivid)",
      "Helvetica + serif mixed in same diagram",
      "decorative background patterns / textures",
      "illustrative photo backgrounds inside stage blocks",
      "stage blocks of unequal size or unaligned baselines",
      "Chinese mixed with English labels unless explicitly bilingual"
    ]
  }
}
```

### 参数策略

- **必问**：`stage_count`、每个 stage 的名称
- **可默认**：`aspect_ratio`（16:9）、`background`（白色）、`figure_label` / `caption`、stage 块尺寸 / 颜色
- **可随机**：每个 stage 内的 `icon_or_glyph` 具体造型（用户没指定时可推断）

### 自动补全策略

- 用户给出方法名和"我有 4 个 stage"但没说每 stage 是什么 → 反问（不能瞎编算法细节）
- 用户给出 stage 名但没给 sub_label → 留空或自动推断（可推断时填上 "ResNet-50" 这种典型选项）
- 用户没说有没有跳连 → 默认 `skip_connections: false`
- 用户没说有没有 loss → 默认 `loss_branch: false`（只在用户明确要 training pipeline 时才加）
- 用户说"中文论文" / "答辩" → 切换标签为中文 + 字体 PingFang / 思源黑

## 变体 1：双行多分支 pipeline

```json
{
  "type": "双行多分支 pipeline 图",
  "modify": {
    "layout": "上下两行 stages 平行流动；中间用 fusion block 汇合",
    "use_case": "多模态融合方法（如 visual + text，或 RGB + depth）",
    "rule": "上行处理一种模态、下行处理另一种，最后中央汇合到 fusion block 再到输出"
  }
}
```

适用：多模态、双流网络、teacher-student 方法。

## 变体 2：训练 + 推理两套 pipeline 对照

```json
{
  "type": "Training vs Inference 对照 pipeline 图",
  "modify": {
    "layout": "上下两行：上行 'Training Phase'（含 loss、ground truth 输入、梯度回流），下行 'Inference Phase'（仅前向、轻量化）",
    "annotation": "左侧用大括号标 'Training' / 'Inference'",
    "use_case": "需要明确区分训练和推理流程的方法"
  }
}
```

适用：知识蒸馏、自监督预训练、半监督方法。

## 变体 3：迭代 / Recurrent pipeline

```json
{
  "type": "迭代式 / 循环 pipeline 图",
  "modify": {
    "layout": "stages 横向，但最后一个 stage 有一条曲线箭头回到第二个 stage，形成循环",
    "annotation": "在循环箭头上标 'iterate × N' 或 'until convergence'",
    "use_case": "迭代优化、扩散去噪、Diffusion model timestep 流"
  }
}
```

适用：扩散模型、迭代细化方法、能量模型。

## 变体 4：工程类技术路线图（左 / 中 / 右 三段式）

```json
{
  "type": "工程类技术路线图（engineering research roadmap）",
  "modify": {
    "layout": "左 / 中 / 右 三段式：左侧 = 研究对象与背景（简化线稿示意），中间 = 多步骤分析路径（4-7 个学术化模块），右侧 = 输出与结果导向（3-4 个短语化结论方向）",
    "rule": "三段宽度比约 2:5:2；左右两侧用学术化短语 + 简化线稿，禁止商业图标 / 写实渲染 / 火焰浓烟特效；中间分析路径模块大小统一、对齐严格、连接关系简洁",
    "tone": "更接近高质量 Graphical Abstract 与方法路线图融合的工程论文图，不是 office 流程框图，也不是商业海报",
    "stage_naming_examples_for_engineering": [
      "fuel / material characterization",
      "kinetics / thermodynamics analysis",
      "experimental setup OR numerical model",
      "boundary / operating condition design",
      "process simulation or experiment",
      "field / behavior evaluation",
      "emission / performance analysis"
    ],
    "color_palette": "deep blue / slate blue / charcoal as main; one low-saturation amber accent for high-temperature or risk modules ONLY when user signaled it; ≤ 3 main colors total",
    "data_authenticity": "if no real data is provided, do NOT invent equations, kinetic constants, temperature values, emission factors, or chart numbers; render module summaries as qualitative phrases only",
    "use_case": "能源动力 / 燃烧 / 热能工程 / 环境工程 / 材料 / 化工 等工程方向的开题答辩、综述论文、Methods 章节首图；区别于 CS/CV pipeline 的横向 stage 块结构"
  }
}
```

适用：能源动力、燃烧、热能工程、环境工程、化工、材料等工程方向的研究路线图与高质量 Graphical Abstract 融合需求；CS/CV/ML 类首选主模板。

## 避免事项

- 用渐变 / drop shadow / 玻璃质感 → 立刻 "PPT 风" 而不是论文风
- stage 块大小不一 / 高度不齐
- 用 emoji / 卡通图标当 stage glyph
- 用 Comic Sans / 手写体当标题字体
- 颜色超过 4 种或饱和度过高
- 输入输出缩略图分辨率明显不同
- 箭头穿过 stage 块或标签碰撞
- 中英文标签混用（除非显式双语）
- 把"对比方法"也画在同一 pipeline 上（应该用 `qualitative-comparison-grid.md`）
- 把网络层细节（卷积核大小、激活函数）塞进 pipeline 图（这属于 `neural-network-architecture.md` 的范畴）
