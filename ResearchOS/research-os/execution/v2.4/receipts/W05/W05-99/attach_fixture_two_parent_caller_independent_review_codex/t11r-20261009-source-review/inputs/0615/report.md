# Attach contract fixture correction

Status: SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW_AND_ROOT_ACTUAL. No self approval or formal acceptance.

One candidate file: internal/domain/client_protocol_attach_contract_windows_test.go. The base is the exact ATT3 source pinned by the parent (1805234187e765e965077f9d38afa8e7f79e58385b8bdccd364386627a87a2e7, 10682 bytes). Two narrowly bounded replacements preserve all five original Test function names, every original case name, all unrelated helper/test bytes, and the original acquisition, generation, replay, stale competitor, active-work, terminal-label, configuration, task and runtime binding assertions.

## 1. Legal no-live-owner state

The prior unowned fixture attempted writer_client_id=''. The existing next_v24_sessions.sql CHECK requires length(writer_client_id)>=1; Root's A9 actual log failed at that setup statement before attach business behavior.

The candidate retains the persisted nonempty writer attribution and clears only lease_expires_at. This is a legal existing schema state: lease_expires_at is nullable; BuildSessionSnapshot emits writer:null exactly when the lease is NULL; SessionSnapshot.writer explicitly accepts null. The production attach path cannot use its live-owner renewal shortcut when that lease is absent and therefore follows existing settled reacquisition, epoch/CAS and CLIENT_HANDOFF behavior.

The revised unowned case additionally calls the actual session.get handler and requires its original COMPLETED result, present writer:null and published schema validation before proceeding through all original acquisition/replay assertions. The separate expired-same-owner case remains byte-identical and continues to exercise an existing owner with a past deadline. Neither case removes or weakens the nonempty writer CHECK.

## 2. Claimed epoch is a decoder refusal

The formal RequestEnvelope conditional for session.attach request_write_owner=true requires writer_epoch:null. DecodeEnvelope returns nil plus the exact diagnostic ATTACKER_CLAIMED_EPOCH when a takeover claims an epoch. The existing handlerCommand fixture calls handlerDecode before starting its sourceTx; handlerDecode calls t.Fatal on that expected decoding error. That is the actual A9 line154 failure, not a new business protocol error code.

The candidate keeps the claimed-epoch case and requires nil decoded envelope plus that exact diagnostic. It requires unchanged Session state and zero CLIENT_HANDOFF for that command, then continues the loop before handlerCommand/Execute. This directly tests the actual refusal boundary instead of fabricating a Response from an undecodable command. The existing common REJECTED/ErrorCode/state assertion is unchanged for stale-revision and wrong-project; subsequent command-identity and configuration-binding negative assertions are unchanged.

internal/api/v2.go maps this ordinary decode error to HTTP 400 ProtocolError INVALID_REQUEST and returns before BeginTx/Execute. ATTACKER_CLAIMED_EPOCH remains a decoder diagnostic and was not added to the protocol error whitelist or schema. The candidate does not claim a new HTTP execution test.

## Evidence and validation limits

contract-inputs/T9 contains exact byte copies of the inspected schema, production, public HTTP mapping and fixture helpers. Original ATT3 HDF/MF plus all manifest members were verified. A9's 58 input Source refs and T9 formatted members were pinned along with directly read dependencies; all 140 unique declared inputs are closed unchanged at seal. Root canonical concurrent work is excluded.

The exact inverse of both replacements recovers the original 10682-byte source. Static checks preserve the original five tests and all case lists, balance lexical delimiters, and confirm the current T9 file corresponds to the original after exactly two known gofmt semicolon-to-newline changes. The first comparison failure is retained: Root gofmt removed only the explicit semicolons before want = INVALID_REQUEST and want = FORBIDDEN. The corrected check permits only those exact replacements before complete remaining token equality; no general token whitelist is used.

These checks are Python source/text/hash checks. No Go AST parser, formatter, compilation, Go test, SQL connection, native child, model request or actual new business execution was performed. The two corrected fixture paths remain PENDING_ROOT_ACTUAL. Existing A9 failures are preserved as historical actual evidence, not deleted or reclassified as passing.

Only this new namespace was written. Production/schema/contracts, Main/canonical, T9/T6, ATT3/Q5 and the previously sealed shared-fence SOURCE_BLOCKED packet remain unchanged.

## Mechanical failures retained

876: afRead2 guessed absent spec/v2.4; rg error2, chunk aab099, outer1, Python/nativeNULL.
878: functions.exec JavaScript parse failed on the backtick embedded in a Python regex before any script statement, apply_patch or exec_command executed; all actual exits NULL. The complete original JS input and returned parse error are recorded.
882: first construct-source.py run failed its overly literal original-vs-gofmt token assertion, chunk379404, outer1 and explicit SOURCE_PYTHON_EXIT=1, nativeNULL. Its original script bytes and invocation/result are preserved; exact two-token diagnosis and corrected successful retry are included.

No counter is reset and unrelated Root failures are not duplicated. Inspect 0c201e and retry ed1e19 returned outer0 and explicit SOURCE_PYTHON_EXIT=0. Final seal output is returned externally to avoid a manifest self-reference cycle.

Root next: independent Source review, then fresh authorized composition and actual original five attach test groups. This packet supplies no acceptance authority. STOP.

