# Explicit coding private IPC v1 — Source candidate contract

Transport remains the dedicated inherited anonymous stdin/stdout pipe, `researchos-desktop-management/1`, maximum UTF-8 frame 65536 bytes including all paths. Existing PREPARE, CONFIRM, STATUS and SHUTDOWN operations retain their shapes. No token, principal, executable PID, owner root, credentials or full frozen tool-policy fields are accepted from the caller. Host derives the OS parent identity and Owner internally.

## PREPARE_CODING

Common required fields: `protocol`, `message_id`, `operation:"PREPARE_CODING"`, `host_id`, `project_id`, `session_id`, `model_config_ref` (the session's CURRENT model reference), `coding` below. No request_id/request_hash. Duplicate keys at any depth, unknown fields, mixed operations, escaped duplicates and trailing input are refused.

```json
{
 "client_id":"original-current-client", "expected_revision":1, "writer_epoch":1,
 "config_revision":2, "workspace_ref":"original-session-READ_WRITE-workspace",
 "read_paths":["go.mod","calc/value.go","calc/value_test.go","notes.txt"],
 "write_paths":["calc/value.go","notes.txt"],
 "max_read_bytes":8192,"max_write_bytes":8192,"max_tool_calls":8,"max_output_tokens":2048,
 "checks":[{
   "id":"value-check","package":"./calc","test_pattern":"^TestValue$",
   "source_paths":["go.mod","calc/value.go","calc/value_test.go"],
   "toolchain_root":"C:/explicitly-selected-installed-go", "vendor_root":"C:/explicitly-selected-offline-vendor",
   "timeout_seconds":90,"process_limit":32,"memory_mib":1024,"max_text_bytes":4096
 }]
}
```

`vendor_root` may be omitted for a standard-library-only check. All relative paths are exact canonical forward-slash paths, case-insensitively unique, with no glob or traversal. Write paths must appear in read_paths. Read paths <=512, write paths <=64. Every check's source_paths is an explicit subset of read_paths, <=512 files/32 MiB; checks 1..8. Read/write limits 1..65536 bytes; toolcalls1..32; outputtokens1..8192. Timeout1..120s; process2..32; memory256..1024MiB; text1..8192bytes. Exact package excludes `...`; test selector anchored `^...$`, must match an explicitly included test. Missing local production dependencies, go.mod/go.sum, same-package helper or embed members are rejected with their missing name and never silently added. No model, subprocess, shell or Go command executes during preparation.

The current session writer lease, expected_revision/writer_epoch, original Owner/project/workspace, current configuration and next head revision must match. `config_revision` is current host head +1, not necessarily old session config revision +1. Only credential-free numeric-loopback current configuration is supported.

Successful RESULT.result is:

```json
{"state":"AWAITING_CODING_CONFIRMATION","request_id":"...","request_hash":"sha256:...","expires_at":"RFC3339Nano","project_id":"...","session_id":"...","old_model_config_ref":"...","scope":{},"frozen_checks":[{"id":"...","package":"./calc","test_pattern":"^TestValue$","source_count":3,"source_bytes":123,"source_manifest_hash":"sha256:...","toolchain_hash":"sha256:...","build_hash":"sha256:...","vendor_hash":""}],"normal_max_model_calls":8,"qualification_model_calls":1,"qualification_tool_calls":0,"model_calls":0}
```

`scope` is the full exact coding input. Confirmation expires 60 seconds after completed preparation. Present a human-readable path/check/limit summary and require explicit confirmation of THAT result. Preserve request_id/hash privately in Desktop main; no credential is returned. PREPARE leaves current configuration untouched.

## CONFIRM_CODING

Common fields plus operation `CONFIRM_CODING`, project_id, request_id, request_hash only. No session/model/coding fields. Host rechecks original parent, Owner root, current session/writer/config/workspace and exact frozen source/toolchain/vendor bytes, then performs existing host.configure CAS and the new immutable authorization/profile/qualification plan in ONE transaction. Runtime remains REGISTERED; no model or tool executes. Consumed confirmation cannot be replayed.

RESULT.result: state `CODING_CONFIGURED`, request_id/hash, project_id, session_id, NEW model_config_ref, old_model_config_ref, runtime_id, runtime_status `REGISTERED`, profile_ref, revision (new session revision), config_revision, configuration_command_id, scope, frozen_checks, normal_max_model_calls8, qualification_model_calls1, qualification_tool_calls0, model_calls0.

Refresh the ordinary session/configuration views from original V2 responses. Keep the NEW model_config_ref for the existing qualification PREPARE→explicit CONFIRM sequence. Qualification uses the same immutable coding profile/config hash but existing effect gate permits only one MODEL and refuses TOOL effects. It proves model transport only, not tool success or coding semantics. Tool schemas remain frozen in that model config and may be advertised to the model; any attempt to use a tool during qualification is refused.

## STATUS_CODING

Same exact fields as CONFIRM_CODING, operation `STATUS_CODING`. Returns original CODING_CONFIGURED result if committed, otherwise original preparation projection with state AWAITING_CODING_CONFIRMATION or EXPIRED. No replay, repair, new confirmation, config installation or model invocation. For lost result, read this status before any explicit new action.

ERROR envelope remains kind ERROR and error `{code:"MANAGEMENT_REJECTED",message:"..."}`. EOF closes only the link. A committed config is durable even if subsequent offline route reconciliation or output write fails; STATUS reads that original result.

## Current evidence limits

Source is frozen at 860a8935c8fffe4a1671eafa177e7fc5a053158a. New full synthetic Host/Mu/verifier attempt29 passes: coding qualification 1 MODEL / 0 TOOL effects, ordinary turn 5 MODEL / 4 TOOL (read/edit/write/run_check), native Go exit0 with stopped/drained/cleanup true, subsequent model response and canonical Run SETTLED, private SHUTDOWN accepted. Six original MODEL UNKNOWN/null entries remain unchanged; the identical ledger still refuses release promotion. Prior failed attempts are retained. Real model calls 0. This is source/native-fixture evidence, not live model, Electron user-flow or formal acceptance.

Final frozen attempts36/37 pass with zero skips, including the three original opt-in control/Host cases and the full four-tool chain. See source-bundle-final.json for exact source, binaries and raw logs.
