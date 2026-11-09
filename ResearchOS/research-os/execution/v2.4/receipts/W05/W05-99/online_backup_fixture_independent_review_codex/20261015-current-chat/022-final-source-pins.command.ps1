[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
Get-Content 'D:\作品集\ResearchOS\research-os\.local\worktrees\online-backup-fixture-qualification-20261015\AGENTS.md' -Raw -Encoding utf8
$code=@"
from driver import E,R,W,T,GO,run,save
import hashlib
assert run('s01-final-status',['git','-C',W,'status','--porcelain=v1']).strip()==''
assert run('s02-final-head',['git','-C',W,'rev-parse','HEAD']).strip()=='4f4023c956f84d65743f39ce77d6c8899a21ada1'
assert run('s03-final-tree',['git','-C',W,'rev-parse','HEAD^{tree}']).strip()=='3db13a15cc52b2b0bd75cae3452c66509a9f55c9'
run('s04-go-build-info',[GO,'version','-m',T/'build/backup.exe'])
names=['ops/backup/main.go','internal/store/sqlite.go','internal/domain/backup.go','internal/domain/backup_workspace.go','internal/domain/backup_command_queue.go','internal/domain/backup_recovery.go','internal/domain/store.go','internal/host/host.go','internal/host/roots.go','internal/host/vault.go','internal/host/selections.go','internal/host/state.go','internal/host/backup_windows.go','apps/control/main.go']
paths=[W/n for n in names]+list((T/'build').glob('*.exe'))+list(E.glob('*.go'))+list(E.glob('*.py'))+list(E.glob('*.overlay.json'))
save('source-helper-native-pins.json',[dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths])
print('SOURCE_CLEAN_HEAD_TREE_AND_NATIVE_HELPERS_PINNED')
"@
[IO.File]::WriteAllText("$PSScriptRoot\final_pins.py",$code,[Text.UTF8Encoding]::new($false))
python -B -Xutf8 "$PSScriptRoot\final_pins.py"
exit $LASTEXITCODE