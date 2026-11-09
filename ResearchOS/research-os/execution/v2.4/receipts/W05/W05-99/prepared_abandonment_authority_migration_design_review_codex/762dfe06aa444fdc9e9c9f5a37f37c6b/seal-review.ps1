$ErrorActionPreference='Stop'
$base='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/prepared_abandonment_authority_migration_design_review_codex/762dfe06aa444fdc9e9c9f5a37f37c6b'
$repo='D:/作品集/ResearchOS/research-os'
$source="$repo/execution/v2.4/receipts/W05/W05-99/prepared_run_abandonment_source_v2_codex/a6777ff11e16424eb303721214730682"
$trial="$repo/execution/v2.4/receipts/W05/W05-99/integration_codex/root-model-trial-v5-870ecc93e109c85ee985e1566ff"
$utf8=New-Object System.Text.UTF8Encoding($false)
function Ref([string]$path) { $item=Get-Item -LiteralPath $path; [ordered]@{path=$item.FullName;bytes=$item.Length;sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()} }
function WriteJson([string]$name,$value) { [IO.File]::WriteAllText("$base/$name",(($value | ConvertTo-Json -Depth 100)+"`n"),$utf8) }
$mf=Get-Content -LiteralPath "$source/MF.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$verified=@()
foreach($p in $mf.members.PSObject.Properties) { $actual=Ref $p.Value.path; if($actual.sha256 -ne $p.Value.sha256 -or $actual.bytes -ne $p.Value.bytes){throw "SOURCE_PIN_MISMATCH $($p.Name)"};$verified+=$actual }
$main=@()
foreach($name in @('apps/control/main.go','adapters/runtime/data_root_windows.go','ops/supervisor/control_authority_windows.go','ops/supervisor/release_drain_windows.go','internal/host/native_pipe_windows.go','internal/domain/backup_upgrade.go','internal/domain/backup_configuration_upgrade.go','internal/domain/backup.go','internal/domain/backup_recovery.go')){$main+=Ref "$repo/$name"}
$historical=@()
foreach($name in @('root.execution-authority.actual.json','trial-output/host-job.contract.json','trial-output/host-job.probe.json','trial-output/root-coordinator.lifecycle.json','trial-output/whole-trial-clock.json','trial-output/host-go.once.json','trial-output/root-host-go.json','trial-output/host-execute-admitted.invocation.json','trial-output/host-admit-only.invocation.json')){$historical+=Ref "$trial/$name"}
WriteJson 'inspected-source-pins.json' ([ordered]@{schema='researchos.design-review-source-pins.v1';source_HDF=(Ref "$source/HDF.json");source_MF=(Ref "$source/MF.json");source_manifest_verified_count=$verified.Count;source_manifest_verified=$verified;main_source_snapshots=$main;historical_receipt_snapshots=$historical;limits='Snapshots are content pins, not retrospective origin signatures. Current private DB/accounting was not queried.'})
$members=[ordered]@{}
foreach($name in @('review.json','failure-origin.757.json','evidence-tool-io.json','inspected-source-pins.json','seal-review.ps1')){$members[$name]=Ref "$base/$name"}
WriteJson 'MF.json' ([ordered]@{schema='researchos.design-review-manifest.v1';actor_id='codex:/root/w05_merge_review';members=$members;member_count=$members.Count;metadata_files_excluded=@('HDF.json','MF.json');formal=$false;execution_authority=$false})
WriteJson 'HDF.json' ([ordered]@{schema='researchos.prepared-abandonment-authority-migration-design-handoff.v1';actor_id='codex:/root/w05_merge_review';decision='DESIGN_ONLY_PRODUCTION_AUTHORITY_AND_MIGRATION_OPEN';formal=$false;execution_authority=$false;production_ready=$false;revision_root=$base;review=$members['review.json'];failure_origin=$members['failure-origin.757.json'];manifest=(Ref "$base/MF.json");source_manifest_verified_count=$verified.Count;candidate_semantic_edits=0;existing_database_reads=0;go_native_model_runs=0;remaining='Implement and independently verify current Root plus OWNER historical adoption, private native capability, fixed23-to24 restored rehearsal plus original-root unchanged-row DDL. Separate production authorizations still required.'})
foreach($name in $members.Keys){$again=Ref "$base/$name";if($again.sha256 -ne $members[$name].sha256 -or $again.bytes -ne $members[$name].bytes){throw "MEMBER_CHANGED $name"}}
[ordered]@{verified_members=$members.Count;verified_source_members=$verified.Count;HDF=(Ref "$base/HDF.json");MF=(Ref "$base/MF.json");review=(Ref "$base/review.json");failure=(Ref "$base/failure-origin.757.json")} | ConvertTo-Json -Depth 10

