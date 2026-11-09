# W14 writer takeover diagnosis and construction brief

This packet is read-only diagnosis and a proposed future scope. It does not change ResearchOS, qualify native identity, or mark W14 accepted. CP586/Main556cdc353f47167e5609f23291bf2746e3c8896f is the checkpoint baseline; this archival run does not repeat the disconnected Git check.

## Verified failure and distinction

The unchanged W14 CLI/API fixture and the preserved fc2b1a50662580b1a0fca92559ca26be6e959f01 build overlay both failed at apps/cli/cli_sessions_test.go:237 with HOST_REJECTED:WRITER_BUSY. Original evidence is copied byte-for-byte under prior-evidence/ and hashed in prior-test-evidence.json. No unchanged test was rerun for this packet.

The immediate cause is internal/domain/client_protocol.go:1197-1198: a still-valid lease owned by a different client_id is rejected before settlement is examined. W14 created the session immediately, reused its authenticated Owner token, and changed only the client id (test:234-237). This is not a regression caused by the later prompt bridge.

The frozen specification requires more than this conservative refusal: 22_CLIENT_INTERFACE_DETAILS.md:130 defines attach(true) with observed expected_revision and null writer_epoch; :132 requires current, proven same authenticated local OS subject; :136 requires one durable handoff intent; :137 explicitly says another same-subject client with a valid lease is accepted as ACKNOWLEDGED while the target remains read-only; :138 requires pausing new dispatch and preserving work/checkpoints/queued follow-ups; :139 requires rechecking authority and input state before atomic owner/epoch/revision transfer and CLIENT_HANDOFF; :140-141 preserve CAS conflict and CANCEL priority; :143 defines renewal and host time; :145 says lease expiry proves no process settlement. Related UI behavior is fixed at 19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md:194; current-writer handoff ordering is also in 14_CLI_DESKTOP_PRODUCT.md:71. Exact bytes, hashes and numbered excerpts are in source-evidence.json.

## Preconditions missing from the old fixture

1. cliSessionBindingFixture.AdmitTurn (cli_sessions_test.go:38-40) always returns RESOURCE_UNAVAILABLE: there is no LIVE runtime or Coordinator. The message is saved as BLOCKED plus ERROR, with no Run, not as proof that every process/effect/control is settled. The test's comment at :232 conflates blocked and settled.
2. The fixture has a synthetic domain Owner token and supplied client ids, not fresh native evidence that both current and target client belong to the same authenticated OS principal on the current host. It is not a native identity qualification.
3. It never establishes a durable takeover intent, dispatch hold, completed checkpoint/queue reconciliation, or a completed transfer receipt before assuming control can move.
4. It does not distinguish ACK admission from final ownership. An ACK cannot be treated as a new epoch or authority to write. The test must wait for canonical completion and observe the returned snapshot.

There is also a second implementation barrier: attachSettlement (client_protocol.go:1374, :1408-1410) reuses clientTurnSettled (client_protocol_sessions.go:416, :428-430). A task with no active_run_id must be ACCEPTED/CANCELLED/FAILED; a never-dispatched BLOCKED task does not pass. Expiring the fixture's lease or deleting the first guard alone therefore cannot supply the missing proof. Do not relax this shared predicate: it also prevents new messages from overwriting unfinished tasks and guards configuration changes.

## Missing completion and Coordinator boundary

Execute at client_protocol.go:732 returns original ACKs unchanged for every method except session.control. Only session.control ACK reaches finalizeClientCancel (:749-750). Returning ACK from attach without an attach-specific replay/finalization path would produce a permanent ACK. Keep the original ACK and the later final receipt independently auditable under the same exact command/hash; do not mutate old immutable receipts into invented completions.

ClientSessionRuntime currently has only ValidateBinding and AdmitTurn (client_protocol_sessions.go:17-20); its contract explicitly forbids worker launches or second transactions inside the command transaction. RuntimeCoordinator handling at runtime_coordinator_windows.go:693-720 finalizes and consumes an already-PAUSED journal, but does not establish that attach requested a safe pause. The existing CANCEL controls/fenceClientTask clear/fence work and are not a handoff implementation. ClientService currently has no attach-specific durable intent consumer or fresh same-OS client proof port.

## Proposed bounded construction scope

The first slice may handle only an authenticated same-OS takeover whose complete session relation is proven to have no dispatch, Run, effect, pending tool/queue/control, permission or recovery fence. A BLOCKED Task can remain BLOCKED, preserving Goal/Task/checkpoint identity; ownership transfer must not label it accepted or resume it. Active or unknown work remains visibly pending/blocked until a separate Coordinator pause path is implemented and validated.

Production changes proposed for a separately owned worktree:

- internal/domain/client_protocol.go: route attach through the durable state machine and permit only its exact pending command to make progress on replay; retain current ownership, revision, epoch, role, archival and schema gates.
- New internal/domain/client_protocol_attach.go: attach-only work-settlement proof, original-identity binding, intent creation/progress, current state revalidation, atomic final grant and one CLIENT_HANDOFF event. Keep clientTurnSettled unchanged.
- A new migration filename allocated serially by the root/migration owner: persistent unique active intent per session, requester/current owner/epoch/revision/hash, original ACK and final receipt. Do not edit frozen contracts or historical migration evidence. Do not reuse cancellation rows without a typed distinction.
- Host/API composition files only in an explicitly expanded scope: expose trusted current local OS subject/client facts from the existing Host boundary. A caller-supplied client_id, claimed Owner role, stale credential or old epoch is not evidence. Do not create a public OWNER registration or a bypass.
- internal/domain/runtime_coordinator_windows.go and runtime_command_queue_windows.go only when implementing the active-work branch: persist the intent first, hold new dispatch after commit, request a real safe pause through the selected runtime, wait outside the SQL transaction, reconcile exact process/effect/queue/checkpoint state, then recheck before grant. Preserve unconsumed follow-ups. Do not issue business CANCEL or delete a queue to manufacture settlement. If no compatible pause capability exists, retain an explicit implementation gap.
- apps/cli/cli_sessions_test.go plus attach-specific domain/API tests: supply explicit synthetic authority and settlement facts for fixture tests, distinguish ACK from final completion, and keep the native qualification gap separately visible. The current test must not simply change its expected error to pass.

## Meaningful regression coverage

- Same current client renews without an epoch change; read-only attach neither acquires nor renews.
- Fresh proven same-OS target with a valid old lease gets ACK and stays read-only; exact replay neither repeats pause nor creates another intent.
- Missing, foreign, stale, remote-device or fabricated authority fails without mutating owner/epoch/journal.
- A quiescent never-dispatched BLOCKED task can move ownership only after complete session-history proof; task, Goal, work, checkpoint and accepted/pending queue state remain unchanged; no auto-resume.
- Current and historical Runs, hidden older effects, queued commands, pending permissions, unknown process/effect state and restore fences prevent completion, even after lease expiry.
- Concurrent intents, changed revision/owner/epoch/input/permission and same-command changed payload preserve one winner or refuse; no automatic revision replacement.
- CANCEL wins during pending transfer; later completion cannot revive cancelled work, clear resume_requires_explicit_user or discard follow-ups.
- Faults and restart between intent/ACK/reconciliation/CAS/journal do not produce dual owners; final replay is stable and old writer writes remain rejected.

No part of this diagnosis permits changing the writer/CAS/native gates merely to make a fixture green. No pure-scalar result is authority to bypass the ordinary LIVE Goal gate.
