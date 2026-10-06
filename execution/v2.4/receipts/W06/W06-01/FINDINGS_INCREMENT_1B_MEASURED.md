# W06-01 increment 1b - what the acceptance service emits today, run rather than read

Fixture mode only; `--mode live` was not run because the LIVE provider backend is a recorded missing
resource, and running it would have manufactured an unverifiable claim.

| check id | exit | status | ids emitted | ids not in expected.json |
| --- | --- | --- | --- | --- |
| `W06-G01` | 0 | PASS | 72 | 0 |
| `W06-G02` | 1 | FAIL | 0 | 0 |
| `W06-01` | 2 | - | 0 | 0 |

- 76 assertion ids exist in `tests/orchestration/expected.json` across 18 groups.
- 72 of them were actually emitted by `ops/ci/orchestration.py` in fixture mode across the three
  selectors probed (including `W06-01`, which has no registry key: the handler answers the env
  selector even though `dispatch.py test.orchestration` returns NOT_IMPLEMENTED).
- 4 ids were never emitted by any of the three probes; first twelve: `C01-01-CONTINUATION`, `C01-02-HISTORY-NO-ASK`, `C01-03-PROVENANCE`, `W06-G02-SUCCESSOR-ACCEPTED`

## Why this changes increment 2

The handler exists and is reachable by environment selector, but nothing reaches it through the
dispatcher - so the missing piece is genuinely a registry binding plus whatever `W06-01`-specific
ids must be added, not a from-scratch acceptance service. That is the "复用" half of the card, now
backed by runs instead of inference, and it also means a bound key would emit real ids on day one.

One caution the numbers carry: `W06-01` produced 0 ids under a selector that no accepted card owns.
Whether those rows are the right assertions for this card, or leftovers from the gate suites, is a
design question for increment 2 and is not settled by them existing.

Measured 2026-10-03T17:09:15.034468+00:00 at HEAD de1d196e; every probe wrote its own report under `execution/receipts/W06/`, which is
harness output rather than this card's evidence.

## Correction, after re-running each selector separately

The table above was written from one batch and its headline overstated the handler. Re-measured, one
process per selector, fixture mode:

| selector | exit | status | ids emitted |
| --- | --- | --- | --- |
| `W06-G01` | 0 | PASS | 72 |
| `W06-G02` | 1 | FAIL | 0 |
| `W06-01` | 2 | - | 0 |
| `W06-G99-BOGUS` | 2 | - | 0 |

What actually holds:

1. `W06-G01` is the working gate suite - it answers the env selector and emits 72 of the 76 expected
   ids, which is where the "already 72 emitted" figure came from.
2. **`W06-G02` currently fails in fixture mode: exit 1, status FAIL, 0 assertions.** That is a live red
   in the W06 line and it is not this card's doing; it is recorded here so the next window starts from
   it rather than assuming the successor-acceptance suite is green. The four ids nothing emitted
   (`C01-01-CONTINUATION`, `C01-02-HISTORY-NO-ASK`, `C01-03-PROVENANCE`,
   `W06-G02-SUCCESSOR-ACCEPTED`) belong to that failing suite.
3. `W06-01` emits **nothing**: exit 2 with an argparse usage error, so the handler does not recognise
   that selector at all. The claim that survives is narrower than the title suggested - a handler
   reachable by env selector exists for the accepted gate ids, not for this card's.
4. A fabricated selector behaves the same way (exit 2), so an unknown `--check-id` cannot silently
   produce a report, which is the property the registry gate is supposed to keep.


