import ast,copy,difflib,hashlib,json,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
R=Path('D:/作品集/ResearchOS/research-os')
C=R/'execution/v2.4/receipts/W09/W09-99/w09_formal_profile_v3_source_codex/profv3-01a12c09'
N=Path(__file__).resolve().parent
S=R/'execution/v2.4/receipts/W09/W09-99/checkpoint_r369_native_source_root/cp369-c19-20261009'
PY=Path('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe')
pins={};checks=[];written=[]
def pin(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def fixed(p,digest,size):return dict(path=str(p),sha256=digest,bytes=size)
def read(p,ref=None):
 r=pin(p)
 if ref is not None:assert r==dict(path=str(Path(ref['path']).resolve(strict=True)),sha256=ref['sha256'],bytes=ref['bytes'])
 assert r['path'] not in pins or pins[r['path']]==r;pins[r['path']]=r
 return Path(p).read_bytes()
def save(name,obj):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
 return pin(N/name)
def ck(name,value,detail=None):
 assert value,name;checks.append(dict(name=name,status='PASS',detail=detail))
def mod(name,raw,path):
 m=types.ModuleType(name);m.__file__=str(path);sys.modules[name]=m;exec(compile(raw,str(path),'exec'),m.__dict__);return m
def put(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_bytes(raw)
 if p not in written:written.append(p)
 return p
def putj(p,obj):return put(p,(json.dumps(obj,ensure_ascii=False,sort_keys=True)+'\n').encode())
def relpin(p,root,three=False):
 ref=pin(p);result=dict(path=p.relative_to(root).as_posix(),sha256=ref['sha256'])
 if three:result['bytes']=ref['bytes']
 return result
hr=fixed(C/'HDF.json','ea70b9e94ee38403a374b7f9586ce0373ca708c48e51a841f6a6d98de5c80962',2678)
mr=fixed(C/'MF.json','9dfac1c2966af3aefaeb645ed0edc19d81233db346dcbd5abc1b11e9ec2128eb',9043)
h=json.loads(read(hr['path'],hr));mf=json.loads(read(mr['path'],mr));assert h['manifest_ref']==mr
for ref in mf['members']:read(ref['path'],ref)
for ref in mf['v2_independent_review'].values():read(ref['path'],ref)
sample_ref=fixed(S/'nonformal-registration-delivery.original.root.jsonl','219312642745d2ee5cc919a410faa2e59e560aba41b0dfef399e792aeeb7f900',24304)
binding_ref=fixed(S/'nonformal-registration-delivery.binding.root.json','a9efe15f1f68bfbab03f0426c6d9e7a1bb30536091eeeb4e0683bf703d6df56e',1733)
sample=read(sample_ref['path'],sample_ref);binding=json.loads(read(binding_ref['path'],binding_ref))
for rel in ('execution/v2.4/formal_profile_w07.py','ops/ci/retrieval.py','ops/ci/w09_formal_router.py','ops/ci/w09_evidence_closure.py'):read(R/rel)
rt=ast.parse((R/'ops/ci/retrieval.py').read_bytes());source21=ast.literal_eval(next(x.value for x in rt.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SOURCES' for t in x.targets)))
for rel in source21:read(R/rel)
read(PY);read(Path(__file__))
gp=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
gr=read(gp,fixed(gp,'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',11404))
gm=mod('w09v3_review_guard',gr,gp);guard=gm.SourceReadGuard();fake=N/'synthetic-repo';fake.mkdir()
try:
 guard.acquire(list(pins.values()))
 ck('locked_python',Path(sys.executable).resolve()==PY.resolve())
 ck('finite_source_pins_exact_while_held',all(hashlib.sha256(guard.get_buffer(p)).hexdigest()==r['sha256'] for p,r in pins.items()),len(pins))
 before=guard.get_buffer(str(C/'formal_case_index.before.py'));after=guard.get_buffer(str(C/'formal_case_index.after.py'));profile=guard.get_buffer(str(C/'formal_profile_w09.after.py'))
 ck('W04_W07_prefix51719_exact',before[:51719]==after[:51719] and hashlib.sha256(before[:51719]).hexdigest()==mf['w07_prefix']['sha256'])
 ck('original_CRLF_prefix_preserved',before[:51719].count(b'\r\n')==after[:51719].count(b'\r\n')>0)
 bt,at,pt=ast.parse(before),ast.parse(after),ast.parse(profile);old={v.name:v for v in bt.body if isinstance(v,(ast.FunctionDef,ast.ClassDef))};new={v.name:v for v in at.body if isinstance(v,(ast.FunctionDef,ast.ClassDef))}
 ck('old_CLI_guard_exact',ast.dump(bt.body[-1])==ast.dump(at.body[-1]))
 ck('Reader_W07_loader_AST_unchanged',all(ast.dump(old[k])==ast.dump(new[k]) for k in ('Reader','_w07_profile')))
 ck('only_scoped_old_function_changes',{k for k in old if ast.dump(old[k])!=ast.dump(new[k])}=={'_registered_roots','_verify_owner','recheck_inputs','derive_formal_cases'})
 left=before.decode().replace('\r\n','\n').splitlines(keepends=True);right=after.decode().replace('\r\n','\n').splitlines(keepends=True)
 ck('forward_diff_exact',''.join(difflib.unified_diff(left,right,fromfile='formal_case_index.before.py',tofile='formal_case_index.after.py')).encode()==(C/'formal_case_index.forward.diff').read_bytes())
 ck('inverse_diff_exact',''.join(difflib.unified_diff(right,left,fromfile='formal_case_index.after.py',tofile='formal_case_index.before.py')).encode()==(C/'formal_case_index.inverse.diff').read_bytes())
 ck('full_original_inverse_bytes',hashlib.sha256(before).hexdigest()==mf['complete_byte_inverse']['sha256'] and len(before)==mf['complete_byte_inverse']['bytes'])
 api=mod('w09v3_review_index',after,C/'formal_case_index.after.py');pro=mod('w09v3_review_profile',profile,C/'formal_profile_w09.after.py')
 ck('new_CAS_API_wired',api._profile_api()._owned_inventory is api._owned_inventory and api._profile_api()._audit_range is api._audit_range)
 def reject(label,fn,code):
  try:fn()
  except api.InvalidEvidence as exc:ck(label,exc.code==code,exc.code)
  else:raise AssertionError(label+' accepted')
 pro._native_zero(api,{'exit_code':0},{'native_exit_code':0},'synthetic');ck('F1_int_zero',True)
 for label,value in [('false',False),('float',0.0),('null',None),('nonzero',1),('string','0')]:
  reject('F1_report_'+label,lambda v=value:pro._native_zero(api,{'exit_code':v},{'native_exit_code':0},'synthetic'),'NATIVE_EXIT_TYPE')
  reject('F1_tool_'+label,lambda v=value:pro._native_zero(api,{'exit_code':0},{'native_exit_code':v},'synthetic'),'NATIVE_EXIT_TYPE')
 rr=api.Reader(R);producer=rr.path('ops/ci/retrieval.py');sources=pro._producer_sources(api,rr,{producer:api.sha256(producer)})
 vector={rr.path(rel):api.sha256(rr.path(rel)) for rel in sources};hashes={rel:'sha256:'+vector[rr.path(rel)] for rel in sources}
 pro._source21(api,rr,{'version_manifest':{'source_sha256':hashes}},vector,sources,'synthetic');rr.finish();ck('F4_exact_current_Source21',sources==set(source21) and len(sources)==21)
 reject('F4_missing_source',lambda:pro._source21(api,api.Reader(R),{'version_manifest':{'source_sha256':dict(list(hashes.items())[:6])}},vector,sources,'synthetic'),'NATIVE_SOURCE21_SET')
 drift=dict(hashes);drift[next(iter(drift))]='sha256:'+'0'*64
 reject('F4_drift',lambda:pro._source21(api,api.Reader(R),{'version_manifest':{'source_sha256':drift}},vector,sources,'synthetic'),'CURRENT_SOURCE_CLOSURE')
 # F2 original v2 raw-time counterexample and genuine terminal ordering.
 def ev(action,time,test=None):
  e={'Action':action,'Time':'2026-10-01T00:00:'+time+'Z','Package':'synthetic'}
  if test:e['Test']=test
  return e
 events=[ev('start','00'),ev('run','01','TestW09Synthetic'),ev('pass','02','TestW09Synthetic'),ev('pass','03')]
 enc=lambda rows:('\n'.join(json.dumps(x) for x in rows)+'\n').encode()
 report={'started_at':'2026-10-01T00:00:00Z','ended_at':'2026-10-01T00:00:04Z'}
 interval=pro._native_event_interval(api,enc(events),report,['TestW09Synthetic'],'synthetic');ck('F2_ordered_original_events_accept',interval==('2026-10-01T00:00:00+00:00','2026-10-01T00:00:03+00:00'))
 future=copy.deepcopy(events)
 for e in future:e['Time']=e['Time'].replace('2026-10-01','2026-10-20')
 reject('F2_v2_Oct20_vs_Oct1_rejected',lambda:pro._native_event_interval(api,enc(future),report,['TestW09Synthetic'],'synthetic'),'GO_EVENT_CLOCK')
 reject('F2_missing_package_terminal',lambda:pro._native_event_interval(api,enc(events[:-1]),report,['TestW09Synthetic'],'synthetic'),'GO_EVENT_TERMINAL')
 reverse=copy.deepcopy(events);reverse[1]['Time']='2026-10-01T00:00:03Z'
 reject('F2_test_pass_before_run',lambda:pro._native_event_interval(api,enc(reverse),report,['TestW09Synthetic'],'synthetic'),'GO_EVENT_TERMINAL')
 early_package=[ev('start','00'),ev('pass','01'),ev('run','02','TestW09Synthetic'),ev('pass','03','TestW09Synthetic')]
 early_accepted=True
 try:pro._native_event_interval(api,enc(early_package),report,['TestW09Synthetic'],'synthetic')
 except api.InvalidEvidence:early_accepted=False
 ck('F2_package_terminal_causal_probe_completed',True,{'package_pass_before_selected_test_run_accepted':early_accepted,'events':early_package})
 outputs={route:{'native_started_at':report['started_at'],'native_ended_at':report['ended_at'],'native_event_started_at':interval[0],'native_event_ended_at':interval[1],'started_at':'2026-10-01T01:00:00Z','ended_at':'2026-10-01T01:10:00Z'} for route in pro.ROUTES}
 global_runs={case:{'ended_at':'2026-10-01T02:00:00Z'} for case in ('C19','A06')}
 pro._review_execution_cutoff(api,outputs,global_runs,'2026-10-02T00:00:00Z','2026-10-03T00:00:00Z');ck('F2_six_route_cutoff_accept',True)
 for key in ('native_event_ended_at','native_ended_at','ended_at'):
  future_output=copy.deepcopy(outputs);future_output[next(iter(outputs))][key]='2026-10-20T00:00:00Z'
  reject('F2_cutoff_future_'+key,lambda v=future_output:pro._review_execution_cutoff(api,v,global_runs,'2026-10-02T00:00:00Z','2026-10-03T00:00:00Z'),'REVIEW_EXECUTION_CUTOFF')
 # F3 all case variants, nested additions, mutation, removal and prior hashes.
 directory='execution/receipts/W09/retrieval/run-synthetic/owned';owned=fake/directory;first=put(owned/'one.raw',b'one');claim=relpin(first,fake,True)
 reader=api.Reader(fake);inventory=api._owned_inventory(reader,directory,[claim]);snapshot={'files':{str(p):v for p,v in reader.read_hashes.items()},'inventories':[inventory]}
 ck('F3_inventory_baseline',api.recheck_inputs(snapshot)['status']=='PASS')
 for name in ('extra.raw','extra.RAW','nested/extra.RaW'):
  p=put(owned/name,b'extra');ck('F3_reject_'+name,api.recheck_inputs(snapshot)['status']=='INVALID');p.unlink()
 first.write_bytes(b'drift');ck('F3_changed_member',api.recheck_inputs(snapshot)['status']=='INVALID');first.write_bytes(b'one')
 first.unlink();ck('F3_deleted_member',api.recheck_inputs(snapshot)['status']=='INVALID');first.write_bytes(b'one')
 badreader=api.Reader(fake);badreader.read_hashes[first.resolve()]='0'*64
 reject('F3_inventory_prior_hash',lambda:api._owned_inventory(badreader,directory,[claim]),'INPUT_CHANGED_DURING_READ')
 reject('F3_observed_prior_hash',lambda:pro._pin_observed(api,badreader,first.resolve(),claim['sha256']),'INPUT_CHANGED_DURING_READ')
 # F5 actual three-line Root sample is only protocol evidence.
 lines=sample.splitlines(keepends=True);records=[api.strict_json(line) for line in lines]
 ck('F5_actual_sample_pins_shape',len(lines)==3 and [hashlib.sha256(line).hexdigest() for line in lines]==binding['original_line_sha256'] and binding['protocol_observation_only'] is True and binding['W09_parent_or_formal_delivery'] is False)
 ranges=[{'path':binding['source_audit_path'],'offset':offset,'bytes':len(line),'sha256':digest} for offset,line,digest in zip(binding['source_line_offsets'],lines,binding['original_line_sha256'])]
 for item in ranges:api._audit_range(item)
 ck('F5_actual_original_audit_ranges_match',True,{'range_count':len(ranges),'source_append_allowed':True})
 cp=fake/'execution/v2.4/checkpoint.json';putj(cp,{'work_in_progress':{}})
 fake_ref={'path':pro.ROOT_CAPTURE_PREFIX+'capture.json','sha256':'0'*64,'bytes':1}
 reject('F5_missing_approved_Canon_index',lambda:pro._capture_registry(api,api.Reader(fake),{'delivery_ref':fake_ref}),'ROOT_CAPTURE_AUTHORITY_OPEN')
 context=putj(fake/pro.PREFIX/'context.json',{'synthetic_non_authoritative':True});review=putj(fake/pro.PREFIX/'review.json',{'synthetic_non_authoritative':True})
 cr=relpin(context,fake);vr=relpin(review,fake)
 def packet(origin_raw,capture):
  op=put(fake/pro.ROOT_ORIGIN_PREFIX/'origin.jsonl',origin_raw);orr=relpin(op,fake,True)
  cap=copy.deepcopy(capture);cap['original_capture_ref']=orr
  cap_path=putj(fake/pro.ROOT_CAPTURE_PREFIX/'capture.json',cap);capref=relpin(cap_path,fake,True)
  reg={'schema':'researchos.root-delivery-capture-index.v2','writer_actor':'codex:/root','Root_thread_id':pro.ROOT_THREAD_ID,'entries':[{'event_id':cap['message_id'],'capture_ref':capref,'origin_ref':orr}]}
  regpath=putj(fake/pro.ROOT_CAPTURE_INDEX,reg);regref=relpin(regpath,fake,True)
  putj(cp,{'work_in_progress':{'w09_root_delivery_capture_index_ref':regref}})
  return {'event_id':cap['message_id'],'delivery_ref':capref,'origin_event_ref':orr,'review_ref':vr,'context_ref':cr}
 issued=packet(sample,binding)
 reader=api.Reader(fake);reader.w09_audit_ranges=[]
 reject('F5_real_nonformal_sample_cannot_authorize',lambda:pro._root_original(api,reader,issued,binding['sender'],{'context':context}),'ROOT_ORIGINAL_EVENT')
 # Inspect actual record parser independently, ending before formal acceptance conditions.
 original=next(x for x in pt.body if isinstance(x,ast.FunctionDef) and x.name=='_root_original')
 stop=next(i for i,x in enumerate(original.body) if isinstance(x,ast.Expr) and isinstance(x.value,ast.Call) and any(isinstance(v,ast.Constant) and v.value=='researchos.root-actual-audit-formal-delivery.v1' for v in ast.walk(x)))
 parser=copy.deepcopy(original);parser.name='_review_protocol_prefix_only';parser.body=parser.body[:stop]+[ast.Return(value=ast.Tuple(elts=[ast.Name(id='header',ctx=ast.Load()),ast.Name(id='communication',ctx=ast.Load()),ast.Name(id='message',ctx=ast.Load())],ctx=ast.Load()))]
 parser_tree=ast.fix_missing_locations(ast.Module(body=[parser],type_ignores=[]));ns=dict(pro.__dict__);exec(compile(parser_tree,'<independent-prefix-only-nonauthoritative>','exec'),ns)
 parse=ns[parser.name];got=parse(api,api.Reader(fake),issued,binding['sender'],{'context':context})
 ck('F5_actual_sample_protocol_parser_only_accepts',list(got)==records,'AST prefix only, expressly no formal authority')
 def protocol_negative(label,mutate,code='ROOT_ORIGINAL_EVENT'):
  objs=copy.deepcopy(records);mutate(objs);iss=packet(enc(objs),binding)
  reject(label,lambda:parse(api,api.Reader(fake),iss,binding['sender'],{'context':context}),code)
 protocol_negative('F5_bool_ordinal',lambda v:v[1].update(ordinal=True))
 protocol_negative('F5_nonadjacent_ordinal',lambda v:v[2].update(ordinal=v[2]['ordinal']+2))
 protocol_negative('F5_different_timestamps',lambda v:v[2].update(timestamp='2026-10-01T00:00:00Z'))
 protocol_negative('F5_wrong_root_thread',lambda v:v[0]['payload'].update(id='not-root'))
 protocol_negative('F5_wrong_sender',lambda v:v[2]['payload'].update(author='/root/author'))
 protocol_negative('F5_wrong_recipient',lambda v:v[2]['payload'].update(recipient='/root/else'))
 protocol_negative('F5_wrong_message_id',lambda v:v[2]['payload'].update(id='invented'))
 protocol_negative('F5_encrypted_content',lambda v:v[2]['payload'].update(content=[{'type':'input_text','encrypted_content':'not-plaintext'}]),'ROOT_ORIGINAL_PLAINTEXT_REQUIRED')
 protocol_negative('F5_mixed_content',lambda v:v[2]['payload']['content'].append({'type':'input_text','text':'extra'}),'ROOT_ORIGINAL_PLAINTEXT_REQUIRED')
 # Real protocol envelope plus fabricated formal plaintext still must match actual audit bytes.
 forged=copy.deepcopy(records);text=cr['sha256']+' '+vr['sha256']+' SYNTHETIC NOT A REAL DELIVERY';forged[2]['payload']['content']=[{'type':'input_text','text':text}]
 forged_raw=enc(forged);forged_lines=forged_raw.splitlines(keepends=True)
 cap={'schema':'researchos.root-actual-audit-formal-delivery.v1','issued_by':'codex:/root','protocol_observation_only':False,'W09_parent_or_formal_delivery':True,'Root_thread_id':pro.ROOT_THREAD_ID,'message_id':binding['message_id'],'sender':binding['sender'],'recipient':binding['recipient'],'received_at':binding['received_at'],'review_ref':vr,'context_ref':cr,'content_sha256':hashlib.sha256(text.encode()).hexdigest(),'root_observed_at':binding['captured_utc'],'source_line_offsets':binding['source_line_offsets'],'original_line_sha256':[hashlib.sha256(line).hexdigest() for line in forged_lines],'source_audit_path':pro.ROOT_SOURCE_AUDIT_LOG,'source_prefix_size_observed':binding['source_prefix_size_observed']}
 iss=packet(forged_raw,cap);rdr=api.Reader(fake);rdr.w09_audit_ranges=[]
 reject('F5_fabricated_formal_plaintext_vs_real_audit',lambda:pro._root_original(api,rdr,iss,binding['sender'],{'context':context}),'ROOT_ORIGINAL_SOURCE')
 # Pin adapter: byte-count bool/extra field/index drift and range CAS negative controls.
 reg=api.strict_json(cp.read_bytes());reg['work_in_progress']['w09_root_delivery_capture_index_ref']['bytes']=True;putj(cp,reg)
 reject('F5_boolean_approved_byte_count',lambda:pro._capture_registry(api,api.Reader(fake),iss),'ROOT_CAPTURE_AUTHORITY_OPEN')
 rangefile=put(fake/'range-source.txt',b'original\n');rng={'path':str(rangefile),'offset':0,'bytes':9,'sha256':hashlib.sha256(b'original\n').hexdigest()};rs={'files':{},'inventories':[],'audit_ranges':[rng]}
 ck('F5_range_CAS_baseline',api.recheck_inputs(rs)['status']=='PASS');rangefile.write_bytes(b'changed!\n');ck('F5_range_CAS_changed_reject',api.recheck_inputs(rs)['status']=='INVALID')
 for item in ranges:api._audit_range(item)
 ck('F5_original_Root_ranges_unchanged_after_controls',True)
 save('protocol-and-clock-observations.json',{'scope':'SYNTHETIC_NONAUTHORITATIVE_SOURCE_ONLY','real_sample_ref':sample_ref,'binding_ref':binding_ref,'real_original_ranges':ranges,'actual_formal_delivery_created':False,'current_Canon_approval_created':False,'package_terminal_causal_probe':{'accepted':early_accepted,'events':early_package,'report_interval':report},'source_authority_note':'Only the isolated synthetic repository received sample checkpoint/index objects. No real Canon approval or Root-origin data was written.'})
finally:
 observation=guard.close();save('sourceguard.final.json',observation)
 for p in reversed(written):
  assert p.resolve(strict=False).is_relative_to(fake.resolve())
  if p.exists():p.unlink()
 for p in sorted([p for p in fake.rglob('*') if p.is_dir()],key=lambda p:len(p.parts),reverse=True):
  assert p.resolve().is_relative_to(fake.resolve());p.rmdir()
 fake.rmdir()
ck('actual_SourceGuard_closed0',observation['verification']=='PASSED' and observation['closed'] is True and observation['retained_handles_count']==0 and not observation['errors'])
save('input-pins.json',list(pins.values()))
save('controls.json',{'scope':'SYNTHETIC_NONAUTHORITATIVE_SOURCE_ONLY','checks':checks,'actual_runs':0,'canonical_writes':0,'formal_cases_created':0,'package_terminal_before_test_accepted':early_accepted})
print(json.dumps({'status':'PASS_REVIEW_CONTROLS','checks':len(checks),'guarded_inputs':len(pins),'retained_handles_count':0,'package_terminal_before_test_accepted':early_accepted}))
