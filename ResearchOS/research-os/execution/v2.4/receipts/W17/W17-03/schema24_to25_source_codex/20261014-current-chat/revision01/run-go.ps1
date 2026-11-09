param([Parameter(Mandatory=$true)][string]$Name,[Parameter(Mandatory=$true)][string[]]$Arguments)
$ErrorActionPreference='Stop'
$evidence=$PSScriptRoot
$candidate='D:/作品集/ResearchOS/research-os/.local/worktrees/schema24-to25-native-20261014'
$env:GOROOT='D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go'
$env:GOMODCACHE='D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod'
$env:GOCACHE='D:/作品集/ResearchOS/research-os/.local/go-cache/mu-m1-core-20261014'
$env:GOTMPDIR='D:/作品集/ResearchOS/research-os/.local/go-tmp/schema24-to25-native-20261014'
$env:TEMP=$env:GOTMPDIR
$env:TMP=$env:GOTMPDIR
$env:GOPROXY='off'
$env:GOSUMDB='off'
$env:GOTOOLCHAIN='local'
$env:GOWORK='off'
$capture=Join-Path $evidence $Name
if(Test-Path -LiteralPath $capture){throw 'Capture already exists; history cannot be overwritten'}
New-Item -ItemType Directory -Path $capture | Out-Null
Set-Location -LiteralPath $candidate
$scope=Get-Content -Raw -LiteralPath (Join-Path $evidence 'scope.json') | ConvertFrom-Json
$inputs=@($scope.paths | ForEach-Object { $file=Join-Path $candidate $_; if(Test-Path -LiteralPath $file){@{path=$_;sha256=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLower()}} })
$inputs | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $capture 'inputs.json') -Encoding utf8
$started=[DateTime]::UtcNow.ToString('o')
& "$env:GOROOT/bin/go.exe" @Arguments 1> (Join-Path $capture 'stdout.jsonl') 2> (Join-Path $capture 'stderr.txt')
$code=$LASTEXITCODE
$command=@{argv=@("$env:GOROOT/bin/go.exe")+$Arguments;cwd=$candidate;started=$started;finished=[DateTime]::UtcNow.ToString('o');exit=$code;environment=@{GOROOT=$env:GOROOT;GOMODCACHE=$env:GOMODCACHE;GOCACHE=$env:GOCACHE;GOTMPDIR=$env:GOTMPDIR;TEMP=$env:TEMP;TMP=$env:TMP;GOPROXY=$env:GOPROXY;GOSUMDB=$env:GOSUMDB;GOTOOLCHAIN=$env:GOTOOLCHAIN;GOWORK=$env:GOWORK}}
$command | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $capture 'command.json') -Encoding utf8
$ledgerPath=Join-Path $evidence 'ledger.json'
$ledger=Get-Content -Raw -LiteralPath $ledgerPath | ConvertFrom-Json
$ledger.attempts=@($ledger.attempts)+@(@{name=$Name;exit=$code;started=$started;command_sha256=(Get-FileHash -LiteralPath (Join-Path $capture 'command.json') -Algorithm SHA256).Hash.ToLower()})
if($code -ne 0){$ledger.failed_attempt_count++}
$ledger | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ledgerPath -Encoding utf8
Get-Content -LiteralPath (Join-Path $capture 'stderr.txt')
Get-Content -LiteralPath (Join-Path $capture 'stdout.jsonl') -Tail 12
exit $code
