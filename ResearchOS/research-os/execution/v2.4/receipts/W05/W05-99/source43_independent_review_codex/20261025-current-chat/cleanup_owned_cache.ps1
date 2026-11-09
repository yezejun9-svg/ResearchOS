$ErrorActionPreference = 'Stop'
$fixtureBase = 'C:\Users\yqyyds\.codex\researchos-fixture-cache\source43-independent-review-20261025'
$resolvedBase = (Resolve-Path -LiteralPath $fixtureBase).Path
if ($resolvedBase -ne $fixtureBase) { throw 'Unexpected fixture base' }
$owner = Get-Content -LiteralPath (Join-Path $fixtureBase 'OWNER.json') -Raw | ConvertFrom-Json
if ($owner.owner -ne 'codex:/root/source43_independent_review_20261025') { throw 'Unexpected owner' }
foreach ($leaf in @('gocache','tmp','roots')) {
    $target = Join-Path $resolvedBase $leaf
    $resolvedTarget = (Resolve-Path -LiteralPath $target).Path
    if (-not $resolvedTarget.StartsWith($resolvedBase + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Target escapes owned root' }
    $entries = @(Get-Item -LiteralPath $resolvedTarget -Force) + @(Get-ChildItem -LiteralPath $resolvedTarget -Recurse -Force)
    if ($entries | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }) { throw 'Reparse target refused' }
    Remove-Item -LiteralPath $resolvedTarget -Recurse -Force
    Write-Output "REMOVED owned cache: $resolvedTarget"
}
