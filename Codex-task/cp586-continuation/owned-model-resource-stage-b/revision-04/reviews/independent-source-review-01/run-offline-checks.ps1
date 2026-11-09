$ErrorActionPreference = 'Stop'
$reviewRoot = 'C:\Users\yqyyds\Documents\Codex\2026-11-04\task\cp586-continuation\owned-model-resource-stage-b\revision-04'
$reviewOut = Join-Path $reviewRoot 'reviews\independent-source-review-01'
$reviewRepo = 'D:\' + [string]::Concat([char]0x4f5c,[char]0x54c1,[char]0x96c6) + '\ResearchOS\research-os'
$reviewGo = Join-Path $reviewRepo '.local\tools\go1.27.1\go\bin\go.exe'
$reviewExpectedGo = 'd3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490'
if ((Get-FileHash -LiteralPath $reviewGo -Algorithm SHA256).Hash.ToLowerInvariant() -ne $reviewExpectedGo) { throw 'Go pin mismatch' }
if (Test-Path -LiteralPath (Join-Path $reviewOut 'offline-checks.json')) { throw 'One-use offline checks already exist' }
$env:GOENV = 'off'
$env:GOTOOLCHAIN = 'local'
$env:GOPROXY = 'off'
$env:GOSUMDB = 'off'
$env:GOTELEMETRY = 'off'
$env:GOFLAGS = '-mod=readonly'
$env:GOCACHE = Join-Path $reviewOut 'go-cache'
$env:GOMODCACHE = Join-Path $reviewRepo '.local\tools\gopath\pkg\mod'
$env:GOTMPDIR = Join-Path $reviewOut 'go-tmp'
New-Item -ItemType Directory -Path $env:GOCACHE,$env:GOTMPDIR -ErrorAction Stop | Out-Null
Set-Location -LiteralPath $reviewRoot
$reviewChecks = [ordered]@{
  schema = 'researchos.stage-b-r4-independent-offline-checks.v1'
  started_utc = [DateTime]::UtcNow.ToString('o')
  locked_go_sha256 = $reviewExpectedGo
  environment = @{GOENV='off';GOTOOLCHAIN='local';GOPROXY='off';GOSUMDB='off';GOTELEMETRY='off';GOFLAGS='-mod=readonly';GOCACHE=$env:GOCACHE;GOMODCACHE=$env:GOMODCACHE;GOTMPDIR=$env:GOTMPDIR}
  controller_executions = 0
  native_backend_executions = 0
  real_network_requests = 0
  model_GPU_starts = 0
  inference = 0
  D_writes = 0
  formal_increment = 0
  counter_reset = $false
}
$reviewChecks | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $reviewOut 'offline-checks-started.json') -Encoding utf8
& $reviewGo test -json -count=1 -timeout=20s connection.go lifecycle.go boundaries_test.go *> (Join-Path $reviewOut 'pure-fixtures-01.jsonl')
$reviewChecks.pure_fixture_exit = $LASTEXITCODE
$reviewChecks.pure_fixture_command = 'go test -json -count=1 -timeout=20s connection.go lifecycle.go boundaries_test.go'
$reviewChecks | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $reviewOut 'offline-checks.json') -Encoding utf8
& $reviewGo build -trimpath -o (Join-Path $reviewOut 'controller.compile-only.exe') . *> (Join-Path $reviewOut 'compile-01.log')
$reviewChecks.build_exit = $LASTEXITCODE
$reviewChecks.build_command = 'go build -trimpath -o reviews/independent-source-review-01/controller.compile-only.exe .'
$reviewChecks | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $reviewOut 'offline-checks.json') -Encoding utf8
& $reviewGo vet . *> (Join-Path $reviewOut 'vet-01.log')
$reviewChecks.vet_exit = $LASTEXITCODE
$reviewChecks.vet_command = 'go vet .'
$reviewChecks.finished_utc = [DateTime]::UtcNow.ToString('o')
$reviewChecks | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $reviewOut 'offline-checks.json') -Encoding utf8
$reviewChecks | ConvertTo-Json -Depth 5
if ($reviewChecks.pure_fixture_exit -ne 0 -or $reviewChecks.build_exit -ne 0 -or $reviewChecks.vet_exit -ne 0) { exit 1 }

