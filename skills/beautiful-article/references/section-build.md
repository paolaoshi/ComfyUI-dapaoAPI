# Section 构建与多 Agent 并行

## 铁律：一个 Section = 一个组件文件

每个 Section **必须**是独立组件文件，**坚决不允许**把多个 Section 直接写进一个组件。

```text
article/
  Article.tsx          # assembler（主 Agent 拥有）：import + 排序各 Section
  sections/
    01-opening.tsx     # export function SectionOpening() { return <Section .../> }
    02-context.tsx
    03-mechanism.tsx
  raw-blocks/
    01-token-flow.tsx  # 大型 / 复用的 Raw 隔离到这里，被对应 section import
```

- 每个 `sections/NN-*.tsx` 导出一个组件，内部用 `<Section index="NN" title="...">…</Section>`。
- `Article.tsx` 只做组装：
  ```tsx
  import { Article, Hero, Lead, Conclusion } from "reacticle";
  import { SectionOpening } from "./sections/01-opening";
  import { SectionContext } from "./sections/02-context";
  export function ArticleDoc() {
    return (
      <Article toc width="regular">
        <Hero ... /><Lead>…</Lead>
        <SectionOpening />
        <SectionContext />
        <Conclusion>…</Conclusion>
      </Article>
    );
  }
  ```
- 文件级隔离 + reacticle 无裸 CSS（样式全走主题 token）→ 多个 Agent 改不同 section 文件
  **不会互相破坏**。

## 章节序号由主 Agent 统一编（避免序号错乱）

`Section` / `Subsection` 的 `index` 是**手写字符串**，组件既不自动编号、也不校验——它只会原样显示。
所以一旦哪个 section 文件写错了序号（典型：并行模式里 subagent 看不到自己在全篇的位置，凭空写出
"第 8 章下挂一个 5.1"），就会一路漏到成品里。规则：

- **全局序号归主 Agent（assembler）所有。** 在 `Article.tsx` 排定最终顺序后，主 Agent 据此把每个
  `Section` 的 `index` 校准成 `01 / 02 / 03 …`，并把每个 `Subsection` 的序号前缀对齐到所属
  `Section`（第 08 章下只能是 `8.1 / 8.2 …`）。
- **subagent 不自编全局序号。** 主 Agent 在派活时直接告诉它"你是第 `<NN>` 章"，subagent 用这个
  `<NN>` 写 `Section index` 和本节 `Subsection` 的前缀；拿不准就留 outline 给的占位，最终由主
  Agent 统一过一遍。
- **组装后必校验**：对照 TOC 显示与 `outline.md` 顺序，确认序号连续单调、子节前缀正确（并入终审
  Technical Reviewer 的"章节序号全篇自洽"清单）。

## 两种开发模式（Checkpoint 2 由用户选定）

第一个 Section 无论哪种模式都先由**主 Agent 完成并验收**（风格锚点）。差异在第 2 个 Section 起：

### A · 单 Agent 顺序（默认，最稳）

主 Agent 顺序写 `02 → 03 → …`，风格最统一，随时验收。

### B · 多 Agent 并行（最快）

subagent 各**拥有一个** `sections/NN-*.tsx` 并行开发。**主 Agent 负责合并与稳定性**：

- 维护 `Article.tsx` 的 import 与 Section 顺序（唯一组装点，避免冲突），并据最终顺序**统一校准每个
  Section 的 `index` 与各 Subsection 的序号前缀**（见上节"章节序号由主 Agent 统一编"）。
- 每轮并行结束跑 `npm run typecheck` + `npm run build`，修构建错误。
- 兜底主题与风格一致（颜色 / 字体 / 间距走 token，气质不跑偏）。
- 解决重复 / 衔接问题（相邻 section 论点是否承接）。

风格在并行下会有轻微差异（这是预期，主题 token 兜底视觉统一）。

### 并行 subagent 的 prompt 必须包含

```text
你负责文件 article/sections/<NN>-<id>.tsx，只改这一个文件，导出一个 Section 组件。
你是全篇第 <NN> 章（这个编号由主 Agent 指定，你看不到自己在全篇的位置，不要自己另编）。
读取：plan/plan.md 的 Outline 段本节段落 + Brief 段（信息保留比例）+
      source/source.md 本节对应内容 + 选定主题 theme-profiles/<id>.md +
      references/component-policy.md + references/raw-policy.md +
      第一个 section 文件作为“代码风格”参考（不是抄袭对象）。
硬规则：
- 一个文件 = 一个 Section 组件；不要碰 Article.tsx 或别的 section 文件。
- 正文为主体，组件按需（默认核心组件优先），Raw 用 --ra-* token 现写。
- 符合本节 outline 任务与信息保留比例；与前后节衔接。
- 序号：<Section index="<NN>">；本节所有 <Subsection> 的序号前缀必须等于 <NN>
  （如 <NN>=08 则小节是 8.1 / 8.2 …），不要从别的章节复制序号。
- 完工自检对照 references/review-checklist.md 的 Section 清单。
不要修改 Article.tsx（主 Agent 统一组装与序号校准），不要改主题。
```

## 每个 Section 完工（必走质检 · SubAgent · 消息返回）

按硬性质检协议创建 **Section Reviewer** SubAgent，对照清单核查：完成 outline 任务 / 符合
信息保留比例 / 与前后衔接 / 不过度组件化 / 正文充足 / Raw 与配图有明确目的 / **本节序号
自洽**（`Section index` 等于 `<NN>`，各 `Subsection` 序号前缀等于 `<NN>`）。

**SubAgent 以消息形式返回 pass/fail + 修复点**（pass 一行 OK，fail 列出修复点），**不要写
`review/section-NN-review.md` 文件**。主 Agent 收到 fail 项后直接修对应 section 文件，再
汇报本节交付。完整 prompt 模板见 `references/review-checklist.md` 的 Section 段。
