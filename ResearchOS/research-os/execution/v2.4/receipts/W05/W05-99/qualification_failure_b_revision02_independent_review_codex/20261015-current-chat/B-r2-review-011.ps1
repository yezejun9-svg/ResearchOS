$ErrorActionPreference='Stop'
git -C 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015' status --porcelain=v1
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
git -C 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015' rev-parse HEAD 'HEAD^{tree}'
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
git -C 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015' diff f48fca0e HEAD -- adapters/runtime/bridge_windows.go internal/domain/runtime_broker_windows.go internal/domain/runtime_command_queue_windows.go internal/domain/runtime_coordinator_windows.go
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
git -C 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015' diff f48fca0e HEAD -- internal/domain/runtime_command_queue_windows_test.go
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
$p='D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/internal/domain/runtime_qualification_failure_windows_test.go'
$a=Get-Content -LiteralPath $p -Encoding utf8
for($i=462;$i -lt 562;$i++){ '{0}: {1}' -f ($i+1),$a[$i] }
exit 0
