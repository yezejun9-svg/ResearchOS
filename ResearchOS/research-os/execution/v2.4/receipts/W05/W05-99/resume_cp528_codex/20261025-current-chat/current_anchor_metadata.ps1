$ErrorActionPreference = 'Stop'
$packageRoot = 'C:\Users\yqyyds\.codex\researchos-resource-cache\normal-verifier-replacement-4f4023-20261015'
$anchors = @(
    @{ role = 'historical_core'; process_id = 54076; expected_core_sha256 = 'c4a3b498fc15120828427b237b8176710acfd7a9333cd24e9911fded9cd63e24' },
    @{ role = 'historical_desktop'; process_id = 69996; expected_core_sha256 = $null }
)
$observations = @()
foreach ($anchor in $anchors) {
    $rows = @(Get-CimInstance -ClassName Win32_Process -Filter ('ProcessId=' + $anchor.process_id) -ErrorAction Stop)
    if ($rows.Count -eq 0) {
        $observations += [pscustomobject]@{ role=$anchor.role; queried_pid=$anchor.process_id; status='ANCHOR_NOT_PRESENT'; current_process_binding=$false }
        continue
    }
    if ($rows.Count -ne 1) { throw 'Unexpected exact process query cardinality' }
    $row = $rows[0]
    $imagePath = [string]$row.ExecutablePath
    $withinPackage = $imagePath.StartsWith($packageRoot + '\', [StringComparison]::OrdinalIgnoreCase)
    $imageHash = $null
    $hashStatus = 'NOT_QUERIED_OUTSIDE_DECLARED_PUBLIC_PACKAGE'
    if ($withinPackage) {
        try { $imageHash = (Get-FileHash -LiteralPath $imagePath -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant(); $hashStatus='PUBLIC_IMAGE_HASH_READ' }
        catch { $hashStatus='PUBLIC_IMAGE_HASH_UNAVAILABLE_' + $_.Exception.GetType().Name }
    }
    $observations += [pscustomobject]@{
        role=$anchor.role; queried_pid=$anchor.process_id; status='PRESENT_REQUIRES_IDENTITY_BINDING'; current_process_binding=$false
        parent_pid=[uint32]$row.ParentProcessId; creation_utc=$row.CreationDate.ToUniversalTime().ToString('o')
        image_within_declared_package=$withinPackage; image_path=$(if($withinPackage){$imagePath}else{'REDACTED_OUTSIDE_DECLARED_PACKAGE'})
        public_image_sha256=$imageHash; hash_status=$hashStatus
        expected_core_hash_match=$(if($anchor.expected_core_sha256 -and $imageHash){$anchor.expected_core_sha256 -eq $imageHash}else{$null})
        historical_creation_continuity='NOT_ESTABLISHED_BY_PID_OR_IMAGE_HASH_ALONE'
    }
}
[pscustomobject]@{
    schema='researchos.current-exact-historical-anchor-metadata.v1'; observed_utc=[DateTime]::UtcNow.ToString('o')
    query_scope='Only exact historical PIDs54076 and69996; no all-process scan, parent extension, CommandLine or environment capture'
    declared_public_package=$packageRoot; package_directory_exists=(Test-Path -LiteralPath $packageRoot -PathType Container)
    anchors=$observations; original_database_read=$false; product_api_call=$false; mutation=$false; actual_backup_gate_accepted=$false
} | ConvertTo-Json -Depth 8
