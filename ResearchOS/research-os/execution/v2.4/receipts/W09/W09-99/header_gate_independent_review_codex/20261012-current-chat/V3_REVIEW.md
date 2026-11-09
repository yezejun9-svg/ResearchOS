# W09 v3 independent source review

Actual non-author reviewer: `/root/w09_header_gate_review`.
Decision: **ACCEPTED_RECOVERY_SOURCE_ONLY**.
Scope: **INTERPRETER_RECOVERY_ONLY / SOURCE_COMPATIBILITY_ONLY**.

The v2 executable-trust blocker is closed. Relative to frozen v2, v3 adds a
profile-owned exact helper SHA-256 and byte count, rejects a mismatched authority
reference before reading code, and hashes the exact raw code before compile/exec.
The same malicious-helper repinning exploit succeeds on frozen v2 and is rejected
by v3 with `CORRECTION_MODULE_PIN`. The exact trusted helper itself is byte-identical
to v2. Its actual non-author review and current original delivery checks therefore
cannot be replaced by choosing another helper through Canon authority.

Independent rerun: 26/26 methods PASS, original 22 methods AST-identical. Test
temporary locations alone were redirected into this review directory; disposable
files were removed by the test cleanup. Actual historical 18 audit ranges were
read and dependency-rechecked. Extra reviewer controls show business source drift
still rejected, an actual current-chat rejection cannot become v3 approval by
changing a review claim, actual delivery cannot impersonate another reviewer, and
old-thread delivery claims fail. The actual negative message used was
`amsg_01a12ecd-a647-7620-9d84-cfa29b43dec0`; it was read into memory only and was not
rewritten or represented as an acceptance capture.

Manifest, certificate, candidate source and frozen copies all matched their exact
pins. Certificate semantic changes from v2 are only creation time and new profile
hash. Historical Context, review, issuance, five-role registry and business
assertions stay unchanged. Main profile and index still matched original pins;
the helper was not installed and recovery authority was absent during these tests.

The compatibility exception accepts exactly the historical offset-zero old/new
22,732-byte header pair and exact `model_provider: openai -> custom` delta.
Second-field mutation, alternate bytes, nonzero offsets, business messages,
certificate drift, wrong project, missing role/delivery bindings, altered index,
author self-approval and missing review controls remain rejected. Only the exact
old profile ref may transition; no arbitrary product/source hash exemption was
added. Full `_vector`, role, dependency, closure, producer, dispatch, GLOBAL,
independent historical review and original delivery gates remain on the existing
`verify_owner` path after correction authorization.

This decision approves these exact source bytes for the bounded interpreter
compatibility change. It does not reissue historical verdicts, accept W09/A06/C19,
authorize Native/consumer work, or assert any change from 0/42. The positive
`authorize` path requires Root to capture this actual decision after its real
delivery and register exact refs under current authority. It was intentionally
not fabricated during this source review. After adoption, Root must preserve the
actual full formal derivation and `recheck_inputs` result, including any remaining
failures. The v2 REQUEST_CHANGES record remains valid and unchanged.
