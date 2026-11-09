# C7 narrow Source correction

C6/O4 independent review returned REQUEST_CHANGES with one P1,
C6-O4-R01: the actual before_resume context lacked four reviewed Source pins.
C7 adds exactly canonical_transactions_source, job_watchdog_source,
source_guard_source and base_owned_process_source to that actual context Dict.

The delta control extracts the real Dict AST, evaluates it with C7's current
hard pins, and passes it through O4's extracted 11-role provenance helper.
Removing exactly those four text lines restores C6 controller text and AST.
All six helper Source files are byte-identical to C6; HERE-local hard paths
relocate to this C7 namespace with unchanged content hashes.

This packet is Source-only. It has not imported O4 as a candidate, launched
Windows processes, created threads, queried WinAPI, contacted providers,
written Canonical state, or self-issued READY. C6's first pure-control failure
remains ordinal 706 and is pinned separately.
