# C57 interim development test ledger

This file records commands observed after numbered receipt 031. Those commands
were executed through the tool terminal but were not separately redirected to
raw receipt files. It is an interim ledger, not a replacement for final raw
test transcripts or independent acceptance. No original ResearchOS root, DB,
process, ACL or reboot was used for these tests.

| Order | Target / observation | Exit |
| --- | --- | --- |
| 1 | Domain compile after the new historical native/source changes | 0 |
| 2 | Host/Domain/Store/Control compile after first Host routing | 0 |
| 3 | Store schema24/87 existing-RW fixture plus protected/residual census | 0 |
| 4 | Journal pending/abort/unknown inventory fixture | 0 |
| 5 | Historical classifier fixture first attempt: UNKNOWN because residual selector required the circular external plan hash for idempotency | 1 |
| 6 | Historical classifier after residual selector correction: NOT_APPLIED/APPLIED/UNKNOWN fixture | 0 |
| 7 | Shared boot6 compile while independently edited: windows.FILE_DELETE_CHILD undefined | 1 |
| 8 | Shared boot6 compile while independently edited: ACCESS_MASK/uint32 mismatch | 1 |
| 9 | Private native hold commit/rollback, file rename denied until Close | 0 |
| 10 | Planned writer fixture first attempt: duplicate fixture runtime_dispatches identity | 1 |
| 11 | Planned writer fixture second attempt: fixture database basename domain.sqlite, not required researchos.sqlite | 1 |
| 12 | Planned writer fixture after isolated SQLite clone: writer committed but recovery classifier returned UNKNOWN because a live Task reference revision advanced | 1 |
| 13 | Planned writer after reference resolver correction: classifier APPLIED, but test assumed Task had exactly one baseline version | 1 |
| 14 | Planned writer five-version delta against actual baseline | 0 |
| 15 | Planned writer upload-then-version collision rollback, successful commit and same-plan private writer replay refusal | 0 |
| 16 | C Host business identity native hold and early Control CLI parser fixtures | 0 |
| 17 | Journal full-plan hashes and wrong applied outcome fixtures | 0 |
| 18 | Overbroad test name filter started unrelated existing qualification tests and was interrupted intentionally; narrower target selected afterward | 1 (interrupted) |
| 19 | Narrow combined command while boot6 editing: inspectExistingBusinessProcess undefined | 1 |

The boot6 compile failures in this ledger occurred while its separate owner
was actively editing its six files. The maintenance builder did not edit them.
The next combined test run must be captured as recipe, raw stdout/stderr and
exit status after boot6 freezes.

## Continuation after 031

These first commands were observed in tool output but were not redirected at invocation. They remain diagnostic only; later numbered commands capture recipes, outputs and native exits.

| Order | Target / observation | Native exit |
| --- | --- | --- |
| 20 | Historical native raw3/ACK2 positive and TOOL/suffix/missing-raw negatives | 0 |
| 21 | Existing replacement crash recovery | 0 |
| 22 | Existing replacement commit/readonly/identity/causal suite | 0 |
| 23 | Five selected upgrade positives plus historical domain tests: existing `TestConfigurationUpgradeActiveQueueRecovery` failed at schema22 `client_command_identities` | 1 |
| 24 | `TestConfigurationUpgradeFrozen22ProgramLock` without its explicit external program-root environment prerequisite | 1 |
| 25 | New C-LD03 replacement own-pending test first synthetic plan changed a forbidden installation field | 1 |
| 26 | Corrected C-LD03 before/after publish fixture | 0 |
| 27 | Isolated detached 085b baseline initial attempt: sparse worktree omitted evaluation packages | 1 |
| 28 | Isolated detached 085b baseline with evaluation present: same schema22 `client_command_identities` error | 1 |
| 29 | Candidate repaired schema22 fixture first attempt lacked a real Task binding | 1 |
| 30 | Candidate direct legacy SQL rows with Task/queue/fence/control/idempotency bindings and original recovery assertions | 0 |
| 31 | New ops backup namespace gate | 0 |
| 32 | New ops release-host namespace gate | 0 |
| 33 | New C-LD02 five-plan lease/normalization/native-rename tests | 0 |
| 34 | New Host root gate both namespace test | 0 |
| 35 | 034-041 first combined suite used default TEMP/TMP/GOTMPDIR outside the registered fixture root; 039 apps/control additionally failed an obsolete expected error string after the earlier journal gate | 039=1; others=0 |
| 36 | 042-049 same selected suites with own TEMP/TMP/GOTMPDIR/GOCACHE and updated expected early error; all eight native exits | 0 |
| 37 | Blocked driver rollback/commit-error native hold test | 0 |

032/033 are the separately captured baseline/fixed configuration commands. The baseline was clean at HEAD 085b4711afe0c1288448b174eef24ecd5af0551b; its dedicated temporary worktree was removed after evidence capture. 034-041 remain diagnostics because their environment variables were incomplete. 042-049 source bytes are captured in 042-049-source-snapshot.json; later source edits need separate validation. The fixture test’s real-Task and SQL22 correction preserves the original queue/control/Run recovery checks.
