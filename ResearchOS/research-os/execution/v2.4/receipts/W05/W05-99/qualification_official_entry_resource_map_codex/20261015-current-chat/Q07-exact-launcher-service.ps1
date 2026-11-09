$root='D:/作品集/ResearchOS/research-os'
$launcher=Join-Path $root 'execution/v2.4/receipts/W05/W05-99/normal_qualification_actual_observer_codex/20261012-current-chat/launch_and_wait.py'
'ACTUAL_LAUNCHER '+$launcher+' SHA256='+(Get-FileHash -LiteralPath $launcher -Algorithm SHA256).Hash.ToLower()
Get-Content -LiteralPath $launcher -Raw
'TOP_DIRECTORY_NAMES';Get-ChildItem -LiteralPath $root -Directory|Select-Object -ExpandProperty Name
'KNOWN_OPERATOR_SCRIPT_FILENAMES'
& rg --files (Join-Path $root 'ops') -g '*.ps1' -g '*.cmd' -g '*.bat' -g '*.sh' -g '*.py'
'NATIVE_RG_EXIT='+$LASTEXITCODE
foreach($rel in @('apps/control/prepared_recovery_windows.go','adapters/runtime/data_root_windows.go','apps/cli/main.go')){
 $p=Join-Path $root $rel;if(Test-Path -LiteralPath $p){'SOURCE '+$rel+' SHA256='+(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower();if($rel -like '*prepared_recovery*'){Get-Content -LiteralPath $p -Raw}else{& rg -n -C 2 'coordinator.lock|\.lock|func main|flag\.|RESEARCHOS_|ReadFile|credential|exec\.|go run' $p;'NATIVE_RG_EXIT='+$LASTEXITCODE}}else{'ABSENT '+$rel}
}
'PRODUCT_SERVICE_EXACT_REGISTRY'
$sp='Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\ResearchOSVerifierCanary'
try{
 $svc=Get-ItemProperty -LiteralPath $sp -ErrorAction Stop
 $row=@{path=$sp;status='READ';properties=@{}}
 foreach($name in @('ImagePath','DisplayName','Description','Type','Start','ErrorControl','ObjectName','FailureActions','FailureActionsOnNonCrashFailures')){if($svc.PSObject.Properties.Name -contains $name){$row.properties[$name]=$svc.$name}}
 $row|ConvertTo-Json -Depth 10
 $row|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'canary-service-metadata.json') -Encoding utf8
}catch{@{path=$sp;status='UNKNOWN';error=$_.Exception.Message}|ConvertTo-Json}
'OWN_METADATA_SUMMARY'
$m=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'file-ancestor-metadata.json') -Raw|ConvertFrom-Json
@{records=$m.records.Count;read=@($m.records|Where-Object status -eq 'READ').Count;unknown=@($m.records|Where-Object status -like 'UNKNOWN*').Count;absent=@($m.records|Where-Object status -eq 'ABSENT').Count;fileid_nonzero=@($m.records|Where-Object {$_.fsutil_file_id -and $_.fsutil_file_id.native_exit_code -ne 0}).Count;actual_data_rows=@($m.records|Where-Object kind -eq 'ACTUAL_DATA_METADATA_ONLY'|Select-Object path,status,sha256,bytes,fsutil_file_id);reparse=@($m.records|Where-Object reparse -eq $true|Select-Object path,link_type,link_targets)}|ConvertTo-Json -Depth 10

