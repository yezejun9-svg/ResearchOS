# Review request: W13-01, round 2

Reviewer identity (must not have ruled on this card or any other): `qoder-desktop:/root/w1301_verifier_r2`.
Write your verdict to `execution/v2.4/receipts/W13/W13-01/independent_review_round2.json` and to nothing else.
Vocabulary: ACCEPT / ACCEPT_WITH_LIMITATIONS / ACCEPT_WITH_RESERVATIONS / ACCEPT_BLOCKED_RECORDING / REJECT.
Registration happens only on an empty `blocking_issues` array, and every array you produce must be carried.
Timestamps must end with `Z`. Settle your bytes and write once — the registrar pins the digest.

## What round 1 blocked, and what to check now
Read `executor_response_round2.json` first: it states each of the three blockers, the change, and the number that
answers it. Round 1 came back REJECT from `qoder-desktop:/root/w1301_verifier_r1` (digest pinned in
`verdict_pin_round1.json`, sha256 prefix `303490fc`); the executor reproduced all three and they were real.

1. **Node identity (B1).** The check program used to run a bare `node`. It now resolves the pinned binary from
   `execution/toolchains/locked.json`, verifies absolute path + sha256 + version output, drives the driver with it,
   and asserts `W1301-TOOLCHAIN-NODE-FROM-LOCKED-TABLE` plus `W1301-TOOLCHAIN-NODE-PATH-FALLBACK-IS-REFUSED`.
   Verify rather than trust: read `resolve_node()` and confirm a bogus table yields no executable; confirm the
   report's `node_pinned_version` equals the locked table's `version_output` and that
   `node_pinned_binary_hash_verified` is true; and check the PATH version is still reported, because if PATH and the
   pinned binary were the same the identity row would be vacuous on that host.
2. **Disclosure reason (B2).** The installed-shell row used to claim `main.js` loads a single status view. Confirm
   the new reason matches the file, and that the property is still genuinely blocked by the resource
   `Windows_desktop_session` rather than newly asserted.
3. **Census digests (B3).** `c23_forwarded_flake_census.json` is now produced by a tracked script that hashes raw
   bytes. Recompute every `stdout_sha256`/`stderr_sha256` yourself from `execution/invocations/<id>/*.txt`; confirm
   the non-empty streams (19 rows) verify; then attack `audit_receipt_w1301.py` probe 9 — falsify one digest in a
   copy and confirm the auditor reports it, since a green self-audit that cannot fail is the finding, not the pass.

## Re-run
- `python execution/command_dispatcher/dispatch.py test.ui.routes --task-id W13 --check-id W13-01`
  — expect PASS **31** (the two toolchain rows are new; the frozen id set is in
  `binding_and_parity_rev15_at_head.json`, measured at the HEAD the receipt reports).
- `python execution/v2.4/receipts/W13/W13-01/mut_w1301.py` — 10 cases, all caught, `tree_clean_after_restore: true`.
- The three parity shapes: local W13-01 served; `--case-id C23` forwarded; bare selector refused with zero
  assertions. C23 drives a real Windows browser and is nondeterministic; the census classifies 22 runs, 6
  COMMAND_FAILED, four causes. Do not treat one PASS as proof of stability, and do not credit the mount with the
  old reds — that causal claim was measured away in round 1.
- Recompute all 14 artifact hashes and the registry entry for `test.ui.routes` (revision 15, owner_card W13-01).

## Open on the card, not fixed by this round
11 assertion rows have neither a mutant nor a stated reason; say so if you find the `no_mutant_rows` map still does
not cover them. Step 4 of the card (packaged install, Start menu, U01 gate) and the native directory dialog stay
blocked by `Windows_desktop_session`; `desktop.shell_launch` carries owner_card W13-01 while still UNBOUND; nothing
here accepts parent W13 or signs formal case C23 or A10.
