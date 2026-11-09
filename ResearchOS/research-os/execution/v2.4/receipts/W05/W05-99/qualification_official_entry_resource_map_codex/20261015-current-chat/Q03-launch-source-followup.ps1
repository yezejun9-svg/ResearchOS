$root='D:/作品集/ResearchOS/research-os'
'ROOT_ENTRY_FILENAMES'
Get-ChildItem -LiteralPath $root -File -Force|Select-Object -ExpandProperty Name
'KNOWN_ACTIVATION'
foreach($rel in @('execution/v2.4/receipts/W05/W05-99/normal_desktop_attach_retry09_codex/20261014-current-chat/launch.json','execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp494/normal-desktop-reopen-new-qualification-scope.json')){
 $p=Join-Path $root $rel;$obj=Get-Content -LiteralPath $p -Raw|ConvertFrom-Json
 'FILE '+$rel+' SHA256='+(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower()
 foreach($prop in $obj.PSObject.Properties){if($prop.Name -match 'key|secret|password|token|credential|env'){continue};if($prop.Name -match 'launch|script|package|scope|path|root|command|argv|args|receipt|rule|require|pid|session|schema'){$prop.Name; $prop.Value|ConvertTo-Json -Depth 8}}
}
'SOURCE_LAUNCH_MATCHES'
$files=@('apps/desktop/main/main.js','apps/desktop/main/lib/desktop-management.js','apps/desktop/main/lib/host.js','apps/control/prepared_recovery_windows.go','apps/control/replay_command.go','ops/supervisor/release_host/control_windows.go')
foreach($rel in $files){
 $p=Join-Path $root $rel;if(Test-Path -LiteralPath $p){'FILE '+$rel;& rg -n -C 3 'spawn\(|exec\.|start\(|restart|Restart|setLoginItem|loginItem|register.*Protocol|setAsDefaultProtocol|relaunch|process\.env|fixture|go run|--' $p;'NATIVE_RG_EXIT='+$LASTEXITCODE}
}
foreach($p in @('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-profile-c8b7adab-20261014/apps/desktop/main/main.js','C:/Users/yqyyds/.codex/researchos-resource-cache/normal-verifier-replacement-4f4023-20261015/apps/desktop/main/main.js')){
 'PACKAGE_ENTRY '+$p+' SHA256='+(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower()
 & rg -n -C 2 'configuredCore|coreExecutable|dataRoot|verifierManifest|runtimeAssetsDir|RESEARCHOS_|desktopManagement|require\(' $p
 'NATIVE_RG_EXIT='+$LASTEXITCODE
}

