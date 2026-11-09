$root='D:/作品集/ResearchOS/research-os'
$rels=@('README.md','Makefile','apps/desktop/main/main.js','apps/desktop/main/lib/context.js','apps/desktop/main/lib/host.js','apps/desktop/main/lib/desktop-management.js','ops/supervisor/release_host/main.go','apps/control/main.go')
foreach($rel in $rels){
 $p=Join-Path $root $rel
 if(Test-Path -LiteralPath $p){'SOURCE '+$rel+' SHA256='+(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower();$lines=Get-Content -LiteralPath $p;for($n=0;$n -lt $lines.Count;$n++){if($rel -like '*desktop*' -or $lines[$n] -match 'electron|go run|release_host|backup|replay|recover|migration|flag\.|RESEARCHOS_|exec\.|start|Restart|restart|autostart'){'{0}:{1}' -f ($n+1),$lines[$n]}}}else{'ABSENT '+$rel}
}
foreach($p in @('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-profile-c8b7adab-20261014/apps/desktop/main/lib/context.js','C:/Users/yqyyds/.codex/researchos-resource-cache/normal-verifier-replacement-4f4023-20261015/apps/desktop/main/lib/context.js')){
 'PACKAGE_CONTEXT '+$p;Get-Content -LiteralPath $p -Raw
}
foreach($rel in @('execution/v2.4/receipts/W05/W05-99/verifier_replacement_package_codex/20261015-current-chat/FINAL-manifest.json','execution/v2.4/receipts/W05/W05-99/coding_profile_desktop_build_codex/20261014-current-chat/FINAL-manifest.json')){
 $p=Join-Path $root $rel;$obj=Get-Content -LiteralPath $p -Raw|ConvertFrom-Json
 'MANIFEST '+$rel+' SHA256='+(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower()
 'TOP_KEYS';$obj.PSObject.Properties.Name
 function Find-LauncherPath($o,$prefix){
  if($null -eq $o){return}
  if($o -is [string]){if($o.Length -lt 600 -and $o -match '(launch_and_wait\.py|launch[^ /\\]*\.(py|ps1|cmd)|activation[^ /\\]*\.json)$'){[PSCustomObject]@{field=$prefix;path=$o}|ConvertTo-Json -Compress};return}
  if($o -is [array]){$index=0;foreach($v in $o){Find-LauncherPath $v ($prefix+'['+$index+']');$index++};return}
  if($o -is [PSCustomObject]){foreach($p2 in $o.PSObject.Properties){Find-LauncherPath $p2.Value ($prefix+'.'+$p2.Name)}}
 }
 Find-LauncherPath $obj ''
}
foreach($rel in @('execution/v2.4/receipts/W05/W05-99/normal_desktop_attach_retry09_codex/20261014-current-chat','execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp494','.local/live/current-chat-normal-desktop-first-use-20261012')){
 $p=Join-Path $root $rel;if(Test-Path -LiteralPath $p){'LAUNCHER_FILENAME_SCOPE '+$rel;Get-ChildItem -LiteralPath $p -File -Force|Where-Object {$_.Name -match 'launch|activation|scope|package|invoke'}|Select-Object -ExpandProperty FullName}else{'ABSENT '+$rel}
}

