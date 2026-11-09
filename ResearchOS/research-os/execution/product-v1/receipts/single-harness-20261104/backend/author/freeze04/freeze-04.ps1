$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new()
$w='D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-backend-20261104'
$b='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-backend-author'
$dst=$b+'/final-04'
New-Item -ItemType Directory -Path $dst -ErrorAction Stop|Out-Null
$pins=Get-Content -LiteralPath ($b+'/attempt-10/source-manifest.json') -Raw|ConvertFrom-Json
foreach($pin in $pins){$path=Join-Path $w $pin.path;if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pin.sha256){throw 'final source drift'};$target=Join-Path ($dst+'/source') $pin.path;New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force|Out-Null;Copy-Item -LiteralPath $path -Destination $target}
$manifest=[ordered]@{scope_id='PRODUCT_V1_SINGLE_HARNESS_BACKEND';base_head='29f92310a0bdefefbb7c020c792a3565f7b71504';worktree=$w;frozen_at=[DateTime]::UtcNow.ToString('o');author_stopped_source_changes=$true;independent_review='PENDING';product_acceptance_increment=0;interface_sha256='046a49b2b1f82593fe86924913b2ee4d77152ac1cef7dbbb86562f6dfe0cfa1c';pins=@($pins)}
[IO.File]::WriteAllText(($dst+'/source-manifest.json'),($manifest|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
git -C $w status --porcelain=v1 --untracked-files=all|Set-Content -LiteralPath ($dst+'/git-status.txt')
git -C $w diff --check *> ($dst+'/git-diff-check.txt');$diffExit=$LASTEXITCODE
git -C $w diff --binary -- adapters/runtime/codex.go adapters/runtime/process_windows.go apps/control/main.go internal/api/server.go internal/domain/runtime_admission.go internal/domain/runtime_coordinator_windows.go internal/domain/runtime_dispatch.go internal/domain/runtime_recovery_windows.go|Set-Content -LiteralPath ($dst+'/tracked.diff')
@{diff_check_exit=$diffExit;source_count=@($pins).Count;manifest_sha256=(Get-FileHash -LiteralPath ($dst+'/source-manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant()}|ConvertTo-Json
