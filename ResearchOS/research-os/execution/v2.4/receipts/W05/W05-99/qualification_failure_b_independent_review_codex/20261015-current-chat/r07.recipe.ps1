$ErrorActionPreference='Stop'
$W='D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-20261015'
Get-Content "$W\internal\domain\orchestration.go" | Select-Object -First 150
Get-Content "$W\internal\domain\client_protocol_sessions.go" | Select-Object -First 70
Get-Content "$W\adapters\runtime\process_windows.go" | Select-Object -First 95
$p="$W\internal\domain\runtime_coordinator_windows.go";$l=Get-Content $p;472..510|ForEach-Object {"$($_+1): $($l[$_])"};590..670|ForEach-Object {"$($_+1): $($l[$_])"}
$p="$W\adapters\runtime\bridge_windows.go";$l=Get-Content $p;807..885|ForEach-Object {"$($_+1): $($l[$_])"}
rg -n 'CREATE TABLE.*(client|queue)|func .*RevokePrincipal|func .*contextFixture' "$W\internal"
Get-Content "$W\internal\domain\runtime_tools_windows.go" | Select-Object -First 65
