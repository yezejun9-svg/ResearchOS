$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$StageRoot = 'C:/Users/yqyyds/Documents/Codex/2026-11-04/task/cp586-continuation/owned-model-resource'
$Utf8 = [System.Text.UTF8Encoding]::new($false)
$Journal = $null
$OwnerLock = $null
$Sequence = 0
$Copied = [System.Collections.Generic.List[object]]::new()

function Hash-File([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
}
function Write-NewJson([string]$Path, $Value) {
    $bytes = $Utf8.GetBytes(($Value | ConvertTo-Json -Depth 12) + [Environment]::NewLine)
    $stream = [System.IO.File]::Open($Path, 'CreateNew', 'Write', 'Read')
    try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
}
function Assert-PlainPath([string]$Path) {
    $cursor = [System.IO.Path]::GetFullPath($Path)
    while ($cursor) {
        if ([System.IO.File]::Exists($cursor) -or [System.IO.Directory]::Exists($cursor)) {
            if (([System.IO.File]::GetAttributes($cursor) -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Reparse path refused: $cursor"
            }
        }
        $parent = [System.IO.Path]::GetDirectoryName($cursor)
        if ($parent -eq $cursor) { break }
        $cursor = $parent
    }
}
function Destination([string]$Relative) {
    $root = [System.IO.Path]::GetFullPath($StageRoot).TrimEnd('\') + '\'
    $path = [System.IO.Path]::GetFullPath((Join-Path $StageRoot $Relative))
    if (-not $path.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Destination escaped scope' }
    Assert-PlainPath $path
    return $path
}
function Write-Event([string]$Event, $Data) {
    $script:Sequence++
    $row = [ordered]@{ sequence = $script:Sequence; utc = [DateTime]::UtcNow.ToString('o'); event = $Event; data = $Data }
    $bytes = $Utf8.GetBytes(($row | ConvertTo-Json -Depth 8 -Compress) + "`n")
    $Journal.Write($bytes, 0, $bytes.Length)
    $Journal.Flush($true)
}

try {
    Assert-PlainPath $StageRoot
    $ScopePath = Join-Path $StageRoot 'SCOPE.json'
    $Scope = Get-Content -LiteralPath $ScopePath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($Scope.owner -ne 'codex:/root/runtime_readiness' -or $Scope.success_status -ne 'ASSETS_STAGED_NOT_STARTED' -or
        [System.IO.Path]::GetFullPath($Scope.destination_root) -ne [System.IO.Path]::GetFullPath($StageRoot)) { throw 'Scope identity differs' }
    $OwnerLock = [System.IO.File]::Open((Destination 'owner.lock'), 'CreateNew', 'Write', 'Read')
    $Journal = [System.IO.File]::Open((Destination 'copy.jsonl'), 'CreateNew', 'Write', 'Read')
    $FreeBefore = (Get-PSDrive -Name C).Free
    if ($FreeBefore -lt $Scope.minimum_C_free_bytes -or ($FreeBefore - $Scope.expected_asset_bytes) -lt $Scope.minimum_C_free_bytes) {
        throw 'Conservative C free-space guard failed; no cleanup or copy allowed'
    }
    Write-Event 'SCOPE_LOADED' @{ scope_sha256 = (Hash-File $ScopePath); C_free = $FreeBefore; starts = 0; probes = 0; inference = 0 }
    $Assets = [System.Collections.Generic.List[object]]::new()
    foreach ($asset in $Scope.known_assets) {
        [void]$Assets.Add([pscustomobject]@{ source = $asset.source; destination_relative = $asset.dest; expected_bytes = [long]$asset.bytes; expected_sha256 = $asset.sha256 })
    }
    $LibRoot = [System.IO.Path]::GetFullPath($Scope.runtime_library_source).TrimEnd('\')
    Assert-PlainPath $LibRoot
    $LibEntries = @(Get-ChildItem -LiteralPath $LibRoot -Recurse -Force -ErrorAction Stop)
    if (@($LibEntries | Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 }).Count -ne 0) { throw 'Runtime source contains reparse points' }
    $LibFiles = @($LibEntries | Where-Object { -not $_.PSIsContainer } | Sort-Object -Property FullName)
    $LibBytes = [long]($LibFiles | Measure-Object -Property Length -Sum).Sum
    if ($LibFiles.Count -ne $Scope.runtime_expected_file_count -or $LibBytes -ne $Scope.runtime_expected_bytes) { throw 'Runtime source count/size changed; stop before copy' }
    foreach ($file in $LibFiles) {
        $relative = $file.FullName.Substring($LibRoot.Length + 1).Replace('\', '/')
        [void]$Assets.Add([pscustomobject]@{ source = $file.FullName; destination_relative = ($Scope.runtime_library_destination + '/' + $relative); expected_bytes = [long]$file.Length; expected_sha256 = $null })
    }
    if ($Assets.Count -ne $Scope.expected_asset_file_count -or [long]($Assets | Measure-Object -Property expected_bytes -Sum).Sum -ne $Scope.expected_asset_bytes) { throw 'Asset roster/count/size differs from scope' }
    $Seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    $SourceIndex = [System.Collections.Generic.List[object]]::new()
    foreach ($asset in $Assets) {
        Assert-PlainPath $asset.source
        $destination = Destination $asset.destination_relative
        if (-not $Seen.Add($destination) -or (Test-Path -LiteralPath $destination)) { throw 'Duplicate or existing destination; no overwrite permitted' }
        $file = Get-Item -LiteralPath $asset.source -Force
        if ($file.PSIsContainer -or $file.Length -ne $asset.expected_bytes) { throw 'Source size/type differs' }
        $digest = Hash-File $asset.source
        if ($asset.expected_sha256 -and $digest -ne $asset.expected_sha256) { throw 'Known asset SHA256 differs' }
        [void]$SourceIndex.Add([pscustomobject]@{ source = $file.FullName; destination_relative = $asset.destination_relative; bytes = [long]$file.Length; sha256 = $digest })
        Write-Event 'SOURCE_HASHED' @{ index = $SourceIndex.Count; source = $file.FullName; bytes = [long]$file.Length; sha256 = $digest }
        if ($SourceIndex.Count % 128 -eq 0) { Write-Output ("SOURCE_HASHED {0}/{1}" -f $SourceIndex.Count, $Assets.Count) }
    }
    $IndexPath = Destination 'source-index.json'
    Write-NewJson $IndexPath ([ordered]@{ schema = 'researchos.owned-model-source-index.v1'; scope_sha256 = (Hash-File $ScopePath); count = $SourceIndex.Count; bytes = $Scope.expected_asset_bytes; assets = $SourceIndex.ToArray() })
    Write-Event 'SOURCE_INDEX_SEALED' @{ path = $IndexPath; sha256 = (Hash-File $IndexPath); count = $SourceIndex.Count }
    Write-Output ("SOURCE_INDEX_SEALED {0} assets / {1} bytes" -f $SourceIndex.Count, $Scope.expected_asset_bytes)
    foreach ($asset in $SourceIndex) {
        if (((Get-PSDrive -Name C).Free - $asset.bytes) -lt $Scope.minimum_C_free_bytes) { throw 'Remaining C free-space guard failed; preserve state without cleanup' }
        $destination = Destination $asset.destination_relative
        [void][System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($destination))
        Assert-PlainPath $asset.source
        Assert-PlainPath $destination
        Write-Event 'COPY_STARTED' @{ index = $Copied.Count + 1; source = $asset.source; destination = $destination; bytes = $asset.bytes }
        $sourceStream = [System.IO.File]::Open($asset.source, 'Open', 'Read', 'Read')
        try {
            if ($sourceStream.Length -ne $asset.bytes -or (Get-FileHash -InputStream $sourceStream -Algorithm SHA256).Hash.ToLowerInvariant() -ne $asset.sha256) { throw 'Source changed since sealed index' }
            $sourceStream.Position = 0
            $targetStream = [System.IO.File]::Open($destination, 'CreateNew', 'Write', 'Read')
            try { $sourceStream.CopyTo($targetStream, 1048576); $targetStream.Flush($true) } finally { $targetStream.Dispose() }
        } finally { $sourceStream.Dispose() }
        $targetHash = Hash-File $destination
        if ((Get-Item -LiteralPath $destination).Length -ne $asset.bytes -or $targetHash -ne $asset.sha256) { throw 'Target readback SHA256/length mismatch; preserve failed file' }
        [void]$Copied.Add([pscustomobject]@{ source = $asset.source; destination = $destination; destination_relative = $asset.destination_relative; bytes = $asset.bytes; source_sha256 = $asset.sha256; destination_sha256 = $targetHash; verified = $true })
        Write-Event 'COPY_VERIFIED' $Copied[$Copied.Count - 1]
        if ($Copied.Count % 128 -eq 0 -or $asset.bytes -gt 100MB) { Write-Output ("COPY_VERIFIED {0}/{1}" -f $Copied.Count, $SourceIndex.Count) }
    }
    $EmptyDirectories = @()
    foreach ($relative in $Scope.private_empty_directories) {
        $directory = Destination $relative
        [void][System.IO.Directory]::CreateDirectory($directory)
        Assert-PlainPath $directory
        if ([System.IO.Directory]::EnumerateFileSystemEntries($directory).GetEnumerator().MoveNext()) { throw 'Private profile directory is not empty' }
        $EmptyDirectories += [pscustomobject]@{ path = $directory; empty = $true; configuration_loaded = $false; keys_created_or_copied = $false }
    }
    $Readme = @'
ASSETS_STAGED_NOT_STARTED

Only the public Ollama CLI executable, complete lib/ollama runtime tree, and the selected qwen3:4b-instruct manifest plus its five blobs are staged here.
profile/.ollama, profile/AppData/Local, profile/AppData/Roaming and tmp are intentionally empty. They are proposed child-process configuration directories, not a new Windows account or a qualified runtime. No old profile, keys, user configuration, credentials or ResearchOS data was copied.
No server, installer, model runner, metadata request, pull or inference was executed. No RESOURCE_READY or CP587 claim is made. A later separately scoped owner must inspect this manifest before starting anything.
Source and destination hashes are recorded in MANIFEST.json and source-index.json. copy.jsonl is append-only. Failures and partial files must be preserved, not silently retried or deleted.
'@
    $ReadmePath = Destination 'PROFILE-AND-STATUS.txt'
    $ReadmeBytes = $Utf8.GetBytes($Readme + [Environment]::NewLine)
    $stream = [System.IO.File]::Open($ReadmePath, 'CreateNew', 'Write', 'Read')
    try { $stream.Write($ReadmeBytes, 0, $ReadmeBytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
    Write-Event 'ALL_ASSETS_VERIFIED_NOT_STARTED' @{ count = $Copied.Count; bytes = $Scope.expected_asset_bytes; C_free = (Get-PSDrive -Name C).Free; private_directories = $EmptyDirectories }
    $Journal.Dispose(); $Journal = $null
    $Manifest = [ordered]@{ schema = 'researchos.owned-model-assets-manifest.v1'; status = 'ASSETS_STAGED_NOT_STARTED'; owner = $Scope.owner; completed_at = [DateTime]::UtcNow.ToString('o'); root = $StageRoot; baseline_checkpoint = 586; baseline_head_from_checkpoint = $Scope.baseline_head_from_checkpoint; ResearchOS_D_writes = 0; CP587_written = $false; scope_path = $ScopePath; scope_sha256 = (Hash-File $ScopePath); source_index_path = $IndexPath; source_index_sha256 = (Hash-File $IndexPath); copy_log_path = (Destination 'copy.jsonl'); copy_log_sha256 = (Hash-File (Destination 'copy.jsonl')); script_sha256 = (Hash-File $PSCommandPath); status_note_sha256 = (Hash-File $ReadmePath); source_file_count = $SourceIndex.Count; verified_asset_file_count = $Copied.Count; asset_bytes = $Scope.expected_asset_bytes; C_free_before = $FreeBefore; C_free_after = (Get-PSDrive -Name C).Free; private_empty_directories = $EmptyDirectories; process_starts = 0; process_stops = 0; metadata_requests = 0; inference_calls = 0; credentials_read = $false; original_asset_writes = 0; hardlinks_or_junctions_created = 0; formal_increment = 0; counter_reset = $false; independent_review_required = $true; assets = $Copied.ToArray() }
    $ManifestPath = Destination 'MANIFEST.json'
    Write-NewJson $ManifestPath $Manifest
    Write-Output ([pscustomobject]@{ status = $Manifest.status; manifest = $ManifestPath; manifest_sha256 = (Hash-File $ManifestPath); verified_assets = $Copied.Count; bytes = $Scope.expected_asset_bytes; C_free_after = $Manifest.C_free_after; starts = 0; inference = 0 } | ConvertTo-Json -Compress)
} catch {
    $failure = [ordered]@{ schema = 'researchos.owned-model-stage-failure.v1'; utc = [DateTime]::UtcNow.ToString('o'); status = 'ASSET_STAGE_FAILED_PRESERVED'; owner = 'codex:/root/runtime_readiness'; message = $_.Exception.Message; script_line = $_.InvocationInfo.ScriptLineNumber; copied_verified_count = $Copied.Count; original_asset_writes = 0; starts = 0; probes = 0; inference = 0; automatic_retry = $false; counter_reset = $false; formal_increment = 0 }
    if ($Journal) { try { Write-Event 'STAGE_FAILED_PRESERVED' $failure } catch {} }
    $FailurePath = Join-Path $StageRoot ('FAILED-' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ') + '.json')
    Write-NewJson $FailurePath $failure
    Write-Output ($failure | ConvertTo-Json -Compress)
    exit 1
} finally {
    if ($Journal) { $Journal.Dispose() }
    if ($OwnerLock) { $OwnerLock.Dispose() }
}
