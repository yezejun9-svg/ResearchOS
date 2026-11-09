$ErrorActionPreference = 'Stop'
$manifest = 'C:/Users/yqyyds/.codex/researchos-resource-cache/normal-status-combined-5ddc0abb-20261014/apps/desktop/resources/control/runtime-verifier-installation.json'
$receipt = 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_status_desktop_build_codex/20261014-current-chat'
$out = Join-Path $receipt 'acl-readback.json'
if (Test-Path -LiteralPath $out) { throw 'ACL_READBACK_ALREADY_EXISTS' }
$acl = Get-Acl -LiteralPath $manifest
$sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$rules = @($acl.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier]))
if (-not $acl.AreAccessRulesProtected -or $rules.Count -ne 1 -or
    $rules[0].IdentityReference.Value -ne $sid -or
    $rules[0].AccessControlType -ne [System.Security.AccessControl.AccessControlType]::Allow -or
    ($rules[0].FileSystemRights -band [System.Security.AccessControl.FileSystemRights]::FullControl) -ne [System.Security.AccessControl.FileSystemRights]::FullControl) {
  throw 'LIVE_ACL_READBACK_MISMATCH'
}
$row = [pscustomobject]@{
  schema = 'researchos.cp458-status-live-acl-readback.v1'
  manifest = (Resolve-Path -LiteralPath $manifest).Path
  current_user_sid = $sid
  protected = $acl.AreAccessRulesProtected
  rule_count = $rules.Count
  single_ace_identity = $rules[0].IdentityReference.Value
  single_ace_rights = $rules[0].FileSystemRights.ToString()
  manifest_sha256 = (Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToLowerInvariant()
  status = 'LIVE_READBACK_PASS'
}
$row | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $out -Encoding utf8NoBOM
$row | ConvertTo-Json -Compress -Depth 5
