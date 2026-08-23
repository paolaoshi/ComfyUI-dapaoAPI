# Graphical Abstract / 图形摘要模板

本文件用于生成「期刊投稿 Graphical Abstract / 论文图形摘要 / 投稿封面图」：

- 期刊投稿要求附带的 Graphical Abstract
- 论文一图概览（"一图讲清主贡献"）
- 答辩首页 / 组会汇报首页里的研究亮点图

特征：

- 极简、紧凑、4 部分核心叙事（问题 → 方法 → 关键过程 → 结果）
- 横向左→右 或 中心展开布局
- 白底、低饱和工程色、≤3 主色，**像高质量期刊图形摘要，绝不像营销海报**
- 文字精炼到短语，禁止段落式说明

## 适用范围

- Elsevier / ACS / Wiley / Springer / IEEE 等期刊投稿要求的 Graphical Abstract
- arXiv / 预印本 README 顶部的"研究一图"
- 论文 supplementary 或 highlight figure
- 答辩 / 汇报"研究亮点"页

## 何时使用

- 用户提到「graphical abstract / 图形摘要 / 投稿摘要图 / 一图讲清 / highlight figure」
- 用户希望视觉「期刊封面级摘要图，简洁克制学术风」
- 用户已能用 1-2 句话讲清"这篇论文做了什么、得到了什么"

不要使用：

- 用户要的是「方法 pipeline 总览」 → 用 `academic-figures/method-pipeline-overview.md`
- 用户要的是「开题 / 答辩首页总览图」 → 用 `academic-figures/research-overview-poster.md`
- 用户要的是「机制 / 机理图」 → 用 `academic-figures/mechanism-diagram.md`
- 用户要的是「营销 / 品牌 / 杂志封面感」 → 用 `poster-and-campaigns/editorial-cover.md`

## 缺失信息优先提问顺序

1. 研究主题（一句话；写在标题或图注里）
2. 目标期刊或目标场景（决定纵横比 + 主色调；不同期刊偏好不同）
3. 4 个核心要素：研究问题 / 方法或系统 / 关键过程或机制 / 主要结果
4. 是否有"研究对象"的简化示意（颗粒 / 分子 / 器件 / 流程）
5. 标签语言（中文 / 英文 / 双语；多数期刊要求英文）
6. 比例（默认横向 16:9 / 2:1；部分期刊要求方形 1:1，要先确认）

## 主模板：横向 4 段式 Graphical Abstract

📖 描述

整张图横向流动：从最左边的「研究问题 / 研究对象」开始，依次到「方法 / 系统」、「关键过程 / 机制」、「主要结果」。四个区域比例均匀，文字精炼到短语，视觉层级清晰，整体像高质量工程类期刊摘要图。

📝 提示词

```json
{
  "type": "学术期刊图形摘要（Graphical Abstract）",
  "goal": "生成一张可直接用于期刊投稿的 Graphical Abstract，要求极简、白底、工程化克制配色、几秒内可读、绝无营销海报感",
  "canvas": {
    "aspect_ratio": "{argument name=\"aspect_ratio\" default=\"2:1\"}",
    "background": "pure white #FFFFFF",
    "outer_padding": "60px around the diagram",
    "render_quality": "vector-clean look, anti-aliased edges, sharp text, suitable for grayscale print"
  },
  "title_block": {
    "enabled": "{argument name=\"title_block_enabled\" default=\"false\"}",
    "title": "{argument name=\"title\" default=\"\"}",
    "rule": "most journals do not allow titles inside the graphical abstract; enable only when user explicitly requested a title"
  },
  "sections": [
    {
      "id": "P1",
      "role": "Problem",
      "label": "{argument name=\"problem_label\" default=\"Research Problem\"}",
      "summary": "{argument name=\"problem_summary\" default=\"a short phrase stating the gap, e.g. 'unstable combustion under variable moisture'\"}",
      "depiction": "{argument name=\"problem_depiction\" default=\"a minimal line-art sketch of the studied object or scenario\"}"
    },
    {
      "id": "P2",
      "role": "Method",
      "label": "{argument name=\"method_label\" default=\"Method\"}",
      "summary": "{argument name=\"method_summary\" default=\"a short phrase, e.g. 'thermogravimetric + kinetics analysis'\"}",
      "depiction": "{argument name=\"method_depiction\" default=\"a minimal schematic of the analytical or experimental setup\"}"
    },
    {
      "id": "P3",
      "role": "Process",
      "label": "{argument name=\"process_label\" default=\"Key Mechanism\"}",
      "summary": "{argument name=\"process_summary\" default=\"a short phrase, e.g. 'two-stage volatile combustion'\"}",
      "depiction": "{argument name=\"process_depiction\" default=\"a small mechanism strip with 2-3 sub-steps, line-art style\"}"
    },
    {
      "id": "P4",
      "role": "Result",
      "label": "{argument name=\"result_label\" default=\"Outcome\"}",
      "summary": "{argument name=\"result_summary\" default=\"a short phrase, e.g. 'optimized excess-air ratio reduces NOx by ~X%'\"}",
      "depiction": "{argument name=\"result_depiction\" default=\"a minimal qualitative chart sketch (no fabricated numbers) or a result icon (gauge / bar)\"}"
    }
  ],
  "section_block_style": {
    "shape": "implicit columns separated by generous whitespace, NOT four heavy rectangles in a row",
    "header_text": "section label in bold sans-serif, 12-13pt, top-aligned",
    "summary_text": "single phrase, 10pt regular, max 2 lines, no period",
    "depiction_size": "around 35-50% of column height, vertically centered"
  },
  "connectors": {
    "style": "thin arrows (1.2px) with simple triangle arrowheads, dark gray #334155, between adjacent sections only",
    "rule": "no crossing, no curved decorative arcs; arrows convey 'leads to' / 'analyzed by' relationships",
    "label_arrows": "false by default; only add label when the relationship is non-trivial"
  },
  "color_palette": {
    "rule": "≤ 3 main colors total, drawn from a low-saturation engineering set: deep blue #1E3A8A / slate blue #3B82F6 / charcoal #1F2937; allow ONE low-saturation accent (e.g. amber #F59E0B for a heat / risk highlight) only if the user signaled a thermal or risk emphasis",
    "must_print_grayscale_readable": true
  },
  "typography": {
    "language": "{argument name=\"language\" default=\"english\"}",
    "rule": "english → Inter / Helvetica / Arial; chinese → PingFang SC / Source Han Sans; bilingual → english as primary, chinese as smaller secondary line",
    "consistency": "all section headers identical size; all summaries identical size; never mix serif and sans-serif"
  },
  "constraints": {
    "must_keep": [
      "all four sections visually equal-weight, no section dominates",
      "white background, no gradient, no decorative pattern, no photographic background",
      "language matches the target journal (default english)",
      "summaries are short phrases, never full sentences with periods",
      "the figure must look like it could appear on an Elsevier / ACS / IEEE table of contents page",
      "every numerical claim must come from the user; if absent, render qualitatively"
    ],
    "avoid": [
      "marketing-poster aesthetics, brand campaign aesthetics, magazine cover aesthetics",
      "3D effects, drop shadows, gradients, glossy fills, lens flare, motion blur",
      "exaggerated flames, smoke, sparks (even when the topic is combustion)",
      "cartoon mascots, emoji, decorative icons, hand-drawn wobble",
      "stock-photo-style realistic backgrounds",
      "fabricated numbers, percentages, equations, or chart data not provided by the user",
      "saturated colors (no neon, no vivid), more than 3 main colors",
      "watermarks, copyright stamps, vendor logos"
    ]
  }
}
```

### 参数策略

- **必问**：4 个 `*_summary`（问题 / 方法 / 关键过程 / 结果）至少能给出短语
- **可默认**：`aspect_ratio`（2:1）、`background`（白色）、`color_palette`（深蓝/灰蓝/黑灰）
- **可随机**：每个 section 的 `*_depiction` 具体造型（用户给了对象/方法名时可推断；否则反问）

### 自动补全策略

- 用户只给主题但没给 4 段 → 反问 4 个 summary，**禁止编造研究内容**
- 用户给了定性贡献但没数 → 用 `qualitatively shows` / `consistently reduces` 这类无数字表达
- 用户给了数（如"NOx 降低 18%"）→ 直接写 `~18%`，不要伪造其他指标
- 用户说"中文期刊 / 中文摘要图" → 切换中文 + 字体 PingFang / 思源黑

## 变体 1：中心展开式（Hub-and-spoke）

```json
{
  "type": "中心展开式 Graphical Abstract",
  "modify": {
    "layout": "中心放置研究对象 / 核心系统的简化示意，向外辐射出 3-4 个扇区，每个扇区代表一个核心要素（问题、方法、机制、结果之一）",
    "rule": "扇区在视觉上等权，使用细线条分隔；中央对象占画面 30-40%",
    "use_case": "适合系统型研究、平台型研究，或难以线性叙事的多模态贡献"
  }
}
```

适用：综合性研究、系统性贡献（如新平台、新框架）。

## 变体 2：方形 1:1（部分期刊要求）

```json
{
  "type": "方形 Graphical Abstract",
  "modify": {
    "aspect_ratio": "1:1",
    "layout": "2×2 网格，左上 = 问题 / 对象，右上 = 方法，左下 = 关键过程，右下 = 结果",
    "rule": "四象限严格等大、对齐；象限间留出统一间距；箭头沿 Z 字型走 P1 → P2 → P3 → P4",
    "use_case": "ACS / Wiley 等部分期刊要求方形 Graphical Abstract"
  }
}
```

适用：投稿要求方形比例的期刊。

## 变体 3：竖版（社交媒体 / 预印本卡片）

```json
{
  "type": "竖版 Graphical Abstract",
  "modify": {
    "aspect_ratio": "3:4",
    "layout": "上 → 下 四段式：Problem → Method → Mechanism → Outcome",
    "rule": "宽度紧凑，每段保留呼吸空间；适合手机端或 Twitter / LinkedIn 卡片预览",
    "use_case": "用于社交媒体推广预印本、Lab 主页 highlight 卡"
  }
}
```

适用：投稿之外的科研宣传，但仍保持学术克制风格。

## 避免事项

- 把 Graphical Abstract 画成"全文压缩版"——塞进所有方法步骤、所有公式、所有结果
- 用任何形式的渐变 / 玻璃质感 / 光晕 / 3D → 立刻像营销图
- 中英文标签随意混用（除非显式要求双语）
- 在没有真实数据时画出带具体数值的柱图 / 折线（**严格禁止虚构数据**；只能定性展示）
- 用饱和 brand 色或霓虹色——期刊摘要图应保持低饱和工程色
- 把研究对象画成超现实 3D 渲染（学术风需要的是简化线稿）
- 加期刊 logo / 水印 / "submitted to ..." 等标签
