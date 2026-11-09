$ErrorActionPreference='Stop'
$b='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-cli-s04-author'
$w='D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-cli-20261104'
$changes=Get-Content -LiteralPath ($b+'/source-05.json') -Raw|ConvertFrom-Json
$writes=@{}
foreach($c in $changes){$p=Join-Path $w $c.path;if((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() -ne $c.baseline_sha256){throw 'source drift'};$s=[IO.File]::ReadAllText($p).Replace("`r`n","`n");foreach($r in $c.replacements){if($s.IndexOf($r.old) -lt 0 -or $s.IndexOf($r.old) -ne $s.LastIndexOf($r.old)){throw 'replacement cardinality'};$s=$s.Replace($r.old,$r.new)};$writes[$c.path]=$s+$c.append}
$pins=foreach($rel in $writes.Keys){$p=Join-Path $w $rel;[IO.File]::WriteAllText($p,$writes[$rel],[Text.UTF8Encoding]::new($false));[ordered]@{path=$rel;sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}}
$pins|ConvertTo-Json -Depth 4|Set-Content -LiteralPath ($b+'/source-05.result.json')
