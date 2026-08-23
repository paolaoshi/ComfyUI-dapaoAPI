# 机理示意图模板

本文件用于生成「学术机理示意图 / 因果链路 / 转化路径 / 演化机制图」：

- 论文正文里的机制 / 机理分析图
- 反应 / 转化 / 退化路径图
- 因果链路 / 多阶段演化图
- 答辩 PPT 的机制说明页

特征：

- 中心对象 + 多阶段转化路径 + 结果区域
- 阶段化标注（干燥 → 热解 → 燃烧 → 氧化 → 排放，或类似的因果序列）
- 白底 + 工程化低饱和配色（深蓝 / 灰蓝 / 黑灰为主，可加 ≤1 种低饱和暖色作为高温/风险强调）
- 学术克制风格，**绝对不是营销插画或科普海报**

## 适用范围

- 燃烧 / 化学反应 / 催化 / 退化 / 老化 / 腐蚀 / 衰减 等机制示意
- 生物 / 医药 / 药物作用 / 分子互作 等通路图（学术风，非科普插画）
- 材料相变 / 损伤演化 / 失效路径
- 因果链分析图 / 演化路径图

## 何时使用

- 用户提到「机理 / 机制 / 反应路径 / 转化 / 演化 / 因果 / 通路 / 失效路径」
- 用户希望视觉「论文里的机制图，不是科普插画也不是营销图」
- 用户已能给出阶段顺序或转化关系

不要使用：

- 用户要的是「方法 pipeline / 系统总览」 → 用 `academic-figures/method-pipeline-overview.md`
- 用户要的是「实验装置 / 测试系统」 → 用 `academic-figures/scientific-schematic.md`
- 用户要的是「业务流程 / 决策图」 → 用 `technical-diagrams/flowchart-decision.md`
- 用户要的是「教学步骤、温暖插画感」 → 用 `infographics/step-by-step-infographic.md`

## 缺失信息优先提问顺序

1. 机制 / 现象总名称（写在标题或图注里）
2. 中心研究对象是什么（颗粒 / 分子 / 器件 / 组织 / 反应体系）
3. 阶段顺序（建议 3-6 个阶段；超过 6 个考虑分组）
4. 每个阶段：阶段名 + 主导过程的极简描述（短语化）
5. 是否有分支 / 平行路径 / 反馈环
6. 是否需要标注高温区 / 风险区 / 关键反应区等局部强调
7. 标签语言（中文 / 英文 / 双语；论文图通常英文）
8. 比例（默认横向 16:9；机制图也常见 4:3）

## 主模板：中心对象 + 多阶段转化 + 结果区

📖 描述

中心是研究对象的简化示意（颗粒 / 分子结构 / 器件 / 反应体系），周围以"阶段化转化路径"展开：从初始态经过若干中间机制阶段到达最终结果区。所有连接以学术克制风格的箭头表达，禁止戏剧化效果（无火焰、无浓烟、无炫光）。

📝 提示词

```json
{
  "type": "学术机理示意图（mechanism / pathway figure）",
  "goal": "生成一张可直接放进工程类或自然科学论文正文的机制示意图，强调因果路径清晰、学术克制、可单色印刷可读",
  "canvas": {
    "aspect_ratio": "{argument name=\"aspect_ratio\" default=\"16:9\"}",
    "background": "pure white #FFFFFF",
    "outer_padding": "60px around the diagram",
    "render_quality": "vector-clean look, anti-aliased edges, sharp text"
  },
  "title_caption": {
    "figure_label": "{argument name=\"figure_label\" default=\"Figure X.\"}",
    "caption": "{argument name=\"caption\" default=\"Schematic of the proposed mechanism.\"}",
    "position": "bottom-center, italic serif or compact sans-serif, smaller font size"
  },
  "central_object": {
    "label": "{argument name=\"object_label\" default=\"Biomass particle\"}",
    "depiction": "{argument name=\"object_depiction\" default=\"a simplified cross-sectional sketch of a porous biomass particle, line-art style, no photo realism\"}",
    "position": "horizontally centered, occupying roughly 25-35% of canvas width",
    "style": "thin line-art / engineering schematic, no 3D, no shading, no hyperreal texture"
  },
  "stages": {
    "count": "{argument name=\"stage_count\" default=\"5\"}",
    "items": [
      {
        "id": "M1",
        "name": "{argument name=\"stage_1_name\" default=\"Drying\"}",
        "summary": "{argument name=\"stage_1_summary\" default=\"moisture evaporation under heating\"}",
        "highlight": "{argument name=\"stage_1_highlight\" default=\"none\"}"
      },
      {
        "id": "M2",
        "name": "{argument name=\"stage_2_name\" default=\"Pyrolysis\"}",
        "summary": "{argument name=\"stage_2_summary\" default=\"thermal decomposition releasing volatiles\"}",
        "highlight": "{argument name=\"stage_2_highlight\" default=\"reaction zone\"}"
      },
      {
        "id": "M3",
        "name": "{argument name=\"stage_3_name\" default=\"Volatile Combustion\"}",
        "summary": "{argument name=\"stage_3_summary\" default=\"gas-phase combustion of released volatiles\"}",
        "highlight": "{argument name=\"stage_3_highlight\" default=\"high-temperature region\"}"
      },
      {
        "id": "M4",
        "name": "{argument name=\"stage_4_name\" default=\"Char Oxidation\"}",
        "summary": "{argument name=\"stage_4_summary\" default=\"surface oxidation of the remaining char\"}",
        "highlight": "{argument name=\"stage_4_highlight\" default=\"none\"}"
      },
      {
        "id": "M5",
        "name": "{argument name=\"stage_5_name\" default=\"Emission Formation\"}",
        "summary": "{argument name=\"stage_5_summary\" default=\"formation of NOx, CO, particulate matter\"}",
        "highlight": "{argument name=\"stage_5_highlight\" default=\"emission risk region\"}"
      }
    ]
  },
  "result_region": {
    "enabled": "{argument name=\"result_region_enabled\" default=\"true\"}",
    "label": "{argument name=\"result_region_label\" default=\"Outcome\"}",
    "items": "{argument name=\"result_region_items\" default=\"temperature distribution, combustion efficiency, emission characteristics\"}",
    "position": "rightmost block or bottom-right region, visually separated from stages but stylistically consistent"
  },
  "stage_block_style": {
    "shape": "rounded rectangle (corner radius ~6px) OR stage label + leader line directly attached to the central object",
    "size_per_stage": "consistent across all stages",
    "fill": "very light tint (e.g. #F1F5F9, #ECFEFF) — at most 2 different tints; use a low-saturation warm tint (e.g. #FEF3C7) only for stages whose 'highlight' is non-none",
    "border": "1.2px solid dark gray #334155",
    "title_text": "stage name in bold sans-serif (Helvetica / Inter / Arial / PingFang / Source Han Sans for CJK), 11-12pt",
    "summary_text": "single phrase, 9-10pt regular, no full sentence, no period"
  },
  "connectors": {
    "style": "thin arrows (1.2px) with simple triangle arrowheads, dark gray #334155",
    "rule": "connect stages in causal / temporal order, no crossing, no decorative curves; only label arrows when carrying a named quantity (e.g. 'heat flux', 'O2', 'volatiles')",
    "feedback_loop": {
      "enabled": "{argument name=\"feedback_loop\" default=\"false\"}",
      "rule": "if true, add one curved dashed arrow looping back, labeled e.g. 'self-propagating heat'"
    }
  },
  "highlight_strategy": {
    "rule": "for stages whose 'highlight' is non-none, apply ONLY a subtle low-saturation tint background (e.g. #FEF3C7 for high-temperature; #FEE2E2 for emission risk). NEVER use flames, smoke, glow, lens flare, or 3D heat-map effects",
    "max_highlighted_stages": 2
  },
  "constraints": {
    "must_keep": [
      "central object visually anchors the figure; stages radiate or flow outward in a stable reading order",
      "white background, no gradient, no decorative pattern",
      "color palette ≤ 3 main colors, must remain readable in grayscale print",
      "only sans-serif typography, no script / handwritten / display fonts",
      "stage labels are short phrases, never full sentences",
      "the figure must look like it came from a journal article, not a popular-science illustration",
      "all arrows aligned, no crossings unless the mechanism genuinely requires it"
    ],
    "avoid": [
      "exaggerated flames, smoke, sparks, glow, lens flare, motion blur",
      "3D rendering, metallic highlights, glossy fills",
      "cartoon mascots, emoji, decorative icons, hand-drawn wobble",
      "photo-realistic photography of equipment, products, or scenery",
      "marketing poster aesthetics, magazine cover aesthetics",
      "fabricated numbers, equations, or chemical formulas not provided by the user",
      "saturated brand-style colors (no neon, no vivid)",
      "watermarks, copyright stamps, vendor logos"
    ]
  }
}
```

### 参数策略

- **必问**：`object_label` / `object_depiction`、阶段名、阶段顺序
- **可默认**：`aspect_ratio`（16:9）、`background`（白色）、`figure_label` / `caption`、配色 tint
- **可随机**：每个 stage 的 `summary` 措辞（用户给了大意可学术化润色）、`highlight` 是否启用（无明确说明时默认 none）

### 自动补全策略

- 用户给出现象名 + 阶段数但没说每阶段细节 → 反问，**禁止编造不存在的物理 / 化学过程**
- 用户给出阶段名但没给摘要 → 用学术化短语补全（保持 ≤6 词）
- 用户没说有没有反馈环 → 默认 `feedback_loop: false`
- 用户说"中文论文 / 答辩" → 切换标签为中文 + 字体 PingFang / 思源黑

## 变体 1：左 → 中 → 右 三段式因果链

```json
{
  "type": "三段式因果链机制图",
  "modify": {
    "layout": "左侧 = 初始条件 / 触发因素；中间 = 多阶段转化机制；右侧 = 最终结果 / 表征",
    "rule": "三段之间用粗一些的分隔留白（视觉分组），但保持统一描边和字体；左右两侧文字精炼到 ≤4 项",
    "use_case": "需要清晰区分'起因 → 过程 → 结果'的机制图，例如'生物质燃烧 → 多阶段反应 → 排放与残炭'"
  }
}
```

适用：燃烧 / 反应工程、退化老化、损伤演化、临床因果通路（学术风）。

## 变体 2：循环 / 自激发机制

```json
{
  "type": "循环自激发机制图",
  "modify": {
    "layout": "阶段排成环形，箭头沿环顺时针方向；中央写出循环驱动力或关键中间产物",
    "annotation": "环上选 1-2 个箭头加 dashed 样式标注 'positive feedback' / 'self-propagating'",
    "use_case": "正反馈机制、自催化反应、慢性退化循环"
  }
}
```

适用：自催化、链式反应、热失控、慢性炎症通路。

## 变体 3：多分支竞争路径

```json
{
  "type": "多分支竞争机制图",
  "modify": {
    "layout": "中心对象向外分出 2-3 条平行路径，每条代表一种竞争性机制；末端各自连到不同的结果区",
    "annotation": "每条路径起点处标注控制条件（temperature / O2 partial pressure / pH 等）",
    "use_case": "需要表达'相同前体在不同条件下走不同机制'的对比型机理图"
  }
}
```

适用：路径选择性反应、相分离、不同温度区间下的反应主导机制。

## 避免事项

- 用渲染感火焰 / 浓烟 / 爆炸 / 炫光来"装专业" → 立刻沦为营销插画
- 阶段块大小不一、字号混乱、字体混用衬线 + 无衬线
- 用 emoji 或卡通图标当阶段图示
- 用饱和 / 霓虹 / 渐变背景代替克制工程色
- 把不存在的化学方程、物理常数、温度数值塞进图里（**严格禁止虚构数据**）
- 把"机制示意图"画成完整设备剖视图（应该用 `scientific-schematic.md`）
- 把对比 / 多工况结果（应该用 `multi-condition-comparison.md`）混进机制图
