# CP367 transaction operation v5 independent Source review

Decision: SOURCE_ACCEPTED_PENDING_FRESH_ROOT_LIVE_CONTEXT_VALIDATION.

22 checks and253 exact input pins passed. Writer differs from reviewed v4 by exactly one byte span: update_pair operation register becomes activate. Reversing that span reconstructs the full original bytes. Facts change only diagnostics/cut/count, failure guard receipt and checkpoint note; full facts UTF-8 inverse passes. Scope, Source/review bindings, WIP and canonical before refs are unchanged.

The original transaction helper AST prelude was independently executed with pure in-memory Windows path and WinDLL stubs. Operation register raises unknown canonical transaction before WinDLL. Operation activate reaches precisely the stubbed kernel32 WinDLL boundary, where execution deliberately stops. No real helper WinAPI, filesystem operation, file handle, transform or canonical write occurs in this control. The SourceReadGuard used separately for read integrity is real and closes all acquired handles.

Failure951 preserves original524e08 args/result, observed outer1 and explicit ROOT_SOURCE_PYTHON_EXIT=1; Native/model remain NULL. Its original input guard is closed with errors[] and retained0. The current four canonical files still match CP366/OW170 and fixed SS/commands before pins. Old934 raw and semantic rows remain unchanged;15 new rows937..951 yield949 registered. Only one W09 worker/subtask is added, and complete canonical semantic inverse passes without W05 authority expansion.

The canonical helper does not automatically roll back. On a write failure it may retain failed.partial.json and exact partial observations for explicit Root reconciliation. A complete semantic inverse check is a Source control, not an automatic runtime recovery guarantee. Failure951 occurred before the helper WinDLL/ownership/write phase.

Actual qualification requires a new Root live context issued after this review, bound to cut951/next952 and the complete current pending interval. If no new failure occurs, live952/pending[] is appropriate. Partial writes must never trigger an automatic replay. This review ran no writer.main, actual helper mutation, Main/Canonical write, Go/SQL/API/model or product Native call. Formal delta0; no new original failure.
