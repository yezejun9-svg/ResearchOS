$ErrorActionPreference='Stop'
$reads=@(
@{path='D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/internal/domain/runtime_broker_windows.go';start=105;end=198},
@{path='D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/internal/domain/runtime_broker_windows.go';start=275;end=370},
@{path='D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/internal/domain/runtime_coordinator_windows.go';start=600;end=719},
@{path='D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/internal/domain/runtime_command_queue_windows.go';start=424;end=630},
@{path='D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/adapters/runtime/bridge_windows.go';start=520;end=640})
foreach($spec in $reads){'FILE '+$spec.path;$a=Get-Content -LiteralPath $spec.path -Encoding utf8;for($i=$spec.start-1;$i -lt [Math]::Min($spec.end,$a.Count);$i++){'{0}: {1}' -f ($i+1),$a[$i]}}
$author='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision02_source_codex/20261015-current-chat'
foreach($name in @('diagnostic-ledger.json','capture-gap-and-skip-supplement.json')){'AUTHOR '+$name; Get-Content -LiteralPath (Join-Path $author $name) -Raw -Encoding utf8}
exit 0
