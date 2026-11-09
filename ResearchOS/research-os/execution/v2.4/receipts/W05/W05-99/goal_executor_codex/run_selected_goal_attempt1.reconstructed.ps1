$ErrorActionPreference = 'Stop'
$repo = 'D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-goal'
$receipt = Join-Path $repo 'execution/v2.4/receipts/W05/W05-99/goal_executor_codex'
$go = 'D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe'
$goroot = 'D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go'
$node = 'C:/nvm4w/nodejs/node.exe'
$bundle = 'D:/作品集/ResearchOS/research-os/.local/w1401-mu-worker/mu-worker.mjs'
$selector = '^(TestClient|TestRuntimeMu|TestRuntimeOriginalToolPermission|TestRuntimePermission|TestPermissionProducer|TestPermissionRespond|TestW14Session)'

function FileHash($path) { (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant() }
function SaveJson($path, $value) {
    $json = $value | ConvertTo-Json -Depth 12
    [System.IO.File]::WriteAllText($path, $json + "`n", [System.Text.UTF8Encoding]::new($false))
}
function RepoInputs($path) {
    Push-Location $repo
    try {
        $paths = & git ls-files -- apps adapters contracts evaluation internal migrations ops spec tests third_party go.mod go.sum
        if ($LASTEXITCODE -ne 0) { throw 'git ls-files failed' }
        $files = @($paths | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Sort-Object -Unique | ForEach-Object {
            $item = Get-Item -LiteralPath $_
            [ordered]@{ path = $_.Replace('\','/'); bytes = [int64]$item.Length; sha256 = FileHash $item.FullName }
        })
        $snapshot = [ordered]@{
            schema = 'researchos.w05.goal-test-input-snapshot.v1'
            scope = 'every materialized tracked file in the selected test source, schema, migration, fixture and module roots'
            tracked_path_count = @($paths).Count
            materialized_file_count = $files.Count
            sparse_missing_count = @($paths).Count - $files.Count
            files = $files
            external_inputs = [ordered]@{
                go_exe_sha256 = FileHash $go
                node_exe_sha256 = FileHash $node
                mu_bundle_sha256 = FileHash $bundle
            }
        }
        SaveJson $path $snapshot
        return $snapshot
    } finally { Pop-Location }
}

if (-not (Test-Path -LiteralPath $receipt -PathType Container)) { throw 'receipt directory missing' }
$runnerPath = $MyInvocation.MyCommand.Path
$runnerHashBefore = FileHash $runnerPath
$started = (Get-Date).ToUniversalTime().ToString('o')
$beforePath = Join-Path $receipt 'selected-input-before.json'
$afterPath = Join-Path $receipt 'selected-input-after.json'
$before = RepoInputs $beforePath

$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $go
$psi.WorkingDirectory = $repo
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
foreach ($arg in @('test','-json','./internal/domain','-run',$selector,'-count=1')) { [void]$psi.ArgumentList.Add($arg) }
$psi.Environment['GOROOT'] = $goroot
$psi.Environment['RESEARCHOS_GO'] = $go
$psi.Environment['GOCACHE'] = 'D:/作品集/ResearchOS/research-os/.local/gocache'
$psi.Environment['GOPROXY'] = 'off'
$psi.Environment['GOTOOLCHAIN'] = 'local'
$psi.Environment['RESEARCHOS_MU_BUNDLE'] = $bundle
$psi.Environment['PATH'] = (Split-Path -Parent $node) + ';' + $psi.Environment['PATH']

$stdoutPath = Join-Path $receipt 'selected-go.stdout.raw'
$stderrPath = Join-Path $receipt 'selected-go.stderr.raw'
$stdout = [System.IO.File]::Create($stdoutPath)
$stderr = [System.IO.File]::Create($stderrPath)
$process = $null
try {
    $process = [System.Diagnostics.Process]::Start($psi)
    $stdoutCopy = $process.StandardOutput.BaseStream.CopyToAsync($stdout)
    $stderrCopy = $process.StandardError.BaseStream.CopyToAsync($stderr)
    $process.WaitForExit()
    [System.Threading.Tasks.Task]::WhenAll(@($stdoutCopy, $stderrCopy)).GetAwaiter().GetResult()
    $exitCode = [int]$process.ExitCode
} finally {
    $stdout.Dispose()
    $stderr.Dispose()
    if ($null -ne $process) { $process.Dispose() }
}
$finished = (Get-Date).ToUniversalTime().ToString('o')
$after = RepoInputs $afterPath
$runnerHashAfter = FileHash $runnerPath
$beforeFiles = @{}
foreach ($file in $before.files) { $beforeFiles[$file.path] = $file.sha256 }
$changed = @($after.files | Where-Object { $beforeFiles[$_.path] -ne $_.sha256 } | ForEach-Object { $_.path })
$events = @(Get-Content -LiteralPath $stdoutPath | ForEach-Object { $_ | ConvertFrom-Json })
$top = @($events | Where-Object { $_.Test -and $_.Test -notmatch '/' -and $_.Action -in @('pass','fail','skip') })
$manifest = [ordered]@{
    schema = 'researchos.w05.goal-test-subprocess-run.v1'
    measurement_mode = 'FIXTURE'
    started_at_utc = $started
    finished_at_utc = $finished
    runner_path = 'execution/v2.4/receipts/W05/W05-99/goal_executor_codex/run_selected_goal.ps1'
    runner_sha256_before = $runnerHashBefore
    runner_sha256_after = $runnerHashAfter
    executable = $go
    argv = @('test','-json','./internal/domain','-run',$selector,'-count=1')
    working_directory = $repo
    environment = [ordered]@{
        GOROOT = $goroot
        RESEARCHOS_GO = $go
        GOCACHE = 'D:/作品集/ResearchOS/research-os/.local/gocache'
        GOPROXY = 'off'
        GOTOOLCHAIN = 'local'
        RESEARCHOS_MU_BUNDLE = $bundle
        PATH_prepended = (Split-Path -Parent $node)
    }
    subprocess_exit_code = $exitCode
    top_level = [ordered]@{
        pass = @($top | Where-Object Action -eq 'pass').Count
        fail = @($top | Where-Object Action -eq 'fail').Count
        skip = @($top | Where-Object Action -eq 'skip').Count
    }
    top_level_failures = @($top | Where-Object Action -eq 'fail' | ForEach-Object { $_.Test })
    stdout = [ordered]@{ path = 'selected-go.stdout.raw'; bytes = (Get-Item $stdoutPath).Length; sha256 = FileHash $stdoutPath }
    stderr = [ordered]@{ path = 'selected-go.stderr.raw'; bytes = (Get-Item $stderrPath).Length; sha256 = FileHash $stderrPath }
    input_before = [ordered]@{ path = 'selected-input-before.json'; sha256 = FileHash $beforePath; materialized_file_count = $before.materialized_file_count }
    input_after = [ordered]@{ path = 'selected-input-after.json'; sha256 = FileHash $afterPath; materialized_file_count = $after.materialized_file_count }
    changed_source_files = $changed
    runner_unchanged = $runnerHashBefore -eq $runnerHashAfter
    source_inputs_unchanged = $changed.Count -eq 0 -and $before.materialized_file_count -eq $after.materialized_file_count
    provider_calls = 'local fixture endpoint only; no live provider'
    acceptance_issued = $false
}
SaveJson (Join-Path $receipt 'selected-subprocess-run.json') $manifest
Write-Output "exit=$exitCode pass=$($manifest.top_level.pass) fail=$($manifest.top_level.fail) skip=$($manifest.top_level.skip) source_changed=$($changed.Count) stdout_bytes=$($manifest.stdout.bytes) stderr_bytes=$($manifest.stderr.bytes)"
exit $exitCode
