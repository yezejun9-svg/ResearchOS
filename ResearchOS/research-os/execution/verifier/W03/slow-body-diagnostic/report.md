# W03 slow-body independent diagnosis

Verdict: **INCONCLUSIVE for the original `/healthz` timeout**. One targeted instrumented run passed. It narrows the problem but does not establish the cause of the historical failure or clear the failing qualification receipt.

## Scope and provenance

- Read-only target: `.local/worktrees/runtime-qualification`, HEAD `bfce0db553a2947916ed955b2d1079a21ac8eb6e` (contains requested source revision `78564ba`). Target Git status was clean before and after the probe. Source file SHA-256 values are recorded in `baseline.json` and rechecked in `integrity.json`.
- Only verifier-owned files under this diagnostic directory were written. The target source and author receipts were not changed. Go `-overlay` substituted instrumented copies of three files solely for this invocation.
- Exactly one diagnostic invocation: `go test -overlay <this-directory>/overlay.json ./internal/domain -run ^TestW03SlowBodyDoesNotBlockDatabase$ -count=1 -timeout=30s -json`, using the repository's pinned Go 1.27.1 with `GOENV=off` and `GOTOOLCHAIN=local`. Exit 0; test 5.62 seconds, package 5.851 seconds. The existing 1-second independent-GET limit and 5-second body-read limit were retained; no business request was replayed.
- Original failure log SHA-256: `caeda71979fd3ababbf7db1308f5abcc64420e218083a9a364311ec11ec0b4d7`. A byte-identical copy is retained as `original-healthz-isolated.jsonl`.

## Original failure: what is known

The original test started at `2026-10-01T00:17:37.186127+08:00`. Its pre-business loopback connection attempts failed at `00:17:38.3055571` and `00:17:39.3116523`, each with Windows `connectex` failure. The subsequent connection and slow-body-start barrier succeeded. The `/state` GET completed with status 200, as execution advanced to the next loop iteration. At `00:17:40.6255196`, `/healthz` failed with `Client.Timeout exceeded while awaiting headers`; the test ended after 3.45 seconds.

The original log has no HTTP transport events, server-arrival timestamp, Ready entry/exit timestamps, or database pool statistics for this request. Consequently, that message cannot distinguish waiting for a connection, waiting for server dispatch, waiting in Ready, or waiting for response bytes. The two earlier failed connection attempts establish a real loopback setup symptom, but do not prove the cause of the later `/healthz` timeout.

## Observed instrumented timeline (UTC)

| Event | Timestamp | Evidence |
| --- | --- | --- |
| Slow POST accepted | 16:24:08.3712596 | Remote port 5050; DB idle |
| Slow body read blocked | 16:24:08.371915 | Read deadline 16:24:13.371915; no transaction-entry event for this request |
| Independent state TCP connected | 16:24:08.3724316 | Remote port 5051; fresh connection |
| State handler returned | 16:24:08.3729462 | DB InUse=0, Idle=1, WaitCount=0, WaitDuration=0 |
| Health client obtained connection | 16:24:08.3729462 | Reused=true, WasIdle=true, same port 5051 |
| Health request arrived / Ready entered | 16:24:08.3729462 | Same timestamp as request write; no pool wait |
| Ready and health handler returned / first byte | 16:24:08.373748 | All four PRAGMA checks and quick_check passed; approximately 0.8018 ms |
| Slow POST read deadline expired | 16:24:13.3723951 | Response 400; DB still idle with no pool wait |

The source reads the request body before opening a transaction (`internal/domain/http.go:80`, transaction at line 102). The pool has a single connection (`internal/store/sqlite.go:35`). In this run the stalled POST never reached the transaction-entry trace, and the state handler had released its transaction before health arrived. Thus this run contains no evidence of DB pool starvation or a PRAGMA/quick_check stall.

The trace's `1970-01-01T00:00:01Z` read deadlines and immediate socket `i/o timeout` after successful GET handlers are Go's `net/http.connReader.abortPendingRead` behavior, not failed business requests. The pinned `net/http/server.go:785` sets an expired deadline to stop its background reader, then clears it at line 796. The recorded state connection likewise clears its read deadline before processing health. The 5-second application deadline did not expire during either independent GET. Nothing in the historical 3.45-second timeline supports treating that 5-second deadline expiration as the demonstrated root cause.

## Smallest justified next change

Do not change production `Ready`, increase the 1-second assertion limit, or repeat the test until green on this evidence. Keep the original failure attached to qualification.

The smallest useful test-only change is to separate fixture readiness from the measured slow-body window: establish the independent GET connection(s) before submitting the partial POST, then start the 1-second bound only after the existing body-read barrier. Give each measured path a known connection so transport setup cannot consume its database-concurrency assertion window. Preserve real HTTP and the expectation that the body timeout eventually returns 400. This is a fixture-hardening proposal, not a proven cure for the original `/healthz` symptom.

Retain compact in-memory transport/server/Ready/DBStats events, emitted on failure, to classify the next failure by phase without verbose synchronous tracing. If the server entered Ready and DBStats shows InUse=1 plus rising WaitCount, investigate ownership of the single DB connection; if Ready completed but response headers did not arrive, investigate transport/dispatch. A production fix requires such failure-phase evidence.

## Limits

The one instrumented run did not reproduce the failure. Synchronous tracing can perturb scheduling. There is no justified probability estimate or stability claim from this sample. This document is diagnostic evidence only; it is not a replacement PASS receipt and does not approve W03/W05 or a broader stage.
