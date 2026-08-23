import { Section, Aside, Raw } from "reacticle";

// One Section per file. In parallel builds a single subagent owns this file and
// must not touch Article.tsx or other section files. See references/section-build.md.
//
// Rules of thumb (references/component-policy.md + raw-policy.md):
//   - Prose is the body. Write paragraphs as <Section> children.
//   - Semantic components (Aside / Quote / Table / RiskList ...) are accents.
//   - Raw is freely used but hand-authored for THIS section, token-driven.
export function SectionOpening() {
  return (
    <Section index="01" title="第一节">
      <p>正文段落用 children —— 这应是文章主体，尽量多写正文，把背景、推理、结论讲清楚。</p>
      <p>再写一段，保持阅读节奏。语义组件只在内容确实"是"那个结构时才用。</p>

      <Aside tone="principle" label="核心判断">一句话的核心判断，给本节点睛。</Aside>

      <Raw title="为本段现写的内联 SVG（用主题 token 取色）">
        <svg viewBox="0 0 240 60" width="100%">
          <polyline
            points="0,50 40,42 80,46 120,20 160,28 200,8 240,14"
            fill="none"
            stroke="var(--ra-color-accent)"
            strokeWidth="2"
          />
        </svg>
      </Raw>
    </Section>
  );
}
