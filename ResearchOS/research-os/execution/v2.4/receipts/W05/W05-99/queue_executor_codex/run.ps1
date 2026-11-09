param([Parameter(Mandatory=$true)][string]$Name,[Parameter(Mandatory=$true)][string]$Exe,[Parameter(Mandatory=$true)][string[]]$RunArgs)
$ErrorActionPreference='Stop'
$receiptRoot=Join-Path $PSScriptRoot $Name
if(Test-Path -LiteralPath $receiptRoot){throw 'Receipt already exists'}
New-Item -ItemType Directory -Path $receiptRoot|Out-Null
$env:GOTOOLCHAIN='local';$env:GOENV='off';$env:GOROOT='D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go';$env:GOCACHE='D:/作品集/ResearchOS/research-os/.local/gocache';$env:GOPATH='D:/作品集/ResearchOS/research-os/.local/gopath'
$env:RESEARCHOS_MU_BUNDLE=Join-Path (Get-Location) '.local/w1401-mu-worker/mu-worker.mjs'
$env:RESEARCHOS_GO='D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe'
$env:RESEARCHOS_NODE='C:/nvm4w/nodejs/node.exe'
$env:RESEARCHOS_W04_PACKAGE_INPUT=Join-Path $PSScriptRoot 'frozen-package-input'
if((Get-FileHash -LiteralPath (Join-Path $env:RESEARCHOS_W04_PACKAGE_INPUT 'PACKAGE_MANIFEST.json')).Hash.ToLower() -ne '4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964'){throw 'frozen package changed'}
$env:RESEARCHOS_QUEUE_WORKER_BUNDLE=$env:RESEARCHOS_MU_BUNDLE
$env:RESEARCHOS_QUEUE_FAILURE_DIR=Join-Path $receiptRoot 'failed-fixture'
$sourcePaths=@(git ls-files -- '*.go' 'go.mod' 'go.sum' 'migrations/sqlite/*' 'adapters/runtime/mu/*' 'internal/api/contracts/*')+@(git ls-files --others --exclude-standard -- '*.go' 'migrations/sqlite/*' 'adapters/runtime/mu/*')
$sourceInputs=@($sourcePaths|Sort-Object -Unique|ForEach-Object {if(Test-Path -LiteralPath $_){[ordered]@{path=$_;sha256=(Get-FileHash -LiteralPath $_).Hash.ToLower();bytes=(Get-Item -LiteralPath $_).Length}}})
$sourceInputs|ConvertTo-Json -Depth 5|Set-Content -Encoding utf8 (Join-Path $receiptRoot 'inputs.json')
[ordered]@{exe=$Exe;exe_sha256=(Get-FileHash -LiteralPath $Exe).Hash.ToLower();argv=$RunArgs;cwd=(Get-Location).Path;environment=[ordered]@{GOROOT=$env:GOROOT;GOENV=$env:GOENV;GOTOOLCHAIN=$env:GOTOOLCHAIN;GOCACHE=$env:GOCACHE;GOPATH=$env:GOPATH;RESEARCHOS_W04_PACKAGE_INPUT=$env:RESEARCHOS_W04_PACKAGE_INPUT;RESEARCHOS_QUEUE_FAILURE_DIR=$env:RESEARCHOS_QUEUE_FAILURE_DIR;RESEARCHOS_GO=$env:RESEARCHOS_GO;RESEARCHOS_NODE=$env:RESEARCHOS_NODE;RESEARCHOS_MU_BUNDLE=$env:RESEARCHOS_MU_BUNDLE};head=(git rev-parse HEAD);started=(Get-Date).ToUniversalTime().ToString('o');bundle_sha256=$(if(Test-Path -LiteralPath $env:RESEARCHOS_MU_BUNDLE){(Get-FileHash -LiteralPath $env:RESEARCHOS_MU_BUNDLE).Hash.ToLower()})}|ConvertTo-Json -Depth 5|Set-Content -Encoding utf8 (Join-Path $receiptRoot 'command.json')
& $Exe @RunArgs 1> (Join-Path $receiptRoot 'stdout.raw') 2> (Join-Path $receiptRoot 'stderr.raw')
$code=$LASTEXITCODE
$afterPaths=@(git ls-files -- '*.go' 'go.mod' 'go.sum' 'migrations/sqlite/*' 'adapters/runtime/mu/*' 'internal/api/contracts/*')+@(git ls-files --others --exclude-standard -- '*.go' 'migrations/sqlite/*' 'adapters/runtime/mu/*')
$afterInputs=@($afterPaths|Sort-Object -Unique|ForEach-Object {if(Test-Path -LiteralPath $_){[ordered]@{path=$_;sha256=(Get-FileHash -LiteralPath $_).Hash.ToLower();bytes=(Get-Item -LiteralPath $_).Length}}})
$afterInputs|ConvertTo-Json -Depth 5|Set-Content -Encoding utf8 (Join-Path $receiptRoot 'inputs-after.json')
$drift=@($sourceInputs|Where-Object {!(Test-Path -LiteralPath $_.path) -or (Get-FileHash -LiteralPath $_.path).Hash.ToLower() -ne $_.sha256}|ForEach-Object {$_.path})
[ordered]@{exit_code=$code;ended=(Get-Date).ToUniversalTime().ToString('o');source_drift=$drift;stdout_sha256=(Get-FileHash (Join-Path $receiptRoot 'stdout.raw')).Hash.ToLower();stderr_sha256=(Get-FileHash (Join-Path $receiptRoot 'stderr.raw')).Hash.ToLower();classification='DEVELOPMENT_NOT_FORMAL_ACCEPTANCE'}|ConvertTo-Json -Depth 5|Set-Content -Encoding utf8 (Join-Path $receiptRoot 'result.json')
Get-Content (Join-Path $receiptRoot 'stdout.raw')|Select-Object -Last 16
Get-Content (Join-Path $receiptRoot 'stderr.raw')|Select-Object -Last 16
Write-Output "RECORDED_EXIT=$code RECEIPT=$receiptRoot"
exit $code
