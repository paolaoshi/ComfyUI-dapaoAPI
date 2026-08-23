# Design Calibration

Use this reference after gathering context and before declaring the design system. Its purpose is to turn a brief into visible decisions, not to decorate the response with scores.

## Contents

1. Design Read
2. Five Dials
3. Presets
4. Resolve Conflicts
5. Optional Image-First Branch
6. Completion Test

## 1. Design Read

Write a compact read containing:

- **Artifact**: landing page, dashboard, prototype, slide deck, visualization, campaign page, and so on.
- **Audience**: who must understand, trust, or act.
- **Visual language**: a specific family such as restrained builder SaaS, kinetic editorial, warm humanist, or institutional data-first. Avoid empty labels such as “modern” or “clean.”
- **Mode**: greenfield, extension, redesign-preserve, or redesign-overhaul.
- **Constraints**: brand, accessibility, platform, viewport, content, deadline, and supplied assets.

If two plausible readings would produce materially different work, ask one focused question. Otherwise state the read and proceed.

## 2. Five Dials

Use whole numbers from 1 to 10.

### Visual Variance

Controls compositional departure from familiar patterns.

| Band | Behavior |
|---|---|
| 1–3 | Stable grids, symmetry, familiar navigation, low surprise |
| 4–6 | One or two asymmetric moves, varied section rhythm, controlled novelty |
| 7–8 | Strong art direction, off-grid moments, multiple layout families |
| 9–10 | Experimental composition; use only when comprehension and brand permit |

### Motion Intensity

Controls how much meaning is carried through time.

| Band | Behavior |
|---|---|
| 1–2 | Static; state feedback only |
| 3–4 | Hover, focus, short entry transitions |
| 5–7 | Sequenced reveals, state choreography, restrained scroll response |
| 8–10 | Cinematic transitions, pinning, scrubbing, spatial storytelling |

Every animation must communicate hierarchy, feedback, causality, or narrative. Honor reduced motion whenever motion exceeds simple state feedback.

### Information Density

Controls useful information per viewport, not visual clutter.

| Band | Behavior |
|---|---|
| 1–3 | Gallery-like, one dominant idea, generous pauses |
| 4–6 | Balanced marketing/product density |
| 7–8 | Analytical, operational, comparison-heavy |
| 9–10 | Cockpit-like; requires strong grouping, scanning, and progressive disclosure |

### Asset Dependence

Controls how much the result relies on real imagery, screenshots, illustration, identity assets, or generated visual references.

| Band | Behavior |
|---|---|
| 1–3 | Typography, data, or interface structure can carry the artifact |
| 4–6 | A few key visuals materially improve recognition or explanation |
| 7–10 | The product, brand, campaign, or story fails without high-fidelity assets |

At 7+, inventory assets before layout. Do not hide missing assets with decorative CSS.

### Brand Fidelity

Controls how strictly existing identity and interaction language must be preserved.

| Band | Behavior |
|---|---|
| 1–3 | New or intentionally exploratory identity |
| 4–6 | Adapt recognizable cues while allowing meaningful evolution |
| 7–8 | Preserve core assets, tokens, voice, and signature patterns |
| 9–10 | Extension-level fidelity; new work should appear native to the existing system |

## 3. Presets

Treat these as starting points, not mandatory values.

| Brief | Variance | Motion | Density | Assets | Fidelity |
|---|---:|---:|---:|---:|---:|
| Mainstream SaaS landing | 6 | 5 | 4 | 6 | 5 |
| Creative studio / campaign | 8 | 7 | 3 | 8 | 4 |
| Developer tool landing | 6 | 5 | 5 | 6 | 6 |
| Data dashboard | 4 | 3 | 8 | 3 | 7 |
| Public-sector service | 3 | 2 | 6 | 3 | 9 |
| Editorial presentation | 7 | 5 | 4 | 7 | 5 |
| Existing-product extension | match | match | match | match | 10 |
| Redesign · Preserve | current + 1 max | current + 1 max | match | match | 9 |
| Redesign · Overhaul | 6–8 | 4–7 | match content | 6–9 | 5–7 |

## 4. Resolve Conflicts

- **High variance + high density**: preserve a stable navigation and grid spine; concentrate experimentation in one layer.
- **High motion + high density**: animate transitions or focus, not every element.
- **High assets + low fidelity**: establish a new visual bible before generating or sourcing a set.
- **High assets + high fidelity**: source official assets first; generation may extend the world but must not replace identity-critical material.
- **High fidelity + overhaul request**: explicitly identify which brand invariants survive before changing the visual language.
- **Accessibility constraints** override aesthetic scores. Reduce motion, clarify hierarchy, and preserve contrast without asking permission.

## 5. Optional Image-First Branch

Use image-first exploration only when it materially improves a visually important greenfield or overhaul task, such as a campaign landing page, brand launch, product hero, or highly art-directed portfolio.

Skip it when:

- the user supplied Figma, screenshots, or a mature design system;
- the task is an extension, repair, dashboard, form, or data table;
- the main uncertainty is behavior rather than visual direction;
- image generation would add cost without reducing design risk.

When used:

1. Define a visual bible: palette, typography character, radius, material, image treatment, and forbidden drift.
2. Generate only the critical references needed to resolve uncertainty; one image per section is not a requirement.
3. Prefer fresh, readable section references over cropping tiny details from a compressed full-page board.
4. Extract implementation decisions from the references.
5. Treat code and supplied brand assets as higher-authority sources when they conflict with generated pixels.

Use `gpt-image-2` when available for structured generation; otherwise follow the host's image workflow or leave honest asset requirements.

## 6. Completion Test

The calibration is successful only if someone can point from each dial to concrete consequences in the artifact. If changing a score would not change the plan, remove the score or make the mapping explicit.
