param([Parameter(Mandatory = $true)][string]$DataDir)
$ErrorActionPreference = 'Stop'
if (-not [IO.Path]::IsPathRooted($DataDir)) { throw 'DataDir must be absolute' }
$data = [IO.Path]::GetFullPath($DataDir)
$pidFile = Join-Path $data 'fixture-control.pid'
if (-not (Test-Path -LiteralPath $pidFile -PathType Leaf)) { throw 'fixture PID file missing' }
$processId = [int](Get-Content -LiteralPath $pidFile -Raw).Trim()
$process = Get-Process -Id $processId -ErrorAction SilentlyContinue
if ($process) {
    $root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\', '/')
    $expected = [IO.Path]::GetFullPath((Join-Path $root 'bin/control.exe'))
    $actual = (Get-CimInstance Win32_Process -Filter "ProcessId=$processId").ExecutablePath
    if (-not [string]::Equals($expected, $actual, [StringComparison]::OrdinalIgnoreCase)) { throw 'PID belongs to another executable' }
    # R1 has only a disposable fixture control. Production drain/SCM is R2.
    Stop-Process -Id $processId -Force
    Wait-Process -Id $processId -Timeout 10 -ErrorAction SilentlyContinue
}
Remove-Item -LiteralPath $pidFile
@{ status = 'FIXTURE_STOPPED'; pid = $processId; data_preserved = $data } | ConvertTo-Json -Compress
