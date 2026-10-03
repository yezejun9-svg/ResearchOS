# W05-01 resume note

State at 2026-10-03T06:54:16.674779+00:00 (checkpoint revision 46, HEAD ec7f0da2):

- The card reports EXECUTION_REPORTED at receipt HEAD 2c8e04cb: 28 assertions through the registry binding command, 14 matrix cases all caught by a named assertion, equivalence probe E1 filed outside the matrix, tree clean after restore.
- Self-audit CLEAN (20 probes); the three first-pass findings were auditor scope errors, each with its reproduction note in receipt_selfaudit.json.
- review_request_round1.json is derived from the frozen files and names the five claims to attack.

Next, in order:

1. Dispatch a reviewer identity that has never seen this card (suggested w0501_verifier_r1) with the brief above; it writes execution/v2.4/receipts/W05/W05-01/independent_review_round1.json and nothing else.
2. Wait until that file is byte-stable for 90 seconds before pinning it; a missing artifact is not a dead reviewer.
3. Register only on a verdict with blocking_issues empty: python execution/v2.4/receipts/W05/W05-01/register_w0501_accepted.py (it refuses to write without a verdict, and its dry run exits 1 with no writes).
4. Carry every reservation and follow-up item into open_obligations_before_next_card rather than editing the frozen receipt; hashed evidence is append-only.

Still owed outside this card: W06-01 needs a test.orchestration before-baseline for 12 selectors; W12-99 DAILY/MONTHLY windows; W07-01 source connection; the 42-case selector debt (8 cases with no selector, 3 CLI/Desktop commands UNBOUND); the W12-01 tooling nit list is NOT applied because all 33 W12-01 evidence files are hash-pinned, so any correction must arrive as a new file plus an integrity event.

Audit standing: 16 of 71 cards accepted, 0 of 22 parent tasks, 0 of 42 formal cases. Not complete.
