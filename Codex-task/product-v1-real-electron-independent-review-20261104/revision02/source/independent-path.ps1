$ErrorActionPreference = 'Stop'
$parseTokens = $null
$parseErrors = $null
$helperPath = Join-Path $PSScriptRoot 'choose-owned-folder.ps1'
$ast = [Management.Automation.Language.Parser]::ParseFile($helperPath,[ref]$parseTokens,[ref]$parseErrors)
if ($parseErrors.Count -gt 0) { throw 'HELPER_AST_SYNTAX_ERROR' }
$names = @('Convert-UiaAbsolutePath','Assert-UiaPathEvidence','Test-UiaPathCandidate')
foreach ($name in $names) {
  $defs = @($ast.FindAll({ param($node)
    $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq $name
  },$true))
  if ($defs.Count -ne 1) { throw ('PURE_FUNCTION_NOT_UNIQUE:' + $name) }
  # Only these actual pure function definitions are evaluated, never helper body,
  # Add-Type, a Windows message, process inspection, UIAutomation or GUI.
  . ([ScriptBlock]::Create($defs[0].Extent.Text))
}
$script:passed = 0
$script:cases = [Collections.Generic.List[object]]::new()
function Check-Pass([string]$Name, [ScriptBlock]$Action) {
  & $Action
  $script:passed++
  $script:cases.Add(@{ name=$Name; status='PASS' })
}
function Check-Fail([string]$Name, [ScriptBlock]$Action, [string]$Reason) {
  $caught=$false
  try { $null = & $Action } catch {
    if ($_.Exception.Message -notlike ('*'+$Reason+'*')) {
      @{ status='PURE_FIXTURE_REASON_MISMATCH'; case=$Name; expected_reason=$Reason; actual_reason=$_.Exception.Message } | ConvertTo-Json -Compress | Write-Output
      throw
    }
    $caught=$true
  }
  if (-not $caught) { throw ('UNSAFE_ACCEPTANCE:'+$Name) }
  $script:passed++
  $script:cases.Add(@{ name=$Name; status='PASS_EXPECTED_REJECTION' })
}
function Assert-True($Value) { if ($Value -ne $true) { throw 'ASSERT_TRUE_FAILED' } }
function Assert-False($Value) { if ($Value -ne $false) { throw 'ASSERT_FALSE_FAILED' } }
function Reading($Provider,$Value) { return @{ source=$Provider; value=$Value } }

$expected='C:\Users\synthetic\owned\workspace'
Check-Fail 'old P1 wrong reliable value plus same-name cannot pass' { Test-UiaPathCandidate 'workspace' 'workspace' @((Reading ValuePattern 'D:\other\workspace'),(Reading Name 'workspace')) $expected } 'CONTRADICTORY'
Check-Fail 'later wrong provider cannot hide behind two earlier correct facts' { Assert-UiaPathEvidence @((Reading Name $expected),(Reading ValuePattern $expected),(Reading LegacyIAccessiblePattern 'D:\other\workspace')) $expected $true } 'CONTRADICTORY'
Check-Fail 'later Name conflict cannot hide behind two reliable correct providers' { Assert-UiaPathEvidence @((Reading ValuePattern $expected),(Reading LegacyIAccessiblePattern $expected),(Reading Name 'D:\other\workspace')) $expected $true } 'CONTRADICTORY'
Check-Fail 'arbitrary provider label does not grant reliable evidence' { Assert-UiaPathEvidence @((Reading UnknownProvider $expected),(Reading Name $expected)) $expected $true } 'MISSING'
Check-Fail 'empty evidence cannot authorize final OK' { Assert-UiaPathEvidence @() $expected $true } 'MISSING'
Check-Fail 'relative display chain cannot authorize final OK' { Assert-UiaPathEvidence @((Reading Name 'workspace'),(Reading Name 'owned'),(Reading ValuePattern 'workspace')) $expected $true } 'MISSING'
Check-Pass 'two reliable providers and Name normalized to same absolute path pass' { $proof=Assert-UiaPathEvidence @((Reading Name $expected),(Reading ValuePattern $expected),(Reading LegacyIAccessiblePattern 'c:/Users/synthetic/owned/workspace')) $expected $true; Assert-True ($proof.reliable_count -eq 2) }
Check-Pass 'an unrelated valid absolute path with no name match is not a candidate' { Assert-False (Test-UiaPathCandidate 'different' 'workspace' @((Reading ValuePattern 'D:\other\workspace')) $expected) }
@{status='INDEPENDENT_ACTUAL_PURE_PATH_COUNTEREXAMPLES_PASS';passed=$script:passed;cases=@($script:cases);helper_body=0;add_type=0;uia=0;gui=0;native=0;model=0}|ConvertTo-Json -Depth 12 -Compress
