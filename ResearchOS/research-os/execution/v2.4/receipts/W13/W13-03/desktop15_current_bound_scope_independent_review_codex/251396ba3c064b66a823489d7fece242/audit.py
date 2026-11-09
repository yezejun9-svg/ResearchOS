from pathlib import Path
import ast, hashlib, json, os, traceback
R=Path('D:/作品集/ResearchOS/research-os')
O=Path(__file__).parent
P=R/'execution/v2.4/receipts/W13/W13-03'
B=P/'desktop15_root_scope_binding_executor_codex/8792799f829a23452ae5d89a59e1b0cf'
T=P/'desktop15_root_scope_binding_preparation_codex/5097ef19e4414a81b6457363a3b76060'
checks=[]; observed={}; cache={}
def check(ok,name,detail=None): checks.append({'check':name,'passed':bool(ok),'detail':detail})
def path(v):
 p=Path(v);return p if p.is_absolute() else R/p
def digest(p):
 h=hashlib.sha256();n=0
 with p.open('rb') as f:
  while b:=f.read(1048576):h.update(b);n+=len(b)
 return h.hexdigest(),n
def pin(p):
 p=path(p);h,n=digest(p);return {'path':str(p),'sha256':h,'bytes':n}
def verify(ref):
 p=path(ref['path']);key=str(p).casefold(); before=p.stat()
 if key not in cache:cache[key]=digest(p)
 h,n=cache[key];check((h,n)==(ref['sha256'],ref['bytes']),'pin:'+str(p))
 check(p.resolve()==p.absolute() and not p.is_symlink() and not getattr(before,'st_file_attributes',0)&0x400,'regular-noalias:'+str(p))
 observed[key]={'path':str(p),'sha256':h,'bytes':n};return p
def doc(ref):return json.loads(verify(ref).read_bytes())
def local(n):return json.loads((B/n).read_bytes())
def refs(obj):
 if isinstance(obj,dict):
  if {'path','sha256','bytes'}<=obj.keys():yield obj
  else:
   for v in obj.values():yield from refs(v)
 elif isinstance(obj,list):
  for v in obj:yield from refs(v)
def tree(n):
 d={}
 for line in (B/n).read_bytes().split(b'\0'):
  if line:
   a,b=line.split(b'\t',1);m,k,h=a.decode('ascii').split();d[b.decode('utf-8')]={'mode':m,'kind':k,'blob':h}
 return d
def save(n,obj):
 with (O/n).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
try:
 fixed={'binding.prepared.json':'a2743299f070fddc626674e54b4a97dae998462a14cc85496de761431811f985','manifest.json':'57329d32e95f15defee777ef89c402d1a40045c021d2e438f671647e015998e8','scope.bound.proposed.json':'0672885b089a13beae915a87dc57aeaa978e92eaccd8870aad16af143d36e9a2','scope.activation-plan.json':'691ebfb8188fe355160030b9af335f94dff2be6af1dbae95729c94a627e99d1a'}
 for n,h in fixed.items():check(pin(B/n)['sha256']==h,'fixed '+n)
 mf=local('manifest.json');check(mf['count']==len(mf['entries'])==42,'42 sealed members')
 check(len({str(path(x['path'])).casefold() for x in mf['entries']})==42,'MF unique')
 for x in mf['entries']:check(verify(x).parent==B,'MF direct namespace member')
 binding=local('binding.prepared.json');s=local('scope.bound.proposed.json');act=local('scope.activation-plan.json')
 for x in binding['immutable_inputs']:verify(x)
 check(len(binding['immutable_inputs'])==8844,'immutable input count')
 for k in ['request_ref','scope_ref','activation_plan_ref','current_root_handoff_ref','origin_cut_ref','current_root_manifest_ref']:verify(binding[k])
 active=dict(s);active.update(authorized=True,status='ROOT_REGISTERED_DESKTOP15_SOURCE_COMMIT_ONCE')
 raw=(json.dumps(active,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
 check(act['future_scope_payload']==active and act['authorized'] is False and act['future_root_grant'] is None,'exact activation two fields')
 check((hashlib.sha256(raw).hexdigest(),len(raw))==('62d704e9add7294f11ecfd8dc2ba35238a37b285fa32febfe8977b266142daba',18710),'future byte roundtrip')
 check(act['future_scope_ref']=={'path':str(path(s['registration_namespace'])/'scope_registration.json'),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)},'future exact ref spelling')
 check(binding['expected_before']==s['expected_before_registration']==[331,159,509] and binding['expected_after']==s['expected_registration']==[332,160,516],'explicit tuples')
 check(binding['authorized'] is False and binding['future_root_grant'] is None and s['authorized'] is False,'no preparation grant')
 canon=[]
 for name,live,copy in zip(['checkpoint','path_ownership','step_state','commands'],binding['canonical_before_refs'],binding['canonical_copies']):
  lp=verify(live); cp=verify(copy); check(lp==R/f'execution/v2.4/{name}.json' and lp.read_bytes()==cp.read_bytes(),'ordered current canonical '+name);canon.append(json.loads(lp.read_bytes()))
 check([canon[0]['revision'],canon[1]['revision'],len(canon[0]['failure_counters'])]==[331,159,509],'live tuple')
 check(canon[0]['head']==s['expected_cli43_head']=='a510dbef4a7e08fb5c428df44c39b133f3ffa856','registered current source head')
 origins=binding['confirmed_pending_origins'];check(len(origins)==7 and len({x['origin'] for x in origins})==7 and len({x['evidence_ref']['sha256'] for x in origins})==7,'seven distinct origins')
 for row in origins:
  check(doc(row['evidence_ref'])==row['original_payload'],'whole original payload '+row['origin'])
  check(row['count_once'] is True and row['counter_reset'] is False and row['automatic_retry'] is False and row['product_cases_run']==0,'origin no reset/product '+row['origin'])
 save('origin-mapping.json',[{'origin':x['origin'],'evidence_ref':x['evidence_ref'],'actual_outer_exit':x['actual_outer_exit'],'actual_native_exit':x['actual_native_exit']} for x in origins])
 cut=doc(binding['origin_cut_ref']);save('cut-shape.json',{'keys':list(cut),'origin_count':len(origins)})
 runtime=doc(s['runtime_resources_ref']);append=runtime['root_append_only_exact_git_image'];old=doc(append['base_catalog_ref']);new=append['additional_ref']
 check(runtime['files']==old['files']+[new] and len(old['files'])==1211 and len(runtime['files'])==1212,'1211 exact prefix plus locked Git')
 verify(new);check(new['sha256']=='da240fe9bc24895b3e04150a4990b8a6ff329ecabcd8f19684c2cc310da5ef3f' and new['bytes']==46480,'locked Git addition')
 labels=['head','branch','status','index','config','tree43','tree2cdb','tree06b','desktop-parent','desktop-delta6']
 for label in labels:
  j=local(label+'.invocation.json');r=j['owned_result'];c=r['job_cleanup']
  check(j['actual_native_exit']==r['actual_exit']==0 and j['error'] is None and r['error'] is None and r['timed_out'] is False and r['resumed'] is True,'actual Git '+label)
  check(c['errors']==[] and c['active_processes_last_observed']==0 and all(c[k] is True for k in ['unnamed_exclusive_job','assigned_before_resume','kill_on_job_close_configured','primary_exit_confirmed','job_idle_confirmed','handles_closed']),'actual Job '+label)
 check(binding['Git_readonly_calls']==10,'10 owned read-only calls')
 check((B/'head.stdout.raw').read_text().strip()==s['expected_cli43_head'] and (B/'branch.stdout.raw').read_text().strip()==s['expected_main_branch'] and (B/'index.stdout.raw').read_bytes()==b'','saved head branch index')
 check((B/'status.stdout.raw').read_bytes()==verify(s['status_ref']).read_bytes(),'status exact saved ref')
 check(len(s['old_deleted_paths'])==11 and all(not os.path.lexists(R/x) for x in s['old_deleted_paths']),'old11 absent now')
 exact=doc(s['exact15_ref']); t43=tree('tree43.stdout.raw');tbase=tree('tree2cdb.stdout.raw');td=tree('tree06b.stdout.raw')
 check(len(exact)==15 and len({x['path'] for x in exact})==15,'15 exact unique')
 check(sum(x['before_git'] is None for x in exact)==6,'six absent nine existing')
 for x in exact:
  name=x['path'];check(t43.get(name)==x['before_git']==tbase.get(name) and td.get(name)==x['after_git'],'source tree mode/blob '+name)
  after=verify(x['final_blob_ref']).read_bytes();check(hashlib.sha1(b'blob '+str(len(after)).encode()+b'\0'+after).hexdigest()==x['after_git']['blob'],'actual Git blob '+name)
  if x['before_git'] is None:check(not os.path.lexists(R/name),'absent preimage '+name)
  else:check((R/name).read_bytes()==verify(x['before_blob_ref']).read_bytes(),'current preimage '+name)
 shared=set(s['shared38_paths'])|set(s['cli8_paths']); paths={x['path'] for x in exact}
 check(len(shared)==43 and not shared&paths and len(shared|paths)==58,'43 plus disjoint15 union58')
 protected=local('protected.actual-current43.json');check(len(protected)==6983,'6983 protected')
 for x in protected:verify(x)
 check(not {str(path(x['path'])).casefold() for x in protected}&{str(R/x).casefold() for x in paths},'no protected source target overlap')
 for k in ['new_output_root','registration_namespace']:check(not path(s[k]).exists(),'fresh '+k)
 check(not path(str(s['new_output_root'])+'-outer').exists(),'fresh outer')
 check(s['exact_paths']==15 and s['union_paths']==58 and s['apply_cap']==s['commit_cap']==1 and s['git_step_cap']==80 and s['product_tests_HTTP_SQL_models']==0,'source-only fixed limits')
 check(all(s[k] is False for k in ['source_acceptance','fresh43_validation_authorized','fresh58_validation_authorized','Desktop_GUI_install_NVDA_authorized','author169_inherited_as_Root_current']) and s['formal_increment']==0,'open product/formal gates')
 for x in refs(s):
  if path(x['path']).exists():verify(x)
 builder=(T/'build-metadata-templates.py').read_bytes();engine=(T/'metadata-engine.template.py').read_bytes()
 check(hashlib.sha256(builder).hexdigest()=='d7073a83360468ea7b532466f98140e39349256bb5b4cffa540581dcaba197be','metadata builder pin')
 check(hashlib.sha256(engine).hexdigest()=='bb3beccc2a4c2a576b648871dacc0dcab8f8bbff5258e1f0369d1d0af0f13280','metadata engine pin')
 ast.parse(builder);ast.parse(engine);check(True,'metadata AST only; no imports or candidate execution')
 source=engine.decode('utf-8');nodes={n.name:n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)}
 register=ast.get_source_segment(source,nodes['register']);desired=ast.get_source_segment(source,nodes['desired']);seal=ast.get_source_segment(source,nodes['seal']);grant=ast.get_source_segment(source,nodes['grant'])
 check("for i, q in enumerate(CANON[:2])" in register and register.count('os.replace(')==1 and "four canonical completed prefix drift after source guard" in register and "four canonical target drift after final source guard" in register,'two writes and immediate all4 guard')
 check("cp['failure_counters'].extend(copy.deepcopy(p['origins']))" in desired and "before[2], before[3]" in desired and "cp['failure_counters'][:a[2]] == original_cp['failure_counters']" in desired,'append7 original prefix and byte-preserved STCM')
 check("'compile_test_SQL_HTTP_model_authorized': False" in desired and "'formal_increment': 0" in desired,'lease source only')
 check("save('scope_registration.json', b, True)" in seal and "actual registration failure" in seal and "exclusive grant leaf" in grant,'scope materialized after closed CAS; separate grant')
 save('metadata-static-map.json',{'builder':pin(T/'build-metadata-templates.py'),'engine':pin(T/'metadata-engine.template.py'),'functions':{n:{'line':v.lineno,'end_line':v.end_lineno} for n,v in nodes.items()},'candidate_definitions_imported':False,'pure_transform_executed':False,'review':'Source-level inspection only. Builder invokes only desired after separately reviewed emitter; actual emitted scripts/desired4 require another review. Controller rechecks actual4 and registration seal before any source mutation. Grant observation is point-in-time; it does not prove OS lifecycle.'})
 for live in binding['canonical_before_refs']:check(digest(path(live['path']))==(live['sha256'],live['bytes']),'canonical after review '+live['path'])
 save('observed-inputs.json',list(observed.values()))
 save('audit.json',{'schema':'researchos.desktop15-bound-scope-readonly-audit.v1','checks':checks,'count':len(checks),'failed':[x for x in checks if not x['passed']],'distinct_hashed_refs':len(cache),'candidate_executions':0,'canonical_writes':0,'new_failure_origins':[]})
 print(json.dumps({'checks':len(checks),'failed':[x for x in checks if not x['passed']],'distinct_hashed_refs':len(cache),'output':str(O)},ensure_ascii=False))
except BaseException:
 save('audit.exception.json',{'traceback':traceback.format_exc(),'candidate_executions':0});raise
