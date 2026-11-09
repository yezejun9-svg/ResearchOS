$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$root=(Get-Location).Path
$bootstrap=Join-Path $root 'qualification_failure_b_revision02_independent_review_codex/20261015-current-chat'
$resolved=(Resolve-Path -LiteralPath $bootstrap).Path
if(!$resolved.StartsWith($root+[IO.Path]::DirectorySeparatorChar)){throw 'Bootstrap path outside workspace'}
Get-ChildItem -LiteralPath $resolved -File | ForEach-Object { Move-Item -LiteralPath $_.FullName -Destination $PSScriptRoot }
Remove-Item -LiteralPath $resolved
Remove-Item -LiteralPath (Split-Path -Parent $resolved)
$scopePath='execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp521/qualification-failure-B-r2-independent-review-scope.json'
$s=Get-Content -LiteralPath $scopePath -Raw -Encoding utf8 | ConvertFrom-Json
'SCOPE SHA '+(Get-FileHash -LiteralPath $scopePath -Algorithm SHA256).Hash
foreach($i in $s.inputs){$h=(Get-FileHash -LiteralPath $i.path -Algorithm SHA256).Hash.ToLowerInvariant(); if($h -ne $i.sha256){throw ('INPUT MISMATCH '+$i.path)}; 'VERIFIED '+$i.path+' '+$h}
foreach($p in @($s.inputs[0].path,$s.inputs[1].path,$s.inputs[4].path,$s.inputs[7].path)){ 'FILE '+$p;Get-Content -LiteralPath $p -Raw -Encoding utf8 }
$wt=$s.worktree
Get-ChildItem -LiteralPath $wt -Filter AGENTS.md -Recurse -File | ForEach-Object { 'RULE '+$_.FullName; Get-Content -LiteralPath $_.FullName -Raw -Encoding utf8 }
exit 0
