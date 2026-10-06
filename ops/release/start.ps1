param(
    [Parameter(Mandatory = $true)][string]$DataDir,
    [Parameter(Mandatory = $true)][string]$Listen,
    [switch]$Fresh
)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd('\', '/')
& (Join-Path $PSScriptRoot 'verify.ps1') -ReleaseRoot $root | Out-Null
if (-not [IO.Path]::IsPathRooted($DataDir)) { throw 'DataDir must be absolute' }
$data = [IO.Path]::GetFullPath($DataDir).TrimEnd('\', '/')
if ($data.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or $data -eq $root) { throw 'DataDir must be outside release root' }
if ($Listen -notmatch '^127\.0\.0\.1:([0-9]{2,5})$') { throw 'Listen must be 127.0.0.1:<port>' }
$port = [int]$Matches[1]
if ($port -lt 1024 -or $port -gt 65535 -or $port -in @(32736, 79136)) { throw 'Listen port unavailable for fixture' }
if ((Test-Path -LiteralPath $data) -and $Fresh -and @(Get-ChildItem -LiteralPath $data -Force).Count -ne 0) { throw 'Fresh DataDir is not empty' }
New-Item -ItemType Directory -Force -Path $data | Out-Null
$pidFile = Join-Path $data 'fixture-control.pid'
if (Test-Path -LiteralPath $pidFile) { throw 'fixture PID file already exists' }
function PathHash([string]$path) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($path.ToUpperInvariant()))).Replace('-', '').ToLowerInvariant() }
    finally { $sha.Dispose() }
}
$instance = [guid]::NewGuid().ToString('N')
$dataHash = PathHash $data
$rootHash = PathHash $root
$identityArgs = "-- researchos-fixture-$instance data-$dataHash root-$rootHash"
$env:RESEARCHOS_DATA_DIR = $data
$env:RESEARCHOS_WEB_DIR = Join-Path $root 'web/dist'
$env:RESEARCHOS_LISTEN = $Listen
$control = Join-Path $root 'bin/control.exe'
$process = Start-Process -FilePath $control -ArgumentList $identityArgs -WorkingDirectory $root -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $data 'control.stdout.log') -RedirectStandardError (Join-Path $data 'control.stderr.log')
try {
    $native = Get-CimInstance Win32_Process -Filter "ProcessId=$($process.Id)"
    if (-not $native -or -not $native.CommandLine.Contains($identityArgs) -or -not [string]::Equals($native.ExecutablePath, $control, [StringComparison]::OrdinalIgnoreCase)) { throw 'fixture process identity unavailable' }
    $created = $process.StartTime.ToUniversalTime().Ticks
    @{ schema = 'researchos.fixture-process.v1'; pid = $process.Id; created_utc_ticks = $created; instance = $instance; data_dir = $data; release_root = $root; listen = $Listen } | ConvertTo-Json -Compress | Set-Content -LiteralPath $pidFile -NoNewline
} catch {
    if (-not $process.HasExited) { $process.Kill() }
    Remove-Item -LiteralPath $pidFile -ErrorAction SilentlyContinue
    throw
}
$healthy = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 250
    if ($process.HasExited) { break }
    try {
        $reply = Invoke-WebRequest -Uri "http://$Listen/healthz" -TimeoutSec 2 -UseBasicParsing
        if ($reply.StatusCode -eq 200) { $healthy = $true; break }
    } catch { }
}
if (-not $healthy) {
    if (-not $process.HasExited) { $process.Kill() }
    Remove-Item -LiteralPath $pidFile -ErrorAction SilentlyContinue
    throw 'fixture control did not become healthy; inspect DataDir logs'
}
@{ status = 'FIXTURE_RUNNING'; pid = $process.Id; listen = $Listen; data_dir = $data } | ConvertTo-Json -Compress
