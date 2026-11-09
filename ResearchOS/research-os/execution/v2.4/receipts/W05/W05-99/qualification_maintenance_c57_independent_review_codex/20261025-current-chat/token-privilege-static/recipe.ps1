$ErrorActionPreference='Stop'
$r='D:\作品集\ResearchOS\research-os'
$w=Join-Path $r '.local\worktrees\qualification-maintenance-c57-20261025'
'INITIAL_DISCOVERY: project AGENTS.md read through tool before recipe; no other discovery commands executed.'
'MODEL: inherited gpt-6-astra, high reasoning; bounded independent security static review.'
'GIT_HEAD'
git -C $w rev-parse HEAD
"NATIVE_EXIT=$LASTEXITCODE"
'GIT_TREE'
git -C $w rev-parse 'HEAD^{tree}'
"NATIVE_EXIT=$LASTEXITCODE"
'GIT_PARENT'
git -C $w rev-parse 'HEAD^'
"NATIVE_EXIT=$LASTEXITCODE"
$files=@(
 (Join-Path $r 'execution\v2.4\receipts\W05\W05-99\resume_cp528_codex\20261025-current-chat\continuation-cp547\C57-independent-phase2-exact57-amendment.json'),
 (Join-Path $r 'execution\v2.4\receipts\W05\W05-99\resume_cp528_codex\20261025-current-chat\continuation-cp533\C57-source-scope.json'),
 (Join-Path $r 'execution\v2.4\receipts\W05\W05-99\qualification_boot_supplement_independent_design_review_codex\20261015-current-chat\design-review.md'),
 (Join-Path $w 'internal\recoveryboundary\contract.go'),
 (Join-Path $w 'internal\recoveryboundary\boot_windows.go')
)
foreach($file in $files){
 "FILE=$file"
 "SHA256=$((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant())"
 $i=0
 Get-Content -LiteralPath $file -Encoding UTF8 | ForEach-Object { $i++; '{0,5}: {1}' -f $i,$_ }
}
'RECIPE_COMPLETED'