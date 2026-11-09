
$ErrorActionPreference='Stop'
$wt='D:\作品集\ResearchOS\research-os\.local\worktrees\online-backup-fixture-qualification-20261015'
$ev='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\host_stored_finalpath_diagnosis_codex\20261015-current-chat'
$tmp='D:\作品集\ResearchOS\research-os\.local\host-stored-finalpath-diagnosis-20261015-tmp'
Set-Location -LiteralPath $wt
foreach($spec in @(@('internal/host/host.go',197,260),@('internal/host/native.go',260,335),@('internal/host/surface.go',1,50),@('internal/host/workspace_files_windows.go',65,110),@('internal/host/workspace_write_windows.go',350,403))) {
"SOURCE=$($spec[0])"
$lines=Get-Content -LiteralPath (Join-Path $wt $spec[0]) -Encoding UTF8
for($i=$spec[1]-1;$i -lt [Math]::Min($spec[2],$lines.Length);$i++){'{0}: {1}' -f ($i+1),$lines[$i]}
}
& rg -n -g '*test.go' 'func.*Root|FinalPath|fileIdentity|roots.Register|RootRegistry' internal/host
if($LASTEXITCODE -gt 1){exit $LASTEXITCODE}
foreach($rev in @('4f4023c956f84d65743f39ce77d6c8899a21ada1','6802628826dcc4b79a16ced20a8e26f7e5494a1b')){
foreach($path in @('internal/host/roots_windows.go','internal/host/roots.go','internal/host/backup_windows.go','internal/host/host.go','internal/host/native.go')){
 $obj=$rev+':'+$path
 "BLOB=$obj"
 & git rev-parse $obj
 if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
}
}
[IO.Directory]::CreateDirectory($tmp) | Out-Null
foreach($leaf in @('module','cache','gotmp','temp')){[IO.Directory]::CreateDirectory((Join-Path $tmp $leaf)) | Out-Null}
$module=Join-Path $tmp 'module'
Copy-Item -LiteralPath (Join-Path $wt 'internal\host\roots_windows.go') -Destination (Join-Path $module 'roots_windows.go')
Copy-Item -LiteralPath (Join-Path $wt 'go.sum') -Destination (Join-Path $module 'go.sum')
Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $wt 'internal\host\roots_windows.go'),(Join-Path $module 'roots_windows.go')
[IO.File]::WriteAllText((Join-Path $module 'go.mod'),("module hostpathdiagnosis.local/fixture"+[Environment]::NewLine+[Environment]::NewLine+"go 1.27.1"+[Environment]::NewLine+[Environment]::NewLine+"require golang.org/x/sys v0.48.0"+[Environment]::NewLine),(New-Object Text.UTF8Encoding($false)))
$env:GOTOOLCHAIN='local'
$env:GOPATH='D:\作品集\ResearchOS\research-os\.local\tools\gopath'
$env:GOMODCACHE=Join-Path $env:GOPATH 'pkg\mod'
$env:GOCACHE=Join-Path $tmp 'cache'
$env:GOTMPDIR=Join-Path $tmp 'gotmp'
$env:TMP=Join-Path $tmp 'temp'
$env:TEMP=$env:TMP
$env:GOPROXY='off'
$env:GOSUMDB='off'
& 'D:\作品集\ResearchOS\research-os\.local\tools\go1.27.1\go\bin\go.exe' version
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
"X_SYS_EXISTS=$(Test-Path -LiteralPath (Join-Path $env:GOMODCACHE 'golang.org\x\sys@v0.48.0'))"
