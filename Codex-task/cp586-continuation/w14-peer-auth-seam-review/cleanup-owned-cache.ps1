param([Parameter(Mandatory=$true)][string]$ReceiptRoot)
$ErrorActionPreference='Stop'
$workspace='C:\Users\yqyyds\Documents\Codex\2026-11-04\task'
$reviewRoot=Join-Path $workspace 'cp586-continuation\w14-peer-auth-seam-review'
$bindingRoot=Join-Path $workspace 'cp586-continuation\production-binding-review'
$cache=[IO.Path]::GetFullPath((Join-Path $bindingRoot 'run-01\private\go-cache'))
$modules=Join-Path $bindingRoot 'run-01\private\gopath\pkg\mod'
$receipt=[IO.Path]::GetFullPath($ReceiptRoot)
$archiveManifest=Join-Path $receipt 'archive-manifest.json'
$archiveHash=(Get-FileHash -LiteralPath $archiveManifest -Algorithm SHA256).Hash.ToLowerInvariant()
if($archiveHash -ne 'f33db8b3006178ceb05a0513abff0f23c2f225b0be06c9237c746663f0f8dab8'){throw 'Independent archive must be intact before cache cleanup.'}
if(-not $cache.StartsWith(([IO.Path]::GetFullPath($bindingRoot)+'\'),[StringComparison]::OrdinalIgnoreCase)){throw 'Cache path escaped owned review root.'}
if(-not $cache.EndsWith('\run-01\private\go-cache',[StringComparison]::OrdinalIgnoreCase)){throw 'Only the exact approved build cache is eligible.'}
if(-not (Test-Path -LiteralPath $modules -PathType Container)){throw 'Preserved module input directory is missing.'}
$processes=@(Get-CimInstance Win32_Process | Where-Object {$_.Name -match '^(go|compile|link|vet|domain\.test|api\.test|host\.test)\.exe$'} | Select-Object ProcessId,Name)
function Write-NewJson([string]$Path,$Value){
 $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($Value|ConvertTo-Json -Depth 15)+"`n")
 $stream=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
 try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
}
if($processes.Count -ne 0){
 $blocked=[ordered]@{status='BLOCKED_GO_OR_TEST_PROCESS_PRESENT_NO_DELETE';processes=$processes;cache=$cache;archive_sha256=$archiveHash;counter_reset=$false}
 Write-NewJson (Join-Path $reviewRoot 'cache-cleanup-blocked.json') $blocked
 $blocked|ConvertTo-Json -Depth 5
 exit 2
}
$resolved=(Resolve-Path -LiteralPath $cache).ProviderPath
if(-not [string]::Equals($resolved,$cache,[StringComparison]::OrdinalIgnoreCase)){throw 'Resolved target differs from the exact approved cache.'}
$ancestor=$resolved
while($ancestor.StartsWith($workspace,[StringComparison]::OrdinalIgnoreCase)){
 $item=Get-Item -Force -LiteralPath $ancestor
 if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'Reparse-point cache ancestry refused.'}
 if([string]::Equals($ancestor,$workspace,[StringComparison]::OrdinalIgnoreCase)){break}
 $ancestor=[IO.Path]::GetDirectoryName($ancestor)
}
$all=@(Get-ChildItem -LiteralPath $resolved -Recurse -Force -File)
if(@($all|Where-Object {$_.Extension -eq '.exe'}).Count -ne 0){throw 'Named executable evidence unexpectedly exists in cache; no deletion.'}
$inventory=@($all|ForEach-Object {[ordered]@{relative_path=$_.FullName.Substring($resolved.Length).TrimStart('\');bytes=$_.Length}})
$cacheBytes=[long](($all|Measure-Object -Property Length -Sum).Sum)
$freeBefore=[long](Get-PSDrive -Name C).Free
$preserve=@{}
foreach($path in @((Join-Path $bindingRoot 'run-01\offline-dependency-copy.json'),(Join-Path $bindingRoot 'source-review.json'),(Join-Path $reviewRoot 'run-01\result.json'),$archiveManifest)){
 $preserve[$path]=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
}
$before=[ordered]@{status='OWNED_REGENERABLE_CACHE_DELETE_PREPARED';utc=[DateTime]::UtcNow.ToString('o');target=$resolved;owned_review_root=$bindingRoot;workspace=$workspace;processes=$processes;archive_sha256=$archiveHash;file_count=$all.Count;file_bytes=$cacheBytes;free_before_bytes=$freeBefore;preserved_module_input_root=$modules;preserved_evidence_sha256=$preserve;file_inventory=$inventory;counter_reset=$false}
Write-NewJson (Join-Path $reviewRoot 'cache-cleanup-before.json') $before
Write-NewJson (Join-Path $receipt 'cache-cleanup-before.json') $before
# One shell, one exact verified LiteralPath; never remove module/tmp/source/log roots.
Remove-Item -LiteralPath $resolved -Recurse -Force
if(Test-Path -LiteralPath $resolved){throw 'Cache removal did not reach an absent terminal state.'}
if(-not (Test-Path -LiteralPath $modules -PathType Container)){throw 'Module input directory was not preserved.'}
foreach($path in $preserve.Keys){if((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $preserve[$path]){throw 'Preserved evidence hash changed during cleanup.'}}
$freeAfter=[long](Get-PSDrive -Name C).Free
$after=[ordered]@{status='OWNED_BUILD_CACHE_REMOVED_EVIDENCE_AND_MODULE_INPUTS_PRESERVED';utc=[DateTime]::UtcNow.ToString('o');target=$resolved;target_absent=$true;processes_before=$processes;removed_file_count=$all.Count;removed_file_bytes=$cacheBytes;free_before_bytes=$freeBefore;free_after_bytes=$freeAfter;free_after_gib=[Math]::Round($freeAfter/1GB,4);minimum_12gib_met=($freeAfter -ge 12GB);module_input_root_preserved=$modules;preserved_evidence_sha256=$preserve;raw_source_inputs_results_archived_before_delete=$true;other_directories_deleted=@();counter_reset=$false}
Write-NewJson (Join-Path $reviewRoot 'cache-cleanup-result.json') $after
Write-NewJson (Join-Path $receipt 'cache-cleanup-result.json') $after
$after|ConvertTo-Json -Depth 6
