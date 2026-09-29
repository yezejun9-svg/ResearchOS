# W02 development checks

Run from the repository root through the registered dispatcher. `build.py` consumes
`RESEARCHOS_GO`, `RESEARCHOS_NODE`, and `RESEARCHOS_NPM_CLI` as absolute paths;
the dispatcher owns toolchain verification. It installs the frozen npm lock,
builds React and Go, runs Go tests, then starts the control service against a
temporary SQLite database and probes its HTTP response. `contracts.py` checks
the immutable specification package and the selected-route dependency declarations.

Both commands print one final JSON result with `scope=DEVELOPMENT_ONLY`.
Business `/v1` operations are deliberately `NOT_IMPLEMENTED`; these checks do
not satisfy product acceptance cases.
