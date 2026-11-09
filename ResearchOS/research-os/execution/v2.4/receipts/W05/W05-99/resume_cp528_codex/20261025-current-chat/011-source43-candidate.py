import json,subprocess,hashlib
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");N=Path(__file__).parent;E=R/'execution/v2.4/receipts/W05/W05-99/source43_b_stop_finalpath_codex/20261025-current-chat';W=R/'.local/worktrees/source43-b-stop-finalpath-20261015'
s=json.loads((N/'continuation-cp529/source43-resume-scope.json').read_text(encoding='utf8'));print('SCOPE KEYS '+str(list(s)))
o=json.loads((R/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp527/source43-B-STOP-finalpath-source-scope.json').read_text(encoding='utf8'));print('OLD SCOPE KEYS '+str(list(o)))
for k,v in o.items():
 if isinstance(v,list):print(k,len(v),str(v[:1])[:350])
print('AUTHOR TOP FILES '+json.dumps([p.name for p in E.iterdir()],ensure_ascii=False))
git=['git','-c','maintenance.auto=false','-c','gc.auto=0'];out={}
for name,args in [('head',['rev-parse','HEAD']),('tree',['rev-parse','HEAD^{tree}']),('status',['status','--porcelain=v1','--untracked-files=all']),('source43',['diff','--name-only','4f4023c956f84d65743f39ce77d6c8899a21ada1','HEAD'])]:
 p=subprocess.run(git+args,cwd=W,capture_output=True);assert p.returncode==0,(name,p.stderr);out[name]=p.stdout.decode('utf8').strip()
assert out['head']=='085b4711afe0c1288448b174eef24ecd5af0551b' and out['tree']=='227d36324fd1053c285d0b2846a2b707ac2df6bd' and not out['status']
out['source43']=out['source43'].splitlines();assert len(out['source43'])==43
out['source_pins']=[{'path':p,'sha256':hashlib.sha256((W/p).read_bytes()).hexdigest(),'bytes':(W/p).stat().st_size}for p in out['source43']]
with (N/'Source43-candidate-root-verification.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in out.items()if k!='source_pins'},ensure_ascii=False,indent=2))
