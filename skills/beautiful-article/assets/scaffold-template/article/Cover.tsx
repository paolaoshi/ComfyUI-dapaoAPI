// Cover.tsx —— 文章封面（独立于 Article，位于 TOC + 正文 + colophon 之上）
//
// 这一文件是 article-specific 的（跟 Article.tsx / sections/*.tsx 同等地位）。
// 主 Agent 在 Phase 4 First Spread 把下面的【封面内容区】替换成按 **主题 + 文章主旨**
// 定制的设计。**外壳（3:4 比例、定位、PDF 分页）不要动**。
//
// 硬约束（详见 references/cover.md）：
//   1. **3:4 比例固定（屏幕 + PDF）**：不要改 aspectRatio；打印时 .ra-cover 会自动
//      独占首页，保持屏幕版 3:4 构图以避免 Chromium print 裁切内部布局。
//      让内部元素用百分比 / aspect-ratio / inset 自适应，不要写绝对 px 高度。
//   2. **图文并茂**：必须有视觉元素 + 简短文字（标题 + 可选副题 / 小标签）。
//      **禁止纯文字封面**。视觉用什么技术由你选（见约束 5）。
//   3. **主题忠实**：颜色 / 字号 / 字重 / 边框 / 律动**只能用 `--ra-*` token**。
//      切主题时封面要跟随刷新；不要写死颜色 / 字体名 / 像素字号。
//   4. **内容忠实**：封面的视觉主图与文字要呼应正文主旨（看一眼能猜出文章是讲什么的）。
//   5. **技术自由**：内联 SVG / CSS 几何 / Canvas / 复杂 React 组件 / 字体艺术 / 多层
//      gradient / mask / clip-path / 任意组合 —— 任选，最终效果好就行。**唯一禁止**：
//      远程图片（offline-first）；base64 raster 仅当 Plan Checkpoint "配图模式" 是
//      user-assets / ai-generated 才允许。
//   6. **封面不承担正文**：不要把 Lead 第一段、TOC、阅读时间塞进来 —— 封面只承担
//      "识别 + 风格信号 + 引起阅读欲望"，正文从下面的 Article 开始。

export function Cover() {
  return (
    <section
      className="ra-cover"
      aria-label="文章封面"
      data-ra-cover=""
      style={{
        // ── 外壳（请不要动） ──
        position: "relative",
        width: "100%",
        // 屏幕上像"一本立着的书"：限宽 48rem（768px）；同时**从视口高度反推宽度**
        // (100vh - 8rem) * 3/4，确保整个 3:4 封面**一屏看全、不用下拉**。8rem
        // (128px) 给顶栏 / 边距 / site nav 等留出充足呼吸（典型场景 site nav 60 +
        // 容器顶 padding 32 + 边框 1 ≈ 93px，仍有 35px 余量）。
        // 3:4 比例由 aspect-ratio 保证不破。
        maxWidth: "min(100%, 48rem, calc((100vh - 8rem) * 3 / 4))",
        margin: "0 auto var(--ra-space-7, 3rem) auto",
        aspectRatio: "3 / 4",
        overflow: "hidden",
        // 背景透明：让外层 .ra-root / .gx-reader 的 --ra-color-bg "纸面色" 直接透上来。
        // 整片视觉是一张连续的纸，封面不再"自带一块色"。封面的辨识度由内部插画 + 边框
        // + 内容排版承担。如果你的封面**确实需要**整体着色（如孟菲斯主题大色块覆盖），
        // 可以改成 surface / surface-2 / accent-soft 等任意主题 token。
        background: "transparent",
        color: "var(--ra-color-fg, inherit)",
        borderRadius: "var(--ra-radius-md, 0)",
        border: "1px solid var(--ra-color-border, currentColor)",
        // 让 ::before 之类的几何装饰可以铺满
        isolation: "isolate",
      }}
    >
      {/*
        ─── 封面内容区 · 在这里写 ───
        默认占位长这样：
          • 一层主题感的几何装饰（SVG 网格 + 一个 accent 圆 + 描边斜线）
          • 居中的占位标题、副题、小标签
        构建时**替换为按文章 + 主题定制的封面**。占位是为了
        "即使忘了替换，也不会渲染出一团乱"，但**不能交付出去**。
      */}
      <CoverPlaceholder />
    </section>
  );
}

// ────────────────────────────────────────────────────────────────────
// 占位实现 —— 主 Agent 把 <CoverPlaceholder /> 替换成本文真正的封面。
// 删掉这个 function 也行；保留它能让占位回退更友好。
// ────────────────────────────────────────────────────────────────────
function CoverPlaceholder() {
  return (
    <>
      {/* 默认占位用了 SVG 是图省事，**不代表"应该用 SVG"** —— 你完全可以删掉这个
       *  <svg>，换成 CSS 渐变层、Canvas、复杂 React 组件、字体艺术拼贴等任何能产生
       *  漂亮视觉的方式。视觉技术由你选，效果好就行。 */}
      <svg
        viewBox="0 0 1200 1600"
        preserveAspectRatio="xMidYMid slice"
        aria-hidden="true"
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          color: "var(--ra-color-border, currentColor)",
          opacity: 0.55,
          zIndex: 0,
        }}
      >
        <defs>
          <pattern id="ra-cover-grid" width="80" height="80" patternUnits="userSpaceOnUse">
            <path
              d="M 80 0 L 0 0 0 80"
              fill="none"
              stroke="currentColor"
              strokeWidth="0.6"
            />
          </pattern>
        </defs>
        <rect width="1200" height="1600" fill="url(#ra-cover-grid)" />
        <circle
          cx="900"
          cy="1180"
          r="220"
          fill="var(--ra-color-accent, currentColor)"
          opacity="0.18"
        />
        <line
          x1="80"
          y1="1400"
          x2="560"
          y2="1400"
          stroke="currentColor"
          strokeWidth="2"
        />
      </svg>

      {/* 文字层 */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          zIndex: 1,
          display: "grid",
          alignContent: "center",
          justifyItems: "start",
          padding:
            "var(--ra-space-7, 3rem) var(--ra-space-8, 4rem) var(--ra-space-7, 3rem) var(--ra-space-8, 4rem)",
          gap: "var(--ra-space-3, 0.75rem)",
        }}
      >
        <span
          style={{
            fontSize: "var(--ra-text-xs, 0.75rem)",
            letterSpacing: "0.22em",
            textTransform: "uppercase",
            color: "var(--ra-color-muted, inherit)",
            opacity: 0.85,
          }}
        >
          COVER · 3 : 4 · 占位
        </span>
        <h1
          style={{
            margin: 0,
            fontSize: "clamp(1.6rem, 4.6vw, var(--ra-text-4xl, 3rem))",
            lineHeight: 1.05,
            fontWeight: "var(--ra-font-weight-bold, 700)",
            color: "var(--ra-color-fg, inherit)",
            maxWidth: "70%",
          }}
        >
          按文章主旨 + 主题，在此处设计封面
        </h1>
        <p
          style={{
            margin: 0,
            fontSize: "var(--ra-text-sm, 0.95rem)",
            color: "var(--ra-color-muted, inherit)",
            maxWidth: "70%",
            lineHeight: 1.4,
          }}
        >
          先读 <code>references/cover.md</code> 与选定主题的 <code>theme-profiles/&lt;id&gt;.md</code>，
          再替换 <code>CoverPlaceholder</code> 为本文专属的图文构图。视觉用什么技术（SVG /
          CSS / Canvas / 复杂 React 组件 / 任意混搭）由你选，效果好就行；唯一禁止远程图片。
        </p>
      </div>
    </>
  );
}
