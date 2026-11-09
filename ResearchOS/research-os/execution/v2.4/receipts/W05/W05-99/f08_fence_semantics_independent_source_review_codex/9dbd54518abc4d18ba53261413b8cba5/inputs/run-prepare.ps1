& 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe' -I -S -X utf8 "$PSScriptRoot/prepare_v3.py"
$f08PrepareNativeExit = $LASTEXITCODE
Write-Output "F08_PREPARE_NATIVE_EXIT=$f08PrepareNativeExit"
exit $f08PrepareNativeExit
