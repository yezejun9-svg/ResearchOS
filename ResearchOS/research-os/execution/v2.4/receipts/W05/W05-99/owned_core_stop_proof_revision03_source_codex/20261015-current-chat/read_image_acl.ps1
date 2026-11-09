$paths = @(
  'C:\', 'C:\Users', 'C:\Users\yqyyds',
  'C:\Users\yqyyds\AppData\Local\Python\pythoncore-3.14-64\python.exe',
  'D:\'
)
foreach ($item in $paths) {
  if (Test-Path -LiteralPath $item) {
    $acl = Get-Acl -LiteralPath $item
    Write-Output ($item + ' OWNER ' + $acl.Owner)
    $acl.Access | Where-Object { $_.IdentityReference -match 'Everyone|Users|Authenticated' } | Select-Object -First 5 IdentityReference, FileSystemRights, AccessControlType | Format-Table -HideTableHeaders
  }
}
