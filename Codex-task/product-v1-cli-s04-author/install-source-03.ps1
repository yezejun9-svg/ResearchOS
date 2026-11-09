$ErrorActionPreference='Stop'
$b='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-cli-s04-author'
$w='D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-cli-20261104'
$c=Get-Content -LiteralPath ($b+'/source-03.json') -Raw|ConvertFrom-Json
$p=Join-Path $w $c.path
if((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() -ne $c.baseline_sha256){throw 'source drift'}
$s=[IO.File]::ReadAllText($p).Replace("`r`n","`n")
foreach($r in $c.replacements){if($s.IndexOf($r.old) -lt 0 -or $s.IndexOf($r.old) -ne $s.LastIndexOf($r.old)){throw 'replacement cardinality'};$s=$s.Replace($r.old,$r.new)}
[IO.File]::WriteAllText($p,$s+$c.append,[Text.UTF8Encoding]::new($false))
[ordered]@{path=$c.path;sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}|ConvertTo-Json|Set-Content -LiteralPath ($b+'/source-03.result.json')
