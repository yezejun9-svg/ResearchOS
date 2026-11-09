import ast,json,hashlib,os
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W05/W05-99';O=Path(__file__).parent
N=P/'integration_codex/cli43-fresh-held2-r325-71b091d20d94443bbf4e732d201eeb29';reads={};checks=[]
def ck(v,n):checks.append({'check':n,'pass':bool(v)})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def read(p):
 p=path(p);raw=p.read_bytes();reads[str(p)]=raw;return raw
def ref(p):
 p=path(p);raw=read(p);return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def doc(p):return json.loads(read(p))
def vr(r):
 raw=read(r['path']);ck(hashlib.sha256(raw).hexdigest()==r['sha256'] and len(raw)==r['bytes'],'pin '+r['path']);return raw
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
oldreview=doc(P/'cli43_root_caller_static_independent_review_codex/cb051900a68144bbba222cd24154e436/review.json');old=vr(oldreview['caller_ref']).decode();new=read(N/'root-launch-once.v2.py').decode();ot=ast.parse(old);nt=ast.parse(new)
def prefix(t):
 nodes=[]
 for x in t.body:
  if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id=='result' for y in x.targets):break
  if isinstance(x,ast.Expr) and isinstance(x.value,ast.Constant) and isinstance(x.value.value,str):continue
  if isinstance(x,ast.Import) and [y.name for y in x.names]==['traceback']:continue
  nodes.append(ast.dump(x))
 return nodes
ck(prefix(ot)==prefix(nt),'prelaunch pin/argv/environment/intent prefix unchanged except docstring/import')
calls=[x for x in ast.walk(nt) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and isinstance(x.func.value,ast.Name) and x.func.value.id=='subprocess' and x.func.attr=='run'];oldcalls=[x for x in ast.walk(ot) if isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and isinstance(x.func.value,ast.Name) and x.func.value.id=='subprocess' and x.func.attr=='run']
ck(len(calls)==1 and ast.dump(calls[0])==ast.dump(oldcalls[0]),'exact one unchanged subprocess invocation and3900 timeout')
tr=next(x for x in nt.body if isinstance(x,ast.Try));oldtr=next(x for x in ot.body if isinstance(x,ast.Try))
ck([ast.dump(x) for x in tr.body]==[ast.dump(x) for x in oldtr.body],'raw xb and child call identical')
ck(not any(isinstance(x,ast.Raise) for x in ast.walk(tr.handlers[0])),'primary exception retained without immediate rethrow')
for needle in ["error = {'error': repr(exc), 'traceback': traceback.format_exc()}","pin(raw_path) if raw_path.is_file() else None","raw_refs[name + '_ref'] = None","'stage': name + '-raw-reference'","'stage': 'invocation-receipt'","'first_cause': error","result.returncode if result else None","result.returncode if result is not None and error is None and not secondary else 1","'caller_OS_lifecycle_qualification': False"]:ck(needle in new,'failure evidence guard '+needle)
ck(len(tr.finalbody)>0 and sum(isinstance(x,ast.Try) for x in ast.walk(tr))>=3,'per-raw and invocation independent guarded finalization')
scope=doc(N/'scope_registration.json');grpath=Path(scope['new_authorization_root'])/'authorization.execute.json';ck(ref(grpath)['sha256']=='4358b6b1c494e33104aff066e4e07f12cec0b3029a95ed56f1be940500df9f7a','same actual sealed grant');ck(ref(N/'scope_registration.json')['sha256']=='c942ced8bc4e34668e74997a1950150816ee819298e54a448b588e0e3ea2eb20','same exact reviewed scope')
vr(scope['launcher_ref']);vr(scope['python_ref']);vr(oldreview['grant_completed_ref']);vr(oldreview['grant_manifest_ref'])
for k in ['new_output_root','new_wrapper_root','new_export_root']:ck(not os.path.lexists(scope[k]),'execution leaf remains absent '+k)
for name in ['root-launch.intent.json','root-launch.stdout.raw','root-launch.stderr.raw','root-launch.invocation.json']:ck(not(N/name).exists(),'caller output absent '+name)
for p,raw in reads.items():ck(Path(p).read_bytes()==raw,'after stable '+p)
failed=[x for x in checks if not x['pass']]
save('audit.json',{'checks':checks,'failed_checks':failed,'input_refs':[{'path':p,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)} for p,raw in reads.items()],'target_execution':False,'new_failure_origins':[]})
review={'schema':'researchos.cli43-root-caller-static-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'READY_FOR_ROOT_ONCE_ONLY_PINNED_LAUNCHER_CALL' if not failed else 'REQUEST_CHANGES','requested_changes':failed,'caller_ref':ref(N/'root-launch-once.v2.py'),'scope_ref':ref(N/'scope_registration.json'),'grant_ref':ref(grpath),'prior_request_review_ref':ref(P/'cli43_root_caller_static_independent_review_codex/cb051900a68144bbba222cd24154e436/review.json'),'audit_ref':ref(O/'audit.json'),'finding_closed':'CLI43-CALLER-01','branch_findings':['Before subprocess launch, raw creation errors preserve first error and actual_launcher_native_exit=NULL; missing raw ref stays NULL.','Individual raw hash errors and invocation persistence errors are secondary, with stderr fallback preserving first cause.','Timeout preserves NULL child exit; nonzero completed child returns its actual code; success requires actual child0 and no caller/secondary error.','Prelaunch pins and exclusive intent remain outside raw/subprocess try; their failure produces ordinary caller nonzero/stderr before any launch, not an invented child invocation.'],'limits':'Same one subprocess, pinned Python -I -S -X utf8, exact launcher/scope/grant, public environment, caller3900 vs launcher3600/cleanup5 and inner3300. Caller makes no owned Job or OS lifecycle qualification. Reuses prior grant closure; no resource-tree rehash or target execution.','actual_caller_execution':False,'actual_product_execution':False,'new_failure_origins':[],'source_acceptance':False,'formal_increment':0,'status':'STOPPED'}
save('review.json',review);save('handoff.json',{'review_ref':ref(O/'review.json'),'caller_ref':review['caller_ref'],'decision':review['decision'],'actual_target_execution':False,'new_failure_origins':[],'status':'STOPPED'})
entries=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.json'];save('manifest.json',{'entries':entries,'count':len(entries),'excluded_only_self':True})
print(json.dumps({'refs':{n:ref(O/n) for n in ['review.json','manifest.json','handoff.json']},'checks':len(checks),'failed_checks':failed},ensure_ascii=False))
