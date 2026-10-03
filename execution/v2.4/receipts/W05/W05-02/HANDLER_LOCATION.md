# Where W05-02's write path lives - measured, not assumed

Extracted from `internal/domain/client_protocol.go` at HEAD 13bb0c78. `ClientService.handleWrite` spans
lines 938-1060 and routes exactly these methods today: `session.attach`, `session.control`. Its explicit refusals on this build are: `NOT_IMPLEMENTED`: only CANCEL control is implemented on this host build; `NOT_IMPLEMENTED`: handler belongs to a later card; `NOT_IMPLEMENTED`: handler belongs to a later card.

## What that means for the card

1. The card's step 3 ("tool write and workspace.write go through the same authorization / hash / CAS
   handler") is about a **single existing handler in the domain service**, reached over the client
   protocol through the host. It is not an instruction to create a new file-writing package.
   `adapters/workspace/**` is in this card's write scope, but nothing measured here says it should be
   created, and inventing a parallel writer would fork the CAS semantics onto a second path - the
   exact failure the card's step 3 exists to prevent. The earlier work plan's increment 2, which
   proposed implementing the CAS write in `adapters/workspace`, is superseded by this file.
2. What is genuinely missing, and is this card's work: `workspace.write` does not appear among the
   routed methods, while the contract already defines its payload and result and
   `internal/domain/client_protocol.go:217` already validates the payload shape. So the increment is
   to route `workspace.write` through the same writer-epoch/CAS discipline that `session.attach` and
   `session.control` already use, consuming `domain.WorkspaceAuthority`
   (`adapters/local_workspace/authority.go`, which mints nothing) for the path checks.
3. The other half of the card is the CLI. `apps/cli/main.go` is still W02-03's thin launcher: it
   implements version, help and doctor, and prints NOT_IMPLEMENTED for `chat`, `run --output jsonl`,
   `cancel` and `/goal`. The diff display, the failing-check-driven bounded repair, and the
   clear_queue -> abort -> settled -> child-confirmation cascade all sit behind that, and the domain
   already implements CANCEL and writer handoff, so the CLI has a real control plane to drive rather
   than a stub to fake.

## Scope consequence, stated plainly

`internal/domain/**` is **not** in this card's write scope. If routing `workspace.write` needs a
domain change, then either the change belongs to the card that owns `internal/domain` (W03-02 took
that ownership for the writer-lease attribution) or W05-02 is blocked on it for that increment.
Recording this now so the next window does not discover it by attempting an out-of-scope edit.

## State of this card

Claimed in `checkpoint.work_in_progress` at revision 98; nothing built, no receipt, no acceptance.
`task_packet.py next --state execution/v2.4/step_state.json` still selects W05-02. The card's own
binding line needs the `W05-02` selector added to `test.runtime`, which per the work plan rides on the
before-baseline plus erratum convention rather than on a scope entitlement.
