import { Article, Hero, Lead, Raw } from "reacticle";
import { SectionOpening } from "./sections/01-opening";

// Article.tsx is the ASSEMBLER, owned by the main agent. It imports and orders
// Section components — it must NOT contain Section bodies inline.
//
// 铁律：每个 Section 是独立组件文件（article/sections/NN-*.tsx），坚决不允许把
// 多个 Section 直接写进这里。这样多个 Agent 才能并行各写一个 section 文件，主 Agent
// 在这里负责合并与稳定性。详见 references/section-build.md。
//
// width (narrow/regular/wide/full) + toc 在 Plan Checkpoint 确认，与主题解耦
// （见 references/layout.md）。
export function ArticleDoc() {
  return (
    <Article toc width="regular">
      <Hero
        title="文章标题"
        subtitle="副标题：一句话框定这篇要解决什么"
        meta={[{ label: "日期", value: "2026-06-08" }]}
      />
      <Lead>导语：用一两句话框定主题与读者要带走的判断。</Lead>

      <SectionOpening />
      {/* 在此按顺序加入更多 section 组件：<SectionContext /> <SectionMechanism /> … */}

      {/*
        ─── Colophon ───
        每篇 Beautiful Article 必须保留这一段，位置在 </Article> 之前、所有 Section /
        Conclusion 之后。它是文章的"印记"，告诉读者文章是用什么工作流生成的。

        约束：
          • 不要删除。不要移到 Hero 旁边或浮动到角落。
          • 文本格式固定：Made with beautiful-article（带链接到 github 仓库）· <主题> theme
          • 主题名（下方 __THEME__ 占位）由 scaffold 写入；切换主题时同步更新这里和
            main.tsx 的 <ThemeProvider theme="...">。
          • 样式只能用 --ra-* token，跟随主题自适应；保持低对比、小字、居中。
      */}
      <Raw title="">
        <footer
          style={{
            marginTop: "var(--ra-space-7, 3rem)",
            paddingTop: "var(--ra-space-4, 1rem)",
            borderTop: "1px solid var(--ra-color-border, currentColor)",
            color: "var(--ra-color-muted, inherit)",
            fontSize: "var(--ra-text-xs, 0.78rem)",
            textAlign: "center",
            letterSpacing: "0.02em",
            opacity: 0.85,
          }}
        >
          Made with{" "}
          <a
            href="https://github.com/ConardLi/garden-skills"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: "inherit",
              textDecoration: "underline",
              textUnderlineOffset: "0.2em",
            }}
          >
            beautiful-article
          </a>{" "}
          · __THEME__ theme
        </footer>
      </Raw>
    </Article>
  );
}
