# STOP-r4 independent reviewer command recipe

Before reading project material, this recipe establishes reviewer-owned evidence.
All subsequent shell commands will be captured by reviewer_logger.py to immutable numbered stdout, stderr, command metadata, and ledger records within this directory.
Initial bootstrap reads are captured explicitly in bootstrap-read-output.json before further work.
Read order: project AGENTS.md; pinned independent-review-scope.json; scope-authorized inputs only.
Do not mutate shared states, original Core/DB/API/keys/models, author-owned fixtures, or old policy-denied resources.
Use Python 3.14 -B -X utf8; Go and module cache fixed by scope. All build/cache/TMP evidence stays on D; new native fixture support only in the expressly authorized C fixture subtree.
Review source semantics, all 19 paths, and scoped independent positive/negative fixtures. Retain every failed attempt and command exit. Freeze review.md, review.json, diagnostic ledger, command index, then FINAL manifest.

Finalization recipe: run build_review.py through reviewer_logger.py. After its subprocess exits, logger closes the complete current capture and ledger, then calls seal_after_capture in-process to construct the command index, diagnostic ledger, review references and FINAL manifest. No later evidence-writing shell command is planned. The initial bootstrap reads are retained in command-captures/0001 and /0002 rather than a separate bootstrap-read-output.json. Generated fixture binaries/data remain useful audit/reproduction evidence; the unused first test build has been removed.
