import hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');B=Path(__file__).parent;S=R/'execution/v2.4/receipts/W05/W05-99/qualification_failure_b_revision03_source_codex/20261015-current-chat'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 x=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
rows=read(S/'command-index.json');out=[]
for row in rows:
 d=(S/row['stdout']['path']).parent;p=d/'invocation.json';v=read(p);assert v['id']==row['id']and v['argv']==row['argv']and v['cwd']==row['cwd']
 assert 'env'in v and 'recipe'in v and 'start_utc'in v
 recipe=v['recipe'];x={'id':row['id'],'invocation':ref(p),'recipe_type':type(recipe).__name__,'recipe':recipe}
 if isinstance(recipe,str)and len(recipe)<500 and'\n'not in recipe:
  q=Path(recipe)
  if not q.is_absolute():q=S/q
  x['recipe_is_existing_file']=q.is_file()
  if q.is_file():x['recipe_ref']=ref(q)
 out.append(x)
helpers=[p for p in S.iterdir()if p.is_file()and p.suffix=='.py']
print('HELPERS',json.dumps([p.name for p in helpers]))
for p in helpers:
 if p.name in ['run_command.py','run_logged.py','run.py','command_runner.py','logger.py']:
  print('LOGGER',p.name,p.read_text(encoding='utf-8-sig')[:7000])
print('RECIPES_FIRST_TWO',json.dumps(out[:2],ensure_ascii=False))
p=B/'B-r3-invocation-recipe-correction.json';assert not p.exists();p.write_text(json.dumps({'verified_invocations':73,'records':out,'corrects':'B-r3-capture-metadata-verification.json filename-only heuristic failed to recognize invocation.json and external recipe; not73actualgaps. See retainedlogger/prewritteninvocations.','prior_output_preserved':True},ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('OUTPUT',json.dumps(ref(p),ensure_ascii=False))
