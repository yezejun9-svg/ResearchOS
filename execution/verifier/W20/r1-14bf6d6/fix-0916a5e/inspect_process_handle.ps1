$ErrorActionPreference = 'Stop'
$process = Get-Process -Id $PID
$flags = [Reflection.BindingFlags]::Instance -bor [Reflection.BindingFlags]::NonPublic
$fields = $process.GetType().GetFields($flags) | Where-Object { $_.Name -match 'handle' -and $_.FieldType -eq [bool] }
function Snapshot([string]$stage) {
    $values = @{}
    foreach ($field in $fields) { $values[$field.Name] = $field.GetValue($process) }
    @{stage=$stage; private_handle_flags=$values}
}
$rows = @()
$rows += Snapshot 'after-GetProcess'
$created = $process.StartTime.ToUniversalTime().Ticks
$rows += Snapshot 'after-StartTime'
$handle = $process.Handle
$rows += Snapshot 'after-explicit-Handle'
@{powershell=$PSVersionTable.PSVersion.ToString(); framework=[Environment]::Version.ToString(); assembly=$process.GetType().Assembly.FullName; owned_self_pid=$PID; creation_ticks=$created; observations=$rows} | ConvertTo-Json -Depth 5
$process.Dispose()
