# C57 boot6 v10 owned-source result

## Result

The exact six owned boot6 source files are ready for parent integration. The Windows package tests and Linux crossbuild exited 0. The source remains untracked and was neither staged nor committed. This is source and disposable-fixture evidence, not formal C57 acceptance.

The dense plan writer now admits `plan.json` through the pre-existing 32 MiB read cap; every other managed record retains the 256 KiB writer cap. The 22-target, 67-ancestor fixture with a 208-ACE descriptor serialized to **1,977,761 bytes**, passed protected create and pinned-handle read, and failed the obsolete 256 KiB read limit as expected. This proves capacity and IO for a synthetic inventory; it does not prove production ACL preservation by itself.

The separate owned native fixture installed 208 varied ACEs plus two management ACEs, ran production `setTargetDescriptor` to install a fence and restore the captured native preimage, and verified the actual same-handle `NtQuerySecurityObject` bytes after restoration. The 7,628-byte native preimage was binary equal after restoration (SHA-256 `a08e3946121679f9870aefec994fa05c2a61ba095957353ff8db1ca9720659e4`); ACE count/order/flags and descriptor control `0x9004` matched. The generated allow trustees were unrelated synthetic SIDs and did not deny the current management token.

## Evidence

| Check | Result | Raw evidence |
| --- | --- | --- |
| Windows package tests, `-count=1 -v` | Exit 0; one intentional PE helper-only skip | `final-v10-windows-tests.*` |
| Dense plan and native ACL tests | Both PASS within full run | `final-v10-windows-tests.stdout.raw` lines 46-51 |
| Linux amd64 crossbuild | Exit 0 | `final-v10-linux-crossbuild.*` |
| Exact six-file source manifest | SHA-256, bytes and lines recorded | `final-v10-six-source-manifest.json` |
| Six-file full additive patch | All six `git diff --no-index` exits 1, expected for new files | `final-v10b-six-new-files.diff`, `final-v10b-diff-exits.json` |
| Patch staging feasibility, read-only | `git apply --cached --check --whitespace=error` exit 0; no staging performed | `final-v10b-diff-check.*` |

The first `final-v10-six-new-files.diff` was reencoded with CRLF by PowerShell `Out-File`; its whitespace check exited 128. Those failed raw files and `diagnostic-ledger-v10.jsonl` remain preserved. The corrected `v10b` patch copied raw Git stdout bytes and passed without changing source.

## Evidence boundary

Current proof covers compiled source, pure-contract tests, owned Windows native fixtures, an owned SQLite/WAL fixture, and a disposable PE/script denial probe. It does not include actual production targets, a distinct privileged management SID on a real business file, a readable-SACL OS positive case, a real `FullRestart`, an actual C transaction, independent final review, or formal parent/card acceptance. Formal acceptance count remains zero. Earlier v5/v6/v7-v9 receipts and diagnostic failures remain historical and were not reset.

The owned temporary root has no new test residue; the pre-existing `diagnostic-acl-v6c.tmp` from an earlier diagnostic remains because cleanup was blocked by automatic approval review. No original ACL, database, restart state, VPS, or product target was changed.
