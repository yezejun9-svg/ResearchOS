# B3: bounded native qualification producer

Frozen proposal for a separate source lease; not an execution scope. C-only preparation, zero Native/CLI/App/model/probe invocations and zero product writes. Baseline reported by Root: CP667, Main c3c7812347bb72930365fbb5db0efee8a965bc78; B1/B2 are independently in progress. B1 shared-api-v1/API.json and its current C source were inspected. This plan does not reopen its nonce/thread barrier.

## Selected route and primary evidence

At rust-v0.166.0, command/exec has experimental permissionProfile, an exact named selection, but no threadId; it is standalone. It accepts argv, cwd and bounded execution options. [Protocol](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/app-server-protocol/src/protocol/v2/command_exec.rs#L18).

The handler reloads configuration for cwd with default_permissions set to that name, rejects a permission_profile disallowed warning, and constructs an execution request with the resulting permissions. It does not execute inside the previously inspected thread snapshot. [Handler](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/app-server/src/request_processors/command_exec_processor.rs#L188).

Select a separate fixed `sandbox --include-managed-config --permission-profile <freshnonce>` Native invocation for B3 v1. This keeps B1's RPC whitelist unchanged and supplies independently observable synthetic operations. It is not presented as unavailable command/exec support; it is a deliberate smaller implementation. No automatic switch between these routes. Sandbox named-profile selection may fall back; meaningful negative operations detect tested widenings, but finite probes do not prove every managed fallback absent. Model admission still requires B1's exact current-process effective-profile barrier. [Sandbox loader](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/cli/src/debug_sandbox.rs#L653).

## Private integration, without a blocking boolean callback

Keep B1 CodexQualificationProvider.Qualified(CodexTurnEvidence) bool as a quick live-observation check. Do not perform subprocess IO inside that callback: B1 may be awaiting RPC input on the same goroutine. Existing trusted Go fake provider remains test composition only.

Add a production constructor `NewCodexRPCWithNativeQualification(options, qualificationOptions)` whose implementation constructs the concrete private nativeQualifier. It does not accept an arbitrary provider, function, ready boolean, receipt path or qualification JSON. The old NewCodexRPC remains closed with nil qualifier. QualificationOptions contain only Host-owned approved root/helper identity/budget/source-scope facts; their origin is the composition root, never a request decoder. Prefer HostBoot generated privately by this concrete instance over a caller string.

The production wrapper Start validates launch, current canonical policy/hash/environment and that the launch belongs to the authorized synthetic source binding. Before starting the model RPC child, it calls private `ensure(ctx, launch) error`; after success it delegates to B1. The returned handle/cancel/wait contract must include preparation work and cancellation, even if ensure runs asynchronously; do not block an HTTP submit handler or detach preparation from the run context. If preparation fails, return a known pre-prompt failure through existing run settlement, with evidence and cleanup state. Do not call the model BeforeResume callback for the qualification child: its identity is not the model dispatch identity.

The private qualifier owns a mutex/state machine NOT_STARTED -> RUNNING -> OBSERVED_PASS | FAILED | UNKNOWN. One in-flight attempt; concurrent callers do not spawn duplicates. Failure/unknown consumes the attempt and stays closed. Context cancellation must stop its owned Job and complete collection. No automatic retry, change of scope, setup or receipt import. A successful observation is in memory only, bound to HostBoot, reviewed build, native hash, template/helper/env-policy identity, fixture/source scope, its originating Task/Run/epoch, and bounded expiry. For the first acceptance slice make it single-consumer for that originating Task/Run, not a cross-project cache. Qualified(e) checks these bindings plus the current B1 live evidence; it cannot create B1's permit.

Root's same-Core-boot acceptance flow is: one newly submitted synthetic Task -> lazy qualification once -> success-only one RPC preparation -> B1 barrier -> BeforeModelTurn authority/identity fence -> at most one user turn. No GET capability side effects. On qualification failure, user prompt bytes are zero and model RPC child count is zero. Qualification is part of that Task's preparation, not a second model Task. Subsequent policies for reuse across Tasks are out of this first slice.

## S/W/D fixtures and helper

Create one unique Host-owned base under an approved C Documents location outside known Windows/ProgramFiles/ProgramData/TEMP platform-minimal roots. Its three sibling directories are S/source, W/cwd and D/denied. Canonical paths and ancestor no-reparse checks are required; D and W are outside S. Host precreates only synthetic files: S/allow.txt, S/write-existing.txt, W/write-existing.txt, D/denied.txt and a marker in W. Fixed synthetic content only; Host compares byte hashes. No user-project or credential reads. First accepted model Task source binding is S itself, so qualification does not claim another project's path was tested.

Helper is a dedicated fixed self-contained Windows executable located in S, included in S's existing source-read grant. Build it through the existing Go toolchain without adding dependencies; use Win32 file operations and Winsock APIs (existing x/sys/windows or minimal wrappers) to retain native error codes. No shell/interpreter, external runtime, recursive traversal, child process, dynamic module load, generic path/URL runner, config reads or disk logging. Its dedicated entry point accepts only the versioned fixed synthetic plan. Plan contains S/W/D canonical paths, run nonce, exact loopback tuple and fixed case list; do not put expected allow-file contents/hash in it. The helper emits actual operation outcomes and read digest, not a self-declared PASS. Host is the evaluator.

Before Native invocation, Host directly verifies these synthetic files are readable and writable as the current user, writes/restores fixed control values and captures baselines. This rules out absent files, read-only attributes or ACLs masquerading as sandbox denial. Close target handles before testing; no sharing-mode write lock may create the expected denial. Pin helper/binary separately without locking tested target files. If helper cannot start/read from S under the requested policy, classify BOOTSTRAP_BLOCKED; do not grant another path or write access.

Cases, each with START/result and final complete bitmap:
1. Read S/allow.txt, <=64 KiB, actual hash must equal Host baseline.
2. Open/read D/denied.txt using native read access. Only an expected access-denied result qualifies; any opened readable handle or read data fails. Never expose denied contents, even though synthetic.
3. Request write access to existing S/write-existing.txt and W/write-existing.txt. Acquiring write access already fails the policy check; bounded sentinel write is unnecessary. Host post-hashes must remain unchanged.
4. CREATE_NEW one fixed previously absent target in S and W. A successful handle/create fails; do not hide/delete the failed evidence before post-audit.
5. Connect once to the exact IPv4 loopback listener tuple. Successful connect fails even if subsequent handshake fails. Native WSAEACCES 10013 may qualify; timeout/refusal/route errors are UNKNOWN, not enforcement proof.

Win32 ERROR_ACCESS_DENIED 5 is the default accepted filesystem denial. Any added equivalent code must be justified, frozen and tested before execution. Missing-file/path, sharing violation, malformed-plan, helper exception and incomplete records are UNKNOWN/invalid, never PASS. Record raw numeric operation errors. D denied-read and S/W denied-write results must be accompanied by their successful Host precontrols and complete post-audit.

## Network controls

Host starts one loopback-only 127.0.0.1 listener, selects its port dynamically, then freezes that actual tuple into the plan before launch. No DNS, public address or external server. Listener handle is non-inheritable; qualification child inherits only reviewed stdio handles. Host performs nonce-labelled connect/read-write roundtrip positive controls immediately before and after the helper; listener stays alive throughout and records accepts. Helper uses a different nonce if it unexpectedly connects. Positive controls use Host APIs, not another Native command.

Any successful helper connect/accept is FAIL; unsuccessful pre/post control, listener loss or ambiguous connection attribution is UNKNOWN. Only the exact IPv4 TCP tuple is observed; do not generalize to IPv6, UDP, DNS, all ports or outer Native network. IPv6 is out of v1 unless Root explicitly adds its separate listener/control/case and budget.

## Frozen invocation construction and lifecycle

Use the SAME canonical policy builder as B1 for the requested security projection, substituting a fresh qualification nonce and S/W. Include fixed mxc, exact root deny/minimal read/source read/network false/approval never, memory scalars and existing extension requests. Bind environment policy revision/hash and actual normal-home authority identically. No new read/write grants. Native normal account/config/cloud behavior remains D03 PLATFORM_POLICY; include-managed-config can perform auth/cloud bootstrap. Host never reads/copies credentials.

Argument vector (template only; not runnable scope): pinned Codex executable, then ordered `-c <canonical pair>` arguments, then `sandbox`, `--include-managed-config`, `--permission-profile`, `<qualificationNonce>`, `-C`, `<W>`, `--`, `<S>\qualification-helper.exe`, `--plan-v1`, `<fixed encoded plan>`. Use actual canonical backslash Windows helper path; no cmd.exe shell. Select fresh nonce as in B1 and omit extends. Before Root execution, freeze every actual argv element and rendered digest; the security projection digest must be traceable to B1's template despite the separate command transport. Do not pass --ignore-user-config to sandbox, or add --sandbox-state-readable-root, --add-dir, prefer_mxc, unsafe or setup.

Use existing original owned-Job launch/stop primitives. Qualification has its own named Job/creation identity and receipt; B1 subsequently owns its separate model process Job. Do not change f13/Kernel or fabricate shared Job membership. Suggested fixed qualification budget: one top-level Native invocation, <=16 total processes in its tree, <=2048 MiB Job memory, <=35s soft /45s hard /5s cleanup, <=60s entire qualification including controls, helper <=10s, each connect <=1s, capture ingestion <=1MiB per stream and <=64KiB durable prefixes. Existing tighter constraints win. Explicitly account for this inside the Task's 300s total deadline. A combined Root outer scope must accommodate preparation plus RPC/model budgets without nesting incompatible Job behavior; verify ownership through fake child tests, not assumptions.

Collector persists bounded diagnostics from first chunk, pauses/stops ingestion at bounds and stops the Job; full hash only for streams actually completed. Collect child exit, stream drain, case bitmap, postcontrols and Job-zero proof before OBSERVED_PASS. Keep failure artifacts; cleanup timeout or unknown child ownership -> UNKNOWN. No externally loaded archived artifact can reconstruct the live observation. Failure receipt is not permission to retry.

## Failure taxonomy and narrow report

QUALIFICATION_REQUIRED: no production producer/scope. QUALIFICATION_SCOPE_MISMATCH: wrong source, Task, budget or identity. QUALIFICATION_BOOTSTRAP_BLOCKED: helper/startup unavailable under exact grants. QUALIFICATION_POLICY_VIOLATION: any forbidden access/connect succeeds. QUALIFICATION_CONTROL_INVALID: synthetic pre/post baseline or listener control fails. QUALIFICATION_INCOMPLETE: timeout, output cap, parse/case/IO failure. QUALIFICATION_IDENTITY_CHANGED: binary/build/template/env/boot mutation. QUALIFICATION_CLEANUP_UNKNOWN: cannot establish termination/Job-zero.

Map these bounded reasons through existing HARNESS_UNAVAILABLE/pre-model failure lifecycle; only known completed cleanup permits confirmed failure. Unknown cleanup remains existing reconciliation state. All are nonretryable for that consumed attempt. Public rev2 fields stay UNVERIFIED and enforcement_verified=false; report `OBSERVED_CASES_MATCH_REQUEST` only for the exact fixture operations/IPv4 tuple, with Native startup and global-context limitations. B1 same-start barrier and BeforeModelTurn remain mandatory regardless of this report.

## Small source lease and B1 adaptation

New adapters/runtime/codex_qualification_windows.go: concrete producer, trusted constructor wrapper, private live result, job collector and evaluator. New adapters/runtime/codex_qualification_plan.go: narrow schema/case identity builder (no public decoder into authority). New cmd/researchos-qualification-helper/main_windows.go: standalone synthetic helper; no dependencies added. New matching qualification/helper tests. Minimal adapters/runtime/codex_rpc_windows.go adaptation only for constructing/wrapping with the concrete producer; preserve B1 bool test provider and original closed constructor. internal/host/harness_windows.go chooses production constructor from actual Host composition; no HTTP setup endpoint. Existing domain result/event mapping changes only if required to preserve bounded failure reasons; exact additional file must be included by Root before edit.

Production wrapper must not use NewCodexRPCForTrustedGoTest to bypass composition. Runtime package creates the private provider internally. The approved helper's file/build hash is fixed by Host's shipped artifact identity, not a hash supplied by a Task. B3 source can ship closed if that approved helper or execution authority is missing; no installer or user setup flow.

## Eight implementation checks

1. Production constructor/provider boundary: JSON/env/archived PASS cannot qualify; old constructor remains closed; GET capabilities never invokes helper/Native.
2. Once/cancel: concurrent Starts consume at most one qualification attempt; cancellation and failed result never respawn; qualifier failure means zero model RPC spawns/user prompt bytes.
3. Identity mutation: changed native/helper/template/build/env/boot/source/Task/epoch or expired observation fails; historical evidence never recreates private state.
4. Canonical argv/plan: exact security projection equality to B1; nonce uniqueness; no extra grant/extends; proper quoted synthetic paths; denied/cwd roots outside S; no generic command/URL or actual data path accepted.
5. Positive-control adversaries: missing/read-only/locked fixture, changed bytes, bogus denial code or helper fabricated expected hash cannot PASS; successful forbidden open/create always fails and preserves evidence.
6. Network false-positive adversaries: absent listener/refusal/timeout, failed postcontrol and ambiguous accept cannot PASS; unexpected helper connect always fails. Use loopback fake helper only, no Native.
7. Actual owned fake-child collector: partial lines, overflow, hard stop after first output, wrong/missing bitmap, exit mismatch and orphan descendants retain bounded evidence and cannot PASS; prove Job cleanup rather than callback ordering alone.
8. End-to-end fake composition: live qualification plus B1 matching thread barrier and both domain fences permits exactly one frozen turn; qualification alone, wrong thread/profile or revoked owner cannot. Old failed Task and echo 2/2 counters are unchanged.

## Root must freeze before any real invocation

- New diagnostic origin/attempt=1, exact source lease/review pins, approved helper source/build/hash, native canonical path/hash/version, Host binary/build/boot and Windows build.
- Actual S/W/D paths/ancestor identities, synthetic filenames/content hashes, nonexistent create targets, first model Task's S binding and trusted owner authorization.
- Exact argv array, ordered -c projection and rendered hashes, environment policy revision/home constraints, no credential contents.
- Listener address/actual dynamically allocated port and distinct control/helper nonce scheme; bound controls/deadlines; accepted native error codes.
- Qualification limit=1 Native command; model limit=1 newly created Task/first turn conditional on PASS; B1 RPC process limit=1. These counts are distinct from total Job descendants; old echo budget stays consumed and Native lifetime accounting continues.
- Account kind=existing ChatGPT account; no API key fallback, login attempt, setup/admin action or paid fallback. Native bootstrap/context may use the normal platform account.
- Per-phase/overall time, process/memory/output budgets, original Job/controller identity, output locations and no-overwrite receipt names.
- Runtime failure/unknown mapping, cancellation/cleanup and prompt-byte observation; if qualification fails, stop that attempt with no model input and no automatic resubmission.

This document supplies no actual execution scope, helper binary, fixture tree, listener or registration. It is ready for Root to lease the concrete producer implementation, followed by independent review and one explicitly frozen conditional synthetic acceptance run.