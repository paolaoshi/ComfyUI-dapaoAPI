# 手绘风信息图模板

本文件用于生成"手绘 / 笔记本 / 涂鸦 / 暖色 macaron / morandi 雾感"质感的信息图：

- 学习笔记 / 知识卡 / 概念图解
- 公众号 / 小红书"手绘种草"图文
- 教学讲义 / 课堂涂鸦
- 旅行手账 / 美食手账 / 阅读笔记
- 活动通知 / 暖系活动海报

特征：

- 所有线条都有轻微抖动 / 不规则（hand-drawn wobble）
- 配色低饱和、温暖、像水彩或彩铅
- 元素之间有大量"留白 + 涂鸦装饰"
- 字体是手写感（非电脑字体）
- 颜色填充会"留边"，像手工上色

> 设计判断：手绘风是「风格语言」，自由度极高，不同主题（学习 / 美食 / 旅行 / 心情）的具体元素差异极大。**强行 JSON 反而会限制画面自由度**，因此本模板采用「**结构化自然语言提示词 + 参数表 + 元素清单**」的混合形式，比纯 JSON 更自然。

## 适用范围

- 学习笔记 / 概念解析 / 知识卡片
- 步骤教程 / how-to / 操作流程的"手绘版"
- 列表 / 清单 / 排行榜的"手绘版"
- 暖系内容（情绪 / 治愈 / 美食 / 旅行）
- 公众号 / 小红书 / 社交平台"手账风"配图

## 何时使用

- 用户提到 "手绘 / 手账 / sketch notes / 涂鸦 / 笔记 / 课堂笔记 / macaron / morandi / 暖色 / 治愈"
- 用户希望视觉「亲切、好读、不像 PPT」
- 用户希望「读者感觉是真人手画的」

不要使用：

- 用户要的是高密度科普因果链 / 解剖图（用 `infographics/legend-heavy-infographic.md`）
- 用户要的是模块化便当格（用 `infographics/bento-grid-infographic.md`）
- 用户要的是工程精度的流程图 / 架构图（用 `technical-diagrams/`）
- 用户要的是出版级图表（用 `academic-figures/publication-chart.md`）
- 用户要的是真正的治愈系场景插画（用 `scenes-and-illustrations/healing-scene.md`）

## 缺失信息优先提问顺序

1. 主题（要讲什么？比如"5 种泡咖啡的方法"、"番茄工作法"、"上海 City Walk Top 10"）
2. 信息条数（建议 3-7 条）
3. 配色基调（macaron 暖奶油 / morandi 雾感 / kraft 牛皮纸 / 黑板色）
4. 是否有人物 / 吉祥物（一只猫 / 简笔小人 / 无人物）
5. 比例（小红书 3:4 竖版 / 公众号 16:9 横版 / 1:1 方版）
6. 是否要配色块「条目分区」还是"自由排布"

## 主模板：手绘风信息图

📖 描述

整张图是一张「像被人在笔记本上手画出来」的信息图：暖色背景 + 手写体大标题 + 3-7 条手绘卡片 / 圆圈 / 气泡 + 简笔图标 + 涂鸦装饰 + 手绘箭头连接。

📝 提示词（结构化自然语言模板）

```
A hand-drawn educational infographic in the style of a high-quality bullet journal page.

Topic: {argument name="topic" default="番茄工作法的 5 个核心步骤"}.

Aspect ratio: {argument name="aspect_ratio" default="3:4 portrait"}.

Background:
- Warm {argument name="background_color" default="cream / off-white"} paper texture with subtle grain.
- Optional washi-tape strips in the corners (diagonal stripes, muted tones).
- DO NOT use pure white or pure black background.

Color palette:
- {argument name="palette" default="macaron"} — describe colors:
  - macaron: warm cream #F5F0E8 background, muted blue #A8D8EA, lavender #D5C6E0, mint #B5E5CF, peach #F8D5C4, coral red #E8655A accent
  - morandi: dusty sage, terracotta, mustard, taupe, soft brick
  - kraft: kraft paper background, dark brown ink, tomato red accent, muted navy
  - chalkboard: dark slate background, white chalk, yellow / coral / mint chalk highlights
- Limit to 4-5 colors total. Use the accent color sparingly for emphasis.

Title:
- "{argument name="title" default="番茄工作法 5 步"}" in large hand-lettered calligraphy at the top.
- Title sits inside a hand-drawn frame: irregular oval, scalloped rectangle, or wavy banner.
- Optional subtitle below in smaller handwritten print.

Body:
- {argument name="item_count" default="5"} information items.
- Each item is presented as a hand-drawn card / rounded rectangle / cloud bubble / circle, with:
  - A number badge (1, 2, 3 ... in a circle, drawn by hand)
  - Item title in bold handwritten text
  - 1-2 lines of body text in neat handwritten print
  - A simple doodle icon (1-2 strokes, NOT realistic) representing the item
- Items can be arranged: vertical list / 2-column grid / circular wheel / winding path.

Doodle decorations (sprinkle naturally, not symmetrically):
- Tiny stars, sparkles, hearts, arrows-curvy, dotted lines, exclamation marks
- Hand-drawn underlines and circle-marks for emphasis on key words
- Smiley / frowny faces (😊 ☹) as quality indicators where relevant
- Optional: a single mascot character (a cat / a stick-figure person / a coffee cup with face) as the "narrator"

Style enforcement:
- ALL lines have visible hand-drawn wobble — never perfectly straight
- ALL color fills leave a tiny gap before the outline (hand-painted feel)
- All text is hand-lettered — NO computer fonts, NO Helvetica, NO Arial
- Slight imperfection is intentional — it should NOT look digitally precise
- The whole image feels like a single page from someone's notebook

Composition:
- Generous whitespace (~30-40% of the canvas)
- Information hierarchy: title > item titles > body > doodle decorations
- Items are large enough to be readable; do not cram

Language: {argument name="language" default="中文（手写体感）"}; technical / proper nouns can stay in English.
```

### 参数策略

- **必问**：`topic`、`item_count`、`aspect_ratio`
- **可默认**：`palette`（默认 macaron）、`background_color`（跟随 palette）、`language`（默认中文）
- **可随机**：mascot 是否出现 / 用什么吉祥物、doodle 装饰的具体造型、卡片形状（圆角矩形 / 云朵 / 圆圈）

### 自动补全策略

- 用户只给 `topic` 时：
  - 自动决定 5 条要点（除非主题明显是 list 类的，比如"7 个习惯"那就用 7 条）
  - 自动用 macaron 配色
  - 自动用 3:4 portrait（小红书友好）
  - 不放 mascot（除非主题适合，如"猫咪护理 5 步"自然出现猫）
- 用户说"我要小红书风" → palette 自动选 macaron 或 morandi，aspect 3:4
- 用户说"教学 / 课堂" → palette 自动选 chalkboard 或 macaron
- 用户说"暖系 / 美食 / 治愈" → palette 自动选 morandi 或 kraft

## 变体 1：黑板粉笔风手绘信息图

把上面提示词里的 palette 换成 `chalkboard`：

```
Background: dark slate / chalkboard green (#2F4F4F) with faint chalk dust texture.
Lines and text: white chalk with visible pressure variation.
Highlights: yellow chalk for important keywords, coral / mint chalk for accents.
Decorations: hand-erased smudges in the background, chalk arrows, chalk underlines.
```

适用：教学讲义、班级文化墙、知识科普"上课"感。

## 变体 2：牛皮纸 / Kraft 暖系手绘信息图

把背景换成 `kraft paper`：

```
Background: warm kraft paper #C9A876 with visible paper fibers.
Lines and text: dark espresso brown #3E2723 with hand-drawn wobble.
Accents: tomato red #E63946, muted teal #457B9D.
Decorations: stamp marks, dotted borders, thread / yarn doodles, postal style elements.
```

适用：复古手账、咖啡 / 烘焙 / 慢生活、文创周边。

## 变体 3：单色铅笔 / 极简手绘信息图

```
Background: pure cream #FAF7F2.
Lines: single dark color (charcoal #2B2B2B or sepia #6B4423) only.
NO multi-color fills. Use varying line weight and cross-hatching for shading.
Decorations: minimal — just dotted lines and small symbols.
```

适用：克制 / 文艺 / 严肃但仍要手绘感的内容（哲学、读书笔记）。

## 避免事项

- 任何元素出现完美的几何形状 / 直线 → 失去手绘灵魂
- 使用 Helvetica / Arial / 思源黑等电脑字体 → 立刻塑感
- 颜色填满到边缘没有留白 → 像电子贴纸，不像手画
- 渐变 / 阴影 / 玻璃质感 / 金属质感 → 完全跑偏
- 一张图 ≥ 6 种主色 → 失去手账的克制感
- 文字行距过紧 / 字号一致 → 失去层次感
- 装饰物太多到喧宾夺主 → 信息读不出来
- 所有信息卡造型完全一致（一模一样的圆角矩形 ×5）→ 失去手绘的有机感
