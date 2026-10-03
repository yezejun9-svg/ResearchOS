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
