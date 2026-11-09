# Construction checks

Run from the repository root through the registered dispatcher. `build.py` consumes
`RESEARCHOS_GO`, `RESEARCHOS_NODE`, and `RESEARCHOS_NPM_CLI` as absolute paths;
the dispatcher owns toolchain verification. It installs the frozen npm lock,
builds React and Go, runs Go tests, then starts the control service against a
temporary SQLite database and probes its HTTP response. `contracts.py` checks
the immutable specification package and the selected-route dependency declarations.

Both commands print one final JSON result with `scope=DEVELOPMENT_ONLY`.
W03 adds authenticated core `/v1` operations, listed in
`contracts/operation_coverage.json`; deferred operations return an explicit error.

`test.domain` runs the actual Go domain fixtures and writes raw test events.
`domain.http.check` starts the built executable against temporary data and checks
concurrency, persistent replay, project isolation and live authorization revocation.
For example: `python -X utf8 execution/command_dispatcher/dispatch.py domain.http.check --task-id W03`.
These construction checks do not grant formal product acceptance.
