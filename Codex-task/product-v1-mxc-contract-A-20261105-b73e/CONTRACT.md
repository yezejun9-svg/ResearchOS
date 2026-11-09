# Frozen Slice A contract (Root accepted, CP663 baseline)

Source implementation belongs to Root's separately leased author. This document is C-only preparation; no product edit, CLI/model/probe/setup, test execution or runtime scope occurred. Historical Task 449cdce6ba09adefcbaa57e95e2e9411 remains failed/consumed; MXC echo attempts remain 2/2 consumed. A later new synthetic Task is distinct and requires the approved gates and execution scope.

## Identity and revision constants

Policy revision: researchos-codex-mxc-readonly-v1
Requested Windows sandbox: mxc
Requested permission profile: researchos-readonly
Sealed sandbox identifier: codex-mxc-permissions-workspace-read-v2
Sealed command identifier: codex-mxc-readonly-v2
Keep backend/adapter family codex-cli-readonly-v1 / codex-cli-harness-v1; the new sandbox/command/policy identity must distinguish this behavior even when the native binary hash is unchanged.

CodexPolicyIdentity fields: Revision, WindowsSandbox, PermissionProfile, RequestedConfigSHA256, BinarySHA256. RequestedConfigSHA256 is computed by one canonical Host policy builder over the complete requested configuration/template including the source placeholder, mode, filesystem, network, approval and existing extension requests. It is not a renderer-provided hash and not an effective-managed-policy claim. BinarySHA256 uses the existing executable SHA256 representation consistently.

Exact requested permissions remain :root deny; :minimal read; :workspace_roots '.' read; source workspace bound by trusted Host resolution; network.enabled=false; approval_policy=never. Add only explicit windows.sandbox="mxc" to production requested policy. No prefer_mxc, fallback, full access, new write grant or owned-cwd write. Preserve ignore-user-config and the existing native context boundary.

The source placeholder is resolved only from existing h.workspace/dispatch authority. The template identity and the actual source binding are different facts. Revalidate workspace principal/project/access/status/canonical real path/revision through the existing authority and dispatch gates; do not hash a user JSON claim as source authority. Slice A must not claim the resolved native effective permission set has been measured. If adding a stronger immutable source binding to the submission record, use only Host-produced fields and review it explicitly; do not silently rebind old Tasks.

## One readiness contract

CodexReadiness: State = UNVERIFIED | UNAVAILABLE | READY; Reason; PolicyIdentity. Suggested reasons: PERMISSION_PROFILE_UNVERIFIED; PERMISSION_PROFILE_UNAVAILABLE; CODEX_POLICY_IDENTITY_MISMATCH; existing installation/auth/config reason codes retained.

Use one EvaluateCodexReadiness function for capabilities, submit, scan, launch, BeforeResume, plus the driver's prelaunch check. Check installation, controlled config, login, any unavailable reason, exact expected policy identity and trusted readiness state. Any missing/mismatched/unknown input blocks. Shared gate must produce the same can_submit and reason semantics; query APIs do not launch a probe.

Production NewCodexCLI remains UNVERIFIED / PERMISSION_PROFILE_UNVERIFIED throughout A. No constructor bool, descriptor JSON field, external receipt import, environment variable or CLI switch may mint production READY. A successful echo and synthetic fixture labels cannot do so. A later producer requires an independently reviewed same-start effective-policy barrier; it is not implemented in A.

Test injection is trusted Go composition, not isolation from arbitrary same-user Go code: an auditable Go-only provider/interface can supply fake readiness to the real NewCodexCLI argv/owned-child lifecycle for existing domain fake-executable tests. The actual Host composition uses the production unverified provider. No HTTP/renderer/CLI/env path constructs or selects the fake provider. Do not add allowUnverified. CodexDriver may gain ReadinessSnapshot (or an equivalent separately typed interface); injected fakes exercise the same gate. Production Descriptor.Policy/Options values alone are not evidence authority.

At each gate obtain a fresh snapshot, compare to the sealed policy identity and fail closed on changes. BeforeResume repeats the gate while the child remains suspended; refusal uses existing owned Job stop/receipt handling. Claimed/consumed dispatches must never be automatically relaunched after a gate or policy failure.

## Existing store and sealed profile binding

Add native_policy_revision, requested_config_sha256, windows_sandbox, permission_profile to the Host-sealed RuntimeProfile. Retain build_hash and the new sandbox/command IDs above. Validate required nonempty fields and exact constants in profile creation/reuse, native admission and dispatch validation; compare the seal with the current driver policy identity before launch/resume. A forged content hash is not trusted Host readiness.

Reuse sealRuntimeSetupProfile -> uploaded_content/sealed Artifact -> runtime_bindings -> existing dispatch admission. runtimeProfileBody already verifies bytes against content_hash; runtimeTechnicalHash alone omits this new policy and is insufficient. No new database/scheduler/qualification boolean store. Existing generic v1 profiles must fail new admission; create a distinct current binding/registration by the existing reviewed setup path if needed, never rewrite an old profile/task/result. Historical read/list/get remains available even when current readiness is false.

## Exact Slice A source scope

- adapters/runtime/codex.go
- adapters/runtime/codex_driver_windows.go
- adapters/runtime/codex_policy.go (new shared identity/gate)
- adapters/runtime/codex_driver_windows_test.go
- adapters/runtime/codex_policy_test.go (new focused pure cases if needed)
- internal/domain/runtime_harness_windows.go
- internal/domain/harness_v1.go
- internal/domain/runtime_dispatch.go
- internal/domain/runtime_harness_windows_test.go
- internal/host/harness_windows.go
- internal/host/harness_windows_test.go

No changes to f13/Kernel/Job owner, UI authorization, model budgets, old records or product filesystem policy. Root controls the implementation lease and exact final scope if a new call-site compile adjustment is required.

## Eight meaningful checks

1. Parse argv config pairs: exactly one explicit mxc selection and exact root/minimal/source/network/approval policy; reject duplicate/conflicting mode or profile overrides, preserve escaped synthetic source paths.
2. Production constructor plus forged descriptor READY / external receipt-like JSON / ambient env cannot pass readiness or launch; query calls never invoke executable.
3. Trusted Go-only fake readiness reaches the real owned fake executable with actual production argv; no fixtureArgs replacement can stand in for this assertion.
4. Readiness table covers missing/UNVERIFIED/UNAVAILABLE/auth/config/reason/policy-hash failures consistently through capability, submit, scan and prelaunch paths; all blocked cases have zero resumed children.
5. A provider mutation between admission and BeforeResume is rejected and the suspended child is owned/stopped with no model event; identity changes include binary/template/mode.
6. Missing v2 fields, old sandbox/command IDs and stale sealed policy identity fail admission/reuse. No silent upgrade; historical failed Task/result remains readable and unchanged.
7. Fake child emits pre-thread sandbox failure: bounded reason and raw artifact remain, no assistant/thread fabricated, stop proof retained, dispatch consumed once/no retry.
8. Existing authority revocation/workspace revocation/expiry/epoch cancellation/idempotent request semantics still block through the same gates; a successful fake response never updates production enforcement verification.

## Concrete limitation discovered in pinned native source

In rust-v0.166.0 [resolve_default_permissions](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/config/mod.rs#L4859), a disallowed selected profile is replaced with the managed fallback after a warning; the fallback is compiled before the original runtime profile is captured. Thus requested researchos-readonly can be replaced by :workspace. The later permission constraint path also falls back and clears active-profile binding. This disproves a universal unchanged-or-reject guarantee for the requested named profile. Explicit MXC differs: [windows_sandbox_config](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/config/windows_sandbox_config.rs#L84) first checks whether MXC is permitted. [Sandbox -P](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/cli/src/debug_sandbox.rs#L654) just supplies default_permissions and cannot bypass the profile fallback. These are source facts, not evidence that this host currently has such managed requirements.

This is a specific policy-binding limitation, not a demand for perfect global context isolation or a private config generation API. Slice A remains deliverable now, honestly blocked. Slice B must find/use a same-start fail-closed effective-profile selection/inspection boundary before production READY; past probes plus expiry do not close the identified replacement path. Native outer authentication/cloud networking remains PLATFORM_POLICY; sandbox workload network denial says nothing about outer Native connectivity.