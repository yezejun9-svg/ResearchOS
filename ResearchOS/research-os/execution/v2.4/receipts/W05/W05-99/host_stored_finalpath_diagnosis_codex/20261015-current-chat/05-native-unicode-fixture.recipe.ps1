
$ErrorActionPreference='Stop'
$ev='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\host_stored_finalpath_diagnosis_codex\20261015-current-chat'
$tmp='D:\作品集\ResearchOS\research-os\.local\host-stored-finalpath-diagnosis-20261015-tmp'
$env:GOTOOLCHAIN='local'
$env:GOPATH='D:\作品集\ResearchOS\research-os\.local\tools\gopath'
$env:GOMODCACHE=Join-Path $env:GOPATH 'pkg\mod'
$env:GOCACHE=Join-Path $tmp 'cache'
$env:GOTMPDIR=Join-Path $tmp 'gotmp'
$env:TMP=Join-Path $tmp 'temp'
$env:TEMP=$env:TMP
$env:GOPROXY='off'
$env:GOSUMDB='off'
$env:DIAGNOSIS_FIXTURE_ROOT=Join-Path $tmp 'fresh-workspaces'
$go='D:\作品集\ResearchOS\research-os\.local\tools\go1.27.1\go\bin\go.exe'
$goArgs=@('test','-mod=readonly','-overlay',(Join-Path $ev 'diagnosis-overlay.json'),'-count=1','-v','-run','^TestDiagnosis','.')
Set-Location -LiteralPath (Join-Path $tmp 'module')
$envRecord=@{}
foreach($k in @('GOTOOLCHAIN','GOPATH','GOMODCACHE','GOCACHE','GOTMPDIR','TMP','TEMP','GOPROXY','GOSUMDB','DIAGNOSIS_FIXTURE_ROOT')){$envRecord[$k]=[Environment]::GetEnvironmentVariable($k)}
@{cwd=(Get-Location).Path;executable=$go;argv=$goArgs;env=$envRecord} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $ev '05-native-go.execution.json') -Encoding UTF8
& $go @goArgs
$native=$LASTEXITCODE
[IO.File]::WriteAllText((Join-Path $ev '05-native-go.exit.txt'),[string]$native)
exit $native
