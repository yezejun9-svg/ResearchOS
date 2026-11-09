$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$source=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'choose-owned-folder.ps1') -Raw -Encoding UTF8
$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
if ($errors.Count) {throw 'HELPER_SYNTAX'}
foreach ($name in @('Limit-DiagnosticText','Read-DiagnosticField','Diagnostic-Number','Project-TreeDiagnostic')) {
  $defs=@($ast.FindAll({param($node)$node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq $name},$true))
  if ($defs.Count -ne 1) {throw 'PURE_FUNCTION_NOT_UNIQUE'}
  . ([ScriptBlock]::Create($defs[0].Extent.Text))
}
$script:foreignReads=0;$script:pidReads=0;$script:currentReads=0
$foreign=New-Object psobject
$foreign|Add-Member ScriptProperty ProcessId {$script:pidReads++;99}
foreach ($name in @('Name','AutomationId','BoundingRectangle','ControlType','NativeWindowHandle','ClassName','IsOffscreen','IsEnabled')) {
  $foreign|Add-Member ScriptProperty $name {$script:foreignReads++;'FORBIDDEN_FOREIGN_DATA'}
}
$script:activeInfo=$foreign
$element=New-Object psobject
$element|Add-Member ScriptProperty Current {$script:currentReads++;$script:activeInfo}
$row=Project-TreeDiagnostic $element 0 42
if ($row.status -cne 'FOREIGN_PROVIDER_OWNER' -or $row.process_id -ne 99 -or
  $row.Count -ne 2 -or $script:foreignReads -ne 0 -or $script:pidReads -ne 1 -or $script:currentReads -ne 1) {
  throw 'FOREIGN_GETTERS_READ_OR_SNAPSHOT_REPEATED'
}
$cases=@(@{name='foreign owner reads only ProcessId';status='PASS';foreign_getters=$script:foreignReads;pid_reads=$script:pidReads;current_reads=$script:currentReads})
$script:pidReads=0;$script:currentReads=0;$script:nameReads=0;$script:automationReads=0
$owned=[pscustomobject]@{
  ControlType=[pscustomobject]@{ProgrammaticName='ControlType.Tree'}
  NativeWindowHandle=123;ClassName='SysTreeView32';IsOffscreen=$false;IsEnabled=$true
  BoundingRectangle=[pscustomobject]@{X=1;Y=2;Width=3;Height=4;IsEmpty=$false}
}
$owned|Add-Member ScriptProperty ProcessId {$script:pidReads++;42}
$owned|Add-Member ScriptProperty Name {$script:nameReads++;'OWNED_NAME'}
$owned|Add-Member ScriptProperty AutomationId {$script:automationReads++;'OWNED_ID'}
$script:activeInfo=$owned
$row=Project-TreeDiagnostic $element 1 42
if ($row.status -cne 'METADATA_ONLY' -or $row.process_id -ne 42 -or $row.name -cne 'OWNED_NAME' -or
  $row.automation_id -cne 'OWNED_ID' -or $script:nameReads -ne 1 -or $script:automationReads -ne 1 -or
  $script:pidReads -ne 1 -or $script:currentReads -ne 1) {throw 'OWNED_PROJECTION_NOT_SINGLE_SNAPSHOT'}
$cases+=@{name='allowed owner metadata remains correct';status='PASS';name_reads=$script:nameReads;automation_reads=$script:automationReads;pid_reads=$script:pidReads;current_reads=$script:currentReads}
$script:foreignReads=0;$script:currentReads=0
$selected=New-Object psobject
$selected|Add-Member ScriptProperty Current {
  $script:currentReads++
  if ($script:currentReads -eq 1) {return $owned}
  return $foreign
}
# Simulate an earlier successful outer/selected precheck. The projector must
# independently guard its own one Current snapshot, without relying on it.
$precheck=$selected.Current
if ($precheck.ProcessId -ne 42) {throw 'FIXTURE_PRECHECK'}
$row=Project-TreeDiagnostic $selected 2 42
if ($row.status -cne 'FOREIGN_PROVIDER_OWNER' -or $row.process_id -ne 99 -or
  $script:foreignReads -ne 0 -or $script:currentReads -ne 2) {throw 'SELECTED_LATE_OWNER_NOT_GUARDED'}
$calls=@($ast.FindAll({param($node)$node -is [Management.Automation.Language.CommandAst] -and $node.GetCommandName() -ceq 'Project-TreeDiagnostic'},$true))
if ($calls.Count -ne 2) {throw 'EXPECTED_ROOT_AND_SELECTED_CALLS'}
foreach ($call in $calls) {if ($call.CommandElements.Count -ne 4 -or $call.CommandElements[3].Extent.Text -cne '$coreId') {throw 'OWNER_ARGUMENT_NOT_CONNECTED'}}
$cases+=@{name='selected late owner change internally guarded';status='PASS';foreign_getters=$script:foreignReads;current_reads=$script:currentReads}
@{status='OWNER_ORDER_PURE_PASS';passed=3;cases=$cases;helper_entrypoint=0;add_type=0;uia=0;gui=0;model=0}|ConvertTo-Json -Depth 10 -Compress
