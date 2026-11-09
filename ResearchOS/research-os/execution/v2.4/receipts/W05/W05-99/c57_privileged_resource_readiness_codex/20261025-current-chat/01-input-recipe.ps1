$ErrorActionPreference='Stop'
$root='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\resume_cp528_codex\20261025-current-chat\continuation-cp550'
foreach($name in @('next-C57-readiness-boundaries.json','C57-limited-source-adopted.json')) {
 $path=Join-Path $root $name
 "FILE=$path"
 "SHA256=$((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant())"
 Get-Content -LiteralPath $path -Encoding UTF8
}