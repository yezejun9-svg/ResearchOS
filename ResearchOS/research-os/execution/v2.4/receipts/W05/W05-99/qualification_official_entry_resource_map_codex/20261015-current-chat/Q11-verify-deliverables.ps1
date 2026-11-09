$own=$PSScriptRoot
$root='D:/作品集/ResearchOS/research-os'
$scopePath=Join-Path $root 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp518/official-entry-readonly-resource-scope.json'
$scope=Get-Content -LiteralPath $scopePath -Raw|ConvertFrom-Json
if((Get-FileHash -LiteralPath $scopePath -Algorithm SHA256).Hash.ToLower() -ne 'eeac5e55ab5df7a60c5361095bd48d50a382cf666888c878f09092ea5751bb9d'){throw 'CP518_SCOPE_DRIFT'}
foreach($i in $scope.inputs){if((Get-FileHash -LiteralPath (Join-Path $root $i.path) -Algorithm SHA256).Hash.ToLower() -ne $i.sha256){throw ('INPUT_DRIFT '+$i.path)}}
$map=Get-Content -LiteralPath (Join-Path $own 'officialsurfaces.json') -Raw|ConvertFrom-Json
$meta=Get-Content -LiteralPath (Join-Path $own 'file-ancestor-metadata.json') -Raw|ConvertFrom-Json
$members=Get-Content -LiteralPath (Join-Path $own 'package-member-hashes.json') -Raw|ConvertFrom-Json
$register=Get-Content -LiteralPath (Join-Path $own 'checked-registrations.json') -Raw|ConvertFrom-Json
if($map.actual_authority -or $map.source_C_authority -or $map.formal_increment -ne 0 -or $map.full_coverage_claim -or $map.native_fence_claim){throw 'AUTHORITY_OR_CLAIM_DRIFT'}
if($meta.records.Count -ne 67 -or $members.Count -ne 116){throw 'RESOURCE_COUNT_DRIFT'}
if(@($meta.records|Where-Object {$_.kind -eq 'ACTUAL_DATA_METADATA_ONLY' -and $null -ne $_.sha256}).Count -ne 0){throw 'DATA_HASH_FORBIDDEN'}
foreach($s in @($map.surfaces|Where-Object {$_.id -in @('S01','S02','S03','S04')})){foreach($p in $s.mandatory_product_files){$norm=$p.Replace('/','\');if(-not @($meta.records|Where-Object {$_.path -eq $norm -and $_.sha256}).Count){throw ('MISSING_MAPPED_TARGET '+$p)}}}
$commands=@(Get-ChildItem -LiteralPath $own -Filter '*.command.json' -File)
$logGaps=@()
foreach($c in $commands){
 $group=$c.Name.Replace('.command.json','')
 foreach($suffix in @('.fullraw.txt','.result.json')){if(-not(Test-Path -LiteralPath (Join-Path $own ($group+$suffix)))){$logGaps+=($group+$suffix)}}
}
$allowedCurrentGroupGaps=@('Q11.fullraw.txt','Q11.result.json')
$unexpected=@($logGaps|Where-Object {$_ -notin $allowedCurrentGroupGaps})
if($unexpected.Count){throw ('MISSING_LOGS '+($unexpected -join ','))}
foreach($f in Get-ChildItem -LiteralPath $own -Filter '*.json' -File){Get-Content -LiteralPath $f.FullName -Raw|ConvertFrom-Json|Out-Null}
$summary=@{schema='researchos.CP518.static-artifact-validation.v1';status='STATIC_INTEGRITY_OK_NOT_SOURCE_NATIVE_ACCEPTANCE';input_hashes_reverified=4;scope_hash_reverified=$true;surfaces=$map.surfaces.Count;file_ancestor_records=67;public_package_files=116;registration_scope_records=$register.records.Count;registration_read_errors=$register.gaps.Count;current_group_pending_logs=$logGaps;unexpected_log_gaps=0;actual_authority=$false;source_C_authority=$false;formal_increment=0}
$summary|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $own 'static-integrity.json') -Encoding utf8
$summary|ConvertTo-Json -Depth 10

