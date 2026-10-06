# W04-99 execution evidence

This directory is execution evidence only. The executor cannot accept its own
work, register canonical state, or grant product LIVE qualification.

`collect.py` is the explicit single-run collector. It freezes applicable bytes,
records real executable hashes, runs pure intercepted transport controls, runs
one locked Go suite, and runs the frozen package validator once with locked
Python. Every failed attempt retains its raw stdout/stderr and source vector.
An unchanged failure is not automatically retried. The Go suite uses actual
HTTP/SQLite domain operations plus actual native workspace authority/scanning.
The package validator has specification-only scope.

`parent_driver.py` reads that observed proof without starting Go or validators.
It verifies exact current bytes, added/removed source inventory, tool binaries,
test completion, exact assertion rosters and both actual process results. Its
eleven direct outputs cover six full formal command bindings and five parent
checks. Counts are 10 unique formal assertions, 3 formal cases, 6 command
bindings and 5 parent gates. Repeated assertions are not additional cases.

`bridge.py` adds the fixed execution-index reference for the registered child.
Only exact W04 current tuples use the new reader. Old `test.context` and
`test.domain` tuples retain the full revision-37 argv, cwd, locked tool mapping,
fixed environment, streams and exit status; the latter retains the W03 bridge.
The new `package.validate` key supports only W04/A01. It does not alias or modify
the existing `package.validate_v24` command. Root owns all registration changes.
`test_bridge.py` tests this transport by interception; it performs no legacy
product, provider, GUI or Go execution.

Source coverage includes all Go and embedded assets under internal/adapters,
migrations, required schemas, external parent tests and the collector/readers.
The complete frozen v2.4 package and historical v2.0 import fixtures are input
bytes, not dynamically selected production policy. Production always uses the
fixed embedded 15 document and fixed MU_FORK constructor.

`current_proof.json` and `current_execution.json` point at immutable run files.
The execution index has four distinct GLOBAL files per case and five gate
command receipts. The fifth GLOBAL part belongs to the independent reviewer.
`verifier_id` records the root-assigned reviewer identity only; execution does
not imply that review occurred. Root must independently inspect semantics,
pin the current context, dispatch the eleven registered selectors, retain the
real independent issuance and update the canonical ledger after acceptance.

## Delivered execution

The successful run is `runs/20261005T225411Z-9b77d17e0eb1`. The prior failed
run `runs/20261005T224949Z-418d17844405` remains unchanged. Both retain all 598
unique applicable source/input/lock/tool-identity file bytes in an archived
source snapshot, with a manifest matching their original version vector.

Root supplied `tests/context/parent/w0499_test.go` under CP215 and the single
artifact-count baseline adjustment in `internal/domain/w03_current_binding_test.go`
under CP216. Their successful-run hashes are respectively
`0328bf3d3c24b41707f756986aaabca463fb97571ca32dad7dd5996c16323468` and
`f6fbce27b5576eed521e57e0a391ecdd28c63c792cc8938ba95de80d205be36a`.
They are included in the executor commit by explicit root authorization; the
same independent reviewer reviews both contributions.

H01 physically missing sealed original bytes currently return `sql.ErrNoRows`
from the domain materializer. The evidence records this actual error and no
output/effects; it does not invent a typed HTTP status. Separate corruption,
missing-current-contract and revoked-authority branches record their actual
typed refusals. Optional recall degradation is observed before freezing the
next required context, rather than claiming an outdated context stayed valid.

The external scanner evidence uses native directory choice and real domain
bootstrap calls. It does not claim a GUI or published client-bootstrap protocol
end-to-end run, and unchanged AGENTS/README bytes do not prove generic conflict
resolution. Subsequent research stages remain NOT_STARTED.
