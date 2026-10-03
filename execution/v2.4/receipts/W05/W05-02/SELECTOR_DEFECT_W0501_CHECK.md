# The accepted W05-01 check program does not read the selector it is bound to

Measured just now with the locked toolchain (`D:\作品集\ResearchOS\research-os\.local\tools\go1.27.1\go\bin\go.exe`), three invocations of the same program:

| invocation | exit | status | assertions |
| --- | --- | --- | --- |
| `--check-id W05-01` | 0 | PASS | 32 |
| `--check-id W99-DOES-NOT-EXIST` | 0 | PASS | 32 |
| `(no arguments)` | 0 | PASS | 32 |

All three emitted the **same 32 assertion ids** (`W0501-ADAPTER-ARTIFACT-BOUNDED-TO-BYTES...`), including the run that passed a check id
that exists on no card and the run given no arguments at all.

## Why this blocks honest use of `test.runtime`

`execution/v2.4/commands.json` binds `test.runtime` with `check_id: [W05-G01, W05-G02, W05-01]`, and
W05-02's card line asks for `--check-id W05-02`. The dispatcher will happily forward any selector it
matches to a program that ignores it and answers with W05-01's suite. So a W05-02 receipt built on
this program would report W05-01's assertions under a W05-02 selector, which is exactly the
"aggregate empty PASS" failure mode the plan forbids, only dressed up as a real 32-assertion run.

## What W05-02 does about it

`tests/runtime/check/**` is inside this card's write scope, so the fix belongs here and is the first
thing W05-02 must land before any of its own assertions count:
1. parse `--check-id` (and the task/case selectors the dispatcher forwards) and branch on it;
2. an id this program has no suite for must exit non-zero with a named refusal and zero assertions,
   never a borrowed PASS;
3. each suite must emit only its own assertion id namespace, so a W05-02 run cannot report W0501-*
   ids and vice versa.

## What is NOT claimed here

W05-01 is ACCEPTED and its evidence is frozen; this file records a defect found later and changes
nothing registered. Whether W05-01's acceptance should have caught it is a question for whoever reads
this - the card's own binding line always passed `--check-id W05-01`, so the accepted run was correct
for the id it was asked about; what is missing is the refusal for every other id.
