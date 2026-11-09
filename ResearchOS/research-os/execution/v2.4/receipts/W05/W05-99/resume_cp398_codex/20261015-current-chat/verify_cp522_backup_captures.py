import hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');E=R/'execution/v2.4/receipts/W05/W05-99';B=E/'resume_cp398_codex/20261015-current-chat';Q=E/'online_backup_fixture_qualification_codex/20261015-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 x=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
v=read(Q/'command-index.json');rows=v['commands'];refs=[];complete=[];missing=[];nonzero=[];exit_keys=None
for row in rows:
 p=Q/row['recipe'];a=ref(p);assert a['sha256']==row['recipe_sha256'];refs.append(a)
 paths={k:Q/(row.get(k)or(row['id']+suffix)) for k,suffix in [('exit','.exit.json'),('stdout','.stdout.raw'),('stderr','.stderr.raw')]}
 if all(p.is_file()for p in paths.values()):
  for p in paths.values():refs.append(ref(p))
  x=read(paths['exit']);exit_keys=list(x)if exit_keys is None else exit_keys
  native=x.get('native_exit',x.get('nativeExit',x.get('exit_code',x.get('exitCode'))))
  assert native is not None,(row['id'],list(x))
  if row.get('native_exit')is not None:assert native==row['native_exit'],row['id']
  complete.append({'id':row['id'],'native_exit':native,'exit':ref(paths['exit'])})
  if native!=0:nonzero.append(complete[-1])
 else:missing.append({'id':row['id'],'paths':{k:str(p)for k,p in paths.items()},'present':{k:p.is_file()for k,p in paths.items()}})
assert len(rows)==195 and len(complete)==194 and len(nonzero)==25 and len(missing)==1 and missing[0]['id']=='bootstrap-read'
sup=read(Q/'capture-index-supplement.json')
out={'recipe_count':len(rows),'currently_complete':len(complete),'frozen_complete':193,'missing':missing,'native_nonzero':nonzero,'refs':refs,'exit_keys':exit_keys,'supplement_nonzero':sup['nonzero_native_exit'],'misplaced_bootstrap_prewrite':sup['misplaced_bootstrap_prewrite'],'actual_authority':False,'formal_increment':0}
p=B/'cp522-backup-capture-verification.json';assert not p.exists();p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'output':ref(p),'recipe_count':195,'currently_complete':194,'frozen_complete':193,'native_nonzero_count':25,'verified_files':len(refs),'exit_keys':exit_keys,'nonzero_classification':sup['nonzero_native_exit'],'path_deviation':sup['misplaced_bootstrap_prewrite']},ensure_ascii=False))
