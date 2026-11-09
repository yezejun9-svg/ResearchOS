$ErrorActionPreference = 'Stop'
$bindingReceiptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$bindingPython = 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'
$bindingScript = Join-Path $bindingReceiptRoot 'prepare_binding.py'
$bindingBefore = Get-FileHash -Algorithm SHA256 -LiteralPath $bindingScript
$global:LASTEXITCODE = $null
& $bindingPython -I -S -X utf8 $bindingScript 1> (Join-Path $bindingReceiptRoot 'prepare.stdout.txt') 2> (Join-Path $bindingReceiptRoot 'prepare.stderr.txt')
$bindingActualNativeExit = $LASTEXITCODE
$bindingObservation = [ordered]@{ schema='researchos.actual-native-observation.v1'; actor='codex:/root/f08_i17_binding_impl'; command=@($bindingPython,'-I','-S','-X','utf8',$bindingScript); cwd=(Get-Location).Path; script_sha256=$bindingBefore.Hash.ToLowerInvariant(); native_exit=$bindingActualNativeExit; candidate_execution=$false; observation='actual Python text/data preparation only'; timestamp_utc=[DateTime]::UtcNow.ToString('o') }
$bindingObservation | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8NoBOM -LiteralPath (Join-Path $bindingReceiptRoot 'prepare.native-observation.json')
Get-Content -Raw -LiteralPath (Join-Path $bindingReceiptRoot 'prepare.stdout.txt')
Write-Output ('ACTUAL_NATIVE_EXIT='+$bindingActualNativeExit)
exit $bindingActualNativeExit
