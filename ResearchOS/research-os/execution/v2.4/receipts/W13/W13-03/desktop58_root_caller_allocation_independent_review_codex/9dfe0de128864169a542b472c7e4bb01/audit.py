import ast,hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;P=R/'execution/v2.4/receipts/W13/W13-03'
N=P/'desktop58_root_caller_allocation72ff_source_preparation_codex/7c863730e8d444ada5196d332e70cbc8'
OLD=P/'desktop58_root_caller_allocation_independent_review_codex/7c8e667263a24c9d9b50c5c3e73ab559/review.json'
I={};C=[]
def path(x):
 p=Path(x);return p if p.is_absolute() else R/p
def raw(x):
 p=path(x);b=p.read_bytes();I[str(p)]={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b
def ref(x):raw(x);return I[str(path(x))]
def doc(x):return json.loads(raw(x))
def ck(n,v):C.append({'check':n,'passed':bool(v)})
def verify(r):
 b=raw(r['path']);ck('pin '+r['path'],len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']);return b
def save(n,x):
 with (O/n).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 return ref(O/n)
h=doc(N/'handoff.json');m=doc(N/'manifest.json');old=doc(OLD)
ck('handoff expected',ref(N/'handoff.json')['sha256']=='cc01977eb7be007c749aba88ded6c1ea73f73aacad1424b1593e4a57ff753bf0')
ck('MF expected',ref(N/'manifest.json')['sha256']=='9320f36c17451906863e86901204cd2020d353fdef5ab1ac0cd2a4c5800521d2')
ck('four exact manifestmembers',m['count']==len(m['entries'])==4 and m['excluded_only_self'] is True and len({x['path'] for x in m['entries']})==4)
for r in m['entries']:verify(r);ck('own source member '+r['path'],path(r['path']).parent==N)
for k in ['inverse_ref','static_audit_ref','allocation_ref','seed_ref']:verify(h[k])
nb=verify(h['caller_ref']);ob=verify(h['seed_ref']);alloc=json.loads(verify(h['allocation_ref']));A=path(h['allocation_ref']['path']).parent
uid='72ff32d0d24a42c4a8effd849d54f882';seeduid='429e1734d9da4efba276680e78e2510b';nt=nb.decode();ot=ob.decode()
ck('only three UID occurrences',nb.count(uid.encode())==ob.count(seeduid.encode())==3 and seeduid.encode() not in nb)
ck('whole byteinverse oldsource exact',nb.replace(uid.encode(),seeduid.encode())==ob)
changed=[i+1 for i,(x,y) in enumerate(zip(ob.splitlines(keepends=True),nb.splitlines(keepends=True))) if x!=y]
ck('only lines11/13/14',changed==[11,13,14] and len(ob.splitlines())==len(nb.splitlines()))
ck('whole ASTinverse exact',ast.dump(ast.parse(nt.replace(uid,seeduid)),include_attributes=False)==ast.dump(ast.parse(ot),include_attributes=False))
constants={}
for n in ast.parse(nt).body:
 if isinstance(n,ast.Assign):
  for t in n.targets:
   if isinstance(t,ast.Name):
    try:constants[t.id]=ast.literal_eval(n.value)
    except (TypeError,ValueError):pass
ck('null futureactualvalues',constants['OUT'] is None and constants['SCOPE_SHA'] is None and constants['GRANT_SHA'] is None)
ck('run_uuid allocated',constants['RUN_UUID']==alloc['run_uuid']==uid)
ck('registrationliteral actualallocation',nt.splitlines()[10]=="REGISTRATION = ROOT / '"+A.relative_to(R).as_posix()+"'" and path(alloc['registration_namespace'])==A)
ck('authliteral actualallocation',nt.splitlines()[12]=="AUTH_ROOT = DESKTOP_RECEIPTS / 'desktop58_finite_authorization_codex/"+uid+"'" and path(alloc['roots']['new_authorization_root'])==P/'desktop58_finite_authorization_codex'/uid)
ck('allocation ungranted',alloc['before']==[334,162,532] and alloc['after_checkpoint']==335 and alloc['after_ownership']==163 and alloc['after_failure_count'] is None and alloc['execution_authorized'] is False and alloc['canonical_writes']==0 and alloc['formal_increment']==0)
ck('preparationflags',h['candidate_execution'] is False and h['caller_OS_lifecycle_qualification'] is False and h['source_acceptance'] is False and h['formal_increment']==0)
ck('oldindependentreviewexact',ref(OLD)['sha256']=='ddecfe2297ab99c3ec6f9d31c25430ebbecffee6f874a51bc8d1280d5d71f6b2' and old['decision']=='READY_SOURCE_PREPARATION_ONLY' and old['candidate_ref']['sha256']==h['seed_ref']['sha256'])
for k,v in alloc['roots'].items():ck('future leaf absent '+k,not path(v).exists())
canon=doc(A/'canonical-before.json');ck('canonical-before expected SHA',ref(A/'canonical-before.json')['sha256']=='5ebf4510c8c3a174276f993f7237f5ec122811bf832570b24ee8bcff960be77b')
ck('canonical exact order',[x['canonical_path'] for x in canon['entries']]==['execution/v2.4/'+x+'.json' for x in ['checkpoint','path_ownership','step_state','commands']])
docs=[]
for row in canon['entries']:
 br=verify(row['ref']);ck('live equals original '+row['canonical_path'],raw(row['canonical_path'])==br);docs.append(json.loads(br))
ck('actualtuple/head frozen', [docs[0]['revision'],docs[1]['revision'],len(docs[0]['failure_counters'])]==[334,162,532] and docs[0]['head']=='e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7')
for label,needle in [
 ('3argv',"need(len(sys.argv) == 4"),('scope/grantargv',"SCOPE_SHA, GRANT_SHA = sys.argv[1:3]"),('fresh caller',"need(OUT.is_dir() and not any(OUT.iterdir())"),
 ('isolated flags',"'-I', '-S', '-X', 'utf8'"),('timeout',"timeout=7800, check=False"),('budgets',"scope['inner_seconds'] == 7200 and scope['outer_seconds'] == 7500"),('reserve',"scope['controller_evidence_reserve_seconds'] == 60 and"),
 ('rawexclusive',"'root-launch.stdout.raw').open('xb')"),('null result',"'actual_launcher_native_exit': result.returncode if result else None"),('secondary errors',"secondary.append({'stage': 'invocation-receipt'"),('OSqualification false',"'caller_OS_lifecycle_qualification': False"),('publicenv',"{'SystemRoot', 'WINDIR', 'ComSpec', 'PATH', 'PATHEXT'}"),('retryfalse',"'automatic_retry': False")]:ck('unchanged behavior '+label,needle in nt)
ck('single subprocess call AST',sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='subprocess' and n.func.attr=='run' for n in ast.walk(ast.parse(nt)))==1)
audit=save('audit.json',{'schema':'researchos.desktop58-root-caller-allocation-static-audit.v1','checks':C,'failed':[x for x in C if not x['passed']],'input_refs':list(I.values()),'changed_source_lines':changed,'whole_inverse':True,'source_non_author':True,'actual_candidate_executed':False,'new_failure_origins':[]})
decision='READY_SOURCE_PREPARATION_ONLY' if all(x['passed'] for x in C) else 'REQUEST_CHANGES'
review={'schema':'researchos.desktop58-root-caller-allocation-independent-source-review.v1','reviewer':'codex:/root/w05_merge_review','non_author':True,'decision':decision,'requested_changes':[x for x in C if not x['passed']],'caller_sha256':h['caller_ref']['sha256'],'candidate_ref':h['caller_ref'],'original_source_ref':h['seed_ref'],'source_handoff_ref':ref(N/'handoff.json'),'source_manifest_ref':ref(N/'manifest.json'),'inverse_ref':h['inverse_ref'],'allocation_ref':h['allocation_ref'],'canonical_before_ref':ref(A/'canonical-before.json'),'baseline_review_ref':ref(OLD),'audit_ref':audit,'tool_observations_ref':ref(O/'tool-observations.json'),'checks_passed':sum(x['passed'] for x in C),'changed_source_lines':changed,'future_scope_sha':None,'future_grant_sha':None,'future_caller_output':None,'required_future_inputs':['Root reviewed actual new Scope SHA','Actual Root CAS/seal and unique Grant SHA','Separate fresh empty caller output and reviewed literal three-argument launch'],'scope_ref_protocol_note':'Caller locally pins scope/grant as ABS observational intent references and passes path+SHA arguments to launcher. It does not produce prepared/CP/OW/grant authority scope_ref dictionaries. Those must be canonical ROOT-relative from first prepare through grant. Do not globally rewrite caller observational/code/runtime ABS refs.','boundary_note':'All other bytes match reviewed caller. Pre-subprocess argument/output/pin failures retain tool stderr; caller does not claim whole-process OS lifecycle proof. Subprocess/raw-open failures preserve nullable launcher exit/firstcause/secondary and exclusive raw. Actual scopes, grants and caller output are not yet bound by this source review.','actual_candidate_imported':False,'actual_candidate_executed':False,'actual_CAS_calls':0,'actual_product_calls':0,'actual_execution_authorized':False,'caller_OS_lifecycle_qualification':False,'source_acceptance':False,'formal_increment':0,'counter_mutations':False,'new_failure_origins':[],'new_failed_tool_count':0,'status':'STOPPED'}
rr=save('review.json',review);hr=save('handoff.json',{'schema':'researchos.independent-review-handoff.v1','reviewer':review['reviewer'],'decision':decision,'review_ref':rr,'audit_ref':audit,'status':'STOPPED','new_failure_count':0,'new_failure_origins':[],'manifest_filename':'manifest.json'})
entries=[ref(x) for x in sorted(O.iterdir()) if x.is_file() and x.name!='manifest.json'];mr=save('manifest.json',{'schema':'researchos.public-review-manifest.v1','entries':entries,'count':len(entries),'self_excluded':True})
print(json.dumps({'decision':decision,'checks':len(C),'failed':[x for x in C if not x['passed']],'review_ref':rr,'manifest_ref':mr,'handoff_ref':hr,'new_failure_count':0},ensure_ascii=False))
