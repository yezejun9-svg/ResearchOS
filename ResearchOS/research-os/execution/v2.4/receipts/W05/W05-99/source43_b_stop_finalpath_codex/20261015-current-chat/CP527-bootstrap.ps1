$ErrorActionPreference = 'Stop'
$own = 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\source43_b_stop_finalpath_codex\20261015-current-chat'
$null = [System.IO.Directory]::CreateDirectory($own)
$targets = @(
  'C:\Users\yqyyds\AGENTS.md',
  'D:\作品集\ResearchOS\AGENTS.md',
  'D:\作品集\ResearchOS\research-os\AGENTS.md',
  'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\resume_cp398_codex\20261015-current-chat\continuation-cp527\source43-B-STOP-finalpath-source-scope.json'
)
$invocation = [ordered]@{
  command = 'powershell -File CP527-bootstrap.ps1'
  cwd = (Get-Location).Path
  own = $own
  targets = $targets
  start_utc = [DateTime]::UtcNow.ToString('o')
}
$invocation | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $own 'CP527-bootstrap-invocation.json') -Encoding utf8
$raw = Join-Path $own 'CP527-bootstrap-raw.txt'
$writer = [System.IO.StreamWriter]::new($raw, $false, [System.Text.UTF8Encoding]::new($false))
try {
  foreach ($path in $targets) {
    $writer.WriteLine("=== $path ===")
    if ([System.IO.File]::Exists($path)) {
      $bytes = [System.IO.File]::ReadAllBytes($path)
      $writer.WriteLine("bytes=$($bytes.Length) sha256=$([Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant())")
      $writer.WriteLine([System.Text.Encoding]::UTF8.GetString($bytes))
    } else {
      $writer.WriteLine('MISSING')
    }
    $writer.Flush()
  }
  @{exit=0; end_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $own 'CP527-bootstrap-exit.json') -Encoding utf8
} catch {
  $writer.WriteLine("ERROR: $($_.Exception.ToString())")
  $writer.Flush()
  @{exit=1; end_utc=[DateTime]::UtcNow.ToString('o'); error=$_.Exception.ToString()} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $own 'CP527-bootstrap-exit.json') -Encoding utf8
  throw
} finally {
  $writer.Dispose()
}
Get-Content -LiteralPath $raw -Raw
