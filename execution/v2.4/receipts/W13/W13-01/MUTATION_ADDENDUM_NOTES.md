# W13-01 mutation addendum - what each uncovered row is now

The shipped matrix and its 14 pinned artifacts are unchanged; everything here is a new file.

- assertion ids emitted by the accepted check program: **31**
- rows the shipped matrix's 10 cases actually kill: **12**
- rows therefore without a discriminating mutant: **19**
- the shipped artifact's own `no_mutant_rows` field claims: **7**, and the round-3 reviewer reported **13**. Three different answers to one question, all inside registered files, so the computed set (emitted minus the union of killed ids) is used here and no frozen number is edited.

## Attribution rule

Only rows lost **while `W1301-DRIVER-RAN` survived** are credited to a mutant. Addendum mutant A5 took the driver down and therefore discriminates nothing on its own, even though seven ids vanished with it; those seven are listed as owed or measured elsewhere instead. Clean rows newly discriminated by this addendum: **0**.

## What was actually run here

- `A1-preload-drops-a-registered-channel` (-): **file-absent**
- `A2-ipc-drops-a-route` (apps/desktop/main/lib/ipc.js): **survived**
- `A3-ipc-drops-a-client` (apps/desktop/main/lib/ipc.js): **survived**
- `A4-workbench-tells-the-user-to-use-a-terminal` (-): **file-absent**
- `A5-host-refuses-unknown-clients-anyway` (apps/desktop/main/lib/host.js): **crashed** - vanished while the driver died: W1301-ABSENT-DISCOVERY-IS-NAMED, W1301-ABSENT-PRINCIPAL-STORE-IS-NAMED, W1301-DRIVER-RAN, W1301-EXISTING-PROJECT-SKIPS-EMPTY-STATE, W1301-PRINCIPAL-READ-LOCAL-NOT-PASTED, W1301-UNKNOWN-CLIENT-AND-METHOD-REFUSED, W1301-UNREACHABLE-CORE-IS-REPORTED-NOT-FAKED
- `A6-provider-catch-all-branch-returns-success` (apps/desktop/main/lib/host.js): **survived**

Four of the six planned file mutants reported `anchor-missing`: the line each one wanted to break is not where the addendum searched, so no mutant was applied rather than a different edit being substituted and renamed a kill.

## Per-row disposition

| row | disposition |
| --- | --- |
| `W1301-ABSENT-DISCOVERY-IS-NAMED` | killed by staged mutant M27 (reviewer measurement); shipping it into the accepted matrix is owed as a new artifact |
| `W1301-ABSENT-PRINCIPAL-STORE-IS-NAMED` | killed by staged mutant M28 (reviewer measurement) |
| `W1301-AUTH-RATELIMIT-UNSUPPORTED-ARE-FAILURES` | partly covered: the reviewer's one-line branch mutants killed the AUTH_REQUIRED, RATE_LIMITED and UNSUPPORTED branches; the catch-all branch survives, reproduced again here as A6 |
| `W1301-DRIVER-RAN` | meta row, not a source behaviour: its negation is 'node declined to launch', measured by forcing resolve_node to return no binary, which produced FAIL with 26 named failures rather than a silent pass (reviewer round 3, what_i_ran item 10) |
| `W1301-EXISTING-PROJECT-SKIPS-EMPTY-STATE` | OWED: addendum anchors for this behaviour did not exist in the files searched (A1-A4 reported anchor-missing), so no mutant was applied |
| `W1301-FIRST-RUN-METHODS-ALL-ROUTED` | OWED: mutant A2 anchor-missing in ipc.js as searched |
| `W1301-FOUR-NATIVE-CLIENTS-ROUTED` | OWED: mutant A3 anchor-missing in ipc.js as searched |
| `W1301-LAUNCH-USES-THE-LOCAL-CONTROL-HOST` | killed by staged mutant M29 in .local/prepare_w1301_mutants_round3.py as measured by the round-3 reviewer; not folded into the shipped matrix because mutation_selfcheck_w1301.json is pinned by an accepted receipt |
| `W1301-PRELOAD-MATCHES-REGISTERED-CHANNELS` | OWED: mutant A1 could not be applied because the expected channel line is not in preload.js as searched |
| `W1301-PRINCIPAL-READ-LOCAL-NOT-PASTED` | killed by staged mutant M28 (reviewer measurement) |
| `W1301-PROVIDER-OK-IS-SUCCESS` | OWED: this is the card's own second negative and the catch-all branch is undiscriminated - mutant A6 (provider catch-all returning ok:true) SURVIVED again in this addendum |
| `W1301-ROUTING-TRUTH-TABLE` | OWED: the table is asserted as data inside the check program, and no mutant yet rewrites the routing it tabulates |
| `W1301-TOOLCHAIN-NODE-FROM-LOCKED-TABLE` | covered by measurement rather than a filed mutant: nine hostile tool tables were passed to resolve_node and only the good one returned an executable (reviewer round 3, what_i_ran item 9); folding that as a mutant into the pinned matrix is owed |
| `W1301-TOOLCHAIN-NODE-PATH-FALLBACK-IS-REFUSED` | OWED, and weakly discriminating by design: the row tests a hard-coded bogus table, so it would still pass if a PATH fallback were reintroduced at the subprocess call (reviewer round 3, reservation 7) |
| `W1301-TRANSPORT-AND-SILENCE-ARE-FAILURES` | covered by the reviewer's NO_REPLY and TRANSPORT branch mutants; not folded into the pinned matrix |
| `W1301-UNKNOWN-CLIENT-AND-METHOD-REFUSED` | attempted by addendum mutant A5, which crashed the driver instead of isolating the row; a narrower mutant is still owed |
| `W1301-UNREACHABLE-CORE-IS-REPORTED-NOT-FAKED` | OWED, same reason: only reached through the crashed run, which credits nothing |
| `W1301-WORKBENCH-COVERS-FOUR-CLIENTS` | OWED: mutant A4 anchor-missing in workbench.html as searched |
| `W1301-WORKBENCH-TELLS-NOBODY-TO-USE-A-TERMINAL` | OWED: mutant A4 anchor-missing in workbench.html as searched |

## Counts

- killed, covered by a reviewer measurement, or otherwise accounted for: **9**
- OWED (a real gap, not a formatting problem): **10**
- unclassified: **0**

The single most important owed item is `W1301-PROVIDER-OK-IS-SUCCESS`: mutant A6 (the provider catch-all branch answering `ok:true` for an unlisted status) survived again here, which is the same survival the round-3 reviewer reproduced. It is the card's own second negative - a provider failure must never be shown as success - and the suite would not notice that regression.

Reproduce: `python execution/v2.4/receipts/W13/W13-01/mut_addendum_w1301.py`

Generated 2026-10-03T16:50:05.601930+00:00 at HEAD 0ca44443; every mutated file was restored byte-identically and `git status` over apps and tests is clean.

## Passes 2, 3 and 4 - what the extra attempts established

Pass 1's four anchor-missing results were my wrong paths, and the fix was to read the card's own
artifact list: the files are `apps/desktop/preload/preload.js` and `apps/desktop/main/workbench.html`.

Pass 2 mutated `ipc.js` routes and a `provider` token in the workbench markup. All three applied
cleanly and **survived**. That was a targeting error, not a hole: `tests/ui/check/main.py` builds
`clients` from `host.CLIENTS` and `route_shape` from `host.ROUTES` (main.py:90-91) and requires
`ipc.js` only at line 146 for a different row.

Pass 3 crashed before measuring: the ROUTES map turned out to be `const CLIENTS =
Object.keys(ROUTES).sort()`, so clients are derived, and my token anchors sat on lines that do not
contain them.

Pass 4 aimed correctly: it deleted the `status` entry, then the `workspace` entry, from
`host.ROUTES`. Both runs **failed** - the suite does notice a client vanishing - but the driver died
with them, so under the rule used throughout this addendum (only rows lost while
`W1301-DRIVER-RAN` survives may be credited to a mutant) they credit no individual row. Recorded as
`crashed`, not renamed as a kill.

Net effect on the disposition table: no row moved out of OWED in passes 2-4. What did improve is the
quality of the statement: for the structural routing rows it is now known that the suite detects their
negation loudly at whole-run level, that the discriminating file is `host.js` rather than `ipc.js`, and
that turning that into per-row credit needs a mutant which removes a route without breaking the
driver's require chain - still owed.

Regenerated 2026-10-03T16:54:39.663726+00:00 at HEAD 78a902ae; every mutated file restored byte-identically and `git status` over apps and
tests is clean.

## Pass 5 - the aimed mutant finally landed, and so did an uncomfortable result

`E2` removed one method (`models: ['GET', '/provider/models']`) from `host.ROUTES.provider`. The run
failed with **the driver still alive** and exactly one row missing:
`W1301-FIRST-RUN-METHODS-ALL-ROUTED`. That row therefore moves from OWED to killed by a filed mutant -
the first clean kill this addendum produced, and the proof that the pass-2-to-4 problem was aiming,
not the suite.

`E3` is the other half of the story: it **added** a route that exists in the table and nowhere else
(`provider.bogus -> GET /bogus`) and the run stayed PASS with the driver alive. Nothing notices an
entry that is declared but wired to no channel. `W1301-ROUTING-TRUTH-TABLE` stays OWED, and its
disposition now says what was demonstrated rather than what is merely missing.

`E1` (removing `pick_directory`) reported anchor count 0 because the needle text differed in
whitespace. It was left unfixed rather than retargeted by guesswork, since E2 already establishes the
mechanism on the same map.

Counts after pass 5: **10** rows accounted for by a filed or reviewer-measured mutant, **9** OWED,
0 unclassified. Every mutated file restored byte-identically; the pinned receipt and its 14 artifacts
are untouched.

Updated 2026-10-03T16:55:42.773864+00:00 at HEAD 67935d3e.

## Passes 6 and 7 - clean kills, and a row that does not test what its name says

`F1-F5` turn the five provider failure branches into `ok:true`. All five are caught with the driver
alive. They credit no new row, because those two rows were already counted as measured by the round-3
reviewer - the difference is that the measurements are now reproducible from this repository instead of
from a temp directory.

`F6` exposed a defect in **this addendum's own bucketing**, now fixed and recorded: the earlier rule
looked only at rows no shipped case had ever killed, so a mutant that failed only already-covered rows
printed as "survived". Re-measured, F6 kills `W1301-DEGRADED-PROBE-IS-NEVER-SUCCESS` and
`W1301-DEGRADED-PROVIDER-VIA-CHANNEL-IS-FAILURE`. Buckets are now `caught-new` /
`caught-already-covered` / `crashed` / `survived`, decided on the full lost set.

`G2` makes `emptyState()` report `FIRST_RUN` even when projects exist and cleanly kills
`W1301-EXISTING-PROJECT-SKIPS-EMPTY-STATE` - a new row out of OWED.

`G1` is the sharpest result of the pass: setting `requires_terminal: true` in `host.js` failed
`W1301-FIRST-RUN-NEEDS-NO-TERMINAL`, while
`W1301-WORKBENCH-TELLS-NOBODY-TO-USE-A-TERMINAL` stayed PASS. A row named for the terminal promise is
not sensitive to the terminal flag, so it either reads markup only or duplicates the other row - and
that is now written as a demonstrated mismatch rather than as a missing mutant.

Counts after pass 7: **11** accounted, **8** OWED, 0 unclassified. The remaining important owed item
is `W1301-PROVIDER-OK-IS-SUCCESS`: the provider catch-all branch (A6) still answers `ok:true` for an
unlisted status without any row noticing, which is the card's own second negative.

Regenerated 2026-10-03T16:58:17.443449+00:00 at HEAD 36620507; `host.js` restored byte-identically after every run and the pinned receipt
and its 14 artifacts are untouched.

## Pass 8 - reservation 7 becomes a reproducible mutant

`H4` put a PATH fallback back at the place that actually launches the driver
(`[node_bin, drv, td]` -> `[node_bin or 'node', drv, td]`). The run stayed **PASS with all 31
assertions and the driver alive**. The round-3 reviewer predicted this in prose as reservation 7 -
that `W1301-TOOLCHAIN-NODE-PATH-FALLBACK-IS-REFUSED` tests a hard-coded bogus table rather than the
launch site - and this pass turns that prediction into a mutant anyone can re-run:
`python execution/v2.4/receipts/W13/W13-01/mut_addendum8_w1301.py`.

`H2` (accept a mismatched node hash) was skipped rather than fudged: the anchor it wanted to break
was located by its refusal *message* line, and the condition it needed to disable sits elsewhere, so
the script recorded a skip instead of editing something nearby and calling it the same mutant.

## Two counts in this file, deliberately reconciled

- `19` rows in the disposition table (emitted 31 minus rows the shipped matrix kills).
- `8` marked OWED: no filed mutant **and** no reviewer measurement covers them.
- `15` rows that no mutant filed in this repository has taken down: this set is larger because some
  rows rest only on the round-3 reviewer's temp-directory measurements, which are evidence but are not
  runnable from here.

Both numbers are kept on purpose: collapsing them would either overstate what this repository can
reproduce or understate what the card has actually shown.

Updated 2026-10-03T16:59:09.152759+00:00 at HEAD 08b3db2d; `tests/ui/check/main.py` is a pinned artifact and was edited only transiently,
restored byte-identically, exactly as the shipped matrix does with the equally pinned `host.js`.

