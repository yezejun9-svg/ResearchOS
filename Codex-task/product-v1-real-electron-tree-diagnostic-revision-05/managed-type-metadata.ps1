$ErrorActionPreference='Stop'
# Passive loading of the same installed managed assemblies as the helper.
# No FromHandle, UIA element/pattern query, COM object or helper entrypoint.
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$rows=@()
foreach ($name in @('AutomationElement','ValuePattern','SelectionPattern','LegacyIAccessiblePattern')) {
  $type=([Management.Automation.PSTypeName]::new('System.Windows.Automation.'+$name)).Type
  $rows+=@{name=$name;available=($null -ne $type);assembly=$(if ($type) {$type.Assembly.FullName}else{$null})}
}
$report=@{schema='researchos.managed-uia-type-availability/1';status='PASSIVE_TYPE_METADATA_ONLY';shell_version=$PSVersionTable.PSVersion.ToString();types=$rows;assembly_loads=2;helper_entrypoint=0;uia_element_calls=0;com_objects=0;gui=0;model=0}
$target=Join-Path $PSScriptRoot 'MANAGED_TYPE_METADATA.json'
if (Test-Path -LiteralPath $target) {throw 'METADATA_ALREADY_EXISTS'}
$report|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $target -Encoding utf8
$report|ConvertTo-Json -Depth 8 -Compress
