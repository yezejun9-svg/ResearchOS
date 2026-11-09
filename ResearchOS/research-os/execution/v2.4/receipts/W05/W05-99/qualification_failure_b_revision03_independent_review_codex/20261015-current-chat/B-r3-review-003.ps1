$ErrorActionPreference='Stop'
rg -n 'validatedQualificationFailureTx|\.nativeHold|HoldQualificationNativeFacts|qualificationFailureClosure|func TestQualification' 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015/internal/domain' 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015/adapters/runtime'
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
git -C 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015' diff 1d3cc504 HEAD -- adapters/runtime/qualification_failure_proof_windows_test.go internal/domain/runtime_qualification_failure_windows_test.go
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
$sourceManifest=Get-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision03_source_codex/20261015-current-chat/FINAL-manifest.json' -Raw -Encoding utf8|ConvertFrom-Json
foreach($f in $sourceManifest.source_hashes.PSObject.Properties){$p=Join-Path 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015' $f.Name;$h=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant();if($h -ne $f.Value.sha256){throw ('SOURCE MISMATCH '+$f.Name)};'SOURCE VERIFIED '+$f.Name+' '+$h}
New-Item -ItemType Directory -Path 'D:/作品集/ResearchOS/research-os/.local/qualification-failure-b-r3-independent-review-20261015-tmp/gocache','D:/作品集/ResearchOS/research-os/.local/qualification-failure-b-r3-independent-review-20261015-tmp/tmp' -Force |Out-Null
$old='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision02_independent_review_codex/20261015-current-chat'
foreach($name in @('independent_b2_domain_windows_test.go','independent_b2_adapter_windows_test.go','independent_b2_followup_windows_test.go')){Copy-Item -LiteralPath (Join-Path $old $name) -Destination (Join-Path $PSScriptRoot ('original-'+$name));Get-FileHash -LiteralPath (Join-Path $old $name),(Join-Path $PSScriptRoot ('original-'+$name)) -Algorithm SHA256|ConvertTo-Json}
exit 0
