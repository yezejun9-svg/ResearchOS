$ErrorActionPreference = 'Stop'
$driverReviewReceiptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$global:LASTEXITCODE = $null
& 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe' -I -S -X utf8 (Join-Path $driverReviewReceiptRoot 'seal_review.py')
$driverReviewNativeExit = $LASTEXITCODE
Write-Output ('ACTUAL_NATIVE_EXIT='+$driverReviewNativeExit)
exit $driverReviewNativeExit
