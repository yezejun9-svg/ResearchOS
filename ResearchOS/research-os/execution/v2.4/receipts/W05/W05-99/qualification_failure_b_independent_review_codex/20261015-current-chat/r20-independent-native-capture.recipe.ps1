$ErrorActionPreference='Stop'
$W='D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-20261015'
$T='D:\作品集\ResearchOS\research-os\.local\qualification-failure-b-independent-review-20261015'
$E='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_independent_review_codex\20261015-current-chat'
Copy-Item -LiteralPath "$T\overlay\runtime_qualification_failure_windows_test_v2.go" -Destination "$E\independent-domain-overlay.go"
Copy-Item -LiteralPath "$T\overlay\qualification_failure_proof_windows_test.go" -Destination "$E\independent-adapter-overlay.go"
$replace=@{}
$replace["$W\internal\domain\runtime_qualification_failure_windows_test.go"]="$E\independent-domain-overlay.go"
$replace["$W\adapters\runtime\qualification_failure_proof_windows_test.go"]="$E\independent-adapter-overlay.go"
@{Replace=$replace}|ConvertTo-Json|Set-Content -Encoding utf8 "$E\independent-overlay.json"
$env:GOPATH='D:\作品集\ResearchOS\research-os\.local\tools\gopath'
$env:GOCACHE="$T\gocache";$env:GOTMPDIR="$T\gotmp";$env:TEMP="$T\gotmp";$env:TMP="$T\gotmp"
Set-Location $W
@{cwd=(Get-Location).Path;GOPATH=$env:GOPATH;GOCACHE=$env:GOCACHE;GOTMPDIR=$env:GOTMPDIR;TEMP=$env:TEMP;TMP=$env:TMP;reason='Bounded repeat of three independent cuts to capture separate native byte stdout/stderr; no historical suite rerun'}|ConvertTo-Json|Set-Content "$E\r20.test-env.json"
& 'D:\作品集\ResearchOS\research-os\.local\tools\go1.27.1\go\bin\go.exe' test -count=1 -timeout 90s -overlay "$E\independent-overlay.json" -run '^TestIndependentQualification' -v ./internal/domain ./adapters/runtime 1> "$E\r20.go.stdout.raw" 2> "$E\r20.go.stderr.raw"
$code=$LASTEXITCODE
@{native_exit=$code}|ConvertTo-Json|Set-Content "$E\r20.go-native-exit.json"
Get-Content "$E\r20.go.stdout.raw"
Get-Content "$E\r20.go.stderr.raw"
$global:LASTEXITCODE=$code
