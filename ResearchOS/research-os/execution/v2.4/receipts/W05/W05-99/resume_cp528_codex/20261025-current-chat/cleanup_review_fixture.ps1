$ErrorActionPreference = 'Stop'
$fixtureRoot = 'C:\Users\yqyyds\.codex\researchos-fixture-cache\qualification-maintenance-c57-independent-review-20261025\native-c'
$fixturePath = 'C:\Users\yqyyds\.codex\researchos-fixture-cache\qualification-maintenance-c57-independent-review-20261025\native-c\.researchos-configuration-template-2985372397'
$resolvedRoot = (Resolve-Path -LiteralPath $fixtureRoot).Path
$resolvedFixture = (Resolve-Path -LiteralPath $fixturePath).Path
if (-not [string]::Equals($resolvedFixture, $fixturePath, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unexpected resolved fixture path' }
if (-not [string]::Equals([IO.Path]::GetDirectoryName($resolvedFixture), $resolvedRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Fixture escaped owned native root' }
$directory = Get-Item -LiteralPath $resolvedFixture -Force
if (($directory.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Refuse reparse fixture' }
$children = @(Get-ChildItem -LiteralPath $resolvedFixture -Force)
if ($children.Count -ne 1 -or $children[0].Name -ne 'schema.sqlite' -or $children[0].PSIsContainer) { throw 'Unexpected fixture contents' }
if (($children[0].Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Refuse reparse child' }
$schemaPath = $children[0].FullName
[pscustomobject]@{ action='remove_completed_owned_test_fixture'; path=$resolvedFixture; file=$schemaPath; bytes=$children[0].Length; sha256=(Get-FileHash -LiteralPath $schemaPath -Algorithm SHA256).Hash.ToLowerInvariant(); recursive=$false } | ConvertTo-Json -Compress
Remove-Item -LiteralPath $schemaPath -Force -ErrorAction Stop
if (@(Get-ChildItem -LiteralPath $resolvedFixture -Force).Count -ne 0) { throw 'Directory not empty after exact file cleanup' }
Remove-Item -LiteralPath $resolvedFixture -Force -ErrorAction Stop
if (Test-Path -LiteralPath $resolvedFixture) { throw 'Fixture cleanup did not complete' }
Write-Output 'OWNED_SINGLE_SCHEMA_FIXTURE_CLEANED; historical denied cleanup targets untouched'
