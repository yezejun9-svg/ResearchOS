$ErrorActionPreference = 'Stop'
function Get-FileHash { param([string]$LiteralPath,[string]$Algorithm) $stream=[IO.File]::OpenRead($LiteralPath); try { $sha=[Security.Cryptography.SHA256]::Create(); $hex=[BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-',''); [pscustomobject]@{Path=$LiteralPath;Hash=$hex} } finally {$stream.Dispose()} }
$ErrorActionPreference = 'Stop'
$base = 'D:/作品集/ResearchOS/research-os'
$scopePath = "$base/execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp528/original-backup-process-binding-readonly-scope.json"
$scope = [IO.File]::ReadAllText($scopePath) | ConvertFrom-Json
Get-FileHash -LiteralPath $scopePath -Algorithm SHA256 | Select-Object Path,Hash | ConvertTo-Json -Compress
foreach ($entry in $scope.inputs) {
 $p = Join-Path $base $entry.path
 $h = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()
 [ordered]@{path=$entry.path; bytes=(Get-Item -LiteralPath $p).Length; sha256=$h; hash_match=($h -eq $entry.sha256)} | ConvertTo-Json -Compress
 [IO.File]::ReadAllText($p)
}
$src = 'D:/作品集/ResearchOS/research-os/.local/worktrees/online-backup-fixture-qualification-20261015'
& git -C $src rev-parse HEAD
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
foreach ($p in @("$base/.local/AGENTS.md","$base/.local/worktrees/AGENTS.md","$src/AGENTS.md","$src/apps/AGENTS.md","$src/apps/control/AGENTS.md","$src/ops/AGENTS.md","$src/ops/backup/AGENTS.md")) {
 if (Test-Path -LiteralPath $p) { "AGENTS: $p"; [IO.File]::ReadAllText($p) }
}
& rg -n --glob '*.go' 'NewRuntimeSetup|runtimeAssetsDir|host\.Config|host\.New|func main|backup' "$src/apps/control" "$src/ops/backup"
if ($LASTEXITCODE -gt 1) { exit $LASTEXITCODE }