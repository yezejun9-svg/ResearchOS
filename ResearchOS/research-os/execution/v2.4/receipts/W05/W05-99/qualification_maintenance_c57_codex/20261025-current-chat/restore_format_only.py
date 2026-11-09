from pathlib import Path
import subprocess
import sys
worktree=Path(sys.argv[1]).resolve()
assert worktree.name == 'qualification-maintenance-c57-20261025'
assert subprocess.check_output(['git','-C',str(worktree),'branch','--show-current'], text=True).strip() == 'qualification-maintenance-c57-20261025'
keep={
'adapters/runtime/bridge_windows.go','adapters/runtime/data_root_windows.go',
'internal/domain/backup_prepared_abandonment_handoff.go',
'internal/domain/backup_prepared_abandonment_upgrade.go',
'internal/domain/backup_prepared_abandonment_upgrade_other.go',
'internal/domain/backup_prepared_abandonment_upgrade_windows.go',
'internal/domain/backup_upgrade.go',
'internal/host/runtime_verifier_replacement_windows.go',
'ops/backup/main.go',
}
paths=subprocess.check_output(['git','-C',str(worktree),'diff','--name-only','-z']).split(b'\0')
for raw in paths:
    if not raw: continue
    p=raw.decode('utf-8')
    if p in keep: continue
    target=(worktree / p).resolve()
    assert target.is_relative_to(worktree)
    before=subprocess.check_output(['git','-C',str(worktree),'show','HEAD:'+p])
    target.write_bytes(before)
    print('restored exact HEAD bytes:',p)
