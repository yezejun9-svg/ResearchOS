$ErrorActionPreference='Stop'
$b='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-cli-s04-author'
$hash=(Get-FileHash -LiteralPath ($b+'/final-02/source-manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant()
$d=Get-Content -LiteralPath ($b+'/diagnostics.json') -Raw|ConvertFrom-Json
$d|Add-Member previous_author_diagnostics_sha256 '11c58d24133dda26e798a2aa69e2204020c8ec4b051ed43cc6874617b0680f40'
$d.diagnostic_events+=[ordered]@{origin_key='CLI-QA-001';classification='PRODUCTION_SOURCE_INDEPENDENT_REVIEW';severity='P2';candidate_freeze=1;evidence=[ordered]@{reporter='codex:/root/resource_controller_review';tool_chunk='05f9b2';raw='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-cli-independent-qa-20261104/checks-01-counterexample/stdout';raw_sha256='5a58447b802cbf1e5b14ca3fc39d04e8c7c4cb56c7ff5ee566fc311c43f95bd0';fixture='TestQCLIContractRunStartedNullableSnapshot'};detail='The frozen rev2 schema permits RUN_STARTED payload.task=null and requires actual run/status. The first CLI candidate incorrectly required a non-null task snapshot, rejecting a schema-valid event. Same-frame snapshot-present positive control passed.';fixed_in='source-07.json';fix='Removed only RUN_STARTED p.task mandatory predicate. Existing validation of any present task/status/run snapshot remains. Schema still requires the nullable key itself.';resolved_by_author='attempt-04 fmt/test/vet0; null/matching positive controls and wrong-task/status/run/missing-key negatives';independent_resolution='PENDING'}
$d.attempts+=[ordered]@{attempt=4;kind='RUN_STARTED_NULLABLE_SNAPSHOT_INTEROPERABILITY';fmt_exit=0;test_exit=0;vet_exit=0;pass_events=103;top=16;sub=87;new_S04=71;new_S04_top=11;new_S04_sub=60;existing_pure_Mu=32;fail_events=0;skip_events=0;evidence='attempt-04'}
[IO.File]::WriteAllText(($b+'/diagnostics-02.json'),($d|ConvertTo-Json -Depth 15),[Text.UTF8Encoding]::new($false))
$s=Get-Content -LiteralPath ($b+'/final/summary.json') -Raw|ConvertFrom-Json
$s.manifest='final-02/source-manifest.json';$s.manifest_sha256=$hash;$s.diagnostics='diagnostics-02.json'
$s.validation.attempt=4;$s.validation.pass_events=103;$s.validation.top=16;$s.validation.sub=87;$s.validation.new_S04_pass=71;$s.validation.new_S04_top=11;$s.validation.new_S04_sub=60
$s.raw_results=@('attempt-04/fmt.log','attempt-04/fmt.result.json','attempt-04/test.jsonl','attempt-04/test.result.json','attempt-04/vet.log','attempt-04/vet.result.json','attempt-04/source-manifest.json')
$s.command='attempt-04.ps1'
$s.behavior+='RUN_STARTED permits the contract-valid null task snapshot. Any present snapshot still must match task/status/run; a missing nullable key remains schema-invalid.'
$s|Add-Member previous_candidate ([ordered]@{path='final/source-manifest.json';sha256='6138822e5c28a596cce3363a8850612e7a81ac119d67bd5659f0da8d349fc99a';usable_for_integration=$false;reason='CLI-QA-001 valid RUN_STARTED nullable snapshot rejected';preserved=$true})
[IO.File]::WriteAllText(($b+'/final-02/summary.json'),($s|ConvertTo-Json -Depth 15),[Text.UTF8Encoding]::new($false))
$f=[ordered]@{schema='researchos.product-v1-freeze-marker.v1';state='AUTHOR_FROZEN';candidate=2;scope_id='PRODUCT_V1_S04_CLI_HARNESS';manifest='source-manifest.json';manifest_sha256=$hash;summary='summary.json';diagnostics='../diagnostics-02.json';source_changes_stopped=$true;source_count=3;previous_candidate_preserved=$true;independent_review='PENDING';product_acceptance_increment=0}
[IO.File]::WriteAllText(($b+'/final-02/freeze.json'),($f|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
$files=@(Get-ChildItem -LiteralPath $b -File|Where-Object{$_.Name -ne 'archive-file-list-02.json'})
foreach($dir in @('final','final-02')){$files+=@(Get-ChildItem -LiteralPath ($b+'/'+$dir) -File -Recurse)}
foreach($dir in @('attempt-01','attempt-02','attempt-03','attempt-04')){$files+=@(Get-ChildItem -LiteralPath ($b+'/'+$dir) -File)}
$rows=@($files|Sort-Object FullName -Unique|ForEach-Object{[ordered]@{relative_path=[IO.Path]::GetRelativePath($b,$_.FullName).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant();bytes=$_.Length}})
$total=0L;foreach($row in $rows){$total+=[int64]$row['bytes']}
$index=[ordered]@{schema='researchos.product-v1-archive-file-list.v1';base_directory=$b;candidate=2;excluded=@('**/gocache/**','**/tmp/**','module cache','temporary executables');original_c_preserved=$true;total_bytes=$total;files=$rows}
[IO.File]::WriteAllText(($b+'/archive-file-list-02.json'),($index|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
@('final-02/freeze.json','final-02/summary.json','diagnostics-02.json','final-02/source-manifest.json','archive-file-list-02.json')|ForEach-Object{[ordered]@{path=$_;sha256=(Get-FileHash -LiteralPath ($b+'/'+$_) -Algorithm SHA256).Hash.ToLowerInvariant()}}|ConvertTo-Json -Depth 4
