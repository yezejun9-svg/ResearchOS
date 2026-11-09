# Q5 typed fixture attach binding revision

Status: SEALED_SOURCE_CANDIDATE_NOT_EXECUTED. Authority: NONE. Formal acceptance: false.

## Production dependency and scope

This test-only revision requires the independently reviewed ATT3 production client_protocol.go (bbf0d1442b9ca5211e3069dc180911273b906476f4b88a29872cf66d66f9192e, 57574 bytes). ATT3 review decision is SOURCE_ONLY_APPROVE_WITH_FRESH_POSITIVE_BLOCKED; that decision does not establish runtime, restored-positive, whole-chain or formal acceptance.

The baseline is the immutable Q3 package. Q4 was correctly blocked on production attach completion and has no candidate Source. Q5 contains the same five Source filenames: one helper, three runtime test files, and the original Goal test file. No production Source, Main, canonical files, T6, prior package or another author's files are modified.

## Changes

The helper consumes only the actual original session.attach write command's COMPLETED response. muClientCall keeps its existing strict COMPLETED requirement. ACKNOWLEDGED, read-only write_owner_acquired=false, wrong command/method/session/project/owner/revision, missing writer, and invalid schema are refused; the helper never upgrades a response or fabricates a journal entry.

Before attach, a public session.get obtains the current revision, writer and snapshot. Its workspace/model/native/core identities must still match the original session.create response. The command uses this observed revision, null writer_epoch, the same authenticated f.owner principal and current client/project/session. AttachResult and the full SessionSnapshot are validated by the existing schema; the binding projection uses typed int64 fields decoded from the original JSON, with no float64 integer cast.

The helper distinguishes an ordinary same-owner valid-lease renewal from a real other-owner or expired-owner settled transfer. Renewal must keep revision, writer epoch and event sequence. A transfer must have exactly one epoch increment, the existing two revision increments (HandoffEpoch then journal), and one event-sequence increment. It compares parsed lease timestamps against the actual command interval, allowing only the narrow expiry-during-command boundary for a same-owner transfer. It never supplies settlement evidence.

A protected-snapshot digest excludes only revision, writer, event_sequence and updated_at. All remaining returned fields, including Goal/run identity, pending work, model/workspace/native bindings and resume flags, must remain equal. A subsequent actual public session.get must equal the original AttachResult snapshot. A public session.events read must contain no new event for lease-only renewal or exactly the original command's committed CLIENT_HANDOFF for transfer, with matching previous owner/epoch, new writer lease/epoch and effective time within the actual command interval. Exact original-command replay must return the same terminal and leave public state and journal unchanged.

The three runtime files each have exactly two source edits: capture the helper's returned binding, and use its actual project/session/owner/revision/writer_epoch for the first session.send. They no longer hardcode revision 1 / epoch 1 after attach. No original business assertion or later stale/binding rejection was changed.

The Goal file is byte-identical to Q3, including the expired_lease and missing_lease LEASE_EXPIRED assertions.

## Preserved tests and helper boundaries

Original four-file inventory remains 181 exact t.Fatal/Error/Skip calls and 20 original Test names. All 196 lexical assertion-or-error if token sequences are identical; this includes 190 strict t-assertion nodes and 6 fmt.Errorf-only nodes. These counts are not runtime test results.

The complete helper prefix before the old attach function is byte-identical to Q3: strict JSONL action/field/null/type/duplicate/trailing handling, OutputType scope, original run/pass/fail/skip state machine, fixed Go/test2json/Node/Mu resource pins, Root Job and native-child provenance requirements, TLS/x509 checks, public host.configure, exact profile/provider/credential/Host routing and original model callbacks are preserved.

Two additional helper tests are Source only:
- TestTypedRuntimeFixtureAttachRejectsAlteredTerminal starts with an ordinary actual typed transaction fixture response, then rejects 17 in-memory terminal/binding/schema/lease mutations. These mutated copies are negative inputs, never production records or authority.
- TestTypedRuntimeFixtureAttachTransitionUsesExactGeneration checks ordinary renewal and transfer tuples with int64 values above 2^53, and rejects seven stale/missing-journal/double-generation/live-owner/expired-owner/protected-state mutations. These are pure tuple checks, not native or restored-positive evidence.

No new test is treated as a substitute for the eight original runtime failure leaves or the original Goal leaves. No Go test, Go parser/compiler/gofmt, SQL, native process, model call or credential access was executed by this author.

## Separate legacy test conflict

T6 internal/domain/client_protocol_control_windows_test.go TestClientSameWriterRenewsExpiredLease still expects ACKNOWLEDGED. It is outside the Q3 four-original-Source scope and is not copied or edited by Q5. Root must compose a separately authorized/reviewed minimal correction to real COMPLETED/AttachResult while retaining its original future expiry, epoch=2 and stale revision VERSION_CONFLICT assertions. Q5 does not reduce the original unit suite or claim that this conflict has been resolved here.

## Remaining Root work and evidence limits

Root owns fresh isolated composition of ATT3, Q5 and the separate legacy test correction; compilation and the full original test set; strict reporter JSONL and actual exit reconciliation; descendant Go Job/lease closure; and independent actual review. Q3/T6's original 49 Sources / 25 selected parents and observed 61 PASS / 6 FAIL / 0 SKIP, including eight attach-failing native leaves, remain preserved historical results rather than being rewritten by Source work.

Active asynchronous takeover, historical cached ACK terminal reconciliation, true fresh restore positives and shared TEXT-dependent whole-chain behavior remain OPEN/BLOCKED. This helper is scoped to ordinary synchronous typed fixtures; it grants no restored-generation or native authority. True fresh restore remains BLOCKED/PENDING_ROOT_RESOURCE and requires actual authorized current-epoch post-barrier observations and Root-owned verification.

Sourceguard closure covers the public package members, actual frozen production/test inputs and specified dependencies. It excludes independently advancing Root canonical progress. Original IO is in original-tool-io.json; exact inverse replacements and per-file patches cover all changes. Only Python stdlib file hashing, Python lexical utilities and text comparisons were performed.

Mechanical failure 845 is retained in its immutable failure-origin.845.json: initial PowerShell pin-path expression failed with outer exit 1, Python/native exits null; the distinct corrected input succeeded. No prior ordinal is reset. Seal IO is necessarily external to its own manifest. Author stops after sealing and does not self-approve.

