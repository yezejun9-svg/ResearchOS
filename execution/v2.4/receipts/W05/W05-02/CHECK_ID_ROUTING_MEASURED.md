# How `test.runtime` selects a suite - measured, after retracting a wrong claim

## The retraction first

An earlier note in this directory, `SELECTOR_DEFECT_W0501_CHECK.md`, claimed `tests/runtime/check`
ignores the selector it is bound to and would hand any card W05-01's PASS report. **That claim was
wrong and the file has been removed.** It came from a probe that passed `--check-id W05-01`,
`--check-id W99-DOES-NOT-EXIST` and no arguments on the command line. The dispatcher does not pass
flags at all: `execution/command_dispatcher/dispatch.py:141` writes the selectors into the child
environment as `RESEARCHOS_TASK_ID`, `RESEARCHOS_CHECK_ID` and `RESEARCHOS_CASE_ID`, and
`tests/runtime/check/legacy.go:23-25` reads exactly those. So the probe never touched the channel the
program uses, and three identical runs proved only that argv is ignored - which is by design, since
the card's binding line feeds those flags to the dispatcher, not to the check program.

## The same question, asked through the channel the program reads

`RESEARCHOS_TASK_ID=W05` set for every row, locked go1.27.1, `go run ./tests/runtime/check`:

| RESEARCHOS_CHECK_ID | exit | status | assertions | sample ids |
| --- | --- | --- | --- | --- |
| `W05-01` | 0 | PASS | 32 | `W0501-ADAPTER-ARTIFACT-BOUNDED-TO-BYTES`, `W0501-ADAPTER-CURRENT-EPOCH-RENEWAL-ACCEPTED` |
| `W05-02` | 1 | no report | 0 | (none) |
| `W99-BOGUS` | 1 | no report | 0 | (none) |
| `(empty)` | 1 | no report | 0 | (none) |

The program routes W05-01 and refuses everything else: exit 1, no report, zero assertion ids. None of
the three non-W05-01 runs emitted a single `W0501-*` id, so there is no borrowed PASS and no
selector-blindness defect to file. The property I thought was missing is already there.

## What this does change for W05-02

It confirms the actual prerequisite from the other side. A `RESEARCHOS_CHECK_ID=W05-02` run today
refuses because `test.runtime` lists `check_id: [W05-G01, W05-G02, W05-01]` and the program has no
W05-02 suite - the two facts that gate this card's evidence are the registry selector and a real
W05-02 suite, in that order, and the refusal behaviour means forgetting either one fails loudly rather
than passing quietly. That is the outcome the earlier obligation should have described.

## Standing correction discipline

This file replaces a claim that was measured, but measured against the wrong interface. The lesson is
the one W13-01 was rejected twice for in the other direction: read the resolver before judging the
routed thing. The obligation `W05-01-check-id-ignored` in `checkpoint.open_obligations_before_next_card`
is marked corrected in place rather than deleted, so the trail stays.
