$ErrorActionPreference='Stop'
$base='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/prepared_abandonment_v4_independent_review_codex/839da8e0a9014ebd91b3fc57c4e1502c'
$utf8=New-Object System.Text.UTF8Encoding($false)
function Ref([string]$p){$f=Get-Item -LiteralPath $p;[ordered]@{path=$f.FullName;bytes=$f.Length;sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}}
function WriteJson([string]$name,$value){[IO.File]::WriteAllText("$base/$name",(($value|ConvertTo-Json -Depth 100)+"`n"),$utf8)}
$sp=Get-Content -LiteralPath "$base/inspected-source-pins.json" -Raw -Encoding UTF8|ConvertFrom-Json
$ap=Get-Content -LiteralPath "$base/actual-component-intake.json" -Raw -Encoding UTF8|ConvertFrom-Json
foreach($ref in @($sp.pins)+@($ap.verified_refs)){$a=Ref $ref.path;if($a.bytes -ne $ref.bytes -or $a.sha256 -ne $ref.sha256){throw "INPUT_DRIFT $($ref.path)"}}
$members=[ordered]@{}
foreach($name in @('review.json','inspected-source-pins.json','review-tool-io.json','verify-source.ps1','verify-actual.ps1','actual-component-intake.json','root-original-tool-io.json','seal-review.ps1')){$members[$name]=Ref "$base/$name"}
WriteJson 'MF.json' ([ordered]@{schema='researchos.prepared-abandonment-v4-review-manifest.v1';actor_id='codex:/root/w05_merge_review';member_count=$members.Count;members=$members;metadata_excluded=@('HDF.json','MF.json');formal_acceptance=$false;execution_authority=$false})
WriteJson 'HDF.json' ([ordered]@{schema='researchos.prepared-abandonment-v4-review-handoff.v1';actor_id='codex:/root/w05_merge_review';decision='READY_SOURCE_AND_ACTUAL_FIXTURE_SUITE_ONLY';component_ready=$true;formal_acceptance=$false;execution_authority=$false;production_ready=$false;review=$members['review.json'];manifest=(Ref "$base/MF.json");actual_intake=$members['actual-component-intake.json'];source_unique_pin_count=48;actual_unique_pin_count=72;go_leaf_cases=36;checker_only_leaf_cases=5;top_level_operation_leaf_cases=31;all_selected_passed=$true;full_prepared_abandonment_suite=$true;full_domain_regression=$false;backup_regression=$false;remaining='Production native authority factory OPEN; populated23-to24 migration UNAUTHORIZED. Old trial provider requests remain null. No new trial or formal acceptance.';reviewer_new_failures=0;stopped=$true})
foreach($name in $members.Keys){$a=Ref "$base/$name";if($a.bytes -ne $members[$name].bytes -or $a.sha256 -ne $members[$name].sha256){throw "MEMBER_DRIFT $name"}}
[ordered]@{verified_members=$members.Count;source_refs=48;actual_refs=72;HDF=(Ref "$base/HDF.json");MF=(Ref "$base/MF.json");review=(Ref "$base/review.json");actual=(Ref "$base/actual-component-intake.json")} | ConvertTo-Json -Depth 10

