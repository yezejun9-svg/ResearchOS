[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$ErrorActionPreference='Stop'
Get-Content 'D:\作品集\ResearchOS\research-os\AGENTS.md' -Raw -Encoding utf8
$s='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\resume_cp398_codex\20261015-current-chat\continuation-cp524\original-online-backup-readonly-resource-scope.json'
$h=(Get-FileHash -LiteralPath $s -Algorithm SHA256).Hash.ToLowerInvariant()
if($h -ne '56387a95a4158cbc4c83f7e350c2563b4b93c202acf4d555a29956d947cc366d'){throw 'scope hash mismatch'}
Write-Output "SCOPE_SHA256=$h"
Get-Content -LiteralPath $s -Raw -Encoding utf8
exit 0