$ErrorActionPreference='Stop'
$p='D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/internal/domain/runtime_qualification_failure_windows.go'
$a=Get-Content -LiteralPath $p -Encoding utf8
for($i=458;$i -lt $a.Count;$i++){ '{0}: {1}' -f ($i+1),$a[$i] }
exit 0
