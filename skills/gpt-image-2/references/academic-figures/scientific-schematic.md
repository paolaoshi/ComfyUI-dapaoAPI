# 概念 / 原理示意图模板

本文件用于生成"科学概念 / 原理 / 实验装置"示意图：

- 物理 / 化学 / 生物 实验装置图
- 算法 / 数学 概念示意（如 attention 机制、流形、坐标系）
- 机制 / 通路 / 过程示意（细胞通路、化学反应）
- 教科书风原理图
- Nature / Science 综述里的"我们这个领域大概是这样工作的"概念图

特征：

- **自由度极高**：每张科学示意图都长得不一样，不像 pipeline / network 那样可被网格化
- 极简白底 / 浅灰底
- 几何精确：标尺 / 坐标轴 / 角度对齐
- 简化但非卡通的风格（科学严谨）
- 标注线 + 编号 + 公式
- 出版物字体（Helvetica / Inter / Computer Modern 数学公式）

> 设计判断：**这类图自由度极高、变化丰富，强行 JSON 反而限制构图**。本模板采用「**结构化自然语言提示词 + 关键参数 + 示例**」的混合形式，把控约束但不锁死构图。

## 适用范围

- 实验装置示意（光学 / 力学 / 流体 / 化学反应器）
- 生物机制 / 通路 / 解剖示意
- 算法 / 数学概念可视化（attention / convex set / manifold / 坐标变换）
- 物理过程示意（波 / 场 / 粒子轨迹）
- 综述论文里"领域 big picture"概念图

## 何时使用

- 用户提到 "schematic / illustration / 示意图 / 原理图 / 实验装置 / 机制图 / Nature 风 / 教科书风"
- 用户希望"自由构图、白底、几何精确、有学术感"
- 用户的内容是「单一概念 / 单一装置 / 单一机制」而非「pipeline / 网络 / 多方法」

不要使用：

- 用户要的是「方法 pipeline」（多 stage 流）→ 用 `academic-figures/method-pipeline-overview.md`
- 用户要的是「神经网络架构」 → 用 `academic-figures/neural-network-architecture.md`
- 用户要的是「数据图表」 → 用 `academic-figures/publication-chart.md`
- 用户要的是「手绘卡通示意」 → 用 `infographics/hand-drawn-infographic.md`
- 用户要的是「儿童科普」 → 用 `scenes-and-illustrations/picture-book-scene.md`

## 缺失信息优先提问顺序

1. 要解释什么概念 / 装置 / 机制？（一句话定义）
2. 主体是什么？（中央那个核心实体——分子 / 细胞 / 透镜 / 反应器 / 矩阵 / ...）
3. 配套元素？（标注线 / 公式 / 坐标 / 参数）
4. 风格倾向（Nature 综述风 / 教科书风 / 顶会论文严肃风 / BioRender 友好风）
5. 是否需要数学公式标注？需要的话哪些？
6. 是否中英文（默认英文）
7. 比例（论文常用 1:1、4:3、16:9）

## 主模板：科学概念 / 原理示意图（自然语言结构化）

📖 描述

整张图围绕一个中心概念 / 装置 / 机制展开，用极简几何元素 + 标注线 + 公式 + 简洁辅助色构成，达到出版物级的清晰度和严谨感。

📝 提示词（结构化自然语言模板）

```
A scientific schematic illustration in the style of {argument name="reference_style" default="a Nature / Science methods figure"}.

CORE CONCEPT
The figure illustrates: {argument name="core_concept" default="how cross-attention works between a query sequence and a key/value sequence"}.

CENTRAL SUBJECT
The visual centerpiece is {argument name="central_subject" default="a 2D matrix grid representing query × key dot products, with arrows feeding in queries from the left and keys from the top"}.

SUPPORTING ELEMENTS
{argument name="supporting_elements" default="(1) a softmax curve diagram on the right showing how raw scores become attention weights; (2) a small inset showing the resulting weighted sum producing the output"}.

Each supporting element is positioned with deliberate spacing and connected to the central subject by thin labeled arrows or leader lines.

ANNOTATIONS
- Use leader lines (thin black, no arrowheads or tiny arrowheads) to label specific parts of the central subject.
- Each label is in {argument name="label_font" default="11pt sans-serif (Helvetica / Inter / Arial)"}.
- {argument name="annotation_count" default="4-6"} labels total — do NOT overcrowd.
- Use lowercase italic letters (a, b, c) for sub-figure labels in the top-left of each panel.

EQUATIONS
{argument name="equations_list" default="Show one or two key equations near the relevant region. Use Computer Modern / serif math font, italic variables. Example: Attn(Q,K,V) = softmax(QK^T / √d_k) V"}

Equations should be small but readable, placed adjacent to the part of the figure they explain (not floating in the corner).

COLOR PALETTE
- Limit total to {argument name="color_count" default="3-4"} muted, academic colors:
  - {argument name="primary_color" default="deep blue #1E3A8A"} — for the central subject
  - {argument name="secondary_color" default="warm orange #D97706"} — for the highlighted / contrasting flow
  - {argument name="neutral_color" default="medium gray #475569"} — for annotation lines and supporting structures
  - white background, near-white shading for sub-regions
- The figure must remain readable when printed in grayscale: rely on shape and labels, not color alone.

LAYOUT
- {argument name="layout_style" default="single-panel, central subject occupies ~60% of the canvas, supporting elements arranged around it"}.
- Generous whitespace (~25% of canvas), rigorous alignment to an invisible grid.
- Aspect ratio: {argument name="aspect_ratio" default="4:3"}.

STYLE ENFORCEMENT
- Crisp vector-clean lines (no anti-aliasing artifacts, no jitter)
- All shapes are geometrically precise (perfect circles, exact angles)
- All text typeset, NEVER hand-drawn lettering
- Background pure white #FFFFFF or very light gray
- NO 3D extrusion, NO drop shadow, NO gradient fill, NO glossy highlight
- NO cartoon characters, NO emoji, NO decorative ornaments
- Should look like it was generated with TikZ / Inkscape / Adobe Illustrator for a peer-reviewed publication

CAPTION (optional, drawn below figure)
{argument name="caption_text" default="Figure 2. Illustration of the cross-attention mechanism. Queries (Q) attend to keys (K) via scaled dot-product, producing attention weights that aggregate values (V)."}
```

### 参数策略

- **必问**：`core_concept`、`central_subject` 至少一句话描述
- **可默认**：`reference_style`（Nature methods 风）、`color_count`（3-4）、配色三件套（深蓝 + 橙 + 灰）、`label_font`、`aspect_ratio`
- **可随机**：annotation 摆放角度、leader line 走向（应避开关键内容）、equations 是否启用

### 自动补全策略

- 用户给"我要画 attention 机制示意图"但没说细节 → 自动用 default 给出 cross-attention 示意，问用户是否还需要 self-attention 单独一张
- 用户给"光学双缝干涉实验" → central_subject = 双缝挡板 + 屏幕 + 入射光，supporting = 干涉条纹小图 + 公式 d sinθ = mλ
- 用户给"细胞 receptor 信号通路" → 用 BioRender 友好风：圆角细胞膜 + 受体 + 配体 + 内部信号链
- 用户没给 reference_style：根据领域猜——CV/ML 用 "顶会论文风"；生物用 "BioRender / Nature methods 风"；物理用 "教科书 + 公式风"
- 用户说"我要无英文，全中文" → 切换 label_font 为思源黑 / 宋体 + 公式保留 LaTeX 数学体

## 变体 1：实验装置示意图（光学 / 化学）

```
Modify the main template:

CENTRAL SUBJECT
A precise schematic of an experimental apparatus, drawn in side view (orthographic projection).

LAYOUT
- Equipment components arranged from left to right along the optical / fluid path:
  light source / reactant inlet → first optical / chemical element → second element → ... → detector / outlet
- Components shown as simplified geometric primitives:
  - Lasers / lamps: small box with arrows indicating beam direction
  - Lenses: standard biconvex / planoconvex symbol (two arcs)
  - Mirrors: thin angled lines with hatching on the back
  - Reactors: round-bottom flask outline
  - Detectors: rectangular box with diagonal corner stripes
- Beam / fluid path drawn as a thin colored line (e.g. red for light, blue for fluid)

ANNOTATIONS
- Each component labeled with its role and (if relevant) a parameter (e.g. f = 50mm, λ = 532nm)
- Arrows show direction of light / flow

VIBE
Like a JOSA / Optics Letters experimental setup figure, or like a chemistry textbook reaction apparatus.
```

适用：光学实验、化学反应装置、流体 / 力学装置、半导体制造流程示意。

## 变体 2：生物 / 医学机制示意（BioRender 风）

```
Modify the main template:

CENTRAL SUBJECT
A simplified biological structure (cell membrane / cell / tissue / organ / molecule).

STYLE
- BioRender-friendly: rounded organic shapes, slightly stylized but anatomically reasonable
- Color-coded biology palette: warm membrane (peach / coral), cool nucleus / organelles (blue / purple), bright signaling molecules (yellow / green)
- 3D suggestion via subtle shading (single-direction soft shading, no harsh highlights)

ANNOTATIONS
- Each structure labeled with its biological name (italic Latin / standard nomenclature)
- Signaling pathways drawn as arrows with mechanism keywords ("phosphorylation", "binding", "translocation")
- If multi-step, number each step and provide a brief side caption

VIBE
Like a Cell / Nature review pathway figure, balanced between scientific accuracy and visual approachability.
```

适用：分子生物学通路、细胞机制、解剖示意、药物作用机制。

## 变体 3：数学 / 算法概念可视化

```
Modify the main template:

CENTRAL SUBJECT
A mathematical / algorithmic concept rendered as geometry:
- vectors as arrows, matrices as grids, functions as curves, manifolds as surfaces
- coordinate systems with labeled axes (x, y, z), origin marked

STYLE
- Clean TikZ / Asymptote aesthetic
- Heavy use of LaTeX-rendered equations integrated into the figure
- Greek letters and mathematical symbols throughout
- Sparingly use color — usually 2 colors (black + one accent) to highlight what's being discussed

ANNOTATIONS
- Equation snippets next to relevant geometry
- Brief textual descriptions on the side ("optimal transport plan minimizes ...")
- Sub-figure labels (a), (b), (c) for multi-panel concept figures

VIBE
Like a figure from "Convex Optimization" by Boyd, or from a SIGGRAPH technical paper.
```

适用：优化理论、几何 / 拓扑、概率分布、信号处理、计算机图形数学基础。

## 避免事项

- 卡通化、夸张化的元素 → 失去科学严谨感
- 渐变 / 玻璃质感 / drop shadow → 像 PPT 不像论文
- 颜色超过 4 种 / 高饱和 / 霓虹色
- 公式用非数学字体（必须斜体变量 + serif 数学体）
- 中英文混排（除非显式双语）
- 装饰性背景纹理 / 图案
- 标注线穿过主体 / 标签碰撞
- 用 emoji 当生物 / 化学元素图标
- 多个互不相关概念塞在一张图（应拆分）
- 模糊或低分辨率（论文图必须矢量级清晰）
- 自由手绘风的"草图感" → 用 `infographics/hand-drawn-infographic.md` 才对，本模板必须几何精确
