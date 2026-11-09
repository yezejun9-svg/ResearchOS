$ErrorActionPreference='Stop'
$b='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-backend-author'
$m=Get-Content -LiteralPath ($b+'/final-02/source-manifest.json') -Raw|ConvertFrom-Json
$manifestHash=(Get-FileHash -LiteralPath ($b+'/final-02/source-manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant()
$d=Get-Content -LiteralPath ($b+'/diagnostics.json') -Raw|ConvertFrom-Json
$d|Add-Member previous_author_diagnostics_sha256 '79f0201a3b2efe7b75bcdc896f72604607a9bd1ecc09fec3345e9935ce1ab19b'
$d.diagnostic_events+= [ordered]@{origin_key='backend-v1-native-project-marker';classification='PRODUCTION_SOURCE_INDEPENDENT_REVIEW';candidate_freeze=1;evidence=[ordered]@{reporter='codex:/root/implementation_review';official_source='Codex0.166 loader::discover_project_root 1614-1625';prior_manifest_sha256='ddfcfd8530b1fe88aa065c02bae3a9443e8354939a8649ec2bc5e5c4411ce3f5';raw_independent_counterexample='Reviewer-owned C evidence; linked by Root'};detail='Empty .git without HEAD is skipped by the native loader, so the first candidate could inherit ancestor non-managed project configuration. Original author fake test checked only directory existence and was insufficient.';fixed_in='source-13.json';fix='Regular Host-owned .researchos-codex-root file with fixed same-name project_root_markers, exact-byte/regular-file/no-fake-git assertions';resolved_by_author='attempt-07 fmt/test/vet0';independent_resolution='PENDING'}
$d.attempts+=[ordered]@{attempt=7;kind='CUSTOM_MARKER_FIX';fmt_exit=0;test_exit=0;pass_test_events=23;pass_top_tests=6;pass_subtests=17;skip_test_events=1;fail_test_events=0;vet_exit=0;evidence='attempt-07'}
[IO.File]::WriteAllText(($b+'/diagnostics-02.json'),($d|ConvertTo-Json -Depth 15),[Text.UTF8Encoding]::new($false))
$s=Get-Content -LiteralPath ($b+'/final/summary.json') -Raw|ConvertFrom-Json
$s.manifest='final-02/source-manifest.json';$s.manifest_sha256=$manifestHash;$s.diagnostics='diagnostics-02.json'
$s.validation.final_new_fixtures.attempt=7
$s.validation.existing_pure_compatibility|Add-Member source_scope_note 'Original parser unchanged by the two-file marker fix; the relevant final fake driver and same-DB chain were rerun in attempt07.'
$s.implemented=@($s.implemented|ForEach-Object{$_.Replace('owned cwd plus .git marker','owned cwd plus regular .researchos-codex-root marker file')})
$s|Add-Member previous_candidate ([ordered]@{path='final/source-manifest.json';sha256='ddfcfd8530b1fe88aa065c02bae3a9443e8354939a8649ec2bc5e5c4411ce3f5';usable_for_integration=$false;reason='Independent review identified empty .git marker skipped by current native loader';preserved=$true})
[IO.File]::WriteAllText(($b+'/final-02/summary.json'),($s|ConvertTo-Json -Depth 15),[Text.UTF8Encoding]::new($false))
$f=[ordered]@{schema='researchos.product-v1-freeze-marker.v1';state='AUTHOR_FROZEN';candidate=2;manifest='source-manifest.json';manifest_sha256=$manifestHash;summary='summary.json';diagnostics='../diagnostics-02.json';source_changes_stopped=$true;source_count=18;previous_candidate_preserved=$true;independent_review='PENDING';product_acceptance_increment=0}
[IO.File]::WriteAllText(($b+'/final-02/freeze.json'),($f|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
$index=[IO.File]::ReadAllText(($b+'/archive-index.ps1')).Replace("($b+'/final')","($b+'/final')")
$index=[IO.File]::ReadAllText(($b+'/archive-index.ps1')).Replace("foreach($i in 1..5)","foreach($i in @(1,2,3,4,5,7))")
$index=[IO.File]::ReadAllText(($b+'/archive-index.ps1')).Replace('foreach($i in 1..5)','foreach($i in @(1,2,3,4,5,7))').Replace('archive-file-list.json','archive-file-list-02.json').Replace("($b+'/final')","($b+'/final')")
# Explicitly enumerate both immutable snapshots, scripts and top-level result files only.
$files=@(Get-ChildItem -LiteralPath $b -File|Where-Object{$_.Extension -in @('.json','.ps1') -and $_.Name -ne 'archive-file-list-02.json'})
$files+=@(Get-ChildItem -LiteralPath ($b+'/final') -File -Recurse)
$files+=@(Get-ChildItem -LiteralPath ($b+'/final-02') -File -Recurse)
foreach($i in @(1,2,3,4,5,7)){$files+=@(Get-ChildItem -LiteralPath ($b+'/attempt-'+$i.ToString('00')) -File)}
$files+=@(Get-ChildItem -LiteralPath ($b+'/attempt-06-compatibility') -File)
$rows=@($files|Sort-Object FullName -Unique|ForEach-Object{[ordered]@{relative_path=[IO.Path]::GetRelativePath($b,$_.FullName).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant();bytes=$_.Length}})
$totalBytes=0L;foreach($row in $rows){$totalBytes+=[int64]$row['bytes']}
$index=[ordered]@{schema='researchos.product-v1-archive-file-list.v1';candidate=2;base_directory=$b;excluded=@('**/gocache/**','**/tmp/**','module cache','temporary helper executables');original_c_preserved=$true;total_bytes=$totalBytes;files=$rows}
[IO.File]::WriteAllText(($b+'/archive-file-list-02.json'),($index|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
@('final-02/freeze.json','final-02/summary.json','diagnostics-02.json','final-02/source-manifest.json','archive-file-list-02.json')|ForEach-Object{[ordered]@{path=$_;sha256=(Get-FileHash -LiteralPath ($b+'/'+$_) -Algorithm SHA256).Hash.ToLowerInvariant()}}|ConvertTo-Json -Depth 4
