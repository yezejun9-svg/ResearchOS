param([string]$PrepareChunk, [int]$PrepareOuter, [int]$PrepareNative)
& 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe' -I -S -X utf8 "$PSScriptRoot/seal_namespace.py" $PrepareChunk $PrepareOuter $PrepareNative
$f08SealNativeExit = $LASTEXITCODE
Write-Output "F08_SEAL_NATIVE_EXIT=$f08SealNativeExit"
exit $f08SealNativeExit
