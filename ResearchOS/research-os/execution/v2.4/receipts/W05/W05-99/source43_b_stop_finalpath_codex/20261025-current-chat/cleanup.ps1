$ErrorActionPreference = 'Stop'
$expected = 'D:\作品集\ResearchOS\research-os\.local\source43-b-stop-finalpath-20261025-tmp'
$target = [System.IO.Path]::GetFullPath($expected).TrimEnd('\')
if ($target -cne $expected) { throw "target path changed: $target" }
$workspace = [System.IO.Path]::GetFullPath('D:\作品集\ResearchOS\research-os').TrimEnd('\')
if (-not $target.StartsWith($workspace + '\', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'target escaped workspace' }
$cursor = $target
while ($cursor) {
    $item = Get-Item -LiteralPath $cursor -Force -ErrorAction Stop
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { throw "reparse ancestry: $cursor" }
    $parent = [System.IO.Directory]::GetParent($cursor)
    if ($null -eq $parent) { break }
    $cursor = $parent.FullName
}
Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction Stop
Write-Output "removed task-owned disposable root: $target"
