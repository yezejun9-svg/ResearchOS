$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new()
$wt='D:/作品集/ResearchOS/research-os/.local/worktrees/host-candidate-capture-20261104'
$draft='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/cp599-candidate-capture-author/source01'
$receipt='C:/Users/yqyyds/Documents/Codex/2026-11-04/task/cp599-candidate-capture-author/source-write-01.json'
if(Test-Path -LiteralPath $receipt){throw 'write receipt exists; inspect before action'}
$baseline=@{'internal/domain/runtime_tools.go'='3ac031037f81dc0d838aa3661d79c50875b7a7f4d3fba27abcaac6136a62a878';'internal/host/runtime_check_windows.go'='6d3afda720990063906e1e9ace34177dd6312f8eadfc5934f30a07f9a7dd5d55'}
foreach($rel in $baseline.Keys){if((Get-FileHash -LiteralPath (Join-Path $wt $rel) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $baseline[$rel]){throw ('baseline drift '+$rel)}}
$contents=@{}
$files=@{'runtime_tools_capture.go'='internal/domain/runtime_tools_capture.go';'runtime_tools_capture_test.go'='internal/domain/runtime_tools_capture_test.go';'runtime_check_delivery_windows.go'='internal/host/runtime_check_delivery_windows.go';'runtime_check_delivery_windows_test.go'='internal/host/runtime_check_delivery_windows_test.go'}
foreach($name in $files.Keys){
 $rel=$files[$name];if(Test-Path -LiteralPath (Join-Path $wt $rel)){throw ('new path exists '+$rel)}
 $contents[$rel]=[IO.File]::ReadAllText((Join-Path $draft $name),[Text.Encoding]::UTF8)
}
function ReplaceOnce([string]$text,[string]$old,[string]$new){$i=$text.IndexOf($old,[StringComparison]::Ordinal);if($i -lt 0 -or $text.IndexOf($old,$i+$old.Length,[StringComparison]::Ordinal) -ge 0){throw 'replace cardinality'};return $text.Substring(0,$i)+$new+$text.Substring($i+$old.Length)}
$tool=[IO.File]::ReadAllText((Join-Path $wt 'internal/domain/runtime_tools.go')).Replace("`r`n","`n")
$contents['internal/domain/runtime_tools.go']=ReplaceOnce $tool "type RuntimeToolRequest struct {" "type RuntimeToolRequest struct {`n`tcodingCapture *runtimeToolCaptureContext"
$host=[IO.File]::ReadAllText((Join-Path $wt 'internal/host/runtime_check_windows.go')).Replace("`r`n","`n")
$point=@'
	check, err := parseFrozenRuntimeCheck(request.Policy, checkID)
	if err != nil {
		return nil, err
	}
'@
$addition=@'
	captureView, err := request.CodingCapture()
	if err != nil {
		return nil, err
	}
	if captureView != nil {
		if err := runtimeCaptureCheck(*captureView, check, domain.Hash(request.Policy)); err != nil {
			return nil, err
		}
	}
'@
$host=ReplaceOnce $host $point ($point+$addition)
$start=$host.IndexOf("`treceipt, err := sandbox.Run(ctx, sandbox.Command{",[StringComparison]::Ordinal)
if($start -lt 0){throw 'Run start not found'}
$end=$host.IndexOf("`n`tif err != nil {",$start,[StringComparison]::Ordinal)
if($end -lt 0){throw 'Run end not found'}
$old=$host.Substring($start,$end-$start)
$prefix="`treceipt, err := sandbox.Run(ctx, "
$command=$old.Substring($prefix.Length,$old.Length-$prefix.Length-1)
if(-not $command.EndsWith('}')){throw 'command extraction failed'}
$legacy=$old.Replace('receipt, err :=','receipt, err =')
$new="`tvar receipt sandbox.Receipt`n`tvar captured *runtimeCandidateCapture`n`tif captureView == nil {`n"+$legacy+"`n`t} else {`n`t`tcommand := "+$command+"`n"+@'
		process, startErr := sandbox.Start(ctx, command, sandbox.StartOptions{
			BeforeResume: func(identity sandbox.Identity) error {
				var captureErr error
				captured, captureErr = captureRuntimeCandidate(ctx, *captureView, check, domain.Hash(request.Policy), sourceManifest, identity)
				return captureErr
			},
		})
		err = startErr
		if err == nil {
			// Match Run: ownership includes termination, drain and staging cleanup.
			receipt, err = process.Wait(context.Background())
		}
	}
'@
$host=ReplaceOnce $host $old $new
$bound=@'
	if err := runtimeCheckEvidenceBound(full); err != nil {
'@
$attach=@'
	if captureView != nil {
		proof, captureErr := captured.evidence(receipt)
		if captureErr != nil {
			return nil, captureErr
		}
		full["candidate_capture"] = proof
	}
'@
$host=ReplaceOnce $host $bound ($attach+$bound)
$contents['internal/host/runtime_check_windows.go']=$host
$written=@()
foreach($rel in $contents.Keys|Sort-Object){
 $target=Join-Path $wt $rel
 [IO.File]::WriteAllText($target,$contents[$rel],[Text.UTF8Encoding]::new($false))
 $written+=[ordered]@{path=$rel;sha256=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant();bytes=(Get-Item -LiteralPath $target).Length}
}
[IO.File]::WriteAllText($receipt,([ordered]@{status='SOURCE_WRITTEN_UNFORMATTED_UNTESTED';at_utc=[DateTime]::UtcNow.ToString('o');files=$written}|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
Get-Content -LiteralPath $receipt -Raw -Encoding UTF8

