$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new()
$wt='D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-backend-20261104'
$base='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-backend-author'
$payload=Get-Content -LiteralPath (Join-Path $base 'source-16.json') -Raw -Encoding UTF8|ConvertFrom-Json
$writes=@{}
foreach($entry in $payload.new_files.PSObject.Properties){if(Test-Path -LiteralPath (Join-Path $wt $entry.Name)){throw ('new source exists '+$entry.Name)};$writes[$entry.Name]=[string]$entry.Value}
foreach($change in $payload.modifications){$p=Join-Path $wt $change.path;if((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() -ne $change.baseline_sha256){throw 'source baseline drift'};$s=[IO.File]::ReadAllText($p).Replace("`r`n","`n");foreach($r in $change.replacements){if($s.IndexOf($r.old) -lt 0 -or $s.IndexOf($r.old) -ne $s.LastIndexOf($r.old)){throw 'replacement cardinality'};$s=$s.Replace($r.old,$r.new)};$writes[$change.path]=$s+$change.append}
$pins=foreach($rel in $writes.Keys){$p=Join-Path $wt $rel;[IO.File]::WriteAllText($p,$writes[$rel],[Text.UTF8Encoding]::new($false));[ordered]@{path=$rel;sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant();bytes=(Get-Item -LiteralPath $p).Length}}
[IO.File]::WriteAllText((Join-Path $base 'source-16.result.json'),($pins|ConvertTo-Json -Depth 4),[Text.UTF8Encoding]::new($false))
$pins|ConvertTo-Json -Compress

