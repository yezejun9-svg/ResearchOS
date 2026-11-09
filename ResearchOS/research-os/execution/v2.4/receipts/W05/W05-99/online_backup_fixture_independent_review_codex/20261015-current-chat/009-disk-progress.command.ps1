[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$t='D:\作品集\ResearchOS\research-os\.local\online-backup-independent-review-20261015-tmp'
Get-ChildItem -LiteralPath $t -Directory|ForEach-Object { $sum=(Get-ChildItem -LiteralPath $_.FullName -File -Recurse -ErrorAction SilentlyContinue|Measure-Object Length -Sum).Sum;[pscustomobject]@{name=$_.Name;bytes=$sum;GiB=$sum/1GB}}|ConvertTo-Json
Get-Content "$PSScriptRoot\008-build.stdout.txt" -Encoding utf8
Get-Content "$PSScriptRoot\b01-build-real-cli.stderr.raw" -Encoding utf8 -Tail 5
exit 0