$root='D:/作品集/ResearchOS/research-os'
$packages=@('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-profile-c8b7adab-20261014','C:/Users/yqyyds/.codex/researchos-resource-cache/normal-verifier-replacement-4f4023-20261015')
$publicTargets=New-Object System.Collections.Generic.List[string]
foreach($package in $packages){
 foreach($rel in @('apps/desktop/package.json','apps/desktop/main/main.js','apps/desktop/main/lib/desktop-management.js','apps/desktop/resources/control/researchos-control.exe','apps/desktop/resources/control/runtime-verifier.exe','apps/desktop/resources/control/runtime/node.exe','apps/desktop/resources/control/runtime/mu-worker.mjs','apps/desktop/resources/client-wire/researchos-client-wire-validator.exe')){$publicTargets.Add([IO.Path]::GetFullPath((Join-Path $package $rel)))}
}
foreach($rel in @('apps/desktop/node_modules/electron/dist/electron.exe','apps/desktop/main/main.js','apps/desktop/main/lib/desktop-management.js','apps/control/main.go','ops/backup/main.go','ops/supervisor/release_host/main.go')){$publicTargets.Add([IO.Path]::GetFullPath((Join-Path $root $rel)))}
$data=Join-Path $root '.local/live/current-chat-normal-desktop-first-use-20261012/data'
$metadataOnly=@([IO.Path]::GetFullPath($data),[IO.Path]::GetFullPath((Join-Path $data 'researchos.sqlite')),[IO.Path]::GetFullPath((Join-Path $data 'coordinator.lock')))
$allPaths=New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
foreach($target in (@($publicTargets.ToArray())+$metadataOnly)){
 [void]$allPaths.Add($target)
 $dir=[IO.Path]::GetDirectoryName($target)
 while($dir){[void]$allPaths.Add($dir);$parent=[IO.Path]::GetDirectoryName($dir.TrimEnd('\','/'));if($parent -eq $dir){break};$dir=$parent}
}
$records=New-Object System.Collections.Generic.List[object]
foreach($path in @($allPaths|Sort-Object)){
 $record=[ordered]@{path=$path;kind=if($path -in $publicTargets){'PUBLIC_PRODUCT_TARGET'}elseif($path -in $metadataOnly){'ACTUAL_DATA_METADATA_ONLY'}else{'EXACT_ANCESTOR'};status='UNKNOWN';is_retained_native_identity=$false;is_fence_proof=$false}
 try{
  $item=Get-Item -LiteralPath $path -Force -ErrorAction Stop
  $record.status='READ'
  $record.directory=$item.PSIsContainer
  $record.attributes=$item.Attributes.ToString()
  $record.reparse=([bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint))
  $record.link_type=$item.LinkType
  $record.link_targets=@($item.Target)
  $record.bytes=if($item.PSIsContainer){$null}else{$item.Length}
  if($path -in $publicTargets -and -not $item.PSIsContainer -and -not $record.reparse){$record.sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower()}else{$record.sha256=$null;$record.hash_note='Not hashed: actual data metadata only, ancestor directory, or reparse guard'}
  try{$acl=Get-Acl -LiteralPath $path -ErrorAction Stop;$record.acl=@{status='READ';owner=$acl.Owner;sddl=$acl.Sddl;protected=$acl.AreAccessRulesProtected;canonical=$acl.AreAccessRulesCanonical;aces=@($acl.Access|ForEach-Object {@{identity=$_.IdentityReference.Value;rights=$_.FileSystemRights.ToString();access_type=$_.AccessControlType.ToString();inherited=$_.IsInherited;inheritance_flags=$_.InheritanceFlags.ToString();propagation_flags=$_.PropagationFlags.ToString()}})}}catch{$record.acl=@{status='UNKNOWN_READ_ERROR';error=$_.Exception.Message}}
  $idRaw=@(& "$env:SystemRoot/System32/fsutil.exe" file queryfileid $path 2>&1);$idExit=$LASTEXITCODE
  $record.fsutil_file_id=@{argv=@('file','queryfileid',$path);native_exit_code=$idExit;raw=($idRaw|Out-String -Width 300);class='AUXILIARY_SEPARATE_OPEN_NOT_SAME_HANDLE128BIT_ATTESTATION'}
  if(-not $item.PSIsContainer -and $path -in $publicTargets){
   $linkRaw=@(& "$env:SystemRoot/System32/fsutil.exe" hardlink list $path 2>&1);$linkExit=$LASTEXITCODE
   $record.fsutil_hardlinks=@{argv=@('hardlink','list',$path);native_exit_code=$linkExit;raw=($linkRaw|Out-String -Width 300);class='AUXILIARY_PATH_LIST_NOT_STABLE_HELD_INVENTORY'}
  }
 }catch{if($_.Exception -is [Management.Automation.ItemNotFoundException]){$record.status='ABSENT'}else{$record.status='UNKNOWN_READ_ERROR'};$record.error=$_.Exception.Message}
 $records.Add($record)
}
$volumes=@()
foreach($drive in @('C:','D:')){
 try{$v=Get-CimInstance Win32_LogicalDisk -Filter ("DeviceID='"+$drive+"'") -ErrorAction Stop|Select-Object DeviceID,FileSystem,VolumeSerialNumber,DriveType;$volumes+=@{status='READ';drive=$drive;value=$v;class='AUXILIARY_CIM_VOLUME_METADATA_NOT_NATIVE_BINDING'}}catch{$volumes+=@{status='UNKNOWN';drive=$drive;error=$_.Exception.Message}}
}
$out=@{schema='researchos.CP518.file-ancestor-metadata.v1';records=$records.ToArray();volume_metadata=$volumes;no_DB_content_read=$true;native_same_handle_tool='NOT_AVAILABLE_AS_ACCEPTED_INPUT';actual_authority=$false;formal_increment=0}
$out|ConvertTo-Json -Depth 20|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'file-ancestor-metadata.json') -Encoding utf8
$out|ConvertTo-Json -Depth 20

