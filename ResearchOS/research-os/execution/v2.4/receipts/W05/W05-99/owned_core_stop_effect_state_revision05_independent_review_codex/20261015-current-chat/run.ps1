param([string]$Id,[string]$Script)
$ErrorActionPreference='Stop'
$e=$PSScriptRoot
$t='D:/作品集/ResearchOS/research-os/.local/owned-core-stop-r5-independent-review-20261015-tmp'
New-Item -ItemType Directory -Force -Path $t | Out-Null
$env:TEMP=$t; $env:TMP=$t
$env:GOPATH='D:/作品集/ResearchOS/research-os/.local/tools/gopath'
$env:GOCACHE="$t/gocache"; $env:GOTMPDIR=$t; $env:GOTOOLCHAIN='local'
$Script | Set-Content -Encoding utf8 "$e/$Id.ps1"
@{id=$Id;cwd=(Get-Location).Path;fullargv=@('pwsh','-NoProfile','-File',"$e/$Id.ps1");relevantenv=@{TEMP=$env:TEMP;TMP=$env:TMP;GOPATH=$env:GOPATH;GOCACHE=$env:GOCACHE;GOTMPDIR=$env:GOTMPDIR;GOTOOLCHAIN=$env:GOTOOLCHAIN};stdout="$Id.stdout.txt";stderr="$Id.stderr.txt";nativeexit="$Id.exit.txt"} | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 "$e/$Id.recipe.json"
& pwsh -NoProfile -File "$e/$Id.ps1" 1> "$e/$Id.stdout.txt" 2> "$e/$Id.stderr.txt"
$code=$LASTEXITCODE
$code | Set-Content "$e/$Id.exit.txt"
Get-Content "$e/$Id.stdout.txt","$e/$Id.stderr.txt"
exit $code
