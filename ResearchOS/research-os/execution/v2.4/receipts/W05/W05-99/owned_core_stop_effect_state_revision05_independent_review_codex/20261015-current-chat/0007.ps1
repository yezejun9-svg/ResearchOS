$ErrorActionPreference='Stop'
$e='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/owned_core_stop_effect_state_revision05_independent_review_codex/20261015-current-chat'
$w='D:/作品集/ResearchOS/research-os/.local/worktrees/owned-core-stop-effect-state-r5-20261015'
$t='D:/作品集/ResearchOS/research-os/.local/owned-core-stop-r5-independent-review-20261015-tmp'
$py='C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'
$go='D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe'
Set-Location $w
& $py -B -X utf8 "$e/reviewer_logger.py" $go test -count=1 -v -overlay "$e/store-overlay.json" -run 'TestReviewMalformedModelEffectMustNotBeSafe|TestReviewFiniteEffectStateSemantics|TestOwnedStopLatestEffectStateFiniteMatrix' ./internal/store
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
& $py -B -X utf8 "$e/reviewer_logger.py" $go build -o "$t/fixture-r4.exe" ./ops/owned_core_stop/fixture
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
& $py -B -X utf8 "$e/reviewer_logger.py" $go build -o "$t/fixture-parent-r4.exe" "$e/fixture_parent_r4.go"
exit $LASTEXITCODE
