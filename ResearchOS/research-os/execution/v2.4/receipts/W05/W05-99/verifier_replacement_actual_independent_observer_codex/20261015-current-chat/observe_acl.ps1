param([Parameter(Mandatory=$true)][string]$Label)
$ErrorActionPreference='Stop'
$dataRoot='D:\作品集\ResearchOS\research-os\.local\live\current-chat-normal-desktop-first-use-20261012\data'
$evidence=Split-Path -Parent $MyInvocation.MyCommand.Path
$currentSid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$paths=@($dataRoot,(Join-Path $dataRoot 'host'),(Join-Path $dataRoot 'researchos.sqlite'),(Join-Path $dataRoot 'coordinator.lock'),(Join-Path $dataRoot 'host\host_state.json'),(Join-Path $dataRoot 'host\runtime-verifier-installation.json'))
$journal=Join-Path $dataRoot 'host\runtime-verifier-replacements'
if(Test-Path -LiteralPath $journal){$paths += $journal; $paths += @(Get-ChildItem -LiteralPath $journal -Recurse -Force | ForEach-Object {$_.FullName})}
$rows=@(foreach($path in $paths){
 $acl=Get-Acl -LiteralPath $path
 $owner=$acl.GetOwner([System.Security.Principal.SecurityIdentifier]).Value
 $rules=@($acl.GetAccessRules($true,$true,[System.Security.Principal.SecurityIdentifier]) | ForEach-Object {[pscustomobject]@{sid=$_.IdentityReference.Value;type=$_.AccessControlType.ToString();mask=[int]$_.FileSystemRights;inherited=$_.IsInherited;inheritance_flags=[int]$_.InheritanceFlags;propagation_flags=[int]$_.PropagationFlags}})
 [pscustomobject]@{path=$path;owner=$owner;owner_is_current=($owner -eq $currentSid);protected=$acl.AreAccessRulesProtected;sddl=$acl.Sddl;rules=$rules}
})
$result=[pscustomobject]@{at=[DateTime]::UtcNow.ToString('o');current_sid=$currentSid;rows=$rows;native_security_descriptor_read_only=$true;acl_writes=$false;formal_increment=0}
$target=Join-Path $evidence ($Label+'-acl.json')
if(Test-Path -LiteralPath $target){throw 'Evidence already exists'}
[System.IO.File]::WriteAllText($target,($result|ConvertTo-Json -Depth 6),[System.Text.UTF8Encoding]::new($false))
Get-FileHash -LiteralPath $target -Algorithm SHA256 | Select-Object Path,Hash
