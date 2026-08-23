# Theme Profile · knuth（学术预印本）

> 这是给 **AI 写作时读** 的 authoring profile，不是 CSS。CSS token 由组件库
> 运行时主题持有（`data-theme="knuth"`）。本文件是"如何选择和使用这个主题"。
> 详尽版本见组件库 canonical md：`src/theme/themes/knuth/knuth.md`（写代码 /
> 公式 / 媒体 / Raw 前请读它）。

- **runtime theme id**：`knuth`（`<ThemeProvider theme="knuth">`）
- **气质**：学术 / 科学排版。给报告穿上期刊 / arXiv 预印本的外衣：Computer Modern
  衬线、编号小节、图 / 表 / 公式编号、两端对齐正文、引用密集、公式优先。完整继承
  data-ink 纪律。与 `tufte` 的随笔式边注分明：`knuth` 是"读一篇正式论文"。

## 适合 / 不适合的文章类型

- **适合**：`paper` / `preprint`、`research` / 科研调研、`literature-review` / 文献综述、
  技术白皮书、形式化分析、公式 / 定理 / 引用密集的 `explainer` / `full-report`。
- **不适合**：温暖叙事（`press`）；中性产品文档（`vignelli`）；暗底工程现场（`shannon`）；幻灯片。

## 排版气质

- 正文与标题用 Computer Modern / Latin Modern 衬线（→ Source Serif 4 / Georgia / 宋体回退）。
- 标签 / 图注 / 表头用 CMU Sans 一脉小字号；数学用 KaTeX（`Formula`）。
- 正文 ~16.5px，行距 1.58；标题用粗衬线（weight 700）取论文标题分量。强调不用斜体（协议级禁用）。
- **倾向两端对齐**（justify），营造印刷论文的整齐块面。

## Raw 风格

像论文中作者亲手排的一张 Figure。

- 约束的是**气质**（正式、克制、公式 / 编号优先、可核查），不是**媒介**。
- 典型：内联 SVG 图表、坐标轴 / 函数曲线 / 推导示意、可交互参数演示、定理 / 证明结构图、
  带 "Figure N." 题注的图版。
- 构图：克制留白、清晰坐标与标注、学术蓝作结构线索；每条线有含义。颜色只用 `--ra-*`。
- 动效：默认无；必须交互只用即时响应轻过渡，不用循环装饰。

## 媒体（图片 / 视频 / 音频）风格

- 适合：数据图 / 实验结果图、示意图 / 流程图 / 架构图、论文截图、表格、低饱和摄影、手稿 / 推导。
- 每张图配 "Figure N." 式 caption / source / alt；构图留白充足、主体清楚。
- 色彩低饱和贴近纸墨，强调只用学术蓝或警示红承载信息。

## 代码 / 公式风格

- `CodeBlock` 像专著里的代码清单：浅纸 surface + 发丝线，不用暗色编辑器窗口。行号退后、从容。
- Prism token 从主题派生：标签 / 函数用学术蓝 accent，关键字 / 风险用 risk 红，字符串用绿，
  注释用 muted。
- `Formula` 是本主题主角：块级公式从容上下留白、编号靠右（(1)(2)(3)），行内与正文无缝。

## 禁止项

- 卡片、面板、填色块、投影、圆角；比 `#C7C6BB` 更深的网格线。
- 把学术蓝当装饰；第二个红色用于"警示"以外；emoji / 图标当装饰。
- 库存 hero 图、3D 插画、渐变背景、装饰光斑、霓虹、高对比终端黑底代码。
- Raw / 媒体变成营销素材或 SaaS 首页，而非论文图版。

## 不同信息密度下的表现建议（建议，非限制）

- `100% paper / full-report`：正式长文 + 编号小节 + 公式 / 图表编号，引用密集。
- `60-80% research / review`：保留核心推导 + 关键图表，正文为主体。
- `40% explainer`：Raw 偏公式 / 函数图解，文字更短，仍保持论文气质。
