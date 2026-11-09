# W16 bounded system evolution

This package implements W16-G02 development behavior. `test.evolution` must pass
exactly one W16-G02 check or C09/C10/C12/C20/A16 case selector. The Go executable is
built from `ops/canary/fixture/main.go`; its bytes are sealed before execution.

The four SystemCandidate HTTP operations use existing author, executor,
independent verifier, and separate fixture release identities. Host registration
is local setup and has no HTTP route. Preregistered W10 experiments, frozen
Task/Run inputs, actual runtime output, and normal independent acceptance are
required before a fixture canary. A caller-written report or self score has no
release authority. The candidate receives an AppContainer token, no capabilities,
a one-process Job Object, bounded time and memory, and no write access to the host
suite, labels, permissions, or stable binary.

The fixture host persists one phase reservation and append-only journal. Its W12
effect fence and zero-USD reservation precede the local canary switch. It creates
a W18 authenticated backup, runs the actual candidate, restores to a new isolated
directory, verifies the restored inventory, runs the exact old binary for health,
returns the fixture slot to stable, and freezes the candidate. Startup failure,
timeout and a required regression exercise this path. An unrelated normal Task
can still be accepted afterward. A reserved phase cannot acquire another run.

The rule research path is a separate ChangeProposal retaining old suite/output
references; it does not modify the current host rule or authorize its own adoption.
Future rule activation requires a separately reviewed host release.

## Explicit limits

- Scope is `W16_G02_FIXTURE_ONLY`. Public deterministic math cases are not a formal
  holdout, real research benefit, or model qualification.
- W18 restoration is a real temporary SQLite copy and inventory check. It does
  not switch a production datastore or upgrade a running product instance.
- The fixture coordinator is in the development test host. An independent
  installed OS release service and production scheduler remain unqualified.
- A16 is PARTIAL even when all fixture assertions pass. W16-G03 remains blocked
  by W14 LIVE and independent supervisor/canary qualification; W16-G01 readiness
  is not established by this implementation.
- Host crash/restart recovery is not implemented or tested here. Durable RESERVED
  execution and effect records prevent blind redispatch; interruption after a
  slot switch requires an explicit future reconciliation path. No test claims
  that a host process was killed and safely restarted.
- No migration or backup touches existing user `.local/data`. Migration 0015 is
  additive and only exercised against new temporary fixtures. LIVE promotion is
  explicitly rejected.

Raw receipts retain process identity, SID, token capabilities, input/build/output
hashes, frozen policy and suite, native raw output, W18 restore inventory, normal
acceptance, rejection evidence and version manifest. These are executor evidence;
repository-level acceptance remains an independent review.
