param(
  [Parameter(Mandatory=$true)][string]$SkillUpExe,
  [Parameter(Mandatory=$true)][string]$FixtureRoot,
  [Parameter(Mandatory=$true)][string]$GoExe,
  [Parameter(Mandatory=$true)][string]$OutputDir
)
$ErrorActionPreference = 'Stop'
$probeSource = Join-Path $PSScriptRoot 'mock_qodercli.go'
$probeBin = Join-Path $OutputDir 'qodercli.exe'
$eval = Join-Path $FixtureRoot 'evals/eval.yaml'
foreach ($file in @($SkillUpExe,$probeSource,$eval,$GoExe)) {
  if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing input: $file" }
}
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
& $GoExe build -o $probeBin $probeSource
if ($LASTEXITCODE -ne 0) { throw "Fixture child build failed: $LASTEXITCODE" }
$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = (Resolve-Path -LiteralPath $SkillUpExe).Path
foreach ($arg in @('run',(Resolve-Path -LiteralPath $eval).Path,'--format','json','--output-dir',$OutputDir,'--iteration','1','--no-delete')) { [void]$psi.ArgumentList.Add($arg) }
$psi.WorkingDirectory = (Resolve-Path -LiteralPath $FixtureRoot).Path
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.Environment['PATH'] = "$OutputDir;$env:SystemRoot\System32"
$psi.Environment['HOME'] = $OutputDir
$psi.Environment['USERPROFILE'] = $OutputDir
$psi.Environment['LOCALAPPDATA'] = $OutputDir
$psi.Environment['APPDATA'] = $OutputDir
foreach ($key in @('QODER_PERSONAL_ACCESS_TOKEN','HTTP_PROXY','HTTPS_PROXY','ALL_PROXY')) { [void]$psi.Environment.Remove($key) }
$p = [System.Diagnostics.Process]::Start($psi)
$stdoutTask = $p.StandardOutput.ReadToEndAsync()
$stderrTask = $p.StandardError.ReadToEndAsync()
$p.WaitForExit()
$stdoutTask.GetAwaiter().GetResult() | Set-Content -Encoding utf8 (Join-Path $OutputDir 'stdout.log')
$stderrTask.GetAwaiter().GetResult() | Set-Content -Encoding utf8 (Join-Path $OutputDir 'stderr.log')
$resultPath = Join-Path $OutputDir 'iteration-1/result.json'
if (-not (Test-Path -LiteralPath $resultPath -PathType Leaf)) { throw "Native result.json missing; exit=$($p.ExitCode)" }
$result = Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
$counts = $result.case_results | Group-Object status | ForEach-Object { @{status=$_.Name;count=$_.Count} }
@{
  engine='skill-up'; source_revision='7f1ff9b8e2d7c654728de526867f2f7e7b78ea51';
  child='deterministic Go qodercli.exe fixture'; mode='DEVELOPMENT_FIXTURE';
  exit_code=$p.ExitCode; result_hash=(Get-FileHash -LiteralPath $resultPath -Algorithm SHA256).Hash;
  eval_hash=(Get-FileHash -LiteralPath $eval -Algorithm SHA256).Hash;
  binary_hash=(Get-FileHash -LiteralPath $SkillUpExe -Algorithm SHA256).Hash;
  child_hash=(Get-FileHash -LiteralPath $probeBin -Algorithm SHA256).Hash;
  counts=$counts
} | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 (Join-Path $OutputDir 'probe.json')
Get-Content -LiteralPath (Join-Path $OutputDir 'probe.json') -Raw
