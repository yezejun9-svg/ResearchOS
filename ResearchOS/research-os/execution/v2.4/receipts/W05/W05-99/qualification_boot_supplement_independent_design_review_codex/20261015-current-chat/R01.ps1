$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$scopePath = 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp519/boot-supplement-independent-design-review-scope.json'
if (-not (Test-Path -LiteralPath $scopePath -PathType Leaf)) { throw 'Scope missing' }
$scopeHash = (Get-FileHash -LiteralPath $scopePath -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Output ('SCOPE_SHA256=' + $scopeHash)
if ($scopeHash -ne 'e647ec31630ef5cb542f8f1ea1b4dbc0de2e1c9deb4820bb413efd2b904ce900') { throw 'Scope hash mismatch' }
foreach ($path in @('D:/作品集/ResearchOS/AGENTS.md', 'D:/作品集/ResearchOS/research-os/AGENTS.md', $scopePath)) {
    Write-Output ('FILE=' + $path)
    if (Test-Path -LiteralPath $path -PathType Leaf) { Get-Content -LiteralPath $path -Encoding UTF8 } else { Write-Output 'MISSING' }
}
