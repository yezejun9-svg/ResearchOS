$w='D:\作品集\ResearchOS\research-os\.local\worktrees\owned-core-stop-anchor-r2-20261015'
Get-Content "$w\internal\ownedcorestop\stop_windows_test.go","$w\internal\ownedcorestop\proof_windows_test.go","$w\internal\ownedcorestop\journal_windows_test.go","$w\ops\supervisor\owned_core_handle_windows_test.go" -Raw
$a='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\owned_core_stop_anchor_revision02_source_codex\20261015-current-chat'
(Get-Content "$a\candidate-f5db4a96-final\manifest.json" -Raw | ConvertFrom-Json).PSObject.Properties | Select-Object Name
Get-ChildItem -LiteralPath $a -File | Select-Object Name,Length
