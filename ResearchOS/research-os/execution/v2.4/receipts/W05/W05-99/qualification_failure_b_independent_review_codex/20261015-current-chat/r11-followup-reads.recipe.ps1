$ErrorActionPreference='Stop'
$W='D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-20261015'
git -C $W diff --binary f48fca0e4013bda19913a34d91da0cd23157a08b HEAD | Set-Content -Encoding utf8 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_independent_review_codex\20261015-current-chat\full-candidate-diff.patch'
git -C $W diff f48fca0e4013bda19913a34d91da0cd23157a08b HEAD -- internal/domain/runtime_command_queue_windows_test.go
Get-Content -Raw 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_source_codex\20261015-current-chat\B-diagnostic-ledger.md'
Get-Content -Raw 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_source_codex\20261015-current-chat\FINAL.json'
rg -n 'client_queue_fences|client_commands|queue_control|CREATE TABLE.*resource_effects' "$W\schema" "$W\internal\store" "$W\internal\domain\runtime_command_queue_windows.go"
