$r='D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/owned_core_stop_authority_revision04_independent_review_codex/20261015-current-chat'
Get-Content "$r/review.json"
$w='D:/作品集/ResearchOS/research-os/.local/worktrees/owned-core-stop-effect-state-r5-20261015'
rg -n '^func Test|^func .*test|^func .*Fixture' "$w/internal/ownedcorestop" "$w/internal/store/owned_stop_backup_test.go" "$w/internal/store/owned_stop_barrier_windows_test.go" "$w/internal/host/owned_core_stop_identity_windows_test.go" "$w/ops/owned_core_stop/main_windows_test.go"
