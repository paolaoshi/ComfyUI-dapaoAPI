# 评审清单与 Reviewer

> 本文件的核心目的：**让每个节点用对的方式做对的事**，不要错开 SubAgent、不要错写文件。
> 误开 SubAgent / 错写 review 文件是首要性能问题。完整规则见 SKILL.md「硬性质检协议」段。

## 各阶段质检方式（铁律）

| 阶段 | 质检方式 | 产物 |
|---|---|---|
| **Phase 1 Source（默认）** | 主 Agent 内联 5 条 checklist（见 `source-to-markdown.md`） | 无文件 |
| Phase 1 Source（仅复杂/低置信源） | Source Reviewer SubAgent（对照 `original.*` diff） | `review/source-review.md` |
| **Phase 2 Plan / Checkpoint 1 前** | **主 Agent 内联自查（禁开 SubAgent）** | **无文件** |
| **Phase 4 First Spread / Checkpoint 2 前** | First Spread Reviewer SubAgent | `review/first-spread-review.md` |
| **Phase 5 每个 Section** | Section Reviewer SubAgent | **以消息返回 pass/fail + 修复点，不写文件** |
| **Phase 6 终审 / Checkpoint 3 前** | Editorial + Visual + Technical Reviewer SubAgent | `review/final-review.md` |

拿到结论后**先按 fail 项把产出改完，再向用户汇报**。直接拿结论汇报但不修复 = 违规。

---

## Plan 自查（Phase 2 → Checkpoint 1 · 主 Agent 内联 · 5 条）

写完 `plan/plan.md` 后**就地**核查这 5 条，按结论改 `plan/plan.md` 本身（不要写新文件）：

1. **Brief / Outline 自洽**：信息保留比例与每节"保留信息"加起来对得上；Outline 没有偷偷
   塞 Brief 没承诺的内容，也没有遗漏 Brief 必须保留的内容。
2. **信息取舍有据**：每个"可删减"项都给出了理由（重复 / 旁枝 / 过时）；每个"必须保留"项
   都指向 source.md 的具体段落 / 表格 / 代码。
3. **没有过度组件化**：每节的"需要组件"不是把所有内容都框成 Aside / Quote / Table；正文仍
   是主体（prose-first，见 `component-policy.md`）。
4. **Raw / 图片有目的**：Outline 里每个标注"需要 Raw"或"需要 Image"的位置，都能用一句话
   说出它服务的论点 / 表达目的，不是装饰。
5. **章节序号合理**：Outline 章节连续单调（01 / 02 / 03 …），子节序号前缀对齐父章节（第 08
   章下只能是 8.1 / 8.2，不要出现 5.1）。

> 这一步**绝不开 SubAgent**：内容量小、上下文是热的，SubAgent 冷启动反而慢。

---

## First Spread 自检清单（Phase 4 → Checkpoint 2 前 · SubAgent）

SubAgent 读 `article/Article.tsx`、`article/sections/01-*.tsx`、`article/Cover.tsx`（若有）、
`plan/plan.md`、选定主题 `theme-profiles/<id>.md`，按清单核查，写 `review/first-spread-review.md`：

- **封面**（若开 · 见 `cover.md` 5 条自检）：图文并茂、主题忠实（只用 `--ra-*` token）、
  内容忠实（封面视觉跟正文主旨对得上）、比例自适应（屏幕 3:4 + PDF 独占首页都不错位）、
  不与 Hero 重复内容？
- 首屏像文章，不像 landing page？读者是否立刻知道文章要解决什么？
- 第一节有阅读节奏？Raw 服务理解？图片服务表达？移动端能读？
- 主题气质对不对？版式宽度合适吗？
- 代码可构建（`npm run dev` 无报错），浏览器控制台无红字？

prompt 模板：

```text
请作为 First Spread Reviewer。读取 article/Cover.tsx（若有）、article/Article.tsx、
article/sections/01-*.tsx、plan/plan.md、theme-profiles/<id>.md、references/cover.md
（若有封面），对照 First Spread 自检清单逐项核查。把结论写进
review/first-spread-review.md（pass / fail + 证据 + 必须修复项 + 改写建议）。
不要替我改文件，也不要泛泛夸奖。
```

主 Agent 收到结论后**先按 fail 项改完**，再进 Checkpoint 2。

---

## Section 自检清单（Phase 5 每个 Section · SubAgent · 消息返回）

SubAgent 读对应 `sections/<NN>-*.tsx`、`plan/plan.md` 的本节段落、`source/source.md` 本节
对应内容，按清单核查，**以消息形式返回结论**：

- 完成本节 outline 任务？
- 符合 Brief 的信息保留比例？必须保留的信息没丢？
- 与前后节衔接？没有重复或矛盾？
- 没有过度组件化？正文充足？
- Raw 与配图有明确目的？
- **本节序号自洽**：`Section index` 等于主 Agent 指定的 `<NN>`；每个 `Subsection` 序号
  前缀等于 `<NN>`（如 `<NN>=08` 则小节是 8.1 / 8.2，**不要**写成 5.1）。

prompt 模板：

```text
请作为 Section Reviewer。读取 article/sections/<NN>-*.tsx、plan/plan.md 本节段落、
source/source.md 本节对应内容、theme-profiles/<id>.md。
对照 Section 自检清单逐项核查，**直接以消息形式返回**：
- 第一行：pass / fail
- 若 fail：列出修复点（带行号 / 代码片段证据）
不要写任何 review 文件。不要替我改文件。不要泛泛夸奖。
```

主 Agent 收到 fail 项后**直接修对应 section 文件**，再汇报本节交付。

---

## Phase 6 终审三视角（SubAgent · 写 `review/final-review.md`）

**Editorial Reviewer**（文章性、信息取舍、结构）

- 它仍然是一篇文章，不是网页应用。
- 信息保留比例符合 Brief；必须保留的信息没有丢。
- 语言符合 Brief：全文统一为目标语言，地道、无翻译腔、无残留源语言片段（图注 / 引用 / 术语也算）。
- 没有空泛标题、堆卡片、过度总结。

**Visual Reviewer**（主题、Raw、图片、移动端）

- 主题气质统一；Raw 没有野生样式（都用 `--ra-*` token）。
- 图片符合主题和上下文，不抢正文，不与 Raw 重复。
- 没有明显 AI 味：装饰性视觉、紫粉渐变、圆角彩卡、假插画、emoji 装饰。
- 桌面和移动端都可读，无文字溢出 / 遮挡 / 空白异常。

**Technical Reviewer**（构建、控制台、代码 / 公式、可访问性、序号）

- `npm run html` 可构建，`article/article.html` 可打开、可分享。
- 浏览器控制台无报错；代码 / 公式高亮和主题一致。
- 图片有 alt，链接可用，标题层级合理。
- **章节序号全篇自洽**（`index` 是手写字符串，组件不自动编号也不校验）：
  - `Section` 序号连续单调：`01 / 02 / 03 …`，无跳号、无重复、无错序。
  - 每个 `Subsection` 序号前缀等于其父 `Section` 编号：第 08 章下是 `8.1 / 8.2`，**绝不**出现 `5.1`。
  - 序号与左侧 TOC、`plan/plan.md` Outline 章节顺序三者一致。
  - 逐个 `Section` / `Subsection` 把渲染出来（或 TOC 里）的序号抄下来比对，**不要只看代码顺序** ——
    并行模式（开发模式 B）下 subagent 看不到自己在全篇的位置，最容易在这里写错。

prompt 模板：

```text
请作为 <Editorial / Visual / Technical> Reviewer。读取 plan/plan.md、source/source.md、
article/Article.tsx 和所有 article/sections/*.tsx、theme-profiles/<id>.md。
对照本视角的终审清单逐项核查，把结论追加到 review/final-review.md 的
"<视角>"段（pass / fail + 证据 + 必须修复项 + 改写建议）。
不要替我改文件，不要泛泛夸奖。
```

三个视角可并行起 SubAgent，主 Agent 收齐后按 fail 项最小切片修复（见 `repair-policy.md`）。
