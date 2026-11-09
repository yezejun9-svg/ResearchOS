$w='D:\作品集\ResearchOS\research-os\.local\worktrees\owned-core-stop-anchor-r2-20261015'
Get-Content "$w\internal\store\owned_stop_backup.go","$w\internal\store\owned_stop_barrier_windows.go","$w\ops\owned_core_stop\main_windows.go","$w\ops\owned_core_stop\main_nonwindows.go" -Raw
Get-Content "$w\internal\ownedcorestop\journal_windows.go" | Select-Object -Skip 140 -First 80
