& 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe' -I -S -X utf8 "$PSScriptRoot/audit_patch_bytes.py"
$f08AuditNativeExit = $LASTEXITCODE
Write-Output "F08_AUDIT_NATIVE_EXIT=$f08AuditNativeExit"
exit $f08AuditNativeExit
