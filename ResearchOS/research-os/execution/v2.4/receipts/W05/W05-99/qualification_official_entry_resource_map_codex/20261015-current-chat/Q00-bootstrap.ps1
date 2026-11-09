$root='D:/作品集/ResearchOS/research-os'
$card=Join-Path $root 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp518/official-entry-readonly-resource-scope.json'
'AGENTS'
Get-Content -LiteralPath (Join-Path $root 'AGENTS.md') -Raw
'SCOPE_HASH='+(Get-FileHash -LiteralPath $card -Algorithm SHA256).Hash.ToLower()
if((Get-FileHash -LiteralPath $card -Algorithm SHA256).Hash.ToLower() -ne 'eeac5e55ab5df7a60c5361095bd48d50a382cf666888c878f09092ea5751bb9d'){throw 'SCOPE_HASH_MISMATCH'}
'SCOPE'
Get-Content -LiteralPath $card -Raw

