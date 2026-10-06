[CmdletBinding()]
param(
    [string]$RepoRoot,
    [string]$QoderCli,
    [string]$PythonExecutable = 'python',
    [switch]$CheckOnly,
    [switch]$PrintOnly
)

$ErrorActionPreference = 'Stop'
$specRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$expectedModel = 'Qwen3.8-Flash'

try {
    if ($CheckOnly -and $PrintOnly) { throw 'Choose either -CheckOnly or -PrintOnly.' }
    if (-not $RepoRoot) { $RepoRoot = Join-Path (Split-Path $specRoot -Parent) 'research-os' }
    $RepoRoot = [IO.Path]::GetFullPath($RepoRoot)
    if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) {
        throw "ResearchOS repository does not exist: $RepoRoot"
    }
    if (-not $QoderCli) {
        $resolved = Get-Command qodercli.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($resolved) { $QoderCli = $resolved.Source }
        else { $QoderCli = Join-Path $env:USERPROFILE '.qoder\bin\qodercli\qodercli.exe' }
    }
    if (-not (Test-Path -LiteralPath $QoderCli -PathType Leaf)) {
        throw "Qoder CLI was not found: $QoderCli"
    }
    $QoderCli = (Resolve-Path -LiteralPath $QoderCli).Path
    $goalFile = Join-Path $specRoot 'GOAL_START.txt'
    if (-not (Test-Path -LiteralPath $goalFile -PathType Leaf)) { throw 'GOAL_START.txt is missing.' }
    $launchArgs = @('-w', $RepoRoot, '--add-dir', $specRoot, '--model', $expectedModel,
                    '--permission-mode', 'auto', '--name', 'ResearchOS-v2.4-build')
    if ($PrintOnly) {
        [ordered]@{
            mode = 'PRINT_ONLY_NO_EXECUTION'
            executable = $QoderCli
            argv = $launchArgs
            goal_file = $goalFile
            notice = 'Start the TUI, verify /status, then paste GOAL_START.txt. No Goal was started.'
        } | ConvertTo-Json -Depth 4
        exit 0
    }
    Push-Location $specRoot
    try {
        & $PythonExecutable (Join-Path $specRoot 'tools\validate_package.py')
        if ($LASTEXITCODE -ne 0) { throw 'Specification validation failed. Qoder was not started.' }
    } finally { Pop-Location }
    & $QoderCli --version
    if ($LASTEXITCODE -ne 0) { throw 'Qoder version probe failed.' }
    $modelList = @(& $QoderCli --list-models)
    if ($LASTEXITCODE -ne 0) { throw 'Qoder model catalog failed. No model was substituted.' }
    $modelNames = @($modelList | ForEach-Object { ([string]$_).Trim() })
    if ($modelNames -notcontains $expectedModel) {
        throw "Required model is absent from the current catalog: $expectedModel. No model was substituted."
    }
    Write-Host "CHECKS_OK: package validated; model present: $expectedModel"
    if ($CheckOnly) {
        Write-Host 'CHECK_ONLY: no model prompt, TUI, or Goal was started.'
        exit 0
    }
    Write-Host ''
    Write-Host 'In Qoder, verify /status and paste this Goal (not started automatically):'
    Get-Content -LiteralPath $goalFile -Raw -Encoding UTF8 | Write-Host
    & $QoderCli @launchArgs
    exit $LASTEXITCODE
} catch {
    [Console]::Error.WriteLine('QODER_START_FAILED: ' + $_.Exception.Message)
    exit 1
}
