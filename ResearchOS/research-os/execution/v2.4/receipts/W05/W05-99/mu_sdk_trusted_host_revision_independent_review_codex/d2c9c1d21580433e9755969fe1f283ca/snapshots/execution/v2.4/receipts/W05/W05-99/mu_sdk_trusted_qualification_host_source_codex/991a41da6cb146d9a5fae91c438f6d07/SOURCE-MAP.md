# Source derivation and trust boundary

This proposed helper is new Source under `execution/v2.4/receipts/W05/W05-99`. It has not been installed into Main and has not been compiled or executed. The source base inspected was Main `adc460c2138528f163f7fdab5e8d81dde157b7fb`.

| Existing current source | This Source | Preserved behavior / deliberate difference |
|---|---|---|
| `tests/e2e/live_setup/main.go:74-136`, `internal/host/bootstrap.go:42-100` | `hostapi.go:40-53` | Reopen same isolated DB/Host under OS identity and data-root lease. Refuse to create an OWNER if CLI bootstrap did not do so. |
| `apps/control/main.go:165-248`, `apps/control/discovery.go:9-37` | `hostapi.go:61-106`, `execute.go:183-243` | Bind an actual loopback listener and native Host, then write actual PID/URL/data-root/stable Host ID discovery. No claimed port is written before `net.Listen`. |
| `tests/e2e/live_setup/plan.go:19-210,374-405` | `prepare.go:19-153`, `execute.go:144-168` | Reuse v1 project writes, sealed profile Artifact, owner-only frozen plan, purpose-specific routes. Target project and DRAFT goal must already exist from real CLI init; new Goal is only for independent qualification. No new project or static W14 candidate. |
| `tests/e2e/live_setup/qualify.go:182-229` | `execute.go:54-72,183-243` | Split `BeginRuntimeQualification` from `RunAdmitted`; persist actual Run/epoch/private lease and require a later explicit GO. Native dispatch is once-fenced before calling `RunAdmitted`. |
| `tests/e2e/live_setup/qualify.go:45-180` | `execute.go:244-277` | Use VERIFIER HTTP acceptance and `/runtimes/{id}/qualify` before OWNER ordinary-purpose authorization. No direct status/receipt DB write. |
| `internal/domain/runtime_coordinator_windows.go:258-333`, `apps/control/main.go:213-248` | `execute.go:226-249` | Start the ordinary-task coordinator only after qualification succeeds and after checking no ordinary READY Task already exists. The current coordinator never scans `runtime_qualification` tasks. |
| `internal/domain/runtime_qualification.go:18-33,47-163` | `prepare.go:74-153` | Keep cost bound explicitly `null`, provider MODEL `upper_bound=null`, and require unchanged `UNLIMITED_AMOUNT` / `ALLOW_AND_RECORD` ancestry. No fabricated zero price or additional provider allocation. |

The frozen public profile template is input, not authority by itself: the helper verifies file SHA-256 and actual Node/bundle bytes, then derives runtime ID/technical hash and seals the final profile through the real content/Artifact API. The Root controller must independently review those actual sealed bytes, final Source bytes, provider route, the Host Job tree, and the total 300-second/three-request cap.
