$ErrorActionPreference='Stop'
$tokens=$null; $errors=$null
$text=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'choose-owned-folder.ps1') -Raw -Encoding UTF8
$ast=[Management.Automation.Language.Parser]::ParseInput($text,[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw 'HELPER_SYNTAX' }
$names=@('Assert-DiagnosticOnly','Limit-DiagnosticText','Read-DiagnosticField','Diagnostic-Number','Project-TreeDiagnostic')
foreach ($name in $names) {
  $defs=@($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq $name},$true))
  if ($defs.Count -ne 1) { throw 'PURE_FUNCTION_NOT_UNIQUE' }
  . ([ScriptBlock]::Create($defs[0].Extent.Text))
}
$passed=0
Assert-DiagnosticOnly $true; $passed++
foreach ($bad in @($false,$null,'true',1)) {
  $rejected=$false
  try { Assert-DiagnosticOnly $bad } catch { $rejected=$true }
  if (-not $rejected) { throw 'BAD_DIAGNOSTIC_FLAG_ACCEPTED' }
  $passed++
}
$element=[pscustomobject]@{Current=[pscustomobject]@{
  ControlType=[pscustomobject]@{ProgrammaticName='ControlType.Tree'}
  ProcessId=999; NativeWindowHandle=0; ClassName='SysTreeView32'; AutomationId='fixture'
  IsOffscreen=$true; IsEnabled=$false; Name=('quoted "name" '+[char]10+('x'*160))
  BoundingRectangle=[pscustomobject]@{X=[double]::PositiveInfinity;Y=[double]::NaN;Width=0;Height=1;IsEmpty=$true}
}}
$row=Project-TreeDiagnostic $element 0
if ($row.process_id -ne 999 -or $row.native_window_handle -cne '0' -or -not $row.is_offscreen -or $row.enabled -ne $false) { throw 'FACTS_FILTERED_OR_CHANGED' }
$passed++
if ($row.name.Length -gt 96 -or $row.name.Contains([string][char]10)) { throw 'NAME_BOUNDARY' }
$passed++
if ($row.bounding_rect.x -cne 'Infinity' -or $row.bounding_rect.y -cne 'NaN') { throw 'NONFINITE_BBOX_LOST' }
$passed++
$null=($row|ConvertTo-Json -Depth 12 -Compress|ConvertFrom-Json); $passed++
$unavailable=New-Object psobject
$unavailable|Add-Member ScriptProperty Current { throw 'ELEMENT_UNAVAILABLE_FIXTURE' }
if ((Project-TreeDiagnostic $unavailable 1).status -cne 'ELEMENT_UNAVAILABLE') { throw 'PROVIDER_FAILURE_NOT_CAPTURED' }
$passed++
$okCalls=@($ast.FindAll({param($node)
  $node -is [Management.Automation.Language.CommandAst] -and $node.GetCommandName() -ceq 'Get-OwnedDialogButton' -and
  $node.CommandElements[1].Extent.Text -ceq '1'
},$true))
if ($okCalls.Count -ne 0 -or $text.Contains('$okAttempted=$true') -or $text.Contains('$result.clicked_ok=$true')) { throw 'DIAGNOSTIC_CAN_OK' }
$passed++
$navCalls=@($ast.FindAll({param($node)
  $node -is [Management.Automation.Language.CommandAst] -and $node.GetCommandName() -ceq 'Select-FixtureThroughRealTree'
},$true))
if ($navCalls.Count -ne 0) { throw 'DIAGNOSTIC_NAVIGATION_DISPATCH' }
$passed++
if (-not $text.Contains("$"+'result.diagnostic=Read-OwnedTreeDiagnostic') -or
  -not $text.Contains("throw 'DIAGNOSTIC_ONLY_TREE_SNAPSHOT_COMPLETE_NO_OK'") -or
  -not $text.Contains('$cancel = Get-OwnedDialogButton 2 -ForCleanup')) { throw 'DIAGNOSTIC_CANCEL_NOT_CONNECTED' }
$passed++
if (-not $text.Contains('if ($trees.Count -eq 0)') -or -not $text.Contains('EnumChildWindows($hwnd,$childCallback') -or
  $text.Contains('AutomationElement]::RootElement')) { throw 'ZERO_TREE_OR_SCOPE_BOUNDARY' }
$passed++
@{status='DIAGNOSTIC_PURE_PASS';passed=$passed;helper_entrypoint=0;add_type=0;uia=0;gui=0;model=0}|ConvertTo-Json -Compress
