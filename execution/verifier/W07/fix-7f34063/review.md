# W07 scope fix independent review — PASS (development gate only)

Reviewed `7f3406317c55d8743b491ea69f9987b1645d7653`; resolves **W07-VERIFY-P1-001** from the separately preserved `5879967` FAIL package.

The new guard at `internal/domain/evidence_verification.go:32` restricts the judgement endpoint to SIMULATED Evidence backed by a SIMULATED/FIXTURE SOURCE_SNAPSHOT. Independent public-API probes passed **14 / 14** subtests, with no direct database mutations:

- OBSERVED/LIVE targets: VERIFIED, CONTRADICTED and UNAVAILABLE all return 422; the complete Evidence object remains unchanged.
- SIMULATED/FIXTURE targets: all three statuses return 200, persist the requested judgement and advance revision.
- SIMULATED targets with LIVE snapshots: all three statuses return 422 with no Evidence changes.
- SIMULATED/FIXTURE MANIFEST instead of SOURCE_SNAPSHOT: all three statuses return 422 with no Evidence changes.
- Both directions of Evidence/snapshot OBSERVED versus SIMULATED classification mismatch return 422 at the public creation endpoint.

The test command exits 0. The worktree is clean at the reviewed head; Git blob hashes match the author's scope-fix receipt. The source delta is limited to the scope guard and associated tests/receipt. Earlier passing authority, currentness, binding and lifecycle tests were not redundantly rerun.

This is a **fixture development gate PASS**, not construction acceptance, ordinary LIVE verification or semantic accuracy. LIVE-labelled test snapshots contain only local synthetic temporary-file data. The endpoint still requires UNVERIFIED targets; re-review lifecycle remains outside this change.

Exact commands, immutable source checks and raw responses are in `command-receipt.json`, `source-audit.json`, `probe-output.txt` and the indexed JSON files.
