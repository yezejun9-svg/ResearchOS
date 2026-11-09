$ErrorActionPreference='Stop'
$T='D:\作品集\ResearchOS\research-os\.local\qualification-failure-b-independent-review-20261015'
$expected=[IO.Path]::GetFullPath('D:\作品集\ResearchOS\research-os\.local\qualification-failure-b-independent-review-20261015')
$resolved=(Resolve-Path -LiteralPath $T).Path
if(-not [StringComparer]::OrdinalIgnoreCase.Equals($resolved,$expected)){throw 'Own temporary root mismatch'}
if((Get-Item -LiteralPath $resolved).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Own temporary root is reparse'}
@{cleanup_exact_root=$resolved;retained_reproducible_overlay='own evidence independent-overlay.json and two copied overlay source files';tests_finished=$true}|ConvertTo-Json
Remove-Item -LiteralPath $resolved -Recurse -Force
if(Test-Path -LiteralPath $resolved){throw 'Own temporary cleanup incomplete'}
$W='D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-20261015'
git -C $W rev-parse HEAD 'HEAD^{tree}'
git -C $W status --porcelain=v1
$m=Get-Content -Raw 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_source_codex\20261015-current-chat\B-evidence-manifest.json'|ConvertFrom-Json
$guard=@($m.source.PSObject.Properties|ForEach-Object {$h=(Get-FileHash -LiteralPath "$W\$($_.Name)").Hash.ToLower();[pscustomobject]@{path=$_.Name;sha256=$h;matches=($h -eq $_.Value.sha256)}})
$guard|ConvertTo-Json -Depth 5|Set-Content 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_independent_review_codex\20261015-current-chat\final-source-guard.json'
@{source_files=$guard.Count;mismatches=@($guard|Where-Object {!$_.matches}).Count;temporary_root_removed=(!(Test-Path -LiteralPath $resolved))}|ConvertTo-Json
