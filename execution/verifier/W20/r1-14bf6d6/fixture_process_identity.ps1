param([Parameter(Mandatory=$true)][int]$ProcessIdToInspect)
$ErrorActionPreference = 'Stop'
$process = Get-Process -Id $ProcessIdToInspect -ErrorAction SilentlyContinue
if (-not $process) { @{pid=$ProcessIdToInspect; alive=$false} | ConvertTo-Json -Compress; exit 0 }
$cim = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessIdToInspect"
@{pid=$ProcessIdToInspect; alive=$true; creation_time_utc=$process.StartTime.ToUniversalTime().ToString('o'); executable=$cim.ExecutablePath; command_line=$cim.CommandLine} | ConvertTo-Json -Compress
