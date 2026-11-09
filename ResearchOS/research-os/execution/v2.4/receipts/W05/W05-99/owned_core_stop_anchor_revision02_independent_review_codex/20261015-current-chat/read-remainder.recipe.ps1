$a='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\owned_core_stop_anchor_revision02_source_codex\20261015-current-chat'
$m=Get-Content "$a\candidate-f5db4a96-final\manifest.json" -Raw | ConvertFrom-Json
$m.failure_ledger | ConvertTo-Json -Depth 12
$m.command_capture_index | ConvertTo-Json -Depth 4
$m.limits | ConvertTo-Json -Depth 6
$m.fixture_cases | ConvertTo-Json -Depth 4
$w='D:\作品集\ResearchOS\research-os\.local\worktrees\owned-core-stop-anchor-r2-20261015'
Get-Content "$w\internal\host\owned_core_stop_identity_windows_test.go","$w\internal\store\owned_stop_backup_test.go","$w\internal\store\owned_stop_barrier_windows_test.go","$w\ops\owned_core_stop\main_windows_test.go","$w\ops\owned_core_stop\fixture\main_windows.go" -Raw
