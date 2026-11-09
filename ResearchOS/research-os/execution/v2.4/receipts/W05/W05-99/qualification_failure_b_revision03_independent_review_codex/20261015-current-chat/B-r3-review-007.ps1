$ErrorActionPreference='Stop'
Get-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015/internal/domain/runtime_qualification_failure_windows.go' | Select-Object -Skip 540 -First 145
Get-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015/internal/domain/runtime_qualification_failure_windows.go' | Select-Object -Skip 760 -First 68
Get-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015/internal/domain/runtime_qualification_failure_windows_test.go' | Select-Object -Skip 565 -First 140
Get-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015/internal/domain/runtime_qualification_failure_windows_test.go' | Select-Object -Skip 1176 -First 210
rg -n 'func Test.*(Mu|Qualification|Reparse)' 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015/internal/domain/runtime_command_queue_windows_test.go' 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015/adapters/runtime/qualification_failure_proof_windows_test.go'
Get-Volume | Select-Object DriveLetter,SizeRemaining,Size | ConvertTo-Json

