[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$w='D:\作品集\ResearchOS\research-os\.local\worktrees\online-backup-fixture-qualification-20261015'
rg -n 'backup_require_fresh_observation|WorkspaceBackup|ReadBackup|Walk|Snapshot|Max|limit' "$w\internal\domain\backup_workspace.go" "$w\internal\domain\backup_recovery.go" "$w\internal\host\backup_windows.go"
$ec=$LASTEXITCODE
Write-Output "RG_NATIVE_EXIT=$ec"
Get-Content "$w\internal\host\roots.go" -Encoding utf8 -TotalCount 80
Get-Content "$w\internal\host\vault.go" -Encoding utf8|Select-Object -Skip 192 -First 26
Get-Content "$w\internal\host\selections.go" -Encoding utf8|Select-Object -Skip 48 -First 32
Get-Content "$w\internal\host\state.go" -Encoding utf8 -TotalCount 75
exit $ec