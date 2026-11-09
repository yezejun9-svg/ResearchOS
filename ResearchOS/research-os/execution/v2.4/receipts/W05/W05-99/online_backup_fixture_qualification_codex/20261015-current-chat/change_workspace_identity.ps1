$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath('D:/作品集/ResearchOS/research-os/.local/online-backup-fixture-qualification-20261015-tmp')
$caseRoot = [IO.Path]::GetFullPath((Join-Path $taskRoot 'fixture/Q02'))
$from = [IO.Path]::GetFullPath((Join-Path $caseRoot 'chosen-workspace'))
$to = [IO.Path]::GetFullPath((Join-Path $caseRoot 'chosen-workspace-original'))
foreach ($p in @($caseRoot,$from,$to)) {
    if (-not $p.StartsWith($taskRoot + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'path outside owned task root' }
}
if (-not (Test-Path -LiteralPath $from -PathType Container) -or (Test-Path -LiteralPath $to)) { throw 'unexpected fixture state' }
Move-Item -LiteralPath $from -Destination $to
New-Item -ItemType Directory -Path (Join-Path $from 'src') | Out-Null
[IO.File]::WriteAllText((Join-Path $from 'src/main.go'),"package fixture`n",[Text.UTF8Encoding]::new($false))
Write-Output 'CHANGED_WORKSPACE_ROOT_IDENTITY_WITH_SAME_VISIBLE_FILE_BYTES'
