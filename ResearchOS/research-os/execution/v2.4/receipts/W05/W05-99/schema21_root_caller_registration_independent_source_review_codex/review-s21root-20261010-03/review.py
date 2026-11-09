"""Independent exact Source03 delta review; no caller entry or Root authority."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import ast,copy,hashlib,json,os,types
N=Path(__file__).resolve().parent
B=N.parent.parent
S=B/'schema21_root_caller_registration_source_codex/s21root-20261010-03'
ACTOR='codex:/root/attach_fixture_source_review';THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
checks=[]
def pin(p):
 p=Path(p);v=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(v).hexdigest(),bytes=len(v))
def read(r):return json.loads(Path(r['path'] if isinstance(r,dict) else r).read_bytes())
def same(a,b):return os.path.normcase(os.path.abspath(a['path']))==os.path.normcase(os.path.abspath(b['path'])) and a['sha256']==b['sha256'] and a['bytes']==b['bytes']
def save(n,x):
 p=N/n
 with p.open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
def check(n,x):checks.append(dict(name=n,passed=bool(x)))
def need(x,n):
 if not x:raise ValueError(n)
hr=pin(S/'HDF.json');assert (hr['sha256'],hr['bytes'])==('37d0152dd58020f7c1be76d1a66b6fa2363de8782668998ad89080c84257a45b',12041)
h=read(hr);mr=h['manifest_ref'];m=read(mr);contract=read(h['contract_ref']);builder=read(contract['builder_contract_ref']);oldh=read(h['base_Source_hdf_ref'])
obs=read(h['actual_Task76_observation_ref']);raw=Path(h['actual_Task76_raw_ref']['path']).read_bytes();rows=[json.loads(x) for x in raw.splitlines()]
envelope='Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/full_w09_source_review\nPayload:\n'
text=rows[2]['payload']['content'][0]['text'];assert text.startswith(envelope)
delivered=json.loads(text[len(envelope):]);priorrefs=delivered['review_refs'];priorh,priorm,priord=[read(r) for r in priorrefs]
inputs=[hr,mr,h['caller_ref'],h['contract_ref'],h['base_Source_hdf_ref'],h['base_Source_mf_ref'],h['base_Caller_ref'],h['actual_Task76_observation_ref'],h['actual_Task76_raw_ref'],h['legacy_Task68_raw_ref'],h['inverse_ref'],h['prior_complete_inverse_ref'],oldh['contract_ref'],contract['builder_contract_ref'],builder['source_guard_ref'],pin(__file__)]+m['members']+priorrefs
unique={}
for r in inputs:
 k=os.path.normcase(os.path.abspath(r['path']));assert k not in unique or same(unique[k],r);unique[k]=r
g=types.ModuleType('delta_guard');exec(compile(Path(builder['source_guard_ref']['path']).read_bytes(),builder['source_guard_ref']['path'],'exec'),g.__dict__)
guard=g.SourceReadGuard(per_file_cap=32*1024*1024,total_cap=64*1024*1024);error=None
try:
 guard.acquire(list(unique.values()))
 for r in unique.values():check('input exact '+Path(r['path']).name,same(pin(r['path']),r))
 before=Path(h['base_Caller_ref']['path']).read_bytes();after=Path(h['caller_ref']['path']).read_bytes()
 old=b'and first.get("timestamp") == last.get("timestamp") and payload.get("type") == "agent_message"'
 new=b'and when(first.get("timestamp")) <= when(last.get("timestamp")) and (when(last.get("timestamp")) - when(first.get("timestamp"))).total_seconds() <= 1 and payload.get("type") == "agent_message"'
 check('independent full byte inverse restores Source02 exactly',after.count(new)==before.count(old)==1 and after.replace(new,old)==before)
 ta,tb=ast.parse(after),ast.parse(before)
 fa={n.name:n for n in ta.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};fb={n.name:n for n in tb.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 check('complete function and class inventory unchanged',set(fa)==set(fb))
 changed=[k for k in fa if ast.dump(fa[k],include_attributes=False)!=ast.dump(fb[k],include_attributes=False)]
 check('only validate_peer_delivery AST changed',changed==['validate_peer_delivery'])
 for k in ('failure_rows','projection','original_capture_rows','own_review','runtime_review_chain','runtime_closure'):
  check('inherited exact function unchanged '+k,ast.dump(fa[k],include_attributes=False)==ast.dump(fb[k],include_attributes=False))
 check('all nonfunction top-level AST unchanged',ast.dump(ast.Module(body=[n for n in ta.body if not isinstance(n,(ast.FunctionDef,ast.ClassDef))],type_ignores=[]))==ast.dump(ast.Module(body=[n for n in tb.body if not isinstance(n,(ast.FunctionDef,ast.ClassDef))],type_ignores=[])))
 inverse=read(h['inverse_ref']);check('author inverse agrees with independently computed inverse',inverse['old_hex']==old.hex() and inverse['new_hex']==new.hex() and inverse['candidate_byte_offset']==after.index(new) and inverse['restored_Source_SHA']==hashlib.sha256(before).hexdigest())
 # Bind the accepted Source02 review to the actual original backend delivery.
 parts=[]
 with Path(obs['source_audit_path']).open('rb') as f:
  for offset,size,digest in zip(obs['source_line_offsets'],obs['source_line_bytes'],obs['original_line_sha256']):
   f.seek(offset);v=f.read(size);check('actual Task76 original audit byte range',hashlib.sha256(v).hexdigest()==digest);parts.append(v)
 check('complete original Task76 bytes and source identity',b''.join(parts)==raw and rows[0]['payload']['id']==THREAD and same(obs['original_capture_ref'],h['actual_Task76_raw_ref']))
 check('actual Task76 adjacent backend 1ms',rows[1]['ordinal']==62777 and rows[2]['ordinal']==62778 and rows[1]['timestamp']=='2026-10-09T18:48:49.566Z' and rows[2]['timestamp']=='2026-10-09T18:48:49.567Z')
 check('actual Task76 Source02 accepted independent review',delivered['review_author']=='codex:/root/full_w09_source_review' and delivered['root_thread_id']==THREAD and delivered['operation']=='SOURCE_REVIEW_WITNESS' and delivered['formal_acceptance'] is False and delivered['execution_grant'] is False and priord['verdict']=='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION' and priord['independent_non_author'] is True and same(priord['source_hdf_ref'],h['base_Source_hdf_ref']) and same(priord['source_mf_ref'],h['base_Source_mf_ref']) and same(priord['caller_ref'],h['base_Caller_ref']))
 check('Source observation creates no Root witness',obs['issued_by_Root'] is False and obs['Root_witness'] is False and obs['Root_authorization'] is False and obs['formal_acceptance'] is False and obs['execution_grant'] is False)
 # Evaluate only the changed pure predicate and unchanged actor gate, extracted from real Source.
 def gate(fn):
  return [n.value.args[0] for n in fn.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='need'][:2]
 newgates=gate(fa['validate_peer_delivery']);oldgates=gate(fb['validate_peer_delivery'])
 import re
 env=dict(datetime=datetime,need=need,re=re,ROOT='codex:/root',CALLER_AUTHOR='codex:/root/backup_regression_resources',BUILDER_AUTHOR='codex:/root/native_temp_independent_review')
 exec(compile(ast.fix_missing_locations(ast.Module(body=[fa['when']],type_ignores=[])),str(h['caller_ref']['path'])+'#pure-time','exec'),env)
 expressions=[compile(ast.fix_missing_locations(ast.Expression(body=copy.deepcopy(n))),'<Source03-delta-predicate>','eval') for n in newgates]
 oldexpr=compile(ast.fix_missing_locations(ast.Expression(body=copy.deepcopy(oldgates[1]))),'<Source02-old-predicate>','eval')
 def accepts(first,last,actor='codex:/root/full_w09_source_review'):
  local=dict(first=first,last=last,payload=last['payload'],peer_actor=actor)
  try:return all(eval(expr,env,local) for expr in expressions)
  except (ValueError,TypeError,KeyError):return False
 first,last=rows[1],rows[2]
 check('actual original 1ms delivery accepted by Source03 predicate',accepts(first,last))
 check('actual original 1ms delivery rejected by exact Source02 predicate',eval(oldexpr,env,dict(first=first,last=last,payload=last['payload'],peer_actor='codex:/root/full_w09_source_review')) is False)
 for delta,expected in [(-0.000001,False),(0,True),(1,True),(1.000001,False)]:
  mutated=copy.deepcopy(last);mutated['timestamp']=(env['when'](first['timestamp'])+timedelta(seconds=delta)).isoformat()
  check('independent time boundary '+str(delta),accepts(first,mutated)==expected)
 changed_last=copy.deepcopy(last);changed_last['ordinal']+=1
 check('same valid time but nonadjacent backend rejected',not accepts(first,changed_last))
 changed_last=copy.deepcopy(last);changed_last['payload']['author']='/root/other_peer'
 check('same valid time but different actual actor rejected',not accepts(first,changed_last))
 changed_last=copy.deepcopy(last);changed_last['metadata']['client_authored']=True
 check('same valid time but client authored rejected',not accepts(first,changed_last))
 changed_last=copy.deepcopy(last);changed_last['metadata']['client_authored']=0
 check('integer zero cannot impersonate false client flag',not accepts(first,changed_last))
 changed_first=copy.deepcopy(first);changed_first['payload']['trigger_turn']=0
 check('integer trigger flag rejected',not accepts(changed_first,last))
 check('Source author cannot be independent actor',not accepts(first,last,'codex:/root/backup_regression_resources'))
 # The complete remainder, including narrow legacy bytes, is identical to Source02.
 newfn=copy.deepcopy(fa['validate_peer_delivery']);oldfn=fb['validate_peer_delivery']
 newneed=next(n for n in newfn.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and len(n.value.args)>1 and isinstance(n.value.args[1],ast.Constant) and n.value.args[1].value=='ACTUAL_PEER_DELIVERY_REQUIRED')
 oldneed=next(n for n in oldfn.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and len(n.value.args)>1 and isinstance(n.value.args[1],ast.Constant) and n.value.args[1].value=='ACTUAL_PEER_DELIVERY_REQUIRED')
 newneed.value.args[0]=copy.deepcopy(oldneed.value.args[0])
 check('entire peer function exact after replacing sole predicate',ast.dump(newfn,include_attributes=False)==ast.dump(oldfn,include_attributes=False))
 legacyraw=Path(h['legacy_Task68_raw_ref']['path']).read_bytes()
 constants={n.value for n in ast.walk(fa['validate_peer_delivery']) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
 check('legacy Task68 actual byte SHA and message binding remain exact',len(legacyraw)==27173 and hashlib.sha256(legacyraw).hexdigest()=='797f80403540a5f9da512f47d8698498c40bf36869fb5b4b4f64600e8d57e083' and {'amsg_01a121d5-f9cd-7c73-a691-bd9060ad2d77','2026-10-09T18:03:53.678Z','797f80403540a5f9da512f47d8698498c40bf36869fb5b4b4f64600e8d57e083','EXACT_LEGACY_OLD21_BUILDER_DELIVERY'}<=constants)
 for field in ('actual_RootScope_ref','actual_current4','actual_runtime_manifest_ref','actual_runtime_qualification_ref','actual_build_hostpair_ref','actual_programme_qualification_ref'):check('Source keeps missing authority null '+field,h[field] is None)
 check('old unknown failed guards preserved as unknown',h['old_failed_guard_status']==oldh['old_failed_guard_status']=='UNKNOWN_NOT_SERIALIZED')
 for r in unique.values():check('final exact '+Path(r['path']).name,same(pin(r['path']),r))
except BaseException as e:error=dict(type=type(e).__name__,message=str(e))
finally:closed=guard.close()
check('single independent guard closed0',closed['verification']=='PASSED' and closed['closed'] is True and closed['retained_handles_count']==0 and closed['errors']==[])
gr=save('Source-guard.closed.json',closed);failed=[x for x in checks if not x['passed']]
report=save('independent-delta-checks.json',dict(checks=checks,failed=failed,error=error,passed=len(checks)-len(failed),actual_Task76_observation_ref=h['actual_Task76_observation_ref'],actual_Task76_raw_ref=h['actual_Task76_raw_ref'],inherited_Source02_review_refs=priorrefs,full_byte_inverse=True if not failed and not error else None,only_pure_predicate_executed=True,author_control_programs_rerun=False,old853_39_59_428_rerun=False,programme_qualification=None,Root_witness_created=False,actual_Go_Native_SQL_TP_model_calls=0,live_Canon_handles=0,Source_guard_ref=gr))
if error:
 print(json.dumps(dict(error=error,report_ref=report,guard_ref=gr),ensure_ascii=False),flush=True);raise SystemExit(1)
common=dict(review_author=ACTOR,source_author=h['source_author'],source_hdf_ref=hr,source_mf_ref=mr,formal_acceptance=False,execution_grant=False)
decision=save('decision.json',dict(schema='researchos.old21-caller-independent-source-review-decision.v1',**common,independent_non_author=True,verdict='SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION' if not failed else 'CHANGES_REQUIRED',caller_ref=h['caller_ref'],registrar_ref=h['registrar_ref'],calling_contract_ref=h['contract_ref'],independent_delta_checks_ref=report,Source_guard_ref=gr,Root_external_witness_required=True,runtime_qualification=None,programme_qualification=None,old_failed_guard_status=h['old_failed_guard_status']))
mf=save('MF.json',dict(schema='researchos.old21-caller-independent-source-review-manifest.v1',members=list(unique.values())+[gr,report,decision]))
hdf=save('HDF.json',dict(schema='researchos.old21-caller-independent-source-review-hdf.v1',**common,manifest_ref=mf,source_decision_ref=decision,reviewed_utc=datetime.now(timezone.utc).isoformat(),independent_delta_checks_ref=report,Source_guard_ref=gr,Root_external_witness_required=True,runtime_qualification=None,programme_qualification=None))
print(json.dumps(dict(HDF=hdf,MF=mf,decision=decision,checks=len(checks),failed=failed,held_refs=len(unique),verdict=read(decision)['verdict'],formal_acceptance=False,execution_grant=False),ensure_ascii=False),flush=True)
if failed:raise SystemExit(1)
