from pathlib import Path
import ast, hashlib, json
R=Path('D:/作品集/ResearchOS/research-os'); O=Path(__file__).parent
S=R/'execution/v2.4/receipts/W13/W13-03/desktop58_root_caller_allocation_revision_preparation_codex/0ca8c518e89a4fd68eb66167bb3b3cc1'
checks=[]; refs={}
def pin(p):
 p=Path(p); b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def check(name,ok,details=None):checks.append({'name':name,'passed':bool(ok),'details':details})
def verify(r):
 p=Path(r['path']);b=p.read_bytes();a=pin(p);refs[str(p)]=a;check('pin:'+str(p),a['sha256']==r['sha256'] and a['bytes']==r['bytes']);return b
def write(name,obj):
 with (O/name).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
h=json.loads(verify({'path':str(S/'handoff.json'),'sha256':'aea2c1b499f5212631db67e9e98187272d3012cf7a437e7dd9cb1d6ec5a01dd7','bytes':2930}))
m=json.loads(verify(h['manifest_ref']));inverse=json.loads(verify(h['inverse_ref']))
for r in m['members'].values():verify(r)
check('manifest member actual key paths',all(Path(r['path']).parent==S and Path(r['path']).name==n for n,r in m['members'].items()))
check('physical package exact',set(p.name for p in S.iterdir() if p.is_file())==set(m['members'])|{'handoff.json','manifest.json'})
old=verify(h['old_source_ref']);new=verify(h['candidate_ref']);baseline=json.loads(verify(h['old_non_author_review_ref']));allocation=json.loads(verify(h['new_root_allocation_ref']))
old_uid=h['old_uid'];new_uid=h['new_uid'];text=new.decode('utf-8');oldtext=old.decode('utf-8')
check('old/new UUID count3',old.count(old_uid.encode())==3 and new.count(new_uid.encode())==3)
check('whole-file inverse',new.replace(new_uid.encode(),old_uid.encode())==old)
check('no old UUID remains',old_uid.encode() not in new)
changes=[i+1 for i,(a,b) in enumerate(zip(old.splitlines(),new.splitlines())) if a!=b]
check('exact three line changes',changes==[11,13,14] and len(old.splitlines())==len(new.splitlines()),changes)
old_ast=ast.parse(oldtext);new_ast=ast.parse(text)
compile(new_ast,str(S/'root-launch-once.desktop58.allocated.proposed.py'),'exec')
check('normalized whole AST equal',ast.dump(ast.parse(text.replace(new_uid,old_uid)),include_attributes=False)==ast.dump(old_ast,include_attributes=False))
olddefs={n.name:n for n in old_ast.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))};newdefs={n.name:n for n in new_ast.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
check('same definitions',set(olddefs)==set(newdefs))
for n,v in olddefs.items():
 check('definition AST:'+n,ast.dump(v,include_attributes=False)==ast.dump(newdefs[n],include_attributes=False))
 check('definition bytes:'+n,ast.get_source_segment(oldtext,v)==ast.get_source_segment(text,newdefs[n]))
assigns={}
for n in new_ast.body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):assigns.setdefault(n.targets[0].id,[]).append(n.value)
check('future constants initially None',all(isinstance(assigns[n][0],ast.Constant) and assigns[n][0].value is None for n in ['OUT','SCOPE_SHA','GRANT_SHA']))
check('handoff future inputs NULL',all(h[k] is None for k in ['future_caller_output','future_grant_sha','future_scope_sha']))
check('allocated run UUID',ast.literal_eval(assigns['RUN_UUID'][0])==allocation['run_uuid']==new_uid)
reg=R/ast.literal_eval(assigns['REGISTRATION'][0].right)
auth=(R/'execution/v2.4/receipts/W13/W13-03')/ast.literal_eval(assigns['AUTH_ROOT'][0].right)
check('allocated registration exact',reg==Path(allocation['registration_namespace']))
check('allocated authorization exact',auth==Path(allocation['roots']['new_authorization_root']))
check('allocation before exact',allocation['before']==[334,162,532])
check('allocation next cut unfrozen',allocation['after_checkpoint']==335 and allocation['after_ownership']==163 and allocation['after_failure_count'] is None)
check('allocation unexecuted',allocation['execution_authorized'] is False and allocation['native_target_calls']==0 and allocation['canonical_writes']==0 and allocation['execution_leaves_created']==0)
leaf_facts={k:{'path':v,'exists':Path(v).exists()} for k,v in allocation['roots'].items()}
check('five future execution leaves absent',len(leaf_facts)==5 and all(not v['exists'] for v in leaf_facts.values()),leaf_facts)
check('baseline actual source pin',baseline['caller_ref']==h['old_source_ref'])
check('baseline source-only READY',baseline['decision']=='READY_SOURCE_PREPARATION_ONLY' and baseline['requested_changes']==[])
calls=[n for n in ast.walk(new_ast) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='subprocess' and n.func.attr=='run']
check('single subprocess timeout7800',len(calls)==1 and next(k.value.value for k in calls[0].keywords if k.arg=='timeout')==7800)
check('caller OS false declarations unchanged',text.count("'caller_OS_lifecycle_qualification': False")==oldtext.count("'caller_OS_lifecycle_qualification': False")==2)
check('unchanged caps',all(s in text for s in ["scope['inner_seconds'] == 7200","scope['outer_seconds'] == 7500","scope['cleanup_seconds'] == 5","scope['controller_evidence_reserve_seconds'] == 60","scope['launcher_evidence_reserve_seconds'] == 60"]))
write('audit.json',{'schema':'researchos.desktop58-caller-allocation-readonly-audit.v1','checks':checks,'passed':sum(x['passed'] for x in checks),'failed':[x for x in checks if not x['passed']],'input_refs':list(refs.values()),'candidate_imported_or_executed':False,'AST_compile_only':True,'new_failure_origins':[]})
print(json.dumps({'checks':len(checks),'failed':[x for x in checks if not x['passed']],'audit_ref':pin(O/'audit.json')},ensure_ascii=False))
