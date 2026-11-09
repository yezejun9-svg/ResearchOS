$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
$OutputEncoding=[Console]::OutputEncoding=[Text.UTF8Encoding]::new()
$repoRoot='D:/作品集/ResearchOS/research-os'
$worktreeRoot=$repoRoot+'/.local/worktrees/product-v1-source-context-20261104'
$attemptRoot='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-source-context-author-20261104/attempt-01'
New-Item -ItemType Directory -Path $attemptRoot -ErrorAction Stop|Out-Null
$env:GOENV='off';$env:GOTOOLCHAIN='local';$env:GOPROXY='off';$env:GOSUMDB='off';$env:CGO_ENABLED='0';$env:GOMAXPROCS='2';$env:GOFLAGS='-mod=readonly -p=2'
$env:GOPATH=$repoRoot+'/.local/tools/gopath';$env:GOMODCACHE=$env:GOPATH+'/pkg/mod';$env:GOCACHE=$attemptRoot+'/gocache';$env:GOTMPDIR=$attemptRoot+'/tmp';$env:TEMP=$env:GOTMPDIR;$env:TMP=$env:GOTMPDIR
New-Item -ItemType Directory -Path $env:GOTMPDIR|Out-Null
$goExe=$repoRoot+'/.local/tools/go1.27.1/go/bin/go.exe';$fmtExe=$repoRoot+'/.local/tools/go1.27.1/go/bin/gofmt.exe'
$paths=@('adapters/runtime/codex_driver_windows.go','adapters/runtime/codex_driver_windows_test.go','internal/domain/runtime_harness_windows_test.go')
$selector='^(TestCodexHarness(ExecutionSourceContext|ExecutionInputBudget|FixedArguments|NativeLifecycle)$|TestHarness(CoordinatorFakeChain|UnknownTransitionAtomic)$)'
@{source_scope='PRODUCT_V1_REGISTERED_SOURCE_CONTEXT/rev2';base='dd00c61c6ede0b1b3233479606ee711bff65ed54';go_executable=$goExe;go_sha256=(Get-FileHash -LiteralPath $goExe).Hash.ToLowerInvariant();working_directory=$worktreeRoot;environment=@{GOENV=$env:GOENV;GOTOOLCHAIN=$env:GOTOOLCHAIN;GOPROXY=$env:GOPROXY;GOSUMDB=$env:GOSUMDB;GOMODCACHE=$env:GOMODCACHE;GOCACHE=$env:GOCACHE;GOTMPDIR=$env:GOTMPDIR;GOMAXPROCS=$env:GOMAXPROCS;GOFLAGS=$env:GOFLAGS};test_args=@('test','-mod=readonly','-p=2','-parallel=2','-count=1','-timeout=120s','-json','-run',$selector,'./adapters/runtime','./internal/domain');fixture_class='pure data plus existing owned fake Go processes and fresh test databases; no real CLI/model/auth/old DB';started_utc=[DateTime]::UtcNow.ToString('o')}|ConvertTo-Json -Depth 5|Set-Content -Encoding UTF8 -LiteralPath ($attemptRoot+'/command.json')
Set-Location -LiteralPath $worktreeRoot
& $fmtExe -w @paths *> ($attemptRoot+'/fmt.log');$fmtExit=$LASTEXITCODE
@{exit_code=$fmtExit}|ConvertTo-Json|Set-Content -Encoding UTF8 -LiteralPath ($attemptRoot+'/fmt.result.json')
if($fmtExit -ne 0){Get-Content -LiteralPath ($attemptRoot+'/fmt.log');exit $fmtExit}
$pins=@(foreach($path in $paths){$destination=Join-Path ($attemptRoot+'/source') $path;New-Item -ItemType Directory -Force -Path (Split-Path $destination)|Out-Null;Copy-Item -LiteralPath $path -Destination $destination;@{path=$path;sha256=(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant()}})
$pins|ConvertTo-Json -Depth 4|Set-Content -Encoding UTF8 -LiteralPath ($attemptRoot+'/source-manifest.json')
& $goExe test -mod=readonly -p=2 -parallel=2 -count=1 -timeout=120s -json -run $selector ./adapters/runtime ./internal/domain *> ($attemptRoot+'/test.jsonl');$testExit=$LASTEXITCODE
@{exit_code=$testExit;fixture_only=$true;real_cli=$false;model=$false;completed_utc=[DateTime]::UtcNow.ToString('o')}|ConvertTo-Json|Set-Content -Encoding UTF8 -LiteralPath ($attemptRoot+'/test.result.json')
if($testExit -ne 0){@{status='NOT_RUN';reason='selected test failed'}|ConvertTo-Json|Set-Content -Encoding UTF8 -LiteralPath ($attemptRoot+'/vet.result.json');Get-Content -LiteralPath ($attemptRoot+'/test.jsonl') -Tail 35;exit $testExit}
& $goExe vet -mod=readonly -p=2 ./adapters/runtime ./internal/domain *> ($attemptRoot+'/vet.log');$vetExit=$LASTEXITCODE
@{exit_code=$vetExit;completed_utc=[DateTime]::UtcNow.ToString('o')}|ConvertTo-Json|Set-Content -Encoding UTF8 -LiteralPath ($attemptRoot+'/vet.result.json')
Get-Content -LiteralPath ($attemptRoot+'/test.jsonl') -Tail 5
exit $vetExit
