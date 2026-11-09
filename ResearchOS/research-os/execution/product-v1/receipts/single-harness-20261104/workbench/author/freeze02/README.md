# Workbench draft fix, freeze02

This revision fixes the independently reproduced Q20 late-ACK draft loss. The real Codex textarea and starter suggestions increment an edit version. Workspace/project changes also invalidate that version. A successful asynchronous send clears the submitted draft only if that version still matches and the same controller/view owns it. View cleanup invalidates the version and detaches its controller. Editing away and back to identical text therefore preserves the current draft.

Only apps/web/src/workbench.jsx and tests/ui/desktop/harness-workbench.test.mjs differ from freeze01. The other eight scoped files, Harness interface revision2, IME key handling, capability gates, Host authority and UNKNOWN journal behavior remain unchanged.

Final actual results: four Node syntax checks and46 pure tests passed; Git diff-check/status/stat exited0 with the exact original ten-file scope. Vite compiled the final production source into three files and verified every production input unchanged. The later fixture repair changed only a missing VM visible callback, so production was not rebuilt redundantly. The failed45PASS/1FAIL attempt, its exact two source files and all raw logs are retained. The original independent QA raw contains the two real draft failures plus its separately identified Q02 fixture input error; these are not conflated.

The new regressions execute the actual send function, textarea onChange, scope guard and cleanup code with a controlled promise. They cover new unsent text, edit-back-to-original, unchanged successful submission, view cleanup, workspace changes away and back, and replacement controller. This is pure control-flow evidence, not a real DOM/IME/GUI or model observation.

Old freeze01 files and all276 old evidence pins are immutable and verified. Source modification stopped before this freeze02. No actual GUI/HTTP/native/Harness/model or old probe was run; no commit or Root state change was made. Product/formal increment0. Independent QA must decide source acceptance.

ARCHIVE_FILES.json and EVIDENCE_MANIFEST.json describe the selected portable evidence. They include original failure/raw evidence and final source snapshots and exclude node_modules, caches, build source scratch and all dist directories. Original C folders remain available; the full historical freeze01 manifest is retained by reference and must not be mistaken for a claim that all276 old files were copied into this smaller archive.
