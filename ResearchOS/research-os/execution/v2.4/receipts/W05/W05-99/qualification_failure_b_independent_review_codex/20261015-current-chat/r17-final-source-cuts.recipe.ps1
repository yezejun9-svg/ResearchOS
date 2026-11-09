$ErrorActionPreference='Stop'
$W='D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-20261015'
rg -n '^func Empty' "$W\internal\domain"
$p="$W\internal\domain\runtime_qualification_failure_windows.go";$l=Get-Content $p;816..851|ForEach-Object {"$($_+1): $($l[$_])"}
$p="$W\internal\domain\runtime_coordinator_windows.go";$l=Get-Content $p;509..534|ForEach-Object {"$($_+1): $($l[$_])"}
$p="$W\internal\domain\runtime_qualification_failure_windows_test.go";$l=Get-Content $p;293..345|ForEach-Object {"$($_+1): $($l[$_])"}
Get-Content -Raw 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_independent_review_codex\20261015-current-chat\input-verification.json'
Get-Content -Tail 10 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_independent_review_codex\20261015-current-chat\r16-existing-regression.raw.txt'
