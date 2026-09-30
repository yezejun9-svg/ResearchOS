$ErrorActionPreference = 'Stop'
$reviewRoot = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\')
$expectedSuffix = '\execution\verifier\W20\r1-14bf6d6'
if (-not $reviewRoot.EndsWith($expectedSuffix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unexpected review root' }
$targets = @('fixture-release', 'dirty-build\source-checkout', 'fixture-probe\data-a', 'fixture-probe\data-b')
$result = @()
foreach ($relative in $targets) {
    $target = [IO.Path]::GetFullPath((Join-Path $reviewRoot $relative))
    if (-not $target.StartsWith($reviewRoot + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Cleanup escaped assigned review directory' }
    if (-not (Test-Path -LiteralPath $target)) { throw "Owned cleanup target missing: $relative" }
    if (((Get-Item -LiteralPath $target).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "Root is a reparse point: $relative" }
    $files = @(Get-ChildItem -LiteralPath $target -File -Force -Recurse)
    $result += @{path=$target; files=$files.Count; bytes=($files | Measure-Object Length -Sum).Sum}
}
$result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $reviewRoot 'cleanup-owned-targets.json') -Encoding utf8
foreach ($entry in $result) { Remove-Item -LiteralPath $entry.path -Recurse -Force }
@{removed=$targets; scope='Only new reviewer-owned disposable working directories; original evidence and prior policy-denied paths retained'} | ConvertTo-Json -Compress
