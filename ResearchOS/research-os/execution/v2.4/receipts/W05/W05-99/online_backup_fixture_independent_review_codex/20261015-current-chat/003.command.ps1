$ErrorActionPreference='Stop'
$repo='D:\作品集\ResearchOS\research-os'
$wt="$repo\.local\worktrees\online-backup-fixture-qualification-20261015"
Get-Content "$repo\AGENTS.md" -Raw -Encoding utf8
Get-Content "$wt\AGENTS.md" -Raw -Encoding utf8
git -C $wt status --short
git -C $wt rev-parse HEAD 'HEAD^{tree}'
$au="$repo\execution\v2.4\receipts\W05\W05-99\online_backup_fixture_qualification_codex\20261015-current-chat"
Get-Content "$au\qualification-report.md" -Raw -Encoding utf8
Get-Content "$au\source-helper-overlay-manifest.json" -Raw -Encoding utf8
rg --files $wt -g '*backup*' -g '*root*lease*' -g 'AGENTS.md'
exit $LASTEXITCODE