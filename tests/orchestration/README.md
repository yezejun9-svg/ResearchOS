# W06 orchestration development evidence

Status: DEVELOPMENT_ONLY. Independent acceptance is owned by the external Verifier.
W06-G03 and final W06 acceptance remain BLOCKED by RQ-W05-CLI-POLICY-001.

Run `python -X utf8 ops/ci/orchestration.py --mode fixture` with:

- `RESEARCHOS_TASK_ID=W06` and exactly one selector.
- `RESEARCHOS_CHECK_ID=W06-G01`: 71 exact assertions.
- `RESEARCHOS_CHECK_ID=W06-G02`: 4 exact assertions.
- `RESEARCHOS_CASE_ID=C01`, `A02`, or `A03`: the frozen subset in the runner.
- `RESEARCHOS_GO`: the repository-pinned Go 1.27.1 executable when using an isolated worktree.

`expected.json` freezes IDs per test. Missing, duplicate, unexpected, empty, malformed or failed assertions fail the runner. Unknown/empty/mismatched selectors exit 2. `--mode live` only accepts W06-G03 and exits 1 with BLOCKED without invoking any model or tool.

C01 uses a **MEMORYLESS_FIXTURE_AGENT**, an isolated Go child process receiving only the frozen ContextBundle on stdin. It is a deterministic JSON continuation agent, not a live model qualification. The receipt includes the complete bundle, child argv, environment variable names, stdout, hash, exit and real database QUESTION event counts. The produced JSON artifact goes through the actual scoped upload, trusted fixture observation, report and independent acceptance service. Parent and successor emit identical report bytes; canonical reuse is exercised, not evaded with formatting.

A02 reuses W01's accepted bounded Paperclip failure/THIN_CORE route evidence and performs actual concurrent HTTP claims, replay, expired lease and fresh Service recovery on Windows. It does not repeat Paperclip qualification or call an external model. A02 is rejected outside Windows.

A03 covers invalid Money/BudgetPolicy/time/revision values through the frozen serializer/schema, plus actual HTTP naive-time no-write, state/idempotency/revision/project rejection, concurrent claim, child-process SQLite crash before commit, durable outbox IDs/order/idempotent acknowledgements, and acceptance input/contract/artifact/epoch/current-authority gates. Monetary spending/policy mutation remains W12; these fixtures do not claim that backend.

Task PAUSE holds BLOCKED with a reason and requests cancellation; no resume is permitted before trusted stop. Goal PAUSE blocks new dispatch and does not claim that an existing Run stopped. Reconciliation retains unresolved Run ownership. Retry counters use durable origin/candidate/input keys, survive new Goal/session labels, and select a new key only after effective input changes.

Failed acceptance and claim requests append an immutable audit after the business transaction has rolled back. Audit rows contain correlation, operation, identity (when authenticated), status/code and response hash, with no credential/body content. Successful domain events retain the same request correlation across Run/Task/successor transitions.

Migration 0006 is the final development shape and 0008 contains immutable canonical-use/proof bindings. Only fresh temporary SQLite databases were tested; existing sealed historical databases were not rewritten. Global canonical Artifact validity is never revived by a new use. A stale REPORT is usable only under a new upload/use/MANIFEST proof bound to an explicitly accepted predecessor; SOURCE_SNAPSHOT and REVOKED are never eligible. Current source/input checks remain mandatory.
