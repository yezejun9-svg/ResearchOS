# W16 recovery context and idle fence

Status: IMPLEMENTED_IN_SCOPE; independent delta review pending. This is not an acceptance or a release qualification.

Source commit: `613f65f95f60311a0d938d7c30b1aa1b90c2fb8e`, based on `422fb1e8fa89aaccf15f716878f7ee03858e5e21`. Branch: `work/recovery-context-fence`. The source commit contains only the nine files recorded in `sourcehash.json`; this later evidence commit contains receipts only.

The real backup restore machinery now emits one typed immutable context for an idle same-schema cutover. It binds the source and destination Windows handle identities, database byte hashes, persisted restore-report bytes, manifest/purpose/admission lineage, snapshot and host epochs, before/after inventories, complete table-row digests and allowed changed-table summaries. The business slot changes from STABLE to RECOVERING without advancing its epoch or changing stable/active hashes. The START ledger remains DISPATCHED, the candidate remains EVALUATING, and old credentials remain revoked.

The journal references that context while keeping Data at the original root, with PID=0 and RECOVERING. Append and reload both reject removal/replacement of a bound context; a bound context cannot become an active slot. The actual-control host uses the typed callback and returns `BLOCKED_RECOVERY_AUTHORIZATION` before image lookup or Start. Rollback rereads the journal on both compatibility success and failure, rejecting a changed operation or epoch. Legacy untyped synthetic callback behavior and pre-context journal byte/hash encoding remain compatible.

Each operation has one deterministic destination and an exclusive attempt file. A duplicate attempt or a completed copy whose context has not been acknowledged by the journal is `BLOCKED_RESTORE_OUTCOME_UNKNOWN`; it cannot create a second restore point. Only the exact already-bound context can be revisited, and doing so remains authorization-blocked. Missing/changed context, report, manifest binding or native file identity fails closed.

## Bounded scope

Only idle cutovers are admitted by this slice. Active Run rows or unfinished PREPARED/STARTED/UNKNOWN effects are explicitly rejected with `BLOCKED_RECOVERY_NON_IDLE`. Run, audit, effect, old principal/grant, candidate, release-operation and other business tables must remain unchanged. The permitted generic restore deltas are exact credential revocation, source-root relocation, and creation of an empty restore-barrier table if absent; then the single slot receives its RECOVERING fence.

No current recovery actor/proof exists here. No generation qualification, gain, CANARY/ROLLED_BACK projection, observed release receipt, recovery boot, new launcher, protocol message, command, schema/lock/contract change or generic backup modification is supplied. Actual release actions remain closed. Existing production cutover guards remain in the exported entrypoint; the new tests inject an explicitly public synthetic policy into the internal storage helper and therefore do not qualify those guards.

## Verification

Exact command, environment, exit code and parsed test counts are in `commands.json`. Final raw output is `development/targeted-idle.raw.jsonl`, exit 0. Top-level selector: `^TestW16RecoveryContext`. It selects eight new top-level tests across `internal/domain` and `ops/supervisor`; `ops/supervisor/release_host` was compiled with no matching test and is compile-only evidence.

Coverage includes a real encrypted backup/restore on public synthetic idle rows, unchanged source bytes, RECOVERING/EVALUATING/DISPATCHED preservation, revoked credentials, duplicate/lost-ack refusal, context/report/manifest/native-identity tampering, unauthorized table deltas, journal round-trip/context retention/no Start, old journal byte/hash compatibility, illegal transitions with recomputed journal hashes, typed-error no-fallback, legacy callback compatibility, and operation drift on both callback outcomes. Two deliberately minimal poison-row tests prove non-idle refusal only; no active Run recovery is claimed. The synthetic file identity checks exercise Windows filesystem handles but launch no native control process.

Earlier development raw logs remain provenance only. `targeted-first.raw.jsonl` predates journal seam tests; `targeted-second.raw.jsonl` predates explicit non-idle rejection and narrowing. Only `targeted-idle.raw.jsonl` describes the frozen source. The source bytes were not modified after that successful run; `git diff --check` also exited 0 before the source commit. No historical test entrypoint or old runtime/private helper was run, and no broad prior matrix was rerun.

Native Windows CRLF bytes in raw logs are preserved. The initial evidence whitespace check returned 2 because Git treated those carriage returns as trailing whitespace; the final evidence check uses `git -c core.whitespace=cr-at-eol diff --cached --check`. No raw output was normalized or trimmed.

Not run or claimed: actual-control/native child recovery, private/protected evaluator, provider, blocked CLI, activation/SOURCE/S2, overnight/remote/clean-machine gates, source-root relocation positive fixture, or independent same-user isolation. No protected instance PID 79136, live control PID 32736, schema-13 data, credentials, service or endpoint was opened or changed by these commands. Source-root relocation remains guarded by the generic restore implementation and new strict table checks, but its nonempty positive branch has not been newly exercised.

Follow-up is an independent source/delta review of this slice. A later separately authorized recovery proof/projection design is required to lift the authorization block.
