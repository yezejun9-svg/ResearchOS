$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new()
$wt='D:/作品集/ResearchOS/research-os/.local/worktrees/host-candidate-capture-20261104'
$base='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/cp599-candidate-capture-author'
$attempt=Join-Path $base 'attempt-01'
if(Test-Path -LiteralPath $attempt){throw 'attempt exists; inspect outcome, never replay'}
$null=New-Item -ItemType Directory -Path $attempt
$profile=Join-Path $base 'isolated-profile'
foreach($p in @($profile,(Join-Path $profile 'cache'),(Join-Path $profile 'gopath'),(Join-Path $attempt 'tmp'),(Join-Path $attempt 'snapshot'))){$null=New-Item -ItemType Directory -Force -Path $p}
$env:GOENV='off';$env:GOTOOLCHAIN='local';$env:GOPROXY='off';$env:GOSUMDB='off';$env:CGO_ENABLED='0';$env:GOWORK='off'
$env:GOROOT='D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go'
$env:GOMODCACHE='D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod'
$env:GOPATH=Join-Path $profile 'gopath';$env:GOCACHE=Join-Path $profile 'cache';$env:GOMAXPROCS='2';$env:GOFLAGS='-mod=readonly -p=2'
$env:USERPROFILE=$profile;$env:APPDATA=Join-Path $profile 'AppData/Roaming';$env:LOCALAPPDATA=Join-Path $profile 'AppData/Local'
$env:TEMP=Join-Path $attempt 'tmp';$env:TMP=$env:TEMP;$env:GOTMPDIR=$env:TEMP
$goTool=Join-Path $env:GOROOT 'bin/go.exe';$fmtTool=Join-Path $env:GOROOT 'bin/gofmt.exe'
$paths=@('internal/domain/runtime_tools.go','internal/domain/runtime_tools_capture.go','internal/domain/runtime_tools_capture_test.go','internal/host/runtime_check_windows.go','internal/host/runtime_check_delivery_windows.go','internal/host/runtime_check_delivery_windows_test.go')
function SaveJSON($name,$value){[IO.File]::WriteAllText((Join-Path $attempt $name),($value|ConvertTo-Json -Depth 7),[Text.UTF8Encoding]::new($false))}
Set-Location -LiteralPath $wt
SaveJSON 'environment.json' ([ordered]@{tool=$goTool;tool_sha256=(Get-FileHash -LiteralPath $goTool -Algorithm SHA256).Hash.ToLowerInvariant();goenv=$env:GOENV;gotoolchain=$env:GOTOOLCHAIN;goproxy=$env:GOPROXY;gosumdb=$env:GOSUMDB;gomodcache=$env:GOMODCACHE;gocache=$env:GOCACHE;gopath=$env:GOPATH;go_flags=$env:GOFLAGS;scope='PURE_TEMP_DIRECTORY_FIXTURES_ONLY'})
SaveJSON 'gofmt.command.json' @{executable=$fmtTool;args=@('-w')+$paths}
& $fmtTool -w @paths 1> (Join-Path $attempt 'gofmt.stdout.txt') 2> (Join-Path $attempt 'gofmt.stderr.txt')
$formatExit=$LASTEXITCODE;SaveJSON 'gofmt.result.json' @{exit_code=$formatExit}
$pins=foreach($rel in $paths){$p=Join-Path $wt $rel;Copy-Item -LiteralPath $p -Destination (Join-Path $attempt ('snapshot/'+[IO.Path]::GetFileName($p)));[ordered]@{path=$rel;sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant();bytes=(Get-Item -LiteralPath $p).Length}}
SaveJSON 'source-manifest.json' $pins
if($formatExit -ne 0){SaveJSON 'test.result.json' @{status='NOT_RUN_FORMAT_FAILED'};SaveJSON 'vet.result.json' @{status='NOT_RUN_FORMAT_FAILED'};exit $formatExit}
$argsTest=@('test','-json','-count=1','-vet=off','-timeout=120s','-run','^(TestRuntimeToolCapture|TestRuntimeCandidateCapture)','./internal/domain','./internal/host')
SaveJSON 'test.command.json' @{executable=$goTool;args=$argsTest}
& $goTool @argsTest 1> (Join-Path $attempt 'test.stdout.jsonl') 2> (Join-Path $attempt 'test.stderr.txt')
$testExit=$LASTEXITCODE
$events=@(Get-Content -LiteralPath (Join-Path $attempt 'test.stdout.jsonl') -Encoding UTF8|ForEach-Object{try{$_|ConvertFrom-Json -ErrorAction Stop}catch{}})
$pass=@($events|Where-Object {$_.Action -eq 'pass' -and $_.Test})
SaveJSON 'test.result.json' ([ordered]@{exit_code=$testExit;test_pass_events=$pass.Count;top_pass=@($pass|Where-Object {$_.Test -notmatch '/'}).Count;sub_pass=@($pass|Where-Object {$_.Test -match '/'}).Count;test_fail_events=@($events|Where-Object {$_.Action -eq 'fail' -and $_.Test}).Count;skips=@($events|Where-Object {$_.Action -eq 'skip'}).Count;package_pass=@($events|Where-Object {$_.Action -eq 'pass' -and -not $_.Test}).Count})
if($testExit -ne 0){SaveJSON 'vet.result.json' @{status='NOT_RUN_TEST_FAILED'};Get-Content -LiteralPath (Join-Path $attempt 'test.result.json') -Raw;Get-Content -LiteralPath (Join-Path $attempt 'test.stderr.txt') -Tail 25;Get-Content -LiteralPath (Join-Path $attempt 'test.stdout.jsonl') -Tail 25;exit $testExit}
SaveJSON 'vet.command.json' @{executable=$goTool;args=@('vet','./internal/domain','./internal/host')}
& $goTool vet ./internal/domain ./internal/host 1> (Join-Path $attempt 'vet.stdout.txt') 2> (Join-Path $attempt 'vet.stderr.txt')
$vetExit=$LASTEXITCODE;SaveJSON 'vet.result.json' @{exit_code=$vetExit}
Get-Content -LiteralPath (Join-Path $attempt 'test.result.json') -Raw;Get-Content -LiteralPath (Join-Path $attempt 'vet.result.json') -Raw
exit $vetExit

