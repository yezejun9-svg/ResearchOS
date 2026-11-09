$ErrorActionPreference = 'Stop'
$E = 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/original_backup_process_binding_codex/20261015-current-chat'
$base = 'D:/作品集/ResearchOS/research-os'
$src = "$base/.local/worktrees/online-backup-fixture-qualification-20261015"
$package = 'C:/Users/yqyyds/.codex/researchos-resource-cache/normal-verifier-replacement-4f4023-20261015'
function Hash([string]$p) { $s=[IO.File]::OpenRead($p); try {$h=[Security.Cryptography.SHA256]::Create(); return [BitConverter]::ToString($h.ComputeHash($s)).Replace('-','').ToLowerInvariant()} finally {$s.Dispose()} }
function Lines([string]$p,[int]$first,[int]$last) {$ls=[IO.File]::ReadAllLines($p); $out=@(); for($i=$first;$i -le [Math]::Min($last,$ls.Length);$i++){$out += ('{0}:{1}' -f $i,$ls[$i-1])}; return $out}
function SelectIdentity($node,[string]$trail,[int]$depth) {
 if ($null -eq $node -or $depth -gt 10) { return }
 if ($node -is [string] -or $node -is [ValueType]) { return }
 if ($node -is [array]) { $j=0; foreach($n in $node) { SelectIdentity $n "$trail[$j]" ($depth+1); $j++ }; return }
 foreach($p in $node.PSObject.Properties) {
  if($p.Name -match '(?i)commandline|arguments|argv|env|token|secret|credential|config|payload|content') {continue}
  if($p.Name -match '(?i)^(pid|process_?id|parent_?pid|parent_?process_?id|creation_?date|creation_?time|created_?at|start_?time|executable_?path|image_?path|process_?name|name|sha256|path)$' -and ($p.Value -is [string] -or $p.Value -is [ValueType])) {
    [ordered]@{key="$trail.$($p.Name)";value=$p.Value}
  } elseif($p.Value -is [array] -or $p.Value -is [pscustomobject]) { SelectIdentity $p.Value "$trail.$($p.Name)" ($depth+1) }
 }
}
$result=[ordered]@{at=[DateTime]::UtcNow.ToString('o');source_commit='4f4023c956f84d65743f39ce77d6c8899a21ada1';source=@();historical=@();package=@();processes=@();errors=@();policy=@{all_process_scan=$false;raw_commandline_saved=$false;environment_read=$false;data_root_opened=$false;product_api_calls=0}}
foreach($spec in @(@('apps/control/main.go',1,90),@('apps/control/main.go',200,310),@('ops/backup/main.go',98,155))) {
 $p=Join-Path $src $spec[0]; $result.source += [ordered]@{path=$spec[0];sha256=(Hash $p);lines=@(Lines $p $spec[1] $spec[2])}
}
$mapPath="$base/execution/v2.4/receipts/W05/W05-99/original_online_backup_readonly_resource_codex/20261015-current-chat/resource-map.json"
$mapHash=Hash $mapPath
$result.resource_map=[ordered]@{path=$mapPath;sha256=$mapHash;expected_match=($mapHash -eq '9609d05ad7afdfabf4cf9c635066c1f7df1fb71b21d580f23419a361fe31ec88')}
if($result.resource_map.expected_match) {
 $map=[IO.File]::ReadAllText($mapPath)|ConvertFrom-Json
 $result.resource_map.top_fields=@($map.PSObject.Properties.Name)
 $result.resource_map.public_binding=@(SelectIdentity $map '$' 0 | Where-Object { $_.key -match '(?i)deploy|package|asset|source|process|activation|manifest' -and $_.key -notmatch '(?i)data_root|database|workspace' })
}
$activation="$base/execution/v2.4/receipts/W05/W05-99/normal_desktop_verifier_replacement_activation_codex/20261015-current-chat/attempt01"
if([IO.Directory]::Exists($activation)) {
 $names=@([IO.Directory]::GetFiles($activation,'*.json',[IO.SearchOption]::TopDirectoryOnly) | ForEach-Object {[IO.Path]::GetFileName($_)})
 $result.historical_files=$names
 $chosen=@($names | Where-Object {$_ -match '(?i)identity|process|launch|native|activation' -and $_ -notmatch '(?i)recipe|command|index|manifest|config' } | Select-Object -First 16)
 foreach($n in $chosen) { $p=Join-Path $activation $n; try {$j=[IO.File]::ReadAllText($p)|ConvertFrom-Json; $result.historical += [ordered]@{file=$n;sha256=(Hash $p);selected=@(SelectIdentity $j '$' 0)}} catch {$result.errors += [ordered]@{branch='historical';file=$n;error_type=$_.Exception.GetType().FullName}} }
}
$manifestPublicPaths=New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
$manifestEntries=@()
function CollectAssets($node,[string]$trail,[int]$depth) {
 if($null -eq $node -or $depth -gt 12){return}
 if($node -is [array]) {foreach($n in $node){CollectAssets $n $trail ($depth+1)};return}
 if($node -isnot [pscustomobject]){return}
 $rel=$null; foreach($key in @('path','relative_path','relativePath','file')) {if($node.PSObject.Properties[$key] -and $node.$key -is [string]) {$rel=$node.$key;break}}
 if($rel -and $rel -notmatch '(?i)(^|[/\\])(data|config|secrets?|keys?|credentials?)([/\\]|$)' -and $rel -match '(?i)\.(exe|dll|js|cjs|mjs|wasm)$') {
  $full=[IO.Path]::GetFullPath((Join-Path $package $rel)); $prefix=[IO.Path]::GetFullPath($package).TrimEnd('\')+'\'
  if($full.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)) {
   $null=$manifestPublicPaths.Add($full)
   $exists=[IO.File]::Exists($full);$actual=$null;if($exists){$actual=Hash $full}
   $expected=$null;foreach($key in @('sha256','hash','sha256_hex')){if($node.PSObject.Properties[$key] -and $node.$key -is [string]) {$expected=$node.$key;break}}
   [ordered]@{manifest_node=$trail;relative_path=$rel;exists=$exists;sha256=$actual;manifest_sha256=$expected;hash_matches=($expected -and $actual -and $actual -eq ($expected -replace '^sha256:',''))}
  }
 }
 foreach($p in $node.PSObject.Properties){if($p.Name -notmatch '(?i)secret|token|credential|env|config' -and ($p.Value -is [array] -or $p.Value -is [pscustomobject])) {CollectAssets $p.Value "$trail.$($p.Name)" ($depth+1)}}
}
if([IO.Directory]::Exists($package)) {
 $publicManifestNames=@([IO.Directory]::GetFiles($package,'*manifest*.json',[IO.SearchOption]::TopDirectoryOnly) | Select-Object -First 4)
 $result.package_top_manifest_count=$publicManifestNames.Count
 foreach($p in $publicManifestNames){try{$j=[IO.File]::ReadAllText($p)|ConvertFrom-Json;$entries=@(CollectAssets $j '$' 0);$result.package += [ordered]@{manifest=[IO.Path]::GetFileName($p);sha256=(Hash $p);top_fields=@($j.PSObject.Properties.Name);public_program_entries=$entries}}catch{$result.errors += [ordered]@{branch='package-manifest';file=[IO.Path]::GetFileName($p);error_type=$_.Exception.GetType().FullName}}}
}
try {Import-Module 'C:/Windows/System32/WindowsPowerShell/v1.0/Modules/CimCmdlets/CimCmdlets.psd1' -ErrorAction Stop} catch {$result.errors += [ordered]@{branch='cim-import';error_type=$_.Exception.GetType().FullName}}
foreach($taskPid in @(69996,54076)) {
 try {
  $p=Get-CimInstance -ClassName Win32_Process -Filter "ProcessId = $taskPid" -Property ProcessId,ParentProcessId,Name,ExecutablePath,CreationDate,CommandLine -ErrorAction Stop
  if($null -eq $p) {$result.processes += [ordered]@{pid=$taskPid;state='UNKNOWN_ANCHOR_ABSENT';branch_stopped=$true};continue}
  $image=[string]$p.ExecutablePath
  $underPackage=$image -and ([IO.Path]::GetFullPath($image)).StartsWith(([IO.Path]::GetFullPath($package).TrimEnd('\')+'\'),[StringComparison]::OrdinalIgnoreCase)
  $isDeclared=$image -and $manifestPublicPaths.Contains([IO.Path]::GetFullPath($image))
  $record=[ordered]@{pid=[int]$p.ProcessId;parent_pid=[int]$p.ParentProcessId;name=[string]$p.Name;creation_utc=$p.CreationDate.ToUniversalTime().ToString('o');executable_path=($(if($underPackage -or $isDeclared){$image}else{'[REDACTED_UNBOUND_IMAGE]'}));image_under_expected_package=[bool]$underPackage;image_in_public_manifest=[bool]$isDeclared;historical_creation_continuity='UNKNOWN_NOT_BOUND';sanitized_path_arguments=@();unexpected_arguments='OMITTED';state='UNKNOWN_IDENTITY';branch_stopped=$true}
  if($underPackage -and $isDeclared) {
   $record.image_sha256=Hash $image
   $record.core_expected_sha256_match=($taskPid -eq 54076 -and $record.image_sha256 -eq 'c4a3b498fc15120828427b237b8176710acfd7a9333cd24e9911fded9cd63e24')
   $record.state='CURRENT_IMAGE_MANIFEST_BOUND_CONTINUITY_UNKNOWN';$record.branch_stopped=$false
   $cmd=[string]$p.CommandLine
   foreach($flag in @('data-dir','runtime-assets-dir','user-data-dir')) {
    $pattern='(?:^|\s)--'+[regex]::Escape($flag)+'(?:=|\s+)(?:"(?<v>[^"]*)"|(?<v>[^\s"]+))'
    foreach($match in [regex]::Matches($cmd,$pattern)) {
     $value=$match.Groups['v'].Value
     if($value -match '^[A-Za-z]:[\\/]' -and $value -notmatch '[\r\n]' -and $value.Length -lt 500) {$record.sanitized_path_arguments += [ordered]@{flag=$flag;path=$value}} else {$record.sanitized_path_arguments += [ordered]@{flag=$flag;path='[REDACTED_NON_PATH]'}}
    }
   }
   $record.package_argument_present=$cmd.Replace('\','/').IndexOf($package,[StringComparison]::OrdinalIgnoreCase) -ge 0
   $cmd=$null
  }
  $p=$null
  $result.processes += $record
 } catch {$result.processes += [ordered]@{pid=$taskPid;state='UNKNOWN_QUERY_ERROR';error_type=$_.Exception.GetType().FullName;branch_stopped=$true}}
}
$json=$result|ConvertTo-Json -Depth 30
[IO.File]::WriteAllText((Join-Path $E 'group4-results.json'),$json,(New-Object Text.UTF8Encoding($true)))
$json