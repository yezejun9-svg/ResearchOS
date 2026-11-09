$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
[Console]::OutputEncoding=[Text.UTF8Encoding]::new()
$w='D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-backend-20261104'
$r='D:/作品集/ResearchOS/research-os'
$b='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-backend-author/attempt-06-compatibility'
New-Item -ItemType Directory -Path $b -ErrorAction Stop|Out-Null
$env:GOENV='off';$env:GOTOOLCHAIN='local';$env:GOPROXY='off';$env:GOSUMDB='off';$env:CGO_ENABLED='0'
$env:GOPATH=$r+'/.local/tools/gopath';$env:GOMODCACHE=$env:GOPATH+'/pkg/mod';$env:GOCACHE='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-backend-author/attempt-01/gocache';$env:GOTMPDIR=$b+'/tmp'
New-Item -ItemType Directory -Path $env:GOTMPDIR|Out-Null
Set-Location -LiteralPath $w
& ($r+'/.local/tools/go1.27.1/go/bin/go.exe') test -mod=readonly -p=2 -count=1 -timeout=30s -json -run '^TestW05Protocol(TransientReconnect)?$' ./adapters/runtime *> ($b+'/test.jsonl')
$code=$LASTEXITCODE
@{exit_code=$code;kind='existing-pure-parser-compatibility';native_processes=$false}|ConvertTo-Json|Set-Content -LiteralPath ($b+'/test.result.json')
Get-Content -LiteralPath ($b+'/test.jsonl') -Tail 6
exit $code
