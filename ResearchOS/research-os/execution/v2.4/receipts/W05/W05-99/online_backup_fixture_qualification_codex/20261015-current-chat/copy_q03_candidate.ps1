$ErrorActionPreference = 'Stop'
$source = 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/model_stream_executor_codex/test-f4a65b87734641c8a39d7060dd8b24fb/actual-fixtures/TestCLIModelStreamInterruptedPrefix/fixture.sqlite'
$task = [IO.Path]::GetFullPath('D:/作品集/ResearchOS/research-os/.local/online-backup-fixture-qualification-20261015-tmp')
$destination = [IO.Path]::GetFullPath((Join-Path $task 'fixture/Q03/source-data/researchos.sqlite'))
if (-not $destination.StartsWith($task + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'destination outside task root' }
if (Test-Path -LiteralPath $destination) { throw 'Q03 destination exists' }
$item = Get-Item -LiteralPath $source -ErrorAction Stop
if (-not $item.Length -or $item.Extension -ne '.sqlite') { throw 'candidate is not a regular nonempty SQLite file' }
$sha = (Get-FileHash -Algorithm SHA256 -LiteralPath $source).Hash.ToLowerInvariant()
New-Item -ItemType Directory -Path (Split-Path -Parent $destination) | Out-Null
Copy-Item -LiteralPath $source -Destination $destination
$copied = (Get-FileHash -Algorithm SHA256 -LiteralPath $destination).Hash.ToLowerInvariant()
if ($copied -ne $sha) { throw 'candidate copy hash mismatch' }
[ordered]@{source=$item.FullName;bytes=$item.Length;source_sha256=$sha;copy=$destination;copy_sha256=$copied;last_write_utc=$item.LastWriteTimeUtc.ToString('o')} | ConvertTo-Json -Compress
