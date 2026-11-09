$t='D:/作品集/ResearchOS/research-os/.local/owned-core-stop-r5-independent-review-20261015-tmp'
$e='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/owned_core_stop_effect_state_revision05_independent_review_codex/20261015-current-chat'
Get-ChildItem -LiteralPath $t -File -Recurse | Measure-Object -Property Length -Sum | Select-Object Count,Sum
Get-ChildItem -LiteralPath "$e/command-captures" -Recurse -Filter command.json | ForEach-Object {Get-Content $_.FullName}
Get-ChildItem -LiteralPath "$e/command-captures" -Recurse -Filter result.json | ForEach-Object {Get-Content $_.FullName}
