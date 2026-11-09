$ErrorActionPreference='Stop'
Get-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015/internal/domain/runtime_command_queue_windows_test.go' | Select-Object -First 115
rg -n 'func Test.*Mu|RESEARCHOS_MU|MU_WORKER|os.Getenv' 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015/internal/domain/runtime_command_queue_windows_test.go'
Get-FileHash -LiteralPath 'D:/作品集/ResearchOS/research-os/.local/w0599-main-stream-integration-r268/mu-worker.mjs' -Algorithm SHA256 | ConvertTo-Json

