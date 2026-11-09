param([Parameter(Mandatory=$true)][string]$Name,[Parameter(Mandatory=$true)][string]$Program,[Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
$ErrorActionPreference='Stop'
$receipt=$PSScriptRoot
$wt='C:\Users\yqyyds\.codex\researchos-build-worktrees\native-folder-visibility-20261012'
$build=Join-Path $wt '.local\builds\native-folder-visibility-20261012'
$goRoot='D:\作品集\ResearchOS\research-os\.local\tools\go1.27.1\go'
$env:GOTOOLCHAIN='local'; $env:GOENV='off'; $env:GOROOT=$goRoot
$env:GOPATH='D:\作品集\ResearchOS\research-os\.local\tools\gopath'
$env:GOMODCACHE=Join-Path $env:GOPATH 'pkg\mod'
$env:GOCACHE='C:\Users\yqyyds\.codex\researchos-build-worktrees\coding-client-v2-20261012\.local\builds\product-coding-client-repair-v2-20261012\go-cache'
$env:GOTMPDIR=Join-Path $build 'go-tmp'; $env:TEMP=Join-Path $build 'temp'; $env:TMP=$env:TEMP
$env:GOPROXY='off'; $env:GOSUMDB='off'; $env:RESEARCHOS_NATIVE_FOLDER_GUI_TEST='1'
New-Item -ItemType Directory -Force -Path $build,$env:GOTMPDIR,$env:TEMP | Out-Null
Set-Location -LiteralPath $wt
$invocation=Join-Path $receipt ($Name+'.invocation.json')
if(Test-Path -LiteralPath $invocation){throw 'Evidence attempt name already exists'}
$record=[ordered]@{argv=@($Program)+$Arguments;cwd=$wt;started=(Get-Date).ToUniversalTime().ToString('o');environment=@{};model_calls=0;formal_acceptance_delta=0}
foreach($key in @('GOROOT','GOPATH','GOMODCACHE','GOCACHE','GOTMPDIR','TEMP','TMP','GOTOOLCHAIN','GOENV','GOPROXY','GOSUMDB','RESEARCHOS_NATIVE_FOLDER_GUI_TEST')){$record.environment[$key]=[Environment]::GetEnvironmentVariable($key)}
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $invocation -Encoding utf8
& $Program @Arguments 1> (Join-Path $receipt ($Name+'.stdout')) 2> (Join-Path $receipt ($Name+'.stderr'))
$exit=$LASTEXITCODE
$record.ended=(Get-Date).ToUniversalTime().ToString('o'); $record.exit_code=$exit
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $receipt ($Name+'.result.json')) -Encoding utf8
Get-Content -LiteralPath (Join-Path $receipt ($Name+'.stdout'))
Get-Content -LiteralPath (Join-Path $receipt ($Name+'.stderr'))
exit $exit
