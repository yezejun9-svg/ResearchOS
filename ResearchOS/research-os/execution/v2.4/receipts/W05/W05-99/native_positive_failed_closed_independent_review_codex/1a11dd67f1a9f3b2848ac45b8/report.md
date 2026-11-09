# Security Audit Report

## Summary

FAILED_EXECUTION_CLOSED is independently verified. The SQL inspection and explicit Root cleanup are accepted only as component evidence. The positive native case remains FAILED; Owner authority, original business and formal completion remain unaccepted. No new security finding or mechanical error.

## Failure and process closure

Actual Go stdout reports native_migration_authority_harness_windows_test.go:468: INVALID_REQUEST: credential TTL must be at most 15 minutes. Go PID 53352 / creation time 134359747687806045 exited 1. Controller Python PID 57288 exited 1, matching Root outer and marked Python exit 1. Both owned Jobs reached idle=0 and closed all handles, with no timeout, termination request or cleanup error. Assigned/resumed/live/closed observations bind to Job 1583058f817849358683646372bc85bd.

The failure occurred before backup rehearsal or release/grant payload generation. No issuer signature, grant publication or native migration apply occurred. Diagnostic 820 is qualified with actual Go exit 1. Diagnostic 821 preserves the earlier v3 sharing failure and successful v4 inspection does not erase it.

## Actual SQL inspection

The reviewed v4 reader completed with actual outer/marked Python exit 0 (87088c). It recorded schema ledger 1–23, 296 schema objects, 87 tables and 280 storage-typed row digests. The aggregate typed_rows JCS digest was independently recomputed and matches 1e6c861219bbca48026ad7493897924fd61a0b92383c62363a075ddbf6524427. Baseline and expected target schema remain absent; expected_state_matches=false is preserved. No private raw rows or credentials are recorded.

Both native IDs match the retained snapshot. Same-connection data_version stayed 2; initially enumerated primary and WAL byte pins were unchanged. The 156 source-reader entries include _sqlite3.pyd, sqlite3.dll and sqlite3 Python/pyc files. The two live DB/WAL entries closed with truthful READ_WRITE sharing and no immutable database claim.

## Root release and guards

The concrete cleanup decision binds the exact inspection and snapshot. Its separate exact approval is consumed by the release receipt and matches the published release-fixture approval. Actual release exit 0 is preserved (521466). Eleven distinct guard observations close with no retained handles: six 4085-entry API/server guards, controller 4084, SQL reader 156, live DB/WAL 2, snapshot 2 and release 5. Normal test cleanup deleted the temporary DB and WAL after release.

4145 current references match; the two deleted fixture references are preserved as historical observations, without demanding current-file hashes. CP357/OW168/SS/CM remain exact.

## Evidence limits and recommendation

This reviewer read artifacts and Source only, with no Go/SQL/native rerun. SQL traversal is established by the reviewed reader path, actual successful invocation and guard/inspection artifacts. Raw schema rows were not saved, so the recorded schema digest was not regenerated from the deleted database. Existing-WAL checks do not prove a frozen entire sidecar set.

Keep the failure and cleanup evidence immutable. Repair fixture TTL in a new Source revision, independently review the exact change and its matching compiled artifact before considering a separately authorized new case. Do not relabel this attempt as passed or reset its diagnostics.

