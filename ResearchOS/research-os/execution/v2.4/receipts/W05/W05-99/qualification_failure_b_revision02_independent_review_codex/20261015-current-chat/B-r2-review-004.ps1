$ErrorActionPreference='Stop'
rg --files 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision02_source_codex/20261015-current-chat' | Select-String '030|109|110'
Get-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/adapters/runtime/qualification_failure_proof_windows.go' -Raw -Encoding utf8
rg -n '^func ' 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/internal/domain/runtime_qualification_failure_windows.go' 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/internal/domain/runtime_qualification_failure_windows_test.go' 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/internal/domain/runtime_command_queue_windows_test.go'
exit 0
