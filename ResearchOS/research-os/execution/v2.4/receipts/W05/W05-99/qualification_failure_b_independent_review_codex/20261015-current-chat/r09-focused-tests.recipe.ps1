$ErrorActionPreference='Stop'
$W='D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-20261015'
$T='D:\作品集\ResearchOS\research-os\.local\qualification-failure-b-independent-review-20261015'
$env:GOPATH='D:\作品集\ResearchOS\research-os\.local\tools\gopath'
$env:GOCACHE="$T\gocache"
$env:GOTMPDIR="$T\gotmp"
$env:TEMP="$T\gotmp"
$env:TMP="$T\gotmp"
Set-Location $W
@{cwd=(Get-Location).Path;GOPATH=$env:GOPATH;GOCACHE=$env:GOCACHE;GOTMPDIR=$env:GOTMPDIR;TEMP=$env:TEMP;TMP=$env:TMP}|ConvertTo-Json
& 'D:\作品集\ResearchOS\research-os\.local\tools\go1.27.1\go\bin\go.exe' test -count=1 -timeout 180s -overlay "$T\overlay.json" -run '^Test(QualificationFailure|QualificationBrokerDrain|QualificationRejection|BridgeCancelKeepsFirstCause|IndependentQualification)' -v ./internal/domain ./adapters/runtime
$code=$LASTEXITCODE
@{native_exit=$code}|ConvertTo-Json|Set-Content 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_independent_review_codex\20261015-current-chat\r09.go-native-exit.json'
$global:LASTEXITCODE=$code
