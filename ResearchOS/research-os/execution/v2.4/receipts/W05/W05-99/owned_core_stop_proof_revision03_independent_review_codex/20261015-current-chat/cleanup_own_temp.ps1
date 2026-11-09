$ErrorActionPreference = 'Stop'
$expected = [IO.Path]::GetFullPath('D:\作品集\ResearchOS\research-os\.local\owned-core-stop-r3-independent-review-20261015')
$workspace = [IO.Path]::GetFullPath('D:\作品集\ResearchOS\research-os\.local')
$resolved = (Resolve-Path -LiteralPath $expected).Path
if ($resolved -ne $expected -or -not $resolved.StartsWith($workspace + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Own temporary root boundary mismatch' }
Write-Output ('verified_own_temp=' + $resolved)
Remove-Item -LiteralPath $resolved -Recurse -Force
if (Test-Path -LiteralPath $resolved) { throw 'Own temporary cleanup incomplete' }
Write-Output 'own_temp_removed; evidence retained'
