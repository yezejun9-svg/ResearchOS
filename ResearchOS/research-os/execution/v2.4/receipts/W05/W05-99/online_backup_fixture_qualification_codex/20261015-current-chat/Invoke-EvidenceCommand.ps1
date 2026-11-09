param(
  [Parameter(Mandatory=$true)][string]$Id,
  [Parameter(Mandatory=$true)][string]$Exe,
  [string[]]$Arguments = @(),
  [Parameter(Mandatory=$true)][string]$WorkingDirectory,
  [hashtable]$EnvOverride = @{},
  [switch]$Quiet
)
$ErrorActionPreference = 'Stop'
$evidenceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($Id -notmatch '^[a-zA-Z0-9_-]+$') { throw 'Invalid evidence id' }
$recipePath = Join-Path $evidenceRoot "$Id.recipe.json"
$stdoutPath = Join-Path $evidenceRoot "$Id.stdout.raw"
$stderrPath = Join-Path $evidenceRoot "$Id.stderr.raw"
$exitPath = Join-Path $evidenceRoot "$Id.exit.json"
if (Test-Path -LiteralPath $recipePath) { throw "Recipe already exists: $Id" }
$recipe = [ordered]@{
  id = $Id
  at_utc = [DateTime]::UtcNow.ToString('o')
  exe = $Exe
  argv = @($Arguments)
  cwd = $WorkingDirectory
  env_override = $EnvOverride
  stdout = [IO.Path]::GetFileName($stdoutPath)
  stderr = [IO.Path]::GetFileName($stderrPath)
  status = 'prewritten'
}
$recipe | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $recipePath -Encoding utf8NoBOM
$psi = [Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $Exe
$psi.WorkingDirectory = $WorkingDirectory
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.StandardOutputEncoding = [Text.UTF8Encoding]::new($false)
$psi.StandardErrorEncoding = [Text.UTF8Encoding]::new($false)
foreach ($arg in $Arguments) { [void]$psi.ArgumentList.Add($arg) }
foreach ($name in $EnvOverride.Keys) { $psi.Environment[$name] = [string]$EnvOverride[$name] }
$p = [Diagnostics.Process]::new()
$p.StartInfo = $psi
$startError = $null
try {
  [void]$p.Start()
  $outTask = $p.StandardOutput.ReadToEndAsync()
  $errTask = $p.StandardError.ReadToEndAsync()
  $p.WaitForExit()
  $outTask.GetAwaiter().GetResult() | Set-Content -LiteralPath $stdoutPath -Encoding utf8NoBOM -NoNewline
  $errTask.GetAwaiter().GetResult() | Set-Content -LiteralPath $stderrPath -Encoding utf8NoBOM -NoNewline
  $code = $p.ExitCode
} catch {
  $startError = $_.Exception.Message
  $code = -1
  '' | Set-Content -LiteralPath $stdoutPath -Encoding utf8NoBOM -NoNewline
  $startError | Set-Content -LiteralPath $stderrPath -Encoding utf8NoBOM -NoNewline
}
$exit = [ordered]@{ id=$Id; native_exit=$code; at_utc=[DateTime]::UtcNow.ToString('o'); start_error=$startError }
$exit | ConvertTo-Json -Compress | Set-Content -LiteralPath $exitPath -Encoding utf8NoBOM
if (-not $Quiet) {
  Write-Output "[$Id] native exit $code"
  Get-Content -LiteralPath $stdoutPath -Raw
  if ((Get-Item -LiteralPath $stderrPath).Length -gt 0) { Write-Output "[$Id] stderr captured: $stderrPath" }
}
exit $code
