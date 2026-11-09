param(
  [Parameter(Mandatory=$true)][string]$WitnessPath,
  [Parameter(Mandatory=$true)][string]$CoreImage,
  [Parameter(Mandatory=$true)][string]$Workspace,
  [Parameter(Mandatory=$true)][string]$OutDirectory
)
$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class ResearchOSPipeServerPid {
  [DllImport("kernel32.dll", SetLastError=true)]
  public static extern bool GetNamedPipeServerProcessId(IntPtr pipe, out uint serverPid);
}
'@

function Read-Witness {
  $w = Get-Content -LiteralPath $WitnessPath -Raw -Encoding utf8 | ConvertFrom-Json
  if ($w.schema -ne 'researchos.product-supervisor/1' -or $w.state -ne 'READY') { throw 'WITNESS_NOT_READY' }
  if ($w.control_process.PID -le 0 -or $w.host_id -notmatch '^host-[0-9a-f]{12}$') { throw 'WITNESS_CORE_ID_INVALID' }
  return $w
}
function Assert-Core($w) {
  $pidExpected = [int]$w.control_process.PID
  $row = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $pidExpected)
  if (!$row -or $row.ExecutablePath -ine $CoreImage) { throw 'CORE_IMAGE_MISMATCH' }
  $process = Get-Process -Id $pidExpected
  $createdNS = [long](($process.StartTime.ToUniversalTime().Ticks - [long]621355968000000000) * [long]100)
  if ($createdNS.ToString() -ne [string]$w.control_process.CreatedNS) { throw 'CORE_CREATION_MISMATCH' }
  $hash = (Get-FileHash -LiteralPath $CoreImage -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($hash -ne [string]$w.control_process.ImageSHA256) { throw 'CORE_HASH_MISMATCH' }
  return $pidExpected
}

$w = Read-Witness
$corePid = Assert-Core $w
$pipeName = 'ResearchOSHost-v1-' + $w.host_id.Substring(5)
$pipe = [System.IO.Pipes.NamedPipeClientStream]::new('.', $pipeName, [System.IO.Pipes.PipeDirection]::InOut)
try {
  $pipe.Connect(3000)
  $pipe.ReadMode = [System.IO.Pipes.PipeTransmissionMode]::Message
  [uint32]$serverPid = 0
  if (![ResearchOSPipeServerPid]::GetNamedPipeServerProcessId($pipe.SafePipeHandle.DangerousGetHandle(), [ref]$serverPid)) {
    throw ('PIPE_SERVER_PID_UNAVAILABLE:' + [Runtime.InteropServices.Marshal]::GetLastWin32Error())
  }
  if ($serverPid -ne $corePid) { throw 'PIPE_SERVER_NOT_WITNESSED_CORE' }
  $w2 = Read-Witness
  if ($w2.host_id -ne $w.host_id -or $w2.control_process.PID -ne $w.control_process.PID -or
      $w2.control_process.CreatedNS -ne $w.control_process.CreatedNS -or
      $w2.control_process.ImageSHA256 -ne $w.control_process.ImageSHA256) { throw 'WITNESS_CHANGED_BEFORE_REQUEST' }
  [void](Assert-Core $w2)
  $request = @{ kind='NATIVE_WORKSPACE_CHOOSE_REQUEST'; client_id='native-chooser-diagnosis-02';
    payload=@{requested_path=$Workspace; requested_access='READ_WRITE'} } | ConvertTo-Json -Compress -Depth 5
  $requestBytes = [System.Text.Encoding]::UTF8.GetBytes($request)
  if ($requestBytes.Length -eq 0 -or $requestBytes.Length -gt 8192) { throw 'REQUEST_SIZE_INVALID' }
  [System.IO.File]::WriteAllBytes((Join-Path $OutDirectory 'native-request.raw'), $requestBytes)
  $pipe.Write($requestBytes, 0, $requestBytes.Length)
  $pipe.Flush()
  $buffer = [byte[]]::new(8192)
  $bytes = [System.IO.MemoryStream]::new()
  do {
    $n = $pipe.Read($buffer, 0, $buffer.Length)
    if ($n -le 0) { throw 'NATIVE_REPLY_EMPTY' }
    $bytes.Write($buffer, 0, $n)
    if ($bytes.Length -gt 8192) { throw 'NATIVE_REPLY_TOO_LARGE' }
  } until ($pipe.IsMessageComplete)
  $replyBytes = $bytes.ToArray()
  [System.IO.File]::WriteAllBytes((Join-Path $OutDirectory 'native-reply.raw'), $replyBytes)
  $w3 = Read-Witness
  if ($w3.host_id -ne $w.host_id -or $w3.control_process.PID -ne $w.control_process.PID -or
      $w3.control_process.CreatedNS -ne $w.control_process.CreatedNS -or
      $w3.control_process.ImageSHA256 -ne $w.control_process.ImageSHA256) { throw 'WITNESS_CHANGED_AFTER_REPLY' }
  [void](Assert-Core $w3)
  [uint32]$serverPidAfter = 0
  if (![ResearchOSPipeServerPid]::GetNamedPipeServerProcessId($pipe.SafePipeHandle.DangerousGetHandle(), [ref]$serverPidAfter) -or $serverPidAfter -ne $corePid) {
    throw 'PIPE_SERVER_CHANGED_AFTER_REPLY'
  }
  $reply = [System.Text.Encoding]::UTF8.GetString($replyBytes) | ConvertFrom-Json
  if ($reply.kind -ne 'NATIVE_ERROR' -and $reply.kind -ne 'NATIVE_WORKSPACE_CHOOSE_RESULT') { throw 'UNEXPECTED_REPLY_KIND' }
  @{request_sent=1; pipe_server_pid=$serverPid; pipe_server_pid_after=$serverPidAfter;
    core_pid=$corePid; host_id=$w.host_id; reply_kind=$reply.kind;
    error_code=$reply.error.code; error_message=$reply.error.message;
    selection_ref=$reply.payload.selection_ref; display_path=$reply.payload.display_path} | ConvertTo-Json -Compress -Depth 5
} finally {
  $pipe.Dispose()
}
