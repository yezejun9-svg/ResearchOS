# R2 persistent actual-control host and encrypted cutover mechanism

Owner: codex:/root/control_drain. Lease: R2-independent-supervisor-v1.
Base merge: 352828d (main5019f5b preserved; the only merge conflict retained main sourceFixtureAdapter and all release drain fields in runtime_coordinator).
Implementation source: f05126dba0a194a5af531f3c5bf105f7e3ebc7aa.
Final source: c645ce3674483ac2f01a42d560a8ae136b9e76f8 (only two test corrections after f05126d).
Independent acceptance: PENDING.
ACTUAL_CONTROL_BEHAVIOR_PROOF=UNAVAILABLE. Actual-control qualification/switch gate remains closed. No different-hash actual-control release, actual-control rollback, gain, LIVE/SCM or formal acceptance is claimed.

## Implemented connections

The existing release_host now has a persistent actual-control mode with bounded stdin seal/execute/status/rollback/stop commands. Its actual-control mode owns the supervisor journal and no authority DB connection. The historical one-shot calculator host remains available only after obtaining an exclusive authority-root lease, so it cannot open the same authority while actual control holds the lease.

Control is the only online authority DB writer. Its private inherited HMAC/peer-bound drain channel carries FIXTURE_SEAL, FIXTURE_CURRENT, FIXTURE_DISPATCH, FIXTURE_CUTOVER and FIXTURE_PROJECT. The host's journal snapshot is bound to the current child process identity, root, epoch and operation. Control does not open the host's journal. The CanaryStore locator is inherited in the existing capability bootstrap, with no public HTTP or JSON authorization flag. PREPARED-to-DISPATCHED and receipt projection are control-owned; projection honors the frozen DISPATCHED-to-OBSERVED-to-PROJECTED SQL transitions.

The pre-intent admission backup remains separate. After actual private QUIESCED and DISPATCHED, the host asks control to make a new encrypted cutover snapshot containing that same authority DB. Its distinct manifest hash, original root/database, operation/epoch, purpose and migrations are journal-bound. Snapshot keys use separate cutover paths. Duplicate snapshot attempts refuse rather than silently create a new recovery point.

Actual rollback is connected to normal drain/checkpoint/exit, exact process identity/handle wait, and original-root exclusive lease before offline restore. Recovery validates the real encrypted backup, schema/inventory and external protected references into a new inactive root; the failed root is retained. Existing source relocation, credential revocation and reconciliation policy are preserved. This full actual-control rollback connection has not been exercised because actual-control business proof is unavailable.

## Verification

Command (both attempts): `go test ./ops/supervisor/release_host ./internal/domain -run '^(TestPersistentActualControlHostClosedQualification|TestReleaseCutoverEncryptedSnapshotMechanism)$' -count=1 -v -p=1 -timeout=2m`, using the pinned Go executable, GOENV=off, GOTOOLCHAIN=local, GOFLAGS=-mod=readonly.

1. f05126d first attempt: overall FAIL / exit 1, raw `../same-authority-f05126d/mechanism-tests-first.raw.txt`. The new host test had a uint32/WAIT_TIMEOUT comparison compile error. The new snapshot test queried the nonexistent Project kind instead of ProjectProfile. Production source was not changed to fix either failure.
2. c645ce3 second attempt: overall PASS / exit 0, raw `mechanism-tests-second.raw.txt`.
   - PersistentActualControlHostClosedQualification: real independently started release_host PID 82224 and actual control PID 7864, creation 1790798797737591100, exact image SHA256 1f4b104b810d6929761df3da69f7b4523d555084cc63807a586346a7a5007f67. A competing root lease was refused. A private seal for an unregistered candidate was rejected with NOT_FOUND and stable identity retained. Normal private stop reached clean process exit, STOPPED journal and released root lease. Reopening that journal with a fresh driver cannot manufacture the inherited stop capability or replay an effect. This last check is journal/driver restart fencing, not a second live host takeover.
   - ReleaseCutoverEncryptedSnapshotMechanism: this is an isolated database mechanism test using the existing calculator's legitimately generated fixture proof, never an actual-control admission. The encrypted cutover manifest af9ddd3e2af207c0097639910188b626c54808527abb773746286c5ced26c35e differs from pre-intent backup 82d095afde021ba3c74cb04be712bdb2edc96066b4a92895724d87a8de33538c. Post-seal ProjectProfile 88e9e7072475d2589ecf2245f486cea1 survived with identical body hash. DISPATCHED survived restoration, all auth credentials were revoked, protected references resolved without host-side payload copies, and the original failed DB bytes were unchanged. A revoked verifier could not dispatch; repeated dispatch and cutover calls failed; closed lease recovery was rejected. This tests direct private-domain calls, not the complete actual-control QUIESCED-to-restore path.

The early `../same-authority-wip/compile-first.raw.txt` was a zero-test compiler check of intermediate uncommitted source. It is retained as diagnostic output only and supplies no behavioral acceptance.

## Remaining gates

The three requested integrated release acceptance items are not yet satisfied: Owner intent to different-hash actual-control switch/project/task continuity; full actual-control encrypted rollback; actual live-host restart and lost-ACK reconciliation across that release. Their independent components are present, but full flow remains blocked on legitimate exact-control behavior proof. No calculator/marker proof was relabeled, and no gain was fabricated. The independent proof-profile owner will supply exact build/profile/generation validation; releaseAdmissionInputs must call that helper during serial integration before qualification can open.

Migrations 0001..0020, contracts and command/lock registrations were not edited. No old protected process/service/DB, stopped S2 work, exhausted I2 SOURCE probe, SCM or LIVE operation was touched. No full matrix was rerun. Source, failed raw and passing raw remain separately attributable.
