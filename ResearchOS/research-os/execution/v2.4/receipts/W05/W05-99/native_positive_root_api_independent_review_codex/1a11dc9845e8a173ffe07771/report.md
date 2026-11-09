# Security Audit Report

## Summary

Critical: 0; High: 0; Medium: 1; Low: 0. The public phase API's inspection hash contract needs correction. This does not revoke the accepted v2 server launch.

## [MEDIUM] Inspection uses Marshal escaping instead of production JCS

Location: root_public_api.actual.py:116–119,164–166. Production contracts.go Hash passes JSON through canonical.JSON; internal/canonical/jcs.go invokes jsontext.Value.Canonicalize. Its minimal string representation differs from the API's forced HTML/JS escaping. Actual migration SQL has epoch>0 and page_cursor_out<>''. A correct schema would therefore receive a different hash and expected_state_matches=false.

The independent illustrative string-only input ["CHECK(epoch>0)"] produces JCS digest b8832d1e7bd54d48b127c5d2a95674c30a1a074de155c23265980d3a4c0a470c, versus ffce7e50025f7e1d94840f8b8f70fb6cda552e593e4d26b211dd9d83f709f51b after the current forced escaping. This is an encoding illustration, not a target Go/SQL execution.

Fix: restrict serialization to the actual string/list/string-keyed-dict data domain, validate Unicode, sort object keys by UTF-16 code units and emit minimal strings without re-escaping HTML/JS characters. Do not claim a general numeric JCS serializer without implementing its number rules.

## Positive observations

The accepted same-buffer/held-source bootstrap is preserved. Actions are explicit, and sign/publish/release consume separate exact Root approvals. Fixed key metadata is held before its issuer-path value is used. Private key contents are not read by the wrapper; signer stdout/stderr are discarded; persisted controller/helper receipts omit full signer argv and private path. The path is necessarily present transiently in genuine signer CLI arguments, which is distinct from persistence.

Typed row encoding matches Go exactly for NULL, int64 decimal, float64 bits, TEXT and BLOB with 8-byte big-endian lengths. All schema objects and all typed rows are traversed through mode=ro/query_only. Reader modules/DLLs/DB are guarded and closed before receipt publication. Completion flags mean traversal, not expected-state success; release still needs separate Root approval.

## Scope

4091 current references match; CP357 remains exact. No target/Go/SQL/private-file/signature execution or canonical write occurred. No new mechanical errors. Concrete snapshots and approvals still require phase-specific review; no Owner/native/formal acceptance is conferred.

