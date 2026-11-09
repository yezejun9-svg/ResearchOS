$a='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\owned_core_stop_anchor_revision02_source_codex\20261015-current-chat'
$f=Get-Content "$a\candidate-f5db4a96-final\failure-ledger.json" -Raw | ConvertFrom-Json
$f | ConvertTo-Json -Depth 2
$i=Get-Content "$a\candidate-f5db4a96-final\command-capture-index.json" -Raw | ConvertFrom-Json
$i | Select-Object -First 1 | ConvertTo-Json -Depth 3
