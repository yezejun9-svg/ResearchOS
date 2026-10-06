# I2 source freeze b1877d4

Source commit: `b1877d4a32f15868d19ed9d32f39fc2b6b563db9` on `work/research-cycle-driver`.
Parent source checkpoint: `47cd747` (includes earlier source/stage work and its original raw evidence).
This note and new raw logs are committed separately from source. No public contract, previous SQL migration, live DB, service process or external provider changed.

## Verification scope

| Raw file | Result and source relationship |
| --- | --- |
| bound-close-first.jsonl | Preserved failed test setup: direct READY to FAILED mutation was rejected by existing lifecycle guard. |
| bound-close-second.jsonl | PASS after using real claim/heartbeat/failed observation/report. MaxTasks=1 reserves a report; public READY/FAILED/EXECUTION_REPORTED without independent receipt cannot close. Accepted public close counts one original report Run. This predates permanent zero-work cycle binding. |
| cycle-binding-first.jsonl | New zero-work test initially used invalid MANUAL trigger and failed 400. Other two selected cycle/bound-close regressions passed. |
| cycle-binding-native-pair.jsonl | PASS after correcting to contract USER trigger. Zero-work binding survives retirement; SQL replace/update/delete rejected. Existing W10 native AppContainer paired experiment also passed. This predates final lifecycle changes. |
| offline-native-experiment-first.jsonl | Preserved failed fixture call: public BeginExperiment requires QUEUED, but this host-stage test had already heartbeated. |
| offline-native-experiment-second.jsonl | PASS using the same beginExperimentTx as the host experiment broker. Approved monitor template creates registered per-cycle experiment and Task; real local AppContainer baseline and candidate executions produce the existing eight-output seal pipeline; original effect receipt reconciles and replays; independent acceptance receives all artifact refs; driver records IMPROVED, reports and closes; progress audit records new gain. Re-created same-content Artifact IDs retain the same progress key. No network listener involved. |
| lifecycle-first.jsonl | Cross-cycle no-progress PASS: distinct accepted report Runs increment one stable record and defer at its finite limit. Lifecycle raw retains failures for stale-profile cancellation and invalid effect key. |
| lifecycle-second.jsonl | Pause/resume/cancel PASS. Profile drift still failed on store.ref rejecting historical profile reference; UNKNOWN fixture failed because STARTED was missing. No claim that either failed subcase passed. |
| lifecycle-migration-third.jsonl | PASS for all lifecycle subcases, legal STARTED to UNKNOWN, schema migration count and New() reopen. Source includes the approved narrow store.ref cancellation exception. Initial historical-ref negative case used an invalid revision, subsequently strengthened. |
| drift-historical-ref-final.jsonl | PASS at the exact frozen source content: old profile_ref is retained for cancellation; stale RUNNING and changing to a different real historical profile ref are rejected. Only the affected profile-drift subcase was rerun after strengthening the test. |

The whole suite was not rerun at b1877d4. Prior passing checks were not repeated without relevant changes. The latest full SOURCE native network binding test remains unverified: `native-source-binding.jsonl` exhausted three loopback readiness listeners before business I/O. It is retained as FAIL; earlier successful source checks and current offline source/candidate checks do not replace this missing network evidence. No retry of that exhausted input was attempted.

The offline experiment test exercises real AppContainer execution and durable stage/effect/acceptance mechanisms, while its outer orchestration is in-process fixture control. It does not establish outer native child broker transport, live provider qualification, or live research accuracy. LIVE experiment capability remains unavailable. Report outcomes preserve source gaps and unknown costs.

## Source changes for independent review

- Immutable `research_monitor_cycles` relation created in migration 0020; cycle creation binds in the same transaction, before Tasks exist. Adoption checks exact approved profile and bounded manual window. Public close requires current independent delivery receipt for all bound cycles.
- Finite stage capacity reserves delivery. Omitted required experiments remain explicit gaps.
- Native experiment work uses the existing experiment state machine, eight sealed outputs and independent verifier. No second execution queue.
- Cross-cycle progress is keyed by reviewed origin identity or role-separated sealed artifact content hashes. Run/cycle/object IDs, hypothesis prose and observed sample values cannot create a fresh improvement key. Correctly accepted reports remain ACCEPTED at no-progress deferral.
- Pause/resume affects only monitor-owned holds; cancellation commits stop requests while unsettled execution/effects retain ownership. Profile drift safely cancels and retires the original monitor after reconciliation, preserving prior/current profile references.
- The only store.go change permits exact historical `/profile_ref` for a noninitial CANCELLED ResearchCycle whose profile ref is unchanged from its preceding version; historical existence and hash checks still apply.

## Cleanup rejection: BLOCKED_HYGIENE

One temporary folder from the original failed bound-close fixture remains:

`C:/Users/yqyyds/AppData/Local/Temp/TestResearchTaskBoundAndPublicCloseGate1373465950`

Read-only `Test-Path -LiteralPath` returned `True` after the rejection. No alternate deletion mechanism or retry was attempted. Existing previously blocked I1/S2 cleanup paths were not touched.

The rejected exec command combined gofmt, one profile-drift test, git diff check and this exact cleanup tail:

```powershell
$tempPath='C:/Users/yqyyds/AppData/Local/Temp/TestResearchTaskBoundAndPublicCloseGate1373465950'; if(Test-Path -LiteralPath $tempPath){$resolved=(Resolve-Path -LiteralPath $tempPath).Path; if($resolved -eq 'C:\Users\yqyyds\AppData\Local\Temp\TestResearchTaskBoundAndPublicCloseGate1373465950'){Remove-Item -LiteralPath $resolved -Recurse -Force}}
```

Automatic tool rejection text ended with `rejected: blocked by policy` (`exec_command failed: CreateProcess`, `Rejected(...)`). The tool itself truncated the serialized command with `…376 chars truncated…`; this note does not invent omitted rejection content. The entire combined command did not execute. The independent nondeletion gofmt/test/diff/read-only-presence command then ran and produced `drift-historical-ref-final.jsonl` PASS. The rejected command has no test PASS/FAIL result.

Source is frozen for independent review; this is not a final completion, release or hygiene approval.
