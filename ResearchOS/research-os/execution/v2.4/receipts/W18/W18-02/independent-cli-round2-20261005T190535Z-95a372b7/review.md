# W18 CLI continuation independent review round 2

Verdict: PASS_IN_SCOPE. W1802-CLI-R1-001 (P2) is CLOSED_VERIFIED. No new finding. This verdict covers only the Run-state classification repair and proportionate CLI regressions, not W18-02/A12/U06 acceptance.

Candidate/fix commit: 878c5b89646ed96eb8772b8eb8a910b60b9d3695. Main at freeze: d92cd639d0124bed760ea1660d9444b89dfe4a6c. All three scoped CLI files match the fix commit and main byte-for-byte. Before/after hashes show no drift in either source location. Original round 1 report and every hashed raw file, including the FAIL, are unchanged.

## Independent closure proof

The original round 1 independent_terminal_run_test.go overlay was copied byte-for-byte; both copies have SHA-256 5e3ef58d67cf1b87f1bcf8468306310c392ac1e7533a1d71b9438f94906b86f9. It was rerun against the repaired production source without test edits. TestIndependentContinuationTerminalRunDoesNotHideActiveRun now passes (exit 0). Its assertions verify that a prior terminal Run no longer obscures the unique actual active Task and that the projection does not mutate business state.

The repair classifies the actual fetched Run.status against the frozen Run enum: QUEUED, STARTING, RUNNING, CANCEL_REQUESTED, LOST and RECONCILING remain ACTIVE_RUN candidates; SETTLED, FAILED and CANCELLED fall through to ContextBundle/sole-unfinished-task logic; unrecognized states fail as CONTINUATION_INVALID_RUN_STATUS. Terminal unaccepted Tasks remain visible. Identity and scope checks still precede classification. This addresses the original faulty else-if and does not change operations, GET authorization, page/byte/deadline limits, output shape or no-Goal compatibility.

## Regression results

The 9 continuation top-level tests and 6 previous CLI/session tests pass (15 top-level total), with 9 passing subtests and no skips. The tests cover all three terminal Run states using real API-created/claimed Task/Run rows whose recovered status is injected into SQLite before projection; each retains its unfinished Task, allows ContextBundle and only-task fallback, and stops obscuring a single active Run. All six nonterminal enum states preserve active selection. Two genuine active Run candidates remain AMBIGUOUS. Unknown persisted Run enum is rejected by real API response validation (HTTP 500); an injected malformed successful HTTP response is independently rejected by the client classifier. Both paths are UNAVAILABLE/nonzero. Business-state digests and effect/dispatch/outbox counts remain unchanged during the read projection. Existing status operation, no-Goal, authorization, pagination and transport limits continue to pass.

Actual argv, cwd, environment, durations, parsed test names, exit codes, raw stdout JSONL and stderr are retained in original-counterexample.* and baseline-regression.*. The pinned go1.27.1 windows/amd64 binary hash is d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490; every run uses count=1.

## Limits

The work is limited to apps/cli/cli_verbs.go, cli_continuation.go and cli_continuation_test.go. Backend backup tests were not rerun. No W13 workspace permission/read/write/diff audit, GUI, credential migration interaction, live provider, live user data or whole-case acceptance was performed. Status restoration transitions are constructed persisted-state fixtures, not evidence of live runtime lifecycle execution. The independent test and production test suite use actual API/SQLite and the existing CLI function/process fixtures, not packaged-release qualification. Root remains responsible for later GUI and full-card evidence. No production/test source, Git index, state/checkpoint, old receipts or other source was changed.
