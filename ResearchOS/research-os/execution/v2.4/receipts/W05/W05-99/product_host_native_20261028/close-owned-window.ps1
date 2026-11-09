param(
    [Parameter(Mandatory=$true)][int]$OwnedDesktopPid,
    [Parameter(Mandatory=$true)][string]$OwnedDesktopImage,
    [Parameter(Mandatory=$true)][string]$OwnedDesktopCreatedNS,
    [Parameter(Mandatory=$true)][string]$OwnedDesktopSHA256
)
$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class ResearchOSOwnedWindow {
  public delegate bool EnumCallback(IntPtr hwnd, IntPtr data);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumCallback cb, IntPtr data);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr hwnd, StringBuilder text, int max);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr hwnd, StringBuilder text, int max);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hwnd);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern IntPtr SendMessageTimeout(IntPtr hwnd, uint message, IntPtr wp, IntPtr lp, uint flags, uint timeout, out IntPtr result);
}
'@
$expectedImage = (Resolve-Path -LiteralPath $OwnedDesktopImage).Path
function Assert-OwnedDesktop {
  $process = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $OwnedDesktopPid)
  if (!$process -or $process.ExecutablePath -ine $expectedImage) { throw 'OWNED_DESKTOP_IMAGE_MISMATCH' }
  $nativeProcess = Get-Process -Id $OwnedDesktopPid
  $createdNS = [long](($nativeProcess.StartTime.ToUniversalTime().Ticks - [long]621355968000000000) * [long]100)
  if ($createdNS.ToString() -ne $OwnedDesktopCreatedNS) { throw 'OWNED_DESKTOP_CREATION_MISMATCH' }
}
Assert-OwnedDesktop
if ((Get-FileHash -LiteralPath $expectedImage -Algorithm SHA256).Hash.ToLowerInvariant() -ne $OwnedDesktopSHA256) { throw 'OWNED_DESKTOP_HASH_MISMATCH' }
$limit = [DateTime]::UtcNow.AddSeconds(25)
$found = [System.Collections.Generic.List[IntPtr]]::new()
while ([DateTime]::UtcNow -lt $limit) {
  $found.Clear()
  $callback = [ResearchOSOwnedWindow+EnumCallback]{ param($hwnd, $data)
    [uint32]$windowPid = 0
    [void][ResearchOSOwnedWindow]::GetWindowThreadProcessId($hwnd, [ref]$windowPid)
    if ($windowPid -eq $OwnedDesktopPid -and [ResearchOSOwnedWindow]::IsWindowVisible($hwnd)) {
      $class = [System.Text.StringBuilder]::new(256)
      $title = [System.Text.StringBuilder]::new(256)
      [void][ResearchOSOwnedWindow]::GetClassName($hwnd, $class, 256)
      [void][ResearchOSOwnedWindow]::GetWindowText($hwnd, $title, 256)
      if ($class.ToString() -eq 'Chrome_WidgetWin_1' -and $title.ToString() -like '*ResearchOS*') { $found.Add($hwnd) }
    }
    return $true
  }
  [void][ResearchOSOwnedWindow]::EnumWindows($callback, [IntPtr]::Zero)
  if ($found.Count -gt 0) { break }
  Start-Sleep -Milliseconds 100
}
if ($found.Count -ne 1) { throw 'EXACT_OWNED_PRODUCT_WINDOW_NOT_FOUND' }
Assert-OwnedDesktop
$result = [IntPtr]::Zero
$sent = [ResearchOSOwnedWindow]::SendMessageTimeout($found[0], 0x0010, [IntPtr]::Zero, [IntPtr]::Zero, 2, 5000, [ref]$result)
if ($sent -eq [IntPtr]::Zero) { throw 'OWNED_CLOSE_MESSAGE_UNCONFIRMED' }
@{ scope='ONLY_OWNED_PRODUCT_WINDOW_CLOSE'; desktop_pid=$OwnedDesktopPid; image=$expectedImage; created_ns=$OwnedDesktopCreatedNS; hwnd=$found[0].ToInt64(); message_delivered=$true; process_exit_claimed=$false } | ConvertTo-Json -Compress
