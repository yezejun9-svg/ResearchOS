$paths = @(
  'C:\', 'C:\Windows', 'C:\Users', 'C:\Users\yqyyds',
  'D:\', 'D:\作品集', 'D:\作品集\ResearchOS',
  'D:\作品集\ResearchOS\research-os',
  'D:\作品集\ResearchOS\research-os\.local',
  'D:\作品集\ResearchOS\research-os\.local\worktrees',
  'D:\作品集\ResearchOS\research-os\.local\worktrees\owned-core-stop-authority-r4-20261015'
)
foreach ($path in $paths) {
  try {
    $acl = Get-Acl -LiteralPath $path -ErrorAction Stop
    [pscustomobject]@{
      path = $path
      owner = $acl.Owner
      sddl = $acl.Sddl
    } | ConvertTo-Json -Compress
  } catch {
    [pscustomobject]@{ path = $path; error = $_.Exception.Message } | ConvertTo-Json -Compress
  }
}
