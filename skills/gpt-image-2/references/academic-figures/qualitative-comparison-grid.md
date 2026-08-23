# 多方法 Qualitative 对比网格模板

本文件用于生成"论文 qualitative results 对比网格"：

- CV 论文：多方法分割 / 检测 / 生成结果对比
- NLP 论文：多方法生成文本对比（截图式）
- 3D / 重建论文：多方法重建结果对比
- Diffusion / 图像生成论文：不同 prompt × 不同方法的网格
- Ablation study 的视觉对比

特征：

- 严格的网格：行 = 样本 / 输入，列 = 方法（含 GT 和 Ours）
- 列首行有方法名（带 citation）
- Ours 列通常加边框 / 高亮
- 单元格内容统一（图片 / 文本片段 / heatmap）
- 网格之间留细 gap，整体白底
- 可附 caption 解释

## 适用范围

- 论文 qualitative results section
- Ablation study 的视觉对比
- 顶会 supplementary 大网格图
- 综述论文 method gallery
- 答辩 PPT 对比页

## 何时使用

- 用户提到 "qualitative / 对比图 / comparison grid / methods comparison / ablation visual"
- 用户希望「行=样本、列=方法的标准论文对比网格」

不要使用：

- 用户要的是「双产品消费对比」 → 用 `infographics/comparison-infographic.md`
- 用户要的是「多人头像网格」 → 用 `avatars-and-profile/character-grid-portrait.md`
- 用户要的是「数据图表」 → 用 `academic-figures/publication-chart.md`
- 用户要的是「视频帧序列」 → 用 `storyboards-and-sequences/`

## 缺失信息优先提问顺序

1. 行数（样本数，建议 3-6 行）
2. 列数（方法数，建议 3-6 列，含 Input/GT 和 Ours）
3. 每列的方法名（含 citation 引用，如 "Method A [12]"）
4. 单元格内容类型（RGB 图 / mask / heatmap / 文本片段 / 3D 渲染）
5. 是否要 row labels（左侧标"Sample 1 / 2 / ..."或"Easy / Medium / Hard"）
6. 是否要在某些位置加红框 zoom-in（focus area）
7. 是否要 caption 注释

## 主模板：Qualitative comparison grid (M rows × N cols)

📖 描述

整张图是严格的 M×N 网格：每一行是一个样本，每一列是一个方法。最左可加 row labels，最上一行是列首（方法名 + citation）。Ours 列加边框高亮，可在某些 cell 内画红色 zoom-in 框。

📝 提示词

```json
{
  "type": "Qualitative Comparison Grid（论文级多方法多样本对比网格）",
  "goal": "生成一张可直接放进论文 qualitative results 章节的网格对比图，要求严格对齐、清晰列首、Ours 高亮、可单色印刷可读",
  "canvas": {
    "aspect_ratio": "{argument name=\"aspect_ratio\" default=\"4:3\"}",
    "background": "white #FFFFFF",
    "outer_padding": "40px"
  },
  "grid": {
    "rows": "{argument name=\"rows\" default=\"4\"}",
    "cols": "{argument name=\"cols\" default=\"5\"}",
    "cell_size_rule": "all cells identical size; gap between cells 4-6px",
    "cell_aspect": "{argument name=\"cell_aspect\" default=\"square\"}"
  },
  "headers": {
    "column_headers": {
      "enabled": true,
      "items": [
        { "id": "C1", "label": "{argument name=\"col1_name\" default=\"Input\"}" },
        { "id": "C2", "label": "{argument name=\"col2_name\" default=\"Method A [12]\"}" },
        { "id": "C3", "label": "{argument name=\"col3_name\" default=\"Method B [34]\"}" },
        { "id": "C4", "label": "{argument name=\"col4_name\" default=\"Method C [56]\"}" },
        { "id": "C5", "label": "{argument name=\"col5_name\" default=\"Ours\"}", "highlight": true }
      ],
      "style": "centered above each column, sans-serif bold 11pt, citations in smaller superscript or in [brackets]"
    },
    "row_labels": {
      "enabled": "{argument name=\"row_labels_enabled\" default=\"true\"}",
      "items": [
        "{argument name=\"row1_label\" default=\"Sample 1\"}",
        "{argument name=\"row2_label\" default=\"Sample 2\"}",
        "{argument name=\"row3_label\" default=\"Sample 3\"}",
        "{argument name=\"row4_label\" default=\"Sample 4\"}"
      ],
      "style": "rotated 90° on the left margin OR placed above each row in italic 10pt"
    }
  },
  "cell_content": {
    "type": "{argument name=\"content_type\" default=\"rgb_image\"}",
    "options_explained": {
      "rgb_image": "natural images / photos",
      "segmentation_mask": "color-coded mask overlays",
      "heatmap": "viridis / jet style heatmap",
      "depth_map": "grayscale or turbo colormap",
      "text_snippet": "rendered text block in a code-like box",
      "3d_render": "rendered 3D mesh from a fixed viewpoint",
      "side_by_side": "two halves: input | result"
    },
    "consistency_rule": "all cells in the same row should depict the SAME underlying sample so the comparison is fair"
  },
  "highlights": {
    "ours_column": {
      "enabled": true,
      "style": "thicker border 1.5px in deep red / accent color (e.g. #DC2626) around each Ours cell"
    },
    "zoom_in_boxes": {
      "enabled": "{argument name=\"zoom_in_enabled\" default=\"false\"}",
      "rule": "if true, draw small red rectangles inside cells highlighting interesting regions; same red box appears at the same coordinate across the row to make comparison fair",
      "callout_style": "optional zoomed crop placed below the row, connected by thin lines"
    }
  },
  "caption": {
    "enabled": "{argument name=\"caption_enabled\" default=\"true\"}",
    "label": "{argument name=\"figure_label\" default=\"Figure 4.\"}",
    "text": "{argument name=\"caption_text\" default=\"Qualitative comparison with state-of-the-art methods. Our method (last column) preserves fine details and reduces artifacts.\"}",
    "style": "below the grid, italic serif or compact sans-serif, justified, smaller font"
  },
  "constraints": {
    "must_keep": [
      "all cells identical size and tightly aligned",
      "white or near-white background, no gradient",
      "column headers clearly above each column with citation",
      "Ours column visually distinguished (border / shaded header)",
      "row content depicts the same sample across all methods",
      "if zoom-in boxes used, position is identical across the row",
      "labels in English by default, no mixing with Chinese unless requested",
      "must remain interpretable in grayscale print"
    ],
    "avoid": [
      "different cell sizes between rows / columns",
      "random colors as cell backgrounds (cells are content, not decoration)",
      "missing citations on baseline methods",
      "ours column hidden or unmarked",
      "rotated cells / tilted layouts (must be axis-aligned)",
      "decorative emoji / cartoon icons inside cells",
      "varying content type per row (e.g. one row mask, next row RGB) without explicit row label",
      "more than 6 cols (becomes unreadable in two-column paper format)"
    ]
  }
}
```

### 参数策略

- **必问**：`rows`、`cols`、每列方法名（含 citation）、`content_type`
- **可默认**：`aspect_ratio`（4:3）、`row_labels_enabled`（true）、`caption_enabled`（true）
- **可随机**：列间 gap 精确像素、字体大小（在合理范围内）

### 自动补全策略

- 用户给 "我有 4 个方法 + ours" → 自动加上 Input 列（成为 5 列：Input / M1 / M2 / M3 / M4 / Ours，共 6 列）
- 用户没给 row labels → 默认用 "Sample 1, 2, 3, ..." 或反问是否要分难易度
- 用户没给 citation → 提示 "建议加 [n] 引用占位" 而不是擅自编造
- 用户说 "ablation study" → 列名改为 "w/o A", "w/o B", "Full" 等消融变体
- 用户说 "需要 zoom-in" → 启用 `zoom_in_enabled` 并提示需要标 region 坐标

## 变体 1：纯文本 NLP qualitative 对比

```json
{
  "type": "NLP qualitative comparison grid",
  "modify": {
    "content_type": "text_snippet",
    "cell_aspect": "tall rectangle (e.g. 2:3 portrait)",
    "cell_styling": "monospace font in cell, black text on white, with key tokens highlighted in colored boxes",
    "row_labels": "input prompt / question 显示在每一行最左",
    "use_case": "对比多个 LLM / 翻译 / summarization 输出"
  }
}
```

适用：NLP 论文生成结果对比、机器翻译质量对比。

## 变体 2：分割 mask 多列对比（含彩色 overlay）

```json
{
  "type": "Segmentation mask comparison grid",
  "modify": {
    "content_type": "segmentation_mask",
    "cell_styling": "RGB image base + 半透明 mask 叠加；每类颜色一致；GT 列与 Ours 列容易对比",
    "extras": "在 cells 下方可加 'mIoU: 0.78' 等定量指标小字",
    "color_legend": "图右下角附小图例：颜色 → 类别名"
  }
}
```

适用：语义分割、实例分割、医学影像分割论文。

## 变体 3：Diffusion / 生成模型 prompt × method 矩阵

```json
{
  "type": "Generation prompt × method matrix",
  "modify": {
    "rows": "different text prompts (left labels show prompt text)",
    "cols": "different generation methods or different sampling steps",
    "cell_content": "generated images, all from same prompt across the row",
    "extras": "可在 ours 列加 '↑ +0.3 CLIP score' 小标"
  }
}
```

适用：扩散模型、文本到图像生成、图像编辑方法对比。

## 避免事项

- 单元格大小不一致 → 完全失去对比意义
- 缺 citation → 同行评审会扣分
- Ours 列没有标记 → 读者不知道哪个是你的
- 同一行的样本不一致（这一行第一列是猫，第二列是狗）→ 对比不成立
- 添加渐变 / 阴影 / 圆角过大 → 不像论文
- 用 emoji 或 cartoon 装饰 → 严重不专业
- 列数 > 6 → 论文双栏排版下看不清
- 没有 caption → 读者不知道这张图想说什么
- zoom-in 框位置在不同 cell 不一致 → 对比不公平
