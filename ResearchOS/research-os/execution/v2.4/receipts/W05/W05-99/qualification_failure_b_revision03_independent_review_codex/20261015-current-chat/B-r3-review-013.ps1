$ErrorActionPreference='Stop'
Get-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision03_independent_review_codex/20261015-current-chat/B-r3-review-008.stdout.raw' -Tail 45
rg -n 'GetFinalPathName|FinalPath|FILE_LIST_DIRECTORY|func.*Close|GetFileInformation' 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015/adapters/runtime/qualification_failure_proof_windows.go'
git -C 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015' rev-parse HEAD 'HEAD^{tree}'
if($LASTEXITCODE -ne 0){throw 'git rev-parse failed'}
git -C 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015' status --porcelain --untracked-files=all
if($LASTEXITCODE -ne 0){throw 'git status failed'}
$scope=Get-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp525/B-r3-independent-review-scope.json' -Raw | ConvertFrom-Json
$records=@(foreach($p in $scope.source_allowlist_readonly){$f=Get-Item -LiteralPath (Join-Path 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015' $p);[ordered]@{path=$p;bytes=$f.Length;sha256=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}})
$records|ConvertTo-Json -Depth 10
[IO.File]::WriteAllText('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision03_independent_review_codex/20261015-current-chat/final-source-pins.json',($records|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))

