# W12 execution and recovery

DEVELOPMENT_ONLY / executor reports EXECUTION_REPORTED; no self acceptance.

The public frozen API now supports budget-policy/run-policy updates, immutable budget ledger append/read, resource request create/read/resolve, and no-progress read/advance. It uses the existing Service transaction, authentication, ETag, idempotency and outbox.

The trusted scheduler/worker interfaces are Service.PrepareEffect, BeginEffect, ObserveEffect, ResumeCheckpoint and SwitchResource. They do not own another queue or issue external provider calls. The caller commits admission before invoking a provider, queries the original provider key after a lost ACK, and submits the trusted observation before resume. Unknown/unqueryable outcomes stay blocked. Resume retains Run identity, creates a current ContextBundle, rotates only lease epoch, and carries the validated checkpoint bytes into a separately audited ArtifactUse. Frozen dependency vectors cannot be rewritten.

Both checkpoint recovery and resource switching rebuild the execution session (`native_resume=false`). They archive the old external session binding, rotate the lease token and epoch, clear the external ID for the new process's first heartbeat, and carry any checkpoint into the new epoch atomically. A heartbeat without a new checkpoint preserves the durable recovery point. Former-epoch heartbeat/report callbacks are rejected; former observations and late provider costs remain attributable to the original Run. Native provider-session resume requires separate qualification and is not inferred from a registration flag.

AuthorizeFixtureResource only authorizes explicitly labelled development fixtures. LIVE routing/admission remains blocked on W05; no CLI/provider qualification is inferred. Registered Experiment bindings from W10 experiment_tasks are checked alongside the Goal ancestry, but that integrated path must be revalidated after root merges W10.

RECONCILE records the corrected final total for one original provider request. It appends history and does not overwrite the original COMMIT. Only the original reservation/UNKNOWN root can be referenced; aliases cannot settle again. Money uses integer numerator/denominator arithmetic. DAILY/MONTHLY use policy timezone; unresolved reservations carry across periods. BudgetUsage projects incurred, estimated, unknown, reserved and in_flight columns; in_flight is a subset, not an additional amount.

Validation: set RESEARCHOS_TASK_ID=W12 plus exactly one RESEARCHOS_CHECK_ID (W12-G01/G02) or RESEARCHOS_CASE_ID (C11/C13/C14/C15/C16), RESEARCHOS_GO to pinned Go, then python -X utf8 ops/ci/resources.py. G02 reports BLOCKED and exits nonzero. Case selectors run named tests and report every assertion actually executed, including explicit supporting assertions from shared scenarios. Unknown/empty selectors fail. Each invocation saves source/input/lock hashes, native process evidence, real loopback HTTP exchanges (credential redactions with wire hashes), before/after SQLite projections, stdout/stderr and expected/actual results.

C11 uses a validated ResearchCycle fixture envelope and the official Run reporting/AcceptanceService callbacks. W08 periodic scheduling and W10 experiment-specific callbacks are outside this fixture; root must rerun the integrated bindings when those owners land. It does not prove live model/tool recovery.

Shared proposals requiring root serial integration:
- http.go: route resources operations, policy ETag targets and early resource write fence; correct resource/policy event types.
- orchestration.go: existing queue/global concurrency admission and zero-cost registered fixture dispatch reservation.
- orchestration_recovery.go: durable per-Run iteration provenance and strict inherited retry limits.

Migration is exclusively 0011_resources.sql; W10 owns 0010. No shared registry/schema/lock/verifier changes.
