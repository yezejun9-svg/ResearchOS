$ErrorActionPreference='Stop'
$W='D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-20261015'
rg -n 'func .*put\(|CREATE TABLE.*client|CREATE TABLE.*resource_effects|CREATE TABLE.*uploaded_content|CREATE TABLE.*object_refs' "$W\internal" "$W\migrations"
rg -n 'qualificationFirstGateRejectionTx|validatedQualificationFailureTx|closeOnlineQualificationFailure|runCommandBridge\(' "$W\internal" "$W\adapters"
Get-Content -Raw 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_source_codex\20261015-current-chat\b105-existing-regression.recipe.json'
$p='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_revision02_architecture_codex\20261015-current-chat\C-ARCHITECTURE.md'
Get-Content $p | Select-Object -Skip 35 -First 120
