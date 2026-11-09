import sys
sys.dont_write_bytecode = True
import ast, copy, hashlib, json, types
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os')
C=R/'execution/v2.4/receipts/W09/W09-99/w09_formal_profile_v2_source_codex/profv2-01a12b31'
N=Path(__file__).resolve().parent
PY=Path('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe')
pins={};checks=[];written=[]
def pin(p):
 p=Path(p).resolve(strict=True); b=p.read_bytes(); return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(p,ref=None):
 current=pin(p)
 if ref is not None: assert current=={'path':str(Path(ref['path']).resolve(strict=True)),'sha256':ref['sha256'],'bytes':ref['bytes']}
 assert current['path'] not in pins or pins[current['path']]==current
 pins[current['path']]=current
 return Path(p).read_bytes()
def fixed(p,digest,size):return {'path':str(p),'sha256':digest,'bytes':size}
def save(name,v):
 p=N/name
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
 return pin(p)
def ck(name,ok,detail=None):
 assert ok,name
 checks.append({'name':name,'status':'PASS','detail':detail})
def load_module(name,raw,path):
 m=types.ModuleType(name); m.__file__=str(path);sys.modules[name]=m
 exec(compile(raw,str(path),'exec'),m.__dict__)
 return m
def put(p,body):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(body)
 written.append(p)
 return p
def putj(p,obj):return put(p,(json.dumps(obj,ensure_ascii=False,sort_keys=True)+'\n').encode())
def localref(p,repo):
 v=pin(p);return {'path':p.relative_to(repo).as_posix(),'sha256':v['sha256']}
hr=fixed(C/'HDF.json','2acf88b5158088a6bcc2da809a47a6ade0378e997ecf4d9f8c31c5af35aa369a',2665)
mr=fixed(C/'MF.json','552dfb2e8a0f2f7a5710c120ffc09d153ebdc91497bf15de4292c449c8ba11ef',6058)
h=json.loads(read(hr['path'],hr));mf=json.loads(read(mr['path'],mr));assert h['manifest_ref']==mr
for ref in mf['members']:read(ref['path'],ref)
read(mf['review_findings_ref']['path'],mf['review_findings_ref'])
for rel in ('execution/v2.4/formal_profile_w07.py','ops/ci/retrieval.py','ops/ci/w09_formal_router.py','ops/ci/w09_evidence_closure.py'):
 read(R/rel)
producer_ast=ast.parse((R/'ops/ci/retrieval.py').read_bytes())
source_list=ast.literal_eval(next(x.value for x in producer_ast.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SOURCES' for t in x.targets)))
assert len(source_list)==21
for rel in source_list:read(R/rel)
read(PY);read(Path(__file__))
gp=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
gr=read(gp,fixed(gp,'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',11404))
gm=load_module('w09v2_review_real_guard',gr,gp);guard=gm.SourceReadGuard()
fake=N/'synthetic-repo';fake.mkdir()
try:
 guard.acquire(list(pins.values()))
 ck('locked_python_executable',Path(sys.executable).resolve()==PY.resolve(),str(sys.executable))
 ck('real_finite_source_guard_all_pins_exact',all(hashlib.sha256(guard.get_buffer(p)).hexdigest()==r['sha256'] for p,r in pins.items()),len(pins))
 before=guard.get_buffer(str(C/'formal_case_index.before.py'));after=guard.get_buffer(str(C/'formal_case_index.after.py'));profile=guard.get_buffer(str(C/'formal_profile_w09.after.py'))
 ck('W04_W07_first_51719_bytes_exact',before[:51719]==after[:51719] and hashlib.sha256(after[:51719]).hexdigest()==mf['w07_prefix']['sha256'])
 bt,at,pt=ast.parse(before),ast.parse(after),ast.parse(profile)
 old={x.name:x for x in bt.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))};new={x.name:x for x in at.body if isinstance(x,(ast.FunctionDef,ast.ClassDef))}
 changed={name for name in old if ast.dump(old[name])!=ast.dump(new[name])}
 ck('existing_changes_scoped',changed=={'_registered_roots','_verify_owner','recheck_inputs','derive_formal_cases'},sorted(changed))
 ck('old_final_CLI_guard_exact',ast.dump(bt.body[-1])==ast.dump(at.body[-1]) and isinstance(at.body[-1],ast.If))
 ck('complete_original_inverse_exact',hashlib.sha256(before).hexdigest()==mf['complete_byte_inverse']['sha256'] and len(before)==mf['complete_byte_inverse']['bytes'])
 ck('W04_Reader_and_W07_loader_AST_unchanged',all(ast.dump(old[k])==ast.dump(new[k]) for k in ('Reader','_w07_profile')))
 api=load_module('w09v2_independent_index',after,C/'formal_case_index.after.py');pro=load_module('w09v2_independent_profile',profile,C/'formal_profile_w09.after.py')
 closure=load_module('w09v2_trusted_closure',guard.get_buffer(str(R/'ops/ci/w09_evidence_closure.py')),R/'ops/ci/w09_evidence_closure.py')
 def rejected(label,fn,code):
  try:fn()
  except api.InvalidEvidence as exc:ck(label,exc.code==code,exc.code)
  else:raise AssertionError(label+' was accepted')
 pro._native_zero(api,{'exit_code':0},{'native_exit_code':0},'synthetic')
 ck('F1_integer_zero_accepts',True)
 for label,value in [('false',False),('true',True),('float',0.0),('null',None),('string','0'),('nonzero',1)]:
  rejected('F1_report_'+label,lambda v=value:pro._native_zero(api,{'exit_code':v},{'native_exit_code':0},'synthetic'),'NATIVE_EXIT_TYPE')
  rejected('F1_tool_'+label,lambda v=value:pro._native_zero(api,{'exit_code':0},{'native_exit_code':v},'synthetic'),'NATIVE_EXIT_TYPE')
 ck('F1_guard_called_from_native',any(isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='_native_zero' for x in ast.walk(next(x for x in pt.body if isinstance(x,ast.FunctionDef) and x.name=='_native'))))
 rr=api.Reader(R);prod=R/'ops/ci/retrieval.py';sources=pro._producer_sources(api,rr,{prod:api.sha256(prod)})
 vector={rr.path(rel):api.sha256(rr.path(rel)) for rel in sources};hashes={rel:'sha256:'+vector[rr.path(rel)] for rel in sources};report={'version_manifest':{'source_sha256':hashes}}
 pro._source21(api,rr,report,vector,sources,'synthetic');rr.finish()
 ck('F4_all_current_Source21_exact',sources==set(source_list) and len(sources)==21)
 for label,value in [('missing15',dict(list(hashes.items())[:6])),('foreign_extra',dict(hashes,extra='sha256:'+'0'*64))]:
  rejected('F4_'+label,lambda v=value:pro._source21(api,api.Reader(R),{'version_manifest':{'source_sha256':v}},vector,sources,'synthetic'),'NATIVE_SOURCE21_SET')
 drift=dict(hashes);drift[next(iter(drift))]='sha256:'+'0'*64
 rejected('F4_changed_vector',lambda:pro._source21(api,api.Reader(R),{'version_manifest':{'source_sha256':drift}},vector,sources,'synthetic'),'CURRENT_SOURCE_CLOSURE')
 # Real Windows CAS over an isolated synthetic repository, no Main writes.
 ownedrel='execution/receipts/W09/retrieval/run-synthetic/owned';owned=fake/ownedrel
 first=put(owned/'one.raw',b'one');claim=dict(localref(first,fake),bytes=3)
 reader=api.Reader(fake);inv=api._owned_inventory(reader,ownedrel,[claim]);snapshot={'files':{str(p):v for p,v in reader.read_hashes.items()},'inventories':[inv]}
 ck('F3_baseline_CAS_accepts',api.recheck_inputs(snapshot)['status']=='PASS')
 lower=put(owned/'extra.raw',b'extra');ck('F3_lowercase_added_rejected',api.recheck_inputs(snapshot)['status']=='INVALID');lower.unlink()
 upper=put(owned/'extra.RAW',b'extra');windows_set=[p.name for p in owned.rglob('*.raw')];uppercas=api.recheck_inputs(snapshot)
 ck('F3_uppercase_added_RAW_bypasses_CAS',uppercas['status']=='PASS' and 'extra.RAW' in windows_set,{'cas':uppercas,'closure_rglob_members':windows_set,'registered_members':[claim['path']]});upper.unlink()
 first.write_bytes(b'changed');ck('F3_changed_member_rejected',api.recheck_inputs(snapshot)['status']=='INVALID');first.write_bytes(b'one')
 first.unlink();ck('F3_deleted_member_rejected',api.recheck_inputs(snapshot)['status']=='INVALID');first.write_bytes(b'one')
 conflict=api.Reader(fake);conflict.read_hashes[first.resolve()]='0'*64
 rejected('F3_inventory_conflict_rejected',lambda:api._owned_inventory(conflict,ownedrel,[claim]),'INPUT_CHANGED_DURING_READ')
 rejected('F3_observed_conflict_rejected',lambda:pro._pin_observed(api,conflict,first.resolve(),claim['sha256']),'INPUT_CHANGED_DURING_READ')
 # F2: exact raw consumer accepts a future Go Time while report times predate review.
 rid='1'*32;runrel='execution/receipts/W09/retrieval/run-'+rid;run=fake/runrel;reportpath=putj(run/'report.json',{'synthetic_non_authoritative':True})
 selected=['TestW09Synthetic'];expected=['SYNTHETIC-01'];stdoutrel=runrel+'/go-test.stdout.jsonl';stderrrel=runrel+'/go-test.stderr.txt'
 assertion={'test_name':selected[0],'assertion_id':expected[0],'run_id':rid,'status':'PASS','evidence':{'synthetic':True}}
 rawtime='2026-10-20T00:00:00Z'
 events=[{'Time':rawtime,'Action':'run','Package':'synthetic','Test':selected[0]}, {'Time':rawtime,'Action':'output','Package':'synthetic','Test':selected[0],'Output':'W09_ASSERTION '+json.dumps(assertion)+'\n'}, {'Time':rawtime,'Action':'pass','Package':'synthetic','Test':selected[0]}]
 put(fake/stdoutrel,('\n'.join(json.dumps(v) for v in events)+'\n').encode());put(fake/stderrrel,b'')
 inert_go=put(fake/'inert-go-not-executable.bin',b'SYNTHETIC NEVER EXECUTED');go=pin(inert_go)
 lock=putj(fake/'execution/toolchains/locked.json',{'tools':{'go':{'path':str(inert_go),'sha256':go['sha256']}}})
 six={'internal/domain/retrieval_test.go','internal/domain/domain_test.go','internal/domain/w09_evidence_export_test.go','ops/ci/retrieval.py','ops/ci/w09_formal_router.py','ops/ci/w09_evidence_closure.py'}
 synthetic_source={}
 for rel in six:
  f=put(fake/rel,b'SYNTHETIC SOURCE NOT EXECUTED');synthetic_source[rel]='sha256:'+api.sha256(f)
 native={'run_id':rid,'raw_evidence_references':[stdoutrel,stderrrel],'assertion_results':[dict(assertion,raw_evidence_reference=stdoutrel)],'go_executable':go,'actual_invocation':[str(inert_go),'test','-count=1','-json','-run','^(?:TestW09Synthetic)$','./internal/domain'],'version_manifest':{'go_lock_sha256':'sha256:'+api.sha256(lock),'source_sha256':synthetic_source},'started_at':'2026-10-01T00:00:00Z','ended_at':'2026-10-01T00:10:00Z'}
 replay=closure.verify_native(fake,dict(native,report_reference=reportpath.relative_to(fake).as_posix()),native,expected,selected)
 outputs={route:{'native_started_at':native['started_at'],'native_ended_at':native['ended_at'],'started_at':'2026-10-01T01:00:00Z','ended_at':'2026-10-01T01:10:00Z'} for route in pro.ROUTES}
 globals_={case:{'ended_at':'2026-10-01T02:00:00Z'} for case in ('C19','A06')}
 cutoff=pro._review_execution_cutoff(api,outputs,globals_,'2026-10-02T00:00:00Z','2026-10-03T00:00:00Z')
 ck('F2_future_original_Go_Time_not_bound_to_review_cutoff',replay['run_id']==rid and api.stamp(rawtime,'raw')>cutoff,{'raw_Go_Time':rawtime,'native_report_end':native['ended_at'],'review_cutoff':cutoff.isoformat(),'scope':'isolated real native raw consumer + real cutoff; no full native/profile execution'})
 for field in ('native_ended_at','ended_at'):
  mutated=copy.deepcopy(outputs);mutated[next(iter(mutated))][field]='2026-10-20T00:00:00Z'
  rejected('F2_self_reported_future_'+field,lambda v=mutated:pro._review_execution_cutoff(api,v,globals_,'2026-10-02T00:00:00Z','2026-10-03T00:00:00Z'),'REVIEW_EXECUTION_CUTOFF')
 later=copy.deepcopy(globals_);later['A06']['ended_at']='2026-10-20T00:00:00Z'
 rejected('F2_self_reported_future_GLOBAL',lambda:pro._review_execution_cutoff(api,outputs,later,'2026-10-02T00:00:00Z','2026-10-03T00:00:00Z'),'REVIEW_EXECUTION_CUTOFF')
 # F5: all fixed paths + actual Reader pins, but entirely fabricated event origin.
 contextp=putj(fake/pro.PREFIX/'context.json',{'synthetic_non_authoritative':True});reviewp=putj(fake/pro.PREFIX/'review.json',{'synthetic_non_authoritative':True})
 contextref=localref(contextp,fake);reviewref=localref(reviewp,fake);eventid='invented-event-with-no-tool-channel'
 content='Synthetic author invented '+contextref['sha256']+' '+reviewref['sha256']
 origin={'schema':'researchos.original-collaboration-event.v1','source':'collaboration_tool_original','event_id':eventid,'sender':'codex:independent-name','recipient':'codex:/root','event_type':'MESSAGE','content':content,'received_at':'2026-10-04T00:00:00Z'}
 originp=putj(fake/pro.ROOT_ORIGIN_PREFIX/'invented.json',origin);originref=localref(originp,fake)
 capture={'schema':'researchos.root-observed-original-delivery.v1','root_actor':'codex:/root','event_id':eventid,'origin_ref':originref,'review_ref':reviewref,'context_ref':contextref,'content_sha256':hashlib.sha256(content.encode()).hexdigest(),'original_event_sha256':originref['sha256'],'root_observed_at':'2026-10-04T01:00:00Z'}
 capturep=putj(fake/pro.ROOT_CAPTURE_PREFIX/'invented.json',capture);captureref=localref(capturep,fake)
 registry={'schema':'researchos.root-delivery-capture-index.v1','writer_actor':'codex:/root','entries':[{'event_id':eventid,'capture_ref':captureref,'origin_ref':originref}]}
 registryp=putj(fake/pro.ROOT_CAPTURE_INDEX,registry)
 issuance={'event_id':eventid,'delivery_ref':captureref,'origin_event_ref':originref,'review_ref':reviewref,'context_ref':contextref}
 reader=api.Reader(fake);got=pro._root_original(api,reader,issuance,'codex:independent-name',{'context':contextp});reader.finish()
 ck('F5_invented_original_at_fixed_paths_accepted',got==(capture,origin),{'all_paths_checked_by_real_Reader':True,'real_original_tool_event_exists':False,'channel_or_thread_id_supplied':False,'event_id':eventid,'pinned_files':len(reader.read_hashes)})
 rejected('F5_author_receipt_path_rejected',lambda:pro._capture_registry(api,api.Reader(fake),{'delivery_ref':{'path':pro.PREFIX+'invented.json'}}),'ROOT_CAPTURE_REQUIRED')
 wrong=copy.deepcopy(issuance);wrong['event_id']='missing'
 rejected('F5_unregistered_event_rejected',lambda:pro._root_original(api,api.Reader(fake),wrong,'codex:independent-name',{'context':contextp}),'ROOT_CAPTURE_REQUIRED')
 originp.write_bytes(b'{}')
 rejected('F5_pinned_origin_tamper_rejected',lambda:pro._root_original(api,api.Reader(fake),issuance,'codex:independent-name',{'context':contextp}),'HASH_MISMATCH')
 save('synthetic-counterexamples.json',{'scope':'SYNTHETIC_NONAUTHORITATIVE_NO_FORMAL_AUTHORITY','F2':{'events':events,'report_times':{k:native[k] for k in ('started_at','ended_at')},'review_issued_at':'2026-10-03T00:00:00Z'},'F3':{'closure_rglob_members':windows_set,'snapshot':snapshot,'after_uppercase_CAS':uppercas},'F5':{'registry':registry,'capture':capture,'invented_origin':origin,'issuance':issuance,'claim':'None of these objects represents an actually received collaboration event.'}})
finally:
 observation=guard.close();save('sourceguard.final.json',observation)
 # Remove only known transient synthetic files within this new review namespace.
 for p in reversed(written):
  assert p.resolve(strict=False).is_relative_to(fake.resolve())
  if p.exists():p.unlink()
 for p in sorted([p for p in fake.rglob('*') if p.is_dir()],key=lambda p:len(p.parts),reverse=True):
  assert p.resolve().is_relative_to(fake.resolve());p.rmdir()
 fake.rmdir()
ck('real_sourceguard_closed0',observation['verification']=='PASSED' and observation['closed'] is True and observation['retained_handles_count']==0 and not observation['errors'])
save('input-pins.json',list(pins.values()))
save('controls.json',{'scope':'SYNTHETIC_NONAUTHORITATIVE_SOURCE_ONLY','status':'PASS_REVIEW_CONTROLS','checks':checks,'source_findings_remaining':['F2','F3','F5'],'source_fixes_closed':['F1','F4'],'actual_runs':0,'canonical_writes':0,'formal_cases_created':0})
print(json.dumps({'status':'PASS_REVIEW_CONTROLS','checks':len(checks),'guarded_inputs':len(pins),'retained_handles_count':0,'remaining_findings':['F2','F3','F5']},ensure_ascii=False))
