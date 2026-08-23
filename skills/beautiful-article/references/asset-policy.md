# 配图与素材策略

配图必须服务文章，不是装饰。Phase 2 把配图策略与逐图计划写进 `plan/plan.md` 的
**Assets** 段（见 `plan-template.md`），**不再产出独立的 `asset-plan.md` 文件**。

## 与 Raw 正交：配图策略只管 Image，不管 Raw（铁律）

**配图策略 = 是否使用外部 `Image`，以及用哪种来源。它与 `Raw` 完全正交，不是二选一：**

- **`Raw` 始终存在**，是每篇文章默认的表现力层（任意 HTML / CSS / JS / React：交互、
  自定义布局排版、动效、小工具，以及按需的 SVG / canvas 图解），不受配图策略影响，也永远
  不需要用户"开启"。
- **`Image` 是独立的可选叠加层**，由配图策略决定是否使用、用哪种来源。
- 选 `none` **不等于**"用 Raw 替代 Image" —— 它只表示"不使用外部图片"，`Raw` 照常使用。

> 别把它框成 "Image vs Raw"。正确心智是："Raw 一定有；Image 要不要、用哪种来源，由用户在
> Plan Checkpoint 明确选定。"

## 四种来源模式（只针对 Image）

| 模式 | 说明 | 适合情况 |
|---|---|---|
| `user-assets` | 用户提供截图 / 照片 / 图表 / 素材目录 | 产品文章、代码审阅、真实报告 |
| `placeholders` | 先用占位图或图片位说明 | 用户稍后补素材 |
| `ai-generated` | AI 按文章和主题生成图片提示词 | 视觉文章、概念解释、封面图 |
| `none` | 不使用外部图片（`Raw` 自由层 / 表格不受影响，照常使用） | tufte 风、技术分析、证据型文章 |

**不主动生成 AI 图片**：`ai-generated` 必须用户显式选择。但即便选 `none`，也不影响 `Raw`。

## Asset Checkpoint 必问（Plan Checkpoint 内 · 必须让用户选，不能默认通过）

配图模式是**必选项**，不允许用一个默认值一笔带过。先一句话说明"Raw 照常使用"，再让用户
从四种 **Image** 来源里明确选一种：

```text
配图模式（这一项只决定是否使用外部 Image；Raw 自由层 —— 交互 / 布局 / 动效 / 图解 —— 不受影响，照常使用）。
请从以下四种里选一种：
- none：不使用外部图片，靠正文 + Raw + 表格表达（推荐给技术 / 证据型文章）。
- user-assets：你提供素材目录或截图，我据此排版。
- placeholders：先放占位图，我在 plan.md 的 Assets 段标注每张图应替换成什么。
- ai-generated：我先生成配图提示词，等你确认后再生成图片。
我的推荐：<策略>，原因：<一句话>。你确认或改成别的？
```

## ai-generated 提示词原则

选 `ai-generated` 时**不直接随意生成图片**，先在 `plan/plan.md` 的 Assets 段列出每张图：
位置 · 服务的段落 / 论点 · 目的 · 主题风格 · 构图 · 禁止项 · 提示词 · 备选提示词。

示例：

```text
Image 01
位置：Hero 背景
目的：建立"技术出版物"气质，不解释具体机制
主题：press
风格：warm editorial still life, paper texture, low saturation
禁止：3D icon, neon gradient, SaaS stock photo, smiling office people
Prompt: Warm editorial photograph of a desk with annotated technical notes,
printed code snippets, a graphite pencil, soft morning light, low saturation,
refined book-publishing mood, no screens, no logos.
```

## 图片自检（每张图）

- 是否服务文章中的具体位置？是否符合选定主题 `theme-profiles/<id>.md` 的媒体风格？
- 是否不是纯装饰？是否不会抢正文？是否没有和 Raw 表达重复？
- 是否有 caption / source / alt 文本？

配图自查并入 Plan 自查（5 条之一："Raw / 图片有目的"）—— 由主 Agent 内联完成，
**不再单独开 Asset Reviewer SubAgent**。详见 `review-checklist.md` 的 Plan 自查段。
