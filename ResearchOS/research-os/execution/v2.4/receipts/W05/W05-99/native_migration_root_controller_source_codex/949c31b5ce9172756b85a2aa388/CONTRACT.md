# Root-only native migration controller

Status: SOURCE_ONLY_PENDING_ROOT_INDEPENDENT_REVIEW_AND_ACTUAL_EXECUTION.
This package supplies one persistent controller and one minimally extended owned-process helper. It does not alter e57c/7050, Main, T3/T4/T5, fixture schema, production authority or the private-stdin broker. The Source author executed only Python construction/AST/metadata work.

## Public controller configuration

Every API takes config_ref = {path, sha256, bytes}; the hash includes sha256:.
The referenced JSON has exactly these PascalCase keys:

- Schema = researchos.root-native-migration-controller.v1
- ControllerDirectory = fresh absolute path, parent already exists
- ControllerSource, HarnessConfig, TestProgram, ObservedOwnedHelper, OriginalOwnedHelper, SourceReadGuard, CompilerInventory, BuildInvocation = exact public refs
- FrozenInputs = a deduplicated list of public refs including every preceding ref, all seven RawPins from HarnessConfig, the actual selected compiler/source/tool inputs and actual loaded Python/native runtime modules
- Environment = reviewed public fixture environment, limited to the Source allowlist

ControllerSource and ObservedOwnedHelper point to this package's two Source files. OriginalOwnedHelper is the unchanged reviewed windows_owned_process.py. SourceReadGuard is the reviewed held-handle guard. Root converts plain build-receipt hashes into sha256:-prefixed refs. No issuer DPAPI path, Owner value or private resource reference belongs in this configuration or FrozenInputs.

Root's existing positive HarnessConfig ef404512f197dda8223526af9f301fa922b54a84416e43094f79202e70f9fd32/2784 and T5 native-migration-harness.test.exe are public inputs, not modified by this package. The controller runs test.exe directly with cwd = HarnessConfig.BuildRoot/internal/domain and fixed arguments:
-test.run=^TestNativeMigrationAuthorityHarness$ -test.count=1 -test.timeout=25m

Each case requires a separate fresh ControllerDirectory, HarnessConfig.OutputDirectory and Root/Control program directory. Root and Control must share that case program directory; the two signed fixed files and consumed-schema23-to24-grants must not exist at start. Root copies and pins the four accepted programs before starting; no private sidecar is installed. Positive's single planned replay stays within its case.

The controller requires its actual Python executable to match HarnessConfig.PythonProgram. Root launches the controller with that executable and -I -S -B -X utf8 under the existing Root-owned outer lifetime. Freeze the Source guard itself before bootstrap. The server verifies FrozenInputs once with retained read-only handles; polling does not rehash the whole compiler inventory. Loaded module paths must already be included in Root's public inventory. The helper supports 256 MiB per file and 2 GiB total guard bytes.

## Controller API

serve(config_ref) blocks for the complete case. It creates the test process suspended, assigns it to a fresh unnamed exclusive KILL_ON_JOB_CLOSE Job, then resumes it. The same held Job and process handles span release-payload pause, grant-payload pause and fixture-release pause. It creates no approval and calls no signer. Root may run serve in its existing asynchronous owned process.

poll(config_ref) requests a fresh observation from the helper that owns the actual handles; no PID lookup or reconstructed process ownership is used. It returns a public response ref containing PID, creation time, stable runtime job_binding_id, actual active-process count and current phase. The response is produced only from the owned helper's held-handle observation. A job_binding_id is a controller-issued identifier for that actual handle binding, not an OS job name or proof of the production Root's different inner Control Job.

snapshot(config_ref) creates an immutable public review artifact for release, grant or fixture-retained. It records the current held-Job observation, exact config/payload/readiness/compiler/build refs, typed-row inventory refs, declared versus observed public file pins and independent native root/DB file identities. Deliberate negative source-pin/DB-identity mismatches remain visible for Root review. The snapshot is never approval. The controller does no SQL read; Root independently reads the retained actual DB.

stop(config_ref) publishes the exact public cancellation request. The observed helper uses its own retained Job handle for termination and bounded exit/idle cleanup. This does not release the fixture as an accepted result.

Public CLI:
python -I -S -B -X utf8 root_native_migration_controller.py serve|poll|snapshot|stop <config-path> <sha256:-digest> <bytes>

CLI stdout contains only a public result ref. Exceptions print error type only. serve returns nonzero if the test or required process/guard closure fails.

## Root signing and publication are separate decisions

sign_reviewed(config_ref, approval_ref, issuer_dpapi_path_runtime) is API-only. Root supplies the private DPAPI resource path only as a runtime argument in its protected execution context. Do not put it in tool logs, scripts, config, public arguments receipts or saved wrappers. The controller never opens that private resource. It passes the in-memory path to the genuine native enrollment CLI:
sign-reviewed release|grant|migration-grant <runtime-private-path> <exact-public-payload> <new-fixed-signed-output>

The signer itself runs suspended in a separate owned Job and must exit zero with whole-Job idle and handles closed. Its stdout/stderr go to NUL because file/DPAPI errors may disclose the private path. The public signing receipt retains the actual process/Job result, public payload/output refs and guard closure, but omits the private argv value. This output-discard decision is explicit; raw signer diagnostics are unavailable in this receipt.

The concrete sign approval JSON has exactly:
Schema = researchos.root-native-concrete-approval.v1
Action = SIGN_EXACT_REVIEWED_PUBLIC_PAYLOAD
ConfigSHA256 = exact controller config digest
Snapshot = exact Root-reviewed snapshot ref
Payload = exact public payload ref
SignedDestination = snapshot's fixed case destination
SignKind = release, migration-grant, or grant only for the wrong-purpose negative

Root creates and pins that approval after inspecting the snapshot. The controller verifies the current case, phase, held Job, exact payload, readiness, source pins and native identities. An O_EXCL consumed marker permits one signing attempt for the phase. Partial/failed signing is inspected; no retry or overwrite is performed. For grants, issued-to-expiry must be positive and <=240 seconds, and current absolute validity must still hold. Only the expired-grant case requires expiry already in the past. No timestamp or nonce is extended.

sign_reviewed returns a public signing receipt; it does not wake the test.
Root independently inspects the actual signed wrapper and then calls:
publish_signed(config_ref, approval_ref)

This second approval has the same schema/fields, Action = PUBLISH_REVIEWED_SIGNED_DOCUMENT, plus SignedDocument and SigningReceipt exact refs. Complete embedded payload bytes must match the original Go-marshaled payload. Only then is the exact harness 01-release.approval.json or 02-grant.approval.json created. Production Root remains the signature/capability authority. The controller does not claim cryptographic verification from JSON shape checks.

## Retained fixture release

When the test reaches 06-fixture-retained.ready.json, Root calls snapshot again and independently inspects the actual fixture and raw native outputs. Early fixture failures can use the actual database path in that retention receipt when the usual public summary was not yet emitted.

Root supplies a separate immutable inspection receipt containing at least:
config_ref, snapshot_ref, fixture_read_complete=true,
whole_row_schema_review_complete=true, private_credentials_recorded=false.
Those fields are Root's independent review assertions, not SQL checks performed by this controller.

release_fixture(config_ref, approval_ref) requires exactly:
Schema = researchos.root-native-fixture-release.v1
Action = RELEASE_AFTER_INDEPENDENT_FIXTURE_INSPECTION
ConfigSHA256, Snapshot, InspectionReceipt.

It checks the retained phase and same live Job, binds the concrete inspection artifact and then creates only {"Action":"release-fixture"} at the harness release path. A failed case may be released after inspection without being accepted. No deadline handler, signer or poll operation creates fixture release approval.

## Lifetime and remaining checks

The test Job timeout is 1260 seconds, above the harness's 20-minute review window and below its 25-minute Go deadline. Cancellation and timeout use original whole-Job cleanup. Source handles remain held until the worker finishes. If worker/exit/idle/handle closure cannot be confirmed, controller.closed.json records failure; it never reports accepted native authority. A hard kill or expired Go review window cannot guarantee graceful fixture retention, as already documented by e57c.

windows_owned_observed.py is the original helper plus public observation callbacks and a cancellation predicate. No native handle leaves the helper. The exact inverse change check recovers the original raw bytes. The process creation, explicit handle allowlist, assignment-before-resume and cleanup bodies otherwise remain intact. Root must independently review this delta and validate its actual observation/cancellation behavior before using it with the Owner-bearing harness.

The nine-case matrix and exact first-log-line error assertions remain entirely in the existing e57c test binary. This controller adds no case loop and no new schema fixture. Root drives the isolated cases individually and retains broader FULL failures separately. Exact prepared abandonment remains outside this package.

Failure 805 is separately sealed and referenced. It was a distinct nonexistent signer Source-path read, actualOuter=1, Python/native=NULL. It is not merged into earlier failure 800. No Source-author signing, Go/native/SQL execution or private-resource read occurred.

