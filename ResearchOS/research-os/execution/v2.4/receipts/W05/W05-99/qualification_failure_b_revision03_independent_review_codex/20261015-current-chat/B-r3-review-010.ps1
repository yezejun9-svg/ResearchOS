$ErrorActionPreference='Stop'
rg -n 'func muBrokerFixtureProgram|MU_WORKER|RESEARCHOS_.*MU|LookupEnv|mu-worker.mjs' 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015/internal/domain/runtime_broker_windows_test.go'
Get-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015/internal/domain/runtime_broker_windows_test.go' | Select-Object -First 155

