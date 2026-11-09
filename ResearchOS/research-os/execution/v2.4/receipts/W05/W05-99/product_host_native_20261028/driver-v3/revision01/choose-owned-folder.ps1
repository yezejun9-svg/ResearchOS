param(
    [Parameter(Mandatory=$true)][int]$OwnedCorePid,
    [Parameter(Mandatory=$true)][string]$OwnedCoreImage,
    [Parameter(Mandatory=$true)][string]$OwnedCoreCreatedNS,
    [Parameter(Mandatory=$true)][string]$OwnedCoreSHA256,
    [Parameter(Mandatory=$true)][string]$OwnedWorkspace
)
$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class ResearchOSOwnedFolder {
  public delegate bool EnumCallback(IntPtr hwnd, IntPtr data);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumCallback cb, IntPtr data);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr hwnd, StringBuilder text, int max);
  [DllImport("user32.dll")] public static extern IntPtr GetDlgItem(IntPtr hwnd, int id);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hwnd);
  [DllImport("user32.dll")] public static extern bool IsWindowEnabled(IntPtr hwnd);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern IntPtr SendMessageTimeout(IntPtr hwnd, uint message, IntPtr wp, IntPtr lp, uint flags, uint timeout, out IntPtr result);
}
'@
$expectedImage = (Resolve-Path -LiteralPath $OwnedCoreImage).Path
$folder = (Resolve-Path -LiteralPath $OwnedWorkspace).Path
$process = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $OwnedCorePid)
if (!$process -or $process.ExecutablePath -ine $expectedImage) { throw 'OWNED_CORE_IDENTITY_MISMATCH' }
$nativeProcess = Get-Process -Id $OwnedCorePid
$createdNS = [long](($nativeProcess.StartTime.ToUniversalTime().Ticks - [long]621355968000000000) * [long]100)
if ($createdNS.ToString() -ne $OwnedCoreCreatedNS -or (Get-FileHash -LiteralPath $expectedImage -Algorithm SHA256).Hash.ToLowerInvariant() -ne $OwnedCoreSHA256) { throw 'OWNED_CORE_VERSION_MISMATCH' }
$creation = [string]$process.CreationDate
$limit = [DateTime]::UtcNow.AddSeconds(25)
$found = [System.Collections.Generic.List[IntPtr]]::new()
while ([DateTime]::UtcNow -lt $limit) {
  $found.Clear()
  $callback = [ResearchOSOwnedFolder+EnumCallback]{ param($hwnd, $data)
    [uint32]$windowPid = 0
    [void][ResearchOSOwnedFolder]::GetWindowThreadProcessId($hwnd, [ref]$windowPid)
    if ($windowPid -eq $OwnedCorePid -and [ResearchOSOwnedFolder]::IsWindowVisible($hwnd)) {
      $class = [System.Text.StringBuilder]::new(256)
      [void][ResearchOSOwnedFolder]::GetClassName($hwnd, $class, 256)
      if ($class.ToString() -eq '#32770') { $found.Add($hwnd) }
    }
    return $true
  }
  [void][ResearchOSOwnedFolder]::EnumWindows($callback, [IntPtr]::Zero)
  if ($found.Count -gt 0) { break }
  Start-Sleep -Milliseconds 100
}
if ($found.Count -ne 1) { throw 'EXACT_OWNED_FOLDER_DIALOG_NOT_FOUND' }
$process = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $OwnedCorePid)
if (!$process -or $process.ExecutablePath -ine $expectedImage -or [string]$process.CreationDate -ne $creation) { throw 'OWNED_CORE_CHANGED' }
$nativeProcess = Get-Process -Id $OwnedCorePid
$createdNS = [long](($nativeProcess.StartTime.ToUniversalTime().Ticks - [long]621355968000000000) * [long]100)
if ($createdNS.ToString() -ne $OwnedCoreCreatedNS) { throw 'OWNED_CORE_CREATION_CHANGED' }
$window = $found[0]
# CLI init supplied this exact path as a hint; Core's own in-process callback
# performs BFFM_SETSELECTIONW. Never pass a caller-local pointer across processes.
# The controller must verify the actual selected path in the init response.
$button = [ResearchOSOwnedFolder]::GetDlgItem($window, 1)
if ($button -eq [IntPtr]::Zero -or ![ResearchOSOwnedFolder]::IsWindowEnabled($button)) { throw 'OWNED_FOLDER_CONFIRM_UNAVAILABLE' }
$result = [IntPtr]::Zero
$sent = [ResearchOSOwnedFolder]::SendMessageTimeout($button, 0x00F5, [IntPtr]::Zero, [IntPtr]::Zero, 2, 5000, [ref]$result)
if ($sent -eq [IntPtr]::Zero) { throw 'FOLDER_CONFIRM_MESSAGE_UNCONFIRMED' }
@{ scope='ONLY_OWNED_CORE_FOLDER_DIALOG'; core_pid=$OwnedCorePid; core_image=$expectedImage; creation=$creation; selected_folder=$folder; hwnd=$window.ToInt64(); message_delivered=$true } | ConvertTo-Json -Compress
