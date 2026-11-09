$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
[Console]::OutputEncoding=[Text.UTF8Encoding]::new()
$w='D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-backend-20261104'
$r='D:/作品集/ResearchOS/research-os'
$b='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-backend-author/attempt-07'
New-Item -ItemType Directory -Path $b -ErrorAction Stop|Out-Null
$env:GOENV='off';$env:GOTOOLCHAIN='local';$env:GOPROXY='off';$env:GOSUMDB='off';$env:CGO_ENABLED='0'
$env:GOPATH=$r+'/.local/tools/gopath';$env:GOMODCACHE=$env:GOPATH+'/pkg/mod';$env:GOCACHE='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-backend-author/attempt-01/gocache';$env:GOTMPDIR=$b+'/tmp';$env:TEMP=$b+'/tmp';$env:TMP=$b+'/tmp'
New-Item -ItemType Directory -Path $env:GOTMPDIR|Out-Null
$go=$r+'/.local/tools/go1.27.1/go/bin/go.exe';$fmt=$r+'/.local/tools/go1.27.1/go/bin/gofmt.exe'
Set-Location -LiteralPath $w
$files=@('internal/domain/harness_v1.go','internal/domain/runtime_harness_windows.go','internal/host/harness_windows.go','internal/api/harness_v1.go','adapters/runtime/codex_driver_windows.go','apps/control/main.go','internal/api/server.go','internal/domain/runtime_coordinator_windows.go','internal/domain/runtime_dispatch.go','internal/domain/runtime_admission.go','internal/domain/runtime_recovery_windows.go','adapters/runtime/process_windows.go','adapters/runtime/codex.go','internal/domain/harness_v1_test.go','internal/domain/runtime_harness_windows_test.go','internal/host/harness_windows_test.go','internal/api/harness_v1_test.go','adapters/runtime/codex_driver_windows_test.go')
& $fmt -w @files *> ($b+'/fmt.log');$fmtExit=$LASTEXITCODE
@{exit_code=$fmtExit}|ConvertTo-Json|Set-Content -LiteralPath ($b+'/fmt.result.json')
if($fmtExit -ne 0){Get-Content ($b+'/fmt.log');exit $fmtExit}
$pins=@($files|ForEach-Object{@{path=$_;sha256=(Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash.ToLowerInvariant()}})
$pins|ConvertTo-Json -Depth 4|Set-Content -LiteralPath ($b+'/source-manifest.json')
& $go test -mod=readonly -p=2 -count=1 -timeout=120s -json -run '^(TestHarness|TestCodexHarness)' ./internal/domain ./internal/api ./internal/host ./adapters/runtime *> ($b+'/test.jsonl')
$testExit=$LASTEXITCODE
@{exit_code=$testExit;fixture_only=$true}|ConvertTo-Json|Set-Content -LiteralPath ($b+'/test.result.json')
if($testExit -ne 0){Get-Content -LiteralPath ($b+'/test.jsonl') -Tail 65;exit $testExit}
& $go vet -mod=readonly -p=2 ./internal/domain ./internal/api ./internal/host ./adapters/runtime ./apps/control *> ($b+'/vet.log')
$vetExit=$LASTEXITCODE
@{exit_code=$vetExit}|ConvertTo-Json|Set-Content -LiteralPath ($b+'/vet.result.json')
Get-Content -LiteralPath ($b+'/test.jsonl') -Tail 10
exit $vetExit
