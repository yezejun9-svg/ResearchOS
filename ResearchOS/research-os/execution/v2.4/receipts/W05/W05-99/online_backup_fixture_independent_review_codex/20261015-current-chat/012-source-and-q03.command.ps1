[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$r='D:\作品集\ResearchOS\research-os'
$w="$r\.local\worktrees\online-backup-fixture-qualification-20261015"
$a="$r\execution\v2.4\receipts\W05\W05-99\online_backup_fixture_qualification_codex\20261015-current-chat"
Get-Content "$a\verify_q03.py" -Raw -Encoding utf8
Get-Content "$a\verify-q03-current-history-r5.stdout.raw" -Raw -Encoding utf8
Get-Content "$a\read-q03-restored-report.stdout.raw" -Raw -Encoding utf8
rg -n 'RuntimeAssetsRoot|func NewCurrentMu|func newService|config' "$w\internal\domain\service.go" "$w\apps\control\main.go" "$w\internal\host\vault.go" "$w\internal\host\roots.go"
$e=$LASTEXITCODE
Write-Output "RG_NATIVE_EXIT=$e"
Get-Content "$w\internal\domain\backup_command_queue.go" -Encoding utf8 -TotalCount 190
exit 0