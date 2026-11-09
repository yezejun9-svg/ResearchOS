[CmdletBinding()]
param([Parameter(Mandatory = $true)][string]$ReceiptDirectory)
$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if (([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'RUN_AS_UNELEVATED_DEVELOPER_REQUIRED' }
$root = Join-Path ([Environment]::GetFolderPath('CommonApplicationData')) 'ResearchOSVerifierCanary'
$manifest = Get-Content -LiteralPath (Join-Path $root 'installation.json') -Raw | ConvertFrom-Json
if ($manifest.schema -ne 'researchos.verifier-canary-install.v1' -or $manifest.reader_sid -ne $identity.User.Value -or $manifest.install_root -ne $root) { throw 'INSTALLED_IDENTITY_MISMATCH' }
$binary = Join-Path $root 'broker.exe'
if ((Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash.ToLowerInvariant() -ne $manifest.binary_sha256) { throw 'BINARY_HASH_MISMATCH' }
if (Test-Path -LiteralPath $ReceiptDirectory) { throw 'NEW_RECEIPT_DIRECTORY_REQUIRED' }
$receiptRoot = [IO.Path]::GetFullPath($ReceiptDirectory)
[void](New-Item -ItemType Directory -Path $receiptRoot)

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
public static class ResearchOSCanaryProbe {
  [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
  public static extern SafeFileHandle CreateFileW(string path, uint access, uint share, IntPtr security, uint creation, uint flags, IntPtr template);
  public static int Access(string path, uint rights) {
    using (var h=CreateFileW(path, rights, 7, IntPtr.Zero, 3, 0x00200000, IntPtr.Zero)) {
      return h.IsInvalid ? Marshal.GetLastWin32Error() : 0;
    }
  }
}
'@
$rows = [Collections.Generic.List[object]]::new()
function Assert-Canary([string]$ID, $Expected, $Actual) {
    $match = ($Expected | ConvertTo-Json -Compress -Depth 8) -ceq ($Actual | ConvertTo-Json -Compress -Depth 8)
    $rows.Add([ordered]@{ assertion_id=$ID; expected=$Expected; actual=$Actual; status=$(if($match){'PASS'}else{'FAIL'}); scope='INSTALLED_SYNTHETIC_CANARY' })
}
$service = Get-CimInstance Win32_Service -Filter "Name='ResearchOSVerifierCanary'"
Assert-Canary 'SERVICE-VIRTUAL-ACCOUNT' 'NT SERVICE\ResearchOSVerifierCanary' $service.StartName
Assert-Canary 'SERVICE-RUNNING' 'Running' $service.State
$response = & $binary --probe 2>&1
$probeExit = $LASTEXITCODE
Assert-Canary 'BROKER-PROBE-EXIT' 0 $probeExit
try {
    $summary = ($response -join "`n") | ConvertFrom-Json
    $fields = @($summary.PSObject.Properties.Name | Sort-Object)
    $expectedFields = @('schema','status','total','correct','false_accept','false_reject','abstain','critical_false_accept','maximum_mode' | Sort-Object)
    Assert-Canary 'BROKER-ONLY-FIXED-FIELDS' $expectedFields $fields
    Assert-Canary 'BROKER-PRIVATE-ROUNDTRIPS' @('researchos.protected-summary.v1','EXECUTION_REPORTED',4,4,'ADVISORY') @($summary.schema,$summary.status,$summary.total,$summary.correct,$summary.maximum_mode)
} catch { Assert-Canary 'BROKER-ONLY-FIXED-FIELDS' 'valid fixed summary' 'invalid response' }
foreach ($name in @('input.canary','label.canary','detail.canary','log.canary')) {
    $private = Join-Path $root "data\private\$name"
    # ACCESS_DENIED (5), never FILE_NOT_FOUND (2), is required. Successful opens
    # do not read, truncate, or modify bytes, even when the boundary is wrong.
    Assert-Canary "PRIVATE-READ-$name" 5 ([ResearchOSCanaryProbe]::Access($private, 0x80000000))
    Assert-Canary "PRIVATE-WRITE-$name" 5 ([ResearchOSCanaryProbe]::Access($private, 0x40000000))
}
Assert-Canary 'BINARY-WRITE-DENIED' 5 ([ResearchOSCanaryProbe]::Access($binary, 0x40000000))
Assert-Canary 'BINARY-DACL-WRITE-DENIED' 5 ([ResearchOSCanaryProbe]::Access($binary, 0x00040000))
$binaryOwner = (Get-Acl -LiteralPath $binary).GetOwner([Security.Principal.SecurityIdentifier]).Value
Assert-Canary 'BINARY-ADMINISTRATOR-OWNER' 'S-1-5-32-544' $binaryOwner
$passed = $rows.Count -eq 16 -and @($rows | Where-Object status -ne 'PASS').Count -eq 0
$report = [ordered]@{
    schema='researchos.installed-canary-evidence.v1'; status=$(if($passed){'PASS'}else{'FAIL'})
    executor_status='EXECUTION_REPORTED'; independent_acceptance='PENDING'; scope='INSTALLED_SYNTHETIC_CANARY'
    formal_G04='BLOCKED'; formal_A08='BLOCKED'; formal_holdout_accessed=$false; real_provider_called=$false
    developer_sid=$identity.User.Value; developer_elevated=$false; service_pid=$service.ProcessId
    service_sid=$manifest.service_sid; binary_sha256=$manifest.binary_sha256
    started_by='explicit user-authorized installation'; ended_at=[DateTime]::UtcNow.ToString('o')
    assertions=$rows; assertion_count=$rows.Count
}
$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $receiptRoot 'report.json') -Encoding utf8
$report | Select-Object status,assertion_count,formal_G04,formal_A08 | ConvertTo-Json
if (-not $passed) { exit 1 }
