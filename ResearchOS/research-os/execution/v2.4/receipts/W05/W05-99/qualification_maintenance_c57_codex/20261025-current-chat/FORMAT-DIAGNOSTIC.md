# 009 format scope diagnostic

`009.recipe.json` mistakenly invoked package-wide `go fmt ./internal/domain ./ops/backup`, which formatted files outside the frozen C57 allowlist. The raw formatter path list is retained in `009-fmt.stdout.raw`; stderr and the compile probe are retained separately. A post-command `git diff --stat` and `git diff --name-only` were inspected before recovery; this command output was captured by the session tool but was not written to a separate raw file. The formatter path list is the durable pre-recovery file inventory.

No agent other than this C57 worker used the C57 worktree. I had made no edits in the 20 paths printed in `010.stdout.raw` before command 009. `restore_format_only.py` rewrote only those paths with exact `git show HEAD:path` bytes, without reset/clean. `011.stdout.raw` records SHA256 and exact byte equality to HEAD for every restored path, plus the frozen 40 inherited Source43 pins; `011.stderr.raw` is empty and command native exit was 0. The deliberately edited C57 allowlist files were excluded from the restore and retain their implementation changes.

Further formatting uses explicit filenames only. This diagnostic is append-only and does not claim source acceptance.
