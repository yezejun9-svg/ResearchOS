# Native25 signed staging revision01

Status: **SOURCE_REVISION_IMPLEMENTED_FIXTURE_PASS_PENDING_INDEPENDENT_RECHECK**. This author has implemented the CP476 fix for `P2-NATIVE-TEMP-001`; independent closure remains pending. Native positive/negative/replay execution is **NOT_RUN**, signing is **NOT_RUN**, formal increment is **0**. No original product database/process, issuer private key, Main, package or Mu/Core change is part of this revision.

## Frozen source

- Worktree: `D:/作品集/ResearchOS/research-os/.local/worktrees/schema24-to25-native-20261014`.
- Reviewed base: commit `1b5ec5d049db7811f6e0d8b143659ea5e2f0836b`, tree `3a7d5085a5389ea89ceae8dab637d1fb4f0f9b43`.
- Revision HEAD: `f80955594bdd0373ae1c961cd02ab6be96f2c196`, tree `5bce20214223e8292f16a117a83407f52b4bca4a`.
- Exactly six authorized pause files changed. Working tree clean; diff check passed. `final-freeze/source.patch` is the six-file revision patch, and `combined22.patch` is the complete candidate relative to the original source base. Combined scope remains exactly22.
- `final-freeze/readonly-guards.json` compares all original read-only dependencies and the other16 original-scope files against the reviewed base. No changes. In particular, the old23→24 Root child environment, namespaces, signed options and cleanup helper were not changed.

## Cause and fix

The independent reviewer showed that Native Root starts control with SystemRoot/WINDIR/private bootstrap only. Thus the old new-pause template's empty `MkdirTemp` parent could resolve to `C:\Windows\`, even when the outer broker used approved D-drive TEMP/TMP. The reviewer only probed the selected path; no C-drive write or actual Native access-denied result was claimed.

`pauseMigrationTemplate` now accepts the exact caller options plus their Destination parent explicitly. Both production call sites pass `filepath.Dir` of that same options object's Destination. The Native call remains after signed-options hash validation; the public call remains ordinary handoff and does not gain signing authority.

The new pause-only stage helper checks the fixed plan, parent-to-Destination equality, absolute/nonambiguous paths, native canonical resolution, existing directory parent and existing-directory destination when present. It rejects aliases rather than normalizing away their evidence. It also rejects stage-parent overlap in either direction with the source database directory, backup key directory, backup snapshot and source/target release roots. The public/Native shared path validation performs the same check before normalization and before any staging; the stage-creation helper repeats it immediately before `MkdirTemp(parent, ...)`. Missing parent directories are rejected, not created or replaced with an environment fallback.

No TEMP/TMP/TMPDIR value is consulted by this new helper. The existing `.researchos-backup-stage-` prefix is retained so the existing restricted `backupDiscard` cleanup operates without modification. No public option/signed-byte field, arbitrary temporary path option or environment forwarding capability was added.

## Fresh validation

- Capture31: **5 top-level / 29 leaf** tests pass. Full template creation and cleanup work with missing, empty and hostile TEMP/TMP/TMPDIR, for both fresh and existing rehearsal destinations. Eighteen invalid binding/path/overlap cases reject before staging with an unchanged directory listing. Four actual Windows junction cases reject in the helper and public path validation. Two AST checks bind the actual public/Native production call sites to their own options and Destination parent. These two checks are explicitly source wiring evidence, not Native invocation.
- The same capture also runs real public API handoff under missing and hostile environment values, confirming original typed rows unchanged and stage cleanup. Fixture construction occurs before the environment is altered; the actual handoff runs after alteration.
- Capture32: scoped old/new six-package regression passes **66 top-level / 249 leaf** cases, including existing authority and prepared23→24 coverage. No test-level skip/fail; enrollment has no tests and is one package-level skip. No full-project suite is claimed.
- Captures33–36: new r4 `backup.exe`, `control.exe`, `recovery-root.exe`, `enrollment.exe` built from clean revision HEAD with locked Go1.27.1 and `-mod=readonly -trimpath -buildvcs=true`. All four report exact revision and `vcs.modified=false`.
- Capture37: actual old24 producer → r4 public handoff CLI passes. Both native Windows jobs exit0, drain to0 active processes and close all owned handles without cleanup errors. Original before/after typed-row digests match; restored copy reaches25. `public-cli-handoff04/05-case.result.json` remains `PUBLIC_CLI_REHEARSAL_ONLY_NATIVE_NOT_RUN`.

Counts are derived in `final-freeze/verification-summary.json`. Final target compiler pins cover 363 dependency packages / 2311 input files including compiler executables and lockfile, with raw go-list and build metadata in `target25-r4-build-inputs/`.

## Failure history and preservation

The original29 attempts/3 failures and independent review were preserved unchanged. Revision capture30 is an additional failure: the first implementation used a new stage prefix that the old restricted cleanup deliberately ignored; the new tests correctly detected leftover stage directories. The prefix was restored and capture31 passed. Revision ledger therefore carries **37 total Go attempts / 4 total failures**, with the first29 entries identical to the original ledger.

The five capture30 test-stage directories were already removed by their `testing.TempDir` cleanup. `capture30-stage-cleanup-observation.json` records each exact path as absent; the author performed no additional recursive deletion. No old fixture/resource/evidence directory was removed or rewritten.

The previous SOURCE_REPORT, manifest and all274 listed artifact bytes remain unchanged. Their old source/compiler pins describe the old candidate; the new revision's pins describe the current candidate. This does not reinterpret the prior independent finding as a pass.

## Review and later Native inputs

Use `public-handoff04.config.json` and `target25-r4-build-inputs/programs.json` as current exact target pins. The source24 binary is unchanged at `D:/作品集/ResearchOS/research-os/.local/schema24-to25-programs-20261014/source24/backup.exe`, SHA256 `1a08054960d126fc1bfc1ba997e01b3b63ff25c1c6aa14a523ef2610692713c3`. Its original build/compiler evidence is inherited from the parent source directory.

The prior report's Root-only Native harness lifecycle remains applicable after independent recheck, substituting r4 programs and a fresh case/output directory. The current public fixture's Destination parent is a distinct existing D-drive directory and is now the explicit Native template staging authority. Each new Native config must preserve a canonical, existing, nonoverlapping Destination parent in its signed options. Root alone decides and supplies separate reviewed release and short-lived grant signatures; this author did not execute Native cases or access issuer private material. Independent recheck must precede Native execution/signing.
