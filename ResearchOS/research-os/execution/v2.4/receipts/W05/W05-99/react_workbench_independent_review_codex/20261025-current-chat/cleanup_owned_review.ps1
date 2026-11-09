$ErrorActionPreference = 'Stop'
$ownedRoots = @('C:/Users/yqyyds/.codex/researchos-fixture-cache/react-workbench-independent-review-20261025', 'D:/作品集/ResearchOS/research-os/.local/react-workbench-independent-review-20261025-tmp')
$removed = @()
foreach ($ownedPath in $ownedRoots) {
  $expected = [System.IO.Path]::GetFullPath($ownedPath)
  $resolved = (Resolve-Path -LiteralPath $ownedPath).Path
  if (-not [string]::Equals($resolved.TrimEnd('\'), $expected.TrimEnd('\'), [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Owned cleanup path mismatch' }
  $items = @(Get-ChildItem -LiteralPath $resolved -Force -Recurse)
  if (@($items | Where-Object { $_.Attributes -band [System.IO.FileAttributes]::ReparsePoint }).Count -gt 0) { throw 'Unexpected link inside owned cleanup tree' }
  Remove-Item -LiteralPath $resolved -Recurse -Force
  $removed += @{ path = $expected; removed = -not (Test-Path -LiteralPath $expected); entries = $items.Count }
}
$removed | ConvertTo-Json -Depth 5
