# W05-02 · independent review request, round 1

Requested of a fresh identity that has ruled on no card in this repository, holds no lease on
`apps/cli`, `adapters/runtime` or `tests/runtime`, and authored no line of the code or record under
review. Write exactly one file: `execution/v2.4/receipts/W05/W05-02/independent_review_round1.json`.
Edit nothing else, mutate nothing without restoring it, and do not repair anything - reviewing is not
repairing.

- card: W05-02 · 完成CLI读改文件、diff、测试和真实中断 (parent W05, dependency W05-01 ACCEPTED)
- receipt: `execution/v2.4/receipts/W05/W05-02/receipt.json`, status `EXECUTION_REPORTED`,
  `verifier_id` and `independent_reviews` are empty by construction
- reportable face: 33 routed `W0502-*` assertions, 20 hashed artifacts, `blocking_issues` empty,
  mode `DEVELOPMENT_FIXTURE`, 6 stated limitations
- the loop's own auditor is in the directory (`audit_receipt_w0502.py`, 8 probes, currently PASS) and
  is itself a hashed artifact, so attacking it is in scope for you

## What is claimed, and the command that must show it

The routed surface:

```
python execution/command_dispatcher/dispatch.py test.runtime --task-id W05 --check-id W05-02
```

must report PASS with 33 assertion ids. Note that selectors reach the child as
`RESEARCHOS_TASK_ID` / `RESEARCHOS_CHECK_ID` environment variables (`dispatch.py:141`), not as argv
flags - a probe through argv proves nothing about routing, and this card already filed one wrong
conclusion that way before retracting it (`CHECK_ID_ROUTING_MEASURED.md`).

Claims worth attacking directly:

1. the diff is a real patch, not decoration: `apps/cli/coding_task_test.go` applies the program's own
   unified diff with the *locked* git and requires the file to become the candidate byte-for-byte
   (`TestUnifiedDiffAppliesWithRealGit`);
2. refused writes leave bytes alone: every mutation goes through one `AuthoritativeWriter` whose only
   production implementation refuses; there is no `os.WriteFile` anywhere in the engine - grep it, then
   try to make the engine write by some other path;
3. the cancel cascade order is enforced by the adapter, not by caller discipline:
   `Cancel` before `ClearQueue` must return `CANCEL_ORDER_VIOLATED`, and `Admit` after `ClearQueue`
   must be refused (`adapters/runtime/cancel_windows.go`);
4. no orphan can write after the parent dies: `W0502-NO-ORPHAN-WRITE-AFTER-THE-PARENT-DIES` is paired
   with a positive control row showing the worker was writing first - an absence without that control
   is worthless, so check both;
5. the matrix: 10 applied mutants, 9 killed, each naming the rows it took down
   (`mutation_selfcheck_w0502.json`).

## What is explicitly NOT claimed

- card step 3 is not met. `workspace.write` is declared in `methodsV2` (line 38), is write-class in
  `writeMethods` (line 44) and payload-validated at line 212 of
  `internal/domain/client_protocol.go`, but `handleWrite` (938) routes only `session.attach` and
  `session.control` and its `default:` (1051) answers "handler belongs to a later card" (1053).
  Routing it is an edit in `internal/domain`, outside this card's write scope, filed as obligation
  `W05-02-domain-write-route`. No file in this repository is written by the CLI.
- card deliverable 2 is met two of three. The third negative - a Goal restarting after cancel - needs
  session and goal semantics outside this write scope and has no row.
- one mutant survives and says why: `Q3-failing-check-reported-as-passing` cannot be discriminated by
  any routed row, because the CLI refuses the write before a failing check could drive a repair.
  Judge whether that reason holds, and whether it should be blocking.
- mode is `DEVELOPMENT_FIXTURE`: no model backend is installed on this host (see
  `checkpoint.blocked_resources`), so proposals come from a caller-supplied deterministic replacement;
  formal cases A04 and C11 and any LIVE claim stay unclaimed.
- nothing here accepts parent W05.

## Controls to protect while you measure

`test.runtime` is BOUND at registry revision 16 and five other accepted receipts hash
`execution/v2.4/commands.json`; six computed errata for the W05-02 selector addition sit beside those
cards (`pin_drift_erratum_registry_rev16.json`). Re-running the accepted `--check-id W05-01` selector
is a good regression check: it must still report the identical 32 ids. Restore byte-for-byte anything
you mutate, and resolve tools from `execution/toolchains/locked.json` (path plus sha256 plus version
output) rather than from PATH. Do not run two heavy Go suites at once. Report any digest you cannot
reproduce, and record the digest of the receipt you reviewed plus the tree you measured it at.
