param([ValidateSet('prepare','audit','seal')][string]$Phase, [string]$ObservationPrefix = '')
$ErrorActionPreference = 'Stop'
$receiptRoot = $PSScriptRoot
if ($ObservationPrefix -eq '') { $ObservationPrefix = $Phase }
if ($ObservationPrefix -notmatch '^[A-Za-z0-9.-]+$') { throw 'Owned metadata observation prefix required' }
$receiptScripts = @{ prepare = 'revise_prepare.py'; audit = 'audit_revision.py'; seal = 'seal_revision.py' }
$receiptScript = Join-Path $receiptRoot $receiptScripts[$Phase]
$pinnedPython = 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'
if ($Phase -eq 'seal') {
    & $pinnedPython -I -S -X utf8 $receiptScript
    $metadataNativeExit = $LASTEXITCODE
    Write-Output ('ACTUAL_NATIVE_EXIT=' + $metadataNativeExit)
    exit $metadataNativeExit
}
$metadataStdout = Join-Path $receiptRoot ($ObservationPrefix + '.stdout.txt')
$metadataStderr = Join-Path $receiptRoot ($ObservationPrefix + '.stderr.txt')
if ((Test-Path -LiteralPath $metadataStdout) -or (Test-Path -LiteralPath $metadataStderr)) { throw 'Original metadata tool logs must not be overwritten' }
& $pinnedPython -I -S -X utf8 $receiptScript 1> $metadataStdout 2> $metadataStderr
$metadataNativeExit = $LASTEXITCODE
$metadataObservation = [ordered]@{
    schema = 'researchos.actual-native-observation.v1'
    actor = 'codex:/root/f08_i17_binding_impl'
    phase = $Phase
    executable = $pinnedPython
    argv = @('-I','-S','-X','utf8',$receiptScript)
    actual_native_exit = $metadataNativeExit
    native_exit_source = 'PowerShell LASTEXITCODE captured immediately after exact Python process'
    outer_exit = $null
    outer_exit_authority = 'External exec_command result; this native observation is not an outer result'
    target_helper_Go_SQL_SDK_HTTP_model_calls = 0
    stdout_path = $metadataStdout
    stderr_path = $metadataStderr
}
$metadataJSON = $metadataObservation | ConvertTo-Json -Depth 8
$metadataEncoding = [Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllText((Join-Path $receiptRoot ($ObservationPrefix + '.native-observation.json')), $metadataJSON + "`n", $metadataEncoding)
Get-Content -Raw -LiteralPath $metadataStdout
if ((Get-Item -LiteralPath $metadataStderr).Length -gt 0) {
    Get-Content -Raw -LiteralPath $metadataStderr
}
Write-Output ('ACTUAL_NATIVE_EXIT=' + $metadataNativeExit)
exit $metadataNativeExit
