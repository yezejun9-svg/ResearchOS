# Where W05-02's write path lives - corrected and precise

Re-read from `internal/domain/client_protocol.go` at HEAD cb65513e. Line numbers are quoted because each was
located by searching the file at write time, not by memory.

## Measured state of `workspace.write` in the protocol service

- Declared as a legal v2 method in `methodsV2` (the `"workspace.write": true` entries sit at lines 38).
- Classified write-class in `var writeMethods` (table starts line 44), which is what forces a command
  envelope to carry full identity / CAS fields before the method is even dispatched.
- Its payload shape is enforced: `Envelope.validatePayload` has `case "workspace.write":` at line 212,
  binding workspace_ref, relative_path, task_id, expected_content_hash, text and create_if_missing.
- **No handler exists.** `ClientService.handleWrite` starts at line 938, and its method switch (line 950)
  has exactly two cases - `session.attach`, `session.control` - plus a `default:` at line 1051 whose NOT_IMPLEMENTED text reads "handler
  belongs to a later card" (line 1053). So a well-formed `workspace.write` command validates, is
  recognised as a write, and is then refused by the default branch.

This supersedes both earlier drafts of this file. The first draft said workspace.write "does not appear
among the routed methods", which is true of the handler switch but imprecise enough to hide the fact
that the method is otherwise fully wired; the word "routed" also briefly misled me, because the only
`case "workspace.write":` in the file is the payload validator at line 212, not a handler.

## What that means for the card

1. The insertion point is one `case "workspace.write":` inside `handleWrite`'s switch, sharing the
   writer-epoch/CAS discipline the two existing cases already use: they take `tx *sql.Tx`, reject with
   the enumerated codes (`WRITER_BUSY`, `VERSION_CONFLICT`, `NOT_FOUND`), journal under the new epoch,
   and `session.attach` refuses to invent a lease TTL (`HOST_LEASE_POLICY_MISSING`). The card's step 3
   requirement that tool write and `workspace.write` go through the *same* handler is satisfied only by
   extending this switch. Creating `adapters/workspace/**` as a second writer path - which is what this
   card's work plan originally proposed - would fork exactly the semantics step 3 exists to unify, so
   that increment is withdrawn.
2. The path/authority half already exists and mints nothing: `adapters/local_workspace/authority.go`
   implements `domain.WorkspaceAuthority` over `internal/host`, redeeming single-use selection refs and
   re-confirming the bound root is the same pinned object on the same volume. The handler must consume
   it, not re-implement path checks.
3. `internal/domain/**` is not in this card's write scope. The edit at point 1 is therefore a serial
   integration by the owner of the domain line, per the card's own recovery clause ("shared contracts /
   locks / migration numbers are integrated serially by the corresponding owner"), and it is recorded in
   `checkpoint.open_obligations_before_next_card` rather than performed quietly here. Until it lands,
   W05-02 can build the CLI half (diff display, failing-check-driven bounded repair, the
   clear_queue -> abort -> settled -> child-confirmation cascade against the Job Object in
   `adapters/runtime/process_windows.go`) and must report the write step as blocked, not as done.

## State

Claimed in `checkpoint.work_in_progress`; nothing built, no receipt, no acceptance, and `task_packet.py
next --state execution/v2.4/step_state.json` still selects W05-02. `apps/cli/main.go` remains W02-03's
thin launcher, printing NOT_IMPLEMENTED for chat, run, cancel and /goal.
