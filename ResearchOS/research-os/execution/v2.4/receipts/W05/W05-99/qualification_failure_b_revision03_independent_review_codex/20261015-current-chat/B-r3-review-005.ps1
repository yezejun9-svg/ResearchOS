$ErrorActionPreference='Stop'
$original=[IO.File]::ReadAllText('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision03_independent_review_codex/20261015-current-chat/original-independent_b2_domain_windows_test.go')
$old=@'
		defer tx.Rollback()
		_, err = r.f.s.validatedQualificationFailureTx(tx, r.f.project, Str(r.task, "id"), Str(r.run, "id"), epoch)
		return err
'@
$new=@'
		defer tx.Rollback()
		closure, err := r.f.s.validatedQualificationFailureTx(tx, r.f.project, Str(r.task, "id"), Str(r.run, "id"), epoch)
		if err != nil { return err }
		checkErr := closure.Check()
		rollbackErr := tx.Rollback()
		return errors.Join(checkErr, rollbackErr, closure.Close())
'@
if(!$original.Contains($old)){throw 'expected helper not found'}
[IO.File]::WriteAllText('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision03_independent_review_codex/20261015-current-chat/independent_b3_adapted_domain_windows_test.go',$original.Replace($old,$new),[Text.UTF8Encoding]::new($false))
git diff --no-index -- 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision03_independent_review_codex/20261015-current-chat/original-independent_b2_domain_windows_test.go' 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision03_independent_review_codex/20261015-current-chat/independent_b3_adapted_domain_windows_test.go'
if($LASTEXITCODE -gt 1){throw 'diff failed'}
rg -n 'func Test|type qualificationFailureClosure|func \(.*qualificationFailureClosure|HoldQualification|func qualificationNativeClosureMatches|nativeHold|model.Key' 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015/internal/domain/runtime_qualification_failure_windows.go' 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015/internal/domain/runtime_qualification_failure_windows_test.go'
Get-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015/internal/domain/runtime_qualification_failure_windows_test.go' | Select-Object -Skip 760 -First 180
Get-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015/internal/domain/runtime_qualification_failure_windows.go' | Select-Object -Skip 880 -First 200
Get-Content -LiteralPath 'D:/作品集/ResearchOS/research-os/.local/worktrees/qualification-failure-b-r3-20261015/adapters/runtime/qualification_failure_proof_windows.go' | Select-Object -Skip 250 -First 140
exit 0

