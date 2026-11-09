$ErrorActionPreference='Stop'
$p='D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/internal/domain/runtime_qualification_failure_windows_test.go'
$a=Get-Content -LiteralPath $p -Encoding utf8
foreach($range in @(@(183,300),@(411,462),@(902,1026))){for($i=$range[0]-1;$i -lt $range[1];$i++){ '{0}: {1}' -f ($i+1),$a[$i] }}
rg -n 'requestHash|request_hash|provider_response_hash|ReadQualification|WriteFile|persistRuntimeModel|func .*Fact|func .*SSE' 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/internal/domain/runtime_broker_windows.go' 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/internal/domain/runtime_model_transport_windows.go'
Get-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/internal/domain/runtime_command_queue_windows_test.go' -TotalCount 356 -Encoding utf8
exit 0
