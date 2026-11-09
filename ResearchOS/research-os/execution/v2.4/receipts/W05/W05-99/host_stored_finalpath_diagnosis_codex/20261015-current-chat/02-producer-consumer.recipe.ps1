
$ErrorActionPreference='Stop'
$wt='D:\作品集\ResearchOS\research-os\.local\worktrees\online-backup-fixture-qualification-20261015'
Set-Location -LiteralPath $wt
& git rev-parse HEAD
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
& rg --files -g AGENTS.md -g go.mod -g '*roots*' -g '*backup_windows*' -g '!execution/**' -g '!.local/**'
if($LASTEXITCODE -gt 1){exit $LASTEXITCODE}
& rg -n --glob '*.go' --glob '!execution/**' --glob '!.local/**' 'GetFinalPathNameByHandle|SnapshotWorkspace|final_path|FinalPath' .
if($LASTEXITCODE -gt 1){exit $LASTEXITCODE}
foreach($rel in @('internal/host/roots_windows.go','internal/host/roots.go','internal/host/backup_windows.go','go.mod')) {
 $p=Join-Path $wt $rel
 if(Test-Path -LiteralPath $p){ "SOURCE=$rel";$i=0;Get-Content -LiteralPath $p -Encoding UTF8 | ForEach-Object {$i++;'{0}: {1}' -f $i,$_} }
}
