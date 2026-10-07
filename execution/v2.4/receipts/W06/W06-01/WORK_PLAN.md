# W06-01 plan (复用并补足独立接受服务) - measured at HEAD 41c4777a

Claimed, not started: no line of W06-01 code exists yet and nothing here is accepted. Every number was
read from the tree at write time.

## Where the loop is

- 19 of 71 cards ACCEPTED: W00-01, W00-02, W00-03, W00-99, W01-01, W01-02, W01-03, W02-01, W02-02, W02-03, W03-01, W03-02, W17-01, W04-01, W04-02, W12-01, W05-01, W13-01, W05-02
- parent -99 gates accepted: W00-99. Formal cases accepted: 0. checkpoint revision is read by the claim
  written alongside this file.
- registry: 18 command keys, 8 of them not BOUND (fork.install_deps, fork.build_worker, fork.worker_launch_rpc, fork.worker_stop, cli.entry_run, desktop.shell_launch, desktop.installer_build, protocol.v2_roundtrip).

## What the card asked for and what is actually there

Binding line: `python execution/command_dispatcher/dispatch.py test.orchestration --task-id W06
--check-id W06-01`. **`test.orchestration` is not a key in the registry at all** - the dispatcher
answered NOT_IMPLEMENTED with 0 assertions, invocation `3b275b35-610b-464c-8599-711edd408614`, at this
HEAD. So W06-01 is not a selector flip on an existing key like W05-02 was: it needs a new key, a real
handler behind it, and the same before-baseline / parity / computed-erratum discipline that
`commands.json` edits require because five accepted receipts hash that shared file.

Reuse targets that already exist, with lines read just now: `internal/domain/acceptance.go` (505 lines), `internal/domain/acceptance_goal.go` (294 lines), `internal/domain/acceptance_goal_test.go` (64 lines), `internal/domain/acceptance_test.go` (195 lines), `internal/domain/orchestration.go` (473 lines), `internal/domain/orchestration_agent_test.go` (238 lines). Under `tests/orchestration` there is
`verify_runner.py` (34 lines), `expected.json` and a README. The card's own wording is 复用并补足 -
so the first job is to establish what that runner already proves and which of the card's negatives it
refuses today, before anything is added.

## The increments, in the order they can be verified

1. Read `verify_runner.py` and `expected.json` end to end; list the assertion ids it can emit and which
   of the card's three deliverable negatives each one covers. If it emits no ids, say so and register
   the key against a handler that does.
2. Add `test.orchestration` to `commands.json` as a new BOUND key with narrowed selectors
   (task_id W06, check_id W06-01) - exact-key resolution means no cross-key shadowing - under the
   discipline already used: capture the before-baseline refusal above, re-resolve parity after the
   flip, refresh computed errata for every accepted receipt pinning commands.json, and record registry
   revision movement read from the file rather than written by hand.
3. Implement what the card's step 2 names in `internal/domain/acceptance*.go` /
   `orchestration*.go`: the final acceptance transaction re-checks task ownership, revision/epoch,
   permission, open conflicts and side effects, and use qualification; ACCEPTED, the successor
   release and the outbox row must land in one transaction.
4. Negatives with named assertions, each failing for its own stated reason: an executor self-approving;
   stale input; one hard gate missing; a high score over a failing check; state changing during
   reconciliation; and the card's own three - renaming a model, parsing to `met`, a last command
   exiting 0 - none of which may mask a required failure.

## Resource and scope notes

The card lists 本地开发资源 with no `resource_requirements`, so nothing here is resource-blocked; the
write scope covers `internal/domain/orchestration*.go`, `internal/domain/acceptance*.go`,
`tests/orchestration/**` and this receipt directory, so unlike W05-02 the acceptance transaction work
is inside the card's own scope. Formal cases for this card are A03, C07 and C10 and stay unclaimed until
the parent gate.
