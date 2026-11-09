$ErrorActionPreference = 'Stop'
$manifest = 'C:/Users/yqyyds/.codex/researchos-resource-cache/normal-readlane-combined-91218bdd-20261012/apps/desktop/resources/control/runtime-verifier-installation.json'
$receipt = 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/approved_readlane_combined_desktop_build_codex/20261012-current-chat'
$sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
$before = Get-Acl -LiteralPath $manifest
$acl = New-Object System.Security.AccessControl.FileSecurity
$acl.SetOwner($sid)
$acl.SetAccessRuleProtection($true, $false)
$acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($sid, [System.Security.AccessControl.FileSystemRights]::FullControl, [System.Security.AccessControl.AccessControlType]::Allow)))
Set-Acl -LiteralPath $manifest -AclObject $acl
$after = Get-Acl -LiteralPath $manifest
$rules = @($after.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier]))
if (-not $after.AreAccessRulesProtected -or $rules.Count -ne 1 -or
    $rules[0].IdentityReference.Value -ne $sid.Value -or
    $rules[0].AccessControlType -ne [System.Security.AccessControl.AccessControlType]::Allow -or
    ($rules[0].FileSystemRights -band [System.Security.AccessControl.FileSystemRights]::FullControl) -ne [System.Security.AccessControl.FileSystemRights]::FullControl) {
  throw 'MANIFEST_ACL_MISMATCH'
}
$row = [ordered]@{
  schema = 'researchos.cp444-readlane-manifest-acl.v1'
  path = (Resolve-Path -LiteralPath $manifest).Path
  current_user_sid = $sid.Value
  protected = $after.AreAccessRulesProtected
  rule_count = $rules.Count
  sddl = $after.Sddl
  before_sddl = $before.Sddl
  file_sha256 = (Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToLowerInvariant()
  activation = 'NOT_STARTED'
}
$row | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $receipt 'manifest-acl.json') -Encoding utf8NoBOM
$row | Select-Object schema,path,current_user_sid,protected,rule_count,file_sha256 | ConvertTo-Json -Compress
