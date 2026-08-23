# Contextual Failure Patterns

Use this catalog to catch recurring AI-generated design failures. Read only the sections relevant to the artifact. These are strong defaults with explicit exceptions, not universal taste laws.

## Contents

- Marketing and Multi-section Pages
- Layout and Components
- Typography and Content
- Imagery and Brand
- Motion and Interaction
- Dashboards and Product UI
- Final Use

## Marketing and Multi-section Pages

### Repeated section header formula

- **Default**: Do not put a tiny uppercase eyebrow above every heading.
- **Why**: It creates a mechanically templated rhythm.
- **Detect**: The same label + headline + paragraph stack appears in most sections.
- **Exceptions**: Manuals, intentionally indexed editorial systems, or an established brand pattern.
- **Repair**: Remove low-information labels; vary hierarchy using a lead sentence, image, number, quote, or direct headline.

### Zigzag monotony

- **Default**: Avoid three or more consecutive left/right image-text splits.
- **Why**: Alternation alone is not composition.
- **Detect**: Mirroring is the only difference between adjacent sections.
- **Repair**: Introduce a full-width proof point, vertical narrative, comparison, gallery, diagram, or focused text break.

### Default centered hero

- **Default**: Do not choose centered headline + gradient + two CTAs without brief support.
- **Why**: It is a statistical default, not a design decision.
- **Exceptions**: Manifestos, launch statements, search-first utilities, and deliberately ceremonial pages.
- **Repair**: Re-evaluate content hierarchy, asset role, audience, and viewport; choose the composition that makes those constraints clearest.

### Decorative trust theater

- **Default**: No fabricated metrics, testimonials, logos, security badges, or “used by” claims.
- **Why**: False credibility is worse than an honest gap.
- **Repair**: Use a labeled placeholder or request real proof.

### CTA duplication

- **Default**: Keep labels for the same intent consistent.
- **Detect**: “Get started,” “Try free,” and “Create account” all route to the same action without a meaningful distinction.
- **Exceptions**: Tested funnel copy or different commitment levels.
- **Repair**: Normalize the label or clarify the distinct outcomes.

## Layout and Components

### Cardification

- **Default**: Use containers only when grouping, selection, or elevation carries meaning.
- **Detect**: Every paragraph, metric, and icon lives in a rounded card.
- **Repair**: Use whitespace, alignment, dividers, typography, or one shared surface.

### Bento without rhythm

- **Default**: Every cell needs content and a compositional role.
- **Detect**: Blank filler cells, uniform text-only tiles, or arbitrary spans.
- **Repair**: Match cell count to content; create hierarchy through size, media, data, or interaction rather than empty geometry.

### Shape drift

- **Default**: Define a radius grammar and follow it.
- **Detect**: Pills, sharp cards, soft cards, and circular controls appear without semantic rules.
- **Repair**: Assign radius by component role and consolidate tokens.

### Split-header filler

- **Default**: Avoid a large left headline paired with a small floating right paragraph when the split communicates nothing.
- **Repair**: Stack the content or give the second column a real visual, action, or evidence role.

## Typography and Content

### Generic display typography

- **Default**: Do not reach automatically for Inter, Roboto, Arial, system-ui, Fraunces, or Instrument Serif as the identity-bearing display choice.
- **Exceptions**: Existing brand/system requirements, accessibility contexts, or intentional platform neutrality.
- **Repair**: Use the chosen recipe, supplied brand font, or a justified pairing.

### Micro-label noise

- **Detect**: Decorative version numbers, fake coordinates, weather, status dots, section numbers, or metadata that does not help the user.
- **Repair**: Delete it or connect it to real state/content.

### Copy-shaped decoration

- **Detect**: Vague claims, fake precision, agency slogans, or captions written only to fill space.
- **Repair**: Replace with user-provided truth, a clear placeholder, or fewer words.

### Unreadable hero

- **Detect**: CTA falls below the intended initial viewport, display text clips, or copy/image competition destroys hierarchy.
- **Repair**: Recompose; do not enforce a universal word or line cap when the artifact needs a different reading experience.

## Imagery and Brand

### CSS as counterfeit asset

- **Default**: Do not replace a recognizable product, logo, or interface with decorative CSS shapes.
- **Repair**: Source official material, generate a clearly non-identity-critical extension, or expose an honest asset slot.

### Image-label clutter

- **Default**: Do not overlay pills and captions on imagery unless they identify, control, or explain it.
- **Repair**: Move necessary metadata into a stable caption or remove it.

### Generated-world drift

- **Detect**: Multi-image output changes palette, material, lighting, typography character, device treatment, or brand symbols.
- **Repair**: Reuse a visual bible and regenerate the divergent frame rather than patching it with unrelated decoration.

## Motion and Interaction

### Motion for spectacle only

- **Default**: Every animation needs a hierarchy, feedback, causality, or narrative purpose.
- **Detect**: Removing the animation changes no understanding or feedback.
- **Repair**: Remove it, lower the Motion dial, or tie it to meaningful state.

### Scroll-state rendering

- **Default**: Do not update broad React state on every scroll or pointer frame.
- **Repair**: Use CSS, motion values, IntersectionObserver, or an animation library appropriate to the stack.

### Repeated spectacle

- **Default**: Avoid multiple marquees, pinned chapters, magnetic controls, or competing ambient loops on one surface.
- **Repair**: Select one signature moment and make other transitions quieter.

### Missing reduced-motion path

- **Default**: Motion beyond simple state feedback must collapse cleanly under reduced motion.
- **Repair**: Preserve content order and interaction completion without relying on animation.

## Dashboards and Product UI

### Marketing styling on operational UI

- **Detect**: Giant headlines, excessive whitespace, cinematic cards, and low-density gestures impede scanning.
- **Repair**: Raise density, stabilize the grid, clarify state, and prioritize task completion.

### Decorative data visualization

- **Detect**: Gradients, 3D, shadows, or animation obscure comparison and scale.
- **Repair**: Improve data-ink ratio, labels, semantic color, and accessible alternatives.

### Happy-path-only components

- **Detect**: Only populated success states exist.
- **Repair**: Add relevant loading, empty, error, permission, disabled, and overflow states.

## Final Use

Report only consequential failures. Do not dump the whole catalog into the user-facing response. Fix safe in-scope problems directly; surface exceptions and tradeoffs when they affect intent.
