$ErrorActionPreference = 'Stop'
$base = [IO.Path]::GetFullPath($PSScriptRoot)
if (-not $base.EndsWith('\execution\verifier\W20\r1-14bf6d6\fix-6de7543')) { throw 'Unexpected cleanup root' }
$relative = @('source-checkout','fixture-release','fixture-probe\data-a','fixture-probe\data-b','fixture-probe-v2\data-a','fixture-probe-v2\data-b')
$targets = @()
foreach ($name in $relative) {
  $target = [IO.Path]::GetFullPath((Join-Path $base $name))
  if (-not $target.StartsWith($base + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Cleanup escapes root' }
  $item = Get-Item -LiteralPath $target
  if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Cleanup root is reparse point' }
  $targets += $target
}
foreach ($target in $targets) { Remove-Item -LiteralPath $target -Recurse -Force }
@{ targets = $targets; all_absent = (@($targets | Where-Object { Test-Path -LiteralPath $_ }).Count -eq 0) } | ConvertTo-Json -Depth 4
