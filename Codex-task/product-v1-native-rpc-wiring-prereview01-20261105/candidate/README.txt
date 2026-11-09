B2 Native RPC wiring source candidate only.
Shared API v2 pinned in MANIFEST. Distinct RPC V3 profile; Host factory RPC only; per-turn owner/source/worker/process/epoch/cancel fence; exclusive synced marker and LIVE LOG artifact.
Source tests added for RPC/legacy seal, normal-home validation, and journal exclusivity. No Go tests, Native, auth, model, CLI, or probe executed.
Root to run combined B1+B2 Go overlay compile and targeted fake tests under original f13.
Initial local gofmt attempt was denied by sandbox; exact authorized gofmt retry succeeded through escalated review.
