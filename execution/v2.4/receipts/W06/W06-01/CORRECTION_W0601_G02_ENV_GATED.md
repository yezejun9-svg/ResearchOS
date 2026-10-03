# Correction to the W06-G02 classification (supersedes wording in FINDINGS_INCREMENT_1C_G02_CAUSE.md and RESUME_PACK_W0601.md)

Measured at commit `69135687` with the pinned toolchain, full family run:

    .local/tools/go1.27.1/go/bin/go.exe test ./internal/domain -count=1 -timeout=6m -v -run '^TestW06'

Result (raw log: `w06_family_regression.txt`, sha256 pinned in `checkpoint.json` ->
`work_in_progress.w06_family_regression.log_sha256`): **20 PASS / 0 FAIL**, and
`TestW06ContextContinuation` reports `--- SKIP`, i.e. it does **not** require `codex.exe` when
`RESEARCHOS_C01_MODEL` is unset. `ops/ci/orchestration.py:64-70` sets that env var only when the
selected test names include `TestW06ContextContinuation` (`is_c01`), and the three red runs in
`FINDINGS_INCREMENT_1C_G02_CAUSE.md` were all made through that path (`selector "W06-G02"`,
`RESEARCHOS_C01_MODEL=1`).

Therefore the earlier statement must be narrowed:

- WRONG as written: "W06-G02 is resource-blocked because `codex.exe` is absent" as an unconditional
  property of the check.
- Correct: the **C01 live-agent path** of `TestW06ContextContinuation` is resource-blocked on this
  machine (the driver is invoked only under `RESEARCHOS_C01_MODEL=1`, and the runner always sets it
  for `W06-G02`). Outside that environment the test skips, so it also emits none of the four ids
  `C01-01-CONTINUATION`, `C01-02-HISTORY-NO-ASK`, `C01-03-PROVENANCE`,
  `W06-G02-SUCCESSOR-ACCEPTED`. A skip is not a pass and, per the rules, is not acceptance evidence.
- Consequence for the card: `test.orchestration` still stays UNBOUND (binding it would advertise a
  route whose W06-G02 ids cannot be produced here), and the W06-01-owned 7 ids measured in
  increment 2 remain proven only by the direct Go run until the selector registration lands as a
  W02-02-owned change. Nothing about the increment-2 result is changed by this correction.
- `blocked_resources` row `W06-G02-live-model-driver` stands, and is now precisely scoped to the
  `RESEARCHOS_C01_MODEL=1` path. Kept as a new file rather than editing `RESUME_PACK_W0601.md` or
  the increment-1C note, so the earlier text stays reviewable.

Old records are untouched; `failure_counters` (17 rows) and `integrity_events` were not modified by
this correction, and no accepted receipt references the corrected files' digests.
