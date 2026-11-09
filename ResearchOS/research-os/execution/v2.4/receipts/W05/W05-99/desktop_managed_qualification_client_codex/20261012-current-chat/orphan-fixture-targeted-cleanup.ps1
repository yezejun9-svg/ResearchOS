$ErrorActionPreference = 'Stop'
$receipt = Split-Path -Parent $MyInvocation.MyCommand.Path
$childId = 20448
$parentId = 64952
$fixtureRoot = 'D:\作品集\ResearchOS\research-os\.local\worktrees\w05-desktop-managed-qualification-client-20261012\.local\managed-client-coupling-fixture-1'
$controlImage = 'D:\作品集\ResearchOS\research-os\.local\builds\desktop-managed-qualification-core-repair-v2-20261012\researchos-control.exe'
$nodeImage = 'C:\Users\yqyyds\AppData\Local\nvm\v24.9.0\node.exe'
$expectedChild = @{PID=20448; CreatedNS='1791799034114364400'; ImageSHA256='a97e5e8d52d9523817a49b682bce75df243bd8569286ff92b49d31575886e44b'}
$expectedParent = @{PID=64952; CreatedNS='1791799033304534600'; ImageSHA256='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'}
function Observe([int]$id) {
  $cim = Get-CimInstance Win32_Process -Filter "ProcessId = $id"
  if ($null -eq $cim) { throw "PID_MISSING:$id" }
  $proc = [System.Diagnostics.Process]::GetProcessById($id)
  $ns = (([bigint]$proc.StartTime.ToUniversalTime().ToFileTimeUtc()) - [bigint]116444736000000000) * [bigint]100
  $image = $proc.MainModule.FileName
  return [ordered]@{PID=$id; ParentPID=$cim.ParentProcessId; CreatedNS=$ns.ToString();
    Image=$image; ImageSHA256=(Get-FileHash -LiteralPath $image -Algorithm SHA256).Hash.ToLowerInvariant();
    CommandLine=$cim.CommandLine; CreationDate=$cim.CreationDate.ToString('o')}
}
$child = Observe $childId
$parent = Observe $parentId
$snapshot = [ordered]@{at=(Get-Date).ToUniversalTime().ToString('o'); child=$child; parent=$parent;
  fixture_root=$fixtureRoot; expected_child=$expectedChild; expected_parent=$expectedParent}
$snapshot | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $receipt 'orphan-fixture-process-before.json') -Encoding utf8
foreach ($pair in @(@($child,$expectedChild),@($parent,$expectedParent))) {
  $actual=$pair[0]; $expected=$pair[1]
  if ($actual.PID -ne $expected.PID -or $actual.CreatedNS -ne $expected.CreatedNS -or
      $actual.ImageSHA256 -ne $expected.ImageSHA256) { throw "PROCESS_IDENTITY_MISMATCH:$($actual.PID)" }
}
if ($child.ParentPID -ne $parentId -or $child.Image -ine $controlImage -or $parent.Image -ine $nodeImage -or
    $child.CommandLine -notlike "*$fixtureRoot*" -or
    $child.CommandLine -notlike '*--desktop-management-stdio*' -or
    $parent.CommandLine -notlike '*candidate-binary-coupling.mjs*run3*') { throw 'TARGET_SCOPE_MISMATCH' }
$census = Get-Content -LiteralPath (Join-Path $receipt 'orphan-fixture-db-census-before.json') -Raw | ConvertFrom-Json
foreach ($name in @('experiment_runs','host_model_configurations','resource_effects','runtime_dispatches','runtime_qualification_runs')) {
  if ($null -eq $census.relevant_table_counts.$name -or $census.relevant_table_counts.$name -ne 0) { throw "DB_CENSUS_MISMATCH:$name" }
}
$run = Get-Content -LiteralPath (Join-Path $receipt 'candidate-coupling-run3-result.json') -Raw | ConvertFrom-Json
$frames = Get-Content -LiteralPath (Join-Path $receipt 'candidate-coupling-run3-private-frames.json') -Raw | ConvertFrom-Json
if ($run.pid -ne $childId -or $run.confirm_sent -ne $false -or $run.actual_model_calls -ne 0 -or
    $frames.Count -ne 1 -or $frames[0].direction -ne 'core_to_desktop' -or
    ($frames[0].raw | ConvertFrom-Json).kind -ne 'READY') { throw 'PRIVATE_FRAME_CENSUS_MISMATCH' }
# These are the two exact synthetic test processes. This is test cleanup, not protocol SHUTDOWN.
Stop-Process -Id $childId,$parentId -Force -ErrorAction Stop
Start-Sleep -Seconds 1
$remaining = @(Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -in @($childId,$parentId) } | Select-Object -ExpandProperty ProcessId)
$out = [ordered]@{at=(Get-Date).ToUniversalTime().ToString('o'); kind='TARGETED_TEST_CLEANUP_NOT_SAFE_SHUTDOWN';
  stopped_ids=@($childId,$parentId); remaining_ids=$remaining; expected_fixture_root=$fixtureRoot;
  identity_rechecked=$true; read_only_db_census_zero=$true; confirmation_sent=$false; actual_model_calls=0}
$out | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $receipt 'orphan-fixture-process-after.json') -Encoding utf8
if ($remaining.Count -ne 0) { throw 'TARGETED_STOP_UNCONFIRMED' }
$out | ConvertTo-Json -Compress
