# R2 two-P1 correction: readiness receipt fence and explicit actual qualification closure

Source: 20958cbd6d35c11c2d8822518a398f7d5e0d1c11.
Historical source c645ce3 and evidence 818659a remain unchanged; their passing mechanism tests did not cover the two independently found P1 defects.
Owner/lease: codex:/root/control_drain / R2-independent-supervisor-v1.
Independent acceptance: PENDING.

## Shared-boundary corrections

SwitchFixture and RollbackFixture persist the newly started PID/creation/image in existing RECOVERING before readiness. Only successful readiness permits CANARY or ROLLED_BACK. Readiness failure therefore retains the actual started identity behind the existing no-replay fence; the operation cannot call Start again through switch/reconcile.

Both WriteFixtureReceipt and readFixtureReceiptBytes require current driver readiness. This applies to new receipt creation, existing-file retries and ReadFixtureReceipt, rather than a flag supplied by the host execute caller. A driver without Ready is rejected. ControlFixtureDriver supplies exact inherited private-channel identity/readiness; the historical NativeFixtureDriver explicitly supplies its marker-fixture liveness readiness and does not claim actual-control readiness. The CANARY retry path in the host reaches this same shared receipt gate before FIXTURE_PROJECT.

The real control's authenticated private entry explicitly returns ACTUAL_CONTROL_BEHAVIOR_PROOF_UNAVAILABLE for all five FIXTURE_SEAL/CURRENT/DISPATCH/CUTOVER/PROJECT actions. No request/configuration flag can open it. Normal READY/QUIESCE/RESUME/COMMIT_EXIT is retained. The downstream qualified handler remains separate for future typed profile integration and includes a control startup/lease/listener availability check before projection. Isolated domain snapshot mechanisms remain separate and do not qualify actual control.

Caller trace reviewed: BootstrapFixture, SwitchFixture, RollbackFixture; persistent controlCommand execute; legacy RunEvolutionReleaseFixtureOnce; WriteFixtureReceipt new/existing branches; ReadFixtureReceipt and readFixtureReceiptBytes; ControlFixtureDriver.Ready and private control READY/PROJECT. Bootstrap already withheld durable STABLE until Ready, and retained a failed started identity in RECOVERING.

## Bounded evidence

Pinned Go with GOENV=off, GOTOOLCHAIN=local, GOFLAGS=-mod=readonly.

1. `go test ./ops/supervisor ./apps/control ./ops/supervisor/release_host -run '^(TestReleaseReadyFailureCannotProduceReceiptOrReplay|TestActualReleasePrivateActionsExplicitlyClosed|TestPersistentActualControlHostClosedQualification)$' -count=1 -v -p=1 -timeout=1m`: exit 0, three tests PASS, raw targeted-gates.raw.txt.
   - The deterministic state-machine counterexample keeps a simulated process alive while readiness rejects. It asserts RECOVERING with retained identity, one Start only, no usable receipt, and no replay through switch/reconcile. It also constructs the historical CANARY shape, proves new and already persisted receipts require fresh readiness, and checks the allowed readiness case can still write a receipt. The prior implementation would fail the RECOVERING assertion and historical-CANARY receipt assertions. This is a deterministic model test, not a native private-READY failure injection.
   - All five commands traverse a real authenticated named pipe and return the explicit unavailable error before any domain DB call. The test uses the same process as the peer; it does not claim cross-account protection.
   - A separate actual release_host PID 27112 launched actual control PID 86388 (creation 1790799234349346300, image 894af9ad4e71a5d487acac88e595e316808854bab754809032bd9b6a84d2ee77). Seal returned the exact unavailable error, stable identity survived, a second writer was refused, and normal drain/exit released the lease.
2. `go test ./ops/supervisor -run '^TestActualControlDrain$/^idle_same_root_switch_preserves_data$' -count=1 -v -timeout=1m`: exit 0, exact normal-path subcase PASS, raw normal-private-ready-receipt.raw.txt. This preexisting process-mechanics fixture uses a synthetic admission and the same control image twice, with no actual business qualification. Old PID 54332 and new PID 15972 are distinct; Project b6e0519656ad372f24a9f8c87452fd75 revision 1 and profile hash 2606188aa9e044204300b05f11216af818398ee3486bd346158afd6b3ad56a0d survived actual HTTP GET. Added assertions call both WriteFixtureReceipt and ReadFixtureReceipt through actual private readiness on the successful path.

No full suite/matrix, stopped S2 scenario or exhausted SOURCE probe was rerun. Both exact commands passed on their first run at this source. Historical c645/f051 failed runs and all previous raw files remain intact.

## Still closed or unverified

ACTUAL_CONTROL_BEHAVIOR_PROOF=UNAVAILABLE. No different-build actual-control promotion/gain, full actual-control rollback, native readiness-failure injection, live-host takeover, complete lost-ACK chain, SCM/LIVE or formal acceptance is claimed. The new control-only profile is being built independently; root must serially replace the explicit closure with its typed exact build/current authority-generation checks.

Future rollback acceptance must account for the cutover snapshot containing DISPATCHED while the candidate is EVALUATING. Legal rollback projection must derive from durable host journal/receipt rather than pretending the restored DB was already CANARY. Revoked credentials and restore reconciliation fences must remain, while current actor/proof/generation authorization is re-established. This requirement is recorded only; this bounded P1 correction does not implement or test the full rollback projection.
