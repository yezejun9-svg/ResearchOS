$ErrorActionPreference = 'Stop'
$manifest = 'C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-profile-c8b7adab-20261014/apps/desktop/resources/control/runtime-verifier-installation.json'
$receipt = 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/coding_profile_desktop_build_codex/20261014-current-chat'
$out = Join-Path $receipt 'manifest-acl.json'
if (Test-Path -LiteralPath $out) { throw 'MANIFEST_ACL_ALREADY_EXISTS' }
$sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
$before = Get-Acl -LiteralPath $manifest
$priorRules = @($before.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier]))
$alreadyProtected = $before.AreAccessRulesProtected -and $priorRules.Count -eq 1 -and
  $before.GetOwner([System.Security.Principal.SecurityIdentifier]).Value -eq $sid.Value -and
  $priorRules[0].IdentityReference.Value -eq $sid.Value -and
  $priorRules[0].AccessControlType -eq [System.Security.AccessControl.AccessControlType]::Allow -and
  ($priorRules[0].FileSystemRights -band [System.Security.AccessControl.FileSystemRights]::FullControl) -eq
    [System.Security.AccessControl.FileSystemRights]::FullControl
if (-not $alreadyProtected) {
  $acl = New-Object System.Security.AccessControl.FileSecurity
  $acl.SetOwner($sid)
  $acl.SetAccessRuleProtection($true, $false)
  $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($sid,
    [System.Security.AccessControl.FileSystemRights]::FullControl,
    [System.Security.AccessControl.AccessControlType]::Allow)))
  Set-Acl -LiteralPath $manifest -AclObject $acl
}
$after = Get-Acl -LiteralPath $manifest
$ownerSid = $after.GetOwner([System.Security.Principal.SecurityIdentifier]).Value
$rules = @($after.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier]))
if (-not $after.AreAccessRulesProtected -or $rules.Count -ne 1 -or
    $ownerSid -ne $sid.Value -or $rules[0].IdentityReference.Value -ne $sid.Value -or
    $rules[0].AccessControlType -ne [System.Security.AccessControl.AccessControlType]::Allow -or
    ($rules[0].FileSystemRights -band [System.Security.AccessControl.FileSystemRights]::FullControl) -ne
      [System.Security.AccessControl.FileSystemRights]::FullControl) { throw 'MANIFEST_ACL_MISMATCH' }
$row = [ordered]@{
  schema = 'researchos.cp477-profile-result-manifest-acl/1'
  manifest = (Resolve-Path -LiteralPath $manifest).Path
  current_user_sid = $sid.Value
  owner_sid = $ownerSid
  protected = $after.AreAccessRulesProtected
  rule_count = $rules.Count
  single_ace_identity = $rules[0].IdentityReference.Value
  single_ace_rights = $rules[0].FileSystemRights.ToString()
  before_sddl = $before.Sddl
  sddl = $after.Sddl
  manifest_sha256 = (Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToLowerInvariant()
  activation = 'NOT_STARTED'
}
$row | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $out -Encoding utf8NoBOM
$row | Select-Object schema,current_user_sid,owner_sid,protected,rule_count,manifest_sha256 |
  ConvertTo-Json -Compress
