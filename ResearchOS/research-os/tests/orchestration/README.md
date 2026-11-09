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

C01 starts a fresh, ephemeral `gpt-6-luna` CLI session. Its W06-only Codex 0.159.0 binary hash is frozen in the helper and each command receipt; the older W05 qualification pin is unchanged. The host supplies the complete frozen bundle, authorized materialized contents, and versioned records explicitly on stdin. The model identifies the current Goal/Task and D2/D1 lineage, then calculates the source operands using the effective decision (A = addition, B = multiplication). The computation answer is absent from `check.expected`; the generic `verified` report marker remains compatible with the existing acceptance service.

The host validates the actual model computation and trace, seals the full output/trace as a run-scoped LOG Artifact, and sends the actual candidate through scoped upload, report and independent deterministic acceptance. `questions` is a real output channel: every returned question becomes a scoped AgentMessage QUESTION before counts are checked. The model has no service credential. Command, complete input/prompt hashes, raw stdout/stderr, protocol, QUESTION events, and sealed computation ref are preserved under `execution/receipts/W06/continuation-live/`.

Supported feature switches disable shell, web, apps/MCP plugins, browsers, skills instructions and other tool surfaces. This does not claim all catalog tools are absent or W17 isolation. A polling host monitor cancels on the first tool item; the final full event stream must also contain zero tool items. A CLI diagnostic is not a tool. Any real tool attempt fails this run and must not be retried. W05/A04/G03 remain blocked. Direct Go runs require `RESEARCHOS_C01_MODEL=1`; the C01/G02 runner sets this explicitly. Older oracle-echo receipts remain historical and do not establish C01 acceptance.

A02 reuses W01's accepted bounded Paperclip failure/THIN_CORE route evidence and performs actual concurrent HTTP claims, replay, expired lease and fresh Service recovery on Windows. It does not repeat Paperclip qualification or call an external model. A02 is rejected outside Windows.

A03 covers invalid Money/BudgetPolicy/time/revision values through the frozen serializer/schema, plus actual HTTP naive-time no-write, state/idempotency/revision/project rejection, concurrent claim, child-process SQLite crash before commit, durable outbox IDs/order/idempotent acknowledgements, and acceptance input/contract/artifact/epoch/current-authority gates. Monetary spending/policy mutation remains W12; these fixtures do not claim that backend.

Task PAUSE holds BLOCKED with a reason and requests cancellation; no resume is permitted before trusted stop. Goal PAUSE blocks new dispatch and does not claim that an existing Run stopped. Reconciliation retains unresolved Run ownership. Retry counters use durable origin/candidate/input keys, survive new Goal/session labels, and select a new key only after effective input changes.

Failed acceptance and claim requests append an immutable audit after the business transaction has rolled back. Audit rows contain correlation, operation, identity (when authenticated), status/code and response hash, with no credential/body content. Successful domain events retain the same request correlation across Run/Task/successor transitions.

Migration 0006 is the final development shape and 0008 contains immutable canonical-use/proof bindings. Only fresh temporary SQLite databases were tested; existing sealed historical databases were not rewritten. Global canonical Artifact validity is never revived by a new use. A stale REPORT is usable only under a new upload/use/MANIFEST proof bound to an explicitly accepted predecessor; SOURCE_SNAPSHOT and REVOKED are never eligible. Current source/input checks remain mandatory.
