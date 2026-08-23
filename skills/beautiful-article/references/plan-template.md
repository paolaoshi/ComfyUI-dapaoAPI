# plan.md 模板（单一规划文件）

Phase 2 **只产出一份** `plan/plan.md`，四段：**Brief / Outline / Theme / Assets**。
**不直接写 HTML**。写完后由主 Agent 内联跑 5 条自查（见 `review-checklist.md` 的 "Plan
自查"），按结论改 `plan/plan.md` 本身，**不开 SubAgent、不写任何 review 文件**，然后进入
Checkpoint 1。

> 为什么合并：原先四份文件（editorial-brief / outline / theme-decision / asset-plan）真正
> 跨阶段被读取的只有"信息保留比例 / 目标语言 / 章节锚点 / 主题 id"。合并成一份后，主 Agent
> 维护更省心，Section subagent 只需打开 plan.md 找到"Outline"段里自己的章节即可。

---

## `plan/plan.md` 完整模板

```markdown
# Plan

## Brief

- 目标读者：<谁会读，带着什么问题>
- 目标语言：<跟随源语言（默认） / 指定语言>。若指定且与源不一致：源语言 <X> → 目标 <Y>，
  事实底座用翻译版 `source/source.<lang>.md`（地道、去翻译腔）
- 文章类型：<longform / full-report / tutorial / explainer / dialogue / review / essay / interactive-explainer / briefing / visual-essay>
- 信息保留比例：<X%>（默认走类型标配：longform=100% · tutorial=90% · full-report=80% ·
  explainer=80% · dialogue=80% · review=70% · essay=70% · briefing=50% · visual-essay=40% ·
  **interactive-explainer=~25%（特例 · 见下）**；用户偏离标配则写实际值并加一行"非标配组合
  · 注意事项"，提醒主 Agent 在写每节时手动调整正文/视觉比例）
- **interactive-explainer 特例说明**：这个比例的含义和其它类型不同 —— 不是"原文删了 75%"，而是
  "成品里直接来自原文的句子 / 段落约占 25%"；其余 75% 是 AI 围绕核心知识点全新创作的引导文字
  + 交互演示 + 自己试 + 验证理解。本质是**内容重构**而非内容压缩。
- 必须保留的信息：<章节 / 表格 / 代码 / 数据 / 引用，逐条列；指向 source.md 的具体位置>
- 可删减的信息：<重复 / 旁枝 / 过时内容；每条带理由>
- 语气：<克制分析 / 出版叙事 / 决策汇报 / 教学>
- 主要观点：<这篇要让读者记住的 1-3 个判断>
- 阅读目标：<读完能做什么 / 知道什么>
- 版式宽度：<narrow / regular / wide / full>（默认 regular，见 layout.md）
- TOC：<开 / 关>（默认开）
- 配图策略：<none / user-assets / placeholders / ai-generated>
- 封面：<开（默认） / 关>。若开，写一句构图想法 + 选定的封面模板（A 左字右图 / B 大字盖图 /
  C 上字下图 / D 几何拼贴 / E 极简框）+ 主视觉用什么（如"SVG 缓存命中率曲线"/"包豪斯三色块"）。
  详见 `references/cover.md`。Brief 阶段一句话即可，正式视觉在 Phase 4 First Spread 替换
  `article/Cover.tsx` 时落定。

## Outline

- Hero：<标题气质 / 副标题 / meta：日期·来源·作者>
- Lead：<导语，框定主题，1-2 句>
- Summary：<是否需要；放结论先行 / TL;DR>

### Sections

1. <编号 NN> <标题>
   - 保留信息：<从 source.md 哪几段，要保留到什么程度>
   - 需要的组件：<Section 正文 + 是否 Aside/Quote/Table/CodeBlock/Formula/Image>
   - 是否需要 Raw：<是/否；若是，服务哪个论点、表达目的>
2. ...

- 结尾方式：<Conclusion / 行动项 / 留白收束>

## Theme

- 选定主题：<tufte / press / ...>
- 理由：<为什么是它，结合源材料类型 / 语气 / 配图策略>
- 与源材料的冲突：<若有，如何处理；若无，写"无">
- 当前信息密度下的表现建议：<正文 / Raw / 图片比例如何调整；可引用 theme-profiles/<id>.md>

## Assets

> 这一段配合"Brief / 配图策略"使用。`none` 模式下写一句话即可。

- 策略：<none / user-assets / placeholders / ai-generated>
- 一句话说明：<为什么是这个策略；Raw 始终存在、不在本段讨论>

### 逐图计划（仅 user-assets / placeholders / ai-generated 模式需要）

每张图列：

- 位置：<Hero 背景 / Section 02 之后 / ...>
- 服务的段落或论点：<...>
- 目的：<建立气质 / 解释机制 / 提供证据 / ...>
- 主题：<选定主题>
- 风格 / 构图：<...>
- 禁止项：<3D icon / neon gradient / SaaS stock photo / 笑脸办公室人 / ...>
- 来源：<user-assets 文件路径 / placeholders 描述 / ai-generated 提示词>
- 备选提示词（ai-generated 模式）：<...>
```

---

## 模板使用要点

- **Outline 是章节锚点**：Section subagent（开发模式 B 下）会读这一段找到自己负责的章节。
  每节用 `<编号 NN> <标题>` 起头，编号要和最终 `article/sections/NN-*.tsx` 一致。
- **必须保留 / 可删减**列出来不是装饰，**Section Reviewer 会核对**信息保留比例是否兑现。
- **Theme 段不必长**：通常 3-5 句话足够。冲突的处理才是这段的真正价值。
- **Assets 段在 `none` 模式下极短**：一句话说明"不使用外部图片，靠正文 + Raw + 表格表达"
  即可，不需要逐图计划。

## 与其它 reference 的关系

- 文章类型选择：见 `article-types.md` → `article-types/<type>.md`。
- 信息保留比例：见 `information-density.md`。
- 主题选择：见 `theme-selection.md`，结论落到本模板的 **Theme** 段。
- 版式宽度 / TOC：见 `layout.md`，结论落到本模板的 **Brief** 段。
- 配图四种来源 / ai-generated 提示词原则：见 `asset-policy.md`，结论落到 **Assets** 段。
- 封面（书封式题图：屏幕 3:4 / PDF 独占首页）：见 `cover.md`，结论落到 **Brief** 段的
  "封面"一行；正式视觉在 Phase 4 First Spread 写 `article/Cover.tsx` 时定稿。
- 自查清单：见 `review-checklist.md` 的"Plan 自查（5 条）"。
