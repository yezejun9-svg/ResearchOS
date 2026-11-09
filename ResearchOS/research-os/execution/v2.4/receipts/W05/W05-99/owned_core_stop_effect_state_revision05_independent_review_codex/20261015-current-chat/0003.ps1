$ErrorActionPreference='Stop'
$s='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp522/owned-core-stop-effect-state-r5-independent-review-scope.json'
(Get-FileHash -LiteralPath $s).Hash
$sc=Get-Content $s -Raw | ConvertFrom-Json
foreach($p in $sc.source_allowlist_readonly){Write-Output "SOURCE: $p"; Get-Content -LiteralPath (Join-Path $sc.worktree $p)}
rg -n 'W05-99|VALIDATED_FILE' 'C:/Users/yqyyds/.codex/memories/MEMORY.md'
rg --files 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/owned_core_stop_authority_revision04_independent_review_codex/20261015-current-chat' -g '*.py' -g '*.go' -g '*review.json'
