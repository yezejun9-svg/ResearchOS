[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$repo='D:\作品集\ResearchOS\research-os'
$au="$repo\execution\v2.4\receipts\W05\W05-99\online_backup_fixture_qualification_codex\20261015-current-chat"
$wt="$repo\.local\worktrees\online-backup-fixture-qualification-20261015"
foreach($n in @('fixture_setup.go','lease_holder.go','lease_probe.go','run_case.ps1','census.py','verify_restore.py','q03_fixture_test.go','fixture_setup.overlay.json')){Write-Output "FILE $n";Get-Content "$au\$n" -Raw -Encoding utf8}
Get-Content "$wt\ops\backup\main.go" -Raw -Encoding utf8
rg -n 'VACUUM|snapshot|Export|RuntimeAssetsRoot|func New|func.*Open|WithWorkspaces|AcquireDataRootLease' "$wt\internal\domain\backup.go" "$wt\internal\host\host.go" "$wt\adapters\sqlite" "$wt\ops\backup"
exit 0