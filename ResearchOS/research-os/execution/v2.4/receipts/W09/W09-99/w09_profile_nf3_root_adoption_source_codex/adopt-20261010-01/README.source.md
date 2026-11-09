# W09 Q adoption and NF3 Root registrar — Source only

This package supplies the missing future Root mechanism. It does not adopt Q,
register a Scope, call the shared TP, write Main/Canon, launch NF3 or issue any
formal acceptance. Existing Q/QR/NF3/NF3R Sources and their completed checks are
reused unchanged. The 68 new checks cover only this mechanism's pure rules and
AST structure. Synthetic prospective scopes and Canon transforms stay in memory;
they are never saved as authority documents.

The exact API, field sets, future CLI and causality requirements are in
`root-calling-contract.source.json`. `input-pins.json` binds the existing accepted
Sources, four real peer captures, Main23 context and shared TP. Its `baseline`
and `baseline_pending` are Source test inputs only. Future requests must provide
the actual current four files and a freshly sealed contiguous pending suffix;
the runtime does not assume CP373, OW177, start1067 or next1089.

## Future Root sequence

1. Obtain non-author review of this package. Capture its actual author HDF
   delivery and reviewer decision delivery using the existing NF3 actual-audit
   schema. Root cannot supply a self-granted Source review.
2. Create the fixed public Root output parent, then a `PROFILE_ADOPTION` request
   at a Root-owned W09 path. Its unique case directory must still be absent.
   Complete a real Root tool call that exposes the request's exact hash. Capture
   that completed call/return; pass the request ref and audit ref to `propose`.
3. `propose` prepares full raw CP/OW/SS/CM archives, a bounded Q adoption Scope,
   exact owner/worker, a fully invertible CP/OW proposal, and two proposed Main
   byte streams. `check` is followed by `activate`. Only `activate` calls the
   unchanged accepted `canonical_transactions.update_pair` under mandatory
   exclusive CP/OW ownership.
4. `apply-profile` requires that exact registered Current4. It holds CP/OW/SS,
   formal index and immutable Sources while separately opening precisely Main
   `formal_profile_w09.py` and `commands.json` together with CreateFileW
   shareMode=0. The exact before/after bytes and durable intent precede all target
   writes. Q profile bytes are copied exactly; CM40 is the reviewed proposal with
   only the real Root request issuance timestamp substituted. Full index bytes
   stay unchanged. Partial failures retain actual partial files and primary plus
   secondary diagnostics, with no automatic inverse or retry.
5. Capture the actual successful profile commit return. Build a new
   `NATIVE_SCOPES` request from the now-current four files, current pending suffix
   and three distinct finite leases. `propose/check/activate` register the exact
   three NF3 Scopes, owners and workers. Their exact fields, UUID paths, tests and
   budgets come from the accepted NF3 choice and contract. The newly completed Q
   owner/worker alone is marked adopted; earlier unrelated work is preserved.
6. After native `activate` actually returns, capture its real Root tool pair for
   each Scope hash. Each capture must also show the completed activation receipt
   hash and `ROOT_SCOPE_REGISTERED`. `finalize-native-requests` can then create
   the Current4 vector and the three exact NF3 requests, and invokes only NF3's
   authority validator. It prints the existing prepare/run argv for Root.
7. Root later calls the unchanged NF3 `prepare_full_w09.source.py`, then
   `run_full_w09.source.py`, one selector at a time. Keep the same request/vector
   between prepare and run. These branches are not invoked by this package.

The supported selector keys are `W09-G01`, `W09-G02`, `A06`. The reviewed
one-shot receipt/scratch/output paths must remain absent until the authorized
first preparation. A stage intent or partial journal blocks automatic retry.
Root must reconcile an observed failure explicitly.

Original diagnostic rows append once, identified by original hash plus selector.
The suffix must be contiguous from the current Canon next ordinal. Empty suffixes
may leave that ordinal unchanged, never lower or advance it. Booleans are rejected
as ordinals, byte counts or exit integers. Unknown process exit domains remain
null. Every prior counter row, old D/11 evidence, existing receipt and untouched
Canon field survives the complete inverse.

Main23 programme qualification is retained as context only; it grants no W09 or
old21 authority. No execution-role registry, dispatcher route lease, ModeProof,
programme qualification, full formal capture, parent acceptance or AcceptanceReceipt
is issued here. Those remain later independent gates.

## Validation boundary

`source-controls.result.json`: 68 passed, zero failed. No actual registrar stage,
TP transaction, exclusive Main write, Go, Native, SQL or model call occurred.
Existing Q/QR/NF3/NF3R tests were not rerun. Current Canon was read for the Source
baseline but never opened under a Source guard. Source guards hold only immutable
existing Sources and this namespace's private snapshots. A subsequent README/seal
patch-format tool failure is preserved separately; it launched no process and did
not change the checked runtime Source.
