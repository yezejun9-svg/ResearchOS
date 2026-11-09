# Normal local runtime host setup: phase 1 candidate

Candidate: a57ca3e33b4e9d7c9351cd4143f8914c936f6bda
Base: 292ad860f9e76cf2795d5a3010da1d114d01ff56
Worktree: .local/worktrees/w05-normal-runtime-host-20261012
State: IMPLEMENTED_OFFLINE_VERIFIED_PENDING_INDEPENDENT_REVIEW

The normal control startup now owns one coordinator even without a private coordinator JSON. A committed credential-free numeric-loopback configuration plus a project session is reconciled through the current Windows Host binding and existing configuration receipts. Assets come from runtime beside control.exe or --runtime-assets-dir, validated against the Mu build producer metadata. Missing assets affect that model branch, leaving configuration/history usable. No production fixture environment or test-only setup API is used.

Preparation atomically creates a REGISTERED runtime, sealed LIVE dispatch profile, grounded observed requirement, qualification-only goal, DRAFT runtime_qualification task/context, and the existing trusted qualification plan. Existing sealed profile/plan are the persistence index. Reconciliation restores exact runtime identity, rejects drift/revocation, provisions only Owner-root scheduler/executor principals and issues short-lived in-memory credentials. Read snapshots cover all existing production route/provider/scheduler readers. The original admission, independence, budget ancestry, UNKNOWN, status and qualification checks remain effective. No new migrations, dispatch queue, public setup endpoint, or acceptance bypass.

Evidence:
- attempt05: initial offline domain/host cases pass (synthetic assets never executed).
- attempt06: real Windows Host + production resource hashes + ordinary typed configure/session + coordinator Scan + same-runtime restart pass; assets read only, no provider/model execution.
- attempt07: 13 top-level existing configuration/credential/native qualification/S1 regression tests pass (fixture provider/native child where applicable; not LIVE model qualification).
- attempt10: final Host suite, including real production resources, passes 3 top-level tests. Combined command overall FAILED because the host-only test flag was also forwarded to the domain test binary; this failure remains recorded.
- attempt11: corrected domain command passes 4 top-level tests plus 8 subtests. TestRuntimeMuUnknownNeverRetries SKIPPED because its separate immutable execution bundle was not configured; not counted as passed. Existing session failure/cancel/UNKNOWN projection regression passes.
- attempt12: final control executable build passes.
- attempt13/control-offline-smoke.json: final compiled control process starts without coordinator JSON in both missing-assets and real-assets modes. Actual Windows native bootstrap, ordinary HTTP host.configure and host.status succeed. The smoke creates no project; DB census independently records 0 runtime/Run/Effect/Acceptance/BudgetLedgerEntry. Full project/session setup is covered by production Host tests, with a fixture chooser.

Earlier unsuccessful attempts preserved: attempt01 toolchain absent from PATH; attempt02 sparse worktree missing dependencies; attempt04 capped-budget test fixture invalid enforcement; initial smoke missing web build. Remediated environment/test input only. First smoke attempt09 preserved separately; attempt13 is final compiled source.

Resources supplied by parent (read-only): node SHA256 5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6; bundle SHA256 2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441. Parent resource manifest SHA256 7440d892f14704d50e184685ce71ddeb570fd77e1c9c7ac4d826ebb18ec00ca3. Resource status BUILT_NOT_QUALIFIED.

Boundary: phase 2 must begin a bounded qualification Run through existing gates, collect native/provider proof, secure an actual independent VERIFIER acceptance, and apply the existing approval/binding path. This candidate does not call a model, create AVAILABLE status, manufacture independent verification, prove Jev protected holdout, or complete W05/Main24. It does not change desktop/web/CLI or Canon/step_status. No manual DB write or service provisioning harness is needed for the phase-1 production flow.

Additional cold-start verification requested by parent: attempt14 runs the final compiled control in a fresh data root with the real packaged assets and its normal non-nil coordinator. It performs actual OS bootstrap, host.configure, actual Shell folder chooser (only the test control PID's dialog), public typed workspace.register, LIVE project.bootstrap, then session.create. All complete. A read-only database census after shutdown finds exactly 1 committed session, 1 runtime binding, 1 qualification plan, REGISTERED runtime, DRAFT qualification Task, and zero Run/Effect/dispatch/Acceptance/BudgetLedgerEntry. No injected chooser seam, service setup harness, direct DB writes, pre-provisioned session/profile, or nil/fake runtime was used in this case. Existing checkClientCreationBinding explicitly validates committed configuration provenance and workspace without demanding an already-prepared runtime; no circular cold-start dependency exists. See control-cold-session-smoke.ps1, control-cold-session-smoke.json, verify-cold-session-census.py, and control-cold-session-db-census.json.
