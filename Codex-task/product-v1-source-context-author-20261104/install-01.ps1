$ErrorActionPreference='Stop'
$OutputEncoding=[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new()
$worktreeRoot='D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-source-context-20261104'
$evidenceRoot='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-source-context-author-20261104'
$changes=Get-Content -Raw -Encoding UTF8 -LiteralPath ($evidenceRoot+'/changes-01.json')|ConvertFrom-Json
$pending=@()
foreach($change in $changes){
 $targetPath=Join-Path $worktreeRoot $change.path
 $actual=(Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash.ToLowerInvariant()
 if($actual -ne $change.baseline){throw ('Baseline mismatch '+$change.path)}
 $content=[IO.File]::ReadAllText($targetPath).Replace("`r`n","`n")
 foreach($replacement in $change.replacements){
  $hits=([regex]::Matches($content,[regex]::Escape($replacement.old))).Count
  if($hits -ne 1){throw ('Replacement count '+$hits+' '+$change.path+' '+$replacement.old)}
  $content=$content.Replace($replacement.old,$replacement.value)
 }
 $pending+=@{path=$targetPath;relative=$change.path;content=$content}
}
foreach($change in $pending){[IO.File]::WriteAllText($change.path,$change.content,[Text.UTF8Encoding]::new($false))}
$pins=@(foreach($change in $pending){@{path=$change.relative;sha256=(Get-FileHash -LiteralPath $change.path -Algorithm SHA256).Hash.ToLowerInvariant()}})
$pins|ConvertTo-Json -Depth 4|Set-Content -Encoding UTF8 -LiteralPath ($evidenceRoot+'/installed-01.json')
$pins|ConvertTo-Json -Depth 4
