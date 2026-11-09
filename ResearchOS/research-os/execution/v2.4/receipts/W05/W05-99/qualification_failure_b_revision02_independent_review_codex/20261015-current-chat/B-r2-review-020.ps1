$ErrorActionPreference='Stop'
$p='D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/internal/domain/contracts.go'
$a=Get-Content -LiteralPath $p -Encoding utf8
for($i=86;$i -lt 110;$i++){'{0}: {1}' -f ($i+1),$a[$i]}
$author=Get-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision02_source_codex/20261015-current-chat/FINAL-manifest.json' -Raw -Encoding utf8|ConvertFrom-Json
$review=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'review.json') -Raw -Encoding utf8|ConvertFrom-Json
if($review.r2_base -ne $author.base_commit){'CORRECT OWN REVIEW BASE '+$review.r2_base+' -> '+$author.base_commit;$review.r2_base=$author.base_commit}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'review.json'),($review|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
$names=@('bootstrap-recipe.json','bootstrap-read.ps1','B-r2-review-001.command.json','B-r2-review-001.stdout.txt','B-r2-review-001.stderr.txt')
$items=@()
foreach($name in $names){$p=Join-Path $PSScriptRoot $name;$items += [ordered]@{name=$name;originalPath='D:/作品集/ResearchOS/research-os/qualification_failure_b_revision02_independent_review_codex/20261015-current-chat/'+$name;currentPath=$p;sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant();bytes=(Get-Item -LiteralPath $p).Length}}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'bootstrap-relocation.json'),([ordered]@{movedBy='B-r2-review-002';copyOrRewriteOfOriginalBytes=$false;originalEmptyDirectoriesRemoved=$true;files=$items}|ConvertTo-Json -Depth 15),[Text.UTF8Encoding]::new($false))
'OWN REVIEW STATUS '+$review.status
'CORRECT r2_base '+$review.r2_base
exit 0
