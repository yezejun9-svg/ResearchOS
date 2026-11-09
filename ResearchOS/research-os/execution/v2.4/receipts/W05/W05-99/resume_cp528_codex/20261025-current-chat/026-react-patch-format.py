import json,subprocess,hashlib
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");N=Path(__file__).parent;E=R/'execution/v2.4/receipts/W05/W05-99/react_workbench_redesign_codex/20261025-current-chat';W=R/'.local/worktrees/react-workbench-redesign-20261025';s=json.loads((E/'SOURCE14-SEAL.json').read_text(encoding='utf8'))
git=['git','-c','maintenance.auto=false','-c','gc.auto=0'];out={}
for label,start,name in [('full',s['base_commit'],'source14-full.patch'),('ci',s['source13_commit'],'source14-ci.patch')]:
 actual=(E/name).read_bytes();plain=subprocess.check_output(git+['diff','--binary',start,s['final_commit']],cwd=W);full=subprocess.check_output(git+['diff','--binary','--full-index',start,s['final_commit']],cwd=W)
 pos=next((i for i,(a,b)in enumerate(zip(actual,plain))if a!=b),min(len(actual),len(plain)))
 out[label]={'artifact_bytes':len(actual),'plain_bytes':len(plain),'full_index_bytes':len(full),'equals_plain':actual==plain,'equals_full_index':actual==full,'first_difference':pos,'artifact_fragment':actual[max(0,pos-80):pos+150].decode('utf8',errors='replace'),'plain_fragment':plain[max(0,pos-80):pos+150].decode('utf8',errors='replace'),'normalized_newlines_equal':actual.replace(bytes([13,10]),bytes([10]))==plain.replace(bytes([13,10]),bytes([10]))}
paths=subprocess.check_output(['rg','--files',str(E/'commands'),'-g','*.json'],cwd=R).decode('utf8').splitlines();found=[]
for name in paths:
 if'patch'in name.lower():
  p=Path(name);v=json.loads(p.read_text(encoding='utf-8-sig'))
  found.append({'path':str(p),'keys':list(v),'argv':v.get('argv',v.get('command'))})
out['patch_commands']=found
with(N/'React-patch-format-diagnostic.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=False,indent=2))
