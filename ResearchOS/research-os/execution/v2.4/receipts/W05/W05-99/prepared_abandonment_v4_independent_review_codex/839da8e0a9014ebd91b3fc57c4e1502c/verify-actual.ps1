$ErrorActionPreference='Stop'
$base='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/prepared_abandonment_v4_independent_review_codex/839da8e0a9014ebd91b3fc57c4e1502c'
$root='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/prepared-abandonment-v4-validation-root-a6f0cc382b1c4d3f'
$utf8=New-Object System.Text.UTF8Encoding($false)
function Ref([string]$p){$f=Get-Item -LiteralPath $p;[ordered]@{path=$f.FullName;bytes=$f.Length;sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}}
$seen=@{}
function Check($r){$a=Ref $r.path;if($a.bytes -ne $r.bytes -or $a.sha256 -ne $r.sha256){throw "PIN_MISMATCH $($r.path)"};$seen[$a.path]=$a}
function Recurse($v){if($null -eq $v -or $v -is [string] -or $v -is [ValueType]){return};if($v -is [System.Collections.IEnumerable] -and $v -isnot [pscustomobject]){foreach($item in $v){Recurse $item};return};if($v.PSObject.Properties['path'] -and $v.PSObject.Properties['sha256'] -and $v.PSObject.Properties['bytes']){Check $v};foreach($prop in $v.PSObject.Properties){Recurse $prop.Value}}
Check ([pscustomobject]@{path="$root/validation.closed.json";bytes=4830;sha256='26fcba5d5cebd6d84a34d72ba0ce7bf67fb81a903f6e10afe928bcc4a629acbc'})
$documents=[ordered]@{}
foreach($name in @('validation.closed.json','format.invocation.json','test.invocation.json','formatted.source-members.json','input-source-guard.cleanup.actual.json','candidate-source-guard.cleanup.actual.json','original-tool-io.json')){$documents[$name]=Get-Content -LiteralPath "$root/$name" -Raw -Encoding UTF8 | ConvertFrom-Json;Recurse $documents[$name];$docRef=Ref "$root/$name";$seen[$docRef.path]=$docRef}
$closed=$documents['validation.closed.json']
if($closed.full_suite_executed -ne $true -or $closed.actual_native_exit -ne 0){throw 'ACTUAL_SCOPE_MISMATCH'}
$jobs=@()
foreach($name in @('format.invocation.json','test.invocation.json')){$d=$documents[$name];$c=$d.result.job_cleanup;if($d.actual_native_exit -ne 0 -or $d.result.actual_exit -ne 0 -or $d.result.timed_out -or $null -ne $d.result.error -or $null -ne $d.exception -or $c.errors.Count -ne 0 -or $c.active_processes_last_observed -ne 0){throw "JOB_RESULT $name"};foreach($field in @('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed')){if($c.$field -ne $true){throw "JOB_CLOSURE $name $field"}};$jobs+=[ordered]@{name=$name;pid=$d.result.owned_child_pid;creation_time_100ns=[string]$d.result.creation_time_100ns;actual_exit=$d.actual_native_exit;argv=$d.argv;closed=$true}}
$guards=@()
foreach($name in @('input-source-guard.cleanup.actual.json','candidate-source-guard.cleanup.actual.json')){$g=$documents[$name];if($g.verification -ne 'PASSED' -or !$g.closed -or $g.retained_handles_count -ne 0 -or $g.errors.Count -ne 0 -or $null -ne $g.failure){throw "GUARD $name"};foreach($e in $g.entries){if(!$e.verified -or !$e.closed -or !$e.final_path_match){throw "GUARD_ENTRY $name"}};$guards+=[ordered]@{name=$name;entries=$g.entries.Count;closed=$true}}
$events=@(Get-Content -LiteralPath "$root/test.stdout.raw" -Encoding UTF8 | Where-Object {$_ -match '^\{'} | ForEach-Object {$_ | ConvertFrom-Json})
$terminals=@($events | Where-Object {$_.Test -and $_.Action -in @('pass','fail','skip')})
if($terminals.Count -ne 40 -or @($terminals | Where-Object {$_.Action -ne 'pass'}).Count -ne 0 -or @($events | Where-Object {!$_.Test -and $_.Action -eq 'pass'}).Count -ne 1){throw 'GO_EVENT_MISMATCH'}
$leaves=@($terminals | Where-Object {$_.Test -match '/' -or $_.Test -eq 'TestPreparedRunAbandonmentSuccessAndIdempotency'})
if($leaves.Count -ne 36 -or @($terminals | Where-Object {$_.Test -like '*RejectsPreparationUploadAndPins/*'}).Count -ne 7 -or @($terminals | Where-Object {$_.Test -like '*ProfileCheckerRejectsMemoryManifestPins/*'}).Count -ne 5){throw 'GO_CASE_SCOPE'}
if($documents['test.invocation.json'].argv[-1] -ne '^TestPreparedRunAbandonment'){throw 'ACTUAL_PATTERN'}
$io=$documents['original-tool-io.json']
if($io.actual_outer_exit -ne 0 -or $io.actual_python_exit -ne 0 -or $io.original_poll_result.exit_code -ne 0 -or $io.full_suite_executed -ne $true){throw 'ROOT_ORIGINAL_IO_SCOPE'}
[IO.File]::WriteAllBytes("$base/root-original-tool-io.json",[IO.File]::ReadAllBytes("$root/original-tool-io.json"))
$summary=[ordered]@{schema='researchos.prepared-abandonment-v4-actual-review.v1';decision='READY_SOURCE_AND_ACTUAL_FIXTURE_SUITE_ONLY';verified_ref_count=$seen.Count;verified_refs=@($seen.Values);root_original_io=(Ref "$root/original-tool-io.json");local_original_io=(Ref "$base/root-original-tool-io.json");jobs=$jobs;guards=$guards;go_test_nodes=$terminals.Count;go_leaf_cases=$leaves.Count;test_actions=@($terminals | Select-Object Test,Action);full_suite_executed=$true;new_profile_cases_executed=12;checker_only_cases=5;top_level_profile_cases=7;actual_outer_exit=0;actual_python_exit=0;native_exit=0;fixture_provider_requests=0;old_trial_provider_requests=$null;production_authority=$false;formal_acceptance=$false}
[IO.File]::WriteAllText("$base/actual-component-intake.json",(($summary|ConvertTo-Json -Depth 100)+"`n"),$utf8)
[ordered]@{verified_refs=$seen.Count;go_test_nodes=40;go_leaf_cases=36;jobs=$jobs;guards=$guards;actual_review=(Ref "$base/actual-component-intake.json");root_io=(Ref "$base/root-original-tool-io.json")} | ConvertTo-Json -Depth 10



