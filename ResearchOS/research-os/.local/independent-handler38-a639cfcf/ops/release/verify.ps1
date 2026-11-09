param([Parameter(Mandatory = $true)][string]$ReleaseRoot)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($ReleaseRoot).TrimEnd('\', '/')
$manifestPath = Join-Path $root 'release-manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw 'release manifest missing' }
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.format -ne 'RESEARCHOS_WINDOWS_X64_R1_FIXTURE_BUNDLE_V1') { throw 'release format unsupported' }
function FileSha256([string]$Path) {
    $stream = [IO.File]::OpenRead($Path)
    $hasher = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($hasher.ComputeHash($stream))).Replace('-', '').ToLowerInvariant() }
    finally { $hasher.Dispose(); $stream.Dispose() }
}
$expected = @{}
foreach ($item in $manifest.files) {
    $relative = [string]$item.path
    if ($relative -notmatch '^[A-Za-z0-9_./-]+$' -or $relative.StartsWith('/') -or $relative.Contains('..') -or $expected.ContainsKey($relative)) {
        throw "unsafe or duplicate manifest path: $relative"
    }
    $file = [IO.Path]::GetFullPath((Join-Path $root ($relative.Replace('/', '\'))))
    if (-not $file.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw "path escaped release: $relative" }
    $cursor = $root
    foreach ($part in $relative.Split('/') | Select-Object -SkipLast 1) {
        $cursor = Join-Path $cursor $part
        $folder = Get-Item -LiteralPath $cursor
        if (($folder.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "release reparse directory: $relative" }
    }
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "release file missing: $relative" }
    $info = Get-Item -LiteralPath $file
    if (($info.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "release reparse point: $relative" }
    if ($info.Length -ne [int64]$item.size) { throw "release size changed: $relative" }
    if ((FileSha256 $file) -ne $item.sha256) { throw "release hash changed: $relative" }
    $expected[$relative] = $true
}
$actual = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force | ForEach-Object { $_.FullName.Substring($root.Length + 1).Replace('\', '/') })
foreach ($relative in $actual) {
    if ($relative -ne 'release-manifest.json' -and -not $expected.ContainsKey($relative)) { throw "unexpected release file: $relative" }
}
if ($actual.Count -ne $expected.Count + 1) { throw 'release inventory changed' }
@{ status = 'PASS'; checked_files = $expected.Count; build_id = $manifest.build_id } | ConvertTo-Json -Compress
