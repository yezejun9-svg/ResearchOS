$ErrorActionPreference='Stop'
$e='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/owned_core_stop_effect_state_revision05_independent_review_codex/20261015-current-chat'
$py='C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'
Set-Location 'D:/作品集/ResearchOS/research-os/.local/worktrees/owned-core-stop-effect-state-r5-20261015'
$env:FIXTURE_E2E_MODE='review_missing'
& $py -B -X utf8 "$e/reviewer_logger.py" $py -B -X utf8 "$e/fixture_e2e_negative.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
$env:FIXTURE_E2E_MODE='review_null'
& $py -B -X utf8 "$e/reviewer_logger.py" $py -B -X utf8 "$e/fixture_e2e_negative.py"
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
$env:FIXTURE_E2E_MODE='positive'
& $py -B -X utf8 "$e/reviewer_logger.py" $py -B -X utf8 "$e/fixture_e2e_review.py"
exit $LASTEXITCODE
