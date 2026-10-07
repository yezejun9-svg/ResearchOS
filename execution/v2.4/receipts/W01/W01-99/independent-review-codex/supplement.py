import datetime,hashlib,json,pathlib,subprocess,sys
R=pathlib.Path('D:/作品集/ResearchOS/research-os');O=pathlib.Path(__file__).resolve().parent;B=O.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[];refs={}
def check(id,ok,detail=None):
 checks.append({'id':id,'ok':bool(ok),'detail':detail});print(json.dumps(checks[-1],ensure_ascii=False));assert ok,id
def gitfile(rev,path):return subprocess.check_output(['git','show',rev+':'+path],cwd=R)
pin=read(R/'qualification/v2.4/parent_inputs.json'); sample=R/pin['current_sample']; original=read(sample/'receipt.json')
source_bindings={};unavailable=[];drift=[]
for p,h in original['source_inputs_sha256'].items():
 text=p.replace('\\','/'); marker='/.local/worktrees/codex-w0199/'
 if marker in text:text=str(R).replace('\\','/')+'/'+text.split(marker,1)[1]
 target=pathlib.Path(text)
 # Current gate code was intentionally repaired after original observation; product sources/tools were not.
 if '/qualification/v2.4/' in text or '/execution/' in text or '/.local/w0199/' in text:continue
 if not target.is_file():unavailable.append(text);continue
 source_bindings[text]=h
 if sha(target)!=h:drift.append(text)
check('original-product-tool-build-inputs',not unavailable and not drift,{'count':len(source_bindings),'unavailable':unavailable,'drift':drift})
refs.update(source_bindings)
for rel in ['execution/v2.4/route.json','execution/v2.4/reuse_decisions.json','docs/adr/ADR-next-v24-route.md','execution/v2.4/receipts/W01/W01-02/carry_forward_obligations.json','execution/commands.json','ops/ci/core_evidence.py']:
 current=(R/rel).read_bytes();check('preserved-'+rel,current==gitfile('4680f3e7',rel));refs[str(R/rel)]=sha(R/rel)
old=json.loads(gitfile('4680f3e7','execution/v2.4/commands.json'));new=read(R/'execution/v2.4/commands.json')
check('registry-only-core-qualified-added',new['revision']==34 and old['revision']==33 and set(new['commands'])==set(old['commands'])|{'core.qualify'} and all(v==new['commands'][k] for k,v in old['commands'].items()),{'old_command_count':len(old['commands']),'new_command_count':len(new['commands'])})
refs[str(R/'execution/v2.4/commands.json')]=sha(R/'execution/v2.4/commands.json')
state=read(R/'execution/v2.4/step_state.json');states={x['id']:x for x in state['steps']};dep_results=[]
for dep in ['W00-99','W01-01','W01-02','W01-03']:
 row=states[dep]; bad=[]
 for e in row['evidence']:
  p=R/'execution/v2.4'/e['path'];refs[str(p)]=sha(p)
  if refs[str(p)]!=e['sha256']:bad.append(e['path'])
 check('prerequisite-'+dep,row['status']=='ACCEPTED' and not bad,{'status':row['status'],'evidence_count':len(row['evidence']),'drift':bad,'verifier_id':row.get('verifier_id')})
 dep_results.append({'id':dep,'status':row['status'],'evidence':row['evidence'],'verifier_id':row.get('verifier_id')})
check('parent-remains-unaccepted-during-review',states['W01-99']['status']!='ACCEPTED',states['W01-99']['status'])
check('all-reference-hashes-stable',all(sha(pathlib.Path(p))==h for p,h in refs.items()))
result={'checks':checks,'reference_hashes':refs,'prerequisites':dep_results,'source_inputs_interpretation':'Original observation bindings independently mapped from unchanged candidate product paths to integrated main. Historical gate code excluded because later parser/cleanup/provenance changes are separately reviewed. No execution of a newly built integrated package claimed.','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
with (O/'supplement.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'status':'PASS','checks':len(checks),'original_product_tool_inputs':len(source_bindings)}))
