# Existing UI and Redesign Protocol

Read this reference before modifying an existing visual product.

## Contents

1. Classify the Mode
2. Audit Before Editing
3. Protected Contracts
4. Modernization Order
5. Dial Guidance
6. Before-and-After Plan
7. Verification

## 1. Classify the Mode

### Extension

Add or change a bounded element inside the current system. Match the existing vocabulary. Do not “improve” unrelated surfaces.

### Redesign · Preserve

Modernize while retaining identity, information architecture, content voice, and behavioral contracts. Prefer targeted evolution.

### Redesign · Overhaul

Introduce a new visual language while retaining the agreed product, content, and technical contracts. Overhaul is not permission to rewrite everything.

If preserve versus overhaul would materially change the result and the request is ambiguous, ask one focused question.

## 2. Audit Before Editing

Record the current state in project notes or a concise redesign brief.

### Visual system

- Color roles and actual usage ratios
- Type families, scale, weights, and line lengths
- Spacing rhythm and container widths
- Radius, border, shadow, and elevation rules
- Icons, illustration, photography, and image treatment
- Motion durations, easing, triggers, and feedback style

### Product and content

- Page tree, navigation, key journeys, and conversion paths
- Existing content blocks and their purpose
- Brand voice, legal copy, localization, and real data
- Loading, empty, error, disabled, and permission states

### Technical contracts

- Routes, slugs, anchors, and deep links
- Form field names, order, validation, and autofill expectations
- Analytics events, data attributes, test selectors, and experiment hooks
- Component APIs and downstream consumers
- Accessibility semantics, keyboard behavior, focus order, and announcements
- SEO metadata, canonical URLs, structured data, and social cards

### Quality debt

Separate observations into:

- **Preserve**: recognizable or contract-critical strengths
- **Improve**: weak hierarchy, spacing, contrast, responsiveness, or craft
- **Remove**: unsupported clutter, broken patterns, dead interactions, or fabricated content

## 3. Protected Contracts

Never change these silently:

- Route structure, slugs, anchor IDs, or primary navigation labels
- Brand logo, wordmark, or identity-critical assets
- Form field names/order or submission behavior
- Legal, consent, privacy, pricing, or compliance copy
- Analytics events, selectors, and experiment identifiers
- Existing accessibility wins
- Public component APIs or persistent-state keys
- User-provided content and real data

Ask for authorization when the requested outcome genuinely requires a protected-contract change.

## 4. Modernization Order

Apply the lowest-risk lever that solves the problem, then reassess:

1. Correct functional and accessibility failures.
2. Repair hierarchy and typography.
3. Normalize spacing, alignment, and responsive behavior.
4. Consolidate tokens and remove rogue styling.
5. Improve states and interaction feedback.
6. Add justified motion.
7. Recompose hero or key sections.
8. Replace full blocks only when they cannot be repaired.

In Preserve mode, stop once the brief is satisfied. Do not turn incremental work into a portfolio redesign.

## 5. Dial Guidance

- **Extension**: match all existing dials; set Brand Fidelity to 10.
- **Preserve**: keep density and assets stable; change variance/motion by at most one point unless requested.
- **Overhaul**: derive new variance/motion from the brief, but retain a content-density map so information is not lost.

## 6. Before-and-After Plan

For non-trivial redesigns, state:

```text
Mode:
Preserve:
Improve:
Remove:
Protected contracts:
Design Read + dials:
Highest-risk change:
Rollback / fallback:
```

This is a decision record, not a long design essay.

## 7. Verification

The default pre-delivery self-check confirms the requested scope and protected contracts by inspection. Run executable browser acceptance only when the user explicitly asks for it; then use `browser-acceptance.md` and include regression checks for the preserved journeys.
