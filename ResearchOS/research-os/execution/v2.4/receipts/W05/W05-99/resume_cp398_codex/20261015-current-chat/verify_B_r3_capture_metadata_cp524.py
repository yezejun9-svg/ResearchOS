import json,hashlib
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=Path(__file__).parent;S=R/'execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision03_source_codex/20261015-current-chat';W=R/'.local/worktrees/qualification-failure-b-r3-20261015'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 x=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
m=read(S/'FINAL-manifest.json');sources=[]
for name,x in m['source_hashes'].items():
 p=W/name;a=ref(p);sha=x if isinstance(x,str)else x['sha256'];assert a['sha256']==sha
 if isinstance(x,dict)and'bytes'in x:assert a['bytes']==x['bytes']
 sources.append(a)
rows=read(S/'command-index.json');cap=[];metadata_schema={};gaps=[]
for row in rows:
 d=(S/row['stdout']['path']).parent;files=[p for p in d.iterdir()if p.is_file()]
 record={'id':row['id'],'exit':row['exit'],'files':[ref(p)for p in files]}
 for p in files:
  if p.suffix=='.json':
   x=read(p);metadata_schema.setdefault(p.name,list(x)if isinstance(x,dict)else type(x).__name__)
   if isinstance(x,dict):
    for k in ['native_exit','nativeExit','exit_code','exitCode','exit']:
     if k in x and isinstance(x[k],int):assert x[k]==row['exit'],(row['id'],p.name);break
 if not any('recipe'in p.name or'command'in p.name for p in files):gaps.append({'id':row['id'],'missing':'prewritten_recipe_or_command'})
 if not any('result'in p.name or'exit'in p.name for p in files):gaps.append({'id':row['id'],'missing':'result_or_exit'})
 cap.append(record)
bootstrap=[ref(p)for p in S.glob('CP522-bootstrap-*')if p.is_file()]
add=S/'cleanup-rejection-addendum.json';assert ref(add)['sha256']=='1e7cd21ae8e41afb513a2c01dcfff59414c27651584f7d64fed2d555733171cc'
out={'source9':sources,'captures':cap,'metadata_schema':metadata_schema,'capture_gaps':gaps,'bootstrap':bootstrap,'cleanup_rejection_addendum':ref(add),'candidate_accepted':False}
p=B/'B-r3-capture-metadata-verification.json';assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'output':ref(p),'source9':len(sources),'commands':len(cap),'capture_files':sum(len(x['files'])for x in cap),'metadata_schema':metadata_schema,'capture_gaps':gaps,'bootstrap':bootstrap,'cleanup_addendum':read(add)},ensure_ascii=False))
