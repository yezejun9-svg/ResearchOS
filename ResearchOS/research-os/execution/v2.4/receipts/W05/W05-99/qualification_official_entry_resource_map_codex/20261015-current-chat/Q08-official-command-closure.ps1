$root='D:/作品集/ResearchOS/research-os'
foreach($rel in @('ops/release/start.ps1','ops/release/build.py','apps/cli/main.go')){
 $p=Join-Path $root $rel;'FILE '+$rel+' SHA256='+(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower()
 $lines=Get-Content -LiteralPath $p
 for($i=0;$i -lt $lines.Count;$i++){
  if($rel -eq 'ops/release/start.ps1' -or $lines[$i] -match 'go|exe|RESEARCHOS|discovery|credentials|exec|build|def |if __name__|func main|case |protocol|Dial|Connect|Run|transport|recovery'){'{0}:{1}' -f ($i+1),$lines[$i]}
 }
}
'SCRIPTS_FILENAMES'
Get-ChildItem -LiteralPath (Join-Path $root 'scripts') -File|Select-Object -ExpandProperty FullName
'OPERATOR_DOC_LOCATORS'
& rg -l 'go run ./apps/control|go run ./apps/cli|scripts/dev|ops/release/start|electron.*apps/desktop|ResearchOSVerifierCanary|RegisterApplicationRestart|setLoginItemSettings|app.relaunch' (Join-Path $root 'docs') (Join-Path $root 'ops') (Join-Path $root 'internal/protectedstore') (Join-Path $root 'apps/desktop/main')
'NATIVE_RG_EXIT='+$LASTEXITCODE
$activation=Join-Path $root 'execution/v2.4/receipts/W05/W05-99/normal_desktop_verifier_replacement_activation_codex/20261015-current-chat/attempt01/launch.json'
if(Test-Path -LiteralPath $activation){
 'CURRENT_ACTIVATION_RECEIPT_SHA256='+(Get-FileHash -LiteralPath $activation -Algorithm SHA256).Hash.ToLower()
 $a=Get-Content -LiteralPath $activation -Raw|ConvertFrom-Json
 $record=@{path=$activation;schema=$a.schema;at=$a.at;pid=$a.pid;argv=$a.argv;cwd=$a.cwd;smoke_mode=$a.smoke_mode;removed_environment_names=$a.removed_environment_names;explicit_environment=@{};classification='HISTORICAL_ACTIVATION_RECORD_NOT_CURRENT_PROCESSCOMMANDLINE'}
 foreach($name in @('RESEARCHOS_DATA_DIR','RESEARCHOS_DESKTOP_USER_DATA','RESEARCHOS_CLI_DISCOVERY','RESEARCHOS_HOST_DISCOVERY')){if($a.explicit_environment.PSObject.Properties.Name -contains $name){$record.explicit_environment[$name]=$a.explicit_environment.$name}}
 $record|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'actual-activation-binding.json') -Encoding utf8
 $record|ConvertTo-Json -Depth 10
}else{'ACTUAL_ACTIVATION_RECEIPT_ABSENT'}
'FOCUSED_ANCESTOR_ACL'
$m=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'file-ancestor-metadata.json') -Raw|ConvertFrom-Json
foreach($r in $m.records){
 if($r.path -in @('D:\','D:\作品集','D:\作品集\ResearchOS','D:\作品集\ResearchOS\research-os','C:\Users\yqyyds','C:\Users\yqyyds\.codex','C:\Users\yqyyds\.codex\researchos-resource-cache') -or $r.path -match 'electron.exe$|researchos-control.exe$|apps\\desktop\\main\\main.js$'){
  @{path=$r.path;owner=$r.acl.owner;sddl=$r.acl.sddl;sha256=$r.sha256;fileid=$r.fsutil_file_id.raw;hardlinks=$r.fsutil_hardlinks.raw}|ConvertTo-Json -Depth 5
 }
}

