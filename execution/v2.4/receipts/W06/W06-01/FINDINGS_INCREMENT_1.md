# W06-01 increment 1 - what already exists, read rather than assumed (HEAD dc75bd52)

No code was written for this card yet; this file only records what is on disk, because the card says
复用并补足 and reuse cannot be judged without the inventory.

## The existing runner is not acceptance evidence, by its own admission

`tests/orchestration/verify_runner.py` (34 lines) opens with:

> """Adversarial runner-protocol checks, explicitly not domain acceptance evidence."""

It drives `ops/ci/orchestration.py` under `RESEARCHOS_CHECK_ID=W06-G02` and asserts on four forged
stdout shapes - zero assertions, a duplicated assertion, malformed JSON, and one missing entry - all
labelled `'fixture': 'runner protocol only'`. So it tests how the runner reacts to a dishonest
protocol, not whether a domain acceptance transaction commits. That is a real component of the card's
subject but not its deliverable, and the file already knows the difference.

## The gate inventory that does exist

`tests/orchestration/expected.json` names **18** assertion ids across **76** groups, including the hard
gates the card must not weaken: `A02-01-03-FROZEN-ROUTE`, `A02-04-RECOVERY-FENCE`, `A02-04-SINGLE-CLAIM`, `A03-01-CAP-ZERO`, `A03-01-FLOAT-MONEY`, `A03-01-HTTP-NO-WRITE`, `A03-01-NAIVE-TIME`, `A03-01-REVISION-ZERO`, `A03-01-ROUNDTRIP`, `A03-02-IDEMPOTENCY`, `A03-02-INVALID-STATE`, `A03-02-PROJECT-ISOLATION`, `A03-02-STALE-REVISION`, `A03-03-CONSUMER-PROJECTION`.

`ops/ci/orchestration.py` exists (124 lines) and defines none matched as its gate-shaped functions.

## What is missing is the door, not the room

- `test.orchestration` is not a key in `commands.json` at all: **10** keys are BOUND, **8** are not
  (`fork.install_deps`, `fork.build_worker`, `fork.worker_launch_rpc`, `fork.worker_stop`, `cli.entry_run`, `desktop.shell_launch`, `desktop.installer_build`, `protocol.v2_roundtrip`), and no key's argv mentions orchestration.
- Consequence measured at claim time: dispatching the card's own binding line answers
  NOT_IMPLEMENTED with 0 assertions (invocation `3b275b35-610b-464c-8599-711edd408614`).
- So increment 2 is to bind a key whose argv reaches a handler that emits real assertion ids for
  `check_id W06-01`, under the before-baseline / parity / computed-erratum discipline -
  `commands.json` is hashed by several accepted receipts, so the flip needs fresh errata, not a re-pin.
- The domain half the card asks for (acceptance transaction re-checking ownership, revision/epoch,
  permission, open conflicts, side effects and qualification; ACCEPTED + successor release + outbox in
  one transaction) lives in `internal/domain/acceptance*.go` / `orchestration*.go`, which *are* in this
  card's write scope - unlike W05-02's blocked step 3, nothing here waits on another card's file.

## What this does not establish

Whether each of those 76 ids is currently emitted green was not measured in this increment; the
counts above are inventory, not a claim that the acceptance chain works. A03, C07 and C11 stay
unclaimed and this card has no receipt.
