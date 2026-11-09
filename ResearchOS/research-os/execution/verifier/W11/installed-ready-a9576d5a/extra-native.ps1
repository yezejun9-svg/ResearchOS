$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
public static class InstalledPipeBoundary {
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern SafeFileHandle CreateFileW(string name,uint rights,uint share,IntPtr sa,uint disposition,uint flags,IntPtr template);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern SafeFileHandle CreateNamedPipeW(string name,uint mode,uint pipeMode,uint instances,uint output,uint input,uint timeout,IntPtr sa);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetNamedPipeServerProcessId(SafeFileHandle handle,out uint processId);
 public static uint[] Client(string name) {
  using(var h=CreateFileW(name,0x100003,0,IntPtr.Zero,3,0x40110000,IntPtr.Zero)) {
   if(h.IsInvalid)return new uint[]{(uint)Marshal.GetLastWin32Error(),0};
   uint pid; if(!GetNamedPipeServerProcessId(h,out pid))return new uint[]{(uint)Marshal.GetLastWin32Error(),0};
   return new uint[]{0,pid};
  }
 }
 public static int SecondInstance(string name) {
  using(var h=CreateNamedPipeW(name,3,15,1,4096,64,0,IntPtr.Zero)) {return h.IsInvalid?Marshal.GetLastWin32Error():0;}
 }
}
'@
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$elevated = ([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($elevated) { throw 'UNELEVATED_REQUIRED' }
$manifest = Get-Content -LiteralPath 'C:\ProgramData\ResearchOSVerifierCanary\installation.json' -Raw | ConvertFrom-Json
$service = Get-CimInstance Win32_Service -Filter "Name='ResearchOSVerifierCanary'"
$public = [InstalledPipeBoundary]::Client('\\.\pipe\ResearchOSVerifierCanary-v1')
$config = [InstalledPipeBoundary]::Client('\\.\pipe\ResearchOSVerifierCanary-config-v1')
$second = [InstalledPipeBoundary]::SecondInstance('\\.\pipe\ResearchOSVerifierCanary-v1')
$result = [ordered]@{
 captured_at=[DateTime]::UtcNow.ToString('o');developer_sid=$identity.User.Value;developer_elevated=$elevated
 service_pid=$service.ProcessId;service_state=$service.State;service_sid=$manifest.service_sid
 different_os_identity=($identity.User.Value -ne $manifest.service_sid)
 binary_sha256=(Get-FileHash -LiteralPath 'C:\ProgramData\ResearchOSVerifierCanary\broker.exe' -Algorithm SHA256).Hash.ToLowerInvariant()
 manifest_sha256=$manifest.binary_sha256
 public_client_error=$public[0];public_pipe_server_pid=$public[1];public_pid_matches_service=($public[1] -eq $service.ProcessId)
 ordinary_config_client_error=$config[0];public_second_instance_error=$second
 private_formal_data_accessed=$false;credential_accessed=$false;formal_started=$false;real_provider_called=$false
}
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'extra-native.json') -Encoding utf8
$result | ConvertTo-Json -Depth 5
if ($elevated -or -not $result.different_os_identity -or $result.binary_sha256 -ne 'b7af809432a96a175375028088303f0a63abe42f3b273a8cc95faf3c5985c015' -or $public[0] -ne 0 -or -not $result.public_pid_matches_service -or $config[0] -ne 5 -or $second -ne 5) { throw 'INSTALLED_BOUNDARY_FAILED' }
