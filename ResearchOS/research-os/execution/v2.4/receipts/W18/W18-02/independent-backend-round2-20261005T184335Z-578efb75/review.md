# W18-02 independent backend review round 2

Verdict: PASS_IN_SCOPE. Finding W1802-R1-001 is CLOSED_VERIFIED for fix commit 0d7d244056438a71a4111f2860d669c5ee52fe5e. This is not whole-card, U06 or A12 acceptance.

The worktree HEAD at review is c11cb618c3d8e21dd8f26eaeada1f1c4dcf61047. All 9 scoped backup files exactly match the bytes of commit 0d7d2440. No source drift occurred during the review. The original round 1 immutable report and every hashed raw evidence file remain unchanged.

## Finding closure

Host.SnapshotWorkspace now locates a non-revoked pinned root first. Its data-root overlap exception then requires the pinned ref to equal the requested wsref and the normalized absolute path to exactly match BackupWorkspaceDestination(dataRoot, ref). Existing file identity, reparse checks, ownership and content bounds remain in the backup path. The exception does not admit arbitrary data-root children or outputs inside the backed-up workspace.

The exact byte-for-byte original round 1 overlay was run again against the repaired candidate. The previously failing create after restore now succeeds (original-rebackup exit 0). The unmodified candidate integration test additionally executes compiled production CLI create -> restore -> external rebackup -> second restore into a fresh data root. It verifies unchanged project/session/Goal/Task/workspace identity, typed session model/build refs, fresh Host path and usable pin, restored file content and unchanged original source DB/file. Both W1802 tests pass, producing 5 W18-02 assertions.

## Independent negative checks

A second overlay adds checks only around SnapshotWorkspace on the restored fixture root. A mismatched wsref is rejected; output inside the restored source is rejected; a real Windows directory junction is rejected with PATH_OUT_OF_SCOPE; revoking the current root pin causes BACKUP_WORKSPACE_ROOT_NOT_PINNED. The existing newly added test also registers a real unrelated data-root child with its own valid Host pin and confirms the backup exception rejects it. All checks pass without skips. The temporary test junction was removed directly, and Go testing cleaned its temporary fixture roots.

## Commands and evidence

baseline.command.json / baseline.stdout.txt / baseline.stderr.txt: two W1802 tests, exit 0.
original-rebackup.command.json / original-rebackup.stdout.txt / original-rebackup.stderr.txt: exact round 1 rebackup test overlay, exit 0; original and copied overlay hashes recorded.
pin-bounds.command.json / pin-bounds.stdout.txt / pin-bounds.stderr.txt: independent exception boundary checks plus production second roundtrip, exit 0.

The Go binary is the pinned go1.27.1 windows/amd64 executable with SHA-256 d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490. Command records include argv, cwd, explicit GOTOOLCHAIN/GOENV/GOPATH/GOCACHE/RESEARCHOS_GO, raw stdout/stderr and exit codes. All runs use count=1 and no skipped tests.

## Scope limits

Only the original 9 backup files and the backup fix tests were reviewed. W13 workspace permission/read/write audits, GUI, newly added CLI entrypoints, exact dispatcher integration, provider qualification and full card acceptance are excluded. Business data and native chooser callback are FIXTURE; SQLite, Host pinning, filesystem operations and compiled backup CLI are real Windows execution. No live user data, native GUI chooser click, Desktop context continuation, credential migration interaction, or formal 42-case run is claimed. The second restore validates backend continuation state and authorization, not a live model completing the pending Task. File identity checks were inspected; this round does not claim a concurrent replacement race proof. W18-01 regression evidence from round 1 remains preserved and is not relabelled as new whole-product qualification.

No business/test source was modified, no commit/push/deploy occurred, no old evidence was deleted. Root may now integrate the reviewed fix and perform its independent GUI work; resulting main source hashes must match this reviewed candidate before reusing this backend verdict.
