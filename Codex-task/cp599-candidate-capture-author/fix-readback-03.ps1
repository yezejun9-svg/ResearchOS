$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new()
$p='D:/作品集/ResearchOS/research-os/.local/worktrees/host-candidate-capture-20261104/internal/host/runtime_check_windows.go'
if((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'c7258f82eb54aaed9a72644134da8e6d656811bc5af3929d99e11dad83fe5888'){throw 'source changed'}
$s=[IO.File]::ReadAllText($p)
if(-not $s.Contains("}`tcaptureView") -or -not $s.Contains("}`tif err := runtimeCheckEvidenceBound")){throw 'readback needle changed'}
$s=$s.Replace("}`tcaptureView","}`n`tcaptureView").Replace("}`tif err := runtimeCheckEvidenceBound","}`n`tif err := runtimeCheckEvidenceBound")
[IO.File]::WriteAllText($p,$s,[Text.UTF8Encoding]::new($false))
$r=[ordered]@{status='READBACK_NEWLINE_CORRECTION_UNTESTED';path=$p;sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
[IO.File]::WriteAllText('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/cp599-candidate-capture-author/source-write-03.json',($r|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
$r|ConvertTo-Json -Compress

