$ErrorActionPreference='Stop'
$root='D:/作品集/ResearchOS/research-os'
$own=Join-Path $root 'execution/v2.4/receipts/W05/W05-99/qualification_recovery_boot_supplement_architecture_codex/20261015-current-chat'
@{group=6;recipe='Run own seal-deliverables.ps1: verify frozen input hashes, exact C51 plus six equality, JSON and file existence; hash own deliverables';shell='PowerShell';cwd=(Get-Location).Path;ps_version=$PSVersionTable.PSVersion.ToString();actual_authority=$false;formal_increment=0} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $own 'G06-command.json') -Encoding utf8
$raw = & {
 $scopePath=Join-Path $root 'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp517-retry02/qualification-boot-supplement-design-scope.json'
 $scope=Get-Content -LiteralPath $scopePath -Raw|ConvertFrom-Json
 foreach($i in $scope.inputs){$h=(Get-FileHash -LiteralPath (Join-Path $root $i.path) -Algorithm SHA256).Hash.ToLower();if($h -ne $i.sha256){throw ('INPUT_DRIFT '+$i.path)};'INPUT_MATCH '+$i.path}
 $leasePath=Join-Path $root 'execution/v2.4/receipts/W05/W05-99/qualification_failure_revision03_architecture_codex/20261015-current-chat/C-lease-exact-scope.json'
 if((Get-FileHash -LiteralPath $leasePath -Algorithm SHA256).Hash.ToLower() -ne 'ef69f8dcd63578f3692439b95f5ba21c155aeb75bc362bc9a52c65f4352f78b3'){throw 'C51 drift'}
 $prior=Get-Content -LiteralPath $leasePath -Raw|ConvertFrom-Json
 $new=Get-Content -LiteralPath (Join-Path $own 'C-boot-exact-scope.json') -Raw|ConvertFrom-Json
 foreach($k in @('production_existing','production_new','tests_allowed')){if((ConvertTo-Json -Compress @($prior.$k)) -ne (ConvertTo-Json -Compress @($new.original_C51.$k))){throw ('C51 mismatch '+$k)}}
 $all=@($new.original_C51.production_existing)+@($new.original_C51.production_new)+@($new.original_C51.tests_allowed)+@($new.boot_six_paths.production_new)+@($new.boot_six_paths.tests_new)
 if($all.Count -ne 57 -or @($all | Sort-Object -Unique).Count -ne 57){throw 'Not exact unique57'}
 if($new.actual_authority -or $new.source_edit_authority -or $new.source_card_issuable_now -or $new.formal_increment -ne 0){throw 'Authority drift'}
 $cuts=Get-Content -LiteralPath (Join-Path $own 'C-boot-test-cuts.json') -Raw|ConvertFrom-Json
 if($cuts.cuts.Count -ne 28 -or $cuts.counts.executed -ne 0){throw 'Cut count drift'}
 foreach($cut in $cuts.cuts){if($null -ne $cut.path -and $cut.path -notin $all){throw ('Cut path outside scope '+$cut.id)}}
 foreach($f in Get-ChildItem -LiteralPath $own -Filter '*.json' -File){Get-Content -LiteralPath $f.FullName -Raw|ConvertFrom-Json|Out-Null}
 'STATIC_INTEGRITY_OK: C51 exact +6 =57 unique; 28 planned cuts / 0 executed; authority false/formal0'
}
$rawText=$raw|Out-String -Width 240
[IO.File]::WriteAllText((Join-Path $own 'G06-fullraw.txt'),$rawText)
@{group=6;exit_code=0;native_exit_code=$null;result='STATIC_ARTIFACT_INTEGRITY_OK_NOT_SOURCE_TEST';raw='G06-fullraw.txt'}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $own 'G06-result.json') -Encoding utf8
$files=@()
foreach($f in Get-ChildItem -LiteralPath $own -File | Sort-Object Name){if($f.Name -eq 'FINAL-manifest.json'){continue};$files+=@{path=$f.Name;bytes=$f.Length;sha256=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLower()}}
$manifest=[ordered]@{schema='researchos.CP517.C-boot-design-final.v1';owner='codex:/root/qualification_boot_design';model='gpt-6-astra';model_reason='Parent-selected architecture/security design agent; no author acceptance';status='FINITE_BLOCKED_NO_IMPLEMENTABLE_SOURCE_CARD_YET';mechanism='OFFICIAL_ENTRY_FILE_DACL_FENCE_V1';proposed_class='POST_RESTART_CURRENT_QUIESCENCE_V1';new_class_status='NOT_IMPLEMENTED_NOT_ACCEPTED';actual_authority=$false;source_edit_authority=$false;formal_increment=0;author_acceptance=$false;independent_design_review_required=$true;current_source_card_issuable=$false;query_groups_used=6;query_group_limit=12;initial_two_file_intake_outside_groups=$true;source_path_count=57;planned_test_cuts=28;tests_executed=0;source_edits=@();actual_operations=@();root_shared_state_edited=$false;B_candidate='75e5257c19b2e21e6cabd5e912e2ac6a3e2fe603';B_acceptance='NOT_ASSUMED_PENDING';scope_sha256='39d8c02342c6fcbdace902dcde81a4d6728661cfb97490289671ad8acd6a97f4';inputs=$scope.inputs;additional_inputs=@(@{path='execution/v2.4/receipts/W05/W05-99/qualification_failure_revision03_architecture_codex/20261015-current-chat/C-lease-exact-scope.json';sha256='ef69f8dcd63578f3692439b95f5ba21c155aeb75bc362bc9a52c65f4352f78b3'},@{path='execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp511/C-design-adopted-constraints.json';sha256='66df2cc54b7e9ef89db1976043171299f72fd02a6a25971c78b1a23d57dfcf6c'});resource_decision='One bounded readonly resource package can close this specific mechanism if every official launch has a frozen product-exclusive mandatory file and trusted management/restore is feasible; otherwise mechanism exits, no speculative loop';files=$files}
$manifest|ConvertTo-Json -Depth 30|Set-Content -LiteralPath (Join-Path $own 'FINAL-manifest.json') -Encoding utf8
$rawText
'FINAL_MANIFEST_SHA256='+(Get-FileHash -LiteralPath (Join-Path $own 'FINAL-manifest.json') -Algorithm SHA256).Hash.ToLower()

