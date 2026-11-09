$ErrorActionPreference='Stop'
$out='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_maintenance_c57_independent_review_codex\20261025-current-chat\token-privilege-static'
$source=Join-Path $out 'v12-snapshot\internal\recoveryboundary\boot_windows.go'
rg -n 'tokenSecurityShape|rejectFenceBypassPrivileges|inspectExistingBusinessProcess|captureOfficialBusinessToken|verifiedBusinessGroups|checkAncestorControl|BusinessPrivilegesSHA256|ensureOwnerRestorable|AdjustTokenPrivileges|preflightManagementRestore|preflightInstalledRestore' $source
"NATIVE_EXIT=$LASTEXITCODE"
$lines=Get-Content -LiteralPath $source -Encoding UTF8
foreach($range in @(@(820,908),@(1250,1328),@(1410,1495),@(1570,1635),@(2245,2315))) {
 foreach($i in $range[0]..$range[1]) { '{0}: {1}' -f $i,$lines[$i-1] }
}
$test=Join-Path $out 'v12-snapshot\internal\recoveryboundary\boot_windows_test.go'
rg -n 'TestBusinessPrivilegeAdmission|TestOfficialBusinessProducer|rejectFenceBypassPrivileges|Skipf\("current native token' $test
"NATIVE_EXIT=$LASTEXITCODE"