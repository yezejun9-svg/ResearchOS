$ErrorActionPreference='Stop'
$evidence=Split-Path -Parent $MyInvocation.MyCommand.Path
$plan='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\verifier_replacement_actual_root_codex\20261015-current-chat\replacement-plan-01.json'
$p=Get-Content -Raw -LiteralPath $plan|ConvertFrom-Json
$currentSid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$rows=@(foreach($path in @($plan,$p.manifest,$p.installation.executable)){
 $a=Get-Acl -LiteralPath $path
 $owner=$a.GetOwner([System.Security.Principal.SecurityIdentifier]).Value
 $rules=@($a.GetAccessRules($true,$true,[System.Security.Principal.SecurityIdentifier]))
 if($owner -ne $currentSid -or -not $a.AreAccessRulesProtected -or $rules.Count -ne 1){throw 'Unexpected owner or protected ACE count'}
 $r=$rules[0]
 if($r.IdentityReference.Value -ne $currentSid -or $r.AccessControlType -ne 'Allow' -or [int]$r.FileSystemRights -ne 0x001f01ff -or $r.IsInherited -or [int]$r.InheritanceFlags -ne 0 -or [int]$r.PropagationFlags -ne 0){throw 'Strict private ACE mismatch'}
 [pscustomobject]@{path=$path;current_sid=$currentSid;owner=$owner;protected=$a.AreAccessRulesProtected;ace_count=$rules.Count;type=$r.AccessControlType.ToString();mask=[int]$r.FileSystemRights;inherited=$r.IsInherited;inheritance_flags=[int]$r.InheritanceFlags;propagation_flags=[int]$r.PropagationFlags;sddl=$a.Sddl}
})
$out=Join-Path $evidence '02-preflight-plan-acl.json'
if(Test-Path -LiteralPath $out){throw 'Evidence exists'}
[System.IO.File]::WriteAllText($out,([pscustomobject]@{at=[DateTime]::UtcNow.ToString('o');rows=$rows;read_only=$true;result='STRICT_CURRENT_SID_SINGLE_PROTECTED_ACE_MATCH'}|ConvertTo-Json -Depth 5),[System.Text.UTF8Encoding]::new($false))
Get-FileHash -LiteralPath $out -Algorithm SHA256|Select-Object Path,Hash
