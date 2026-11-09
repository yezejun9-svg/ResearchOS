# Native Codex conversation layout proposal

## Finding

Inspected repository HEAD `2b39fe3a6e8d69981a4079bb585086dca98b283e`; the current blob for `apps/web/src/workbench.jsx` is `914593338975ae83dc1d06b0c6cb78a27e213c73` (the file has no reported working-tree change).

The screenshot shows the welcome headline obscured by the composer. It also shows “正在读取真实任务…” and “正在读取 Host 能力…”, so this capture is still loading; it does not establish a ready-state or task-capabilities result.

This is consistent with a missing wrapper in `NativeHarnessWorkbench` (`workbench.jsx`, lines 481–485). Its conversation prop returns `<Panel className="conversation-canvas">` directly. In contrast, `NativeMuWorkbench` at line 646 returns `<div className="session-center"><Panel …>`. The existing layout rules require that wrapper:

- `style.css:38` targets `.workbench-conversation-pane>.session-center>.panel:first-child` for the tall flex canvas.
- `workbench.css:7` targets `.workbench-conversation-pane>.session-center>.panel.conversation-canvas` to remove generic panel styling and establish the flex column.

Without `.session-center`, both selectors miss the native Codex panel. In particular, the canvas does not become the flex column expected by the sticky/bottom composer and transcript rules. The same direct-child selector has a mobile min-height override at `workbench.css:15`.

## Smallest proposed change

Add the same `session-center` wrapper around the Codex conversation `Panel` in `apps/web/src/workbench.jsx` only. Keep the Panel, transcript, welcome component, composer, props, handlers, and all task behavior intact. No CSS change is indicated by the inspected DOM and selectors.

```diff
@@ NativeHarnessWorkbench, conversation prop (around workbench.jsx:481)
-      conversation={<Panel ...existing attributes and children...>
+      conversation={<div className="session-center"><Panel ...existing attributes and children...>
         ...existing conversation content unchanged...
-      </Panel>}
+      </Panel></div>}
```

The fragment above indicates only the opening and closing tag edits; retain the actual intervening JSX verbatim. This restores the DOM shape already used by Mu and required by current CSS, without changing selectors, refs, accessibility labels, submission logic, or authorization.

## Relevant checks

`tests/ui/desktop/harness-workbench.test.mjs` already exercises the real Codex send/edit handlers and checks preservation of unsent draft edits around delayed success, plus Enter/Shift+Enter/IME behavior. It does not assert rendered DOM or layout. After applying the wrapper in the authorized source checkout, use the requested real-render verification to confirm the panel selectors match and the composer no longer covers the welcome content at desktop and mobile widths. Do not add a wrapper-only test.

This is a proposal only; no source file was changed and no application or test was run in this subtask.
