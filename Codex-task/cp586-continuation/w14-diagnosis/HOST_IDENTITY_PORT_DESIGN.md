# W14 local-subject provenance — verified source trace and proposed scope

Status: READ_ONLY_DESIGN_READY_FOR_SCOPE, not implemented or qualified. Parent's current baseline is CP590/Main b84b065739d64a61407ca815651880b6c06ae36a. The earlier blocked-read record remains unchanged. This design changes no product source, token, database, test expectation or native scope.

## Actual conclusion

The existing native transport proves that a native connection came from the Host's Windows user. The current v2 request path does not retain enough provenance to prove that its claimed requester client and current session writer are the two clients covered by that native proof. There is no reusable pair-client attestation registry in the traced Host/v2 chain. Adding a facade returning the same Owner/Host strings would not close this gap.

Verified anchors, bound to exact source hashes in HOST_IDENTITY_SOURCE_EVIDENCE.json:

| Layer | Source facts |
| --- | --- |
| v2 ingress | internal/api/v2.go:155 resolves the bearer through AuthenticateToken; :178 starts the command transaction; :191 calls Execute with principal.ID. No native-peer/client proof is passed. |
| bearer identity | internal/domain/client_protocol_auth.go:24-37 wraps the ordinary credential resolver. internal/domain/auth.go:51-60 issues a row with token_hash, principal and expires_at; :67-98 checks expiration/revocation, roles/grants and remote constraints. The schema at migrations/sqlite/0002_domain.sql:34 has no client, Host or native issuer provenance. This is valid domain authentication, not a two-client native attestation. |
| Native trust root | internal/host/native_pipe_windows.go:127-143 obtains the OS peer PID, resolves its identity and compares SameUser with Host.Identity. :145-151 then passes only raw frame plus boolean true to HandleNative: the peer facts are discarded at that seam. |
| frame client name | internal/host/native.go:44-47 defines caller-supplied ClientID. :121-151 checks the boolean, shape and nonempty id, then dispatches; it does not persist a client/native-peer association. |
| CLI shortcut | apps/cli/cli_native.go:93-120 reads one shared host/session.json token; :123-133 accepts an explicit credential or valid shared file before nativeBootstrap is called. A normal v2 CLI session can therefore have no client-specific native handshake. |
| global credential | internal/host/bootstrap.go:108-130 issues the Host-wide short credential and immediately revokes its predecessor. native.go:62-70 stores the shared private file. The native result echoes client_id, but does not make the domain token client-bound. Do not piggyback a new transfer attestation on BootstrapOwner: it can invalidate the source CLI's cached credential and interfere with CANCEL. |
| Host metadata | internal/host/client_configuration.go:13-23 checks bound Host/principal state and returns OwnerHost/Principal. It neither identifies both clients nor calls native peer verification. The existing interface at client_protocol_configuration.go:19-24 deliberately returns metadata, not credentials. |
| authority root | internal/domain/orchestration.go:85-151 verifies current domain delegation/identity lineage. For a direct non-revoked principal with no orchestration row, :113-118 returns that principal id. It is not a Windows SID or proof of a current peer. |
| reusable confirmation pattern | client_runtime_coding_windows.go:46-63 binds Owner, OwnerRoot, HostID, ParentHash and session/config/workspace snapshots; :386-392 rechecks root and Host metadata. Reuse this exact-binding pattern, not these strings as an OS proof. |
| composition | internal/api/server.go:53-65 injects the existing runtime/configuration authorities. apps/control/main.go:268,292 supplies localHost. The outer drainGate (drain_windows.go:29-53) is a maintenance ingress gate, not a client identity verifier. |
| Host generation | host.go:189-193 derives InstanceID from private directory plus principal ref; it is stable across a process restart. Native proof must additionally bind a current private boot/generation reference, not mistake InstanceID for fresh proof. |

## Minimum new production pieces

This requires a trusted producer plus a read-only verifier; one interface alone is insufficient.

1. Preserve real peer evidence at the native transport boundary. Add an unexported verified-peer value carrying the OS-produced subject ref, observed process identity/connection and current Host generation. Only the actual transport may construct it. Keep the legacy HandleNative(raw,bool,...) behavior for existing operations, but that boolean must never be sufficient to mint a new transfer proof.
2. Persist a native client-instance registration and the session writer's native provenance when that writer is originally granted. The registration binds the logical client to a server-generated client-instance/attestation ref, actual OS subject, Host/generation and original provenance. Reject ambiguous replacement of a registered instance; do not reconstruct historical proof from client_id, workspace locators, a domain Owner label or a database row copied from another Host.
3. For the requester, produce a fresh native attestation bound to the exact proposed attach command id and canonical envelope hash, the current session revision/writer epoch/source attribution, the requester instance, Host generation, Owner/root and actual credential digest. A generic reusable client registry entry alone is insufficient: a holder of a bearer token must not be able to claim a registered client id and borrow an old native proof for a different command.
4. Use a dedicated private native attestation operation/Host prepare-confirm seam without issuing or rotating a credential. It must use the actual verified-peer value and current Host reverify, not a public HTTP call or a caller-supplied same-user flag. The exact private DTO/version belongs to the new scope; the published v2 Envelope remains unchanged. This document does not authorize executing the operation.
5. At v2 ingress, derive a private authentication context from the already resolved principal and actual bearer digest; do not add client-supplied Owner/root/Host/proof fields to the public payload, log raw tokens or expose them to renderer. For the new grant, recheck the credential row's principal/revocation/expiry and native provenance in the caller's transaction. Existing auth remains the authority; this is provenance metadata, not a second Owner/password/role system.

Suggested domain-facing interface (design only):

```go
type ClientWriterTransferAuthority interface {
    VerifyLocalWriterTransfer(
        context.Context, *sql.Tx, LocalWriterTransferQuery,
    ) (VerifiedLocalWriterTransfer, error)
}

type LocalWriterTransferQuery struct {
    Principal, AuthorityRoot, ProjectID, SessionID string
    CommandID, RequestHash string
    CurrentWriterClientID, CurrentWriterAttestationRef string
    RequesterClientID string
    ExpectedRevision, CurrentWriterEpoch int64
    // Actual credential provenance comes from trusted ingress context,
    // never a field claimed in the Envelope or a model-generated object.
}

type VerifiedLocalWriterTransfer struct {
    HostID, HostGeneration, OSSubjectRef string
    OwnerPrincipal, OwnerRoot string
    SourceClientInstanceRef, TargetClientInstanceRef string
    SourceAttestationRef, TargetAttestationRef string
    CredentialProvenanceRef, ProofHash string
    IssuedAt, ExpiresAt time.Time
}
```

The provider may only read attestation/credential state using the supplied transaction and bounded Host identity metadata. No second transaction, native IPC wait, worker/provider start or mutable registration belongs inside that method. Native registration/prepare runs before the v2 transaction and commits its trusted facts separately. The original proof ref/hash is stable; a verification timestamp is not a new transferable proof. A failed/missing/stale/revoked/foreign proof fails closed. The domain independently checks Owner RBAC, non-remote principal, currentAuthorityRoot, original session attribution and current CAS; matching proof strings do not replace those gates.

The identity/provenance facts should be in protected, versioned, Host-issued storage that the command transaction can read consistently. Proof issuance and revocation must not be an unversioned private-file race with the final grant. No new public SQL writer is allowed. Only the trusted native producer may issue these facts; immutable hash-shaped records alone would not authenticate their origin.

## ACK, no-work proof and final CAS

The bounded first slice can support only genuinely canonical quiescent work:

- Current and historical session Tasks/Runs are in the states already accepted by the strict settlement predicates; process/child/queue/effect reconciliation and required terminal projection are confirmed. A BLOCKED task with no Run does not become settled merely because execution never started. Do not change the shared clientTurnSettled predicate for this slice.
- All related dispatches, effects, pending permissions, follow-up/control requests and recovery fences are resolved. The query covers the original session relation, not just the current mapped head. Do not use global drain as a substitute or clear a queue.
- No active Run or external operation is paused/cancelled by this slice. If any active or UNKNOWN work exists, retain the original owner and a visible blocked/unimplemented result. A real safe-pause/Coordinator path is a separate scope.

Call chain:

1. Target observes the actual snapshot, prepares the exact attach(true) envelope with writer_epoch null, and obtains the request-bound attestation through the trusted native path. The source writer's original native provenance must already exist.
2. v2 resolves the existing bearer/principal and creates the private credential-provenance context. Execute reads current domain root, session/original attribution and revisions, then the new authority verifies both native associations for this exact request.
3. One transaction records a unique active attach intent plus the original ACK and a per-session new-dispatch/write hold. Record the complete authority/work snapshot hashes. ACK grants no writer authority and starts no Run. Preserve Goal, Task, result, checkpoint, queue and failure lineage.
4. The exact same command/hash replay gets an attach-specific finalization path. Execute:732/749 currently advances only session.control ACK; historical attach ACK with no valid new intent must remain immutable and must not be invented into a grant.
5. Finalization rechecks credential/proof generation and expiry, Owner/root/Host, full canonical settlement, input/work snapshot and current session/intent CAS. In one transaction transfer owner, advance epoch/revision using the existing grant/journal invariants, append one CLIENT_HANDOFF and seal the final response. Keep the original ACK separately auditable.
6. Only COMPLETED with its returned snapshot may give the target a new writer epoch. Source writes fail the existing epoch/attribution gates. No implicit RESUME, task acceptance, cancellation or new Agent follows a handoff.

If proofs or inputs change between ACK and grant, reject or leave the intent visibly blocked without changing owner. Do not silently replace the expected revision, renew a native proof from an Owner string, or reuse a consumed native scope. CANCEL remains higher priority; never resurrect cancelled work or clear explicit-recovery flags.

## Legacy and migration boundary

- Preserve ordinary token authentication, read-only access and existing same-writer behavior unless a separately reviewed compatibility scope changes them. Do not describe those unproven legacy paths as native-qualified transfer.
- Require proof for every new writer grant/switch, including expired or null-lease fallback. Keeping the old expired-lease branch as a bypass would defeat the new boundary. A legacy token or session without trustworthy writer provenance cannot qualify by guessing an Owner or client id; it needs an explicit trusted rebind/reauthentication scope or remains read-only for transfer.
- Missing tables/provider/proofs close the new capability. Do not auto-backfill SID/Host/issuer evidence from domain strings, public Artifact JSON or locators. New schema, backup/restore invalidation and controlled migration need Root's schema owner; no migration number is assigned here.
- A Host restart or restore invalidates old boot-generation evidence. Persisted pending intents cannot finish until current proof is available under the approved lifecycle. Cross-Host/root/credential drift is a refusal, not a new lineage or budget.
- Attestation must not rotate the shared credential; bootstrap currently revokes its predecessor. Native token expiry/revocation/UNKNOWN facts remain authoritative. Missing an attestation row is not approval to repeat an old native scope.

## Exact path suggestions for the next separately authorized worktree

- internal/host/native_pipe_windows.go and internal/host/native.go: retain verified-peer provenance for a new privileged attestation seam; legacy boolean cannot mint it.
- New internal/host/client_provenance.go: trusted native client/request attestation producer and read-only Host verifier, with private generation and no credential material in responses.
- internal/host/bootstrap.go/state.go only if the new issuer/credential/generation fact lifecycle needs changes; preserve existing rotation/rollback semantics and do not make attestation call BootstrapOwner.
- New internal/domain/client_writer_provenance.go: typed query/evidence, consistent readonly fact lookup and session-writer provenance binding. No new scheduler.
- internal/api/v2.go/server.go: private ingress provenance and optional authority injection. Existing ClientConfigurationAuthority remains metadata-only; absence of the new port fails closed.
- internal/domain/client_protocol.go and new internal/domain/client_protocol_attach.go: durable intent/ACK/replay/final CAS and per-session hold, preserving strict settlement and historical receipts.
- A new migration allocated by Root for protected native/client/writer provenance plus attach intents. Do not edit old migrations or automatically open/migrate the old DB.
- apps/cli/cli_native.go, cli_verbs.go/cli_stream.go: only explicit cross-client takeover obtains the request-bound native proof, sends the identical envelope, and adopts authority only on completed snapshot. Desktop main integration requires its own actual native bridge path to be located before editing; no renderer token or model tool can manufacture the proof.
- Test locations: internal/host/native_pipe_windows_test.go and native_test.go; new domain provenance/attach tests; internal/domain/client_protocol_atomic_test.go; internal/api/v2_sessions_test.go; apps/cli/cli_sessions_test.go. Mock peer/authority fixtures remain explicitly synthetic, never native qualification.

Acceptance scope of this proposal is source/fixture only. Positive tests need real server-issued native facts in their explicit fixture; negative tests include copied/ordinary bearer, fabricated client id, stale/mismatched command hash, foreign SID/Host/generation, revoked/expired credential, missing source proof, registered-id overwrite, same-root-but-different-native-subject, expired-lease bypass, legacy ACK, competing intent, drift during grant and complete canonical work history. Preserve the old blocked fixture as a negative case and add a separate genuinely settled positive case after production logic exists; do not merely change WRITER_BUSY into an expected green result.

No source was modified and no native, model, old qualification, database or test was executed by this investigation.
