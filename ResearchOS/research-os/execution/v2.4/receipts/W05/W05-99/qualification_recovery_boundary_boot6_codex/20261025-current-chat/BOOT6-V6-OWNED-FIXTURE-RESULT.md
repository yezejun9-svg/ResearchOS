# C57 boot6 owned-fixture execution supplement v6

Status: `FAILED_FIXTURE_RESOURCE_AND_SOURCE_DIAGNOSIS_OPEN`; formal acceptance increment 0. This supplement does not supersede v5 source or test claims. The v5 test fixture was actually created at `C:\Users\yqyyds\AppData\Local\Temp\TestDisposableRealPEAndScriptFence1757777756`, outside both CP538 owned roots. Its previous passing result is retained as historical evidence, not reclassified as in-scope.

## Exact owned-root reruns

CP538 SHA256 `a31d4ee8e63f750a71c24a57cd9a1fe50fb121d7b4bbb152d8c11d2c98e069fc` authorizes `D:\作品集\ResearchOS\research-os\.local\qualification-recovery-boundary-boot6-20261025-tmp` and `C:\Users\yqyyds\.codex\researchos-fixture-cache\qualification-recovery-boundary-boot6-20261025`. All v6 `TEMP`, `TMP`, `GOTMPDIR`, and `GOCACHE` values in the three preregistered recipes were within those roots. The six source hashes still match `final-v5-six-source-manifest.json` (mismatch count 0); no source or Linux build was rerun or changed.

| Attempt | TEMP/TMP | Native test exit | Fixture observations |
| --- | --- | ---: | --- |
| v6 | ASCII owned root `native-tmp-v6` | 1 | Two ACL fixture tests skipped on `Access is denied`; stale-descriptor fixture failed on the same bare error. |
| v6b | D owned root `native-tmp-v6b` | 1 | Same two skips and one failure. |
| v6c | Newly created D owned child `native-tmp-v6c`, with explicit inheritable current-user FullControl | 1 | Same two skips and one failure. |

The exact argv, environment, stdout, stderr, and native exit are in `final-v6-owned-fixture-command-recipe.json` and `final-v6-owned-fixture-windows-tests.*`, with corresponding `final-v6b-*` and `final-v6c-*` files. The unchanged tests passed their remaining cases, including same-user native Explorer token inspection, but the ACL fixtures did not pass in any owned root. No attempt is reported as a successful in-scope native suite.

## Bounded diagnosis and cleanup

Only the newly created, resolved child `native-tmp-v6c` had its ACL adjusted. `final-v6c-owned-child-before-acl.json` and `final-v6c-owned-child-after-acl.json` retain exact owner and SDDL. `final-v6c-creator-token.*` retains `whoami /all` and native exit 0. The first `icacls` command returned native exit 1332 because the raw SID lacked the required `*`; its output remains. The corrected command returned native exit 0 and added an `(OI)(CI)` current-user FullControl ACE. No existing owned root, OS ancestor, or original ACL was changed.

The read-only `final-v6c-os-temp-probe.*` confirmed Go `os.TempDir()` selected the authorized D child. A separate owned diagnostic file has current-user owner and explicit FullControl; `final-v6c-native-open-probe.*` shows Win32 `CreateFileW` can open that file with mask `0x000E0081` (`READ_CONTROL|FILE_READ_DATA|FILE_READ_ATTRIBUTES|WRITE_DAC|WRITE_OWNER`), native exit 0. This does **not** identify which API returned `Access is denied` in the frozen `setTargetDescriptor` test path: its bare error could come from the open, `SetSecurityInfo`, or later operations on a different file. No ACL or privilege explanation is asserted without that stage evidence. The live-file read watcher captured no transient test file (`final-v6c-live-fixture-acl-observation.json`).

`final-v6-owned-fixture-cleanup-check.json` finds zero remaining `Test*` or `go-build` entries in all four owned temporary directories after the runs. One manual diagnostic file remains at `D:\作品集\ResearchOS\research-os\.local\qualification-recovery-boundary-boot6-20261025-tmp\native-tmp-v6c\diagnostic-acl-v6c.tmp`: automatic approval review rejected two exact `Remove-Item` commands before execution with the only stated reason `blocked by policy`. No alternate deletion was attempted. This is a cleanup exception, not a test fixture leak.

`diagnostic-ledger-v6.jsonl` adds 11 entries without changing the original ledger. Original `diagnostic-ledger.jsonl` SHA256 remains `b3cdf737af44207d3022939c9f6fd678be48fb6c65e3e9bf93a4539fc07a90f6`; original `final-v5-author-freeze-seal.json` SHA256 remains `804490a6a59252abd1a49a17e37e2019b5e77d9d22c610ca9b568ef6e7202f4c`. Three independently reported P1 source findings remain for the next source revision; this supplement does not sign them off.
