$ErrorActionPreference = 'Stop'
$utf8 = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $utf8
$outDir = $PSScriptRoot
$paths = @('D:/作品集/ResearchOS/AGENTS.md','D:/作品集/ResearchOS/research-os/AGENTS.md','D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp521/qualification-failure-B-r2-independent-review-scope.json')
$record = [ordered]@{commandId='B-r2-review-001'; utc=[DateTime]::UtcNow.ToString('o'); environment=[ordered]@{PSVersion=$PSVersionTable.PSVersion.ToString(); cwd=(Get-Location).Path}; reads=@(); exitCode=0}
$stdout = [System.Collections.Generic.List[string]]::new()
try { foreach ($p in $paths) { if (Test-Path -LiteralPath $p) { $s=[IO.File]::ReadAllText($p,$utf8); $record.reads += [ordered]@{path=$p; sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}; $stdout.Add("FILE $p`n$s") } else {$record.reads += [ordered]@{path=$p; missing=$true}; $stdout.Add("MISSING $p")} } } catch { $record.exitCode=1; [IO.File]::WriteAllText((Join-Path $outDir 'B-r2-review-001.stderr.txt'),($_ | Out-String),$utf8) }
[IO.File]::WriteAllText((Join-Path $outDir 'B-r2-review-001.stdout.txt'),($stdout -join "`n"),$utf8)
if (!(Test-Path -LiteralPath (Join-Path $outDir 'B-r2-review-001.stderr.txt'))) {[IO.File]::WriteAllText((Join-Path $outDir 'B-r2-review-001.stderr.txt'),'',$utf8)}
[IO.File]::WriteAllText((Join-Path $outDir 'B-r2-review-001.command.json'),($record | ConvertTo-Json -Depth 20),$utf8)
[Console]::WriteLine($stdout -join "`n")
exit $record.exitCode
