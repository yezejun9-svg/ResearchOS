$ErrorActionPreference='Stop'
$W='D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-20261015'
git -C $W diff f48fca0e4013bda19913a34d91da0cd23157a08b HEAD -- internal/domain/runtime_broker_windows.go internal/domain/runtime_command_queue_windows.go internal/domain/runtime_coordinator_windows.go adapters/runtime/bridge_windows.go
$p="$W\internal\domain\runtime_qualification_failure_windows.go";$lines=Get-Content $p;0..240|ForEach-Object {"$($_+1): $($lines[$_])"}
Get-Content -Raw "$W\adapters\runtime\qualification_failure_proof_windows.go"
