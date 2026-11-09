$root='D:/作品集/ResearchOS/research-os'
foreach($rel in @('docs/installation/README.md','docs/installation/user-guide.md')){
 $p=Join-Path $root $rel;'FILE '+$rel+' SHA256='+(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower()
 $lines=Get-Content -LiteralPath $p;for($i=0;$i -lt $lines.Count;$i++){'{0}:{1}' -f ($i+1),$lines[$i]}
}
foreach($rel in @('adapters/protectedstore/broker_windows.go','adapters/protectedstore/config_pipe_windows.go')){
 $p=Join-Path $root $rel;'SOURCE '+$rel+' SHA256='+(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower()
 & rg -n -C 4 'ResearchOSVerifierCanary|func |serviceName|exec.Command|Start|Run\(|OpenSCManager|Dial|Canary|fixture|listen|namedPipe|--service|ImagePath' $p
 'NATIVE_RG_EXIT='+$LASTEXITCODE
}
'CONTROL_DEFAULT_PRODUCT_FILE_EXISTENCE_ONLY'
foreach($rel in @('apps/desktop/resources/control/researchos-control.exe','apps/desktop/resources/control/runtime-verifier.exe','apps/desktop/resources/control/runtime/node.exe','apps/desktop/resources/control/runtime/mu-worker.mjs')){
 $p=Join-Path $root $rel;try{$i=Get-Item -LiteralPath $p -Force -ErrorAction Stop;@{path=$p;status='EXISTS_METADATA_ONLY';bytes=$i.Length;attributes=$i.Attributes.ToString()}|ConvertTo-Json}catch{@{path=$p;status='UNKNOWN_OR_ABSENT';error=$_.Exception.Message}|ConvertTo-Json}
}
'COMPACT_NATIVE_TARGET_TABLE_FROM_OWN_READS'
$m=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'file-ancestor-metadata.json') -Raw|ConvertFrom-Json
$compact=@()
foreach($r in $m.records){
 $sd=[Security.AccessControl.RawSecurityDescriptor]::new($r.acl.sddl)
 $aces=@()
 foreach($ace in $sd.DiscretionaryAcl){
  if($ace.SecurityIdentifier.Value -in @('S-1-1-0','S-1-5-11','S-1-5-32-545','S-1-5-32-544','S-1-5-18','S-1-5-21-2314176124-1781180693-2759285857-1001')){
   $aces+=@{sid=$ace.SecurityIdentifier.Value;qualifier=$ace.AceQualifier.ToString();flags=$ace.AceFlags.ToString();mask=('0x{0:x8}' -f $ace.AccessMask)}
  }
 }
 $compact+=@{path=$r.path;kind=$r.kind;owner=$r.acl.owner;canonical=$r.acl.canonical;ace_count=$sd.DiscretionaryAcl.Count;relevant_aces=$aces;sha256=$r.sha256;fsutil_file_id=$r.fsutil_file_id.raw;fileid_exit=$r.fsutil_file_id.native_exit_code;reparse=$r.reparse}
}
$compact|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'file-ancestor-compact.json') -Encoding utf8
@{rows=$compact.Count;all_fileid_aux_success=@($compact|Where-Object fileid_exit -ne 0).Count -eq 0;original_full_descriptors='file-ancestor-metadata.json';interpretation='Filtered ACE summary is not full effective AccessCheck or authorization'}|ConvertTo-Json

