
$ErrorActionPreference = 'Stop'
$root = 'D:\作品集\ResearchOS\research-os'
$wt = Join-Path $root '.local\worktrees\online-backup-fixture-qualification-20261015'
foreach ($path in @('D:\AGENTS.md','D:\作品集\AGENTS.md','D:\作品集\ResearchOS\AGENTS.md', (Join-Path $root 'AGENTS.md'),(Join-Path $wt 'AGENTS.md'))) {
  "AGENTS_PATH=$path EXISTS=$(Test-Path -LiteralPath $path)"
  if (Test-Path -LiteralPath $path) { Get-Content -LiteralPath $path -Raw -Encoding UTF8 }
}
$scope=Get-Content -LiteralPath (Join-Path $root 'execution\v2.4\receipts\W05\W05-99\resume_cp398_codex\20261015-current-chat\continuation-cp526\host-stored-finalpath-source-diagnosis-scope.json') -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($item in $scope.inputs) {
 $p=Join-Path $root $item.path
 $hash=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()
 "FROZEN_INPUT=$p HASH=$hash EXPECTED=$($item.sha256)"
 if ($hash -ne $item.sha256) { throw 'Frozen input hash mismatch' }
 if ($item.path -match 'resource-map.json|limited-fixture-adoption.json') { Get-Content -LiteralPath $p -Raw -Encoding UTF8 }
}
& rg -n --glob '*.go' --glob 'AGENTS.md' 'GetFinalPathNameByHandle|SnapshotWorkspace|final_path|FinalPath' $wt
$native=$LASTEXITCODE
"NATIVE_RG_EXIT=$native"
if($native -gt 1){exit $native}
