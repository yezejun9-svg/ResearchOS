$ErrorActionPreference='Stop'
$W='D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-20261015'
$p="$W\internal\domain\runtime_qualification_failure_windows_test.go";$l=Get-Content $p;0..430|ForEach-Object {"$($_+1): $($l[$_])"}
rg -n 'func .*dispatchGate|func .*PrivateDirectory|func .*ReadBridgeTerminal|func .*currentAuthorityRoot|func .*clientAuthenticatedPrincipal|func .*validateRuntimeToolArguments|CREATE TABLE.*queue|queue_control|client_queue_' "$W\internal\domain\runtime_broker_windows.go" "$W\internal\domain\runtime_command_queue_windows.go" "$W\internal\domain\runtime_qualification*.go" "$W\adapters\runtime" "$W\internal\domain\client*.go"
Get-Content -Raw "$W\internal\domain\runtime_broker_windows.go" | Select-Object -First 1
Get-ChildItem 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_revision03_independent_review_codex\20261015-current-chat' -Name
