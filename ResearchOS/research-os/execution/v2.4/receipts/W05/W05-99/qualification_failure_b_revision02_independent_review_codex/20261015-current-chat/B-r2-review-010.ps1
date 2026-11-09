$ErrorActionPreference='Stop'
$p='D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/internal/domain/runtime_qualification_failure_windows_test.go'
$a=Get-Content -LiteralPath $p -Encoding utf8
foreach($range in @(@(1,182),@(301,768),@(1027,1400))){for($i=$range[0]-1;$i -lt [Math]::Min($range[1],$a.Count);$i++){ '{0}: {1}' -f ($i+1),$a[$i] }}
exit 0
