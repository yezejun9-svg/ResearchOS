$ErrorActionPreference='Stop'
$W='D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-20261015'
$p="$W\internal\domain\runtime_qualification_failure_windows_test.go";$l=Get-Content $p;346..430|ForEach-Object {"$($_+1): $($l[$_])"}
rg -n 'func .*dispatchGate|func .*currentAuthorityRoot|func .*clientAuthenticatedPrincipal|func .*validateRuntimeToolArguments|CREATE TABLE.*queue|queue_control' "$W\internal\domain"
rg -n 'func .*PrivateDirectory|func .*ReadBridgeTerminal' "$W\adapters\runtime"
Get-Content -Raw 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_revision03_independent_review_codex\20261015-current-chat\review.md'
Get-Content -Raw 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_revision03_independent_review_codex\20261015-current-chat\mandatory-addenda.json'
