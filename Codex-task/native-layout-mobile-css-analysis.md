# Native workbench mobile layout analysis (read-only)

## Evidence inspected

- Current Main `apps/web/src/workbench.css` SHA256: `2212d10c50819708ca91a4e8f6cb444c7abb6e9a8a3a7c407bbde650f8297944`.
- Receipt: `product-v1-layout-visual-中文-run-01/receipts/workbench-responsive-visual.json`.
- Receipt source HEAD: `1b3a131320c09f553bd3c2c5e3bd39ee6ecb61f2`; Native JSX SHA256: `060ce0ddaa52e955d797dc82c9a1f0372f9e9a417f1a50453fc3132680b0c125`.
- Receipt status: `FAILED_VISUAL_FINDINGS`; model outcome `NOT_RUN_ZERO_BUDGET`.

The receipt reports 22 findings, all in the 390×844 viewport, split across dark/light themes. Desktop 1440×1000 passes in both themes. At mobile initial view, the composer rectangle starts at y=597.9 and ends at 768, while the welcome heading is y=677.3–718.9 and actions occupy y=769–864. Thus the composer overlaps the heading; its hit target also covers the first two actions. Later action focus attempts show the same overlap. The report records no horizontal overflow. The task and Host capability loading indicators are false in the captured snapshot; readiness is not inferred. No model ran.

## Cause in current CSS

At `workbench.css:10`, `.workbench-conversation-pane .session-composer` uses `position:sticky` and `bottom:16px`. The mobile rule at line 15 changes its padding and `bottom:76px`, but leaves the sticky positioning in force. The same mobile breakpoint lets `.conversation-transcript` grow without a max-height, so the composer can remain visually pinned over the transcript content rather than following it in normal document flow.

The app’s fixed `.bottom-nav` is defined in `style.css:5`, with `position:fixed`, `bottom:0`, `height:64px`, and `z-index:19`. The workbench mobile main area reserves 88px at `workbench.css:15` (the general mobile rule reserves 92px), which gives 24px of clearance beyond the standard 64px bar. That clearance should be retained and extended by the device safe-area inset where the app runs edge-to-edge.

## Exact1 recommendation for the next leased source change

In `apps/web/src/workbench.css` only, extend the existing `@media(max-width:767px)` rule to put the composer back in normal flow. Keep all desktop declarations untouched. The proposed mobile declarations are:

```css
.workbench-conversation-pane .session-composer {
  position: static;
  bottom: auto;
  margin-top: 18px;
}
```

This removes the viewport-sticky overlap and leaves the composer after the transcript in its existing DOM order. It does not affect task state, permissions, refs, or handlers. Keep the existing transcript, welcome, and button layout rules for this first repair; the receipt reports no intrinsic transcript overflow or horizontal overflow, so changing those would widen scope without evidence.

For the fixed navigation, keep its 64px bar and z-index. Preserve bottom scroll room and account for safe areas so page-scroll/focus operations can expose the last action above the bar. The current 88px mobile workbench padding already clears a 64px bar on a standard viewport; a small additional recommendation is `padding-bottom: calc(88px + env(safe-area-inset-bottom))` on the workbench main area. If keyboard-driven focus still scrolls an action behind the fixed bar, set document-root `scroll-padding-bottom: calc(64px + env(safe-area-inset-bottom) + 12px)` under `html:has(.workbench-route)`; apply this only if the fresh visual check confirms it is needed. Do not lower the nav z-index or place the composer above it.

After the new lease, re-run the same visual matrix at 390×844 and 1440×1000 in both themes. Check initial heading/action hit testing, scroll-to-heading, each action’s focus and hit testing, composer visibility, and no horizontal overflow. Confirm the final action clears the bottom nav and safe area. Desktop geometry should remain unchanged.

This is analysis only. No D: source, build, app, or model was touched or run.
