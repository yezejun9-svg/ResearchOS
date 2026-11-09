param([Parameter(Mandatory=$true)][string]$Id, [Parameter(Mandatory=$true)][string]$WorkingDirectory, [Parameter(ValueFromRemainingArguments=$true)][string[]]$CommandArgs)
$ErrorActionPreference = 'Stop'
$tmpRoot = 'D:\作品集\ResearchOS\research-os\.local\source43-b-stop-finalpath-20261025-tmp'
foreach ($name in @('tmp','gotmp','gocache')) { New-Item -ItemType Directory -Force -Path (Join-Path $tmpRoot $name) | Out-Null }
$env:TMP = Join-Path $tmpRoot 'tmp'
$env:TEMP = Join-Path $tmpRoot 'tmp'
$env:GOTMPDIR = Join-Path $tmpRoot 'gotmp'
$env:GOCACHE = Join-Path $tmpRoot 'gocache'
$env:GOPATH = 'D:\作品集\ResearchOS\research-os\.local\tools\gopath'
$env:GOTOOLCHAIN = 'local'
$env:GOPROXY = 'off'
$env:GOSUMDB = 'off'
$env:PYTHONUTF8 = '1'
$env:RESEARCHOS_SOURCE43_ASCII_FIXTURE_ROOT = 'C:\Users\yqyyds\.codex\researchos-fixture-cache\source43-b-stop-finalpath-20261025'
$env:RESEARCHOS_OWNED_STOP_FIXTURE_EXE = 'C:\Users\yqyyds\.codex\researchos-fixture-cache\source43-b-stop-finalpath-20261025\owned-stop-fixture.exe'
$runner = Join-Path $PSScriptRoot 'run.py'
python -B -X utf8 $runner $Id $WorkingDirectory @CommandArgs
exit $LASTEXITCODE
