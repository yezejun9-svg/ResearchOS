$a='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\owned_core_stop_anchor_revision02_source_codex\20261015-current-chat'
$f=Get-Content "$a\candidate-f5db4a96-final\failure-ledger.json" -Raw | ConvertFrom-Json
foreach($r in $f.raw_nonzero_command_captures) { $p=$r.capture; $s=[IO.File]::ReadAllText("$p\stdout.bin"); $t=[IO.File]::ReadAllText("$p\stderr.bin"); [pscustomobject]@{capture=(Split-Path $p -Leaf);exit=$r.native_exit;stdout=$s;stderr=$t} | ConvertTo-Json -Compress }
