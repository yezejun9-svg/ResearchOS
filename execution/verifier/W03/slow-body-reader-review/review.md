# Independent review: W03 reader connection setup

Verdict: **PASS for the test-only change in `d591b9b4322f5e8534b90353ecc76d47539ccebb`**. No actionable finding. This is not a diagnosis or resolution of the earlier intermittent `/healthz` timeout, which remains **INCONCLUSIVE**.

## Source review

The commit changes only `internal/domain/domain_test.go` in the product source tree; its other files are diagnostic/author evidence and the verifier evidence module boundary. The test establishes both the slow-request TCP connection and the independent reader TCP connection before sending the partial POST. Connection setup retains the existing bounded fixture helper; no submitted business request is replayed.

Each real GET sets a fresh 1-second deadline immediately before writing the request. `req.Write`, `http.ReadResponse`, and complete body consumption via `io.Copy` all have checked errors. Both `/state` and `/healthz` must return 200. A single persistent `bufio.Reader` preserves any buffered bytes across the HTTP/1.1 requests. There is no `http.Transport` redial or request retry in the measured portion.

The test still sends a real POST with `Content-Length: 1000` and only one body byte, waits for the handler's body-read barrier, and requires the eventual response to be 400. Production `BodyReadTimeout` remains 5 seconds; the slow client's outer safety deadline remains 8 seconds. Neither production request processing nor SQLite readiness logic changed.

## Independent executions

Exactly two executions were performed against a fixed Git-blob snapshot of the reviewed revision, using the repository's hash-verified Go 1.27.1. No full suite or repeated-until-green run was performed.

| Run | Actual outcome | Interpretation |
| --- | --- | --- |
| Normal targeted test | Go exit 0; test PASS in 5.61 seconds | Both independent GETs completed inside their 1-second bounds, and the stalled POST eventually returned 400 |
| Fault-injected targeted test | Go exit 1; test FAIL in 1.10 seconds | **EXPECTED_NEGATIVE**: the test still detects single-connection DB starvation |

The negative run uses Go `-overlay` for `internal/domain/http.go` only. Before reading the body, and only for a request with `X-Fixture-Slow: true`, it acquires a transaction from the service's DB and defers rollback. Because the existing body-read barrier fires after this acquisition, the competing request starts only after the fault owns the sole DB connection. The untouched source snapshot retains its original bytes.

At `2026-09-30T16:29:55.3292607Z`, the injected trace reports `MaxOpenConnections=1`, `OpenConnections=1`, `InUse=1`, and `Idle=0`. At `16:29:56.3296782Z`, the test reports `stalled body blocked independent read .../state ... i/o timeout`, approximately 1.0004 seconds later. This is the intended assertion failure, not a compilation failure or fixture-connect failure. `/healthz` was not reached in the negative run because `/state` failed first; no separate negative coverage is claimed for it.

## Provenance and limits

`source-manifest.json` records SHA-256 values for 271 files extracted directly from the reviewed Git revision, including Go sources, dependencies, contracts, and migrations. The separate snapshot prevents concurrent integration from changing compilation inputs. `integrity.json` verifies the snapshot still matches those frozen bytes after both runs. Per-run receipts contain commands, working directory, timing, and exit code; stdout and stderr remain separate and unedited. `index.json` hashes all review evidence, including the snapshot and fault overlay.

This review confirms that moving connection setup outside the measured window preserves the intended database-contention detection. It does not claim that the historical `/healthz` timeout was caused by connection setup, establish general runtime stability, or approve unrelated W03/W05/S1 requirements.
