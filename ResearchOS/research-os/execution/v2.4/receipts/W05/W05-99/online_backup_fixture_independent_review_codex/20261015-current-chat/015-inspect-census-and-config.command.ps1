[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$b=Get-Content "$PSScriptRoot\f04-db-before.stdout.raw" -Raw -Encoding utf8|ConvertFrom-Json
$r=Get-Content "$PSScriptRoot\f20-db-restored.stdout.raw" -Raw -Encoding utf8|ConvertFrom-Json
[pscustomobject]@{all=$b.tables.PSObject.Properties.Count;names=@($b.tables.PSObject.Properties.Name);integrity=$b.integrity_check;restoredIntegrity=$r.integrity_check;differences=@($b.tables.PSObject.Properties|Where-Object{($_.Value|ConvertTo-Json -Compress) -ne ($r.tables.($_.Name)|ConvertTo-Json -Compress)}|ForEach-Object {$_.Name})}|ConvertTo-Json -Depth 5
$w='D:\作品集\ResearchOS\research-os\.local\worktrees\online-backup-fixture-qualification-20261015'
Get-Content "$w\internal\domain\store.go" -Encoding utf8 -TotalCount 185
Get-Content "$w\apps\control\main.go" -Encoding utf8|Select-Object -Skip 270 -First 20
rg -n 'func openVault|func openRootRegistry|func openSelectionStore|func loadHostState|privateDir|privateFile' "$w\internal\host" -g '*.go' -g '!**/*_test.go'
exit $LASTEXITCODE