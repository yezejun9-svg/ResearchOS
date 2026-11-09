# Mu SDK v8 source preparation

The candidate binds the future trial to Root's five-Go commit `adc460c2138528f163f7fdab5e8d81dde157b7fb`. The earlier `e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7` does not contain those five Go changes. Root's owned Git receipt lists only those five files and 17 successful operations.

The actual typed-cancel test passed against the same five Go file bytes before the Git commit. Its v4 receipt reports `actual_external_provider_requests=0` and `local_fixture_requests=1`; the test stdout says `provider_calls=1` because the local HTTP fixture received one call. The runner now reads those actual fields, pins the original build and test invocations, verifies the frozen bundle and metadata against the current Main Mu worker source, and pins Root's original I/O. It does not claim that the test ran after the commit.

The v8 input template has the new commit and the actual v4 cancel receipt pin. Runtime authority, registration, lease, CLI binary, and bootstrap evidence remain unissued placeholders. The trial has not been run. Limits remain three requests, 8192 requested output tokens total, 2730 per request, and 300 seconds; no automatic retry is added.
