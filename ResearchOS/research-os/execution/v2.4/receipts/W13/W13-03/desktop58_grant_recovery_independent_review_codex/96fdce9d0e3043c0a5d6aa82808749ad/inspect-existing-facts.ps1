$ErrorActionPreference='Stop'
$r='D:\作品集\ResearchOS\research-os'
$reg=Join-Path $r 'execution\v2.4\receipts\W05\W05-99\integration_codex\desktop58-finite169-go3-r339-9eccde97a9fa4815941768cacaf590dc'
$s=Get-Content -Raw -LiteralPath (Join-Path $reg 'scope_registration.json')|ConvertFrom-Json
$au=$s.new_authorization_root
$pf=$s.new_grant_preflight_root
$checks=[Collections.Generic.List[object]]::new()
$pins=[Collections.Generic.List[object]]::new()
function Check($name,$ok,$detail) { $checks.Add([ordered]@{name=$name;pass=[bool]$ok;detail=$detail}) }
function Pin($path) { if(-not [IO.Path]::IsPathRooted($path)){$path=Join-Path $r $path}; $fi=Get-Item -LiteralPath $path; $v=[ordered]@{path=$fi.FullName;sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower();bytes=$fi.Length};$pins.Add($v);return $v }
function Ref($ref,$name) { $v=Pin $ref.path;Check $name (($v.sha256 -ceq $ref.sha256)-and($v.bytes -eq $ref.bytes)) $v;return $v }
function Doc($path) { Get-Content -Raw -LiteralPath $path|ConvertFrom-Json }
$g=Doc (Join-Path $au 'authorization.execute.json')
$null=Pin (Join-Path $au 'authorization.execute.json')
$null=Ref $g.scope_ref 'grant.scope'
$cm=Doc (Join-Path $au 'preflight-copy-map.json')
$null=Pin (Join-Path $au 'preflight-copy-map.json')
$copiedNames=@()
foreach($e in $cm.entries) {
 $a=Ref $e.original_ref ('copy.original.'+[IO.Path]::GetFileName($e.original_ref.path))
 $b=Ref $e.copy_ref ('copy.destination.'+[IO.Path]::GetFileName($e.copy_ref.path))
 Check ('copy.equal.'+[IO.Path]::GetFileName($e.original_ref.path)) (($a.sha256 -ceq $b.sha256)-and($a.bytes -eq $b.bytes)-and([IO.Path]::GetDirectoryName($a.path)-eq $pf)-and([IO.Path]::GetDirectoryName($b.path)-eq $au)) $null
 $copiedNames += [IO.Path]::GetFileName($e.original_ref.path)
}
$pfNames=@(Get-ChildItem -LiteralPath $pf -File|ForEach-Object Name)
Check 'copy.exact.PF.membership' (@(Compare-Object ($copiedNames|Sort-Object) ($pfNames|Sort-Object)).Count -eq 0) @{copies=$copiedNames.Count;files=$pfNames.Count}
$auNames=@(Get-ChildItem -LiteralPath $au -File|ForEach-Object Name)
$expectedAu=@($copiedNames)+@('authorization.execute.json','preflight-copy-map.json')
Check 'copy.exact.AUTH.membership' (@(Compare-Object ($expectedAu|Sort-Object) ($auNames|Sort-Object)).Count -eq 0) @{expected=$expectedAu.Count;files=$auNames.Count}
foreach($c in $g.canonical_copies) {
 $a=Ref $c.ref ('canon.copy.'+$c.canonical_path)
 $b=Pin $c.canonical_path
 Check ('canon.live.'+$c.canonical_path) (($a.sha256 -ceq $b.sha256)-and($a.bytes -eq $b.bytes)) $b
}
foreach($k in @('output_root','outer_output_root','export_root')) {Check ('absent.'+$k) (-not(Test-Path -LiteralPath $s.$k)) $s.$k}
foreach($p in @((Join-Path $au 'grant.completed.json'),(Join-Path $au 'manifest.json'),(Join-Path $pf 'manifest.json'))) {Check ('missing.tail.'+$p) (-not(Test-Path -LiteralPath $p)) $null}
$jobs=@()
foreach($phase in @('admission','grant-final')) {
 $tw=Doc (Join-Path $pf ($phase+'.time-window.json'))
 Check ($phase+'.parent.null') (($null -eq $tw.actual_stage_native_exit)-and($null -eq $tw.error)-and $tw.point_in_time_only) $null
 foreach($kind in @('head','status','index')){
  $iv=Doc (Join-Path $pf ($phase+'.'+$kind+'.invocation.json'))
  $null=Pin (Join-Path $pf ($phase+'.'+$kind+'.invocation.json'))
  $job=$iv.result
  $cl=$job.job_cleanup
  $ok=($job.actual_exit -eq 0)-and($iv.actual_stage_native_exit -eq 0)-and($null -eq $iv.wrapper_error)-and($null -eq $job.error)-and($job.timed_out -eq $false)-and($job.resumed -eq $true)-and($cl.errors.Count -eq 0)-and($cl.active_processes_last_observed -eq 0)-and($job.creation_time_100ns -is [long])
  foreach($flag in @('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed')) {$ok=$ok -and ($cl.$flag -eq $true)}
  Check ($phase+'.'+$kind+'.job') $ok @{pid=$job.owned_child_pid;creation_time_100ns=$job.creation_time_100ns}
  $o=Ref $iv.stdout_ref ($phase+'.'+$kind+'.stdout')
  $e=Ref $iv.stderr_ref ($phase+'.'+$kind+'.stderr')
  Check ($phase+'.'+$kind+'.stderr.empty') ($e.bytes -eq 0) $null
  if($kind -eq 'head'){Check ($phase+'.head.value') (([IO.File]::ReadAllText($o.path).Trim()) -ceq $s.main_git.head) $null}
  if($kind -eq 'status'){Check ($phase+'.status.value') (($o.sha256 -ceq $s.main_git.status_sha256)-and($o.bytes -eq $s.main_git.status_bytes)) $null}
  if($kind -eq 'index'){Check ($phase+'.index.value') ($o.bytes -eq 0) $null}
  $jobs += @{phase=$phase;kind=$kind;result=$job}
 }
}
$m=Doc (Join-Path $reg 'manifest.json')
foreach($e in $m.entries){$null=Ref $e ('registry.'+[IO.Path]::GetFileName($e.path))}
Check 'registry.declared.count' (($m.count -eq 123)-and($m.entries.Count -eq 123)-and $m.excluded_only_self) $null
$sealedNames=@($m.entries|ForEach-Object{[IO.Path]::GetFileName($_.path)})
$diskNames=@(Get-ChildItem -LiteralPath $reg -File|Where-Object Name -ne 'manifest.json'|ForEach-Object Name)
$diff=@(Compare-Object $sealedNames $diskNames)
$observations=@()
foreach($o in $g.runtime_observation_refs){$null=Ref $o ('runtime.'+[IO.Path]::GetFileName($o.path));$observations += $o}
$report=[ordered]@{schema='researchos.desktop58-grant-recovery-independent-disk-assessment.v1';reviewer='codex:/root/w05_merge_review';at=[DateTime]::UtcNow.ToString('o');checks=$checks;check_count=$checks.Count;failed=@($checks|Where-Object{-not $_.pass});pins=$pins;jobs=$jobs;runtime_observations=$observations;registry_membership_changes_since_manifest=$diff;original_outer_exit=$null;original_python_exit=$null;original_native_exit=$null;candidate_executions=0;canonical_writes=0;grant_tail_writes=0}
$out='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_grant_recovery_independent_review_codex/96fdce9d0e3043c0a5d6aa82808749ad/disk-assessment.json'
$raw=[Text.UTF8Encoding]::new($false).GetBytes(($report|ConvertTo-Json -Depth 30)+"`n")
$stream=[IO.File]::Open($out,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
try{$stream.Write($raw,0,$raw.Length)}finally{$stream.Dispose()}
[ordered]@{path=$out;sha256=(Get-FileHash -LiteralPath $out -Algorithm SHA256).Hash.ToLower();bytes=$raw.Length;check_count=$checks.Count;failed=@($checks|Where-Object{-not $_.pass});registry_membership_changes=$diff;copy_count=$cm.entries.Count;PF_file_count=$pfNames.Count;AUTH_file_count=$auNames.Count}|ConvertTo-Json -Depth 10
