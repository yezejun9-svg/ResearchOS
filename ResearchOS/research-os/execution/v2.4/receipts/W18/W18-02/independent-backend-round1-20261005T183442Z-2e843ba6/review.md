# W18-02 independent backend review round 1

Verdict: NEEDS_FIX. Candidate 4d7ba34529be23afba016bdef575d88781cdf562; main HEAD 05dbd68c16ccb3c73d419d08ab8f8dfdb0b2acbb. Reviewer /root/w1802_review is not author /root/w1101_impl.

## Confirmed finding: W1802-R1-001 (P1)

A successfully restored workspace cannot be backed up again. internal/domain/backup_workspace.go:124-125 places every restored workspace inside destination/workspaces/<ref hash>. internal/host/backup_windows.go:28-29 rejects all overlaps between the workspace and its current data root. Therefore the normal production CLI create command rejects every restored ACTIVE workspace even when the backup output is outside both directories.

Independent reproduction uses only a Go test overlay of the existing production CLI integration test. Immediately after restore --as-data-root succeeds, execute create --db <restoredRoot>/researchos.sqlite --out <sibling>/backup-after-restore --key-file <separate key> --root <repo>. Expected successful encrypted backup; actual exit 1: BACKUP_WORKSPACE_SNAPSHOT_FAILED ... BACKUP_WORKSPACE_RECURSION. See rebackup.command.json, rebackup.stdout.txt, rebackup.stderr.txt, overlay.json and independent_rebackup_windows_test.go. This disables continued backup protection for the restored project and any future progress in its new workspace.

Suggested repair: explicitly permit the exact restored workspace subtree derived from the same wsref and verified current Host pin, while retaining rejection of workspace roots that include the Host vault/identity/database or overlap the backup output. Add restore -> backup -> second restore coverage; ensure the second restore has the same project/session/Goal/Task/workspace ref and no source mutation. Do not broadly remove data-root protection.

## Validated current behavior

- All 9 scoped source files have identical raw bytes in main, candidate worktree and candidate commit; before.json records hashes. No source drift after review.
- Pinned Go binary SHA-256 verified; version go1.27.1 windows/amd64. Actual test argv, environment settings, stdout, stderr, exit status and skip list are retained per command. No skips.
- Baseline TestW1802WorkspaceRestorePreservesEffectAndSessionFences and TestW1802ProductionBackupCLIWorkspaceContinuation pass; exactly 4 W18-02 assertions. Production Host, real SQLite and compiled ops/backup CLI; business data and chooser callback are FIXTURE.
- Five regression tests pass: TestW1801BackupContract, TestW18RestoreNative, TestW18NegativeRecovery, TestW18Boundaries, TestW18CLI. This covers authenticated manifest/content, reference/inventory/cursor recovery, source database preservation, failed migration and no overwrite, credential invalidation, effect reconciliation, cancellation and local CLI compatibility.
- Additional independent overlay passes: MaxDirs=1 rejects a real workspace containing 2 directories with BACKUP_WORKSPACE_DIRECTORY_LIMIT and returns no partial snapshot; source SQLite bytes and source workspace file bytes are unchanged by the production restore command.
- Static review confirms encrypted workspace index and blobs share AES-GCM authenticated content and HMAC manifest, missing active-workspace snapshot fails explicitly, restore validates inventory/bindings/hash/size and orphan blobs, new paths are staged and RESTORE_PENDING before fresh Host pins, activation is transactional, failed pin retains pending status. Existing file oversize and recursive output counterexamples pass.
- Notification fixture correction now uses the real production notice ID and dedup key; regression verifies unchanged logical notice state.

## Limits and excluded claims

This is an independent backend construction review, not W18-02 acceptance, A12/U06 acceptance or formal 42-case acceptance. W13 workspace read/write/diff and client_workspace security audit are explicitly excluded; dependencies were read only to understand backup fences. No provider calls, live business database, native chooser click, real Desktop GUI flow, protected credential reprovision UI flow, new OS principal/machine migration, or complete user-level task continuation was exercised. Typed session snapshot uses the production protocol document but fixture model/build refs. PID reuse was checked through existing lease/fresh-observation fences, not by a live recycled-PID process experiment. Script exact dispatcher routing was statically read; no current GUI/dispatcher receipt is claimed. Directory/file/byte/path limits were inspected, with file-size and directory-count dynamic negatives; not every numeric boundary or concurrent tree mutation was executed. No crash/disk-full injection during final report publication was run.

No production or test source was edited, no commit/push/deploy was performed, no existing evidence was deleted. Overlay source files are retained as reproducible evidence. Further implementation is required for W1802-R1-001 before a new backend review, and full card evidence remains independently necessary.
