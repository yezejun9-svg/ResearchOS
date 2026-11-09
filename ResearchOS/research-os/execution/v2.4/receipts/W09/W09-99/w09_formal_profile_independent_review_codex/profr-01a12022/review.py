import sys
sys.dont_write_bytecode=True
import ast, copy, hashlib, json, types
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
C=R/'execution/v2.4/receipts/W09/W09-99/w09_formal_profile_source_codex/prof-20261009a'
N=Path(__file__).resolve().parent
pins={}; checks=[]
def pin(p):
 p=Path(p).resolve(strict=True); b=p.read_bytes(); return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(p,expected=None):
 r=pin(p)
 if expected: assert r['sha256']==expected['sha256'] and r['bytes']==expected['bytes']
 pins[r['path']]=r; return Path(p).read_bytes()
def write(name,value):
 p=N/name
 with p.open('x',encoding='utf-8',newline='\n') as f: f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
 return p
def ck(name,condition,details=None):
 assert condition,name
 checks.append(dict(name=name,status='PASS',details=details))
def module(name,raw,path):
 m=types.ModuleType(name);m.__file__=str(path);sys.modules[name]=m;exec(compile(raw,str(path),'exec'),m.__dict__);return m
h=json.loads(read(C/'HDF.json',dict(sha256='3af6ed1177c45031d2f4d163924cc8db5e1e0628fb0b681a2315c2067e70031d',bytes=3012)))
mf=json.loads(read(C/'MF.json',dict(sha256='3390eb7e10ca78f8aaff2355df6521275fdd75f187b1c27cde4ec5e8bffb4dda',bytes=5821)))
for ref in mf['artifacts']: read(ref['path'],ref)
read(R/'execution/v2.4/formal_case_index.py',mf['target_before']['execution/v2.4/formal_case_index.py'])
for rel in ('execution/v2.4/formal_profile_w07.py','ops/ci/retrieval.py','ops/ci/w09_formal_router.py','ops/ci/w09_evidence_closure.py'):
 read(R/rel)
gp=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
gr=read(gp,dict(sha256='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',bytes=11404))
guardmodule=module('w09_independent_real_guard',gr,gp)
guard=guardmodule.SourceReadGuard()
try:
 guard.acquire(list(pins.values()))
 ck('finite_source_pins_held',all(hashlib.sha256(guard.get_buffer(p)).hexdigest()==v['sha256'] for p,v in pins.items()))
 before=(C/'formal_case_index.before.py').read_bytes();after=(C/'formal_case_index.after.py').read_bytes();profile=(C/'formal_profile_w09.after.py').read_bytes()
 ck('w07_compat_first_51719_bytes_exact',before[:51719]==after[:51719] and hashlib.sha256(after[:51719]).hexdigest()==mf['w07_compat_prefix']['sha256'])
 bt,at,pt=ast.parse(before),ast.parse(after),ast.parse(profile)
 bf={x.name:x for x in bt.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))};af={x.name:x for x in at.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
 changed=[name for name in bf if ast.dump(bf[name])!=ast.dump(af[name])]
 ck('existing_function_changes_scoped',set(changed)=={'_registered_roots','_verify_owner','derive_formal_cases'},changed)
 ck('original_final_cli_guard_retained',ast.dump(bt.body[-1])==ast.dump(at.body[-1]) and isinstance(at.body[-1],ast.If))
 ck('fixed_loader_no_receipt_path', 'execution/v2.4/formal_profile_w09.py' in ast.get_source_segment(after.decode(),af['_w09_profile']))
 ck('candidate_not_adopted',not (R/'execution/v2.4/formal_profile_w09.py').exists())
 api=module('w09_review_index_nonmain',after,C/'formal_case_index.after.py');pro=module('w09_review_profile_nonmain',profile,C/'formal_profile_w09.after.py')
 ck('six_frozen_routes_exact',pro.ROUTES==(('test.retrieval','W09-G01',''),('test.retrieval','W09-G02',''),('test.research.fixture','','C19'),('test.retrieval','','C19'),('test.retrieval','','A06'),('test.security','','A06')))
 # Extract and evaluate the exact production comparison; no native producer runs.
 native=next(x for x in pt.body if isinstance(x,ast.FunctionDef) and x.name=='_native')
 cmp=next(x for x in ast.walk(native) if isinstance(x,ast.Compare) and 'native_exit_code' in ast.unparse(x))
 ex=compile(ast.Expression(cmp),'<source-native-exit-condition>','eval')
 accepted={}
 for label,value in [('int_zero',0),('bool_false',False),('float_zero',0.0),('unknown_null',None),('nonzero',1)]:
  accepted[label]=eval(ex,{},dict(tool={'native_exit_code':value},report={'exit_code':value}))
 ck('F1_native_false_and_float_accepted',accepted=={'int_zero':True,'bool_false':True,'float_zero':True,'unknown_null':False,'nonzero':False},accepted)
 # Real index Reader and recheck_inputs over this review's disposable owned files.
 sandbox=N/'synthetic_owned';sandbox.mkdir();one=sandbox/'one.raw';one.write_text('{"value":1}',encoding='utf-8')
 reader=api.Reader(R);reader.read(one);snap={'files':{str(p):v for p,v in reader.read_hashes.items()},'inventories':[]}
 two=sandbox/'unregistered.raw';two.write_text('{"value":2}',encoding='utf-8')
 reader.finish();cas=api.recheck_inputs(snap)
 ck('F3_new_owned_raw_not_detected_by_file_CAS',cas=={'status':'PASS'} and len(list(sandbox.glob('*.raw')))==2,cas)
 two.unlink();one.unlink();sandbox.rmdir()
 # Validate actual Reader path rejection without invoking a product or CLI.
 rejects={}
 for value in ('../escape','C:/absolute','execution\\receipts\\W09\\x','execution/v2.4/receipts/W05/x'):
  try: reader.path(value,pro.NATIVE_PREFIX)
  except api.InvalidEvidence as e: rejects[value]=e.code
 ck('path_scope_and_windows_negative_controls',len(rejects)==4,rejects)
 # The trusted native closure only requires six source hashes, even though the producer has Source21.
 closure_raw=(R/'ops/ci/w09_evidence_closure.py').read_text(encoding='utf-8');ct=ast.parse(closure_raw)
 vn=next(x for x in ct.body if isinstance(x,ast.FunctionDef) and x.name=='verify_native')
 req=next(x for x in ast.walk(vn) if isinstance(x,ast.Call) and any(isinstance(a,ast.Constant) and a.value=='CURRENT_SOURCE_CLOSURE_MISMATCH' for a in x.args))
 minset=next(x for x in ast.walk(req.args[0]) if isinstance(x,ast.Set))
 six=ast.literal_eval(minset);hashes={p:'sha256:'+hashlib.sha256((R/p).read_bytes()).hexdigest() for p in six}
 sourcecheck=eval(compile(ast.Expression(req.args[0]),'<native-source-check>','eval'),{'source_hashes':hashes,'root':R,'digest':lambda b:hashlib.sha256(b).hexdigest()})
 rt=ast.parse((R/'ops/ci/retrieval.py').read_text(encoding='utf-8'));source_assignment=next(x for x in rt.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SOURCES' for t in x.targets));source21=ast.literal_eval(source_assignment.value)
 ck('F4_native_source6_admitted_without_source21',sourcecheck and len(source21)==21 and len(six)==6,{'producer_count':len(source21),'accepted_native_minimum':sorted(six),'omitted':sorted(set(source21)-six)})
 # _independent is called unchanged; its reader is a synthetic in-memory adapter.
 # These bytes and hashes are NONAUTHORITATIVE and never enter canonical state.
 evidence=N/'synthetic_independent';evidence.mkdir()
 raw=evidence/'raw.json';raw.write_text('{"actual":"observation","assertion_results":[{"status":"PASS"}]}',encoding='utf-8')
 context_file=evidence/'context.json';context_file.write_text('{}',encoding='utf-8')
 review_path=evidence/'review.json';issuance_path=evidence/'issuance.json';message_path=evidence/'message.json'
 def ref(path):return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else 'a'*64}
 context={'executor_id':'codex:author','run_id':'synthetic-nonauthoritative','created_at':'2026-10-01T00:00:00Z','acceptance_baseline_ref':{},'version_vector':{},'registered_commands':[],'global_evidence_refs':{}}
 roots={'context':context_file,'review':review_path,'issuance':issuance_path};cr=ref(context_file);rr=ref(review_path)
 outputs={('test.retrieval',g,''):{'mode':m,'run_id':'test','report':ref(raw),'started_at':'2026-10-20T00:00:00Z','ended_at':'2026-10-20T01:00:00Z'} for g,m in [('W09-G01','FIXTURE'),('W09-G02','LIVE_WINDOWS')]}
 rows={cid:{'actual':'observed','expected':'expected'} for cid in (*pro.IDS['C19'],*pro.IDS['A06'])}
 verdicts=[dict(id=cid,status='PASS',actual='observed',expected='expected',raw_evidence_refs=[dict(ref(raw),locator={'json_pointer':'/actual'})]) for cid in rows]
 for route,value in outputs.items():verdicts.append(dict(id=route[1],status='PASS',actual='observed',mode=value['mode'],run_id='test',raw_evidence_refs=[dict(ref(raw),locator={'json_pointer':'/assertion_results'})]))
 review=dict(schema=pro.SCHEMAS['review'],executor_id=context['executor_id'],reviewer_id='codex:reviewer',task_id='W09',step_id='W09-99',run_id=context['run_id'],context_ref=cr,acceptance_baseline_ref={},version_vector={},registered_commands=[],global_evidence_refs={},decision='ACCEPTED',missing=[],failed=[],verdicts=verdicts,issued_at='2026-10-02T00:00:00Z')
 issuance=dict(schema=pro.SCHEMAS['issuance'],actor='codex:/root',executor_id=context['executor_id'],reviewer_id='codex:reviewer',task_id='W09',step_id='W09-99',run_id=context['run_id'],context_ref=cr,review_ref=rr,delivery_ref=ref(message_path),observed_at='2026-10-04T00:00:00Z')
 message=dict(schema='researchos.root-received-independent-message.v1',recorded_by='codex:/root',recipient='codex:/root',sender='codex:reviewer',event_type='MESSAGE',review_ref=rr,content=rr['sha256']+' '+api.sha256(context_file),received_at='2026-10-03T00:00:00Z')
 docs={context_file:context,review_path:review,issuance_path:issuance,message_path:message}
 class FakeReader:
  def read(self,path):return docs[path]
  def ref(self,value,*args,**kwargs):return Path(value['path'])
 fake=FakeReader();owner={'accepted_at':'2026-10-05T00:00:00Z'}
 pro._independent(api,fake,owner,roots,context,outputs,rows)
 ck('F2_review_before_execution_accepted',True,{'review_issued':review['issued_at'],'owner_accepted':owner['accepted_at'],'dispatch_ended':next(iter(outputs.values()))['ended_at'],'adapter':'FakeReader isolates independent logic; no actual authority'})
 ck('F5_self_authored_delivery_without_origin_accepted',not any(k in message for k in ('origin_ref','message_id','thread_id','channel_id')),list(message))
 review['reviewer_id']=context['executor_id']
 try:pro._independent(api,fake,owner,roots,context,outputs,rows)
 except api.InvalidEvidence as exc:ck('independent_same_actor_rejected',exc.code=='INDEPENDENT_ACTOR',exc.code)
 else:raise AssertionError('same actor was accepted')
 review['reviewer_id']='codex:reviewer';context['created_at']='2026-10-09T00:00:00Z'
 try:pro._independent(api,fake,owner,roots,context,outputs,rows)
 except api.InvalidEvidence as exc:ck('reversed_self_declared_time_rejected',exc.code=='REGISTERED_TIME_ORDER',exc.code)
 else:raise AssertionError('reversed self-declared time was accepted')
 raw.unlink();context_file.unlink();evidence.rmdir()
 ck('source21_dependencies_not_fully_bound_at_native_layer',bool(set(source21)-six))
finally:
 observation=guard.close();write('sourceguard.final.json',observation)
ck('real_sourceguard_closed0',observation['verification']=='PASSED' and observation['closed'] is True and observation['retained_handles_count']==0 and not observation['errors'])
write('input-pins.json',list(pins.values()))
write('controls.json',{'schema':'researchos.w09.independent-source-controls.v1','scope':'SYNTHETIC_NONAUTHORITATIVE_SOURCE_ONLY','actual_native_runs':0,'actual_index_main_runs':0,'canonical_writes':0,'formal_cases_created':0,'checks':checks})
print(json.dumps({'status':'PASS','scope':'SOURCE_REVIEW_CONTROLS_NONAUTHORITATIVE','checks':len(checks),'guarded_files':len(pins),'retained_handles_count':0,'findings':5}))
