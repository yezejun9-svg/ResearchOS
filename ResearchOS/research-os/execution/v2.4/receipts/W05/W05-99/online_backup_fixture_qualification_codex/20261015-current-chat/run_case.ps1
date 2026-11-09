param([ValidateSet('Q01','Q02','Q03')][string]$Case,[string]$Attempt='')
$ErrorActionPreference = 'Stop'
$evidence = Split-Path -Parent $MyInvocation.MyCommand.Path
$logger = Join-Path $evidence 'Invoke-EvidenceCommand.ps1'
$repo = 'D:/作品集/ResearchOS/research-os/.local/worktrees/online-backup-fixture-qualification-20261015'
$task = 'D:/作品集/ResearchOS/research-os/.local/online-backup-fixture-qualification-20261015-tmp'
$caseRoot = Join-Path (Join-Path $task 'fixture') $Case
$data = Join-Path $caseRoot $(if ($Case -eq 'Q03') { 'current-data-r2' } else { 'source-data' })
$db = Join-Path $data 'researchos.sqlite'
$suffix = if ($Attempt) { "-$Attempt" } else { '' }
$key = Join-Path (Join-Path $task 'private') "$Case$suffix-recovery.key"
$package = Join-Path $caseRoot "encrypted-backup$suffix"
$restored = Join-Path $caseRoot "restored-data$suffix"
$prefix = $Case.ToLowerInvariant() + $suffix
$python = 'python'
$backup = Join-Path (Join-Path $task 'build') 'backup.exe'
$holderExe = Join-Path (Join-Path $task 'build') 'lease_holder.exe'
$probe = Join-Path (Join-Path $task 'build') 'lease_probe.exe'
$envTask = @{TMP=(Join-Path $task 'tmp');TEMP=(Join-Path $task 'tmp');GOTMPDIR=(Join-Path $task 'go-tmp');GOCACHE=(Join-Path $task 'go-cache')}

& $logger -Id "$prefix-keygen" -Exe $backup -Arguments @('keygen','--key-file',$key) -WorkingDirectory $repo -EnvOverride $envTask -Quiet
if ($LASTEXITCODE -ne 0) { throw 'keygen failed' }

$holderId = "$prefix-holder"
$holderRecipe = [ordered]@{id=$holderId;at_utc=[DateTime]::UtcNow.ToString('o');exe=$holderExe;argv=@($data);cwd=$repo;env_override=$envTask;stdout="$holderId.stdout.raw";stderr="$holderId.stderr.raw";status='prewritten';expected_normal_exit=0}
$holderRecipe | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $evidence "$holderId.recipe.json") -Encoding utf8NoBOM
$psi = [Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $holderExe
$psi.WorkingDirectory = $repo
$psi.UseShellExecute = $false
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
foreach($name in $envTask.Keys) { $psi.Environment[$name] = [string]$envTask[$name] }
[void]$psi.ArgumentList.Add($data)
$process = [Diagnostics.Process]::new()
$process.StartInfo = $psi
$ready = $null
$holderError = $null
try {
    [void]$process.Start()
    $lineTask = $process.StandardOutput.ReadLineAsync()
    if (-not $lineTask.Wait(15000)) { throw 'holder readiness timed out' }
    $ready = $lineTask.Result
    if ($ready -notmatch '"status":"HELD"' -or $ready -notmatch '"held":true') { throw "holder did not report live lease: $ready" }
    & $logger -Id "$prefix-probe-before" -Exe $probe -Arguments @($data) -WorkingDirectory $repo -EnvOverride $envTask -Quiet
    if ($LASTEXITCODE -ne 10) { throw "lease challenger before create exited $LASTEXITCODE" }
    & $logger -Id "$prefix-db-before" -Exe $python -Arguments @('-B','-Xutf8',(Join-Path $evidence 'census.py'),'db',$db) -WorkingDirectory $repo -EnvOverride $envTask -Quiet
    if ($LASTEXITCODE -ne 0) { throw 'db baseline failed' }
    & $logger -Id "$prefix-files-before" -Exe $python -Arguments @('-B','-Xutf8',(Join-Path $evidence 'census.py'),'files',$data) -WorkingDirectory $repo -EnvOverride $envTask -Quiet
    if ($LASTEXITCODE -ne 0) { throw 'file baseline failed' }
    & $logger -Id "$prefix-acl-before" -Exe icacls -Arguments @($data,'/T') -WorkingDirectory $repo -EnvOverride $envTask -Quiet
    if ($LASTEXITCODE -ne 0) { throw 'ACL baseline failed' }
    & $logger -Id "$prefix-create" -Exe $backup -Arguments @('create','--db',$db,'--out',$package,'--key-file',$key,'--root',$repo) -WorkingDirectory $repo -EnvOverride $envTask -Quiet
    if ($LASTEXITCODE -ne 0) { throw "CLI create failed with $LASTEXITCODE" }
    if ($process.HasExited) { throw 'lease holder exited during create' }
    & $logger -Id "$prefix-probe-after" -Exe $probe -Arguments @($data) -WorkingDirectory $repo -EnvOverride $envTask -Quiet
    if ($LASTEXITCODE -ne 10) { throw "lease challenger after create exited $LASTEXITCODE" }
    & $logger -Id "$prefix-db-after" -Exe $python -Arguments @('-B','-Xutf8',(Join-Path $evidence 'census.py'),'db',$db) -WorkingDirectory $repo -EnvOverride $envTask -Quiet
    if ($LASTEXITCODE -ne 0) { throw 'db after failed' }
    & $logger -Id "$prefix-files-after" -Exe $python -Arguments @('-B','-Xutf8',(Join-Path $evidence 'census.py'),'files',$data) -WorkingDirectory $repo -EnvOverride $envTask -Quiet
    if ($LASTEXITCODE -ne 0) { throw 'file after failed' }
    & $logger -Id "$prefix-acl-after" -Exe icacls -Arguments @($data,'/T') -WorkingDirectory $repo -EnvOverride $envTask -Quiet
    if ($LASTEXITCODE -ne 0) { throw 'ACL after failed' }
} catch { $holderError = $_.Exception.Message }
finally {
    if (-not $process.HasExited) {
        $process.StandardInput.WriteLine('release')
        $process.StandardInput.Flush()
        $process.StandardInput.Close()
    }
    if (-not $process.WaitForExit(15000)) { $holderError = "holder did not exit normally: $holderError" }
    $tail = $process.StandardOutput.ReadToEnd()
    $ready + "`n" + $tail | Set-Content -LiteralPath (Join-Path $evidence "$holderId.stdout.raw") -Encoding utf8NoBOM -NoNewline
    $process.StandardError.ReadToEnd() | Set-Content -LiteralPath (Join-Path $evidence "$holderId.stderr.raw") -Encoding utf8NoBOM -NoNewline
    [ordered]@{id=$holderId;pid=$process.Id;native_exit=$process.ExitCode;held_ready=($ready -match '"status":"HELD"');at_utc=[DateTime]::UtcNow.ToString('o');error=$holderError} | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $evidence "$holderId.exit.json") -Encoding utf8NoBOM
}
if ($holderError) { throw $holderError }
if ($process.ExitCode -ne 0) { throw "holder exited $($process.ExitCode)" }
& $logger -Id "$prefix-probe-released" -Exe $probe -Arguments @($data) -WorkingDirectory $repo -EnvOverride $envTask -Quiet
if ($LASTEXITCODE -ne 0) { throw "released lease not reacquirable: $LASTEXITCODE" }
& $logger -Id "$prefix-restore" -Exe $backup -Arguments @('restore','--as-data-root','--backup',$package,'--out',$restored,'--key-file',$key,'--root',$repo) -WorkingDirectory $repo -EnvOverride $envTask -Quiet
if ($LASTEXITCODE -ne 0) { throw "restore failed: $LASTEXITCODE" }
& $logger -Id "$prefix-db-restored" -Exe $python -Arguments @('-B','-Xutf8',(Join-Path $evidence 'census.py'),'db',(Join-Path $restored 'researchos.sqlite')) -WorkingDirectory $repo -EnvOverride $envTask -Quiet
if ($LASTEXITCODE -ne 0) { throw 'restored DB census failed' }
Write-Output "$Case CREATE_AND_RESTORE_COMPLETED holder_exit=$($process.ExitCode)"
