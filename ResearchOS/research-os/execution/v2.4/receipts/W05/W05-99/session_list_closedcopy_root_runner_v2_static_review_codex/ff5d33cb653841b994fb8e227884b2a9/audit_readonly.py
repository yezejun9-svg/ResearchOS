from pathlib import Path
import ast,hashlib,json,difflib,datetime
R=Path('D:/作品集/ResearchOS/research-os');N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/session-list-closedcopy-root-replay-draft';O=Path(__file__).parent
checks=[];refs=[]
def ck(name,ok):
 checks.append({'check':name,'passed':bool(ok)})
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p):
 p=Path(p);b=p.read_bytes();refs.append(ref(p));return b
def verify(x):
 p=Path(x['path']);p=p if p.is_absolute() else R/p;b=read(p);ck('ref '+str(p),hashlib.sha256(b).hexdigest()==x['sha256'] and len(b)==x['bytes']);return b
def save(n,d):
 b=(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode();(O/n).write_bytes(b);return ref(O/n)
pins={'root_finite14_replay.v2.py':'32af67288b42f4865f021ff9b5a7d8adeabe0249a82c4734c89a3a6caeaf18f9','root_finite14_scope.v2.json':'1f67e7dece77b444b53a555ed193f3402b566e7960cf8cdef68b38e37d80d0ef','authorization_gate.v2.py':'4bfea9824db523f4c7a5953774a9d87abbdad34bae4fc1b68b68b4bf5e863e42','launch.v2.py':'8210a2b06c3bd2319918be44a21d6a10fe442c0c3f0b9f29ffe96000b39502e1'}
raw={}
for name,h in pins.items():
 raw[name]=read(N/name);ck('pin '+name,hashlib.sha256(raw[name]).hexdigest()==h);(O/('input.'+name)).write_bytes(raw[name])
 if name.endswith('.py'):ast.parse(raw[name]);ck('AST '+name,True)
scope=json.loads(raw['root_finite14_scope.v2.json'])
for k,v in scope.items():
 if isinstance(v,dict) and {'path','sha256','bytes'}<=v.keys():verify(v)
runtime=json.loads(verify(scope['runtime_resources_ref']))
for item in runtime['files']:verify(item)
ck('runtime unique1211',len(runtime['files'])==len({x['path'] for x in runtime['files']})==1211)
old=verify(scope['previous_runner_draft_ref']);a=ast.parse(old);b=ast.parse(raw['root_finite14_replay.v2.py'])
af={n.name:ast.dump(n,include_attributes=False) for n in a.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))};bf={n.name:ast.dump(n,include_attributes=False) for n in b.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
for name in ['run','runtime_paths','check_stage','check_wire','typed_cells','canonical_saved_cells']:
 ck('unchanged original function '+name,af[name]==bf[name])
for name in ['NAMES','SOURCES','PUBLIC_JEV','RESOURCE_PLAN_REF','CANDIDATE','SOURCE_PARENT','BASE']:
 def value(tree):
  for node in tree.body:
   if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets):return ast.literal_eval(node.value)
 ck('unchanged constant '+name,value(a)==value(b))
(O/'runner.diff.txt').write_text(''.join(difflib.unified_diff(old.decode().splitlines(True),raw['root_finite14_replay.v2.py'].decode().splitlines(True),fromfile='original',tofile='v2')),encoding='utf-8')
ck('14cases/caps',len(scope['ordered_cases'])==14 and scope['limits']=={'cases':14,'per_case_HTTP_maximum':16,'total_HTTP_maximum':224,'SDK_MODEL_Node_external_paid_private_calls':0})
for name,h in pins.items():ck('after pin '+name,ref(N/name)['sha256']==h)
save('input_refs.json',refs);audit=save('audit.json',{'actual_operations':'readonly byte hashing, AST parsing and static comparison only; no imported candidate module','checks':checks,'failed':[x for x in checks if not x['passed']],'product_calls':0,'source_mutations':0,'canonical_mutations':0})
review={'schema':'researchos.session-list-root-runner-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'READY_FOR_CANONICAL_ROOT_FINITE14_ONCE' if all(x['passed'] for x in checks) else 'REQUEST_CHANGES','requested_changes':[] if all(x['passed'] for x in checks) else [x for x in checks if not x['passed']],'runner_sha256':pins['root_finite14_replay.v2.py'],'scope_sha256':pins['root_finite14_scope.v2.json'],'launcher_sha256':pins['launch.v2.py'],'gate_sha256':pins['authorization_gate.v2.py'],'audit_ref':audit,'source_commit':scope['source_commit'],'source_paths_sha256':scope['source_paths_sha256'],'original_findings':{'R14-01':'Closed by exact sealed318 registration manifest/audit/intent/verified/done refs, independent source+runner+registration reviews, actual four canonical snapshots, pinned prelaunch Git/tool/runtime and exclusive immutable grant; inner consumes and freezes authorization paths. Draft alone cannot launch.','R14-02':'extend_vector checks prior rows, hashes only new paths and preserves conflict-checked original entries. WORK/archive/exe frozen before buildinfo, checked again after; initial and compile rows remain exact subsets.','R14-03':'Three exact Go sidecar observations plus proof flag consumed; independent lstat before SQLite open and in finally after close. Sidecar presence/error refuses; no deletion.'},'static_preservation':['Original14 selectors and16/224HTTP limits unchanged','Candidate parent and protected14633-byte body original guards unchanged','StrictUTF8 compiler metadata, fullWORK/archive/exe capture and three per-case stages retained','Only new fixture copies; no old failed DB/sidecar reuse','Exclusive ownedJob/fullcleanup, nullable exits, no retry, failure preservation retained','Only immutable318 canonical copies frozen; subsequent live canonical progress is outside product input vector'],'prerequisites_not_yet_executed':['Actual318 registration must satisfy gate exact JSON schema and refs','Root must precreate alias-free authorization parent; unique auth/output/export leaves absent','New compile/exe and14 actualcases remain NOT_RUN','Actual loaded runtime inventory and all input hashes must still pass launch/runtime guards'],'limitations':['Static review did not import or execute controller, gate, launcher, helper, SQLite or product','No current14 PASS, product/source/Main/formal acceptance','Same-user filesystem TOCTOU not excluded; scope explicitly retains this limitation','Implicit SQLite rowid is not separately exported; full declared columns and typed multisets remain required'],'actual_registration_executed':False,'actual_product_execution':False,'source_acceptance':False,'formal_increment':0,'failure_origins':[]}
r=save('review.json',review);entries=[ref(p) for p in sorted(O.iterdir()) if p.is_file()];m=save('manifest.json',{'entries':entries,'count':len(entries),'self_excluded':True});h=save('handoff.json',{'review_ref':r,'manifest_ref':m,'decision':review['decision'],'failure_origins':[],'execution_authorized_by_this_review':False});print(json.dumps({'output':str(O),'review':r,'manifest':m,'handoff':h,'checks':len(checks),'failed':len(audit.get('failed',[]))},ensure_ascii=False))
