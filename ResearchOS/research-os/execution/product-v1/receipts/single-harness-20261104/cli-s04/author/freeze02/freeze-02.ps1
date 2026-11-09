$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new()
$w='D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-cli-20261104'
$b='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-cli-s04-author'
$dst=$b+'/final-02'
New-Item -ItemType Directory -Path $dst -ErrorAction Stop|Out-Null
$pins=Get-Content -LiteralPath ($b+'/attempt-04/source-manifest.json') -Raw|ConvertFrom-Json
foreach($pin in $pins){$path=Join-Path $w $pin.path;if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pin.sha256){throw 'source drift before freeze'};$target=Join-Path ($dst+'/source') $pin.path;New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force|Out-Null;Copy-Item -LiteralPath $path -Destination $target}
$manifest=[ordered]@{schema='researchos.product-v1-source-manifest.v1';scope_id='PRODUCT_V1_S04_CLI_HARNESS';base_head='7006360ad46ce384993b008fe61878195b74b9bf';worktree=$w;frozen_at=[DateTime]::UtcNow.ToString('o');author_stopped_source_changes=$true;interface_sha256='046a49b2b1f82593fe86924913b2ee4d77152ac1cef7dbbb86562f6dfe0cfa1c';independent_review='PENDING';product_acceptance_increment=0;pins=@($pins)}
[IO.File]::WriteAllText(($dst+'/source-manifest.json'),($manifest|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
git -C $w status --porcelain=v1 --untracked-files=all|Set-Content -LiteralPath ($dst+'/git-status.txt')
git -C $w diff --check *> ($dst+'/git-diff-check.txt');$code=$LASTEXITCODE
git -C $w diff --binary -- apps/cli/main.go|Set-Content -LiteralPath ($dst+'/main.diff')
[ordered]@{source_count=@($pins).Count;diff_check_exit=$code;manifest_sha256=(Get-FileHash -LiteralPath ($dst+'/source-manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant()}|ConvertTo-Json
