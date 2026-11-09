$ErrorActionPreference='Stop'
$R='D:\作品集\ResearchOS\research-os'
$W='D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-20261015'
$scope=Get-Content -Raw "$R\execution\v2.4\receipts\W05\W05-99\resume_cp398_codex\20261015-current-chat\continuation-cp517-retry02\qualification-failure-B-independent-review-scope.json"|ConvertFrom-Json
$card=Get-Content -Raw "$R\execution\v2.4\receipts\W05\W05-99\resume_cp398_codex\20261015-current-chat\continuation-cp512\qualification-failure-B-source-scope.json"|ConvertFrom-Json
$refs=$scope.inputs+@($card.accepted_A_ref)+$card.design_refs+@($card.independent_design_ref,$card.C_write_shape_ref,$card.current_classification_review_ref)
$verified=$refs|ForEach-Object {$file=Get-Item -LiteralPath "$R\$($_.path)";$hash=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLower();[pscustomobject]@{path=$_.path;sha256=$hash;bytes=$file.Length;matches=($hash -eq $_.sha256 -and $file.Length -eq $_.bytes)}}
$verified|ConvertTo-Json -Depth 8|Set-Content 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_independent_review_codex\20261015-current-chat\input-verification.json'
$verified|Format-Table path,matches
Get-Content -Raw "$R\execution\v2.4\receipts\W05\W05-99\qualification_projection_a_revision02_independent_review_codex\20261015-current-chat\review.md"
Get-Content -Raw "$R\execution\v2.4\receipts\W05\W05-99\qualification_failure_revision02_independent_review_codex\20261015-current-chat\review.md"
$p="$W\internal\domain\runtime_qualification_failure_windows_test.go";$l=Get-Content $p;560..($l.Length-1)|ForEach-Object {"$($_+1): $($l[$_])"}
