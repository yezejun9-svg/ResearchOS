# Receipt-only C01 revision; adoption prohibited

The full proposed single file is based on frozen b50de13c. Its narrow patch adds
one pure absence helper, calls it from both NO_SESSION branches, and replaces
the incomplete initial-qualification success exit with an explicit fixed gap.
The inverse textual transformation reproduces all original source bytes.
The original proposed test file is an unchanged byte prefix of the new file.

The helper checks all queue states, including historical CONSUMED and DROPPED.
It does not treat a generation-only SQLite FK as proof of Task or Session
ownership. Same-project receipts must have verified raw hashes, an original
fence/Session association and a matching command queue row. CANCEL_FENCE must
have the exact producer shape and legal from/to pair. Orphans, crossed labels,
missing predecessors and cycles refuse. An unrelated Task with a valid
CANCEL_FENCE graph remains eligible for the absence component. Other SDK or
stream receipt kinds remain OPEN and refuse; this may block legitimate
unrelated history until its precise association evaluator is implemented.

The 24 new proposed leaves are NOT_RUN. Their complete Task/Goal documents are
checked against the frozen full schemas, and every source tuple is decoded
through the fixed 34-category registry. They exercise both absence callsites.
These are **not** complete mode0 -> materialization -> mode1 -> mode5 fixtures:
the Goal/Task reference graph, original control admission and complete journal
response chain are not constructed by this component fixture. The original
I02 full-mode positive/negative fixture requirement therefore remains OPEN.
The `positive_unrelated_receipt_not_current_pointer` control concerns graph
association only; it is not a claim that a DROPPED queue with no current receipt
pointer can pass the separate full queue settlement validator.

C02/I01 remains OPEN: sandbox/build, full permission/environment/process/memory,
timeout, output uniqueness/locality and model-profile qualification predicates
are not complete. The prior component extraction remains, but cannot return a
successful qualification authorization. Modes2/8 cannot obtain an initial
origin success through that path. The current driver still lacks the proposed
Innocuous field. Fork/pin, source leases, compile, pure tests, SQLite physical
connection/trusted_schema controls, migration and backup tests require separate
authorization and non-author review.

NO_RUN, NO_EXECUTION, R1, mode3 unbound and other existing OPEN branches are not
weakened. No Main/worktree/cache/canonical/source was changed. No Go, gofmt,
SQLite, HTTP, SDK or model ran. Python metadata AST/hash/inverse-diff checks are
not Go syntax checking, compilation or test success.

Two new metadata errors remain separate: 5b7ca2 outer1/nativeNULL (incorrect
snapshot basename), and a1e3bf outer1/Python1 (assumed absent schema key). Earlier
four author origins and peer eade2d remain linked and are not counted again.
