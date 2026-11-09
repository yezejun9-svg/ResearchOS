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
$expected = 'C:\Users\synthetic\owned-run\workspace'
$outside = 'D:\outside\workspace'
Check-Pass 'exact ValuePattern absolute' { $proof=Assert-UiaPathEvidence @((Reading ValuePattern $expected)) $expected $true; Assert-True ($proof.reliable_count -eq 1) }
Check-Pass 'two consistent reliable providers normalized casing slash' { $proof=Assert-UiaPathEvidence @((Reading ValuePattern $expected),(Reading LegacyIAccessiblePattern 'c:/users/synthetic/owned-run/workspace')) $expected $true; Assert-True ($proof.reliable_count -eq 2) }
Check-Fail 'matching first provider cannot hide contradictory second' { Assert-UiaPathEvidence @((Reading ValuePattern $expected),(Reading LegacyIAccessiblePattern $outside)) $expected $true } 'CONTRADICTORY'
Check-Fail 'contradictory first provider cannot hide later match' { Assert-UiaPathEvidence @((Reading ValuePattern $outside),(Reading LegacyIAccessiblePattern $expected)) $expected $true } 'CONTRADICTORY'
Check-Fail 'absolute Name cannot contradict reliable path' { Assert-UiaPathEvidence @((Reading Name $outside),(Reading ValuePattern $expected)) $expected $true } 'CONTRADICTORY'
Check-Fail 'absolute display Name alone is not reliable proof' { Assert-UiaPathEvidence @((Reading Name $expected)) $expected $true } 'MISSING'
Check-Fail 'matching display ancestry cannot authorize final selection' { Assert-UiaPathEvidence @((Reading Name 'workspace')) $expected $true } 'MISSING'
Check-Fail 'relative provider value is not final proof' { Assert-UiaPathEvidence @((Reading ValuePattern 'workspace')) $expected $true } 'MISSING'
Check-Fail 'drive-relative path rejected' { Assert-UiaPathEvidence @((Reading ValuePattern 'C:workspace')) $expected $true } 'NOT_FULLY_QUALIFIED'
Check-Fail 'rooted but not fully qualified rejected' { Assert-UiaPathEvidence @((Reading ValuePattern '\workspace')) $expected $true } 'NOT_FULLY_QUALIFIED'
Check-Fail 'NUL path rejected' { Assert-UiaPathEvidence @((Reading ValuePattern ($expected+[char]0))) $expected $true } 'MALFORMED'
Check-Fail 'UNC conflict rejected' { Assert-UiaPathEvidence @((Reading ValuePattern '\\server\outside\workspace')) $expected $true } 'CONTRADICTORY'
Check-Fail 'leading-space drive path rejected' { Assert-UiaPathEvidence @((Reading ValuePattern (' '+$expected))) $expected $true } 'MALFORMED'
Check-Fail 'navigation name match cannot override wrong absolute' { Test-UiaPathCandidate 'workspace' 'workspace' @((Reading ValuePattern $outside)) $expected } 'CONTRADICTORY'
Check-Fail 'navigation matching path cannot hide other provider conflict' { Test-UiaPathCandidate 'different' 'workspace' @((Reading ValuePattern $expected),(Reading LegacyIAccessiblePattern $outside)) $expected } 'CONTRADICTORY'
Check-Pass 'unrelated tree node not selected' { Assert-False (Test-UiaPathCandidate 'outside' 'workspace' @((Reading ValuePattern $outside)) $expected) }
Check-Pass 'name-only navigation is not final proof' { Assert-True (Test-UiaPathCandidate 'workspace' 'workspace' @((Reading Name 'workspace')) $expected) }
Check-Pass 'reliable consistent absolute can navigate localized name' { Assert-True (Test-UiaPathCandidate 'localized' 'workspace' @((Reading ValuePattern $expected)) $expected) }
Check-Pass 'empty display names do not create drive candidate' { Assert-False (Test-UiaPathCandidate '' '' @((Reading Name '')) 'C:\') }
Check-Pass 'Legacy absolute alone accepted' { $proof=Assert-UiaPathEvidence @((Reading ValuePattern ''),(Reading LegacyIAccessiblePattern $expected)) $expected $true; Assert-True ($proof.reliable_count -eq 1) }
Check-Fail 'non-string provider rejected' { Assert-UiaPathEvidence @((Reading ValuePattern @{ fake='value' })) $expected $true } 'MALFORMED'
@{ status='PURE_PATH_COUNTEREXAMPLES_PASS'; passed=$script:passed; cases=@($script:cases);
  helper_body_executions=0; add_type=0; uia=0; gui=0; native=0; model=0 } | ConvertTo-Json -Depth 12 -Compress
