[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$t='D:\作品集\ResearchOS\research-os\.local\online-backup-independent-review-20261015-tmp'
$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
icacls $t /inheritance:r /grant:r ("*{0}:(OI)(CI)F" -f $sid)
exit $LASTEXITCODE