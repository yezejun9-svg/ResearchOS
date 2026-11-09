$ErrorActionPreference='Stop'
$W='D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-20261015'
$p="$W\internal\domain\runtime_qualification_failure_windows.go";$lines=Get-Content $p;240..575|ForEach-Object {"$($_+1): $($lines[$_])"}
Get-Content -Raw "$W\adapters\runtime\qualification_failure_proof_windows_test.go"
rg -n '^func Test|func .*Qualification|Owner|tamper|GO|GOCACHE' "$W\internal\domain\runtime_qualification_failure_windows_test.go"
Get-Content -Raw 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_source_codex\20261015-current-chat\b78-final-focused.recipe.json'
