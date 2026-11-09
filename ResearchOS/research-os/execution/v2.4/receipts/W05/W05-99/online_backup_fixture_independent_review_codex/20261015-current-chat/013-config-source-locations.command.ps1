[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$w='D:\作品集\ResearchOS\research-os\.local\worktrees\online-backup-fixture-qualification-20261015'
rg -n 'RuntimeAssetsRoot|func NewCurrentMu|func New\(|func NewWith' "$w\internal\domain" "$w\apps\control" -g '*.go' -g '!**/*_test.go'
exit $LASTEXITCODE