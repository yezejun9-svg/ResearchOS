# boot6 v7–v9 historical diagnostics

This is an additive index of old, mutable-source diagnostic captures. It does not replace v5/v6/v10 seals or claim that a later source snapshot was present during an earlier run. `historical-v7-v9-capture-index.json` lists all **33** captured commands, their original recipe/stdout/stderr/native-exit files and current SHA-256 checksums of those preserved bytes. Every stdout/stderr checksum matches the old `diagnostic-ledger-v7-v9.jsonl`; each native-exit file agrees with its ledger value.

## Native nonzero exits: seven preserved failures

| Capture | Exit | Observed failure |
| --- | ---: | --- |
| `v7-full-01` | 1 | Invalid SID fixture in append-only state test; native target opens requesting `WRITE_OWNER` were denied. Two target tests skipped for fixture access, plus the helper-only PE skip. |
| `v7-full-02` | 1 | `SetSecurityInfo` `P` to `PAI` same-handle SDDL mismatch; one target test failed, two fixture tests skipped, plus the helper-only PE skip. |
| `v7-full-04` | 1 | Nt-only target path dropped the auto-inherited `AI` control bit, causing installed and restore readback mismatch. |
| `v7-sddl-01` | 1 | Focused group projection/readback mismatch. |
| `v7-sddl-02` | 1 | Focused auto-inheritance control-bit mismatch. |
| `v8-full-01` | 1 | Dense installed ACL projection duplicated ACEs; the native probe also had SDDL projection mismatch despite binary restoration. Two tests failed. |
| `v9-sacl-03` | 1 | Build failed because `windows.SUCCESSFUL_ACCESS_ACE_FLAG` was undefined. |

These are historical failures; later exit-0 runs do not erase them. The complete original output and exact exit files remain under their listed names in the index.

## Exit 0 with diagnostic limits

`v7-binary-01`, `02`, and `03` returned 0 while their logs showed native preimage/restored bytes unequal, four ACE inherited flags changing `00` to `10`, and a difference between `GetSecurityInfo` projection and `NtQuerySecurityObject`. `v7-binary-05` and `v8-focused-02` recorded that a parsed installed SDDL binary differed from its native installed form. The latter observations coexist with later binary-equal original restoration; they are not blanket pass claims for all descriptor fields.

`v7-ntset-01` and `02` returned 0 for narrow NtSet probes but did not record native binary equality. `v7-binary-04` first recorded binary-equal restoration; `v7-binary-05`, the later v8/v9 final suites, and v10 have more specific proof in their own receipts. `v9-sacl-01` and `02` passed the expected `UNAVAILABLE` SACL branch with Win32 1314; `v9-sacl-04` passed a **synthetic** readable-SACL digest test. A readable-SACL OS fixture was not proven.

Successful rejection assertions inside the full suites are planned negative tests and appear as `PASS`, not command failures. `TestPEExecutionProbe` skips are helper-process-only behavior; the index lists skips per capture. Some early v7 full runs also skipped actual target tests because fixture access failed, and the table above identifies them separately.

## Gaps and later integration

`v8-full-02` is a numbered gap with **no** recipe, stdout, stderr, or native-exit file. Its execution status is unknown. Per-capture v7/v8 and intermediate v9 source hashes were not recorded; the final-v9 source manifest must not be projected backward. No original exit or source hash has been reconstructed.

The parent-owned `combined-067-boot` integration receipt is newer than v10 and is outside this historical seal. Its C-drive fixture roots currently inherit 208 ACEs; this differs from the v10 D-drive fixture roots and explains its test-helper cleanup and fixed-four-ACE assumption failures. Its raw failure remains in the parent C57 maintenance receipt. The six boot6 source files were not changed for this index.
