import json,hashlib
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");N=Path(__file__).parent;E=R/'execution/v2.4/receipts/W05/W05-99/react_workbench_redesign_codex/20261025-current-chat/browser-fixture-02';W=R/'.local/worktrees/react-workbench-redesign-20261025'
refs=[]
for p in E.iterdir():
 if p.suffix=='.png':b=p.read_bytes();refs.append({'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
print(json.dumps({'images':[Path(x['path']).name for x in refs],'report':json.loads((E/'report.json').read_text(encoding='utf8'))},ensure_ascii=False,indent=2))
for name in ['tests/ui/frontend-redesign.cjs','tests/ui/frontend-redesign-fixture.cjs']:
 p=W/name;lines=p.read_text(encoding='utf8').splitlines();print('FILE '+name+' lines='+str(len(lines)))
 if name.endswith('-fixture.cjs'):selected=[(i+1,x)for i,x in enumerate(lines)if i<28 or 'module.exports'in x]
 else:selected=list(enumerate(lines[:145],1))
 print(chr(10).join(str(i)+': '+x for i,x in selected))
note={'review':'Root actual screenshot visual review, not runtime acceptance','reviewed_image':next(x for x in refs if Path(x['path']).name=='native-1440-light.png'),'findings':['Right worktree card title orphan final character and action label wrap','Global disconnected vs sidebar fixed green waiting status contradict','Raw WAITING/NOT_REQUESTED and disabled-button writer state impede readability','Qualification copy too dense and generic prerequisite does not explain current disabled cause'],'sent_to_author':True,'images':refs,'source_frozen':False,'formal_increment':0}
with (N/'React-first-visual-review.json').open('x',encoding='utf8')as f:json.dump(note,f,ensure_ascii=False,indent=2)
