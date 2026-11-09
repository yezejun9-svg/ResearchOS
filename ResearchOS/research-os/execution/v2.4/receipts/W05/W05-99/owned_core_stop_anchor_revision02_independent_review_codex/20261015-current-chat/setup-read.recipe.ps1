$a='D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99\owned_core_stop_anchor_revision02_source_codex\20261015-current-chat'
Copy-Item "$a\run_logged.py" "$e\run_logged.py"
$h=[IO.File]::ReadAllText("$a\fixture_e2e_r2.py").Replace('owned-core-stop-20261015-tmp','owned-core-stop-r2-independent-review-20261015')
[IO.File]::WriteAllText("$e\fixture_e2e_r2.py",$h,[Text.UTF8Encoding]::new($false))
$d='D:\作品集\ResearchOS\research-os\.local\owned-core-stop-r2-independent-review-20261015'
New-Item -ItemType Directory -Force -Path "$d\gocache","$d\gotmp" | Out-Null
Get-FileHash "$e\run_logged.py","$e\fixture_e2e_r2.py"
python --version
$w='D:\作品集\ResearchOS\research-os\.local\worktrees\owned-core-stop-anchor-r2-20261015'
git -C $w rev-parse HEAD 'HEAD^{tree}'
git -C $w diff --stat 4f4023c956f84d65743f39ce77d6c8899a21ada1 HEAD
Get-Content "$w\internal\ownedcorestop\contract.go" -Raw
