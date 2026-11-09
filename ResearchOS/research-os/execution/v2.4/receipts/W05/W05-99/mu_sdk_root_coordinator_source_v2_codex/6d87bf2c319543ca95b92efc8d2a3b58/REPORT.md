# Root coordinator v2: output failure retention

Decision: IMPLEMENTED_SOURCE_PENDING_INDEPENDENT_REVIEW.

The only Source change is run_resident: when cleanup is uncertain, JSON serialization and print are inside a try block whose finally always calls retain_parent. Successful output, BrokenPipeError, serialization TypeError, and other output RuntimeError all enter retention exactly once in the focused fake control. The prior packet remains immutable.

The prior 24 fixed Source/binary role pins and 40 controls are reused, not rerun or promoted to actual runtime evidence. All other module AST is unchanged; full-byte forward/inverse restoration is verified. New candidate imports/entrypoints, real WinAPI/native/SQL/provider calls, and Main/canonical writes are zero.

NO_PROVIDER remains only bootstrap evidence inspection. MODEL_TRIAL still requires actual successful bootstrap evidence, independent non-author Source review, and separate Root runtime authorization. Parent/Host/C7 native lifecycle, provider reconciliation, and formal acceptance remain OPEN. No READY or execution approval is issued.
