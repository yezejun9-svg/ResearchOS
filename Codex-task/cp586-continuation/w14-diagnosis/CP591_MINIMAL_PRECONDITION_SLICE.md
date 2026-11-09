# CP591 — bounded W14 prerequisite for a separately registered scope

Status: READ_ONLY_DESIGN, not implemented, not a W14 qualification. Observed Main HEAD is b84b065739d64a61407ca815651880b6c06ae36a; checkpoint and its RESUME say revision 591 / 2413 failure records / 0 of 42 formal cases. The prior five-file HOST_IDENTITY_MANIFEST packet remains byte-identical (manifest SHA256 b52769c6f31b354c652e39b59d2c03d66d65e1b249db9ada0d4d21986387d3d8). This report does not assign a migration or authorize an execution scope.

## What the current paths really do

- `internal/domain/client_protocol_sessions.go:176-190`: both `session.create` and project-level `goal.start` call the same session helper. At line 187 it grants epoch 1 to the caller's client_id. It has no native client-instance provenance. `v24_sessions.go:78-110` checks the mapping and inserts `client_sessions`; its writer field is attribution, not authentication.
- `internal/domain/client_protocol.go:907-978`: attach requires current session creation Owner/project authorization, revision CAS, and no claimed writer epoch for takeover. Ordinary writes check current epoch and client attribution. These gates are retained.
- `client_protocol.go:1179-1195`: the same attributed client renews an existing non-null lease without changing epoch. Lines 1197-1198 reject another attributed client while the lease is live, before any same-OS handoff protocol. Lines 1200-1244 allow an expired/null lease transfer only after existing renewal-safety and full settlement checks, then advance epoch, CAS attribution and append CLIENT_HANDOFF. This legacy path does not have trusted two-client OS proof either; do not label it native-qualified or leave it as a bypass when a later proof-requiring handoff is added.
- `client_protocol.go:1303-1333` recovers immutable original creation command/receipt identity, not an OS-client identity. `:1374` is the shared full canonical settlement predicate; BLOCKED/no-Run alone is not proof of settlement.
- `v24_sessions.go:153-177` advances epoch in the caller transaction. `client_protocol.go:1498-1520` emits through the existing `AppendSessionEvent`. `client_protocol_journal.go:43-139` uses the real outbox plus session watermark/revision/epoch CAS and a savepoint. No new writer event journal is needed.
- `client_protocol.go:732-733,749-770`: only session.control ACK currently has a progressing replay path. A later attach ACK must have its own durable intent and explicitly scoped finalizer; returning an ACK alone would persist forever.
- `migrations/sqlite/next_v24_sessions.sql:8-32` contains mapping, attribution, lease and counters, not authenticated client instances or transfer intents. The restore fence in `client_session_fence.go:59-73` is already load bearing and must remain.

## Exact next implementation inventory

Production files, six only:

1. `internal/host/host.go`
2. `internal/host/native.go`
3. `internal/host/native_pipe_windows.go`
4. `internal/domain/auth.go`
5. `internal/domain/client_protocol_auth.go`
6. `internal/api/v2.go`

New test files, three only:

1. `internal/host/native_peer_provenance_test.go`
2. `internal/domain/client_protocol_auth_context_test.go`
3. `internal/api/v2_auth_context_test.go`

No CLI/Desktop, writer grant, settlement predicate, response schema, threshold, native wire operation, database schema, global registry or bootstrap credential policy changes belong to this first slice. Root must register the isolated worktree and exact scope before source edits.

## Minimal private seams

`Host.New(Config) (*Host,error)` remains its public signature. Move its implementation behind package-private `newHost(cfg Config, entropy io.Reader) (*Host,error)` only to test entropy failure without replacing a process-global RNG. Production `New` always supplies `crypto/rand.Reader`. Generate a 32-byte random private boot generation after argument validation and before Mkdir/privateDir/domain.NewCurrentMu or any other mutable setup; return an error directly on short/failed entropy. Do not persist a token/key into host_state.json and do not expose it in native replies.

The existing InstanceID at host.go:189 is derived from directory and OS identity, and stays stable across restart. hostState at state.go:15 has no boot generation. BootstrapIterations also advances during renewal. Neither may stand in for a fresh generation.

Inside native.go, add a package-private `verifiedNativePeer` with private fields for its owning *Host, boot generation, OS-produced identity and observed peer PID. Its validation checks nonzero PID, nonempty real authority, current Host identity via SameUser, exact Host pointer/generation, and an initialized generation. Its sole production constructor belongs to the OS transport path and calls the existing PID identity resolver; it accepts no caller-supplied SID/ref or success boolean. These facts prove the observed peer user, not an approved executable or an independently isolated same-SID process.

The production pipe calls package-private:

```go
func (h *Host) handleVerifiedNative(raw []byte, peer verifiedNativePeer,
    selectionHook func(string) (string,error)) ([]byte,error)
```

It validates the capability, retains it through the common native dispatch boundary, and continues to serve only the existing published kinds. Keep `HandleNative(raw []byte, clientVerified bool, selectionHook ...)` for compatibility, but that legacy adapter supplies no verifiedNativePeer and can never construct one. The internal dispatch can carry a nullable private peer: nil is explicitly legacy/unproven, not equivalent to a successful native peer. No new producer may silently accept that nil path. This slice issues no client registration, attestation or new credential.

In auth.go, factor the existing credential query/expiry/grants/remote-constraint code into:

```go
func authenticateWithCredential(tx *sql.Tx, token string)
    (Principal, authenticatedCredential, error)
```

`authenticatedCredential` has private principal ID, actual credential digest and validated expiry fields; it has no native/client/same-OS flag. Existing `authenticate(tx,token) (Principal,error)` adapts this result to its old signature. This avoids a second weaker resolver, a new writer, or caller-constructed credentials.

In client_protocol_auth.go add:

```go
func AuthenticateCommandTx(ctx context.Context, tx *sql.Tx, token string)
    (context.Context, Principal, error)
```

The function requires the actual caller transaction, resolves the real bearer with the existing checks, and returns a derived context containing the opaque value under a private context key. No exported context setter or credential-value constructor is provided. No public request field, string, bool, header beyond the already validated bearer, or zero value can manufacture a native proof: the opaque value deliberately represents only ordinary credential authentication. Any future native provenance verifier must demand a separate valid Host-issued peer/instance/command binding, not promote this value. Old `AuthenticateToken` remains a compatibility wrapper with its current transaction ownership.

In v2.serve, preserve body limits and protocol-peek precedence, then use the same command transaction for real credential resolution, grants, Execute and commit. Pass the derived context to Execute. Avoid a second nested auth transaction. Never put raw tokens into context, responses, logs or receipts.

## Compatibility and meaningful tests

- An ordinary valid bearer keeps ordinary behavior. Explicit CLI credentials and the shared locator (`apps/cli/cli_native.go:123-133`, Desktop `apps/desktop/main/lib/native.js:86-103`) remain ordinary/unproven. No bootstrap, issue or renewal is invoked just to enrich an HTTP request; explicit old bootstrap's existing rotation remains unchanged.
- Preserve protocol peek before authentication; malformed/unknown method responses remain after the existing auth precedence. Invalid, absent, revoked, expired and failed remote-auth constraints remain 401; an authenticated invalid envelope remains 400; authenticated project grant denial remains 403. host.status still requires a token but no project grant. Preserve the original auth-stage BeginTx failure response (401) and command/commit failures (500), rather than accidentally changing status by moving transaction ownership.
- Host tests: successful same-user typed construction, foreign/empty/zero PID rejection, wrong Host and changed generation rejection, empty capability rejection, legacy bool path cannot produce a capability, failure/short entropy causes no mutable initialization. Use explicit synthetic identity fixtures; no actual native pipe/product process or model is needed.
- Domain tests: fresh fixture real credential query; absent/invalid/revoked/expired credential; revoked principal; grants/remote constraints; context facts equal the actual resolved row; zero/caller-owned context values cannot qualify; a revocation already present in the same tx is observed; legacy wrapper behavior remains. No test labels these facts native-qualified.
- API tests: actual fresh-fixture v2 requests for ordinary-token success/read-only status, all status/error precedence above, revoke/role/grant cases, and a command-side failure rolling back. Retain existing session CAS/replay/native contract tests as narrow regressions; do not edit their assertions to obtain green.

## Persistence and backup boundary for later scopes

First slice adds zero tables and persists zero new provenance facts. This is intentional: a mapping copied into domain_objects or another freely constructed string row would not establish who issued it. Existing private storage can host later records but needs its real producer verification. The verifier-replacement implementation demonstrates ACL-before-content, bounded handle reads, immutable publication and identity checks (`runtime_verifier_replacement_journal_windows.go:89-146`, `runtime_verifier_replacement_windows.go:171-207`); do not generalize that specialized journal or treat its hash chain/DACL/DPAPI as same-SID process isolation.

Before a subsequent slice can enable any new writer grant/switch, Root must allocate reviewed storage/contracts for these minimum relationships (names below are conceptual, not DDL or reserved migration names):

- Host-issued native client-instance/attestation records: server-generated instance ref, real OS subject ref, Host/generation, caller label as attribution only, actual credential binding, issue/expiry/revocation, exact native producer evidence. A transferred shared legacy token cannot itself identify which client is presenting it.
- Writer-grant provenance for `(project,session,writer_epoch)`: initial and subsequent grant command/credential/client-instance/proof refs. Grant facts must commit with the real mapping/journal state; do not backfill historical strings as proof.
- Durable attach intent and original ACK/final receipt: exact command/hash, source grant, requester proof, expected counters and expiry, explicit pending/final state. Integrate with existing command identity/idempotency/outbox and final CAS; do not create a replacement journal or scheduler.

The authority must revalidate actual credential revocation plus trusted records in the final transaction; copying a signed-looking ref/hash into these relationships is insufficient. Cross-file/SQL atomicity, signing/producer authenticity and native proof acquisition need their own explicit design/contract review before a storage format is chosen. No new frozen native wire kind may be invented under the first slice.

`backup_recovery.go:240-246` already fences restored sessions/queues and revokes all credentials. `host/backup_windows.go:175-207` creates fresh roots instead of inheriting the old registry. Future provenance must also become unqualified on generation/restore changes, even when copied domain rows retain matching strings. Do not package private proofs as reusable backup authority. Missing source-instance proof in an old session remains a transfer refusal until a separately authorized trusted rebind workflow exists. Active Run pause/Coordinator work is out of this first slice.

## Read-only diagnostics

All research tool sessions reached terminal status. No native/model process, DB connection, test or product source write was performed. The first broad git status printed a large pre-existing untracked receipt inventory; a subsequent bounded tracked-only status established the 20 old changes and the source-relevant empty diff. Exploratory rg encountered Windows literal-wildcard os123 and one absent guessed session_events.go path; actual files were then located and read as client_protocol_journal.go and Desktop main/lib/native.js. These diagnostics are preserved in the accompanying evidence; no failure counter was reset or modified by this researcher.
