import subprocess,json
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");W=R/'.local/worktrees/source43-b-stop-finalpath-20261015'
for args in [['git','-c','maintenance.auto=false','-c','gc.auto=0','diff','--','internal/host/roots_windows.go'],['rg','-n','^func |^type |Check|Commit|Rollback|Close','internal/domain/runtime_qualification_failure_windows.go']]:
 p=subprocess.run(args,cwd=W,capture_output=True);print(json.dumps({'argv':args,'exit':p.returncode}));print(p.stdout.decode('utf8'));print(p.stderr.decode('utf8'))
 assert p.returncode==0
p=W/'internal/host/roots_windows_test.go';print('FILE '+str(p));print(p.read_text(encoding='utf8'))
