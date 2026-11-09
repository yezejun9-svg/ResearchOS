$ErrorActionPreference='Stop'
$s=Get-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp525/B-r3-independent-review-scope.json' -Raw -Encoding utf8|ConvertFrom-Json
foreach($i in $s.inputs){$p=Join-Path 'D:/作品集/ResearchOS/research-os' $i.path;$hash=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant();$n=(Get-Item -LiteralPath $p).Length;if($hash -ne $i.sha256 -or $n -ne $i.bytes){throw ('INPUT MISMATCH '+$p)};'VERIFIED '+$i.path+' '+$hash}
foreach($path in @('AGENTS.md','adapters/AGENTS.md','adapters/runtime/AGENTS.md','internal/AGENTS.md','internal/domain/AGENTS.md')){$p=Join-Path 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015' $path;if(Test-Path -LiteralPath $p){'RULE '+$p;Get-Content -LiteralPath $p -Raw -Encoding utf8}}
foreach($i in @(0,1,4,5)){'INPUT '+$s.inputs[$i].path;Get-Content -LiteralPath (Join-Path 'D:/作品集/ResearchOS/research-os' $s.inputs[$i].path) -Raw -Encoding utf8}
git -C 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015' status --porcelain=v1
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
git -C 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015' rev-parse HEAD 'HEAD^{tree}'
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
git -C 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015' diff 1d3cc504 HEAD -- adapters/runtime/qualification_failure_proof_windows.go internal/domain/runtime_qualification_failure_windows.go
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
exit 0
