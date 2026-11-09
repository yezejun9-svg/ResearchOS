# W05-02 work plan - written from the tree, before any code

Card: 完成CLI读改文件、diff、测试和真实中断 (parent W05, dependency W05-01 ACCEPTED). Selected by
`task_packet.py next --state execution/v2.4/step_state.json`, which reports `state_source:
VALIDATED_FILE`. Nothing in this file is accepted, implemented or asserted; it records what was
measured so the next window builds instead of rediscovering. The HEAD this was written against is
recorded in the checkpoint `work_in_progress` row, whose `plan_sha256` pins this file.

## Write scope, resolved through execution/v2.4/path_ownership.json aliases

`CLI/**` maps to `apps/cli` (owner `qoder-desktop:/root/cli_owner`) and `ADAPTERS/**` maps to
`adapters`, so the card's five entries resolve to: `apps/cli/**`, `adapters/runtime/**`,
`adapters/workspace/**`, `tests/runtime/**`, `execution/v2.4/receipts/W05/W05-02/**`.

Two scope facts that corrected an assumption I had stated earlier, and are worth writing down:

1. `adapters/workspace/` does not exist yet. It is in scope, so creating it here is legitimate - but
   the card's step 3 requires the tool write and `workspace.write` to go through the *same* handler,
   which means the first job is to find or extend the existing path rather than invent a parallel one.
2. No slice card in the whole plan lists `execution/v2.4/commands.json` in its write scope; only
   W02-02 does, and W02-02 is ACCEPTED. The convention every accepted card actually used is a
   selector flip carried out under the before-baseline, parity-re-resolution and computed-erratum
   discipline. `test.runtime` is BOUND with `check_id: [W05-G01, W05-G02, W05-01]`, so `W05-02` has
   to be added there before the card's own binding line can route at all. Doing that flip without a
   before-baseline and an erratum refresh is precisely what W13-01 was rejected twice over.

## Ownership of these semantics is already on the record, not my inference

`receipts/W01/W01-02/independent_review.json` line 41 grepped every step card and concluded that only
W01-02, W03-02, W05-02, W05-03, W06-01 and W06-02 touch epoch / CAS / unique-writer / queue / cancel,
and assigns this card "W05-02 步骤3/4（工具写与 workspace.write 走同一授权/hash/CAS 处理器；cancel 执行
clear_queue→abort→settled→子进程确认；忙时 steer/follow_up 队列语义）" together with the negative
"父进程退出但子进程仍写". That same review rules W01-02's Node simulator a qualification stub, so
W05-02 is where the real implementation has to land.

## Ground truth for the write path, read rather than guessed

- Contract: `internal/api/contracts/client.protocol.schema.json` defines `WorkspaceWritePayload` as
  `workspace_ref`, `relative_path`, `task_id`, `expected_content_hash` (matching
  `^sha256:[a-f0-9]{64}$`, or null), `text` (max 1048576) and `create_if_missing`, with all six
  required; `WorkspaceWriteResult` is `workspace_ref`, `relative_path`, `task_id`, `before_hash`
  (sha256-or-null), `after_hash` (sha256), `draft_artifact_ref` and `snapshot`, with
  `additionalProperties: false`. `CONTENT_CONFLICT` is an enumerated failure at lines 1048, 4643,
  4734, 6013 and 6030.
- The payload is already parsed in Go at `internal/domain/client_protocol.go:217` and :246-255, which
  enforces the hash shape - so the domain layer knows this method exists today.
- Authorization exists as a port, not as a stub: `adapters/local_workspace/authority.go` implements
  `domain.WorkspaceAuthority` over `internal/host`, redeeming single-use selection refs
  (`ConsumeSelection`, which refuses an empty principal with `FORBIDDEN`) and re-confirming that a
  bound root is still the same pinned object on the same volume (`ConfirmPath`). Its package header
  states plainly that it mints no authorization. A write handler must consume that authority instead
  of re-implementing path checks.
- Process control for the interrupt half is partly real already: `adapters/runtime/process_windows.go`
  creates a Job Object with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, and
  `adapters/runtime/bridge_windows.go` carries the cancellation and journal state machine
  (`cancel context.CancelFunc` at :78, the settled/acknowledged gates at :405 and :586).
  `apps/cli` is 86 lines in total, so the CLI side is essentially unbuilt.

## Increments, ordered by what can actually be verified

1. Read `apps/cli/main.go`, the write-side of `internal/domain/client_protocol.go` and the host ports
   in full; decide the single handler location from what exists, and record that decision here before
   writing code.
2. Implement the authorized CAS write shared by `workspace.write` and the CLI tool write: refuse a
   stale hash with `CONTENT_CONFLICT`, honour `create_if_missing` (null `before_hash` only when
   creating), never write outside the confirmed root, and return the real before/after sha256. Prove
   it with the locked `go` from `execution/toolchains/locked.json` - never PATH - including a negative
   where a stale hash cannot overwrite.
3. Real diff and check display in the CLI: a genuine unified diff of what changed, a real check
   command with its captured exit code, and one failing check driving a bounded repair - bounded
   meaning a counter in the record, not an open loop.
4. Interrupt cascade: Ctrl+C and cancel must run clear_queue -> abort -> settled -> child-process
   confirmation, with the Job Object proving no surviving child writes after the parent exits, and
   busy steer/follow_up getting real queue semantics. Each of the card's three negatives - plan
   written without the file write, parent exited while the child still writes, Goal restarting after
   cancel - needs an assertion that fails for exactly that reason.
5. Only then flip the `W05-02` selector with a before-baseline, re-measure parity at the new HEAD,
   refresh the computed errata for the other accepted receipts that pin `commands.json`, write the
   receipt, and request review from a fresh identity.

## Resource preconditions, recorded honestly

The card lists `authorized_product_model_backend` and Windows. Windows is satisfied. A real model
backend is not: `checkpoint.blocked_resources` still carries the absent pinned codex build for W05-01
LIVE re-qualification and `provider_live_inference_for_W01-02_model_steps`. Increments 1-4 are
DEVELOPMENT and FIXTURE mode against a scripted provider and must be labelled that way in the
receipt; the LIVE label and the formal cases A04 and C11 stay unclaimed. That blocks only the LIVE
portion, not the card.
