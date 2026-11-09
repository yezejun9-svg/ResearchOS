# B command and diagnostic ledger

The frozen evidence manifest indexes b01–b110; the b01–b107 wording below denotes the development and source-diagnostic subset before report finalization.

`B-evidence-manifest.json` lists all b01–b107 recipes and captures with exit code and raw stdout/stderr SHA256. Raw bytes are alongside each command/result record. Recipe JSON was written before each actual logged process. Three early malformed-recipe attempts (b09, b15, b20) failed before native process execution; corrected recipes were used for the logged commands. The manifest's `capture_gaps=[]` refers to the final 107 recorded recipes, not these pre-execution mistakes. Some early exploratory reads were inadvertently made outside `run_logged.py`; they did not mutate Source and are not presented as fully captured commands.

Development failures are retained: b04, b25, b31, b32, b36, b46–b55, b60, b63, b65, b67, b75, b76 and b104 have nonzero or unavailable native exit in their result files. b36 could not find `gofmt` on PATH; explicit Go 1.27.1 executable was used afterward. b75/b76 blocked-broker tests timed out during synchronization debugging; b77 and final b78 pass the corrected bounded test. The b75 test process survived its parent command; b83 identified exact `domain.test.exe` path/PID, b84 stopped only that orphan, and b85 removed its isolated test temp. b82 had a PowerShell nonterminating `Remove-Item` error while the orphan still held files, despite native exit 0; its nonempty stderr is retained. b104's `rg` query named two absent test files, exited 2, and was only a lookup error. No failed attempt was rewritten into PASS.

b91 commit capture: argv `["git","commit","-m","Implement bounded first-gate qualification failure closure"]`; cwd `D:\作品集\ResearchOS\research-os\.local\worktrees\qualification-failure-b-20261015`; `env_allowlist={}` and inherited environment not exhaustively captured; UTC 12:32:36.950243–12:32:45.736815; native exit 0. Raw stderr SHA256 `76b247278b63ff1d1fa75526af822d31b1bbf6f51a142d39754a412b9ad4609b`, 212 bytes:

```text
Auto packing the repository for optimum performance.
See "git help gc" for manual housekeeping.
fatal: bad tree object 064d33818101c336e5a587e65e844c107d2e97f2
fatal: failed to run repack
error: task 'gc' failed
```

This invocation **did not** pass `-c maintenance.auto=false -c gc.auto=0`, contrary to the card. The stderr shows this invocation actually launched automatic GC/repack; it is not merely an old `gc.log` warning. No GC/repack/prune/config fix was attempted afterward. Read-only b92 HEAD, b93/b106 clean status, b94 show/check and b97 tree succeeded. Root is separately checking the object issue's scope. All historical diagnostic bytes remain intact.
