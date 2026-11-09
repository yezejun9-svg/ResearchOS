$ErrorActionPreference = 'Stop'
$base = 'C:/Users/yqyyds/.codex/researchos-resource-cache/normal-verifier-replacement-4f4023-20261015/apps/desktop/resources/control'
$receipt = 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/verifier_replacement_package_codex/20261015-current-chat'
$sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
$rows = @()
foreach ($name in @('runtime-verifier.exe', 'runtime-verifier-installation.json')) {
  $path = Join-Path $base $name
  $before = Get-Acl -LiteralPath $path
  $acl = New-Object System.Security.AccessControl.FileSecurity
  $acl.SetOwner($sid)
  $acl.SetAccessRuleProtection($true, $false)
  $acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($sid,
    [System.Security.AccessControl.FileSystemRights]::FullControl,
    [System.Security.AccessControl.AccessControlType]::Allow)))
  Set-Acl -LiteralPath $path -AclObject $acl
  $after = Get-Acl -LiteralPath $path
  $rules = @($after.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier]))
  $owner = $after.GetOwner([System.Security.Principal.SecurityIdentifier]).Value
  if (-not $after.AreAccessRulesProtected -or $rules.Count -ne 1 -or
      $owner -ne $sid.Value -or $rules[0].IdentityReference.Value -ne $sid.Value -or
      $rules[0].AccessControlType -ne [System.Security.AccessControl.AccessControlType]::Allow -or
      ($rules[0].FileSystemRights -band [System.Security.AccessControl.FileSystemRights]::FullControl) -ne
        [System.Security.AccessControl.FileSystemRights]::FullControl) { throw "ACL_MISMATCH: $name" }
  $rows += [pscustomobject]@{
    file = (Resolve-Path -LiteralPath $path).Path
    before_sddl = $before.Sddl
    after_sddl = $after.Sddl
    current_sid = $sid.Value
    owner_sid = $owner
    protected = $after.AreAccessRulesProtected
    ace_count = $rules.Count
    ace_sid = $rules[0].IdentityReference.Value
    ace_rights = $rules[0].FileSystemRights.ToString()
    sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
  }
}
$out = Join-Path $receipt 'acl-set-readback.json'
if (Test-Path -LiteralPath $out) { throw 'ACL_RECEIPT_EXISTS' }
[System.IO.File]::WriteAllText($out, (($rows | ConvertTo-Json -Depth 5) + "`n"), (New-Object System.Text.UTF8Encoding($false)))
$rows | Select-Object file,owner_sid,protected,ace_count,sha256 | ConvertTo-Json -Compress
