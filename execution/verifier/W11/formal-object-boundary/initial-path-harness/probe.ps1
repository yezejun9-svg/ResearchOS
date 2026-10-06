$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$elevated = ([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($elevated) { throw 'UNELEVATED_DEVELOPER_REQUIRED' }
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
public static class FormalObjectHandleProbe {
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)]
 static extern SafeFileHandle CreateFileW(string name,uint access,uint share,IntPtr security,uint disposition,uint flags,IntPtr template);
 public static int OpenOnly(string path,uint access) {
  using(var h=CreateFileW(path,access,7,IntPtr.Zero,3,0x00200000,IntPtr.Zero)) {
   return h.IsInvalid?Marshal.GetLastWin32Error():0;
  }
 }
}
'@
$root = 'C:ProgramDataResearchOSVerifierCanarydataprivate'
$rows = [Collections.Generic.List[object]]::new()
foreach ($name in @('frozen-run.batch.json','frozen-call-00.envelope.json','frozen-call-00.result.json','frozen-run.terminal.json')) {
 foreach ($mode in @('READ','WRITE')) {
  $rights = if ($mode -eq 'READ') { [uint32]2147483648 } else { [uint32]1073741824 }
  $path = Join-Path $root $name
  $errorCode = [FormalObjectHandleProbe]::OpenOnly($path,$rights)
  $rows.Add([ordered]@{assertion_id="FORMAL-OBJECT-$mode-$name";path=$path;operation='CreateFileW OPEN_EXISTING then immediate CloseHandle';rights=$rights;expected_error=5;actual_error=$errorCode;status=$(if($errorCode -eq 5){'PASS'}else{'FAIL'});bytes_read=0;bytes_written=0})
 }
}
$result = [ordered]@{
 schema='researchos.formal-object-handle-boundary.v1';checked_at=[DateTime]::UtcNow.ToString('o')
 developer_sid=$identity.User.Value;developer_elevated=$elevated;assertions=$rows;assertion_count=$rows.Count
 directory_enumerated=$false;credential_accessed=$false;formal_body_read=$false;service_mutated=$false;provider_called=$false
 existence_evidence='Completed fixed protected service summary plus reviewed creation code; file bodies and private directory were not inspected.'
 status=$(if($rows.Count -eq 8 -and @($rows | Where-Object status -ne 'PASS').Count -eq 0){'PASS'}else{'FAIL'})
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'native-results.json') -Encoding utf8
$result | ConvertTo-Json -Depth 8
if ($result.status -ne 'PASS') { exit 1 }
