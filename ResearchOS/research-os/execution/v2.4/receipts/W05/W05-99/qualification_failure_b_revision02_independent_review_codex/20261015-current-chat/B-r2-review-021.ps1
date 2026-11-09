$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$review=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'review.json') -Raw -Encoding utf8|ConvertFrom-Json
$review|Add-Member -Force -NotePropertyName sourceA_r2_reference -NotePropertyValue ([ordered]@{manifest='execution/v2.4/receipts/W05/W05-99/qualification_projection_a_revision02_independent_review_codex/20261015-current-chat/evidence-manifest.json';sha256='319c2c8a86585ea5daa587fbdbb7df75ba321c367f8b172fc32f49cb3944f1fe';interpretation='Accepted limited source reference as scoped; f48fca0e is not the old rejected A-v1 candidate. No widened Source A acceptance.'})
$review|Add-Member -Force -NotePropertyName native_owner_limit -NotePropertyValue 'Actual different-owner/OS-trusted-owner assignment was not dynamically exercised; current-SID equality is reviewed in source. Extra System ACE refusal is a distinct dynamic check, not an owner reassignment.'
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'review.json'),($review|ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
$expected='D:/作品集/ResearchOS/research-os/.local/qualification-failure-b-r2-independent-review-20261015-tmp'
$full=[IO.Path]::GetFullPath($expected).TrimEnd([IO.Path]::DirectorySeparatorChar)
$allowed=[IO.Path]::GetFullPath('D:/作品集/ResearchOS/research-os/.local/qualification-failure-b-r2-independent-review-20261015-tmp').TrimEnd([IO.Path]::DirectorySeparatorChar)
if($full -ne $allowed -or !$full.StartsWith([IO.Path]::GetFullPath('D:/作品集/ResearchOS/research-os/.local/'))){throw 'Temporary cleanup scope mismatch'}
if(Test-Path -LiteralPath $full){
 $resolved=(Resolve-Path -LiteralPath $full).Path
 if($resolved -ne $allowed){throw 'Resolved temporary root differs'}
 $count=@(Get-ChildItem -LiteralPath $resolved -Recurse -File).Count
 Remove-Item -LiteralPath $resolved -Recurse -Force
 [ordered]@{path=$resolved;filesRemoved=$count;removed=!(Test-Path -LiteralPath $resolved);kind='own isolated temp/cache only'}|ConvertTo-Json -Compress
}
$verification=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'source-final-verification.json') -Raw -Encoding utf8|ConvertFrom-Json
foreach($f in $verification){if((Get-FileHash -LiteralPath (Join-Path 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015' $f.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $f.sha256){throw 'Frozen source changed'}}
git -C 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015' status --porcelain=v1
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
git -C 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015' rev-parse HEAD 'HEAD^{tree}' f48fca0e 75e5257c
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
'VERDICT NEEDS_CHANGES; two P1; actual/formal=0; finite test work ended'
exit 0
