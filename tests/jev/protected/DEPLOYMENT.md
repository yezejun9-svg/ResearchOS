# Frozen independent-identity evaluator deployment

The single reviewed `canary-broker` binary contains the synthetic canary and fixed
formal evaluator. It does not generate protected data or call a provider during
installation. Build/tests/Plan are preparation evidence; actual installed identity,
DPAPI delivery, real provider execution and independent review remain unverified.

## Fixed machine changes and boundaries

`ResearchOSVerifierCanary` is a manual-start own-process Windows service running as
`NT SERVICE\ResearchOSVerifierCanary`. Only its fixed ProgramData directory is
created. Administrators own the immutable binary/install manifest; the ordinary
developer has read/execute and service config/status query rights, without service
start/stop/change rights. Private files have an exact service-user owner/DACL.
Required token privilege is `SeChangeNotifyPrivilege`.

The public remote-rejecting, first-instance protected named pipe accepts exactly
`summary-v1`, `start-frozen-run`, `status`, and `aggregate`. Clients attest SCM
account/configuration, pipe server PID before/after exchange, and installed binary
SHA. There is no arbitrary file/model/path/command interface. Protocol messages
are bounded to 4096 bytes and overall client exchanges to three seconds. Every
public request rechecks the four private canaries. Separate configuration uses an
admin-only pipe; the unelevated developer is denied access.

## Credential delivery and one-run contract

Explicit elevated Install must use the same user as ReaderSID. It verifies the
permanent project identity and reviewed binary SHA, then decrypts only that
project's `.local/secrets/typesafe.dpapi` in memory. Credential bytes travel through
the immutable helper's stdin and the authenticated admin-only configuration pipe.
The service saves only service-user DPAPI ciphertext in its private directory,
using CREATE_NEW. No key appears in argv/env, stdout, SQLite or plaintext files.
Configuration never creates the run marker or starts a provider request.

Only an explicit `--start-frozen-run` triggers the fixed independent generator
inside the actual SCM virtual account. Generator seed, source bodies, labels,
lineage, raw provider responses and decision details stay private. The request
contains only each frozen input and public rubric. The fixed endpoint/model/rubric
and threshold 0.8 have no runtime overrides. The budget is 30 requests, 15 each for
zh and zh-en. No automatic rerun/retry/tuning is available. Fresh connections avoid
reused-connection replay and redirects are refused.

A CREATE_NEW/fsync run marker precedes generation; each CREATE_NEW/fsync invocation
intent consumes its budget slot before network IO. Restart never resumes network
calls. Unknown responses become ABSTAIN/errors in INTERRUPTED; corruption is
FAILED/CORRUPT. Failed durable summary storage returns BLOCKED_STORAGE. Private
formal files prevent the canary uninstall operation from proceeding or deleting
formal evidence.

RUNNING exposes only invariant state/budget, with zero counts and no per-key or
dataset fields. Terminal aggregates expose only fixed scope counters, real label
denominators, nonabstained action counts, ALWAYS_REJECT deterministic baseline,
and static dataset ticket/hash/size/frozen_at. Interrupted denominators cover only
consumed request slots. Per-key verified development evidence is embedded from the
independently sealed `da21a2d4...` aggregate: 30 development examples per key, all
60 raw choices REJECT and ACCEPT coverage zero. Old-rubric cases are not inherited.
Qualification is always FAILED, maximum mode ADVISORY and authority NONE.

`FrozenProvider` offers only authenticated terminal Boundary/Ready/Describe.
The host may bind the immutable descriptor to a product project during trusted
registration. `Read` always returns ErrIsolation, including for Verifier callers;
private body bytes never return to the ordinary control-plane identity.

## Build, review, deploy

```powershell
& $env:RESEARCHOS_GO build -trimpath -o .local/canary-broker.exe ./adapters/protectedstore/cmd/canary-broker
$hash = (Get-FileHash .local/canary-broker.exe -Algorithm SHA256).Hash
./tests/jev/protected/deployment.ps1 -Binary .local/canary-broker.exe -ExpectedSHA256 $hash -ProjectRoot <original-project-root>
```

Default Plan is read-only and does not read credentials. After the concrete binary,
source, plan and independent review are approved, run the same reviewed command
with `-Action Install -ReaderSID <planned-developer-SID> -Confirm:$false` from the
user-authorized elevated session. The script does not request UAC itself and never
overwrites an existing service/directory. Partial failures preserve state.

Run `verify-deployment.ps1 -ReceiptDirectory <new-directory>` from the ordinary
unelevated developer: its 16 assertions prove only installed canary isolation,
not formal evaluation. Administrator restart plus a repeated unelevated probe
provides persistence evidence. Formal run verification must additionally establish
private evidence denial and independently verify terminal aggregate/provider
invocations without opening protected bodies as the developer.

`-Action Uninstall` may remove only an unused canary plus optional service credential;
a run marker or unknown/formal files cause refusal before stopping/deleting.
No recursive removal is used. Formal retention is a separately reviewed workflow.

## Public preparation verification

`run-frozen.py` captures pinned Go source/build, public-fixture tests, read-only Plan,
and binary SHA with no real credentials or provider calls. The loopback test is
PUBLIC_FIXTURE_ONLY. SCM token identity, actual installed DPAPI handoff and formal
30-call behavior are not proven by these public tests. W11-G04/A08 remain blocked
until installed live execution and independent evidence review complete.
