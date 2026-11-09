$ErrorActionPreference = 'Stop'
$driverReviewReceiptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$driverReviewScript = Join-Path $driverReviewReceiptRoot 'review_static.py'
$driverReviewPython = 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'
$driverReviewHash = Get-FileHash -Algorithm SHA256 -LiteralPath $driverReviewScript
$global:LASTEXITCODE = $null
& $driverReviewPython -I -S -X utf8 $driverReviewScript 1> (Join-Path $driverReviewReceiptRoot 'review.stdout.raw') 2> (Join-Path $driverReviewReceiptRoot 'review.stderr.raw')
$driverReviewNativeExit = $LASTEXITCODE
$driverReviewObservation=[ordered]@{schema='researchos.actual-native-observation.v1'; actor='codex:/root/f08_i17_binding_impl'; command=@($driverReviewPython,'-I','-S','-X','utf8',$driverReviewScript); cwd=(Get-Location).Path; script_sha256=$driverReviewHash.Hash.ToLowerInvariant(); actual_native_exit=$driverReviewNativeExit; candidate_executed=$false; target_calls=0; timestamp_utc=[DateTime]::UtcNow.ToString('o')}
$driverReviewObservation | ConvertTo-Json -Depth 8 | Set-Content -Encoding utf8NoBOM -LiteralPath (Join-Path $driverReviewReceiptRoot 'review.native-observation.json')
Get-Content -Raw -LiteralPath (Join-Path $driverReviewReceiptRoot 'review.stdout.raw')
if($driverReviewNativeExit -ne 0){Get-Content -Raw -LiteralPath (Join-Path $driverReviewReceiptRoot 'review.stderr.raw')}
Write-Output ('ACTUAL_NATIVE_EXIT='+$driverReviewNativeExit)
exit $driverReviewNativeExit
