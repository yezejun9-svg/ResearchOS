# I1 intent planning — implementation evidence, independent review pending

The workbench accepts one natural-language statement and keeps it verbatim in an
Owner-bound `USER_STATED` Requirement. Explicit acceptance creates one planning
Goal/Task with frozen deterministic proposal checks, a real ContextBundle and an
initial visible resource block. Browser draft/submission identity and original
idempotency keys survive reload and a lost committed response.

`GoalBrief/v1` is private GENERATED JSON. Its exact raw/context/policy refs,
authoritative fact quotations, bounded DAG, registered checks and explicit unknowns
are independently recomputed by the existing acceptance service. Task acceptance
alone does not compile. Bound planning Goal acceptance rechecks native dispatch
authority, then transactionally creates a stable same-Goal business DAG. Exact
Artifact/Receipt input refs and ImpactLinks carry provenance across Goals.

The current catalog is deliberately limited to `json_report` with the existing
`orchestration.json-equals` verifier. Automatic delivery requires a complete,
positive Owner instruction matching one of these bounded forms:

- `请生成一份 <JSON object> JSON 报告。`
- `请先后生成两份 <JSON object> JSON 报告。`
- `请按先后顺序生成两份 <JSON object> JSON 报告。`
- `请交付 <JSON object>。`

Count, order, literal and `result.json` output must match. A JSON mention,
prohibition, model-invented threshold or arbitrary shell command is not delivery
authority. Other business evaluations/actions remain explicit capability gaps or
business questions in a valid NEEDS_INPUT proposal; no invented branch is created.
This catalog does **not** claim general natural-language business task execution.

The existing S2 coordinator rechecks qualified route, purpose, executor, original
Owner, independent verifier and current inputs before resuming an initially held
intent task. It respects user Task controls and Goal pause/cancel, does not resume
an already-run Task, and refreshes exact dependency context for compiled successors.
Closing a resource request does not grant execution authority. No second queue,
public operation or schema was introduced.

Limits retained for independent review:

- Actual native tests use a deterministic fixture child in AppContainer and remain
  FIXTURE. No real model/provider capability, semantic accuracy, W14 product gate,
  protected verifier isolation or full production E2E acceptance is asserted.
- Independent acceptance uses the existing authenticated VERIFIER operation; this
  slice does not invent a verifier credential or silently grant that role.
- Proposal revisions beyond v1, business answers that change frozen plans, and
  business evaluation capabilities outside this catalog require an explicit new
  planning/W04 implementation. They are rejected or kept as gaps, not upgraded.
- Only private-bound planning Goals have the narrow LIVE acceptance branch.
  Ordinary LIVE business Goal acceptance remains closed.

Relevant tests are in `internal/domain/intent*_test.go` and
`internal/domain/planning_brief_test.go`. `TestIntentNativeChild` is a subprocess
entrypoint, not a counted assertion when invoked without its child arguments.
The functional raw JSONL records 14 substantive top-level tests plus 17 rejection
subtests (32 Go pass entries including that no-op child entry).

`browser_intake.py` is a visible real-browser/temp-control-API test covering raw
input, reload, committed ACK loss, durable uniqueness and planning/business display.
`resource_layout.py` verifies only the affected 320px resource page.

The previous W13 core selectors were updated for the new entry semantics without
removing its actual 412/conflict/draft checks. That run reached and found the long
resource reason-code overflow at 320px. Its FAIL report remains unchanged; the
subsequent narrow 320px test verifies the wrapping fix. `scenarios.py` required no
change after inspection.
