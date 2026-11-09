# Independent final combined fixture audit

Decision: **APPROVED_FIXTURE_INTEGRATION_ONLY**. Pending blockers: none. Formal/product increment: 0.

Observed **21 top-level tests + 85 subtests passed**, 106 matching RUN records, no FAIL/SKIP markers and three successful packages:

| Package | Top-level | Subtests |
|---|---:|---:|
| adapters/runtime | 12 | 57 |
| internal/domain | 7 | 28 |
| internal/host | 2 | 0 |

All 27 registered input hashes match current files. The exact 16 source inputs match B1 rev6 (eight C overlay files) and frozen B2 (eight direct worktree files). The overlay has exactly eight mappings. Both final manifest hashes are unchanged. Full repository source keys and receipt hashes are in REVIEW.json.

The pinned controller receipt records COMPLETED_OWNED_JOB_STOPPED, root exit 0, original Job assigned before resume, original root signaled, Job active count zero and stop proved. Errors, force attempts, timeout, raw limit overflow and input drift are absent. Cumulative Job processes: 918; this is not the simultaneous active count (scope limit 48). Elapsed time: 40.642343 seconds.

Scope SHA256: `6473485a15c8208cf16a13104f571a65558dbe504f31798bf039ff2aa87d98c1`.

Stdout: 12171 bytes, SHA256 `4aa280a070b6354378f762b9664840bf716ac9943d53b8245702a1d784423046`. Stderr: 0 bytes. RESULT SHA256: `c9734a26df81e2b04375a8278a19a65d3affb09e84e7926aeb217c112df76bce`.

The /FAIL subtest passes; its name is not a failed test. CONSUMED.json preserves the launch-intent unknown state and is followed by the matching terminal RESULT; it does not authorize replay. B2's frozen manifest retains its prior B1 test provenance, while this combined scope independently binds final B1 rev6.

No tests, Native, model or probes were launched by this reviewer. This evidence supports fixture integration of these exact pins only. It does not establish Native permission qualification or product acceptance. B3 and separately authorized synthetic runtime checks remain necessary; old failed/consumed attempts remain immutable.

