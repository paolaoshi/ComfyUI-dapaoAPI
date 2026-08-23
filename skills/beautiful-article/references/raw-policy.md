# Raw 政策

Raw 是 Beautiful Article 的关键表现力，但必须受**主题**和**文章性**约束。写 Raw 前先读
选定主题的 `theme-profiles/<id>.md` 的 Raw 风格。

## Raw 是完整的 Web 平台，不是"画 SVG"

**Raw 里可以写任意 HTML / CSS / JS / React 组件 —— 整个 Web 平台都在你手里。** SVG 只是
**其中一种**手段，绝不是默认或唯一。别把 Raw 想成"内联画图"，那会严重限制网页的想象力。
按"哪种媒介最能讲清这一段"自由选择，例如：

- **交互**：拖动条 / 切换 / 折叠 / 步进器 / 计算器 / 小型可调模型 / 假设演算。
- **布局排版**：并排对比、时间线、卡片网格、分栏、引文大字、特殊标题节奏（用 HTML + CSS）。
- **动效**：CSS transition / `@keyframes` / 滚动揭示 / 状态切换的动画。
- **数据可视**：HTML/CSS 条形与热度、`<canvas>`、需要时才用 `<svg>` 折线 / slopegraph。
- **嵌入与组合**：表格 + 控件 + 文本拼成的一次性小工具、可复制片段、对照面板。

判断只问一句：**哪种实现最能服务这一段的理解 / 论证 / 节奏？** 用那个，而不是反射性地画 SVG。

## 核心心法

- **为 THIS 篇文章手写，不是 widget 库。** 每块 Raw 都应为它旁边的段落即时发明：写 token
  成本？现写一个小拖动条；写两套方案？拼一个并排对照面板；写体积趋势？才考虑一条内联折线。
  **绝不**把 Raw 做成一套固定小组件在文章间复用（同一条 pipeline / 同一套配色到处出现）——
  那等于把自由层退化成又一组受限组件。
- **自由但一致：用 token。** Raw 内部随便写 —— 任意 HTML / React 组件、`<style>` 与
  `@keyframes`、行内样式、`<canvas>`、按需的 `<svg>`、一次性小交互 —— 但颜色 / 字体 / 间距
  必须取自主题变量（`var(--ra-color-accent)`、`var(--ra-font-body)`、`var(--ra-space-4)` …），
  这样每块都独一无二却又随主题切换。

## 允许

- 任意服务段落的 HTML / CSS / JS / React：轻量交互解释、可调小工具、自定义布局与排版、
  并排对比、概念动效、阅读节奏中的视觉停顿，以及按需的 SVG / canvas 图解 —— 都是
  为当前段落定制的一次性实现。

## 禁止

- 复杂表单、拖拽工作台、完整 dashboard、产品原型、和文章无关的动画、独立于主题的配色、
  复用固定小组件冒充自由表达。

## Raw by example（每次现写，别复用固定 widget）

> 下面只是几种常见手段（SVG / CSS 动画 / React 交互），**不是穷举也不是优先级**。布局、
> 排版、对照面板、`<canvas>`、嵌入式小工具同样都行 —— 按"最能讲清这一段"来选。

```tsx
// 1) 需要曲线时，才为这个数据点手画一条内联 SVG（不是默认手段）
<Raw title="构建体积走势">
  <svg viewBox="0 0 300 80" width="100%">
    <polyline points={pts} fill="none" stroke="var(--ra-color-accent)" strokeWidth="2" />
  </svg>
</Raw>

// 2) 带一次性 CSS / @keyframes 的 HTML 字符串（内联进产物）
<Raw html={`
  <style>@keyframes ra-rise{from{height:0}to{height:var(--h)}}</style>
  <div style="display:flex;gap:8px;align-items:flex-end;height:80px">
    <i style="--h:60%;flex:1;background:var(--ra-color-accent);animation:ra-rise .6s ease"></i>
    <i style="--h:90%;flex:1;background:var(--ra-color-accent);animation:ra-rise .8s ease"></i>
  </div>
`} />

// 3) 只为这篇文章定义的一个小交互组件
function TokenScale() {
  const [n, setN] = useState(50);
  return (
    <div>
      <input type="range" value={n} onChange={(e) => setN(+e.target.value)} />
      <span style={{ color: "var(--ra-color-accent)" }}>{n}%</span>
    </div>
  );
}
<Raw title="拖动感受差距"><TokenScale /></Raw>
```

整篇文章里变化这些 —— 不同媒介、不同布局、不同交互 —— 让没有两块 Raw 看起来一样。变化是好的，违反
主题气质不行：`tufte` 的 Raw 不该变成发亮营销 dashboard，`press` 的 Raw 不该变成冷霓虹终端
（除非主题 md 明确允许）。

## Raw 自检

- 这块 Raw 删掉后，文章理解是否会变差？
- 它服务哪一个段落 / 论点？
- 它是否使用 `--ra-*` token？是否符合主题 md？
- 它是否让文章更像应用？（如果是，砍掉或收敛成服务阅读的解释性视觉 / 排版）
