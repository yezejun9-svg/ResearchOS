# Source derivation and trust boundary

This proposed revision derives from immutable `execution/v2.4/receipts/W05/W05-99/mu_sdk_trusted_qualification_host_source_codex/991a41da6cb146d9a5fae91c438f6d07`. The original named-files Source compiled, but this changed revision has not been built or executed. The Main source base inspected was `adc460c2138528f163f7fdab5e8d81dde157b7fb`.

| Existing current source | This Source | Preserved behavior / deliberate difference |
|---|---|---|
| `tests/e2e/live_setup/main.go:74-136`, `internal/host/bootstrap.go:42-100` | `hostapi.go:40-53` | Reopen same isolated DB/Host under OS identity and data-root lease. Refuse to create an OWNER if CLI bootstrap did not do so. |
| `apps/control/main.go:165-248`, `apps/control/discovery.go:9-37` | `hostapi.go:61-106`, `execute.go:184-249` | Bind an actual loopback listener and native Host, then write actual PID/URL/data-root/stable Host ID discovery. No claimed port is written before `net.Listen`. |
| `tests/e2e/live_setup/plan.go:19-210,374-405` | `prepare.go:19-158`, `execute.go:145-169` | Reuse v1 project writes, sealed profile Artifact, owner-only frozen plan, purpose-specific routes. Target project and DRAFT goal must already exist from real CLI init; new Goal is only for independent qualification. No new project or static W14 candidate. |
| `tests/e2e/live_setup/qualify.go:182-229` | `execute.go:54-75,184-249` | Split `BeginRuntimeQualification` from `RunAdmitted`; persist actual Run/epoch/private lease and require a later explicit GO. Native dispatch is once-fenced before calling `RunAdmitted`. |
| `tests/e2e/live_setup/qualify.go:45-180` | `execute.go:250-283` | Use VERIFIER HTTP acceptance and `/runtimes/{id}/qualify` before OWNER ordinary-purpose authorization. No direct status/receipt DB write. |
| `internal/domain/runtime_coordinator_windows.go:258-333`, `apps/control/main.go:213-248` | `execute.go:232-249` | Start the ordinary-task coordinator only after qualification succeeds and after checking no ordinary READY Task already exists. The current coordinator never scans `runtime_qualification` tasks. |
| `internal/domain/runtime_qualification.go:18-33,47-163` | `prepare.go:75-158` | Keep cost bound explicitly `null`, provider MODEL `upper_bound=null`, and require unchanged `UNLIMITED_AMOUNT` / `ALLOW_AND_RECORD` ancestry. No fabricated zero price or additional provider allocation. |

The frozen public profile template is input, not authority by itself: the helper verifies file SHA-256 and actual Node/bundle bytes, then derives runtime ID/technical hash and seals the final profile through the real content/Artifact API. The Root controller must independently review those actual sealed bytes, final Source bytes, provider route, the Host Job tree, and the total 300-second/three-request cap.

## Revision-specific repairs

| Finding | Revised Source | Effect and limit |
|---|---|---|
| GO support-record path reread after separate pin | `execute.go` `verifiedBytes`, `readPinnedObject`, `readGO` | Each of the four Root support JSON objects is decoded from the same raw buffer whose length/hash matched its pin. READY, discovery and coordinator are verified once but are externally consumed later; Root must keep these paths stable. |
| Seed pin then profile/Node/bundle reread | `main.go` `readPinnedSeedFile`, `seed.ProfileRaw/NodeRaw/BundleRaw`; `prepare.go` `preparedProfile` | Profile derivation and build/bundle hashes use the verified buffers. Later native launch still uses executable/bundle paths; path TOCTOU remains OPEN. |
| Workspace/data-root layout contradicted observer v2 | `main.go` `readSeed` | Require data root inside `repo/.local`, workspace exactly `<data_root>/workspace`, and old vault disjoint. `prepare.go` still requires exactly one pinned `evidence.txt` regular file, no writes. |
| Tool policy exceeded v8/v9 contract | `prepare.go` `preparedProfile`; `profile.template.json` | Tool calls 1, read/write byte ceilings 4096, read_paths only evidence.txt, write_paths empty array. Model-call limit stays 2 per ordinary Run; qualification remains 1. Root owns runner `{}` to `[]` correction. |
| Concurrent prepare checked state before data-root lease | `prepare.go` `prepare` | State absence check now occurs after `openEnvironment` acquires exclusive lease, before PREPARE claim. No automatic retry of partial state. |
| Package-path build fails at nested module | `HANDOFF.md` | Build from Main root by four absolute named Go files. Original package failure and original named-files success are cited; this revision has not been compiled. |
