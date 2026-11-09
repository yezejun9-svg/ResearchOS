param(
  [Parameter(Mandatory=$true)][int]$TargetPid,
  [Parameter(Mandatory=$true)][long]$ExpectedStartTicksUtc,
  [Parameter(Mandatory=$true)][string]$ExpectedImage,
  [Parameter(Mandatory=$true)][string]$BarrierEvent,
  [Parameter(Mandatory=$true)][string]$ReceiptPath
)
# PROPOSED HARNESS ONLY. Not executed by this readonly investigation.
# Parent creates a uniquely named EventWaitHandle and sets it only after the
# exact target HTTP handler has validated the request. No sleep readiness.
$ErrorActionPreference = 'Stop'
$record = [ordered]@{mode='SYNTHETIC_CLI_INTERRUPT_HARNESS'; target_pid=$TargetPid; started_at=[DateTime]::UtcNow.ToString('o'); stage='barrier'; generated=$false}
$eventHandle = $null
$targetProcess = $null
try {
  $eventHandle = [Threading.EventWaitHandle]::OpenExisting($BarrierEvent)
  if (-not $eventHandle.WaitOne(10000)) { throw 'HTTP_BARRIER_TIMEOUT' }
  $targetProcess = [Diagnostics.Process]::GetProcessById($TargetPid)
  if ($targetProcess.HasExited) { throw 'TARGET_ALREADY_EXITED' }
  if ($targetProcess.StartTime.ToUniversalTime().Ticks -ne $ExpectedStartTicksUtc) { throw 'TARGET_CREATION_IDENTITY_CHANGED' }
  if (-not [String]::Equals([IO.Path]::GetFullPath($targetProcess.MainModule.FileName), [IO.Path]::GetFullPath($ExpectedImage), [StringComparison]::OrdinalIgnoreCase)) { throw 'TARGET_IMAGE_CHANGED' }
  Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class ConsoleBreakSender {
 [DllImport("kernel32.dll", SetLastError=true)] public static extern bool FreeConsole();
 [DllImport("kernel32.dll", SetLastError=true)] public static extern bool AttachConsole(uint pid);
 [DllImport("kernel32.dll", SetLastError=true)] public static extern bool GenerateConsoleCtrlEvent(uint code,uint group);
}
'@
  $record.stage='attach'
  # This is a dedicated hidden sender. Detaching never touches the test parent's console.
  [void][ConsoleBreakSender]::FreeConsole()
  if (-not [ConsoleBreakSender]::AttachConsole([uint32]$TargetPid)) {
    $record.win32_error=[Runtime.InteropServices.Marshal]::GetLastWin32Error()
    throw 'ATTACH_CONSOLE_FAILED'
  }
  $record.stage='generate'
  if (-not [ConsoleBreakSender]::GenerateConsoleCtrlEvent(1,[uint32]$TargetPid)) {
    $record.win32_error=[Runtime.InteropServices.Marshal]::GetLastWin32Error()
    throw 'GENERATE_CTRL_BREAK_FAILED'
  }
  $record.generated=$true
  $record.stage='sent_not_yet_proven_handled'
} catch {
  $record.error=$_.Exception.Message
} finally {
  if ('ConsoleBreakSender' -as [type]) { [void][ConsoleBreakSender]::FreeConsole() }
  if ($null -ne $eventHandle) { $eventHandle.Dispose() }
  if ($null -ne $targetProcess) { $targetProcess.Dispose() }
  $record.finished_at=[DateTime]::UtcNow.ToString('o')
  $json=$record | ConvertTo-Json -Depth 6
  [IO.File]::WriteAllText($ReceiptPath,$json,[Text.UTF8Encoding]::new($false))
}
if (-not $record.generated) { exit 1 }
exit 0
