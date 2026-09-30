param([Parameter(Mandatory = $true)][string]$DataDir)
$ErrorActionPreference = 'Stop'
if (-not [IO.Path]::IsPathRooted($DataDir)) { throw 'DataDir must be absolute' }
$data = [IO.Path]::GetFullPath($DataDir).TrimEnd('\', '/')
$pidFile = Join-Path $data 'fixture-control.pid'
if (-not (Test-Path -LiteralPath $pidFile -PathType Leaf)) { throw 'fixture PID file missing' }
$record = Get-Content -LiteralPath $pidFile -Raw | ConvertFrom-Json
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\', '/')
if ($record.schema -ne 'researchos.fixture-process.v1' -or $record.pid -notmatch '^[0-9]+$' -or $record.instance -notmatch '^[a-f0-9]{32}$' -or -not [string]::Equals($record.data_dir, $data, [StringComparison]::OrdinalIgnoreCase) -or -not [string]::Equals($record.release_root, $root, [StringComparison]::OrdinalIgnoreCase)) { throw 'fixture identity record does not match requested DataDir and release root' }
function PathHash([string]$path) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($path.ToUpperInvariant()))).Replace('-', '').ToLowerInvariant() }
    finally { $sha.Dispose() }
}
$dataHash = PathHash $data
$rootHash = PathHash $root
$identityArgs = "-- researchos-fixture-$($record.instance) data-$dataHash root-$rootHash"
$processId = [int]$record.pid
$process = Get-Process -Id $processId -ErrorAction SilentlyContinue
if (-not $process) { throw 'recorded fixture process is absent; retain identity file for investigation' }
$native = Get-CimInstance Win32_Process -Filter "ProcessId=$processId"
$expected = [IO.Path]::GetFullPath((Join-Path $root 'bin/control.exe'))
if (-not $native -or -not [string]::Equals($expected, $native.ExecutablePath, [StringComparison]::OrdinalIgnoreCase) -or -not $native.CommandLine.Contains($identityArgs) -or $process.StartTime.ToUniversalTime().Ticks -ne [int64]$record.created_utc_ticks) { throw 'recorded PID does not match fixture creation and OS command line' }
# The Process object holds the validated process handle; do not re-resolve a PID.
$process.Kill()
$process.WaitForExit(10000) | Out-Null
if (-not $process.HasExited) { throw 'fixture process did not stop; retain identity file' }
Remove-Item -LiteralPath $pidFile
@{ status = 'FIXTURE_STOPPED'; pid = $processId; data_preserved = $data } | ConvertTo-Json -Compress
