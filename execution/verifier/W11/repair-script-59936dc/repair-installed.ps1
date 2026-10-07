[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Binary,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedSHA256,
    [Parameter(Mandatory=$true)][string]$ProjectRoot
)
$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if (-not ([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'ELEVATION_REQUIRED' }
$oldHash = '6d1882b978440c3fa50cfa7e85677954cb5c699651bf410b1c4f9849a36a6f56'
$name = 'ResearchOSVerifierCanary'
$root = Join-Path ([Environment]::GetFolderPath('CommonApplicationData')) $name
$installed = Join-Path $root 'broker.exe'
$manifestPath = Join-Path $root 'installation.json'
$backup = Join-Path $root 'broker.previous-6d1882.exe'
$backupManifest = Join-Path $root 'installation.previous-6d1882.json'
$Binary = (Resolve-Path -LiteralPath $Binary).ProviderPath
$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).ProviderPath
if ((Get-Content -LiteralPath (Join-Path $ProjectRoot 'execution/project_identity.json') -Raw | ConvertFrom-Json).project_id -ne 'aede0678-7308-43dc-b9f2-cfe3d90cfdfb') { throw 'PROJECT_IDENTITY_MISMATCH' }
$item = Get-Item -LiteralPath $root -Force
while ($null -ne $item) { if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'REPARSE_PATH_REFUSED' }; $item = $item.Parent }
$saved = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$command = '"' + $installed + '" --service --reader-sid ' + $identity.User.Value
$service = Get-CimInstance Win32_Service -Filter "Name='$name'"
if ($saved.schema -ne 'researchos.verifier-canary-install.v1' -or $saved.service -ne $name -or $saved.install_root -ne $root -or $saved.reader_sid -ne $identity.User.Value -or $saved.binary_sha256 -ne $oldHash -or $service.StartName -ne "NT SERVICE\$name" -or $service.PathName -ne $command) { throw 'INSTALL_IDENTITY_MISMATCH' }
if ((Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash -ne $oldHash -or (Get-FileHash -LiteralPath $Binary -Algorithm SHA256).Hash -ne $ExpectedSHA256) { throw 'BINARY_HASH_MISMATCH' }
$priorBackup = Test-Path -LiteralPath $backup
$priorManifest = Test-Path -LiteralPath $backupManifest
if ($priorBackup -or $priorManifest) {
    if (-not $priorBackup -or -not $priorManifest -or (Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash -ne $oldHash -or (Get-FileHash -LiteralPath $backupManifest -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash) { throw 'PRIOR_REPAIR_DIFFERS_PRESERVED' }
}
$binaryACL = Get-Acl -LiteralPath $installed
if (-not $binaryACL.AreAccessRulesProtected -or $binaryACL.GetOwner([Security.Principal.SecurityIdentifier]).Value -ne 'S-1-5-32-544') { throw 'INSTALLED_BINARY_BOUNDARY_CHANGED' }
# This one-time repair preserves all private data and the exact previous binary.
# It does not read labels, reset a run marker, start evaluation, or change any ACL.
if (-not $priorBackup) {
    Copy-Item -LiteralPath $installed -Destination $backup
    Set-Acl -LiteralPath $backup -AclObject $binaryACL
    Copy-Item -LiteralPath $manifestPath -Destination $backupManifest
    Set-Acl -LiteralPath $backupManifest -AclObject (Get-Acl -LiteralPath $manifestPath)
}
$serviceProcess = if ($service.ProcessId -ne 0) { Get-Process -Id $service.ProcessId } else { $null }
Stop-Service -Name $name
(Get-Service -Name $name).WaitForStatus('Stopped', [TimeSpan]::FromSeconds(15))
if ($serviceProcess -and -not $serviceProcess.WaitForExit(15000)) { throw 'SERVICE_PROCESS_EXIT_TIMEOUT_DATA_PRESERVED' }
try {
    Copy-Item -LiteralPath $Binary -Destination $installed -Force
    Set-Acl -LiteralPath $installed -AclObject $binaryACL
    if ((Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash -ne $ExpectedSHA256) { throw 'REPAIRED_BINARY_HASH_MISMATCH' }
    $saved.binary_sha256 = $ExpectedSHA256.ToLowerInvariant()
    $saved | Add-Member -NotePropertyName previous_binary_sha256 -NotePropertyValue $oldHash
    $saved | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding utf8
    Start-Service -Name $name
    (Get-Service -Name $name).WaitForStatus('Running', [TimeSpan]::FromSeconds(15))
} catch {
    if ((Get-Service -Name $name).Status -eq 'Stopped' -and (Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash -eq $oldHash) {
        Copy-Item -LiteralPath $backup -Destination $installed -Force
        Set-Acl -LiteralPath $installed -AclObject $binaryACL
        Copy-Item -LiteralPath $backupManifest -Destination $manifestPath -Force
        Start-Service -Name $name
    }
    throw
}
$state = & $installed --status | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'REPAIRED_STATUS_UNAVAILABLE' }
if ($state.frozen_run.run_state -eq 'NOT_CONFIGURED') {
    $secured=$null; $bstr=[IntPtr]::Zero; $bytes=$null; $helper=$null
    try {
        $secured = Get-Content -LiteralPath (Join-Path $ProjectRoot '.local/secrets/typesafe.dpapi') -Raw | ConvertTo-SecureString
        $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secured)
        $bytes = [Text.Encoding]::UTF8.GetBytes([Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr))
        if ($bytes.Length -eq 0 -or $bytes.Length -gt 4096) { throw 'CREDENTIAL_LENGTH_INVALID' }
        $info=[Diagnostics.ProcessStartInfo]::new()
        $info.FileName=$installed; $info.Arguments='--configure-from-stdin'; $info.UseShellExecute=$false; $info.CreateNoWindow=$true
        $info.RedirectStandardInput=$true; $info.RedirectStandardOutput=$true; $info.RedirectStandardError=$true
        $helper=[Diagnostics.Process]::Start($info)
        $helper.StandardInput.BaseStream.Write($bytes,0,$bytes.Length); $helper.StandardInput.Close()
        if (-not $helper.WaitForExit(10000)) { $helper.Kill(); throw 'CREDENTIAL_HANDOFF_TIMEOUT' }
        $configured=$helper.StandardOutput.ReadToEnd() | ConvertFrom-Json
        if ($helper.ExitCode -ne 0 -or $configured.configured -ne $true -or $configured.started -ne $false) { throw 'CREDENTIAL_HANDOFF_FAILED' }
    } finally {
        if ($bytes) { [Array]::Clear($bytes,0,$bytes.Length) }
        if ($bstr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
        if ($secured) { $secured.Dispose() }
        if ($helper) { $helper.Dispose() }
    }
    $state = & $installed --status | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0) { throw 'CONFIGURED_STATUS_UNAVAILABLE' }
}
if ($state.frozen_run.run_state -ne 'READY') { throw 'REPAIRED_SERVICE_NOT_READY' }
$state | ConvertTo-Json -Depth 10
