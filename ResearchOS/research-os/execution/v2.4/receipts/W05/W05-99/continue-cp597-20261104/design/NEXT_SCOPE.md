# CP597 — fresh session.create Native-origin pilot

Status: READ_ONLY_CONSTRUCTION_BRIEF, not implemented or qualified. Main observed at `001f7e5a4d95152c8f83874a60d9fbd3bbace538`, checkpoint 597, with 20 pre-existing tracked changes retained. This packet is new C evidence; previous frozen packets are untouched. No Go, database, native, model or resource scope was run. The already consumed C resource scope and historical UNKNOWN approvals are unrelated and must never be replayed or consulted by this pilot.

## Fixed outcome

Implement one reachable path: final client request and bearer -> dedicated trusted Native action -> current Host's immutable in-memory witness -> same HTTP transaction creates a fresh session and records its actual initial writer origin -> normal typed result. It is a source/transaction pilot, not full client identity qualification or W14 handoff acceptance.

Root accepted the narrower witness-map construction: no issuer-key infrastructure, no attestation table, no new writer journal. Only the verified native transport may add a witness; ordinary SQLite rows, caller labels and success booleans cannot populate it. Witness values are immutable copies, keyed by server-random reference and bound to current Host/generation. A server-random per-attestation connection-instance ref is attribution for that observed native connection; it is not a stable process/PID identity and promises no cross-process or cross-restart client continuity.

The first useful durable origin must be a **fresh session.create**. Current `client_protocol_sessions.go:187` assigns epoch 1 to a caller client label; neither current epoch nor old creation receipts prove a Native source. Do not backfill any existing session. `goal.start` may also create a session through this helper; that route remains explicitly legacy in this pilot. Same-writer rebind, cross-writer ACK/replay/CAS and active-Run pause are later scopes.

## Current facts that determine the seam

- `host/native_pipe_windows.go:127-151`: kernel peer PID -> verifyNativePeer -> read frame -> handleVerifiedNative. `native.go:123-158` binds OS peer/Host/generation; `:213` retains the invocation at dispatch. Existing boolean HandleNative has nil peer and cannot sign this new action.
- `host/native.go:24-31,45-49` and `contract.go:34-44`: only bootstrap/import/workspace kinds exist; frame top level is kind/client_id/payload, with 8192-byte maximum and no request version slot. Bootstrap payload is EmptyPayload and all existing replies are closed. A dedicated new kind/profile is required; never smuggle fields into bootstrap or change frozen protocol schemas.
- `domain/client_protocol_auth.go:59-81`: actual credential context is private and bound to the exact tx/ClientService/principal. It contains no Native proof. New domain validation must derive the real credential hash from that context; accepting an HTTP-supplied hash/Owner facade is forbidden.
- `domain/client_protocol.go:728-733` can return a sealed original response before dispatch. `:824-836` validates/seals the response and immutable command identity. Put the fresh-only validation after the sealed replay decision and record origin after the original response is sealed, before API commit. Existing ACK progression remains untouched.
- `domain/client_command_identity.go` validates original raw requests and stores exact request bytes in private headers; the existing identity triple `(principal,command_id,request_hash)` is the correct unique response/consumption anchor. Reuse it, not a replacement journal.
- `client_protocol.go:1179-1195` renews the same label's lease, including an expired but non-null lease; `:1197-1198` blocks a live foreign writer. Expired/null foreign leases can still transfer through settlement/HandoffEpoch/CAS at `:1200-1244`. Thus cross-writer transfer is **not globally closed today**.
- `client_protocol_journal.go:126-139` already writes outbox and watermark CAS in one transaction/savepoint. The pilot needs no additional writer event stream.

## Proposed closed Native definition (Root-owned contract scope)

Add `NATIVE_CLIENT_ATTEST_REQUEST` / `NATIVE_CLIENT_ATTEST_RESULT` under a new pinned, closed `internal/host/contracts/native.client-attestation.v1.schema.json`. Keep existing frame shape and three original definitions unchanged. Version only the new payload (`schema_version: 1`), not an unknown frame-top-level field.

Request required fields: schema_version, credential_value (write-only), command_id, method (const session.create), project_id, request_raw_sha256; session_id/expected_revision/writer_epoch must be null if included. Frame.client_id is the committed command label, never an authenticated instance ID. The proposal DTO file fixes shapes and intent; it is not an installed schema or an active wire definition.

The digest-only request deliberately means "this verified native caller commits to these exact bytes". It does not claim that the producer saw/parsed those bytes. The HTTP consumer must hash actual env.originalRaw itself and compare every scoped field with the decoded request. This avoids silently narrowing public CreateSessionPayload: its strings have no maxLength, so a complete legal raw request need not fit inside the existing 8192-byte Native frame. Public request/schema limits are retained. IDs in a Native frame remain subject to that frame's real size bound; failure must be explicit and must not fall back to an unproved create.

Result required fields: schema_version, attestation_ref, server-generated client_instance_ref, host_instance_id, expires_at. Return neither raw credential, credential hash, OS subject, raw boot generation nor private witness body. Reject unknown/duplicate keys and a second JSON value for this new privileged profile; do not claim the legacy single Decode already provides strict canonical parsing.

Producer checks: non-nil current typed peer, real existing bearer authentication, local non-device Owner/project grant, current authority root and bound Host, fresh command scope. It must call no bootstrap, renewal, IssueCredential or revoke function. Target proof therefore cannot rotate the source's cached credential or change CANCEL authority. All values entering the witness map come from actual trusted resolution plus the caller's explicitly identified commitment. Do not reuse old Native/resource approval journals.

Witness expiry is the earlier of credential expiry and a short explicit TTL (proposal 60 seconds); cap live entries (proposal 256) and prune expired entries during insertion. No new scheduler. A failed reply-schema check may withdraw only its unpublished witness; an uncertain delivery is reconciled by the ordinary command identity on later HTTP replay. HTTP execution never deletes or mutates a witness as a substitute for SQL consumption.

## Fixed DTO and ports

Host private producer:

```go
func (h *Host) nativeClientAttest(ctx context.Context,
    invocation nativeInvocation) ([]byte, func(), error)
```

Domain Native-stage resolver, using the existing authenticateWithCredential path in a caller-owned read transaction:

```go
func (s *Service) ResolveNativeCreateCredential(ctx context.Context,
    tx *sql.Tx, token, project string) (NativeCreateCredential, error)
```

This resolves real principal/root/credential hash/expiry and checks local Owner/project permission. Its exported facts alone are not a proof. Host additionally requires its real peer and current binding before inserting into the private map.

Consumer port, injected with the actual same Host in both control handler compositions:

```go
type NativeCreateAuthority interface {
    VerifyNativeCreate(context.Context, *sql.Tx,
        NativeCreateProofQuery) (VerifiedNativeCreateOrigin, error)
}
```

Query fixed fields: AttestationRef; actual Principal/AuthorityRoot/CredentialHash/CredentialExpiresAt from the private exact-tx/service/principal context; CommandID/ClientID/ProjectID/Method and actual raw SHA256; null SessionID/ExpectedRevision/WriterEpoch. The Host compares the immutable current witness, boot, expiry and all facts, and returns only an immutable copy. The port does no IPC, waits for no worker, starts no extra transaction and performs no SQL consumption.

An HTTP header such as `X-ResearchOS-Native-Attestation` carries only an untrusted reference. Reject multiple/oversized malformed references; a reference is not proof until the real Host port resolves it. A narrowly named claim-context helper may transport this reference, but must not let a string/bool create authenticated credential facts or a verified origin.

## Exact grant/consume/replay sequence

1. Client fixes the complete envelope, exact serialized raw bytes, current bearer and Host origin before asking Native. Proof acquisition failure is NOT_SENT; do not silently downgrade.
2. Native issues only the fresh-create witness. CLI/Desktop main retain the reference; renderers receive no credential or private witness facts.
3. HTTP preserves current protocol/auth/decode/RBAC ordering. The existing exact identity lookup may return a sealed ordinary COMPLETED replay. Return those original bytes/identity without any new witness consumption, origin row, session, epoch, grant or event. Ordinary current authentication still applies. ACK replay is untouched.
4. Only a genuinely new session.create with a proof claim enters fresh witness verification. Missing/expired/mismatched witness with a supplied claim is a refusal, never legacy fallback. The absence of a claim remains ordinary legacy compatibility, not Native-qualified creation.
5. Run the existing creation handler and MapClientSession unchanged. After the typed response and original command identity are sealed with the original private v1 header, call a private `recordNativeCreateOrigin(...)` in the same Execute transaction. Query the real created session, assert actual project/session/epoch 1/writer label and response, recover exact original header bytes and verify their raw digest, insert the unique origin/consumption row, then CAS the private header from v1 to its marked v2 form and revalidate the complete pair. Any error rolls back mapping, origin and marker together. No new API result/event fields are required.
6. Preserve Root's adopted policy distinction: legacy sessions keep existing behavior. For **new origin-bearing sessions**, a foreign-client writer attach is rejected before old expired/null-lease fallback, even if the current witness was lost at cold start/restore. A corrupt/missing-related witness is not permission to erase the historical marker and downgrade into legacy takeover. Same-writer renewal creates no new source proof in this pilot. This is not global W14 handoff implementation.

### Stable private marker: absence must not become legacy

Root requires a stable relation even if an origin row is missing. Actual `client_command_identity.go:219-278` uses a strict private v1 header with exactly schema/encoding/raw_envelope_base64. Add a separate private v2 branch with a closed `native_create_attestation` marker (version/reference/witness digest/actual raw digest); continue to read/write legacy v1 unchanged. Only the domain's already verified witness context may seal v2 metadata after successful creation and origin insertion; never copy a request/header claim directly. Preserve exact original raw bytes and public response schema. Add the fixed marker allowance to the v2 private-header size bound rather than reducing the existing 1MiB request capacity.

The original v1 header is built before dispatch. The narrower reviewed order seals v2 only after COMPLETED session.create and origin insertion; no v2 marked REJECTED record is permitted. A marked completed create requires exactly one consistent origin; an origin without a matching marker is corruption. Ordinary sealed replay and attach's original creation lookup enforce these relationships. Use exact stored response body bytes for its digest, not an independently re-encoded body. If the store declares adoption, absent/changed provenance table or invariant triggers is a storage-integrity error, never no-origin/legacy.

Root's schema scope must prohibit direct INSERT of v2 and allow only the checked v1->v2 seal after a matching origin exists in that transaction. Then protect Native-marked idempotency headers/body from UPDATE/DELETE/REPLACE, so missing origins cannot be hidden by downgrading a completed receipt to v1 or REJECTED. SQL markers only enforce consistency; they never create a current Host witness or Native authority. No new current_ref column or writer journal is needed.

## Minimal persistent relation (Root schema/backup owner)

One proposed table, `client_native_writer_origins`, suffices with the immutable in-memory witness design. It is both initial-writer relation and once-only consumption, not an authentication authority or journal.

Minimum fixed relationships: PRIMARY KEY attestation_ref; UNIQUE(principal,command_id); UNIQUE(project,session_id,writer_epoch) with epoch fixed 1 for this pilot; foreign key to existing immutable command identity `(principal,command_id,request_hash)`. The row contains schema version, host/generation reference, server-issued connection-instance ref, OS subject ref, actual credential hash, actual raw request hash, semantic command hash, actual project/session/client, original response hash, issue/expiry/record times, canonical body and its digest. Body/columns, command identity, original raw header and typed response must agree. UPDATE/DELETE/REPLACE/UPSERT cannot rewrite a committed row. Digest shape/SQL uniqueness alone do not authenticate the producer; future use still demands the current Host witness.

Highest tracked numbered migration source is 0024, with separate unnumbered next_v24_sessions.sql. This is not an observation of any DB's applied version. **No migration number is assigned by this author.** Reviewer proposes a narrower embedded, prepared addon at `internal/domain/contracts/0025_client_native_writer_origins.sql`, installed explicitly only in fresh owned fixtures, outside the ordinary numbered migration glob. Root must reserve this name and its adoption policy before construction. Under that prepared-addon approach, do not change the ordinary version-24 ceiling or old startup/DB behavior. New Native use reports authoritative unsupported when the addon was never adopted, and integrity failure for an adopted/marked but missing or drifting addon. This distinction cannot become an invalid-proof fallback. Do not edit the frozen fixed 23->24 upgrade verifier to pretend it is a generic new-version path.

Cold start creates a new Host generation and empty witness map. Backup/restore never serializes/reconstructs that map. Old origin rows/consumption survive as historical immutable relationships, but do not become current Native authority and are never refunded. Cross-restart qualified handoff/rebind is explicitly unsupported by this pilot. This safe limitation must be visible in documentation and must not be converted into an automatic legacy bypass.

## Exact implementation paths to register

Author production paths: new `internal/host/native_client_attestation.go`, new `internal/domain/client_writer_origin.go`; modify `internal/host/host.go`, `internal/host/native.go`, `internal/host/contract.go`, `internal/domain/client_protocol.go`, `internal/domain/client_protocol_auth.go`, `internal/domain/client_command_identity.go`, `internal/api/v2.go`, `internal/api/server.go`, `apps/cli/cli_native.go`, `apps/cli/cli_v2.go`, `apps/cli/cli_verbs.go`, `apps/desktop/main/main.js`, `apps/desktop/main/lib/native.js`, `apps/desktop/main/lib/http-wire.js`, `apps/desktop/main/lib/ipc.js` (17 production files).

Author tests: new `internal/host/native_client_attestation_test.go`, `internal/domain/client_writer_origin_test.go`, `internal/api/v2_native_create_test.go`, `apps/cli/cli_native_attestation_test.go`, and `tests/ui/native-create-attestation-fixture.cjs` (pure mock transport, no GUI/native/model). Do not edit existing acceptance thresholds or fixtures to make old work appear accepted.

Root-owned integration/contract paths: new `internal/host/contracts/native.client-attestation.v1.schema.json`; `apps/control/main.go` (both handler compositions at current lines 228 and 292). Schema/backup owner must separately register the prepared SQL/addon loader, fingerprint/typed validator, backup guard and focused fresh-schema/backup tests. Reviewer's prepared-addon plan supersedes the earlier broad version-25/store-ceiling suggestion; the exact schema-owner manifest is authoritative. This worker does not reserve a number or modify a live DB. Root must also pin client enablement to the adopted prepared capability; unsupported legacy storage must not be misreported as a completed Native vertical, and supplied-proof failure never silently downgrades.

CLI seam: `v2CallTransportDetailed` fixes json.Marshal bytes at cli_v2.go:252 and bearer immediately before HTTP. Add a private attestor callback to v2Context, always wired by production newV2Context using a captured/verified full discovery origin. Programmatic legacy fixture contexts with nil callback stay explicitly unproved; production missing/mismatched discovery returns a refusal. Call only for session.create, after both raw/bearer are fixed. ConfigureCLICall and doctor have independent v2 POSTs, but they never create a session in this pilot and remain ordinary; doctor must not renew.

Desktop seam: main.js injects the actual Native helper into createTransport; ipc.js passes a copied Host origin as private transport metadata. http-wire.js:162 fixes actual raw bytes; after REQUEST preflight and unchanged-object/resource checks (:172-177), obtain the witness for that raw, bearer and origin, then add the reference header before :179 post. Replay may reuse the original request while replacing bearer, so never attach a proof just to credentialFor or regenerate request bytes independently. Existing pending/possiblySent semantics must survive; no secret enters persisted pending request metadata.

## Necessary focused tests, after a real scope exists

- Typed current peer can insert a witness; nil/boolean/foreign Host/old generation cannot. Ref and instance are server issued, not caller-overwritable labels or PID identities. Unknown/duplicate/trailing JSON and secret-canary errors do not leak raw credential. No bootstrap/issue/revoke calls occur.
- Actual raw, method, project, client, command, null session/counters, bearer, principal/root or Host change rejects the old reference. Test real >2^53 wire counters on non-pilot methods remain unaffected; no new float-based integer limit.
- Current fixture SQL auth still rejects revocation/expiry/remote devices and follows existing RBAC/error order. A map row assembled only in SQLite cannot authenticate; a valid witness without the exact HTTP credential context cannot authenticate.
- Fresh real creation commits one mapped session plus one unique origin; failure after mapping, response validation, identity sealing or origin insertion leaves neither committed grant nor origin. Native witness remaining unconsumed is not a refund of an old approval.
- Sealed COMPLETED replay, including a new bearer for the same currently authorized principal, returns the original response with counts/counters unchanged. ACK remains pending and cannot be completed by this feature. Concurrent same-command/different-scope, REPLACE/UPSERT and transaction rollback negatives reject duplicates.
- Legacy old sessions never acquire origin rows from same-writer renewal or valid epoch. New origin-bearing sessions cannot use foreign expired/null-lease fallback. Cold/restore loses current witness without deleting or refunding durable origin rows.
- CLI and Desktop use exactly the bytes passed to HTTP and the bearer selected for that attempt; Host/discovery changes or attestation failure prevents send. Independent configure/doctor paths retain no-renew/legacy semantics. Use injected Native dial and Recorder/mock HTTP for development; any actual native qualification must be a new separately scoped fresh-owned run, never old resource C/UNKNOWN reuse.

## Read-only diagnostics

All reading sessions reached terminal status. Two discovery commands mentioned absent internal/runtime; one later search guessed execution/supervisor. Those paths were not source reads or execution. Actual `ops/supervisor` was then located from its real import and read. Its ObserveProcess also hashes executable images, so do not call that lifecycle/expensive helper just to get a client-instance label. This pilot uses a fresh per-connection server ref and explicitly avoids stable PID continuity. No failure counter or global checkpoint was changed by this researcher.
