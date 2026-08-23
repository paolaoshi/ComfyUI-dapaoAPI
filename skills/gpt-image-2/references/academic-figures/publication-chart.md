# Publication-Ready 数据图表模板

本文件用于生成"论文 / 报告里出现的标准数据图表"：

- Bar chart / grouped bar chart（消融实验、方法对比）
- Line chart / 训练曲线（loss / accuracy 随 epoch）
- Scatter plot（性能-效率 trade-off）
- Box plot / Violin plot（统计分布）
- Heatmap（confusion matrix / attention map / 相关性矩阵）

特征：

- matplotlib / seaborn / R ggplot2 出版物风
- 含坐标轴 + 标签 + 单位 + 图例 + 误差棒 + 显著性标记
- 字体 ≥ 10pt（确保打印可读）
- 配色克制（≤ 6 色），可单色印刷
- 网格线极淡或无

> ⚠️ 重要免责声明：**本模板生成的是"出版级图表的视觉呈现"，不是真实数据可视化**。GPT Image 2 不能保证坐标和数据的精确对应。
>
> - 如果你需要"展示一张论文图表的样子" / "做封面 / hero 配图" → 用本模板
> - 如果你需要"用真实数据生成可发表的图表" → 请用 matplotlib / seaborn / ggplot2 / Plotly

## 适用范围

- 论文方法对比 chart 的视觉示例
- 教学 slide 中"看一眼这个图就懂"的演示图
- Blog / 公众号配图 — "我们的方法在这个 chart 上表现"
- 投资人 deck 中的"数据 mock"
- 演示用、可视化教学用的图表

## 何时使用

- 用户提到 "publication chart / matplotlib 风 / seaborn 风 / 论文图表 / bar chart / line chart / scatter / heatmap / confusion matrix"
- 用户希望「白底、克制、可单色、像 NeurIPS 论文那种图表」
- 用户**明确知道**这只是视觉呈现，不依赖坐标精度

不要使用：

- 用户要的是「真实数据可视化产出」 → 推荐 matplotlib / seaborn / Plotly
- 用户要的是「KPI 仪表盘 / 数据回顾」 → 用 `infographics/kpi-dashboard-infographic.md`
- 用户要的是「商业 PPT 数据页」 → 用 `slides-and-visual-docs/visual-report-page.md`
- 用户要的是「手绘风信息图」 → 用 `infographics/hand-drawn-infographic.md`

## 缺失信息优先提问顺序

1. 图表类型（bar / line / scatter / box / violin / heatmap / pie）
2. 主题（"我们方法在 ImageNet 上的 accuracy vs baselines"）
3. X 轴和 Y 轴名称 + 单位
4. 数据系列数量（单一系列 / 多系列）
5. 是否有误差棒、显著性标记 *
6. 配色基调（学术克制 / 强调对比 / 黑白单色）
7. 图标题 + caption（论文 figure 一般有 caption）

## 主模板：Publication-Ready Bar Chart（默认）

📖 描述

整张图是一张标准学术 bar chart：横轴为方法 / 类别，纵轴为指标，多个方法对比，含误差棒、显著性 *、图例。整体白底，sans-serif 字体，限定配色。

📝 提示词

```json
{
  "type": "Publication-Ready Bar Chart（学术出版级条形图）",
  "goal": "生成视觉呈现一张论文 / 报告中的 bar chart，要求白底、克制、专业、可单色印刷",
  "canvas": {
    "aspect_ratio": "{argument name=\"aspect_ratio\" default=\"4:3\"}",
    "background": "white #FFFFFF",
    "outer_padding": "60px"
  },
  "title": {
    "text": "{argument name=\"title\" default=\"Accuracy on ImageNet-1K\"}",
    "position": "top-center, sans-serif bold 13pt",
    "subtitle": "{argument name=\"subtitle\" default=\"\"}"
  },
  "axes": {
    "x_axis": {
      "label": "{argument name=\"x_label\" default=\"Method\"}",
      "categories": [
        "{argument name=\"cat1\" default=\"ResNet-50\"}",
        "{argument name=\"cat2\" default=\"ViT-B\"}",
        "{argument name=\"cat3\" default=\"Swin-B\"}",
        "{argument name=\"cat4\" default=\"ConvNeXt-B\"}",
        "{argument name=\"cat5\" default=\"Ours\"}"
      ],
      "tick_label_rotation": "0deg or 30deg if labels are long"
    },
    "y_axis": {
      "label": "{argument name=\"y_label\" default=\"Top-1 Accuracy (%)\"}",
      "range": "{argument name=\"y_range\" default=\"75 to 86\"}",
      "tick_format": "decimal or percent",
      "gridlines": "very faint horizontal gridlines (light gray dashed, low opacity)"
    }
  },
  "bars": {
    "style": "vertical bars, ~30-40% width of category slot, gap between bars",
    "color_rule": {
      "default": "use a single muted color for all baselines (e.g. slate blue #64748B), highlight 'Ours' bar in accent color (e.g. orange #D97706 or red #DC2626)",
      "alternative": "if comparing methods grouped by family, use 2-3 muted colors to encode family"
    },
    "value_labels": {
      "enabled": "{argument name=\"value_labels_enabled\" default=\"true\"}",
      "rule": "show numeric value above each bar, sans-serif 9pt bold, e.g. '82.3'"
    }
  },
  "error_bars": {
    "enabled": "{argument name=\"error_bars_enabled\" default=\"true\"}",
    "style": "thin black T-bar at top of each bar, ±std or ±95% CI",
    "annotation": "mention what the error represents in caption (e.g. 'error bars show ±1 std over 5 runs')"
  },
  "significance_markers": {
    "enabled": "{argument name=\"significance_enabled\" default=\"false\"}",
    "rule": "if true, draw thin horizontal brackets between compared bars, with * / ** / *** annotation above (p<0.05 / p<0.01 / p<0.001)"
  },
  "legend": {
    "enabled": "{argument name=\"legend_enabled\" default=\"false\"}",
    "rule": "only show legend if multiple colors / groups used; place top-right inside or outside the plot area",
    "items": ["Baselines", "Ours"]
  },
  "caption": {
    "enabled": "{argument name=\"caption_enabled\" default=\"true\"}",
    "label": "{argument name=\"figure_label\" default=\"Figure 3.\"}",
    "text": "{argument name=\"caption_text\" default=\"Top-1 accuracy on ImageNet-1K. Our method outperforms all baselines while using fewer parameters. Error bars show ±1 std over 5 runs.\"}",
    "style": "below the chart, italic serif or compact sans-serif, justified, smaller font"
  },
  "constraints": {
    "must_keep": [
      "white background, no gradient, no pattern fills",
      "sans-serif fonts only (Helvetica / Inter / Arial); axis tick labels ≥ 9pt, axis labels ≥ 11pt, title ≥ 13pt",
      "color palette ≤ 6 colors, must remain readable in grayscale",
      "all axes have labels and units",
      "no 3D bar effects, no perspective tilt",
      "if multiple bars per category, group them with consistent spacing",
      "Ours bar is visually distinguishable (color or annotation)"
    ],
    "avoid": [
      "rainbow colors / saturated palette",
      "3D extruded bars / pie charts (3D distorts perception)",
      "missing axis labels or units",
      "unreadable tick labels (too small or rotated awkwardly)",
      "decorative background images / textures",
      "emoji / cartoon icons inside or around bars",
      "value labels overlapping bars or each other",
      "random / irrelevant accent colors",
      "fake precision: don't render bar heights to imply real numbers — keep it clearly illustrative"
    ]
  }
}
```

### 参数策略

- **必问**：图表类型（如果不是 bar）、`title`、`x_label` / `y_label` / 单位、`categories`
- **可默认**：`aspect_ratio`（4:3）、`background`（白）、`error_bars_enabled`（true）、`value_labels_enabled`（true）、`legend_enabled`（false 单系列时）
- **可随机**：bar 宽度、tick 数量、网格线密度（在合理范围）

### 自动补全策略

- 用户给"我有 5 个方法的 accuracy 对比" → 自动用 default 5 categories，highlight 最后一个为 Ours
- 用户没指定 y_range → 推断（基于数值范围 ± 5%）
- 用户没说 error → 默认开启 error_bars（论文标准做法）
- 用户没说 significance → 默认关闭（除非是统计学论文）
- 用户说"不是 bar" → 切换到对应变体

## 变体 1：Line Chart（训练曲线 / 时间序列）

```json
{
  "type": "Publication-Ready Line Chart（学术出版级折线图）",
  "modify": {
    "x_axis_typical": "epoch / step / time / iteration",
    "y_axis_typical": "loss / accuracy / metric",
    "lines_count": "1-5 series, each a different muted color",
    "line_style": "solid 1.5px main line + optional shaded area (semi-transparent same color) for std band",
    "markers": "optional small markers at sparse intervals (circles / triangles), not on every point",
    "legend": "always enabled for multi-series, top-right or below",
    "rule_extra": "axes can be log-scale if data spans orders of magnitude (label as 'log scale')"
  }
}
```

适用：训练曲线、time series 趋势、ablation 随超参变化、scaling laws。

## 变体 2：Scatter Plot（trade-off 图）

```json
{
  "type": "Publication-Ready Scatter Plot（学术出版级散点图）",
  "modify": {
    "typical_use": "performance vs efficiency trade-off (e.g. accuracy vs FLOPs / latency / params)",
    "x_axis_typical": "compute / params / latency (often log scale)",
    "y_axis_typical": "accuracy / metric",
    "point_style": "filled circles, size encodes a third dimension (e.g. model size), color encodes a category (e.g. method family)",
    "label_each_point": "small text label next to each point with method name (no leader lines unless crowded)",
    "ours_emphasis": "Our method points are larger and use accent color + black border",
    "frontier_line": "optional: draw a Pareto frontier curve to show 'we push the frontier'"
  }
}
```

适用：性能-效率 trade-off、参数 vs 准确率、Pareto frontier。

## 变体 3：Heatmap（confusion matrix / attention map / 相关性）

```json
{
  "type": "Publication-Ready Heatmap（学术出版级热力图）",
  "modify": {
    "grid": "N × N（默认 5×5 至 10×10）",
    "color_map": "sequential — viridis / Blues / Reds / 灰阶；diverging（如相关矩阵）— RdBu_r 红蓝双向",
    "cell_annotation": "show numeric value inside each cell in monospace, color flips for readability on dark cells",
    "axes_label": "row labels = ground truth, column labels = predicted（confusion matrix 场景）",
    "colorbar": "right side vertical colorbar with label and ticks",
    "rule_extra": "always include colorbar; never use rainbow colormap for sequential data (jet 已被学界淘汰)"
  }
}
```

适用：confusion matrix、attention 权重可视化、相关性矩阵、ablation grid。

## 变体 4：Box Plot / Violin Plot（统计分布）

```json
{
  "type": "Publication-Ready Box / Violin Plot（学术出版级分布图）",
  "modify": {
    "typical_use": "compare distributions across methods / conditions / groups",
    "elements": "box (Q1, median, Q3) + whiskers (1.5 IQR) + outlier dots; violin 形状叠加显示密度",
    "median_line_emphasis": "median 线粗实线，颜色区分 group",
    "annotation": "可叠加 swarm / strip plot 显示每个数据点",
    "rule_extra": "如果用 violin，violin 内部仍画 box；不要纯 violin（损失中位数信息）"
  }
}
```

适用：实验重复结果分布、跨数据集 / 跨用户 / 跨条件分布对比。

## 避免事项

- 用 3D 柱 / 3D 饼 → 严重不专业
- 用彩虹 / jet colormap 表示连续值（学界已抛弃）
- 漏掉单位 / 漏掉坐标轴标签
- value 标签过小读不清
- 没有 caption 或 caption 没解释 error bar
- 把 4-5 个不相关 chart 拼一张（应该用 multi-panel figure 模板，每个 sub 图独立）
- 假装精确（暗示这是真数据但其实是 illustrative）
- 用花哨字体（Comic Sans / 手写体）
- 加水印 / 装饰背景
- 漏掉图例（多系列必须有）
- 多 series 但配色完全相同
- 漏掉 Ours 高亮（论文图通常要让 reviewer 一眼看出你的）
