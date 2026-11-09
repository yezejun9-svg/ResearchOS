$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
[Console]::OutputEncoding=[Text.UTF8Encoding]::new()
$r='D:/作品集/ResearchOS/research-os'
$w=$r+'/.local/worktrees/product-v1-cli-20261104'
$b='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-cli-s04-author/attempt-02'
New-Item -ItemType Directory -Path $b -ErrorAction Stop|Out-Null
$env:GOENV='off';$env:GOTOOLCHAIN='local';$env:GOPROXY='off';$env:GOSUMDB='off';$env:CGO_ENABLED='0'
$env:GOPATH=$r+'/.local/tools/gopath';$env:GOMODCACHE=$env:GOPATH+'/pkg/mod';$env:GOCACHE=$b+'/gocache';$env:GOTMPDIR=$b+'/tmp';$env:TEMP=$b+'/tmp';$env:TMP=$b+'/tmp'
New-Item -ItemType Directory -Path $env:GOTMPDIR|Out-Null
$go=$r+'/.local/tools/go1.27.1/go/bin/go.exe';$fmt=$r+'/.local/tools/go1.27.1/go/bin/gofmt.exe'
Set-Location -LiteralPath $w
$paths=@('apps/cli/main.go','apps/cli/productv1.go','apps/cli/productv1_test.go')
& $fmt -w @paths *> ($b+'/fmt.log');$fmtExit=$LASTEXITCODE
@{exit_code=$fmtExit}|ConvertTo-Json|Set-Content -LiteralPath ($b+'/fmt.result.json')
if($fmtExit -ne 0){Get-Content -LiteralPath ($b+'/fmt.log');exit $fmtExit}
$pins=@($paths|ForEach-Object{[ordered]@{path=$_;sha256=(Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash.ToLowerInvariant()}})
$pins|ConvertTo-Json -Depth 4|Set-Content -LiteralPath ($b+'/source-manifest.json')
& $go test -mod=readonly -p=2 -count=1 -timeout=120s -json -run '^(TestS04|TestCLIPrompt(ParseExplicit|LegacyArgsUntouched|RejectInvalid|SurfaceQualifications|ExactInt64HostArguments)$)' ./apps/cli *> ($b+'/test.jsonl')
$testExit=$LASTEXITCODE
@{exit_code=$testExit;fixture_only=$true;real_cli=$false;model=$false}|ConvertTo-Json|Set-Content -LiteralPath ($b+'/test.result.json')
if($testExit -ne 0){Get-Content -LiteralPath ($b+'/test.jsonl') -Tail 45;exit $testExit}
& $go vet -mod=readonly -p=2 ./apps/cli *> ($b+'/vet.log');$vetExit=$LASTEXITCODE
@{exit_code=$vetExit}|ConvertTo-Json|Set-Content -LiteralPath ($b+'/vet.result.json')
Get-Content -LiteralPath ($b+'/test.jsonl') -Tail 6
exit $vetExit
