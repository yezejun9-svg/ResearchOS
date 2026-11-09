$records=New-Object System.Collections.Generic.List[object]
try{$os=Get-CimInstance Win32_OperatingSystem -ErrorAction Stop|Select-Object Version,BuildNumber,OSArchitecture,Caption;$records.Add(@{kind='OS';status='READ';value=$os})}catch{$records.Add(@{kind='OS';status='UNKNOWN';error=$_.Exception.Message})}
foreach($arg in @('/user','/groups','/priv')){
 $output=@(& "$env:SystemRoot/System32/whoami.exe" $arg /fo csv 2>&1);$code=$LASTEXITCODE
 $records.Add(@{kind='whoami';argv=@($arg,'/fo','csv');native_exit_code=$code;stdout=($output|Out-String -Width 300)})
}
try{
 $identity=[Security.Principal.WindowsIdentity]::GetCurrent()
 $principal=[Security.Principal.WindowsPrincipal]::new($identity)
 $records.Add(@{kind='managed-token-metadata';status='READ';user_sid=$identity.User.Value;owner_sid=$identity.Owner.Value;authentication_type=$identity.AuthenticationType;impersonation_level=$identity.ImpersonationLevel.ToString();administrator_role_enabled=$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator);elevation_type='NOT_DIRECTLY_QUERIED_NO_ACCEPTED_NATIVE_HELPER';token_privilege_state='See whoami /priv and group mandatory label; no native TOKEN_ELEVATION query'})
 $identity.Dispose()
}catch{$records.Add(@{kind='managed-token-metadata';status='UNKNOWN';error=$_.Exception.Message})}
foreach($drive in @('C:','D:')){
 $output=@(& "$env:SystemRoot/System32/fsutil.exe" fsinfo volumeinfo $drive 2>&1);$code=$LASTEXITCODE
 $records.Add(@{kind='fsutil-volumeinfo';drive=$drive;native_exit_code=$code;stdout=($output|Out-String -Width 300);identity_class='AUXILIARY_VOLUME_FACT_NOT_HELD_NATIVE_IDENTITY'})
}
$out=@{schema='researchos.CP518.platform-token.v1';records=$records.ToArray();actual_authority=$false;formal_increment=0}
$out|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'platform-token.json') -Encoding utf8
$out|ConvertTo-Json -Depth 12

