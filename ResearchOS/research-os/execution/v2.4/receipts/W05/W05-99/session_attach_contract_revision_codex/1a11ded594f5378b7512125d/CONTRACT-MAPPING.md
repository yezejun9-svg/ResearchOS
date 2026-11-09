# session.attach contract repair: bounded Source component

Status: SOURCE_ONLY_PENDING_ROOT_INDEPENDENT_REVIEW_AND_FRESH_ISOLATED_BUILD.

## Exact scope and production basis

Overlay only candidate-root/internal/domain/client_protocol.go and the new
client_protocol_attach_contract_windows_test.go into Root's fresh composition.
The production base is T6's actual selected compiler input, SHA-256
8eab2b524cbf436a11c48ac40b738c7f682d6c4e59cf58df9f3655fd2ed85bcf,
50304 bytes. Main/T5/T6, TTL receipts, original tests, commands/state and all
prior packages remain unchanged. This is a production Source candidate, not
an executed native acceptance or a claim that every attach branch is complete.

## Contract to behavior

The canonical input is the top-level
ResearchOS_Implementation_Package_v2.4/22_CLIENT_INTERFACE_DETAILS.md
(the nested duplicate was enumerated but is not substituted).

| Contract | Candidate behavior and evidence |
|---|---|
| §4: COMPLETED means the method finished, with method-specific result | Valid-owner renewal or a synchronously completed settled transfer returns actual AttachResult(snapshot, write_owner_acquired=true). BuildSessionSnapshot runs inside the same transaction after its actual lease/owner writes. |
| §5.1: same current owner renews without epoch/revision increment | A strictly unexpired lease for that exact writer is updated under CAS matching project/session/revision/epoch/writer/old lease and unsealed/unarchived state. It emits no CLIENT_HANDOFF or other event. The snapshot carries the unchanged epoch/revision/event sequence and actual new expiry. |
| §4/§5.1: invalidated/expired writer requires a fresh generation | Expired, absent or malformed lease falls through to the actual settled reacquisition path; it never renews an old generation. |
| §5.1: transfer only after tools/queue settled | Any mapped Run requires runState's real children_stopped && queue_empty. A terminal status alone is insufficient. Unconfirmed settlement returns existing SESSION_BUSY without changing owner, lease or epoch. |
| §5.1: real transfer emits CLIENT_HANDOFF | Existing HandoffEpoch and journal bodies remain. Epoch advances once; existing HandoffEpoch plus event-journal semantics advance revision twice and watermark once. The response revision and snapshot reflect that actual state. |
| §4: same command replays its original response; conflict is not retried | Execute's identity reservation, canonical full-request hash, idempotency storage, schema validation, rejection savepoint and replay logic are byte-unchanged. New terminal attach results persist through this existing path; replay never renews or transfers again. |
| §5.1: session/project/revision/epoch gates | Entire dispatch remains byte-unchanged. Stale revision, claimed epoch on takeover, archived/sealed state, principal/creation attribution and other prior refusal paths remain. Transfer's original Host.LeaseTTL validation order is retained. |
| Existing runtime/profile/session contracts | Attach preserves native_session_ref/workspace_ref/model_config_ref. No runtime/profile/admission code changes. New tests check post-attach binding tamper refusal and reuse the existing actual stored-profile/runtime-route and exact Task/Session negative tests. Native integration remains Root's separate acceptance. |
| §5.1: cancellation cannot be undone by takeover | No CANCEL, RESUME, Run mutation, queue deletion, auto-dispatch or resume flag reset is added. |

## OPEN_BRANCH: active asynchronous takeover

The published complete active-takeover flow still calls for a unique pending
handoff intent, safe-point pause, real tool/child settlement, and later CAS.
ClientSessionRuntime currently exposes only ValidateBinding and AdmitTurn,
not such a pause/settlement completion port. This candidate retains SESSION_BUSY
for an unconfirmed Run. It does not pretend that a terminal Run label is evidence,
does not call CANCEL to manufacture settlement, and does not claim the full
active asynchronous attach contract is implemented. Root needs a separate
defined pending-intent/lifetime/completion design for that branch.

## OPEN_BRANCH: historical cached ACK reconciliation

Existing persisted attach ACK responses replay unchanged through Execute.
They are not rewritten to COMPLETED, re-executed, or reconciled from an arbitrary
current snapshot. Any historical-terminal reconciliation requires a separate
reviewed rule binding the original request/transfer event and actual state.
This candidate fixes new synchronously completed commands only.

## Test Source and preserved checks

Five new Windows test functions cover valid-owner renewal and exact replay;
unowned acquisition, expired reacquisition and different-client transfer;
one CLIENT_HANDOFF and no replay duplication; stale revision/claimed epoch/
wrong-project refusals; cross-session command-id conflict; post-attach changed
model binding refusal; active renewal; and live or terminal-but-unsettled
transfer refusal. A regression wrapper executes the existing stored-profile/
runtime-route and exact Task/Session binding tests without starting a model.

The source unit fixtures and their SQL mutations are deliberate test fixtures.
No fixture state is passed off as native product acceptance. Native 8-leaf
failures remain historical evidence; none was rerun by this author.

Known legacy expectation: TestClientSameWriterRenewsExpiredLease in unchanged
client_protocol_control_windows_test.go currently expects ACKNOWLEDGED.
After this contract correction it should receive COMPLETED plus AttachResult,
while its epoch=2, valid-lease and stale-revision checks remain valid.
Root must independently review that old expectation before any broader-suite
acceptance; this package does not quietly weaken or modify it.

## Static evidence and execution boundary

Recorded sequential replacements reverse byte-for-byte to the complete T6
production input, including all unaffected methods, gates and assertions.
Inputs are SHA-256/length pinned and rechecked during seal.
Go lexical delimiter checks are source sanity checks, not Go parsing or builds.
No Go/gofmt, native subprocess, SQL, model, private resource, signer, canonical
write or test execution occurred. Python only constructed and checked Source
and metadata in this receipt namespace.

Diagnostic 827 preserves the exact failed functions.exec source and SyntaxError.
It failed during JS parsing before any tool/process/file action; outer/Python/
native exit fields are null. The corrected construction uses an independent
valid template and retains the failed input; the failed input was not rerun.

Root must independently review, compose/build a fresh isolated candidate,
execute the new unit tests plus the unchanged relevant runtime binding gates,
inspect any legacy expectation conflict, and then perform the authorized native
leaf validation. This Source handoff grants no execution or acceptance authority.

