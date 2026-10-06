# What actually blocks the only actionable parent gate (W01-99)

The frontier computation (`execution/v2.4/parent_gate_frontier.json`) says 21 of 22 gate cards wait on unmet
dependencies and the chain runs through W01-99: W02-99 needs W01-99, W03-99 needs W02-99, W04-99 needs W03-99,
and W05/W06/W07/W08/W09-99 hang off those. So W01-99 is not one gate among twenty-two, it is the neck of the
whole endgame, and unblocking it is worth more than any further card work.

## The four things it needs

- **A02** - class `no_registered_selector`; registered selectors: NONE; owner cards: W01-01, W01-02, W01-03, W02-01, W01-99, W06-99 (statuses W01-01=ACCEPTED, W01-02=ACCEPTED, W01-03=ACCEPTED, W02-01=ACCEPTED, W01-99=BLOCKED, W06-99=not_started).
  frozen ids that no program in the tree names: A02-02, A02-03

- **C10** - class `no_registered_selector`; registered selectors: NONE; owner cards: W06-01, W16-01, W16-02, W01-99, W06-99, W16-99 (statuses W06-01=not_started, W16-01=not_started, W16-02=not_started, W01-99=BLOCKED, W06-99=not_started, W16-99=not_started).

- **C11** - class `selector_and_only_some_ids_named`; registered selectors: test.resources, test.runtime; owner cards: W05-02, W08-02, W12-01, W12-02, W18-01, W18-02, W19-01, W19-02, W01-99, W05-99, W12-99, W18-99, W19-99 (statuses W05-02=not_started, W08-02=not_started, W12-01=ACCEPTED, W12-02=not_started, W18-01=not_started, W18-02=not_started, W19-01=not_started, W19-02=not_started, W01-99=BLOCKED, W05-99=not_started, W12-99=not_started, W18-99=not_started, W19-99=not_started).
  frozen ids that no program in the tree names: C11-04

- **C04** - class `selector_and_every_id_named_by_a_program`; registered selectors: test.context; owner cards: W04-02, W06-02, W01-99, W03-99, W04-99 (statuses W04-02=ACCEPTED, W06-02=not_started, W01-99=BLOCKED, W03-99=not_started, W04-99=not_started).

## Consequence for the plan
- A02 and C10 have no selector at all, so they need a registry binding by an owner card that is already
  ACCEPTED (W01-01/02/03). Binding onto an existing key is a registry flip: a before-baseline over every
  selector of that key is mandatory, and accepted receipts that hash `commands.json` will drift - the
  response is a computed erratum, never an edit of a registered receipt.
- C11-04 has a selector (`test.resources`, `test.runtime`) but no program names the id, so the gap is an
  emitter, not a binding.
- The LIVE dual-end leg additionally needs the resource Windows_desktop_session, which no card can
  manufacture; that part stays BLOCKED and only that branch is held up.

## Order, once the W13-01 round-2 review lands (registry edits must not run beside it)
1. before-baseline for the key A02 would land on, then the binding, then re-resolve every selector of that key;
2. the same for C10;
3. an emitter for C11-04 inside the owning card's write scope, with a named assertion;
4. only then attempt W01-99: run its own cases, record FIXTURE/DEVELOPMENT/LIVE separately, and get an
   independent verifier to replay it. If the LIVE leg is still unauthorised, W01-99 stays BLOCKED with the
   reason re-measured rather than carried over.
