$ErrorActionPreference='Stop'
$src='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_recovery_boundary_boot6_codex\20261025-current-chat'
foreach($name in @('final-v12-additive-seal.json','final-v12-six-source-manifest.json','final-v12-six-source.patch')) {
 $path=Join-Path $src $name
 "FILE=$path"
 "SHA256=$((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant())"
 Get-Content -LiteralPath $path -Encoding UTF8
}