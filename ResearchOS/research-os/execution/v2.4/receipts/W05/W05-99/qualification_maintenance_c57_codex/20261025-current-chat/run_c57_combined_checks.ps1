$ErrorActionPreference = 'Stop'
$receipt = Split-Path -Parent $MyInvocation.MyCommand.Path
$worktree = 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-maintenance-c57-20261025'
$go = 'D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe'
$env:TEMP = 'C:/Users/yqyyds/.codex/researchos-fixture-cache/qualification-maintenance-c57-20261025/tmp'
$env:TMP = $env:TEMP
$env:GOTMPDIR = 'C:/Users/yqyyds/.codex/researchos-fixture-cache/qualification-maintenance-c57-20261025/go-tmp'
$env:GOCACHE = 'C:/Users/yqyyds/.codex/researchos-fixture-cache/qualification-maintenance-c57-20261025/go-cache'
$env:GOMODCACHE = 'D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod'
Set-Location -LiteralPath $worktree

$checks = @(
    @{ id='065-domain'; args=@('test','-count=1','./internal/domain','-run','^(TestHistoricalQualification.*|TestBackupSourceLease.*|TestPreparedNestedSourceLeaseCloseKeepsOuterNativeOwner|TestConfigurationUpgradeActiveQueueRecovery)$'); os='windows' },
    @{ id='066-core'; args=@('test','-count=1','./adapters/runtime','./internal/store','./internal/host','./internal/qualificationmaintenancejournal','./apps/control','./ops/backup','./ops/supervisor/release_host','-run','^(TestDataRootLease.*|TestDataRootSourceGuard.*|TestMaintenanceBorrow.*|TestBothPendingNamespaces.*|TestOpenQualificationMaintenance.*|TestQualificationJournal.*|TestQualificationMaintenance.*|TestQualificationBusiness.*|TestRuntimeVerifierReplacement.*|TestControlReplay.*|TestBackupSourceLeaseRejectsBoth.*|TestReleaseHostLeaseRejectsBoth.*)$'); os='windows' },
    @{ id='067-boot'; args=@('test','-count=1','./internal/recoveryboundary','./ops/qualification_recovery_boundary'); os='windows' },
    @{ id='068-windows-build'; args=@('build','./...'); os='windows' },
    @{ id='069-linux-build'; args=@('build','./...'); os='linux' }
)
$failed = $false
foreach ($check in $checks) {
    $env:GOOS = $check.os
    $env:GOARCH = 'amd64'
    $prefix = Join-Path $receipt ('combined-' + $check.id)
    $recipe = @(
        "cwd=$worktree", "go=$go", "GOOS=$env:GOOS", "GOARCH=$env:GOARCH",
        "TEMP=$env:TEMP", "TMP=$env:TMP", "GOTMPDIR=$env:GOTMPDIR",
        "GOMODCACHE=$env:GOMODCACHE", "GOCACHE=$env:GOCACHE",
        ('argv=' + $go + ' ' + ($check.args -join ' '))
    ) -join "`n"
    [System.IO.File]::WriteAllText($prefix + '.recipe.txt', $recipe + "`n", [System.Text.UTF8Encoding]::new($false))
    $arguments = [string[]]$check.args
    & $go @arguments 1> ($prefix + '.stdout.raw') 2> ($prefix + '.stderr.raw')
    $native = $LASTEXITCODE
    [System.IO.File]::WriteAllText($prefix + '.native-exit.txt', "$native`n", [System.Text.UTF8Encoding]::new($false))
    Write-Output "$($check.id) native_exit=$native"
    if ($native -ne 0) { $failed = $true }
}
if ($failed) { exit 1 }
exit 0
