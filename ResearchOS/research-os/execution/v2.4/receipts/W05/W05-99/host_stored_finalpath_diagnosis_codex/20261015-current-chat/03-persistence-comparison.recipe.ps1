
$ErrorActionPreference='Stop'
$wt='D:\作品集\ResearchOS\research-os\.local\worktrees\online-backup-fixture-qualification-20261015'
$ev='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\host_stored_finalpath_diagnosis_codex\20261015-current-chat'
Set-Location -LiteralPath $wt
& rg -n --glob '*.go' 'func (readPrivate|writePrivate)|roots.Register|roots.Revoke|func.*(Grant|Revoke|RegisterWorkspace)|FinalPath|fileIdentity' internal/host
if($LASTEXITCODE -gt 1){exit $LASTEXITCODE}
& rg -n --glob '*.go' 'func.*Root|Register\(|Unicode|中文|FinalPath' internal/host/*test.go
"NATIVE_RG_TEST_GLOB_EXIT=$LASTEXITCODE"
& git diff 4f4023c956f84d65743f39ce77d6c8899a21ada1 6802628826dcc4b79a16ced20a8e26f7e5494a1b -- internal/host/roots_windows.go internal/host/roots.go internal/host/backup_windows.go
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
& git log -3 --format='%H %s' 6802628826dcc4b79a16ced20a8e26f7e5494a1b
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
$meta='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\resume_cp398_codex\20261015-current-chat\continuation-cp523\online-backup-limited-fixture-adoption.json'
Get-Content -LiteralPath $meta -Raw -Encoding UTF8
foreach($rel in @('internal/host/store.go','internal/domain/backup_workspace.go','internal/host/host.go')) {
$p=Join-Path $wt $rel
if(Test-Path -LiteralPath $p) {
"SOURCE=$rel"
$lines=Get-Content -LiteralPath $p -Encoding UTF8
for($i=0;$i -lt $lines.Length;$i++){if($rel -eq 'internal/host/store.go' -or ($rel -eq 'internal/domain/backup_workspace.go' -and $i -ge 130 -and $i -lt 235) -or ($rel -eq 'internal/host/host.go' -and $lines[$i] -match 'Root|Register|Revoke|func')){'{0}: {1}' -f ($i+1),$lines[$i]}}
}
}
@{tool='web.run';open=@(@{ref_id='https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfinalpathnamebyhandlew'});response_length='long'} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $ev '03-microsoft-doc-request.json') -Encoding UTF8
