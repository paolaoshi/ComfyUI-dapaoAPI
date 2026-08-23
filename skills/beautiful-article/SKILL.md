---
name: beautiful-article
description: "把用户提供的素材（网页 URL / PDF / DOCX / Markdown / 纯文本 / 截图 / 粘贴材料）编辑、设计成一篇美丽的、可离线打开和分享的**单文件 HTML 网页文章**。基于 reacticle 组件协议：不手写裸 HTML/CSS，而用语义组件 + 受主题约束的 Raw 自由层；按 source→规划→双确认→生成→终审→修复的小型 harness 流程推进，默认 100% 信息保留的长文。触发场景：把 URL/PDF/DOCX/文章做成网页文章 / 长文 / briefing / 解释文 / 视觉文章 / 教程 / 审阅复盘 / 方案分析，'render this as a beautiful web article / 把这篇做成网页文章 / 生成一篇可分享的 HTML 长文 / reacticle 文章'。只生成文章，不生成后台、表单、dashboard、产品原型或通用 Web App。"
---

# Beautiful Article

## 背景原则

AI 生成内容越复杂，输出媒介越重要。HTML 的价值在于同时提升信息密度、视觉清晰度、分享便利性和交互能力：表格、SVG、CSS、代码片段、可调控件、复制与导出按钮，可以让读者不只是“看完”，而是能比较、定位、调整、复查和继续使用。Beautiful Article 的目的，是把原本枯燥、线性、难以消化的文字材料，转换成视觉体验更漂亮、阅读节奏更清晰、也更容易审阅和分享的单文件网页文章。


## 边界（先判断要不要进这个 Skill）

- 最终主产物是 **single HTML 文章**，不是网页应用。
- 文章可以有 `Raw` 自由层（任意 HTML / CSS / JS / React：交互、布局排版、动效、小工具、
  按需的 SVG / canvas 图解），但**必须服务阅读、解释、论证、节奏或审美**。
- **不**生成：后台、表单、拖拽工作台、完整 dashboard、产品原型、通用 Web App。
- 信息密度由用户确认；**默认保留 100% 信息**，生成长文式网页文章。

如果用户要的是应用而不是文章，停下来澄清，不要进入本 Skill。

---

## 工作流总览

```
Phase 0  Intake            判断是否进入本 Skill + 初步文章类型
   ▼
Phase 1  Source → Markdown URL/PDF/DOCX/MD/文本 → source.md + extraction-notes.md
         └ 主 Agent 内联 5 条 checklist 自查（仅复杂/低置信源升级 SubAgent）
   ▼
Phase 2  Editorial Planning 一份 plan.md（Brief / Outline / Theme / Assets 四段）
         └ 主 Agent 内联自查（无 SubAgent、无 review 文件）
   ▼
Phase 3  Plan Checkpoint   ★Checkpoint 1 必须停。逐项确认 5 件事：文章类型（含标配保留比例）/ 主题 / 版式 / 配图模式 / 封面
   ▼
Phase 4  First Spread      首屏 + 第一节 + 一个代表性视觉块（脚手架在此创建）
         └ First Spread Reviewer SubAgent（写 review/first-spread-review.md）
         └ ★Checkpoint 2 必须停。逐项确认 2 件事：验收结论 / 开发模式 A/B
   ▼
Phase 5  Full Article Build 生成完整网页文章（默认单 Agent，超长可按 Section 隔离）
         └ Section Reviewer SubAgent（以消息返回 pass/fail，无须写 review 文件）
   ▼
Phase 6  Final Review      Editorial / Visual / Technical 三视角终审（写 review/final-review.md）
   ▼
Phase 7  Repair            最小切片修复，有修复才写 repair-log.md
   ▼
Phase 8  Delivery          ★Checkpoint 3 必须停。逐项确认交付决策 → 交付 article.html + 简短编辑说明
```

工作区结构（脚手架创建；这些文件是 Skill 的长期记忆，**不要只依赖聊天上下文记决策**）：

```text
<workspace>/
  source/   original.*  source.md  source.<lang>.md(需翻译时)  extraction-notes.md
  plan/     plan.md                                    # 单一规划文件：Brief / Outline / Theme / Assets 四段
  article/  Cover.tsx(默认)  Article.tsx  sections/  raw-blocks/  assets/  article.html(产物)
  review/   first-spread-review.md  final-review.md   # 仅这两份是常规产物
            source-review.md(仅复杂源)  repair-log.md(仅有修复时)
  index.html  package.json  vite.config.ts  tsconfig*.json   (构建工装)
```

---

## 硬性质检协议（贯穿整个 Skill）

**质检方式按节点区分 —— 不是所有质检都要开 SubAgent，也不是所有质检都要写文件。**
误开 SubAgent / 误写文件是首要性能问题，按下表严格执行：

| 节点 | 质检方式 | 产物 | 为什么 |
|---|---|---|---|
| **Phase 1 Source（默认）** | 主 Agent 内联 5 条 checklist | 无文件 | 主 Agent 反正要通读 source.md |
| Phase 1 Source（仅复杂/低置信源） | Source Reviewer SubAgent（对照 `original.*` diff） | `review/source-review.md` | 静默丢失只能 diff 抓到 |
| **Phase 2 Plan / Checkpoint 1 前** | **主 Agent 内联自查（禁止开 SubAgent）** | **无文件** | plan 是文字决策且 200-400 行，上下文是热的，SubAgent 冷启反而更慢 |
| **Phase 4 First Spread / Checkpoint 2 前** | First Spread Reviewer SubAgent | `review/first-spread-review.md` | 首屏定调，多一道独立眼睛更稳 |
| **Phase 5 每个 Section** | Section Reviewer SubAgent | **以消息返回 pass/fail + 修复点（不写文件）** | 一篇可能 5-15 节，N 份 review 文件无人再读 |
| **Phase 6 终审 / Checkpoint 3 前** | Editorial + Visual + Technical Reviewer SubAgent | `review/final-review.md` | 交付物的一部分，留档有价值 |

**铁律：**

1. **Plan Checkpoint（Phase 2 → Checkpoint 1）严禁开 SubAgent 做质检**。主 Agent 写完 plan.md
   后**就地**对照 5 条清单（见 `references/review-checklist.md` 的 Plan 自查段）核查、按结论
   改完 `plan/plan.md`，**不要写任何 review 文件**，然后进入 Checkpoint 1。
2. First Spread / Final 必须用 SubAgent（这两个节点 SubAgent 价值 > 开销）；只有探测不到
   SubAgent 环境才由主 Agent 兜底，并在文件首注明"无 SubAgent 环境，主 Agent 兜底"。
3. Section Reviewer 用 SubAgent，但**返回值是消息**（pass / fail + 修复点）；fail 项主 Agent
   收到后直接修，**不要让 SubAgent 写 `review/section-NN-review.md` 文件**。
4. 拿到任何质检结论 —— **先按 fail 项把产出改完，再汇报"做完了 + 自检结论 + 改了什么"**。
   直接拿原始结论汇报但不修复 = 违规。
5. **决策收集铁律 · 禁止静默替用户选择**：在每个 Checkpoint（1 / 2 / 3），所有需要用户确认的
   决策项**必须每项独立列出 + 等用户答复**。Agent **可以推荐**（"我推荐 X，因为 …"），但
   **不能"已经替你定了 X，如果不对再说"** —— 这等于剥夺选择机会。
   - **优先**：如果环境有 `AskQuestion` 工具，每个决策项作为一个独立 question（一次调用可
     传多个 question），用户能用选择卡逐项确认。
   - **否则**：停下来在消息里把所有问题**编号列出**（每个问题独占一段、写清推荐项 + 理由 +
     备选项），明确说"我等你逐项答复后再继续"，**不要继续做任何后续工作**。
   - **绝不**：把多项决策打包成一个"全选我推荐的 / 全部 OK 吗？"yes/no 问题；也不要在
     "推荐一句话"后默认直接进下一步。

各节点的 checklist 与 SubAgent prompt 模板见 `references/review-checklist.md`。

---

## 各阶段文件读取指南（渐进加载，别一次全读）

| 阶段 | 必读 | 按需查 |
|---|---|---|
| Phase 0 Intake | `references/harness.md` | —— |
| Phase 1 Source→MD | `references/source-to-markdown.md` | `scripts/source-to-markdown-markitdown.py` · `scripts/source-to-markdown.py` |
| Phase 2 Planning | `references/article-types.md` · `references/information-density.md` · `references/plan-template.md` · `references/theme-selection.md` · `references/layout.md` · `references/asset-policy.md` · `references/cover.md`（封面构图想法） | `references/article-types/<type>.md` · `theme-profiles/*.md` |
| Phase 4 First Spread / Phase 5 Build（每节回看） | `references/section-build.md` · `references/component-policy.md` · `references/raw-policy.md` · 选定主题 `theme-profiles/<id>.md` · **封面：`references/cover.md`** | `references/scaffold.md`（建项目时一次）· `references/html-output.md` |
| Phase 6/7 Review & Repair | `references/review-checklist.md` · `references/repair-policy.md` | —— |
| Phase 8 Delivery | `references/html-output.md` | `references/pdf-output.md`（仅当用户选 PDF 导出） |

> **长会话里 agent 容易遗忘原则** —— Phase 5 会重复实现 N 个 Section，**每次开工
> 前回看** `component-policy.md` + `raw-policy.md` + 当前主题 `theme-profiles/<id>.md`。

---

## Phase 0 —— Intake

判断是否进入本 Skill，给出初步文章类型与输出模式（默认 single HTML）。

| 用户给的东西 | 该做的 |
|---|---|
| 一个或多个素材（URL/PDF/DOCX/MD/文本/截图） | 进入 Phase 1 |
| 只说"帮我做篇 X 文章"但没素材 | **反问**：先要素材或大纲。Skill 不替用户凭空构思内容 |
| 明显要的是应用 / 工具 / dashboard | 停下来澄清，不进入本 Skill |

**捕获目标语言**：开场就记录用户**期望的最终文章语言**（如用户提到"用中文/做成英文版"等）。

- **用户指定了语言** → 记进 `plan/plan.md` Brief 段的"目标语言"。若与源材料语言不一致，Phase 1
  需先产出一份**地道翻译版**源文，后续基于翻译版编写（见 Phase 1）。
- **用户未指定** → 默认**最终文章语言跟随源材料语言**，不做翻译。

自检：用户要的是**文章**还是**网页应用**？是否需要完整信息？是否要先索取更多素材？
**用户有没有指定最终语言？与源语言是否一致？**

---

## Phase 1 —— Source → Markdown

把任意输入统一成 `source/source.md`，把不确定项写进 `source/extraction-notes.md`。
规则与各类输入处理见 `references/source-to-markdown.md`；可借助
MarkItDown 主路径或轻量 fallback 脚本做 PDF/DOCX/HTML 抽取。

落盘后由**主 Agent 内联自查**（`references/source-to-markdown.md` 的 5 条 checklist），按结论修复
再进入 Phase 2；**仅当 `extraction-notes.md` 标记低置信 / 复杂源**时，才升级为独立 Source Reviewer
SubAgent 并对照 `original.*` 做 diff 式核查（写 `review/source-review.md`）。

**语言处理（紧接抽取之后）**：判断 `source.md` 的语言。

- 用户**未指定**目标语言，或目标语言**与源一致** → 不翻译，后续直接基于 `source.md` 编写，
  最终文章语言 = 源语言。
- 用户**指定**了目标语言且**与源不一致** → 先产出**地道翻译版** `source/source.<lang>.md`
  （如 `source.zh.md` / `source.en.md`），作为后续 Phase 2+ 的**事实底座**；原文 `source.md` 保留
  备查。翻译要求：**用地道的目标语言、去除翻译腔**（按目标语言的表达习惯重组句子，不逐字直译，
  不留生硬的外语语序 / 被动堆叠 / 异国标点），术语 / 数字 / 代码 / 公式 / 引用保持准确，结构与
  信息保留比例不变。翻译说明写进 `extraction-notes.md`。

---

## Phase 2 —— Editorial Planning

形成编辑方案，**不直接写 HTML**。**只产出一份 `plan/plan.md`**（四段：Brief / Outline /
Theme / Assets），模板见 `references/plan-template.md`：

- **Brief**：目标读者 / 文章类型 / 信息保留比例 / 必须保留 / 可删减 / 语气 / 主要观点 /
  阅读目标 / 目标语言 / 版式宽度 / TOC / 配图策略。
- **Outline**：Hero / Lead / Summary / Section 列表 / 每节保留哪些信息 / 每节是否需要
  Raw·Table·CodeBlock·Formula·Image / 结尾方式。
- **Theme**：选定主题 + 理由 + 冲突说明（见 `references/theme-selection.md`）。
- **Assets**：配图策略与逐图计划（见 `references/asset-policy.md`；`none` 模式下本段
  写一句话即可）。

文章类型路由见 `references/article-types.md`；信息密度与组件比例见
`references/information-density.md`。

**自检方式 · 强约束**：写完 `plan/plan.md` 后由**主 Agent 内联**对照 5 条 Plan 自查清单核查
（见 `references/review-checklist.md` 的 Plan 自查段），按结论改完 `plan/plan.md`，**直接进入
Checkpoint 1，禁止开 SubAgent，禁止写 `review/plan-review.md`**。

---

## Phase 3 —— Plan Checkpoint（★硬节点 · Checkpoint 1，必须停）

**铁律：禁止静默替用户选择。每个决策项必须独立列出、独立等用户答复。**

可以推荐（"我推荐 X，因为 …"），**不能**说"已经替你定了 X，如果不对告诉我"——后者等于把
默认值偷渡过去、剥夺选择机会。

**收集方式（按环境二选一）：**

- **优先 `AskQuestion` 工具**：每项作为一个独立 question 传入（一次调用可传多个 question），
  用户用选择卡逐项确认。
- **无 `AskQuestion` 工具**：停下来在消息里把每个问题**编号列出 + 独占一段 + 写清推荐项 + 理由
  + 备选项**，明确说"我等你逐项答复后再继续"，**不要继续做任何后续工作**。

无论哪种方式：每个**独立决策**对应**一个独立问题**，**不要打包成"全部 OK 吗？" yes/no**。

**必须独立确认的 5 项**（缺一不可）：

| # | 决策项 | 选项（语义化标签 · 含标配信息保留比例） | 备注 |
|---|---|---|---|
| 1 | **文章类型**（信息保留比例打包在内） | 完整长文 / 归档 `longform · ~100%` ／ 研究报告 / 正式分析 `full-report · ~80%` ／ 教学步骤 / 上手指南 `tutorial · ~90%` ／ 概念 / 系统解释 `explainer · ~80%` ／ 对话 / 访谈 / 播客 `dialogue · ~80%` ／ PR / 方案 / 事故审阅 `review · ~70%` ／ 观点 / 评论 / 叙事 `essay · ~70%` ／ 交互式学习 / 玩明白一个概念 `interactive-explainer · ~25% 原文摘录 + 75% AI 重构` ／ 决策摘要 / 给忙人看 `briefing · ~50%` ／ 图文为主 / 传播展示 `visual-essay · ~40%` | AI 推荐一个并写一句理由。**比例已绑进类型选项**，不再单独成题（否则会出现 `longform + 20%` 这种伪组合）。用户想偏离标配，用自由文本一句话覆盖（"我要 longform + 60%"），见下方"如何偏离标配" |
| 2 | **主题** | tufte / press / 其它已注册主题（读 `theme-profiles/index.json`） | AI 推荐一个并写一句理由 |
| 3 | **版式宽度** | narrow / regular / wide / full | AI 推荐一个；默认 `regular` |
| 4 | **配图模式**（必选 · 不允许"默认通过"） | none / user-assets / placeholders / ai-generated | 一句话"只决定是否使用外部 `Image`；`Raw` 不受影响" |
| 5 | **封面**（3:4 书封式题图，位于 TOC + 正文之上） | 开（默认） / 关 | AI 推荐"开"，并给一句构图想法（哪种主视觉 + 选哪个封面模板 A/B/C/D/E）。`briefing` / `dialogue` 可推荐"关"。详见 `references/cover.md` |

**TOC 默认开**：因为它只有一个开关 + 几乎所有文章都该开，可以在 Plan Checkpoint 开场说明
里以"默认 TOC 开，要关告诉我"一句话带过，**不必单独成题**。

**已经走默认值、不必单独问的事项**（仍然要在开场说明里明示"如要改请告诉我"，给用户机会
反悔，不能完全藏起来）：

- 最终文章语言：跟随源语言（除非用户已经在前文指定 / 已经翻译完成）。
- 是否允许编辑删减、重组、改写语气：默认允许（按上面的信息保留比例执行）。
- 是否要先看首屏样张：默认会先做（这就是 Phase 4）。
- TOC：默认开。

主题用户说"你定" → 取你推荐的第一个，**在选项里仍要把它和其它候选并列**，标"默认 · AI
推荐"，留反悔余地，不能直接跳过主题问题。

**如何偏离信息保留比例的"标配"**：每个文章类型都自带一个推荐保留比例（见上表）。绝大
多数情况走标配即可。如果用户想精修（比如 "longform 但只要 60%" → 一篇被深度编辑过的长文），
让用户**在开场说明后的自由文本里写一句**"我要 <类型> + <X%>" 覆盖。AI 收到覆盖后要在
`plan/plan.md` 的 Brief 段同时记下"类型 / 标配保留 / 用户覆盖到 X%"，并提醒用户这是"非标配
组合"——这类组合需要主 Agent 在写每节时手动调整正文/视觉比例。

**Plan Checkpoint 开场消息模板（在收集决策之前先发一条简短说明）：**

```
plan/plan.md 已经写好（自检通过）。我会逐项跟你确认 5 件事：文章类型 / 主题 / 版式宽度 /
配图模式 / 封面。

我的推荐先放在这里供参考（不会替你选）：
- 类型：<X>（含标配信息保留 <Y%>。理由：…）
- 主题：<theme>（理由：…）
- 版式宽度：<width>（理由：…）
- 配图模式：<策略>（理由：…）
- 封面：开 / 关（理由：…；若开，构图想法：…）

默认走但你可以推翻：语言跟随源语言；允许编辑删减重组；TOC 开；接下来会先做首屏样张。
信息保留比例如要偏离类型标配，下面回答完直接告诉我具体百分比（如 "longform 但只要 60%"）。

下面逐项请你确认。
```

发完上面这条说明后，**立刻**用 AskQuestion 传 5 个 question（或在无工具环境下编号列出 5
个问题、停下等答复）。**5 项全部收齐答复才能进 Phase 4**；若用户在自由文本里给了"非标配保留
比例"，先确认 AI 已经记进 `plan/plan.md` 再进 Phase 4。

---

## Phase 4 —— First Spread（文章版"第一章验收"）

先做"封面（若开） + 首屏 + 第一节 + 一个代表性视觉块"。**脚手架在这里创建工作区**：

```bash
# 默认开封面
bash <path-to-beautiful-article>/scripts/scaffold.sh ./my-article --theme=<id>
# Checkpoint 1 用户选了"封面 · 关"
bash <path-to-beautiful-article>/scripts/scaffold.sh ./my-article --theme=<id> --no-cover
bash <path-to-beautiful-article>/scripts/scaffold.sh --list-themes
```

它创建 Vite + React + TS 工作区（从 npm 安装 `reacticle` 最新发布版）+ `source/ plan/
review/` 记忆目录 + assembler `article/Article.tsx` + 一个示例 section 组件
（+ 默认 `article/Cover.tsx`，除非 `--no-cover`）。详见 `references/scaffold.md`。

首屏（Hero / Lead）写进 assembler `article/Article.tsx`；**第一个 Section 必须写成独立组件**
`article/sections/01-*.tsx`（这是后续并行的代码锚点，见 `references/section-build.md`）。
**封面**（若开）替换 `article/Cover.tsx` 里的 `<CoverPlaceholder />` 为按主题 + 文章主旨
定制的图文构图，**外壳（3:4 容器 + 打印分页）不要动**。封面设计指南见 `references/cover.md`。
`npm run dev` 预览。它决定标题气质 / 字号 / 内容密度 / Raw 风格 / 配图方式 / 主题是否合适。

**第一个 Section 完成后，按硬性质检协议创建 First Spread Reviewer SubAgent**，写
`review/first-spread-review.md`（**含封面 5 条自检**，见 `references/cover.md`），改完
再进 Checkpoint 2。

---

## Checkpoint 2 · First Spread（★硬节点，必须停）

让用户验收首屏 + 第一个 Section，**并选定后续开发模式**。同样适用 Checkpoint 1 的决策收
集铁律：**两项独立确认，禁止打包；优先 AskQuestion，无工具则编号列出、停下等答复**。

先发一条简短消息：

```
首屏 + 第一个 Section 做好了，npm run dev 在 localhost 预览。
质检结论见 review/first-spread-review.md（已按 fail 项改完，列出修了哪些）。
下面两件事请你独立确认：1) 验收结论 2) 后续开发模式。
```

然后用 AskQuestion 传**两个独立 question**（或编号列出两个问题，停下等答复）：

1. **验收结论** —— 选项：`通过 · 进入完整生成` / `局部修改 · 我会另起一条说改哪里` /
   `主题或版式不合适 · 回到 Checkpoint 1`。
2. **后续开发模式** —— 选项：`A · 单 Agent 顺序（默认 · 最稳 · 风格最统一）` /
   `B · 多 Agent 并行（最快 · 风格轻微差异）`。

**不要把这两件事打包成"通过 + A，OK 吗？"** —— 用户可能"通过验收但想用 B"或反之。
两题都收齐答复后进入 Phase 5。

---

## Phase 5 —— Full Article Build

按 Checkpoint 2 选定的开发模式生成完整文章。详见 `references/section-build.md` +
`references/component-policy.md` + `references/raw-policy.md`。

**铁律 · 每个 Section 必须是独立组件文件**（`article/sections/NN-*.tsx`），**坚决不允许把
多个 Section 直接写进一个组件**。`article/Article.tsx` 只是 **assembler**：import 并排序各
Section，由**主 Agent 拥有**。大型 Raw 同样隔离到 `article/raw-blocks/NN-*.tsx`。文件级隔离
是多 Agent 并行的前提。

开发模式（Checkpoint 2 选定）：

- **A · 单 Agent 顺序（默认）**：主 Agent 顺序写每个 `sections/NN-*.tsx`，最稳、风格最统一。
- **B · 多 Agent 并行**：subagent 各**拥有一个** `sections/NN-*.tsx` 文件并行开发；**主 Agent
  负责合并与稳定性** —— 维护 `Article.tsx` 的 import 与顺序、跑 `npm run typecheck` / `build`、
  兜底主题与风格一致、解决冲突。subagent prompt 模板见 `references/section-build.md`。

其余原则：正文是主体；所有 Raw 用 `--ra-*` 主题 token，禁止野生样式；100% 信息保留以长文
结构为主、Raw / 配图做增强；低信息密度可提高视觉块比例，但仍必须是**文章形态**。

每个 Section 完成后**必须**按硬性质检协议走 **Section Reviewer SubAgent**：是否完成 outline
任务 / 是否符合信息保留比例 / 是否与前后衔接 / 是否过度组件化 / 是否有足够正文 / Raw 与
配图是否有明确目的 / 本节序号自洽。

**SubAgent 以消息返回 pass/fail + 修复点**（pass 则一行 OK；fail 则列出修复点），**不要写
`review/section-NN-review.md` 文件**。主 Agent 收到 fail 项后**直接修对应 section 文件**，
然后再汇报本节交付。

---

## Phase 6 —— Final Review（三视角终审）

从读者 / 主题 / 技术三个视角验收，产出 `review/final-review.md` + 修复列表。
完整硬性清单见 `references/review-checklist.md`。推荐三个 Reviewer（无 Teams 时至少
一个独立 SubAgent）：

1. **Editorial Reviewer**：文章性、信息取舍、结构。
2. **Visual Reviewer**：主题、Raw、配图、移动端。
3. **Technical Reviewer**：构建、控制台、代码 / 公式、可访问性。

核心红线：它仍是一篇文章（不是应用）· 信息保留比例符合 Plan · 必须保留的信息没丢 ·
主题气质统一 · Raw 无野生样式 · 没有明显 AI 味 · 桌面 + 移动端可读 · HTML 可构建可打开可分享。

---

## Phase 7 —— Repair（最小切片）

按最小单位修复，规则见 `references/repair-policy.md`。**禁止**：只反馈一处就重写整篇 /
为修视觉改动已确认的文章结构 / 为压缩信息删掉用户指定必须保留的内容。**有修复才写**
`review/repair-log.md`（无修复 / 一次过则不写）。

---

## Checkpoint 3 · Final（★交付确认）

终审改完后，**停下来**让用户独立确认交付决策（不要"我打算导出 HTML 了，没问题就这样"
直接跳过）。优先 AskQuestion，无工具则在消息里编号列出问题、停下等答复。

- **交付决策** —— 选项：`通过 · 导出 HTML 交付` / `通过 · 同时导出 HTML + PDF` /
  `还有局部修复 · 我会列出具体修哪里` / `先停一停 · 我要再看看`。

只有这一项决策，但**仍要主动停下来问**，不要静默走默认导出 HTML。

---

## Phase 8 —— Delivery

构建并交付（命令见 `references/html-output.md`）：

- `article/article.html`（自包含单页，CSS + JS 内联，断网可打开）—— **主交付物**。
- **可选** `article/article.pdf`：仅当 Checkpoint 3 用户选了"通过 · 同时导出 HTML + PDF"
  时才生成。命令：
  ```bash
  bash <path-to-beautiful-article>/scripts/html-to-pdf.sh
  ```
  脚本探测系统已装的 chromium-family 浏览器，注入 `@media print` 覆盖（TOC 从左右栅格塌
  成上下排布、TOC 独占首页），headless 打印。零 npm 依赖。详细原理 / 故障排除见
  `references/pdf-output.md`。
- 简短编辑说明：文章类型 / 信息保留比例 / 主题 / 配图策略 / 主要编辑取舍。

---

## 默认策略

- 输出 single HTML；文章类型 `longform`；信息保留 100%。
- 语言：用户**未指定**则**跟随源材料语言**；**指定且与源不一致**则先产出地道翻译版
  `source/source.<lang>.md` 再据此编写（去翻译腔，见 Phase 1）。
- 主题：技术 / 证据优先 `tufte`，叙事 / 评论优先 `press`（按源材料推荐）。
- 版式：宽度默认 `regular`、**TOC 默认开**（与主题解耦，见 `references/layout.md`，均在 Checkpoint 确认）。
- 配图：**配图模式是 Checkpoint 1 必选项**（`none` / `user-assets` / `placeholders` /
  `ai-generated`），只决定是否使用外部 `Image`，**不主动生成 AI 图片**。
- Raw：**与配图正交、始终默认存在**，鼓励多用，但必须服务具体段落、用主题 token。选 `none`
  不影响 Raw。
- 自检：**Plan 内联自查（无 SubAgent、无文件）**；**First Spread 与 Final 用 SubAgent + 写文件**；
  **Section 用 SubAgent + 消息返回（不写文件）**。详见"硬性质检协议"段。
- 决策收集：Checkpoint 1 / 2 / 3 **每项独立确认 · 禁止静默替用户选择**。可推荐，不能跳过。
  优先 `AskQuestion` 工具（每项一个独立 question）；无工具则停下、编号列出问题等用户答复。
- 修复：最小切片，有修复才写 `review/repair-log.md`。
- **Colophon · 不可移除**：scaffold 在 `article/Article.tsx` 末尾自带 colophon Raw 块
  （`Made with [beautiful-article](github 仓库) · <主题> theme`，低对比小字、theme token 自适应）。
  **每篇文章必须保留**，禁止删除、禁止移到 Hero 旁边或浮动到角落。切换主题时同步更新 colophon
  里的主题名 + `main.tsx` 的 `<ThemeProvider theme="...">` 两处。
- **封面 · 默认开 · 必须图文并茂**：scaffold 默认在 `article/Cover.tsx` 创建**屏幕 3:4 +
  PDF 独占首页**的书封式题图外壳 + 占位（`--no-cover` 关闭）。封面位于 TOC + Hero + 正文之上，
  独立存在。Phase 4 First Spread 时主 Agent 把 `<CoverPlaceholder />` 替换为按 **主题 +
  文章主旨** 定制的图 + 字构图。**硬约束**：外壳比例 / 打印分页不可动、必须有视觉元素
  + 文字、只用 `--ra-*` token、不要远程图片、不要重复 Hero 内容。**视觉技术全开放**：
  SVG / CSS / Canvas / 复杂 React 组件 / 任意混搭由 Agent 自选，效果好就行。详见
  `references/cover.md`（含 5 条自检 + 5 个构图模板 + 各主题封面起手）。PDF 导出会自动让
  封面独占首页、TOC 从第二页开始。
- **PDF 导出 · 可选**：主交付物始终是 `article/article.html`。**仅当** Checkpoint 3 用户选了
  "通过 · 同时导出 HTML + PDF"，才跑 `bash <skill>/scripts/html-to-pdf.sh` 生成
  `article/article.pdf`；不选则不动。不要替用户默认导。详见 `references/pdf-output.md`。

---

## 成功标准

- 它**首先是一篇文章**。
- 最终文章语言符合用户意图（未指定=跟随源语言；指定=全文统一为目标语言，地道、无翻译腔、
  无残留源语言片段）。
- 用户确认的信息密度被尊重；源材料关键内容没有意外丢失。
- 主题气质统一；配图和 Raw 都服务阅读。
- 页面比 Markdown 更值得读；HTML 可直接打开和分享。
- 40% 信息时读起来像被编辑过的文章，而非缩水摘要；100% 信息时像被精修过的长文，
  而非原文搬运。

---

## 相关资源（按"何时读"标注）

| 文件 | 何时读 | 内容 |
|---|---|---|
| `references/harness.md` | Phase 0 | Skill 的 harness 视角、六问、状态文件约定 |
| `references/source-to-markdown.md` | Phase 1 | 各类输入 → source.md 规则、抽取自检、脚本用法 |
| `references/article-types.md` | Phase 2 | 文章类型路由总览（含逐类型链接） |
| `references/article-types/<type>.md` | Phase 2 选定类型后 | 单类型结构 / 组件 / Raw 边界 / 配图倾向 / 自检 |
| `references/information-density.md` | Phase 2 | 信息密度等级、与组件 / 视觉比例的关系 |
| `references/plan-template.md` | Phase 2 | 单一 `plan/plan.md` 模板（Brief / Outline / Theme / Assets 四段）与写法 |
| `references/theme-selection.md` | Phase 2 | 主题选择、density 与 theme 解耦、新增主题约束 |
| `references/layout.md` | Phase 2 / Checkpoint | 版式：宽度模式（与主题解耦）+ TOC，确认与用法 |
| `references/asset-policy.md` | Phase 2 | 配图四种来源、AI 配图提示词原则、图片自检 |
| `references/cover.md` | Phase 2 / Phase 4 写封面时 | 书封式封面设计指南（屏幕 3:4 / PDF 独占首页）：硬约束、视觉技术全开放、构图模板、各主题封面起手、5 条自检 |
| `references/section-build.md` | Phase 4/5 | 一节一文件铁律、单/多 Agent 模式、并行 subagent prompt、主 Agent 合并 |
| `references/component-policy.md` | Phase 4/5 每节 | reacticle 组件协议、prose-first、信息密度与组件比例 |
| `references/raw-policy.md` | Phase 4/5 每节 | Raw 允许 / 禁止、token 驱动、Raw 自检 |
| `references/html-output.md` | 构建 / 交付时 | dev / build / 单文件 HTML 命令与产物 |
| `references/pdf-output.md` | Phase 8 Delivery 当用户选 PDF 导出时 | `html-to-pdf.sh` 用法、TOC 排版原理、Raw 在 PDF 的表现、故障排除 |
| `references/review-checklist.md` | Phase 6 | 各阶段 Reviewer 清单与 prompt 模板 |
| `references/repair-policy.md` | Phase 7 | 最小切片修复对照表 |
| `references/scaffold.md` | Phase 4 建项目时 | 脚手架做什么、用法、工作区结构、切主题 |
| `theme-profiles/index.json` + `*.md` | Phase 2 选主题 / Phase 5 写作 | 主题 authoring profile（给 AI 读，非 CSS） |
| `scripts/scaffold.sh` | Phase 4 跑一次 | 一键创建文章工作区 |
| `scripts/html-to-pdf.sh` | Phase 8 Delivery 仅当用户选 PDF | HTML → PDF（headless 浏览器 + 注入 print CSS，零 npm 依赖） |
| `scripts/pdf-print-overrides.css` | 改 PDF 样式时 | `html-to-pdf.sh` 注入到 `<head>` 的 `@media print` 覆盖：A) TOC 塌成上下排布；B) 分页行为（撤销 `.ra-section` 原子化、标题不孤儿、寡行控制等）；C) 封面独占首页 |
| `scripts/source-to-markdown-markitdown.py` | Phase 1 | MarkItDown 主路径，适合复杂 PDF / DOCX / HTML |
| `scripts/source-to-markdown.py` | Phase 1 | 轻量 fallback，适合 Markdown / TXT / 简单 HTML 或 MarkItDown 不可用时 |
