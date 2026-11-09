$ErrorActionPreference='Stop'
$auditRoot=$PSScriptRoot
$repo='D:\作品集\ResearchOS\research-os'
$scopePath=Join-Path $repo 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp506/stop-anchor-independent-design-review-scope.json'
$scopeHash=(Get-FileHash -LiteralPath $scopePath -Algorithm SHA256).Hash.ToLowerInvariant()
if($scopeHash -ne '4e6df8550087d4fdf0ae8294ecba3a0a7d788e132a5316409b05af4421ed5802'){throw 'Scope drift'}
$scope=Get-Content -LiteralPath $scopePath -Raw | ConvertFrom-Json
$verified=@()
foreach($ref in $scope.input_refs) {
  $path=Join-Path $repo $ref.path
  $observed=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
  $bytes=(Get-Item -LiteralPath $path).Length
  if($observed -ne $ref.sha256 -or $bytes -ne $ref.bytes){throw "Input drift: $path"}
  $verified+=@{path=$ref.path;sha256=$observed;bytes=$bytes;match=$true}
}
$oldScopePath=Join-Path $repo $scope.input_refs[5].path
$oldScope=Get-Content -LiteralPath $oldScopePath -Raw | ConvertFrom-Json
$allowed=@($oldScope.production_new_allowed)+@($oldScope.tests_new_allowed)
$review=Get-Content -LiteralPath (Join-Path $auditRoot 'review.json') -Raw | ConvertFrom-Json
$requested=@($review.paths_sufficient.anchor_subset_production)+@($review.paths_sufficient.anchor_subset_tests)+@($review.paths_sufficient.existing19_native_support_if_needed)
foreach($p in $requested){if($p -notin $allowed){throw "Scope violation: $p"}}
$raw=@{scope_sha256=$scopeHash;verified_inputs=$verified;existing_allowed_count=$allowed.Count;requested_path_count=$requested.Count;all_paths_allowed=$true;formal_increment=$review.preserved.formal_increment}
$raw | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $auditRoot '005-final-verify-raw.json') -Encoding utf8
@{native_exit=0;errors=@();checks='All six input hashes/lengths and requested Source/test paths match; no Source or runtime action executed'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $auditRoot '005-final-verify-status.json') -Encoding utf8
$excluded=@('FINAL-manifest.json','FINAL-SHA256.txt','005-freeze-tool-result.json')
$entries=@()
foreach($item in (Get-ChildItem -LiteralPath $auditRoot -File | Sort-Object Name)) {
  if($item.Name -in $excluded){continue}
  $entries+=@{path=$item.Name;bytes=$item.Length;sha256=(Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
}
$manifest=@{schema='researchos.stop-anchor-design-independent-review-manifest.v1';owner='codex:/root/stop_anchor_design_review';status=$review.verdict;scope_sha256=$scopeHash;files=$entries;excluded_self_and_detached_envelopes=$excluded;source_accepted=$false;actual_authorized=$false;formal_increment=0}
$manifestPath=Join-Path $auditRoot 'FINAL-manifest.json'
$manifest | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $manifestPath -Encoding utf8
$manifestHash=(Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()
"$manifestHash  FINAL-manifest.json" | Set-Content -LiteralPath (Join-Path $auditRoot 'FINAL-SHA256.txt') -Encoding ascii
$reviewHash=(Get-FileHash -LiteralPath (Join-Path $auditRoot 'review.json') -Algorithm SHA256).Hash.ToLowerInvariant()
$mdHash=(Get-FileHash -LiteralPath (Join-Path $auditRoot 'review.md') -Algorithm SHA256).Hash.ToLowerInvariant()
@{manifest_sha256=$manifestHash;review_json_sha256=$reviewHash;review_md_sha256=$mdHash;input_hash_matches=$verified.Count;scope_path_count=$allowed.Count;native_exit=0;formal_increment=0} | ConvertTo-Json
exit 0

