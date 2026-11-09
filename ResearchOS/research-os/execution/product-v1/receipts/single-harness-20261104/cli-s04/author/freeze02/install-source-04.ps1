$ErrorActionPreference='Stop'
$b='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-cli-s04-author'
$w='D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-cli-20261104'
$p=Join-Path $w 'apps/cli/productv1_test.go'
if(Test-Path -LiteralPath $p){throw 'new test already exists'}
Copy-Item -LiteralPath ($b+'/productv1_test.go') -Destination $p
[ordered]@{path='apps/cli/productv1_test.go';sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}|ConvertTo-Json|Set-Content -LiteralPath ($b+'/source-04.result.json')
