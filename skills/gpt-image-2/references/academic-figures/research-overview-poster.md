# 开题 / 答辩 / 汇报研究总览图模板

本文件用于生成「开题答辩首页 / 论文汇报首页 / 组会引导页的研究总览图」：

- 硕博开题答辩首页的研究框架图
- 中期 / 终期答辩首页的总览图
- 组会 / 学术汇报 PPT 的引导页
- Lab 主页 / 课题介绍的研究总览

特征：

- 高层级、易读、适合 PPT 一页展示
- 5 个核心模块：背景 / 目标 / 研究模块 1 / 研究模块 2 / 预期结果
- 白底、低饱和工程色、≤3 主色，**论文图感而非商业咨询路演图**
- 文字精炼到短语，禁止文字墙

## 适用范围

- 开题 / 中期 / 答辩首页（学术汇报）
- 组会引导页 / 课题汇报 / Lab meeting cover
- 项目立项书的研究框架图（学术风）
- Faculty 个人主页 / Lab 主页的"current research"区块

## 何时使用

- 用户提到「开题 / 答辩 / 总览图 / 研究框架 / PPT 首页 / 引导页 / lab 主页」
- 用户希望视觉「学术答辩 PPT 首页风，正式克制工程化，不要咨询路演风」
- 用户已能给出 5 个左右的核心模块

不要使用：

- 用户要的是「期刊投稿 Graphical Abstract」 → 用 `academic-figures/graphical-abstract.md`
- 用户要的是「方法 pipeline」 → 用 `academic-figures/method-pipeline-overview.md`
- 用户要的是「商业 / 投资人路演封面」 → 用 `slides-and-visual-docs/visual-report-page.md`
- 用户要的是「品牌主视觉海报」 → 用 `poster-and-campaigns/brand-poster.md`

## 缺失信息优先提问顺序

1. 课题 / 研究主题（写在标题区）
2. 答辩类型（开题 / 中期 / 终期 / 组会 / 立项）—— 决定语气与模块构成
3. 5 个核心模块的命名（默认是：背景 / 目标 / 研究内容 1 / 研究内容 2 / 预期结果）
4. 是否需要主观点 / 关键问题（强烈建议有，写在背景模块下方）
5. 是否需要研究对象简化示意（颗粒 / 器件 / 流程 / 系统）
6. 标签语言（中文 / 英文 / 双语；中文答辩通常中文为主，可英文副标题）
7. 比例（默认 16:9 适配 PPT；4:3 适配旧 PPT 模板）

## 主模板：上中下三层 + 五模块研究总览

📖 描述

整张图按"上方主题 + 中间核心模块 + 下方结果导向"分成三层。中间层包含 4-5 个研究内容模块，呈现层级清晰、对齐严格的学术布局，**绝对不像商业路演 PPT**。

📝 提示词

```json
{
  "type": "学术研究总览图（research overview / framework figure for thesis defense）",
  "goal": "生成一张可直接放进开题答辩 / 论文汇报 PPT 首页的研究总览图，要求正式克制、白底、工程化配色、明显论文图感、绝无商业路演感",
  "canvas": {
    "aspect_ratio": "{argument name=\"aspect_ratio\" default=\"16:9\"}",
    "background": "pure white #FFFFFF",
    "outer_padding": "60px around the diagram",
    "render_quality": "vector-clean look, anti-aliased edges, sharp text"
  },
  "title_block": {
    "main_title": "{argument name=\"main_title\" default=\"Research Overview\"}",
    "subtitle": "{argument name=\"subtitle\" default=\"e.g. thesis topic in one short phrase\"}",
    "occasion_label": "{argument name=\"occasion_label\" default=\"Thesis Proposal Defense\"}",
    "position": "top-center, main_title in bold sans-serif 18-22pt, subtitle in regular 12-14pt below, occasion_label in italic gray 10pt at top-right"
  },
  "background_section": {
    "label": "{argument name=\"background_label\" default=\"Background & Problem\"}",
    "summary": "{argument name=\"background_summary\" default=\"a short phrase stating why this matters and what gap exists\"}",
    "key_question": "{argument name=\"key_question\" default=\"a single research question, expressed as one sentence ≤ 18 words\"}",
    "position": "upper-middle band, full width, visually anchored as 'context'"
  },
  "objective_section": {
    "label": "{argument name=\"objective_label\" default=\"Objective\"}",
    "summary": "{argument name=\"objective_summary\" default=\"a short phrase stating the research goal\"}",
    "position": "directly below background, narrower than background, centered"
  },
  "research_modules": {
    "count": "{argument name=\"module_count\" default=\"3\"}",
    "items": [
      {
        "id": "RM1",
        "name": "{argument name=\"module_1_name\" default=\"Characterization\"}",
        "summary": "{argument name=\"module_1_summary\" default=\"a short phrase stating what is studied / measured\"}",
        "method_hint": "{argument name=\"module_1_method\" default=\"thermogravimetric analysis\"}"
      },
      {
        "id": "RM2",
        "name": "{argument name=\"module_2_name\" default=\"Modeling\"}",
        "summary": "{argument name=\"module_2_summary\" default=\"a short phrase stating the modeling / simulation focus\"}",
        "method_hint": "{argument name=\"module_2_method\" default=\"CFD combustion model\"}"
      },
      {
        "id": "RM3",
        "name": "{argument name=\"module_3_name\" default=\"Optimization\"}",
        "summary": "{argument name=\"module_3_summary\" default=\"a short phrase stating optimization or application focus\"}",
        "method_hint": "{argument name=\"module_3_method\" default=\"parameter sweep + emission analysis\"}"
      }
    ],
    "layout": "horizontal row of equal-width modules in the central band, all modules identical size and identical style"
  },
  "expected_outcome_section": {
    "label": "{argument name=\"outcome_label\" default=\"Expected Outcomes\"}",
    "items": "{argument name=\"outcome_items\" default=\"3-4 short phrases listing deliverables, e.g. 'kinetics database', 'optimized operating window', 'engineering recommendations'\"}",
    "position": "bottom band, full width, visually distinct from research_modules but stylistically consistent"
  },
  "module_block_style": {
    "shape": "rounded rectangle (corner radius ~8px) OR stage label + thin underline",
    "size_per_module": "all modules identical size, vertically aligned",
    "fill": "very light tint (e.g. #F1F5F9, #ECFEFF) — at most 2 different tints; modules of the same role share the same tint",
    "border": "1.2px solid #334155",
    "title_text": "module name in bold sans-serif (PingFang SC / Source Han Sans for CJK; Inter / Helvetica / Arial for english), 13-14pt",
    "summary_text": "single phrase, 10-11pt regular, 1-2 lines max, no period",
    "method_hint_text": "italic gray 9-10pt, below summary"
  },
  "connectors": {
    "style": "thin arrows (1.2px) with simple triangle arrowheads, dark gray #334155",
    "rule": "vertical flow background → objective → modules → outcomes; modules are horizontally parallel (no inter-module arrows unless logically required)",
    "decoration": "none; no curved arcs, no dashed unless explicitly indicating a feedback loop"
  },
  "color_palette": {
    "rule": "≤ 3 main colors total, drawn from a low-saturation engineering set: deep blue #1E3A8A / slate blue #3B82F6 / charcoal #1F2937; allow ONE low-saturation accent (e.g. amber #F59E0B) for the outcome band only if user signaled emphasis",
    "must_print_grayscale_readable": true
  },
  "typography": {
    "language": "{argument name=\"language\" default=\"chinese\"}",
    "rule": "chinese → PingFang SC / Source Han Sans; english → Inter / Helvetica / Arial; bilingual → primary line larger, secondary line smaller and gray",
    "consistency": "all module titles identical size; all summaries identical size; never mix serif and sans-serif"
  },
  "constraints": {
    "must_keep": [
      "all research modules identical size, vertically aligned, equal weight",
      "white background, no gradient, no decorative pattern",
      "language and font consistent across the entire figure",
      "summaries are short phrases, never full paragraphs",
      "the figure must look like the cover slide of an academic defense, not a corporate roadmap or pitch deck",
      "color palette ≤ 3 main colors, must remain readable in grayscale print"
    ],
    "avoid": [
      "consulting / pitch-deck aesthetics, brand campaign aesthetics",
      "decorative icons, emoji, mascots, hand-drawn wobble",
      "3D rendering, glossy fills, lens flare, drop shadow blocks",
      "stock-photo backgrounds, photographic hero images",
      "fabricated quantitative claims (no '+30% efficiency', '150 samples' unless user provided them)",
      "saturated brand colors, neon, vivid gradients",
      "dense text walls; no module summary should exceed 2 lines",
      "watermarks, copyright stamps, university / lab logos unless explicitly requested"
    ]
  }
}
```

### 参数策略

- **必问**：`main_title`、5 个核心模块（背景 / 目标 / 研究内容 1-N / 预期结果）的命名
- **可默认**：`aspect_ratio`（16:9）、`background`（白色）、`color_palette`（深蓝/灰蓝/黑灰）
- **可随机**：`method_hint` 措辞（用户给出方法名时可学术化）；`occasion_label`（开题 / 中期 / 终期 / 组会）

### 自动补全策略

- 用户给出主题但没给模块 → 反问 3-4 个研究模块，**禁止编造研究内容**
- 用户给出 `key_question` 超过 18 词 → 主动建议精简或拆成 2 个子问题
- 用户没给 expected outcomes → 用占位短语（如 "deliverable 1: ..."）并标注待用户补充
- 用户说"中文答辩 / 中文 PPT" → `language` 默认中文，主标题中文 + 英文副标题（小一号 + 灰色）

## 变体 1：中心主题 + 周围模块（辐射式）

```json
{
  "type": "中心主题 + 周围模块的研究总览",
  "modify": {
    "layout": "中央放置研究主题 / 研究对象的简化示意；周围呈环形或四象限放置 4 个研究模块；下方留出预期结果带",
    "rule": "中央对象占画面 25-30%；周围模块等大、等距、对齐严格",
    "use_case": "适合系统型 / 平台型课题，研究模块之间是平行而非前后依赖关系"
  }
}
```

适用：平台型课题、综合性课题、研究方向多支并行的总览。

## 变体 2：左右双栏（左 = 研究内容，右 = 路线 / 时间表）

```json
{
  "type": "左右双栏研究总览",
  "modify": {
    "layout": "左栏 = 研究内容模块（垂直堆叠 3-4 个）；右栏 = 时间表 / 路线 / 里程碑（gantt 风极简）",
    "rule": "左右栏宽度比约 3:2；右栏时间轴用细线 + 节点圆，节点旁标月份或学期",
    "use_case": "开题答辩需要明确"做什么 + 什么时候做"的项目计划"
  }
}
```

适用：开题答辩、项目立项书需要附进度计划的场景。

## 变体 3：极简版（只显示研究模块，无 timeline / 无 outcome 带）

```json
{
  "type": "极简研究总览",
  "modify": {
    "layout": "去掉 expected_outcome_section，去掉时间轴；只保留 title + background/key_question + 3-4 个研究模块",
    "use_case": "组会汇报引导页或 lab meeting cover，只需快速点出'这次要讲什么'"
  }
}
```

适用：组会 / Lab meeting / 课程汇报。

## 避免事项

- 把研究总览图画成商业咨询路演风（深色背景 + 大色块 + brand 色） → 立刻"非学术"
- 用 emoji / 商业图标 / 卡通插画装饰研究模块
- 把研究模块写成完整段落，每个模块超过 2 行 → 视觉拥挤
- 在"预期结果"中编造具体百分比 / 数据指标（**严格禁止虚构数据**）
- 让某一研究模块明显大于其他（应该等权）
- 用饱和 / 渐变 / 玻璃质感装饰背景
- 强加学校 / 实验室 logo 或 watermark（除非用户明确要求）
- 把方法 pipeline 详细图（应该用 `method-pipeline-overview.md`）塞进总览图中
