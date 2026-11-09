import json,subprocess,hashlib
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");N=Path(__file__).parent;W=R/'.local/worktrees/react-workbench-redesign-20261025'
p=R/'ops/ci/ui.py';lines=p.read_text(encoding='utf8').splitlines();print('FILE ops/ci/ui.py lines='+str(len(lines)));print(chr(10).join(str(i)+': '+x for i,x in enumerate(lines[:105],1)))
git=['git','-c','maintenance.auto=false','-c','gc.auto=0'];out={}
for name,args in [('head',['rev-parse','HEAD']),('tree',['rev-parse','HEAD^{tree}']),('status',['status','--porcelain=v1','--untracked-files=all']),('changed',['diff','--name-only','4f4023c956f84d65743f39ce77d6c8899a21ada1','HEAD'])]:
 q=subprocess.run(git+args,cwd=W,capture_output=True);assert q.returncode==0;out[name]=q.stdout.decode('utf8').strip()
out['ci_source']={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
with (N/'React-source13-candidate-and-ci-gap.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=False,indent=2))
