# 版式：宽度模式与 TOC

版式是**与主题解耦的独立决策**（主题只管审美气质，宽度/目录管阅读版式），就像信息密度
与主题解耦一样。在 Plan Checkpoint（Phase 3）由用户确认，落盘到 `plan/plan.md` 的 Brief 段。

## 宽度模式（`Article` 的 `width`，需 reacticle ≥ 0.2.0）

宽度由 `<Article width="...">` 控制，**不再由主题决定**。四种常见模式：

| 模式 | 阅读列宽 | 适合 |
|---|---|---|
| `narrow` | ~34rem | 聚焦短文、`essay`、`briefing`、金句节奏强的文章 |
| `regular`（默认） | ~46rem | `longform` / `explainer` 等常规长文阅读 |
| `wide` | ~58rem | 表格 / 代码 / 数据密集（`full-report`、`review`、`tutorial`） |
| `full` | ~78rem | 图文主导、宽幅媒体（`visual-essay`） |

任意主题都能配任意宽度（解耦）。例：`tufte + wide` 适合大量数据表；`press + narrow`
适合从容随笔。

## TOC（`Article` 的 `toc`）

`<Article toc>` 渲染左侧目录（从 `Section` / `Subsection` 自动派生，最多三级，带滚动高亮）。

- **本 Skill 默认开启 TOC**（长文有导航更易读），但**必须在 Plan Checkpoint 让用户确认**。
- 很短的文章（`briefing` / 短 `visual-essay`）可以关掉，避免目录比正文还显眼。
- TOC 开启会变成"左目录 + 正文"两栏；窄视口（<1000px）自动回落为单栏。

## 用法

```tsx
// 默认：常规宽度 + 开 TOC
<Article toc width="regular"> ... </Article>

// 数据密集报告：更宽 + TOC
<Article toc width="wide"> ... </Article>

// 短随笔：窄列、不要目录
<Article width="narrow"> ... </Article>
```

## 自检

- 宽度是否匹配内容？（表格 / 代码多 → 至少 `wide`；纯叙事 → `regular` / `narrow`）
- 宽度是按内容选的，而不是被主题决定的？
- TOC 的开关是否经用户确认？短文是否误开了喧宾夺主的目录？
- 移动端两栏是否正常回落为单栏？
