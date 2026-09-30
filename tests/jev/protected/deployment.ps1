[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [ValidateSet('Plan', 'Install', 'Uninstall')][string]$Action = 'Plan',
    [Parameter(Mandatory = $true)][string]$Binary,
    [Parameter(Mandatory = $true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedSHA256,
    [string]$ReaderSID = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value,
    [string]$ProjectRoot = (Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent)
)
$ErrorActionPreference = 'Stop'
$serviceName = 'ResearchOSVerifierCanary'
$installRoot = Join-Path ([Environment]::GetFolderPath('CommonApplicationData')) $serviceName
$installedBinary = Join-Path $installRoot 'broker.exe'
$dataRoot = Join-Path $installRoot 'data'
$manifestPath = Join-Path $installRoot 'installation.json'
$sourceBinary = (Resolve-Path -LiteralPath $Binary).ProviderPath
$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).ProviderPath
$projectIdentity = Get-Content -LiteralPath (Join-Path $ProjectRoot 'execution/project_identity.json') -Raw | ConvertFrom-Json
if ($projectIdentity.project_id -ne 'aede0678-7308-43dc-b9f2-cfe3d90cfdfb') { throw 'PROJECT_IDENTITY_MISMATCH' }
$credentialPath = Join-Path $ProjectRoot '.local/secrets/typesafe.dpapi'
if ((Get-FileHash -LiteralPath $sourceBinary -Algorithm SHA256).Hash -ne $ExpectedSHA256) { throw 'BINARY_HASH_MISMATCH' }
if ($ReaderSID -notmatch '^S-1-5-21-[0-9]+-[0-9]+-[0-9]+-[0-9]+$') { throw 'LOCAL_USER_SID_REQUIRED' }
[void][Security.Principal.SecurityIdentifier]::new($ReaderSID)
$sc = Join-Path ([Environment]::SystemDirectory) 'sc.exe'
function Invoke-ServiceTool([string[]]$Arguments) {
    $reply = & $sc @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) { throw "SERVICE_OPERATION_FAILED: $($Arguments[0]): $reply" }
    return $reply
}
$sidText = (Invoke-ServiceTool @('showsid', $serviceName)) -join ' '
$serviceSID = [regex]::Match($sidText, 'S-1-5-80(?:-[0-9]+){5}').Value
if (-not $serviceSID) { throw 'SERVICE_SID_LOOKUP_FAILED' }
$binaryCommand = '"' + $installedBinary + '" --service --reader-sid ' + $ReaderSID
$plan = [ordered]@{
    schema = 'researchos.verifier-canary-install.v1'; action = $Action
    scope = 'CANARY_AND_FROZEN_EVALUATOR_PREPARATION'; formal_G04 = 'BLOCKED'; formal_A08 = 'BLOCKED'
    service = $serviceName; account = "NT SERVICE\$serviceName"; service_sid = $serviceSID
    reader_sid = $ReaderSID; install_root = $installRoot; binary_sha256 = $ExpectedSHA256.ToLowerInvariant()
    binary_command = $binaryCommand; start_mode = 'Manual'; elevation_required = ($Action -ne 'Plan')
    credential_ref = '.local/secrets/typesafe.dpapi'; credential_delivery = 'Current-user DPAPI to service-user DPAPI through admin-only pipe; plaintext only in process memory'
    calls_started_by_install = $false; frozen_request_budget = 30; maximum_mode = 'ADVISORY'
    changes = @('Create only this new service and fixed product directory', 'Administrator-owned immutable binary and install manifest', 'Service-owned private input/label/detail/log and one-run marker', 'Local public pipe exposes only fixed commands and terminal aggregate counts', 'One-time credential configuration does not generate holdout or start provider calls')
}
if ($Action -eq 'Plan') { $plan | ConvertTo-Json -Depth 5; return }
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if (-not ([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'ELEVATION_REQUIRED: request the user-approved final UAC step; this script does not elevate itself' }
if (-not $PSCmdlet.ShouldProcess($installRoot, "$Action $serviceName frozen evaluator service")) { return }

function Assert-PlainPath([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    while ($null -ne $item) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'REPARSE_PATH_REFUSED' }
        $item = $item.Parent
    }
}
function Set-ExactACL([string]$Path, [string]$SDDL) {
    $acl = if ((Get-Item -LiteralPath $Path -Force).PSIsContainer) { [Security.AccessControl.DirectorySecurity]::new() } else { [Security.AccessControl.FileSecurity]::new() }
    $acl.SetSecurityDescriptorSddlForm($SDDL)
    Set-Acl -LiteralPath $Path -AclObject $acl
    if (-not (Get-Acl -LiteralPath $Path).AreAccessRulesProtected) { throw 'ACL_NOT_PROTECTED' }
}
if ($Action -eq 'Install') {
    if ($identity.User.Value -ne $ReaderSID) { throw 'ELEVATE_THE_SAME_DPAPI_USER_REQUIRED' }
    if ((Get-Service -Name $serviceName -ErrorAction SilentlyContinue) -or (Test-Path -LiteralPath $installRoot)) { throw 'EXISTING_SERVICE_OR_DIRECTORY_REFUSED' }
    Assert-PlainPath ([IO.Path]::GetDirectoryName($installRoot))
    Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
public static class ResearchOSInstallDirectory {
  [StructLayout(LayoutKind.Sequential)] struct SA { public int length; public IntPtr descriptor; public int inherit; }
  [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool ConvertStringSecurityDescriptorToSecurityDescriptorW(string sddl, uint revision, out IntPtr descriptor, out uint size);
  [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool CreateDirectoryW(string path, ref SA security);
  [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr address);
  public static void Create(string path, string sddl) {
    IntPtr sd; uint size;
    if (!ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl,1,out sd,out size)) throw new Win32Exception(Marshal.GetLastWin32Error());
    try { var sa=new SA{length=Marshal.SizeOf(typeof(SA)),descriptor=sd,inherit=0}; if(!CreateDirectoryW(path,ref sa)) throw new Win32Exception(Marshal.GetLastWin32Error()); }
    finally { LocalFree(sd); }
  }
}
'@
    # Owner and protected DACL are present at creation, before a same-user
    # process could replace the install directory or change its inherited ACL.
    [ResearchOSInstallDirectory]::Create($installRoot, "O:BAG:BAD:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;GRGX;;;$serviceSID)(A;OICI;GRGX;;;$ReaderSID)")
    Assert-PlainPath $installRoot
    Copy-Item -LiteralPath $sourceBinary -Destination $installedBinary
    Set-ExactACL $installedBinary "O:BAG:BAD:P(A;;FA;;;SY)(A;;FA;;;BA)(A;;GRGX;;;$serviceSID)(A;;GRGX;;;$ReaderSID)"
    if ((Get-FileHash -LiteralPath $installedBinary -Algorithm SHA256).Hash -ne $ExpectedSHA256) { throw 'INSTALLED_BINARY_HASH_MISMATCH' }
    [ResearchOSInstallDirectory]::Create($dataRoot, "O:BAG:BAD:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;FA;;;$serviceSID)")
    $plan | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding utf8
    Set-ExactACL $manifestPath "O:BAG:BAD:P(A;;FA;;;SY)(A;;FA;;;BA)(A;;GR;;;$serviceSID)(A;;GR;;;$ReaderSID)"
    [void](Invoke-ServiceTool @('create', $serviceName, 'binPath=', $binaryCommand, 'type=', 'own', 'start=', 'demand', 'obj=', "NT SERVICE\$serviceName", 'DisplayName=', 'ResearchOS Verifier (frozen evaluator)'))
    # Current developer can query config/status, never start/stop/change the service.
    [void](Invoke-ServiceTool @('sdset', $serviceName, "D:P(A;;0xF01FF;;;SY)(A;;0xF01FF;;;BA)(A;;CCLC;;;$ReaderSID)"))
    [void](Invoke-ServiceTool @('privs', $serviceName, 'SeChangeNotifyPrivilege'))
    [void](Invoke-ServiceTool @('start', $serviceName))
    (Get-Service -Name $serviceName).WaitForStatus('Running', [TimeSpan]::FromSeconds(15))
    # This is the only credential read. It occurs after explicit elevated Install,
    # in the same DPAPI user, and feeds only the immutable installed helper stdin.
    $secured = $null; $bstr = [IntPtr]::Zero; $credentialBytes = $null; $helper = $null
    try {
        $secured = Get-Content -LiteralPath $credentialPath -Raw | ConvertTo-SecureString
        $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secured)
        $credentialBytes = [Text.Encoding]::UTF8.GetBytes([Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr))
        if ($credentialBytes.Length -eq 0 -or $credentialBytes.Length -gt 4096) { throw 'CREDENTIAL_LENGTH_INVALID' }
        $startInfo = [Diagnostics.ProcessStartInfo]::new()
        $startInfo.FileName = $installedBinary; $startInfo.Arguments = '--configure-from-stdin'
        $startInfo.UseShellExecute = $false; $startInfo.CreateNoWindow = $true
        $startInfo.RedirectStandardInput = $true; $startInfo.RedirectStandardOutput = $true; $startInfo.RedirectStandardError = $true
        $helper = [Diagnostics.Process]::Start($startInfo)
        $helper.StandardInput.BaseStream.Write($credentialBytes, 0, $credentialBytes.Length)
        $helper.StandardInput.Close()
        if (-not $helper.WaitForExit(10000)) { $helper.Kill(); throw 'CREDENTIAL_HANDOFF_TIMEOUT' }
        $configured = $helper.StandardOutput.ReadToEnd() | ConvertFrom-Json
        if ($helper.ExitCode -ne 0 -or $configured.configured -ne $true -or $configured.started -ne $false) { throw 'CREDENTIAL_HANDOFF_FAILED' }
    } finally {
        if ($credentialBytes) { [Array]::Clear($credentialBytes,0,$credentialBytes.Length) }
        if ($bstr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
        if ($secured) { $secured.Dispose() }
        if ($helper) { $helper.Dispose() }
    }
    $plan | ConvertTo-Json -Depth 5
    return
}

# Uninstall never touches another service or arbitrary supplied directory. It
# first asks this exact virtual-account service to erase only its four canaries.
if (-not (Test-Path -LiteralPath $manifestPath)) { throw 'OWN_INSTALL_MANIFEST_REQUIRED' }
Assert-PlainPath $installRoot
$saved = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($saved.schema -ne 'researchos.verifier-canary-install.v1' -or $saved.service -ne $serviceName -or $saved.install_root -ne $installRoot -or $saved.binary_sha256 -ne $ExpectedSHA256.ToLowerInvariant() -or $saved.reader_sid -ne $ReaderSID) { throw 'INSTALL_IDENTITY_MISMATCH' }
$service = Get-CimInstance Win32_Service -Filter "Name='$serviceName'"
if ($null -eq $service -or $service.StartName -ne "NT SERVICE\$serviceName" -or $service.PathName -ne $binaryCommand) { throw 'SERVICE_CONFIGURATION_DRIFT' }
if ((Get-FileHash -LiteralPath $installedBinary -Algorithm SHA256).Hash -ne $ExpectedSHA256) { throw 'INSTALLED_BINARY_HASH_MISMATCH' }
if ((Get-Service -Name $serviceName).Status -ne 'Running') { [void](Invoke-ServiceTool @('start', $serviceName)); (Get-Service -Name $serviceName).WaitForStatus('Running', [TimeSpan]::FromSeconds(15)) }
[void](Invoke-ServiceTool @('control', $serviceName, '128'))
(Get-Service -Name $serviceName).WaitForStatus('Stopped', [TimeSpan]::FromSeconds(15))
if (Test-Path -LiteralPath (Join-Path $dataRoot 'private')) { throw 'CANARY_ERASE_FAILED_DATA_PRESERVED' }
if ((Get-ChildItem -LiteralPath $dataRoot -Force | Measure-Object).Count -ne 0) { throw 'UNEXPECTED_DATA_PRESERVED' }
$children = @(Get-ChildItem -LiteralPath $installRoot -Force)
if (($children.Name | Sort-Object) -join ',' -ne 'broker.exe,data,installation.json') { throw 'UNEXPECTED_INSTALL_FILES_PRESERVED' }
[void](Invoke-ServiceTool @('delete', $serviceName))
# Only known files and empty fixed directories; no recursive deletion.
Remove-Item -LiteralPath $installedBinary
Remove-Item -LiteralPath $manifestPath
Remove-Item -LiteralPath $dataRoot
Remove-Item -LiteralPath $installRoot
$plan | ConvertTo-Json -Depth 5
