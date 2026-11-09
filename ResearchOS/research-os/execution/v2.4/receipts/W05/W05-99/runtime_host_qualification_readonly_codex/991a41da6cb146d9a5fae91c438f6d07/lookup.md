# Main Host runtime qualification lookup (read only)

Source HEAD observed: `adc460c2138528f163f7fdab5e8d81dde157b7fb`. This is static source inspection only. No Host, provider, CLI, qualification, or database operation was run.

## Finding

`apps/control/main.go:48-52,213-248` accepts `--runtime-coordinator-config`, `--trial-readonly-model-vault-dir`, `--trial-readonly-credential-ref`, and `--trial-readonly-provider`. It loads the private JSON, fills `data_root` and `api_url` if absent, attaches trusted workspace/configuration/model-credential/tool ports, and runs the coordinator. Trial vault flags must be complete and require the isolated, existing vault layout (`apps/control/main.go:64-70`). The normal coordinator `Scan` selects READY tasks whose type is **not** `runtime_qualification` (`internal/domain/runtime_coordinator_windows.go:258`). Therefore starting `apps/control` with the JSON does not itself create or start the qualification TaskRun.

The qualification launch is a trusted, local `Service` operation, not an exposed HTTP/CLI command: `RegisterRuntimeQualificationPlan(ctx, ownerToken, project, taskID, runtimeID, sealedProfileRef, requiredCapabilities, maxValidity, resumeCheckID)` (`internal/domain/runtime_qualification.go:45-47`); then `BeginRuntimeQualification(ctx, ownerToken, project, taskID, runtimeID, executorID)` returns `(run, lease, error)` (`internal/domain/runtime.go:19-39`); then `coordinator.RunAdmitted(ctx, route, run, lease)` (`tests/e2e/live_setup/qualify.go:182-229`). A new trusted Host command or bounded local orchestrator is needed for a normal CLI-driven bootstrap if that existing test-only setup cannot be used. Adding only an HTTP route would cross the current trusted boundary.

## Exact private coordinator JSON shape

`internal/domain/runtime_coordinator_windows.go:30-50` and `internal/domain/runtime_broker_windows.go:24-42` define these serialized keys. Values below are placeholders, not live credentials or provider settings.

```json
{
  "data_root": "<absolute-isolated-data-root>",
  "api_url": "http://127.0.0.1:<host-port>",
  "scheduler_token": "<short-lived-project-SCHEDULER-token>",
  "routes": [{
    "project_id": "<project-id>",
    "runtime_id": "<runtime-id>",
    "executor_id": "<project-EXECUTOR-principal-id>",
    "executor_token": "<short-lived-EXECUTOR-token>",
    "command_id": "<frozen-profile-command-id>",
    "executable": "<absolute-executable-path>",
    "bundle_file": "<absolute-frozen-bundle-path>"
  }],
  "providers": [{
    "id": "<frozen-route-id>",
    "project_id": "<project-id>",
    "runtime_id": "<runtime-id>",
    "purpose": "runtime_qualification",
    "capability": "MODEL",
    "credential_revision": "<frozen-credential-revision>",
    "endpoint": "<frozen-model-endpoint>",
    "upper_bound": {"amount": "<positive-cost-bound>", "currency": "USD"},
    "measurement_mode": "LIVE",
    "model_config": {"<key>": "<must-equal-frozen-profile-model-config>"},
    "credential_ref": "<sealed-host-credential-ref>"
  }]
}
```

`data_root` must be the SQLite database's parent, `api_url` must be loopback HTTP, `executable` absolute, and `command_id` nonempty (`runtime_coordinator_windows.go:91-150`). The scheduler token must resolve to SCHEDULER on that project and executor token to the exact bound EXECUTOR principal (`:153-175`). The provider route must match task type, capability, measurement mode and the frozen profile's effect route/config (`runtime_broker_windows.go:45-78`). `WorkspaceAuthority`, `ConfigurationAuthority`, `ModelCredential`, `ClientSchema`, and `RunTool` have `json:"-"` and must be attached in process by Host; they cannot be supplied in the JSON (`runtime_coordinator_windows.go:35-42`). The existing `tests/e2e/live_setup/plan.go:374-405` creates a concrete configuration with two MODEL purposes (`runtime_qualification` and `mu_turn`) plus a TOOL purpose. Its W14 model, budget, paths, and 900-second profile timeout are task-specific and should be regenerated for a new 300-second run, not copied as authority.

## Bounded qualification sequence and principals

1. Bind local OWNER through the OS Host, create a real project and prepare a sealed profile Artifact. The existing test setup illustrates `Host.BootstrapOwner` (`tests/e2e/live_setup/main.go:96-136`), Native workspace chooser and `RegisterWorkspace`/`BootstrapProject` (`prepare.go:78-130`), and Native credential import (`prepare.go:132-146`). The Native transport frame is `{kind, client_id, payload}` (`prepare.go:59-66`); chooser `kind=NATIVE_WORKSPACE_CHOOSE_REQUEST` receives `{requested_path, requested_access}` and credential import `kind=NATIVE_CREDENTIAL_IMPORT_REQUEST` receives `{provider_id, credential_kind, credential_value, replace_credential_ref}` (`prepare.go:93,139`, `internal/host/native.go:25-27`). `Host.BootstrapOwner` rebinds an existing OWNER and only creates one if the DB has no principals (`internal/host/bootstrap.go:42-100`). There is no HTTP bootstrap route.
2. Via authenticated v1 HTTP, create a runtime candidate and dependency-free draft `runtime_qualification` Task. The exact `CreateRuntimeRequest` fields are `name, adapter, adapter_revision, capabilities, platform, measurement_mode, credential_ref`; `CreateTaskRequest` fields are `goal_id, title, task_type, stage, dependency_task_ids, requirement_refs, input_refs, acceptance_contract, origin_problem_id, candidate_id, stop_policy` (`spec/v2.0/contracts/domain.schema.json` `$defs`). The profile Artifact ref must be in `input_refs`; the task must be DRAFT and have no dependencies. The existing example constructs these requests at `tests/e2e/live_setup/plan.go:47-169`.
3. Register the plan through local `Service` under OWNER, with a current sealed profile matching runtime technical hash, backend, model, permissions, capability set, budget ancestry and finite validity (`runtime_qualification.go:47-163`). Begin under the same OWNER authority root, with a valid project EXECUTOR principal (`runtime.go:19-39`; `runtime_qualification.go:293-350`). Dispatch once via `RunAdmitted`; a prior begun run must be recovered, not launched twice (`tests/e2e/live_setup/qualify.go:19-45,182-229`).
4. On SETTLED run, use independent VERIFIER credential for `POST /v1/projects/{project_id}/acceptances` with exact `CreateAcceptanceRequest` fields `subject_ref, run_id, contract_hash, input_refs, artifact_refs, checks, verdict, executor_principal_ids, independence_basis, blocking_conflict_ids, qualification_ids, policy_revision, measurement_mode, reason`. Then call `POST /v1/projects/{project_id}/runtimes/{object_id}/qualify` with `qualification_ids, supports_resume, resume_evidence_ref, receipt_artifact_ref`. `qualifyRuntime` validates the acceptance and native observation before assigning AVAILABLE (`tests/e2e/live_setup/qualify.go:45-143`; `runtime_admission.go:181-254`). Do not manufacture these state rows directly.
5. For ordinary work, authorize the needed purpose through the trusted local owner call (`tests/e2e/live_setup/qualify.go:146-180`), then the normal Host coordinator scans READY non-qualification tasks and claims them over v1 HTTP as SCHEDULER. The `ClaimTaskRequest` fields are `runtime_id, executor_principal_id, context_bundle_id` (`runtime_coordinator_windows.go:253-330`, schema `$defs`). An available runtime alone does not authorize every task type.

HTTP v1 writes use `Authorization: Bearer <role-token>`, `Idempotency-Key`, and object/project `If-Match: "r<revision>"` as appropriate; the existing helper implements these at `tests/e2e/live_setup/api.go:61-127`. Never place raw credentials in receipts or renderer-visible command envelopes. Trusted principal provision/credential issuance are local methods, absent from HTTP (`internal/domain/auth.go:27-70`). The CLI's accepted command verbs use the typed `/v2/command` service, so the v1 calls above describe Host setup plumbing, not an existing CLI `qualify` verb (`internal/api/server.go:34-63`, `apps/cli/cli_http.go:3-7`).

## Product gap for Root's target path

For an empty DB followed by real CLI init draft, the repository still needs a trusted local qualification control path that binds the CLI-created project/task and sealed profile to `RegisterRuntimeQualificationPlan`, calls `BeginRuntimeQualification` and `RunAdmitted` once, persists/reconciles the run identity, and surfaces its result for independent VERIFIER acceptance. The current `apps/control` flags provide coordinator resources for ordinary READY work, not that launch. The reusable reference is `tests/e2e/live_setup`; it is a W14 test program with fixed candidate/model/profile/budget, not a general product Host API. A 300-second total budget must be reflected in the new frozen profile/task stop policy and outer controller, rather than inherited from the W14 900-second profile. This is an inferred implementation gap from source inspection, not an execution failure.
