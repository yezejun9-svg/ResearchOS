[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$repo='D:\作品集\ResearchOS\research-os'
$wt="$repo\.local\worktrees\online-backup-fixture-qualification-20261015"
$au="$repo\execution\v2.4\receipts\W05\W05-99\online_backup_fixture_qualification_codex\20261015-current-chat"
Get-Content "$wt\internal\host\host.go" -Encoding utf8 -TotalCount 270
Get-Content "$wt\internal\store\sqlite.go" -Encoding utf8 -TotalCount 150
Get-Content "$wt\internal\domain\backup.go" -Encoding utf8 | Select-Object -Skip 358 -First 225
Get-Content "$au\verify_q03.py" -Raw -Encoding utf8
Get-Content "$au\verify-q03-current-history-r5.stdout.raw" -Raw -Encoding utf8
Get-Content "$au\q03-current-db-before.stdout.raw" -Encoding utf8 -ErrorAction Continue
$web=@{id='006-web';fullargv=@('web.run','open','https://www.sqlite.org/lang_vacuum.html','https://www.sqlite.org/wal.html','https://www.sqlite.org/isolation.html');cwd=$wt;relevantenv=@{};nativeexit='not_applicable_web_tool';rawstdout='006-web-result.json';rawstderr='006-web-errors.txt'}
$web|ConvertTo-Json -Depth 5|Set-Content "$PSScriptRoot\006-web.recipe.json" -Encoding utf8
exit 0