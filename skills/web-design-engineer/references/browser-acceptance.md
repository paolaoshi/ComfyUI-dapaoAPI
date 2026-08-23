# Executable Browser Acceptance

## Contents

1. Trigger Gate
2. Resolve the Acceptance Contract
3. Start Safely
4. Automated Pass
5. Visual Pass
6. Repair Loop
7. Acceptance Report

## 1. Trigger Gate

Run this harness only when the user explicitly requests acceptance / 验收, browser QA/testing / 浏览器测试, responsive verification / 响应式检查, cross-browser inspection, visual regression, interaction testing, or equivalent executable validation.

Do **not** run it merely because the user says build, implement, polish, finish, review the code, or verify your work. Those requests receive the lightweight pre-delivery self-check unless browser execution is explicitly named or unmistakably requested.

If the user asks only for a design critique, inspect the supplied render or artifact and use `critique-guide.md`; do not silently expand into browser acceptance.

## 2. Resolve the Acceptance Contract

Infer from the request and project before asking questions:

- Entry URL or local command
- Critical routes / screens
- Primary interaction path
- Required viewport(s)
- Target browser(s), if specified
- Whether the user wants evidence, repairs, or report-only QA

Use the project's existing dev command and dependencies. Do not replace the stack or install a new test framework unless necessary and authorized.

Default viewports only when the user asked for responsive acceptance but did not provide targets:

| Name | Viewport |
|---|---|
| Small mobile | 390 × 844 |
| Tablet | 768 × 1024 |
| Small laptop | 1280 × 720 |
| Desktop | 1440 × 900 |

For fixed 16:9 artifacts, test the intended internal canvas plus at least one smaller outer viewport to verify non-distorting scale behavior.

## 3. Start Safely

1. Inspect `package.json` and project docs for the intended command.
2. Reuse an already-running server when available.
3. Start the minimum required local process and wait for a real ready signal.
4. Record the actual URL and build/dev mode.
5. Do not modify production services or external data.

## 4. Automated Pass

Use the environment's available browser-control or test tooling. Check the agreed scope:

### Runtime

- Page loads without fatal errors.
- Console contains no new actionable errors; classify unrelated third-party noise rather than hiding it.
- Local assets, fonts, images, and primary network requests succeed.
- No hydration or framework mismatch appears.

### Layout

- No unintended horizontal overflow.
- Navigation, primary CTA, key content, dialogs, and controls remain reachable.
- Text does not clip, collide, or become unreadably narrow.
- Images preserve intended crop and focal point.
- Fixed-canvas artifacts scale without distortion.

### Interaction

- Primary links and buttons perform the intended action.
- Keyboard focus is visible and follows a sensible order.
- Forms expose labels, validation, errors, and submission feedback as applicable.
- Overlays can be opened and closed without trapping or losing the user.
- Loading, empty, error, and disabled states are exercised when they are in scope and safely reachable.

### Motion and preferences

- Animations complete and do not block interaction.
- Reduced-motion behavior preserves content and task completion.
- Auto-playing or looping motion can be paused when required by the artifact.

## 5. Visual Pass

Capture evidence at each requested viewport and critical state. Inspect screenshots for:

- hierarchy and focal order;
- spacing rhythm and alignment;
- design-token drift;
- repeated layout formulas;
- contrast and legibility;
- awkward folds, orphaned controls, and large accidental voids;
- visual differences from supplied references or baselines.

If a formal baseline exists, compare against it. If not, call the pass “visual acceptance,” not “visual regression.”

## 6. Repair Loop

When the user authorized implementation or asked to fix acceptance failures:

1. Record the failure and reproduction condition.
2. Make the smallest causal repair.
3. Re-run the failed check at the same viewport/state.
4. Re-run a nearby smoke path when the change could regress another area.
5. Stop after the contract passes or report the concrete blocker.

For report-only QA, do not edit files. Provide evidence-backed findings ordered by severity.

## 7. Acceptance Report

Keep the report concise and reproducible:

```text
Acceptance scope:
Environment / URL:
Viewports / browsers:
Paths exercised:
Passed:
Repaired:
Remaining issues:
Evidence:
```

Never claim browser acceptance from code inspection alone. If the executable harness could not run, say exactly what was and was not verified.
