# schema24 → schema25 Native migration: author source freeze

Status: **SOURCE_IMPLEMENTED_PUBLIC_FIXTURE_PASS_PENDING_INDEPENDENT_REVIEW_AND_NATIVE_SYNTHETIC_GRANT**.

This is the author delivery for the finite Source/fixture stage A. It is not independent acceptance, Native positive proof, original-product migration, Main integration, package acceptance, or formal-case completion. Formal increment is **0**. No original product database was read or written; no original process was controlled; no Root issuer private key was read/copied; no production or Root fixture grant was signed by this author.

## Frozen identity and scope

- Worktree: `D:/作品集/ResearchOS/research-os/.local/worktrees/schema24-to25-native-20261014`.
- Base commit: `60f8c81a7529081eb51d525ab913d63102148a46`; base tree: `01c9969cc34296b0e8978c2276d69cad29e9759f` (Main source plus accepted storage dependency).
- Final HEAD: `1b5ec5d049db7811f6e0d8b143659ea5e2f0836b`; final tree: `3a7d5085a5389ea89ceae8dab637d1fb4f0f9b43`.
- Exactly the 22 paths in `scope.json` changed. Final working tree is clean and `git diff --check` passed. `final-freeze/source.patch`, `final-freeze/source/`, `source-pins.json`, `readonly-guards.json`, and raw Git observations provide review inputs.
- Existing schema23→24 public options, purpose/schema/argument/grant namespaces, old grant signed bytes, issuer anchor, storage migration25 SQL, Main and Mu Core files remain outside this change. The only backup policy edit is the explicitly scoped ordinary public pause-upgrade handoff branch.

## Implemented behavior

The new fixed plan `schema24-to25-runtime-pause-v1` uses purpose `RESEARCHOS_RUNTIME_PAUSE_SCHEMA24_TO25_V1`, grant schema `researchos.pause-schema-migration-grant.v1`, child argument `--private-pause-schema24-to25`, Root operation `schema24-to25`, grant file `current-schema24-to25-grant.json`, nonce directory `consumed-schema24-to25-grants`, and explicit signer kind `pause-migration-grant`. Shared implementation uses private trusted descriptors; callers cannot supply arbitrary SQL or construct Native tokens.

The ordinary handoff explicitly pins three different programs: actual old schema24 backup producer, new target control, and new target rehearsal backup. It checks the ordinary backup manifest, source producer stdout and process observation, complete encrypted backup integrity, exact source/target inventory, and handoff binding. It performs normal isolated restore/recovery before the fixed migration25 rehearsal. Receipt fields keep original source24 rows distinct from post-restore rows, and include source/restore/pre/post schema values. The original source stays unchanged. The existing public UpgradeLocal route does not accept this new plan.

Native control has a separate private branch. New paths are checked before opening a database, including rejection of relative/fragment/query paths and mismatched bound database/root. The Native authority flow binds current issuer/release, native file identities, required dynamic pins including all three programs and raw producer evidence, current Owner authority, root lease, exclusive database open, and consumable grant. It executes only the fixed SQL25 transaction, checks typed old rows unchanged, appends migration25, and requires the three new tables empty. It retains conservative handling after an uncertain commit result; the handoff receipt never grants Native authority.

## Verification actually executed

The retained Go ledger has 29 attempts and **3 failed attempts**; none was erased or renumbered. Failures were: capture07 synthetic actor missing PLANNER role; capture10 test compile error after a fixture refactor; capture18 harness comparison of slash-normalized source-root options after both child commands had actually succeeded. Corrections and subsequent captures remain separate.

- Capture13: 60 top-level tests / 212 leaf cases passed across the scoped source regression packages, including existing prepared-upgrade/handoff/authority tests. The enrollment package had no tests (one package-level skip, no test-level skip). This capture predates the last path-validation-only edit.
- Capture24: the final control path-validation edit passed 2 top-level / 9 leaf cases, including the existing control boundary test.
- Captures25–28: all four final r3 programs built from the clean final HEAD with `-mod=readonly -trimpath -buildvcs=true` and the locked local Go 1.27.1; each `go version -m` reports `vcs.modified=false`.
- Capture29: actual final-binary public CLI chain passed. `public-cli-handoff03/00-source-backup/` and `00-rehearsal/` retain raw stdout, stderr, invocation and closed Windows-job observations. `05-case.result.json` explicitly says `PUBLIC_CLI_REHEARSAL_ONLY_NATIVE_NOT_RUN`. Before/after original typed-row digests match. The restored copy reached schema25 with required recovery deltas and empty new tables.
- Earlier focused captures retain positive workspace restore fixtures, per-payload corruption negatives, grant/purpose/input-boundary fixtures, rollback cases, and environment forwarding checks. These are source/fixture evidence only.

`final-freeze/verification-summary.json` derives the cited counts from raw Go JSON. No full-project test-suite pass is claimed. Native positive/replay and Native negative execution are **not run** at this freeze.

## Exact binary and compiler inputs

Final target artifacts are under `D:/作品集/ResearchOS/research-os/.local/schema24-to25-programs-20261014/candidate25-r3/`: `backup.exe`, `control.exe`, `recovery-root.exe`, and `enrollment.exe`. Their exact pins are in `target25-r3-build-inputs/programs.json` and `public-handoff03.config.json`.

The source24 producer is the actual `ops/backup` binary built from the existing read-only schema24 worktree `C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-any-combined-build-20261014`, commit `a7ec7ebf2d53848ea163b6115667b3e3761a6bd2`, tree `5b54aa0b8b94cb8012413efd401dc417671b06de`. Its path is `D:/作品集/ResearchOS/research-os/.local/schema24-to25-programs-20261014/source24/backup.exe`, SHA256 `1a08054960d126fc1bfc1ba997e01b3b63ff25c1c6aa14a523ef2610692713c3`. It is not a target binary pretending to be an old producer.

`source24-build-inputs/` and `target25-r3-build-inputs/` contain raw dependency enumeration, compiler/toolchain/module-lock input hashes, VCS/build observations and program pins (final target: 363 dependency packages / 2311 pinned input files including the locked toolchain manifest). Builds use D-drive cache/temp; no new C-drive worktree or Go cache was created. The read-only source24 resource was not modified.

## Independent review and Root-owned Native continuation

First independently review this exact frozen source, patch, program pins, handoff evidence, and the new `TestNativePauseMigrationAuthorityHarness` in `internal/domain/backup_pause_migration_windows_test.go`. The author cannot accept this delivery. Existing issuer resources are not reported missing; Root owns any later signing decision.

The harness needs `RESEARCHOS_NATIVE_PAUSE_MIGRATION_HARNESS_CONFIG` pointing to a new public config derived from `public-handoff03.config.json`, schema `researchos.synthetic-native-pause-migration-config.v1`. Set a fresh CaseID and OutputDirectory and copy the exact r3 programs into a fresh case directory; update only their paths and verify bytes/hashes. Root and control must share that fresh directory. Preserve source24, Python, broker and private-stdin helper pins. The source release root must still be exact schema24. Use `RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT=D:/作品集/ResearchOS/research-os/.local/go-tmp/schema24-to25-native-20261014` as the test's explicit D-temp proof; this is not forwarded to children.

Run from the frozen worktree with the same captured Go environment:

```powershell
go test -mod=readonly -json ./internal/domain -run '^TestNativePauseMigrationAuthorityHarness$' -count=1 -timeout=25m
```

Supported separate case names: `positive-replay`, `missing-native-channel`, `wrong-purpose`, `mismatched-database`, `release-pin-mismatch`, `expired-grant`, `missing-dynamic-pin`, `wrong-owner`, `lease-occupied`. `public-handoff-only` is the already-executed no-signing branch. Negative expectations, including deliberate malformed grants and the signer's own validation boundary, require independent review before Root creates any signatures.

For Native cases the harness creates only isolated synthetic data, executes the old producer and new handoff, then writes `01-release.payload.json` and `01-release.ready.json`. Root reviews the exact payload and pin set and, if authorized after review, signs into the ready record's fixed path. Root supplies `01-release.approval.json` with `Action: release-signed`, `PayloadSHA256` and `SignedSHA256`. The harness then creates the short grant payload/ready pair; Root separately reviews its current database/native identities/paths/pins and signs with the indicated explicit kind, then supplies `02-grant.approval.json` with `Action: grant-signed-and-invoke` and both exact hashes. Approval JSON property names are the exported Go field names; digests use `sha256:` prefix. The harness does not read issuer secrets or sign grants.

The harness invokes the actual Root/control processes through the pinned reviewed broker and retains raw observations. It finally writes `06-fixture-retained.ready.json` and waits for Root inspection before `06-release-fixture.approval.json` with `Action: release-fixture` allows isolated-fixture cleanup. Overall harness context is 20 minutes; Owner fixture token lasts 15 minutes, so review and signing should be coordinated before launch. Each case uses fresh output, binary directory, fixed-file namespace and grant nonce. The expired case intentionally waits past the initially valid grant's 90-second expiry after signing.

Any independent rejection or Native failure remains an additional recorded result. Do not count source tests or the public CLI handoff as Native acceptance, and do not reset the existing three failures.
