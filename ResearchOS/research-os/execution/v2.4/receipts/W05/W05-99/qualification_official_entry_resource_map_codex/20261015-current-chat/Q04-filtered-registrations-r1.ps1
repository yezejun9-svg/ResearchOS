$ErrorActionPreference='Stop'
$match='(?i)researchos|research-os|ros-app|normal-coding-profile-c8b7adab|normal-verifier-replacement-4f4023'
$records=New-Object System.Collections.Generic.List[object]
$gaps=New-Object System.Collections.Generic.List[object]
function Sanitize([string]$value){
 if($null -eq $value){return $null}
 [regex]::Replace($value,'(?i)((?:--?|/)(?:api[-_]?key|access[-_]?token|token|password|secret|credential)(?:=|\s+))("[^"]*"|''[^'']*''|\S+)',{
 param($m)
 $bytes=[Text.Encoding]::UTF8.GetBytes($m.Groups[2].Value)
 $sha=[Security.Cryptography.SHA256]::Create()
 try{$hash=[BitConverter]::ToString($sha.ComputeHash($bytes)).Replace('-','').ToLower()}finally{$sha.Dispose()}
 $m.Groups[1].Value+'<REDACTED_SHA256:'+ $hash +'>'
 })
}
foreach($hive in @([Microsoft.Win32.RegistryHive]::CurrentUser,[Microsoft.Win32.RegistryHive]::LocalMachine)){
 foreach($view in @([Microsoft.Win32.RegistryView]::Registry64,[Microsoft.Win32.RegistryView]::Registry32)){
  $reg=$null
  try{
   $reg=[Microsoft.Win32.RegistryKey]::OpenBaseKey($hive,$view)
   foreach($sub in @('SOFTWARE\Microsoft\Windows\CurrentVersion\Run','SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce','SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon')){
    $key=$null
    try{$key=$reg.OpenSubKey($sub,$false);$hits=@();if($null -eq $key){$status='ABSENT'}else{$status='READ';$names=if($sub -like '*Winlogon'){@('Userinit','Shell')}else{@($key.GetValueNames())};foreach($name in $names){$val=[string]$key.GetValue($name,$null,[Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames);if($name -match $match -or $val -match $match){$hits+=@{name=$name;value=(Sanitize $val)}}}
    }
     $records.Add(@{kind='registry';hive=$hive.ToString();view=$view.ToString();path=$sub;status=$status;product_matches=$hits;match_count=$hits.Count})
    }catch{$gaps.Add(@{kind='registry';hive=$hive.ToString();view=$view.ToString();path=$sub;status='UNKNOWN_READ_ERROR';error=$_.Exception.Message})}finally{if($key){$key.Dispose()}}
   }
   foreach($classSub in @('SOFTWARE\Classes','SOFTWARE\Microsoft\Active Setup\Installed Components')){
    $key=$null
    try{$key=$reg.OpenSubKey($classSub,$false);$hits=@();$scanned=0
     if($null -eq $key){$status='ABSENT'}else{
      $status='READ'
      foreach($name in $key.GetSubKeyNames()){
       $child=$null;$commandKey=$null
       try{
        $child=$key.OpenSubKey($name,$false);if($null -eq $child){continue};$scanned++
        $default=[string]$child.GetValue('','',[Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
        if($classSub -eq 'SOFTWARE\Classes'){$commandKey=$child.OpenSubKey('shell\open\command',$false);$command=if($commandKey){[string]$commandKey.GetValue('','',[Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)}else{''}}
        else{$command=[string]$child.GetValue('StubPath','',[Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)}
        if($name -match $match -or $default -match $match -or $command -match $match){$hits+=@{name=$name;default=(Sanitize $default);command=(Sanitize $command);url_protocol=($child.GetValueNames() -contains 'URL Protocol')}}
       }catch{$gaps.Add(@{kind='registry-child';hive=$hive.ToString();view=$view.ToString();parent=$classSub;child_name_sha256=([BitConverter]::ToString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($name))).Replace('-','').ToLower());status='UNKNOWN_READ_ERROR';error_type=$_.Exception.GetType().FullName})}finally{if($commandKey){$commandKey.Dispose()};if($child){$child.Dispose()}}
      }
     }
     $records.Add(@{kind='registry';hive=$hive.ToString();view=$view.ToString();path=$classSub;status=$status;entries_scanned=$scanned;product_matches=$hits;match_count=$hits.Count})
    }catch{$gaps.Add(@{kind='registry';hive=$hive.ToString();view=$view.ToString();path=$classSub;status='UNKNOWN_READ_ERROR';error=$_.Exception.Message})}finally{if($key){$key.Dispose()}}
   }
  }catch{$gaps.Add(@{kind='registry-base';hive=$hive.ToString();view=$view.ToString();status='UNKNOWN_READ_ERROR';error=$_.Exception.Message})}finally{if($reg){$reg.Dispose()}}
 }
}
try{
 $tasks=@(Get-ScheduledTask -ErrorAction Stop);$hits=@()
 foreach($task in $tasks){$actions=@($task.Actions|ForEach-Object {@{execute=([string]$_.Execute);arguments=(Sanitize ([string]$_.Arguments));working_directory=([string]$_.WorkingDirectory)}});$joined=($actions|ConvertTo-Json -Compress -Depth 6);if($task.TaskName -match $match -or $task.TaskPath -match $match -or $joined -match $match){$hits+=@{name=$task.TaskName;path=$task.TaskPath;actions=$actions;principal=@{user_id=$task.Principal.UserId;group_id=$task.Principal.GroupId;logon_type=$task.Principal.LogonType;run_level=$task.Principal.RunLevel};state=$task.State.ToString();trigger_types=@($task.Triggers|ForEach-Object {$_.CimClass.CimClassName})}}}
 $records.Add(@{kind='scheduled_tasks';status='READ';entries_scanned=$tasks.Count;match_count=$hits.Count;product_matches=$hits})
}catch{$gaps.Add(@{kind='scheduled_tasks';status='UNKNOWN_READ_ERROR';error=$_.Exception.Message})}
try{
 $services=@(Get-CimInstance Win32_Service -ErrorAction Stop);$hits=@()
 foreach($svc in $services){if($svc.Name -match $match -or $svc.DisplayName -match $match -or $svc.PathName -match $match){
  $failure=@{};$servicePath='Registry::HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\'+$svc.Name
  try{$r=Get-ItemProperty -LiteralPath $servicePath -ErrorAction Stop;foreach($k in @('FailureActions','FailureActionsOnNonCrashFailures','DelayedAutoStart')){if($r.PSObject.Properties.Name -contains $k){$failure[$k]=$r.$k}}}catch{$failure=@{status='UNKNOWN_READ_ERROR';error=$_.Exception.Message}}
  $hits+=@{name=$svc.Name;path=(Sanitize $svc.PathName);start_mode=$svc.StartMode;start_name=$svc.StartName;state=$svc.State;failure_actions=$failure}
 }}
 $records.Add(@{kind='services';status='READ';entries_scanned=$services.Count;match_count=$hits.Count;product_matches=$hits})
}catch{$gaps.Add(@{kind='services';status='UNKNOWN_READ_ERROR';error=$_.Exception.Message})}
try{
 $wsh=New-Object -ComObject WScript.Shell
 foreach($special in @('DesktopDirectory','CommonDesktopDirectory','StartMenu','CommonStartMenu','Startup','CommonStartup')){
  $folder=[Environment]::GetFolderPath([Environment+SpecialFolder]::$special)
  try{
   if(-not $folder -or -not(Test-Path -LiteralPath $folder)){$records.Add(@{kind='shortcuts';special_folder=$special;path=$folder;status='ABSENT';match_count=0});continue}
   $lnks=@(Get-ChildItem -LiteralPath $folder -File -Recurse -Filter '*.lnk' -ErrorAction Stop);$hits=@()
   foreach($lnk in $lnks){try{$shortcut=$wsh.CreateShortcut($lnk.FullName);$target=$shortcut.TargetPath;$arguments=$shortcut.Arguments;$working=$shortcut.WorkingDirectory;if($lnk.Name -match $match -or $target -match $match -or $arguments -match $match -or $working -match $match){$hits+=@{path=$lnk.FullName;target=$target;arguments=(Sanitize $arguments);working_directory=$working}};[void][Runtime.InteropServices.Marshal]::ReleaseComObject($shortcut)}catch{$gaps.Add(@{kind='shortcut';scope=$special;status='UNKNOWN_READ_ERROR';error_type=$_.Exception.GetType().FullName})}}
   $records.Add(@{kind='shortcuts';special_folder=$special;path=$folder;status='READ';entries_scanned=$lnks.Count;match_count=$hits.Count;product_matches=$hits})
  }catch{$gaps.Add(@{kind='shortcuts';special_folder=$special;path=$folder;status='UNKNOWN_READ_ERROR';error=$_.Exception.Message})}
 }
 [void][Runtime.InteropServices.Marshal]::ReleaseComObject($wsh)
}catch{$gaps.Add(@{kind='shortcuts-com';status='UNKNOWN_READ_ERROR';error=$_.Exception.Message})}
$out=@{schema='researchos.CP518.filtered-registration-inventory.v1';filter=$match;records=$records.ToArray();gaps=$gaps.ToArray();no_unrelated_values_sealed=$true;runtime_restart_registration='UNKNOWN_NOT_QUERIED_NO_PROCESSCOMMANDLINE';actual_authority=$false;formal_increment=0}
$out|ConvertTo-Json -Depth 20|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'checked-registrations.json') -Encoding utf8
$out|ConvertTo-Json -Depth 20

