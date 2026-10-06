W15-G01 / A09 FIXTURE: set `RESEARCHOS_TASK_ID=W15` and exactly one of
`RESEARCHOS_CHECK_ID=W15-G01` or `RESEARCHOS_CASE_ID=A09`, then run
`python tests/skills/run_fixture.py --mode fixture`. The runner requires the
frozen assertion inventory, records raw Go output and source hashes, and fails
on missing, duplicate, or failed assertions. It runs product HTTP handlers and
a read over real loopback HTTP against file-backed SQLite, sealed synthetic source
snapshots, the W10 paired experiment path, and
the actual independent product acceptance service. It does not establish
W15-G02, real-source quality, host skill installation, or construction sign-off.
