# 组件使用政策（reacticle 协议）

文章用 `reacticle` 组件协议写：**不手写裸 `div` / `className` / 行内 `style` / CSS**。
结构走语义组件，正文走段落，自定义视觉走 `Raw`。从包入口导入：

```tsx
import { ThemeProvider, Article, Hero, Lead, Section, Aside, Table, Raw } from "reacticle";
```

## 核心规则（始终适用）

1. **Prose-first，组件按需，Raw 自由。**
   - **正文是主体**：普通段落写成 `Section` 的 children，应占文章绝大部分。
   - **语义组件是点睛，只在内容确实"是"那个结构时才用**：`Summary` / `Aside` /
     `Quote` / `Table` / `RiskList` / `Decision` 等。不要堆叠当装饰 —— 堆卡片会让
     文章显得做作、零碎。litmus test：若一句话 / 一个列表 / 一张表 / 一块 Raw 读起来
     更好，就用那个。
   - **Raw 相反：鼓励多用。** 交互、动画、自定义可视化、新颖排版 —— Markdown 做不到的
     东西，才是把文章从"能读"变成"值得读"的关键。Raw 不打断阅读，它给密集文本节奏与
     呼吸。
2. **表达语义，不表达布局。** 说"这是 insight / risk / decision"，别说"蓝卡片、24px 边距"。
3. **Props 即协议。** 填齐必填字段；确实没有就留空 —— 组件会渲染显式的 `⚠ 未指定xxx`
   标记，让缺口可见。**绝不为掩盖缺口而编造。**
4. **主题，不写样式。** 作者只通过 `ThemeProvider` 选一个主题，从不写组件样式。
5. **始终用 `<ThemeProvider theme="...">` 包住 `<Article>`。**
6. **版式与主题解耦。** `Article` 的 `width`（`narrow` / `regular` / `wide` / `full`，默认
   `regular`）决定阅读列宽，`toc`（默认在本 Skill 开启）决定是否有左侧目录 —— 都按内容选、
   经 Plan Checkpoint 确认，**不由主题决定**。详见 `references/layout.md`。
7. **一个 Section = 一个文件。** 每个 Section 必须是独立组件（`article/sections/NN-*.tsx`），
   **坚决不允许**把多个 Section 写进一个组件；`Article.tsx` 只做组装（assembler）。这是
   多 Agent 并行开发的前提，详见 `references/section-build.md`。

## 组件分两层：默认核心 + 领域特例

**默认核心组件（绝大多数文章只用这些 + 正文 + Raw）：**

- 结构：`Article`、`Hero`、`Lead`、`Section`、`Subsection`、`Conclusion`、`TOC`
- 观点：`Summary`、`Aside`、`Quote`
- 数据：`Table`
- 技术：`CodeBlock`（写代码**只用它**）、`Formula`
- 媒体：`Image`
- 自由层：`Raw`

**领域特例组件（仅当内容"确实是"该结构时按需取用，不要因为属于某类文章就全用上）：**

- 决策 / 审阅：`RiskList`、`Decision`、`ActionList`、`Checkpoint`、`Tradeoff`、`Incident`
- 代码评审：`DiffReview`
- 交互壳：`Detail`、`Tabs`
- 富媒体：`Video`、`Audio`

> **不要暴露给作者**：`HighlightedCode` 是 `CodeBlock` 的内部底层，写代码一律用
> `CodeBlock`，不直接使用 `HighlightedCode`。

选组件前先过 litmus test（规则 1）：若正文 / 列表 / 表格 / Raw 读起来更好，就不要为了
用组件而用组件。领域特例组件每多用一个，都要能回答"这块内容本质上就是它"。

完整组件 API（属性、用法）见组件库本身的 reference：
`skill/references/{structure,insight,structured,decision,technical}.md`（reacticle-authoring
skill），按需读取，不要一次全读。

## 使用原则

- 正文是主体。组件是语义，不是装饰。
- Raw 是文章表现力，不是应用开发入口（边界见 `raw-policy.md`）。
- `Table` 负责二维信息；`Image` 负责真实或生成配图；`Raw` 是自由的 Web 层 —— 任意
  HTML / CSS / JS / React：交互、自定义布局排版、动效、嵌入小工具，以及按需的图解（SVG /
  canvas），SVG 只是其中一种手段，不是默认。
- **`Raw` 与 `Image` 正交，不是二选一**：`Raw` 始终默认存在、照常使用；`Image` 是否使用、
  用哪种来源由 Plan Checkpoint 的配图策略决定（见 `references/asset-policy.md`）。选配图
  `none` 只表示不用外部图片，`Raw` 不受影响。

## 信息密度与组件比例

见 `information-density.md`：100% 时长文优先、Raw 点亮关键概念；密度越低，视觉块比例
越高，但**仍必须保持文章形态**。

## 最小骨架（注意比例：大量正文 + 一个点睛组件 + 一块 Raw）

```tsx
import { ThemeProvider, Article, Hero, Lead, Section, Aside, Raw } from "reacticle";

export function Article_() {
  return (
    <ThemeProvider theme="tufte">
      <Article>
        <Hero title="标题" subtitle="副标题" meta={[{ label: "日期", value: "2026-06-08" }]} />
        <Lead>导语，框定主题。</Lead>
        <Section index="01" title="第一节">
          <p>正文段落用 children —— 这应是文章主体，尽量多写正文。</p>
          <p>再写一段，把背景、推理、结论用文字讲清楚。</p>
          <Aside tone="principle" label="核心判断">一句话的核心判断。</Aside>
          <Raw title="为本段现写的内联 SVG">
            <svg viewBox="0 0 240 60" width="100%">
              <polyline points="0,50 40,42 80,46 120,20 160,28 200,8 240,14"
                fill="none" stroke="var(--ra-color-accent)" strokeWidth="2" />
            </svg>
          </Raw>
        </Section>
      </Article>
    </ThemeProvider>
  );
}
```
