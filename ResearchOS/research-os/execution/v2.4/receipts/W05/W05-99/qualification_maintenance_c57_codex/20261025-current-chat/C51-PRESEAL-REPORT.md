# C57 owned51 source preseal

**Status:** owned51 source prepared for parent review. No staging, commit, original data/process/ACL action, or formal acceptance. The boot6 files are a separate author's six-path scope and remain under correction.

## Exact bytes and diagnostics

- `C51-PRESEAL.json` SHA256 `cd99649c24552dbd6394ba97daf04bb835da16170cd02c4ef0808684614b29fb`: base commit `085b4711afe0c1288448b174eef24ecd5af0551b`, base tree `227d36324fd1053c285d0b2846a2b707ac2df6bd`, all 51 owned paths, 46 changed paths, 40 inherited Source43 paths checked byte for byte.
- `C51-PRESEAL.patch` SHA256 `3fedd11ac8a7f1dc6958d4a456c9eb66ee591fcab2a746bb6e4bd32ab9a4d090`, 284346 bytes. `git apply --cached --check --whitespace=error` returned native 0 without staging.
- `C51-DIAGNOSTIC-LEDGER.jsonl` is the preserved 89-line regenerated ledger; the separately labeled reconstructed 86-line version matches the first announced hash. `C51-LEDGER-REWRITE-INCIDENT.json` explains the rewrite error. The crosswalk distinguishes repeated descriptions from distinct invocations. `C51-EARLY-RAW-ADDENDUM.md` identifies explicit early Go FAIL outputs and both 007/009 formatter overreaches; numeric exits remain uncaptured for those early commands.
- `032` captures the isolated 085b baseline native exit 1 for the existing schema22 `client_command_identities` fixture mismatch. `033` captures the repaired candidate native exit 0 for the original active-queue recovery test. The baseline worktree's actual HEAD/clean status and verified deletion target were observed in the tool dialogue but not separately persisted as raw files; the recipe's `head` field is a declaration. Neither 032 nor 033 explicitly set `TEMP/TMP/GOTMPDIR` to the registered fixture root, so those tests have that environment limit.

## Coverage by source branch

| Branch | Current evidence | Limit |
| --- | --- | --- |
| C-LD01 root lease copies, generation/kind borrow | `042` runtime native fixture exit 0 | No original Root action |
| C-LD02 normalized five-plan source guard, prepared nested Close | `045` domain and `050` C51 delta exit 0, real held lease and native rename refusal | The five-plan dispatch negative uses incomplete later inputs; existing positive upgrade fixtures remain separate |
| C-LD03 ordinary versus exact own journal recovery | `043` journal and `046` Host replacement exit 0; new before/after publish test, cross-namespace denial, existing crash-recovery suite | No original journal read/write |
| Early normal/replay/backup/release-host gates | `046` Host, `047` Control, `048` backup, `049` release-host exit 0 | `039` failed an older expected error string after the new earlier gate; fixed and retained |
| F01-D01/W-D01 exact historical raw3, ACK2, source/native Job class | `045` and `050` domain native fixtures exit 0; TOOL mutation, suffix, missing raw, no-delete hold | Synthetic native receipt is a grammar/identity fixture, not original worker Wait or independent STOP |
| F01-D02/D03 five-version FAILED write, replay classification | `045`/`050` domain schema24/87 WAL fixture; upload/version collision rollback, five versions, Task/ledger unchanged, same-plan private writer replay denied; protected 78 and residual nine-table census | Full Host commit/recover cannot run without actual post-restart boot witness |
| Native hold through SQL return | `050` includes blocked driver rollback after caller cancellation and blocked Commit error; native source rename fails until driver return and cleanup; Plan and Apply use non-canceling Tx lifetime and original ctx on SQL/gate | No fault-injected end-to-end `ApplyHistoricalQualification` with real boot token; cancellation response waits for synchronous rollback |
| Host replay and business identity | Host source separates management `CurrentQuiescence` from a held business-owned host-state SID and DB OWNER/root; `046`/`052` native business identity fixture exit 0; same-operation/same-plan durable branch classifies exact `APPLIED` and returns prior outcome | No actual distinct-SID manager/BusinessSID or full Host durable replay fixture |

The 042–049 own-environment results bind to `042-049-source-snapshot.json` (SHA256 `866243cd591df14a6cd695213211887f4cd7dada580789f18528e7b3c3353764`). The later 050–052 recipes/raw/native exits bind to the owned51 preseal; `050-052-boot-before.json` and `050-052-boot-after.json` show `boot_windows.go` changed during those commands, so they are C51 local diagnostics, not a frozen combined57 proof. The earlier 034–041 batch did not set own `TEMP/TMP/GOTMPDIR` and is retained as an environment deviation.

## Completion boundary

The parent must integrate a newly frozen and independently reviewed boot6, then rerun only affected package/Host integration and cross-platform compilation against one stable 57-path source snapshot. Privileged distinct-SID ACL deployment, real RestartApps/FullRestart, original Host/DB closure, historical missing verifier Wait and formal acceptance remain unperformed.
