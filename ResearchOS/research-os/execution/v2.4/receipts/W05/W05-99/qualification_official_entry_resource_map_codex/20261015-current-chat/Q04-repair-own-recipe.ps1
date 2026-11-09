$source=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'Q04-filtered-registrations.ps1')
$corrected=@($source[0..21])+@('    }')+@($source[22..($source.Count-1)])
$target=Join-Path $PSScriptRoot 'Q04-filtered-registrations-r1.ps1'
[IO.File]::WriteAllLines($target,$corrected)
'Correction: close registry-key else block before records.Add; failed original Q04 recipe/raw preserved.'
& (Join-Path $PSScriptRoot 'invoke-readonly.ps1') -Group Q04R1 -RecipeFile $target

