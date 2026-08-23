# Implemented Block Library

Use this index to reach an existing working pattern before inventing a new implementation. The implementations currently live in `advanced-patterns.md`; load only the targeted section.

| Need | Implemented block | Source section |
|---|---|---|
| Fixed 16:9 presentation | Responsive Slide Engine | `advanced-patterns.md#responsive-slide-engine` |
| Phone or browser framing | Device Simulation Frames | `advanced-patterns.md#device-simulation-frames` |
| Live visual controls | Tweaks Panel | `advanced-patterns.md#tweaks-panel-implementation` |
| Timeline-driven motion | Animation Timeline Engine | `advanced-patterns.md#animation-timeline-engine` |
| Side-by-side option review | Design Canvas | `advanced-patterns.md#design-canvas` |
| Theme switching | Dark Mode Toggle | `advanced-patterns.md#dark-mode-toggle` |
| Charts and analytical views | Data Visualization Templates | `advanced-patterns.md#data-visualization-templates` |

## Reuse Contract

Before copying a block:

1. Confirm it matches the artifact, stack, and calibrated dials.
2. Preserve its accessibility and responsive behavior.
3. Adapt tokens to the declared design system.
4. Remove features that do not serve the request.
5. Verify dependency availability before importing anything.

## Adding a New Block

Add a reusable block only after it has solved a real task. Document:

- when to use and when not to use it;
- visual structure and props/data contract;
- minimum working implementation;
- mobile/fixed-canvas behavior;
- interaction and motion variants where relevant;
- reduced-motion and accessibility behavior;
- dark/light theme notes where relevant;
- common failures and repairs.

Prefer one implemented block over a catalog of names without code.
