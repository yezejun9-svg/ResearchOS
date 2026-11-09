$ErrorActionPreference='Stop'
$base='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/prepared_abandonment_schema_upgrade_independent_review_codex/cca15e02b36a4545b4218f1e9b7f472c'
$utf8=[Text.UTF8Encoding]::new($false)
function Ref([string]$p){$f=Get-Item -LiteralPath $p;[ordered]@{path=$f.FullName;bytes=$f.Length;sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}}
function WriteJson([string]$name,$value){if(Test-Path -LiteralPath "$base/$name"){throw "EXISTING_SEAL $name"};[IO.File]::WriteAllText("$base/$name",(($value|ConvertTo-Json -Depth 80)+[Environment]::NewLine),$utf8)}
$sp=Get-Content -LiteralPath "$base/inspected-source-pins.json" -Raw -Encoding UTF8|ConvertFrom-Json
foreach($ref in $sp.pins){$a=Ref $ref.path;if($a.bytes -ne $ref.bytes -or $a.sha256 -ne $ref.sha256){throw "INPUT_DRIFT $($ref.path)"}}
$members=[ordered]@{}
foreach($name in @('review.json','failure-origin.767.json','review-tool-io.json','inspected-source-pins.json','verify-source.ps1','seal-review.ps1')){$members[$name]=Ref "$base/$name"}
WriteJson 'MF.json' ([ordered]@{schema='researchos.prepared-abandonment-schema-upgrade-review-manifest.v1';actor_id='codex:/root/w05_merge_review';member_count=$members.Count;members=$members;metadata_excluded=@('HDF.json','MF.json');formal_acceptance=$false;execution_authority=$false})
WriteJson 'HDF.json' ([ordered]@{schema='researchos.prepared-abandonment-schema-upgrade-review-handoff.v1';actor_id='codex:/root/w05_merge_review';decision='READY_SOURCE_ONLY_PENDING_ROOT_ACTUAL_VALIDATION';manifest_ref=(Ref "$base/MF.json");review_ref=(Ref "$base/review.json");source_pins_ref=(Ref "$base/inspected-source-pins.json");failure_origins=@(767);source_unique_pins=73;findings=0;testing_executed=$false;native_executed=$false;sql_executed=$false;provider_requests=0;formal_acceptance=$false;execution_authority=$false;production_migration_authority=$false;root_actual_results_adopted=$false;stop=$true})
$mf=Get-Content -LiteralPath "$base/MF.json" -Raw -Encoding UTF8|ConvertFrom-Json
foreach($p in $mf.members.PSObject.Properties){$ref=$p.Value;$a=Ref $ref.path;if($a.bytes -ne $ref.bytes -or $a.sha256 -ne $ref.sha256){throw "OUTPUT_DRIFT $($ref.path)"}}
[ordered]@{hdf=(Ref "$base/HDF.json");mf=(Ref "$base/MF.json");review=(Ref "$base/review.json");failure767=(Ref "$base/failure-origin.767.json");member_count=$members.Count;input_count=@($sp.pins).Count;all_pins_verified=$true;go_executed=$false;native_executed=$false;sql_executed=$false;provider_requests=0}|ConvertTo-Json -Depth 12

