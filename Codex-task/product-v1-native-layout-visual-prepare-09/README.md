# Native responsive visual candidate 09 — C-only NOT_RUN

This candidate preserves 08's Native helper, JSX selector pin, four viewport/theme cases, real screenshots, original-center elementFromPoint hit checks, and action scroll/focus gate. It adds explicit main-area scroll reset and recorded main scroll geometry. Nonzero initial document, transcript or main scroll produces `INITIAL_SCROLL_NOT_RESET` after all safe captures.

The visibility calculation walks each element's real ancestor chain. Computed overflowX/Y clip only their respective axes for auto, scroll, hidden, clip and overlay using actual ancestor padding/client bounds. Visible overflow does not clip. Raw rectangles, clipped rectangles, and every heading/action/composer clipchain are recorded. A truly visible covered control still fails; every action must be visible, hit and focused after scrolling. No fixed nav offset, DOM/CSS substitution or finding filter exists.

The prior-preclip 09 runner (SHA `829f999e545cc838e6d118a7e09fb2340c324398a99ff41adff593e3558cf3c6`) is preserved under `prior-preclip/` and superseded because it omitted main-area ancestor clipping. The corrected runner has SHA `f3a540bde9a7b332ed7852834bd073fad68543a6b5e32190cf96d19bce24d047`. Candidate 08 remains unchanged.

Build10 source HEAD, all listed source pins including CSS, bundle manifest, Core, Electron and launcher were locally rehashed. Root must independently review this C scope and bind a fresh nonce and original f13 Job/controller/launch-contract pins before an actual run. Template status and null Root pins fail closed. No App, Native, CLI, task or model execution occurred; only new focused scroll and ancestor-clip pure countercases plus Node syntax were checked, not the inherited suite.
