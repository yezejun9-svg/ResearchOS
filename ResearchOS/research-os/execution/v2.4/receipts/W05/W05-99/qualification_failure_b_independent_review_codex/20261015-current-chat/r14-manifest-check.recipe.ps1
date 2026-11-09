$ErrorActionPreference='Stop'
$R='D:\作品集\ResearchOS\research-os'
$A="$R\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_source_codex\20261015-current-chat"
$m=Get-Content -Raw "$A\B-evidence-manifest.json"|ConvertFrom-Json
$m.PSObject.Properties.Name
$m|Select-Object -Property candidate,tree,source_files,files|ConvertTo-Json -Depth 4
Get-Content 'D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-20261015\internal\domain\store.go' | Select-Object -Skip 188 -First 155
Get-Content 'D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-20261015\migrations\sqlite\0022_client_command_queue.sql' | Select-Object -First 70
Get-Content -Tail 8 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_independent_review_codex\20261015-current-chat\r09-focused-tests.raw.txt'
