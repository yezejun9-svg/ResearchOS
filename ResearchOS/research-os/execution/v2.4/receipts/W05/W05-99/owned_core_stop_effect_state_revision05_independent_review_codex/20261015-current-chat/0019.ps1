$w='D:/作品集/ResearchOS/research-os/.local/worktrees/owned-core-stop-effect-state-r5-20261015'
Get-Content "$w/internal/store/owned_stop_barrier_windows_test.go","$w/internal/store/owned_stop_backup_test.go","$w/ops/owned_core_stop/main_windows_test.go"
Get-Content "$w/ops/supervisor/owned_core_handle_windows_test.go" | Select-Object -First 270
