$ErrorActionPreference='Stop'
$expected='D:\作品集\ResearchOS\research-os\.local\owned-core-stop-r2-independent-review-20261015'
$item=Get-Item -LiteralPath $expected
$resolved=(Resolve-Path -LiteralPath $expected).Path
if($resolved -cne $expected -or -not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Task-owned temporary root identity mismatch' }
[pscustomobject]@{verified_absolute_target=$resolved;recursive=$true;purpose='Remove only this completed review task temporary Go cache/work directories'} | ConvertTo-Json
Remove-Item -LiteralPath $resolved -Recurse -Force
if(Test-Path -LiteralPath $expected) { throw 'Task temporary root remains' }
Write-Output 'Task-owned temporary root removed; evidence and source worktree retained.'
