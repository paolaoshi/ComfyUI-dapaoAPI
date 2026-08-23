# 文章类型路由

文章类型是**结构决策**，主题是**审美决策**（见 `theme-selection.md`）—— 两者完全解耦。

**文章类型与信息保留比例的关系**（重要）：理论上"内容保留是独立决策"，**但实践中两者
绑定很紧**。每个类型都自带一个标配保留比例（见下表"推荐信息保留"列）。`longform + 20%` /
`tutorial + 20%` / `briefing + 100%` 这类组合是**伪选项**：要么类型变形（briefing+100%≈full-report），
要么内容空洞（longform 写出 8 章每章 2 段）。所以 Plan Checkpoint 1 把"保留比例"打包进"文章
类型"的语义化选项里（见 SKILL.md Phase 3），**只在用户明确想精修**（如"longform 但只要 60%"
= 一篇被深度编辑的长文）才作为非标配组合记入 plan.md。

Phase 2 选定类型后，读对应 `article-types/<type>.md` 拿结构 / 组件 / Raw 边界 / 配图倾向 /
自检。**非标配组合**要在 `plan/plan.md` Brief 段同时记下"标配 X% → 用户覆盖 Y%"，并让主 Agent
在写每节时手动调整正文/视觉比例（不能照搬 article-types/<type>.md 的默认建议）。

| 类型 | 推荐信息保留 | 用途 | 典型结构 | 详情 |
|---|---|---|---|---|
| `longform` | 100% | 完整长文、归档、深度阅读 | Hero / Lead / Summary / 多 Section / Raw 增强 / Conclusion | `article-types/longform.md` |
| `full-report` | 80% | 研究报告、正式分析 | 执行摘要 / 背景 / 证据 / 数据 / 风险 / 结论 | `article-types/full-report.md` |
| `tutorial` | 80-100% | 教学、步骤、上手 | 目标 / 步骤 / 示例 / 练习 / 总结 | `article-types/tutorial.md` |
| `explainer` | 80% | 解释技术、系统、概念 | 问题 / 机制 / 图解 / 示例 / 常见误区 | `article-types/explainer.md` |
| `dialogue` | 80% | 对话 / Q&A / 访谈 / 播客 / AMA | Hero / 嘉宾 / 多话题 Section / 关键观点摘要 | `article-types/dialogue.md` |
| `review` | 60-80% | PR / 方案 / 事故 / 设计审阅 | 背景 / 发现 / 影响 / 建议 / 行动 | `article-types/review.md` |
| `essay` | 60-80% | 观点、评论、叙事 | 开场 / 论点 / 例证 / 转折 / 收束 | `article-types/essay.md` |
| `briefing` | 40-60% | 给忙人快速判断 | 结论先行 / 关键证据 / 取舍 / 下一步 | `article-types/briefing.md` |
| `interactive-explainer` | ~25%（原文摘录占比，**非删 75%**） | **Raw 交互为主载体的"会用了再走"式学习页**（参考 3blue1brown / distill.pub / ciechanow.ski）。本质是**内容重构**：只摘核心知识点，其余 AI 围绕它们全新创作 | 每知识点：定义 / 交互演示 / 自己试 / 验证理解 | `article-types/interactive-explainer.md` |
| `visual-essay` | 20-60% | 展示、传播、图文主导 | 少文字 / 大视觉 / 强节奏 / 章节短 | `article-types/visual-essay.md` |

## 选型提示

- 源材料信息密度高、要完整归档 → `longform`。
- 源材料是消化后的报告 / 正式分析（执行摘要 + 数据 + 风险 + 建议四件套）→ `full-report`。
- 要把一个机制 / 概念讲清楚（正文为主）→ `explainer`。
- **要让读者"玩明白"一个概念**（Raw 交互为主，正文为辅，每知识点配交互演示）→ `interactive-explainer`。
- 对话 / Q&A / 访谈 / 播客转录 / AMA → `dialogue`。
- 评审某个 **工程** PR / 方案 / 事故 / 设计 → `review`。
- 给决策者快速判断 → `briefing`。
- 观点输出 / 评论 / 产品 / 书 / 论文评测 → `essay`。
- 教别人上手做事（步骤 + 跑通）→ `tutorial`。
- 传播 / 展示、图文主导 → `visual-essay`。

类型只定**结构倾向**，不锁死信息密度和主题；用户可在 Plan Checkpoint 覆盖。
