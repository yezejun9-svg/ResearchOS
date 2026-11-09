# W09 exact header metadata recovery candidate v3

Status: SOURCE_CANDIDATE_AWAITING_NONAUTHOR_REVIEW. Author: `/root/resume_audit`.
This candidate does not issue formal acceptance or authorize product execution.

Read `candidate-v3-manifest.json` first. It pins the certificate, exact two
production-source files, a patch, original source archives and actual test output.
`header-correction.candidate-v1.json` is retained as an earlier candidate; only v3
is proposed for review. The old Context, independent review, issuance, captures,
scopes and all product assertions remain unchanged.

## Implementation boundary

- Modify only `execution/v2.4/formal_profile_w09.py` on future reviewed adoption.
- Add `execution/v2.4/w09_header_correction.py` at its fixed repository path.
- `formal_case_index.py` remains byte-identical to the old Context pin.
- Current source-only validation has 26 passing test methods. Tests cover the
  real 18 historical ranges and isolated negative controls. No runtime/Native,
  consumers, synthetic peer message or formal accepted verdict was produced.
- The correction remains disabled without the explicit Canon authority below.
  Positive `authorize` and complete post-adoption formal derivation have not run,
  because the necessary real non-author review and its delivery do not exist yet.

The old/new header hashes and the only allowed JSON delta are fixed in the new
module. Only the old W09 profile source pin may use an independently reviewed
interpreter transition. Product sources and environments receive no exemption.
Saved original event bytes stay exact, while the dependency snapshot records
actual current header/range hashes so `recheck_inputs` rejects later changes.

## Non-author review contract

The reviewer must independently inspect the candidate diff and actual evidence,
test the controls, and produce its own source-review JSON in its W09 receipt
scope. No author or Root can issue that decision. Required JSON fields are:

```text
schema: researchos.w09.correction-independent-review.v1
scope: INTERPRETER_RECOVERY_ONLY
decision: ACCEPTED_RECOVERY_SOURCE_ONLY (only if actually accepted)
reviewer_id: actual current non-author peer ID
author_id: /root/resume_audit
issued_at: actual timezone-aware review time
certificate_ref: exact path/sha256/bytes of header-correction.candidate-v3.json
checks: certificate_pins, header_delta, business_ranges, project_bindings,
        interpreter_diff, negative_controls (each actual PASS required)
evidence_refs: nonempty array of actual review evidence path/sha256/bytes
```

The reviewer must actually deliver to current Root chat a message containing
the exact certificate SHA, its source-review JSON SHA and the literal decision
`ACCEPTED_RECOVERY_SOURCE_ONLY`. A rejection must be reported as rejection and
must not create the authority. This is source-only review, never a new issuance
of the old eight formal verdicts.

Current Root identity was independently supplied as
`01a12eb9-8243-7761-8f58-1e99a57f595e`, with original source audit path
`C:/Users/yqyyds/.codex/sessions/2026/10/12/rollout-2026-10-12T14-07-51-01a12eb9-8243-7761-8f58-1e99a57f595e.jsonl`.
The fixed expected current header SHA is in the certificate. Current Root must
capture its actual original session header plus the adjacent collaboration
metadata/message pair, preserving raw bytes and exact offsets, after delivery.
The capture descriptor fields are:

```text
schema: researchos.w09.correction-review-delivery.v1
source_audit_path: the exact current Root log above
thread_id: the exact current Root ID above
original_capture_ref: path/sha256/bytes of the three actual original JSONL lines
source_line_offsets: [0, actual metadata offset, actual message offset]
original_line_sha256: corresponding three actual SHA-256 values
```

This is an observation of an event that happened, not a template for generating
a peer message. All source-review/capture refs must lie inside the W09-99 receipt
prefix. The reader checks real current log bytes, author/recipient, adjacent
ordinals, delivery time, `client_authored=false` and both exact artifact hashes.
The historical thread identity and source path stay unchanged.

## Root adoption after actual non-author review

Root may adopt only the exact source bytes reviewed above and serially register
the following new `checkpoint.work_in_progress` property, with current revision
checks and a current metadata-only scope. Existing Native scopes are consumed or
expired and cannot authorize this work or any new product calls.

```text
w09_header_metadata_correction:
  schema: researchos.w09.header-correction-authority.v1
  certificate_ref: exact v3 certificate path/sha256/bytes
  verifier_module_ref: exact new fixed module path/sha256/bytes from certificate
  review_ref: actual non-author source-review path/sha256/bytes
  delivery_ref: actual current-chat capture descriptor path/sha256/bytes
```

Do not modify the original W09 Context, eight verdicts, issuance, dates, actors,
messages or evidence refs. Do not add a second accepted-review root to step_state.
Run the existing read-only formal index afterwards and preserve its real result,
then `recheck_inputs` its dependency snapshot. Any newly exposed downstream gate
remains a failure; these candidate tests do not pre-approve its outcome.

## Reproduce candidate checks

From `D:/作品集/ResearchOS/research-os`:

```powershell
python -B -X utf8 .local/candidates/w09-header-recovery-20261012-v3/tests/test_header_correction.py
```

No temporary test files remain. Durable candidate source copies are under
`candidate-v3-source/`; production loaders never execute code from that receipt
directory. Main profile/index hashes remained unchanged during candidate work,
and the new module has not been installed into Main.

## v3 fixes after independent rejection of v2

The v2 source remains frozen and must not be adopted. Its loader allowed a
Canon authority to repin arbitrary code at the fixed helper path. The v3 profile
now owns the exact helper SHA-256 and byte count. It rejects a different authority
pin before reading the module, then checks the actual raw code hash and length
before compilation or execution. The unchanged helper contains the full review
and actual-delivery checks; Canon may register evidence but cannot choose code.

All original 22 test methods remain AST-identical. Four new loader tests cover
malicious helper and authority repinning, an incorrect declared byte count,
substituted bytes after the Reader pin check, and the profile/helper digest match.
The isolated malicious-helper regression reproduces acceptance on frozen v2 and
rejection by v3. These fixtures create no peer messages or product evidence.

Main index/profile remain original; the helper is not installed, authority absent.
This v3 handoff, source snapshots, certificate and manifest are now frozen for
the same independent reviewer. The candidate author stops all writes at handoff.
