$lines=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'Q04-filtered-registrations.ps1')
for($i=15;$i -lt 45;$i++){'{0}:{1}' -f ($i+1),$lines[$i]}

