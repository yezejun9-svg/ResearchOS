# Q4 typed attach diagnostic: production completion gap

Authority: NONE. Source construction blocked at the published attach-completion boundary; no candidate Source or production file changed. Root T6 actual failures remain failures. This report does not accept a formal case.

## Actual first cause

Root actual namespace: `integration_codex/typed-q3-epoch-targeted-root-0c4318e1c10443f2`. Its exact compiled source root is `.local/worktrees/codex-w0599-typed-q3-83b95f35e9bd4f81ad0c6682895a6ac1`, discovered from actual compilation invocation. The six independently saved child JSONL streams contain eight failing native leaves:

| Parent or leaf | First error line in child.stdout.jsonl |
| --- | --- |
| TestRuntimeMuSessionToolAndIndependentAcceptance | 5 |
| TestRuntimeMuToolRefusalAllowsNextTurn | 5 |
| TestRuntimeOriginalToolPermissionControlsOnePhysicalWrite/ALLOW_ONCE | 7 |
| TestRuntimeOriginalToolPermissionControlsOnePhysicalWrite/DENY | 13 |
| TestRuntimeOriginalToolPermissionExpiresWithoutPhysicalWrite | 5 |
| TestRuntimePermissionDecisionWaitsForAnotherRequiredResource | 5 |
| TestW05RuntimeEventBrokerBeforeIOAndRollback/rollback=false | 7 |
| TestW05RuntimeEventBrokerBeforeIOAndRollback/rollback=true | 13 |

Each first error is the actual typed session.attach response: ACKNOWLEDGED, revision 3, operation_id equal to op- plus its exact command_id. The existing muClientCall helper only accepts COMPLETED (T6 runtime_tool_integration_windows_test.go:31–43), so the child stops before its original business assertions. Each official reporter actual_runner_exit is 1; the strict JSONL verifier correctly rejects its fail terminal. Native child physical exit/PID fields remain null pending Root Go Job reconciliation, rather than being inferred from reporter exit.

`actual-inspection.json` preserves the six result/verdict/invocation/parent-result documents, matching run/fail/error events with original JSONL line references, and all corresponding raw input pins. Root-reported parent 61 PASS / 6 FAIL / 0 SKIP and separately observed eight native failing leaves are different levels, not additive counts. Prior failure 823 stays in the Root actual namespace; this author has not rerun any native input.

## Published completion and writer conditions

The package `22_CLIENT_INTERFACE_DETAILS.md:116` says ACKNOWLEDGED is durable receipt, permits replay/events/snapshot reconciliation, and forbids presenting it as completion. Lines 130–143 require:

- attach(true) uses the just-observed expected_revision and a null writer_epoch.
- Same-owner renewal only renews lease and does not change epoch (137, 143).
- Transfer waits for settled work, preserves existing Task/Goal/queue, then atomically changes owner and increments epoch/revision, emits CLIENT_HANDOFF, and returns COMPLETED/AttachResult (139).
- The target may write only after this completed transfer; attachment itself does not resume or cancel work.

The schema binds ACKNOWLEDGED to PendingResult (`client.protocol.schema.json:1683–1715`, `4774–4788`) and completed session.attach to AttachResult (`4928–4948`). The x-method-contracts at lines 17–70 expose no operation.status method. Neither operation_id nor a read-only completion is a substitute for the original write-owner operation's terminal state.

## Actual production chain

In pinned T6 `internal/domain/client_protocol.go:1127–1187`, attach(true) performs the existing writer gate, HandoffEpoch CAS, writer-client/lease update, and CLIENT_HANDOFF journal in the same transaction. It then returns ACKNOWLEDGED with PendingResult. Same-owner reacquisition explicitly follows the same epoch rotation (1135–1136), so this actual fresh session goes from revision 1/epoch 1 to revision 3/epoch 2.

`HandoffEpoch` in `v24_sessions.go:153–177` advances revision and writer_epoch; `journal` in `client_protocol.go:1239–1262` writes the new claim via `AppendSessionEvent`; `client_protocol_journal.go:46–138` validates event payload, writes outbox and guarded watermark, and increments the revision atomically. `sourceTx` commits the command transaction in the existing fixture.

The ACK cannot currently progress to a final attach response through the available replay path: `client_protocol.go:726–732` immediately returns the original response; only ACKNOWLEDGED session.control gets a special replay finalizer (`748–771`). No attach finalizer or operation-completion handler appears in the exact scoped client/runtime session source search. The only COMPLETED attach branch is the read path (`1036–1060`), whose AttachResult explicitly says write_owner_acquired=false. It cannot stand in for completed attach(true).

Public session.events can read the genuinely committed CLIENT_HANDOFF (`1061–1094`, `client_protocol_journal.go:144–201`); public session.get can return the real current snapshot (`1036–1049`, `BuildSessionSnapshot` in `client_protocol_journal.go:241–351`). Those observations prove durable state, but changing the old ACK into COMPLETED in a test helper or replacing the required original terminal with a read-only result would weaken the published completion condition. No such candidate Source was written.

## Minimal remaining correction boundary

The Q3 fixture has a genuine synchronous assumption defect. The production chain additionally lacks the published attach terminal and same-owner renewal behavior. A strictly conforming Q4 test-only awaiter cannot produce the missing terminal. Root explicitly directed this branch to seal BLOCKED_PRODUCTION_ATTACH_COMPLETION and stop; a separate production Source author must implement the real semantics for independent review before a fixture can await them.

After that product contract is resolved, the fixture should use the original decoded attach command and authenticated principal in the actual command transaction, keep its command_id and request hash for replay, bound its wait, and require the original COMPLETED/AttachResult. It must match session/project/model/workspace/native identity, owner client, returned revision, current writer epoch, unexpired lease, exact original command's CLIENT_HANDOFF where a transfer occurred, and existing run/Task settlement before sending. It may only obtain these from real public results/events and authoritative state, never handwritten journal/ledger/messages.

If completion retains a transfer, the three runtime caller files each need exactly two fixture-input changes: bind the returned writer tuple from attach, then use its revision/epoch for the first send. The existing hardcoded revision 1/epoch 1 at runtime_permission_windows_test.go:192, runtime_tool_integration_windows_test.go:152, and runtime_session_events_windows_test.go:498 cannot follow a real revision 3/epoch 2 transfer. This does not justify altering any business assertion or muClientCall's COMPLETED requirement. This author has changed no original file, call, Test name or assertion; accepted Q3 pins (181 calls, 20 Test names, 196 assertion-or-error if nodes: 190 strict t assertions plus 6 fmt.Errorf blocks) remain unchanged. The three actual T6 runtime files are byte-equal to Q3; actual T6 Goal source has only the separately recorded Root gofmt delta (three struct-field alignments and four return-line indents). Q3 strict JSONL/resource pin/TLS/configuration/Root Job behavior was not changed by this diagnostic.

The first waitable fixture remains synthetic/nonformal: it must still exercise the real fixed SDK, local TLS with strict x509 trust, exact same host.configure model_config_ref and credential revision, original provider/Host/qualification and business assertions inside the real child. No production-model call, private credential inspection, Go/gofmt/compiler/native/SQL execution, Main/canonical mutation, or formal acceptance occurred in this author branch.

Restoration condition: an independently reviewed production path produces the exact original attach terminal and valid writer/lease binding under the published contract, or Root explicitly narrows a synthetic observation contract without treating it as formal attach acceptance. Old Q3/T6 packages and actual failures must remain immutable; any later actual uses fresh integration and evidence inputs.

`source-pins.json` pins every cited actual source, immutable Q3 four original files/helper, exact T6 counterparts, contract documents, closed Root receipt, and matched selected compiler input references. `tool-io.json` contains the complete available author tool inputs/outputs. HDF/MF seal this diagnostic and explicitly declare no candidate Source.

The first seal attempt exited outer/Python 1 at seal.py:58 because this author incorrectly required all four formatted T6 files to be byte-equal to Q3. Only contract-excerpts.json had been written; candidate, production, HDF, MF and static-checks remained absent. Root assigned ordinal 826; failure-origin.826.json preserves exact 67d70a input/output. A distinct read-only inspection (b41eba/Python 0) established the Goal-only whitespace delta in actual-format-delta.json. The original failing seal.py and its IO remain unchanged; new seal_revision.py accounts for that diagnosed delta. Product-native/Go/SQL/model execution remains absent, and the failure count is 1 rather than reset.
