# 多工况 / 多条件结果对比图模板

本文件用于生成「同一研究对象在不同工况 / 条件 / 组别下的多面板结果对比图」：

- 不同温度 / 压力 / 浓度 / 配比 / 时间下的实验或仿真结果
- 不同处理组 / 对照组 / 工艺方案的并列结果
- 多面板 (a)(b)(c)(d) 形式的论文 result figure

特征：

- 2×2 / 1×3 / 1×4 等统一网格布局
- **所有 panel 严格统一**：相同尺寸、相同色彩逻辑、相同图例、相同字体层级、相同边距
- 白底、低饱和工程色，论文结果图风格
- **无真实数据时只做定性表达，禁止虚构数值 / 等值线 / 色标范围**

## 适用范围

- 工程 / 物理 / 化学 / 能源 / 材料 / 环境方向的多工况结果对比
- 燃烧 / 流场 / 温度场 / 应力场 / 浓度场 等场图对比
- 不同处理组 / 不同剂量 / 不同时间点 的实验对照
- 同一指标在多个 condition 下的多面板可视化

## 何时使用

- 用户提到「多工况 / 多条件 / 不同 X 下的对比 / panel (a)(b)(c)(d) / 结果对比图」
- 用户希望视觉「论文 result figure，不是营销信息图」
- 比较的是**同一对象在不同条件下的同类结果**

不要使用：

- 用户要的是「不同方法在同一样本上的输出对比」（行=样本，列=方法） → 用 `academic-figures/qualitative-comparison-grid.md`
- 用户要的是「单个 publication-ready 图表」（bar / line / scatter） → 用 `academic-figures/publication-chart.md`
- 用户要的是「营销 / 信息图风格的二元对比」 → 用 `infographics/comparison-infographic.md`

## 缺失信息优先提问顺序

1. 比较对象是什么（同一现象 / 同一指标）
2. 比较的是哪些工况 / 条件（建议 2-6 个；超过 6 个考虑分两张图）
3. 每个 panel 显示的是什么（场图 / 折线 / 柱图 / 等值线 / 显微图）—— 必须**所有 panel 同类型**
4. 是否有真实数据（**关键**：决定是定性图还是定量图）
5. 网格布局（2×2 / 1×3 / 1×4 / 2×3）
6. 标签语言（中文 / 英文 / 双语）
7. 共享图例 / 共享色标（强烈建议共享）

## 主模板：N panel 多工况对比（统一规格）

📖 描述

整张图按统一网格分割成 N 个 panel，每个 panel 展示同一类结果在不同工况下的表现。所有 panel 共享色标 / 图例 / 字体层级 / 边距。子图标记为 (a)(b)(c)(d)，标签简短克制。**绝对不允许每个 panel 自成一套风格。**

📝 提示词

```json
{
  "type": "学术多工况结果对比图（multi-condition comparison figure）",
  "goal": "生成一张可直接放进论文 results 章节的多面板对比图，要求所有 panel 严格统一、白底、低饱和工程色、可单色印刷可读",
  "canvas": {
    "aspect_ratio": "{argument name=\"aspect_ratio\" default=\"4:3\"}",
    "background": "pure white #FFFFFF",
    "outer_padding": "50px around the grid",
    "inter_panel_gap": "16-20px, identical horizontal and vertical",
    "render_quality": "vector-clean look, anti-aliased, sharp text"
  },
  "title_caption": {
    "figure_label": "{argument name=\"figure_label\" default=\"Figure X.\"}",
    "caption": "{argument name=\"caption\" default=\"Comparison of results under varying conditions.\"}",
    "position": "bottom-center, italic serif or compact sans-serif, smaller font size"
  },
  "grid_layout": {
    "rows": "{argument name=\"rows\" default=\"2\"}",
    "cols": "{argument name=\"cols\" default=\"2\"}",
    "panel_count": "{argument name=\"panel_count\" default=\"4\"}",
    "rule": "rows × cols == panel_count; all panels identical size; consistent vertical and horizontal alignment"
  },
  "panels": {
    "panel_type": "{argument name=\"panel_type\" default=\"contour-field\"}",
    "panel_type_options": "contour-field | line-chart | bar-chart | heatmap | micrograph | flow-field | bubble-chart",
    "rule": "ALL panels MUST share the same panel_type; never mix bar with line within the same comparison figure",
    "items": [
      {
        "id": "(a)",
        "condition_label": "{argument name=\"panel_a_label\" default=\"Condition A\"}",
        "condition_detail": "{argument name=\"panel_a_detail\" default=\"e.g. excess-air ratio λ = 1.0\"}"
      },
      {
        "id": "(b)",
        "condition_label": "{argument name=\"panel_b_label\" default=\"Condition B\"}",
        "condition_detail": "{argument name=\"panel_b_detail\" default=\"e.g. excess-air ratio λ = 1.2\"}"
      },
      {
        "id": "(c)",
        "condition_label": "{argument name=\"panel_c_label\" default=\"Condition C\"}",
        "condition_detail": "{argument name=\"panel_c_detail\" default=\"e.g. excess-air ratio λ = 1.4\"}"
      },
      {
        "id": "(d)",
        "condition_label": "{argument name=\"panel_d_label\" default=\"Condition D\"}",
        "condition_detail": "{argument name=\"panel_d_detail\" default=\"e.g. excess-air ratio λ = 1.6\"}"
      }
    ]
  },
  "panel_style": {
    "frame": "thin border 1px #1F2937 OR clean axis lines without outer frame, applied identically to all panels",
    "label_position": "(a) (b) (c) (d) at top-left of each panel, bold sans-serif, 11pt",
    "condition_label_position": "centered above each panel OR inside each panel top-right, identical position across all panels",
    "axis_labels": "shared if possible; if shown, identical font size, identical tick density across panels",
    "internal_titles": "AVOID per-panel decorative titles; rely on (a)(b)(c)(d) + condition label only"
  },
  "shared_legend": {
    "enabled": "{argument name=\"shared_legend_enabled\" default=\"true\"}",
    "position": "{argument name=\"shared_legend_position\" default=\"right-of-grid\"}",
    "rule": "single legend / colorbar shared across ALL panels; never give each panel its own legend with different range",
    "colorbar_range": "{argument name=\"colorbar_range\" default=\"qualitative-low-to-high\"}",
    "colorbar_range_rule": "if user provided a numerical range, use it; otherwise render as a qualitative gradient labeled 'low → high' with NO fabricated numerical ticks"
  },
  "color_logic": {
    "rule": "≤ 3 main colors total; if a sequential colormap is used, choose a perceptually uniform low-saturation engineering colormap (e.g. viridis-like, blue-to-orange, gray-to-deep-blue); apply the SAME colormap and SAME range to every panel",
    "must_print_grayscale_readable": true
  },
  "data_authenticity": {
    "user_provided_real_data": "{argument name=\"has_real_data\" default=\"false\"}",
    "rule_when_false": "render the panels as QUALITATIVE schematics: smooth gradient fields, generic shapes, no numerical tick labels on the colorbar, no specific values in axes; explicitly avoid the visual impression of a real dataset",
    "rule_when_true": "use the user-provided values; never extrapolate, interpolate, or invent additional values"
  },
  "constraints": {
    "must_keep": [
      "all panels identical size, identical aspect, identical position scheme",
      "shared color logic and shared legend across all panels",
      "white background, no gradient backdrop, no decorative pattern",
      "(a)(b)(c)(d) labels in identical position and identical style across all panels",
      "only sans-serif typography, identical font family across all panels",
      "the figure should look like it came from a results section of an engineering or science journal"
    ],
    "avoid": [
      "different colormap or different color range per panel",
      "different chart type per panel (e.g. mixing bar and line)",
      "decorative panel titles, hero panel that visually dominates the rest",
      "saturated brand colors, neon, vivid gradients",
      "3D effects, drop shadows, glossy fills, lens flare",
      "fabricated numerical tick values, fabricated colorbar ranges, fabricated isolines",
      "marketing-poster aesthetics, infographic-collage aesthetics",
      "watermarks, copyright stamps"
    ]
  }
}
```

### 参数策略

- **必问**：`panel_count`、`panel_type`（所有 panel 同一类型）、`has_real_data`
- **可默认**：`aspect_ratio`、`grid_layout`（2×2 是最常见）、`shared_legend_enabled`（true）
- **可随机**：每个 condition 的 `*_detail` 措辞（用户给了控制变量名时可学术化）

### 自动补全策略

- 用户没说有没有真实数据 → **必须先确认**：`has_real_data` = false 时全图走定性渲染
- 用户给了不同 condition 但没说每 panel 的具体取值 → 在 condition_detail 里用占位短语（如 `λ = X1`），**不要编造数字**
- 用户给了 panel 数但 row × col 不匹配 → 自动选最接近正方的网格（2×2 / 2×3 / 3×3）
- 用户说"中文论文 / 答辩" → 切换标签为中文 + 字体 PingFang / 思源黑

## 变体 1：横向 1×N（适合窄 panel 比较）

```json
{
  "type": "横向 1×N 多工况对比",
  "modify": {
    "layout": "rows = 1, cols = N（建议 N ≤ 4）",
    "use_case": "panel 内部是窄柱图 / 窄折线，更适合横向铺开；或论文双栏排版需要横向单行"
  }
}
```

适用：单栏 / 双栏论文格式中的横向比较。

## 变体 2：行列双因子矩阵（M×N）

```json
{
  "type": "双因子矩阵对比",
  "modify": {
    "layout": "rows = M（一种因子的不同水平），cols = N（另一种因子的不同水平）",
    "rule": "顶部一行写列因子标签，最左一列写行因子标签；panel 内部样式严格统一",
    "use_case": "需要同时变化两个独立变量（如温度 × 含水率，或时间 × 浓度）"
  }
}
```

适用：双因子实验设计的结果展示，正交试验结果可视化。

## 变体 3：定性场图渲染（无真实数据）

```json
{
  "type": "定性场图多工况对比",
  "modify": {
    "panel_type": "contour-field",
    "data_authenticity": {
      "user_provided_real_data": false,
      "rule": "render smooth qualitative gradient fields with NO numerical tick labels and NO specific isoline values; the colorbar shows 'low → high' as a qualitative scale only",
      "intent": "visually communicate 'higher temperature in panel (b)' without claiming any specific value"
    },
    "use_case": "答辩 / 开题阶段尚未拿到数据，需要先讲清研究思路时使用"
  }
}
```

适用：示意性结果对比、方法论说明阶段。

## 避免事项

- 给每个 panel 用不同 colormap / 不同 range → 直接破坏可比性
- 在没有真实数据时画出带具体数值的等值线 / 色标刻度（**严格禁止虚构数据**）
- 让某一 panel 视觉权重明显大于其他 panel（不允许"主图 + 辅图"的结构）
- 在每个 panel 加独立的装饰性标题
- 把不同类型的图（bar / line / contour）混排在同一对比图里
- 使用饱和 brand 色或霓虹渐变
- 把"对比方法"的逻辑（行=样本×列=方法）误用到本模板（请改用 `qualitative-comparison-grid.md`）
- 加水印 / 期刊 logo / 设备品牌标
