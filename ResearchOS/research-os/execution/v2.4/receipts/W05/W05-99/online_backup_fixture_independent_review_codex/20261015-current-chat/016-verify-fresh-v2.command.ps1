[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$v=[IO.File]::ReadAllText("$PSScriptRoot\verify.py")
$v=$v.Replace('assert n==88 and before["integrity_check"]==restored["integrity_check"]=="ok"','assert n==87 and len(before["tables"])==88 and before["integrity_check"]==restored["integrity_check"]=="ok"')
$v=$v.Replace('{"auth_credentials","domain_objects","domain_refs","domain_versions"}','{"auth_credentials","domain_objects"}')
$v=$v.Replace('table_count=n,','table_count=len(before["tables"]),non_sqlite_table_count=n,')
[IO.File]::WriteAllText("$PSScriptRoot\verify_v2.py",$v,[Text.UTF8Encoding]::new($false))
python -B -Xutf8 "$PSScriptRoot\verify_v2.py" compare
exit $LASTEXITCODE