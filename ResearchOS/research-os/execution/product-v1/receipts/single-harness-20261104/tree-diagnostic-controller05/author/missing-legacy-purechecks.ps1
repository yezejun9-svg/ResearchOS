$ErrorActionPreference='Stop'
# Same passive managed assemblies; fake elements only, no FromHandle/provider.
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$tokens=$null;$errors=$null
$source=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'choose-owned-folder.ps1') -Raw -Encoding UTF8
$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
if ($errors.Count) {throw 'HELPER_SYNTAX'}
foreach ($name in @('Limit-DiagnosticText','Project-PublicUiaValue','Read-PublicPatterns')) {
  $defs=@($ast.FindAll({param($node)$node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq $name},$true))
  if ($defs.Count -ne 1) {throw 'PURE_FUNCTION_NOT_UNIQUE'}
  . ([ScriptBlock]::Create($defs[0].Extent.Text))
}
function Assert-DirectNativeTree { }
$coreId=42
$script:nameReads=0;$script:queries=[Collections.Generic.List[int]]::new()
$valueId=[Windows.Automation.ValuePattern]::Pattern.Id
$selectionId=[Windows.Automation.SelectionPattern]::Pattern.Id
$element=New-Object psobject
$info=[pscustomobject]@{ProcessId=42}
$info|Add-Member ScriptProperty Name {$script:nameReads++;'OWNED_NAME'}
$element|Add-Member NoteProperty Current $info
$element|Add-Member ScriptMethod TryGetCurrentPattern {
  param($id,$out)
  $script:queries.Add($id.Id)
  if ($id.Id -eq $valueId) {
    $out.Value=[pscustomobject]@{Current=[pscustomobject]@{Value='C:\owned\workspace'}}
    return $true
  }
  if ($id.Id -eq $selectionId) {
    $fake=New-Object psobject
    $fake|Add-Member ScriptMethod GetCurrentSelection {return @()}
    $out.Value=$fake
    return $true
  }
  throw 'UNEXPECTED_PATTERN_QUERY'
}
$legacyType=([Management.Automation.PSTypeName]::new('System.Windows.Automation.LegacyIAccessiblePattern')).Type
if ($null -ne $legacyType) {throw 'EXPECTED_INSTALLED_MISSING_LEGACY_FOR_THIS_FIXTURE'}
$read=Read-PublicPatterns $element
if ($read.support.LegacyIAccessiblePattern.status -cne 'UNSUPPORTED_TYPE' -or
    $read.support.ValuePattern.supported -ne $true -or
    @($read.values|Where-Object {$_.source -ceq 'ValuePattern'}).Count -ne 1 -or
    $script:queries.Count -ne 1 -or $script:queries[0] -ne $valueId) {throw 'MISSING_LEGACY_ABORTED_VALUE'}
$cases=@(@{name='missing managed Legacy does not abort Value';status='PASS';value_queries=1;legacy_status=$read.support.LegacyIAccessiblePattern.status})
$a=$source.IndexOf('      $selection=$null;$supported=$element.TryGetCurrentPattern(')
$z=$source.IndexOf(([string][char]10+'    } catch {'),$a)
if ($a -lt 0 -or $z -le $a) {throw 'ACTUAL_SELECTION_FRAGMENT_NOT_FOUND'}
$direct=@{patterns=$read.support}
. ([ScriptBlock]::Create($source.Substring($a,$z-$a)))
if ($direct.patterns.SelectionPattern.supported -ne $true -or $direct.selection_count -ne 0 -or
    $script:queries.Count -ne 2 -or $script:queries[1] -ne $selectionId) {throw 'MISSING_LEGACY_ABORTED_SELECTION'}
$cases+=@{name='same actual Selection continuation still executes';status='PASS';selection_queries=1}
$script:nameReads=0;$script:queries.Clear()
$foreign=[pscustomobject]@{ProcessId=99}
$foreign|Add-Member ScriptProperty Name {$script:nameReads++;'FORBIDDEN'}
$element.Current=$foreign
$caught=$false
try {$null=Read-PublicPatterns $element} catch {$caught=$_.Exception.Message -like '*OWNER_UNCONFIRMED*'}
if (-not $caught -or $script:nameReads -ne 0 -or $script:queries.Count -ne 0) {throw 'FOREIGN_PROVIDER_QUERIED'}
$cases+=@{name='owner mismatch prevents Name and all pattern queries';status='PASS';foreign_name_reads=$script:nameReads;pattern_queries=$script:queries.Count}
if ($source.Contains('$okAttempted=$true') -or $source.Contains('Get-OwnedDialogButton 1')) {throw 'OK_PATH'}
$cases+=@{name='no OK path remains';status='PASS'}
@{schema='researchos.optional-legacy.purechecks/1';status='OPTIONAL_LEGACY_PURE_PASS';passed=$cases.Count;cases=$cases;
  assembly_loads=2;helper_entrypoint=0;dynamic_csharp_compile=0;uia_element_calls=0;gui=0;model=0}|ConvertTo-Json -Depth 10 -Compress
