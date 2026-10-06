# Registration repair controls

These ten new synthetic controls target exactly the registration-time dispatcher
dependency repair in both readers. They cover a dispatcher absent from the
earlier product vector, a wrong native digest, changed current bytes, mutation
after reading (local finish and public CAS recheck), and an unpinned child input.
Every negative control starts with a valid isolated positive fixture.

The existing fixture constructor only builds inert fake source/tool/receipt
files beneath this directory. Neither Go, the dispatcher, any child driver nor
any provider runs. The synthetic fixture's three eligible cases test parser
behavior; they contribute zero real formal cases and issue no real acceptance.
The old 65, 30 and 2 controls are not counted as runs of these repaired readers.

`run_controls.py` verifies root-frozen reader hashes and the actual locked Python
binary, archives all applicable source and frozen catalog bytes, then runs only
`test_registration_repair.py` with `-B -X utf8`. Immutable receipts retain argv,
times, raw streams, source hashes, complete control roster and zero product
command/formal-case deltas. Unchanged failed inputs cannot automatically rerun.
