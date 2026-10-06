param(
  [string]$FactsSourceCommit = 'a418d503f29646f62010905f9dc9338630aa0108'
)
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$guideRelative = 'docs/installation/user-guide.md'
$guidePath = Join-Path $repoRoot $guideRelative
$guide = Get-Content -Raw -LiteralPath $guidePath
$sourceCommit = (& git -C $repoRoot rev-parse HEAD).Trim()
$sourceFiles = @(
  'apps/web/src/main.jsx','apps/web/src/screens.jsx','apps/web/src/hooks.js',
  'apps/web/src/api.js','apps/web/src/operations.js','apps/web/src/Pairing.jsx',
  'apps/web/src/profile-draft.jsx','apps/web/src/preview.jsx','apps/web/src/style.css',
  'internal/domain/http.go','internal/domain/contracts.go','internal/domain/auth.go',
  'internal/domain/intent_planning.go','internal/domain/runtime.go',
  'internal/domain/acceptance.go','internal/domain/remote_auth.go',
  'internal/domain/resources.go','internal/domain/budget.go',
  'spec/v2.0/contracts/openapi.json',
  'tests/ui/browser_smoke.py','tests/ui/scenarios.py'
)
$sourceManifest = @()
foreach ($relative in $sourceFiles) {
  $path = Join-Path $repoRoot $relative
  $baseBlob = (& git -C $repoRoot rev-parse "${FactsSourceCommit}:$relative").Trim()
  $currentBlob = (& git -C $repoRoot rev-parse "HEAD:$relative").Trim()
  if ($baseBlob -ne $currentBlob) { throw "Facts source drift: $relative" }
  $sourceManifest += [ordered]@{path=$relative;git_blob=$baseBlob;sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
}
$c26Prefix = 'execution/receipts/W13/c26-recovery/'
$c26Manifest = Get-Content -Raw -LiteralPath (Join-Path $repoRoot ($c26Prefix+'manifest.json')) | ConvertFrom-Json
$links = @()
$missing = @()
foreach ($match in [regex]::Matches($guide, '\[[^\]]+\]\(([^)]+)\)')) {
  $target = $match.Groups[1].Value
  if ($target -match '^[a-zA-Z][a-zA-Z0-9+.-]*:' -or $target.StartsWith('/')) { throw "Unexpected absolute link: $target" }
  $path = [IO.Path]::GetFullPath((Join-Path (Split-Path $guidePath) $target))
  if (-not $path.StartsWith($repoRoot+[IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw "Link escapes repository: $target" }
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $missing += $target; continue }
  $relative = [IO.Path]::GetRelativePath($repoRoot, $path).Replace('\','/')
  $sha = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
  $entry = [ordered]@{target=$target;repository_path=$relative;bytes=(Get-Item -LiteralPath $path).Length;sha256=$sha}
  if ([IO.Path]::GetExtension($path) -eq '.png') {
    $bytes = [IO.File]::ReadAllBytes($path)
    if ([BitConverter]::ToString($bytes[0..7]) -ne '89-50-4E-47-0D-0A-1A-0A') { throw "Not PNG: $relative" }
    $entry.width = ([uint32]$bytes[16] -shl 24) -bor ([uint32]$bytes[17] -shl 16) -bor ([uint32]$bytes[18] -shl 8) -bor [uint32]$bytes[19]
    $entry.height = ([uint32]$bytes[20] -shl 24) -bor ([uint32]$bytes[21] -shl 16) -bor ([uint32]$bytes[22] -shl 8) -bor [uint32]$bytes[23]
    $reportPath = Join-Path (Split-Path $path) 'report.json'
    $report = Get-Content -Raw -LiteralPath $reportPath | ConvertFrom-Json
    $name = Split-Path $path -Leaf
    if ($name -notin $report.screenshots) { throw "Screenshot absent from saved report: $relative" }
    $expected = $report.screenshot_hashes.$name
    if (-not $expected -and $relative.StartsWith($c26Prefix)) { $expected = $c26Manifest.evidence_hashes.($relative.Substring($c26Prefix.Length)) }
    if ($expected -ne ('sha256:'+$sha)) { throw "Frozen screenshot hash mismatch: $relative" }
    $entry.report = [IO.Path]::GetRelativePath($repoRoot,$reportPath).Replace('\','/')
    $entry.report_head = $report.head
    $entry.frozen_hash_matches = $true
    $entry.scope = 'Existing development browser viewport; not physical mobile or sleep acceptance'
  }
  $links += $entry
}
$pageHeadings = @([regex]::Matches($guide, '(?m)^## (\d+)\. '))
$absolutePaths = @([regex]::Matches($guide, '(?i)\b[A-Z]:[\\/]'))
if ($pageHeadings.Count -ne 11) { throw "Expected eleven page sections, got $($pageHeadings.Count)" }
if ($absolutePaths.Count -ne 0) { throw 'Guide contains local absolute paths' }
$api = Get-Content -Raw -LiteralPath (Join-Path $repoRoot 'spec/v2.0/contracts/openapi.json') | ConvertFrom-Json
$wanted = @('createProject','createRequirement','actOnRequirement','actOnTask','cancelRun','sealArtifact','createChangeProposal','updateBudgetPolicy','updateRunPolicy','resolveResourceRequest','markNotificationRead','createDevicePairing','listDevices','updateDeviceGrants','revokeDevice')
$roles = @()
foreach ($path in $api.paths.PSObject.Properties) {
  foreach ($method in $path.Value.PSObject.Properties) {
    if ($method.Value.operationId -in $wanted) { $roles += @{operation=$method.Value.operationId;roles=$method.Value.'x-required-roles'} }
  }
}
$result = [ordered]@{
  schema='W20UserGuideMechanicalCheck/v1'
  status=$(if($missing.Count){'MISSING_LINKS'}else{'LINKS_AND_HASHES_VERIFIED_NOT_PRODUCT_ACCEPTANCE'})
  facts_source_commit=$FactsSourceCommit
  guide_source_commit=$sourceCommit
  guide=@{path=$guideRelative;sha256=(Get-FileHash -LiteralPath $guidePath -Algorithm SHA256).Hash.ToLowerInvariant();page_sections=$pageHeadings.Count}
  link_count=$links.Count
  screenshot_count=@($links | Where-Object repository_path -like '*.png').Count
  missing_links=$missing
  absolute_development_path_count=$absolutePaths.Count
  source_files=$sourceManifest
  operation_roles=$roles
  links=$links
  screenshot_gaps=@('Project entry: no standalone screenshot for four indexed theme/viewport cells','Workbench desktop dark: no existing standalone screenshot')
  limits=@('No browser or product tests run','No screenshot generated or copied','No native/provider/private activation or credential issuance','No real phone or physical OS sleep acceptance','Historical screenshot source heads differ from current facts baseline','Screenshot/execution links target original source repository, outside distribution bundle','README may be changed separately by integrator; this check pins its source-baseline hash')
}
$result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'link-check.json') -Encoding utf8
Write-Output "GUIDE_PAGES=$($pageHeadings.Count) LINKS=$($links.Count) SCREENSHOTS=$(@($links | Where-Object repository_path -like '*.png').Count) MISSING=$($missing.Count)"
if ($missing.Count) { exit 1 }
