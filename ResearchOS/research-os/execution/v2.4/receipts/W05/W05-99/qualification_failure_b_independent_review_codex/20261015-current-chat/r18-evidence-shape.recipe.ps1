$ErrorActionPreference='Stop'
$R='D:\作品集\ResearchOS\research-os'
$W='D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-20261015'
$A="$R\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_source_codex\20261015-current-chat"
$m=Get-Content -Raw "$A\B-evidence-manifest.json"|ConvertFrom-Json
$m.source|Select-Object -First 1|ConvertTo-Json -Depth 5
$m.command_ledger|Select-Object -First 1|ConvertTo-Json -Depth 5
$m.whole_binary_patch|ConvertTo-Json -Depth 5
rg -n 'model, err := latestEffect|model\["state"\]|source.*schema|private.*directory' "$W\internal\domain\runtime_qualification_failure_windows.go"
git -C $W show 'f48fca0e4013bda19913a34d91da0cd23157a08b:internal/domain/runtime_command_queue_windows_test.go' | Select-Object -First 30
git -C $W status --porcelain=v1
git -C $W rev-parse HEAD 'HEAD^{tree}'
Get-Content -Raw 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_independent_review_codex\20261015-current-chat\r09.go-native-exit.json','D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_independent_review_codex\20261015-current-chat\r15.go-native-exit.json','D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_independent_review_codex\20261015-current-chat\r16.go-native-exit.json'
