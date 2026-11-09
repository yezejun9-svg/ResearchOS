$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
[Console]::OutputEncoding=[Text.UTF8Encoding]::new()
$w='D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-backend-20261104'
$r='D:/作品集/ResearchOS/research-os'
$b='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-backend-author/attempt-01'
New-Item -ItemType Directory -Path $b -ErrorAction Stop|Out-Null
$env:GOENV='off';$env:GOTOOLCHAIN='local';$env:GOPROXY='off';$env:GOSUMDB='off';$env:CGO_ENABLED='0'
$env:GOPATH=$r+'/.local/tools/gopath';$env:GOMODCACHE=$env:GOPATH+'/pkg/mod';$env:GOCACHE=$b+'/gocache';$env:GOTMPDIR=$b+'/tmp'
New-Item -ItemType Directory -Path $env:GOTMPDIR|Out-Null
$go=$r+'/.local/tools/go1.27.1/go/bin/go.exe'
$fmt=$r+'/.local/tools/go1.27.1/go/bin/gofmt.exe'
Set-Location -LiteralPath $w
$files=@('internal/domain/harness_v1.go','internal/domain/runtime_harness_windows.go','internal/host/harness_windows.go','internal/api/harness_v1.go','adapters/runtime/codex_driver_windows.go','apps/control/main.go','internal/api/server.go','internal/domain/runtime_coordinator_windows.go','internal/domain/runtime_dispatch.go','internal/domain/runtime_admission.go','internal/domain/runtime_recovery_windows.go','adapters/runtime/process_windows.go','adapters/runtime/codex.go')
& $fmt -w @files *> ($b+'/fmt.log')
$fmtExit=$LASTEXITCODE
@{exit_code=$fmtExit}|ConvertTo-Json|Set-Content -LiteralPath ($b+'/fmt.result.json')
if($fmtExit -ne 0){exit $fmtExit}
& $go test -mod=readonly -p=2 -run '^$' ./internal/domain ./internal/api ./internal/host ./adapters/runtime ./apps/control *> ($b+'/compile.log')
$compileExit=$LASTEXITCODE
@{exit_code=$compileExit;kind='compile-only-zero-tests'}|ConvertTo-Json|Set-Content -LiteralPath ($b+'/compile.result.json')
Get-Content -LiteralPath ($b+'/compile.log') -Tail 50
exit $compileExit
