$ErrorActionPreference='Stop'
rg -n 'func .*Model|func Hash|func Digest|request_hash|provider_response_hash|writeRuntimeFact|completeRuntimeModelSSE' 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/internal/domain/runtime_model_windows.go' 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/internal/domain/types.go'
$searchExit=$LASTEXITCODE
'SEARCH_NATIVE_EXIT '+$searchExit
$p='D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015/internal/domain/runtime_model_windows.go'
if(Test-Path -LiteralPath $p){$a=Get-Content -LiteralPath $p -Encoding utf8;for($i=0;$i -lt $a.Count;$i++){'{0}: {1}' -f ($i+1),$a[$i]}}
$sourceManifest=Get-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision02_source_codex/20261015-current-chat/FINAL-manifest.json' -Raw -Encoding utf8 | ConvertFrom-Json
$verification=@()
foreach($p in $sourceManifest.source_hashes.PSObject.Properties){$path=Join-Path 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015' $p.Name;$actual=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant();if($actual -ne $p.Value.sha256){throw ('SOURCE CHANGED '+$p.Name)};$verification += [ordered]@{path=$p.Name;sha256=$actual;bytes=(Get-Item -LiteralPath $path).Length}}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'source-final-verification.json'),($verification|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
git -C 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015' diff --name-only 75e5257c HEAD
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
git -C 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015' diff --name-only f48fca0e HEAD
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
git -C 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r2-20261015' status --porcelain=v1
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
Get-FileHash -LiteralPath 'D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe','D:/作品集/ResearchOS/research-os/.local/w0599-main-stream-integration-r268/mu-worker.mjs' -Algorithm SHA256 | ConvertTo-Json
$summary=@()
foreach($id in @('006','008','009','014','016')){
 $tag='B-r2-review-'+$id
 $events=@(Get-Content -LiteralPath (Join-Path $PSScriptRoot ($tag+'.stdout.txt')) -Encoding utf8 | Where-Object { $_.StartsWith('{') } | ForEach-Object { $_ | ConvertFrom-Json })
 $cmd=Get-Content -LiteralPath (Join-Path $PSScriptRoot ($tag+'.command.json')) -Raw -Encoding utf8 | ConvertFrom-Json
 $summary += [ordered]@{id=$tag;nativeExit=$cmd.nativeExit;testPass=@($events|Where-Object {$_.Action -eq 'pass' -and $_.Test}).Count;testFail=@($events|Where-Object {$_.Action -eq 'fail' -and $_.Test}).Count;testSkip=@($events|Where-Object {$_.Action -eq 'skip' -and $_.Test}).Count;failedTests=@($events|Where-Object {$_.Action -eq 'fail' -and $_.Test}|ForEach-Object {$_.Test});packageResults=@($events|Where-Object {$_.Action -in @('pass','fail','skip') -and !$_.Test}|Select-Object Package,Action,Elapsed)}
}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'test-summary.json'),($summary|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$summary|ConvertTo-Json -Depth 10
if($searchExit -ne 0){exit $searchExit}
exit 0
