$ErrorActionPreference='Stop'
$R='D:\作品集\ResearchOS\research-os'
$W='D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-20261015'
$A="$R\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_source_codex\20261015-current-chat"
$m=Get-Content -Raw "$A\B-evidence-manifest.json"|ConvertFrom-Json
$checks=@()
foreach($p in $m.source.PSObject.Properties) {
$f=Get-Item -LiteralPath "$W\$($p.Name)";$h=(Get-FileHash -LiteralPath $f.FullName).Hash.ToLower()
$checks+=@{kind='source';path=$p.Name;sha256=$h;bytes=$f.Length;matches=($h -eq $p.Value.sha256 -and $f.Length -eq $p.Value.bytes)}
}
foreach($record in $m.command_ledger) {
$id=$record.id;$recipe="$A\$id.recipe.json";$result="$A\$id.result.json"
$rh=(Get-FileHash -LiteralPath $recipe).Hash.ToLower();$rv=Get-Content -Raw $result|ConvertFrom-Json
$sh=(Get-FileHash -LiteralPath "$A\$id.stdout.raw").Hash.ToLower()
$eh=(Get-FileHash -LiteralPath "$A\$id.stderr.raw").Hash.ToLower()
$checks+=@{kind='command';id=$id;recipe_matches=($rh -eq $record.recipe.sha256);stdout_matches=($sh -eq $record.stdout_sha256);stderr_matches=($eh -eq $record.stderr_sha256);manifest_native_exit=$record.native_exit;result=$rv}
}
$checks|ConvertTo-Json -Depth 12|Set-Content 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_independent_review_codex\20261015-current-chat\author-source-verification.json'
@{source_count=@($checks|Where-Object kind -eq source).Count;source_bad=@($checks|Where-Object {$_.kind -eq 'source' -and !$_.matches}).Count;commands=@($checks|Where-Object kind -eq command).Count;command_hash_bad=@($checks|Where-Object {$_.kind -eq 'command' -and (!$_.recipe_matches -or !$_.stdout_matches -or !$_.stderr_matches)}).Count}|ConvertTo-Json
git -C $W diff --numstat f48fca0e4013bda19913a34d91da0cd23157a08b HEAD
foreach($id in @('r09-focused-tests','r15-private-tamper-tests','r16-existing-regression')){
$l=Get-Content 'D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_independent_review_codex\20261015-current-chat\PLACEHOLDER' -ErrorAction SilentlyContinue
$p='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\qualification_failure_b_independent_review_codex\20261015-current-chat\'+$id+'.raw.txt';$data=Get-Content $p
@{id=$id;pass_nodes=@($data|Select-String '^\s*--- PASS:').Count;fail_nodes=@($data|Select-String '^\s*--- FAIL:').Count;skip_nodes=@($data|Select-String '^\s*--- SKIP:').Count}|ConvertTo-Json
}
