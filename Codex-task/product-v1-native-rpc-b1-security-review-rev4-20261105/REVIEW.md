# B1 rev4 independent security review

Decision: **BLOCKED**.

- B1-F1: PARTIAL_RESIDUAL_BLOCKER. Single-pipe Peek watchdog plus sticky guard/final fence closes the original live-stream gap. Residual raw bytes.Buffer race: guard launched at573 can capture/write at596 while main reads raw.Len at607.
- B1-F2: RESOLVED_IN_SOURCE. Capture reader clamps before ingestion, writes and fsyncs restricted incremental capture; O_EXCL terminal receipt, failures sticky. 8MiB maximum. Source-only, hard-stop observation not audited.
- B1-F3: RESOLVED_IN_SOURCE. UTF-8, duplicate-free JSON, strict envelope and numeric response ID classification reject ambiguous frames.
- B1-F4: RESOLVED_IN_SOURCE. thread/start omits environments; official normal FromThread local default applies, first turn has no override.
- B1-F5: PARTIAL_RESIDUAL_BLOCKER. Items/lifecycle and terminal tail now validated. Remaining turn/completed branch853 ignores a nonnull error when status is completed.
- B1-F6: PARTIAL_RESIDUAL_BLOCKER. Shared ASSISTANT_MESSAGE/NativeID and normal deltas added. Ordinary official first-turn userMessage started/completed still rejected by item type allowlist781, after prompt consumption; fake success omitted this lifecycle.

The eight hashes are recorded in REVIEW.json. Review performed without running tests, fake child processes, Native, model or probes. No production files were modified.

The registered Job amendment is implemented as exact flags 0x2308, active process limit 16, process commit 1 GiB and Job commit 2 GiB. SetInformationJobObject and QueryInformationJobObject must agree and an O_EXCL/fsynced requested/queried evidence file is written before child launch. These are commit limits, not RSS or cumulative process counts. Original f13 control remains required.

Pinned 0.166 DTO confirmation: ThreadStartResponse is camelCase and exposes top-level cwd, runtimeWorkspaceRoots, approvalPolicy, approvalsReviewer, sandbox and activePermissionProfile. Values are built from thread.config_snapshot. ReadOnly sandbox has exactly type=readOnly and networkAccess, with no readRoots. The strict sandbox-key check is therefore compatible. Experimental API is requested. These are actual effective coarse fields plus nonce, not a complete permission graph; the reviewed nonce/config/warning contract and B3 are still necessary.

First turn sends only threadId and input; there are no turn permission/cwd/environment overrides. Qualifier remains nil in the basic production constructor and fails closed. Ensure(ctx,e), the Host callback and private one-use write admission precede prompt write. Raw capture is restricted; reasoning notifications are not projected to public events. Unknowns fail closed and no retry path was introduced.

Primary sources:

- [ThreadStartResponse](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/app-server-protocol/src/protocol/v2/thread.rs#L188-L216)
- [ReadOnly SandboxPolicy](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/app-server-protocol/src/protocol/v2/permissions.rs#L537-L548)
- [effective snapshot response](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/app-server/src/request_processors/thread_processor.rs#L1724-L1744)
- [UserInput Text DTO](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/app-server-protocol/src/protocol/v2/turn.rs#L454-L528)
- [userMessage payload](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/app-server-protocol/src/protocol/v2/item.rs#L295-L305)
- [userMessage emission](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/session/mod.rs#L5489-L5550)
- [regular turn started before input](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/tasks/regular.rs#L60-L123)
- [Turn error DTO](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/app-server-protocol/src/protocol/v2/thread_data.rs#L387-L401)

Limits: no actual Native conformance or permission qualification was executed or certified; Root test results were not independently audited here. B2/B3/Host wiring and fresh authorized synthetic runtime checks remain separate. No READY/business acceptance, no reuse of old echo or task scope, formal increment 0.

