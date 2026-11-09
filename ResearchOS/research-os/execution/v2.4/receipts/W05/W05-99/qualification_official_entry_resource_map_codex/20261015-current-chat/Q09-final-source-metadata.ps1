$root='D:/作品集/ResearchOS/research-os'
'COMMAND_REGISTRY_STARTUP_LINES'
$p=Join-Path $root 'execution/commands.json'
'FILE '+$p+' SHA256='+(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower()
& rg -n -C 3 'desktop|apps/control|apps/cli|ops/runtime|ops/backup|release_host|dev|start' $p
'NATIVE_RG_EXIT='+$LASTEXITCODE
'INSTALL_DOC_FILENAMES'
if(Test-Path -LiteralPath (Join-Path $root 'docs/installation')){Get-ChildItem -LiteralPath (Join-Path $root 'docs/installation') -File|Select-Object -ExpandProperty FullName}
'SERVICE_EXACT_SOURCE_LOCATORS'
& rg -l --fixed-strings 'ResearchOSVerifierCanary' (Join-Path $root 'adapters') (Join-Path $root 'internal') (Join-Path $root 'ops') (Join-Path $root 'docs')
'NATIVE_RG_EXIT='+$LASTEXITCODE
'APP_RESTART_SOURCE_MATCHES'
& rg -n 'RegisterApplicationRestart|setLoginItemSettings|app.relaunch|setAsDefaultProtocolClient' (Join-Path $root 'apps/desktop/main') (Join-Path $root 'apps/control')
'NATIVE_RG_EXIT='+$LASTEXITCODE
'PACKAGE_REHASH'
$locations=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'package-file-locations.json') -Raw|ConvertFrom-Json
$hashes=@()
foreach($f in $locations){$hashes+=@{package_root=$f.package_root;relative_path=$f.relative_path;bytes=(Get-Item -LiteralPath $f.absolute_path).Length;sha256=(Get-FileHash -LiteralPath $f.absolute_path -Algorithm SHA256).Hash.ToLower()}}
$hashes|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'package-member-hashes.json') -Encoding utf8
@{member_count=$hashes.Count;per_package=@($hashes|Group-Object package_root|Select-Object Name,Count);scope='PUBLIC_FILE_BYTES_ONLY_NOT_LOADED_IMAGE_OR_ENTRY_COMPLETENESS'}|ConvertTo-Json -Depth 8
'REGISTERED_SERVICE_EXECUTABLE_METADATA'
$paths=@('C:\ProgramData','C:\ProgramData\ResearchOSVerifierCanary','C:\ProgramData\ResearchOSVerifierCanary\broker.exe')
$records=@()
foreach($path in $paths){
 try{$i=Get-Item -LiteralPath $path -Force -ErrorAction Stop;$a=Get-Acl -LiteralPath $path -ErrorAction Stop;$id=@(& "$env:SystemRoot/System32/fsutil.exe" file queryfileid $path 2>&1);$code=$LASTEXITCODE;$records+=@{path=$path;status='READ';attributes=$i.Attributes.ToString();reparse=[bool]($i.Attributes -band [IO.FileAttributes]::ReparsePoint);bytes=if($i.PSIsContainer){$null}else{$i.Length};sha256=if($i.PSIsContainer){$null}else{(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower()};owner=$a.Owner;sddl=$a.Sddl;fsutil_fileid_raw=($id|Out-String -Width 300);native_exit_code=$code;class='REGISTERED_SERVICE_METADATA_NOT_PRODUCT_RUNTIME_ATTESTATION'}}catch{$records+=@{path=$path;status='UNKNOWN_READ_ERROR';error=$_.Exception.Message}}
}
$records|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'canary-service-file-metadata.json') -Encoding utf8
$records|ConvertTo-Json -Depth 10

