from pathlib import Path, PureWindowsPath
from datetime import datetime,timezone
import json,hashlib,ast,types,copy
R=Path('D:/作品集/ResearchOS/research-os')
S=R/'execution/v2.4/receipts/W09/W09-99/w09_main_c19_dispatcher_caller_source_codex/c19call-01a12d10-v6'
O=R/'execution/v2.4/receipts/W09/W09-99/main_c19_dispatcher_caller_independent_review_codex/c19v6-review-20261009'
def pin(p):
 p=Path(p);raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(p):return json.loads(Path(p).read_bytes())
def save(name,data):
 p=O/name
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 return pin(p)
h=read(S/'HDF.json');m=read(S/'MF.json')
assert pin(S/'HDF.json')['sha256']=='8a5c60ca1a8ec12ad273f098091b5ff580de5be8f72ffe38c19afb8ae64ddd78'
assert pin(S/'MF.json')['sha256']=='68e4889942de67e656ebecc5ffab7007109271c482c2f287aac1f312ae71b077'
prior=read(h['v4_review_ref']['path']);prior_m=read(prior['manifest_ref']['path'])
prior_probe=next(x for x in prior_m['members'] if Path(x['path']).name=='independent-memory-probes.json')
inputs=read(m['input_vector_ref']['path']);nh=read(h['native_handoff_ref']['path']);ready=read(nh['prepare_ready_ref']['path']);choice=read(ready['source_choice_ref']['path'])
names=['checkpoint','path_ownership','step_state','commands'];oldpaths={str(R/('execution/v2.4/'+n+'.json')).casefold() for n in names}
refs=[x for x in inputs['refs'] if x['path'].casefold() not in oldpaths]
refs += [pin(S/'HDF.json'),pin(S/'MF.json'),m['input_vector_ref'],h['source_guard_cleanup_ref'],h['original_observations_ref'],h['v4_review_ref'],prior['manifest_ref'],prior['source_decision_ref'],prior['findings_ref'],prior_probe,prior['caller_ref'],nh['prepare_ready_ref'],nh['producer_closed_ref'],nh['native_packet_ref'],ready['source_choice_ref']]
refs += ready['source21'];refs += [x for x in choice['main_seven_after_refs'] if x['path'].casefold() not in oldpaths]
previous5=read(h['v5_review_ref']['path'])
refs += [h['v5_review_ref'],previous5['manifest_ref'],previous5['caller_ref'],previous5['source_decision_ref'],previous5['findings_ref']]
refs += [x for x in inputs['refs'] if x['path'].casefold()==str(R/'execution/v2.4/commands.json').casefold()]

archives=[]
for n,old in zip(names,ready['canonical_vector']['refs']):
 ar=pin(Path(h['native_handoff_ref']['path']).parent/('historical.cp369.'+n+'.json'))
 assert ar['sha256']==old['sha256'] and ar['bytes']==old['bytes'];archives.append(ar);refs.append(ar)
gr=next(x for x in refs if Path(x['path']).name=='source_read_guard.py');raw=Path(gr['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==gr['sha256']
gm=types.ModuleType('v5_independent_guard');exec(compile(raw,gr['path'],'exec'),gm.__dict__)
g=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);g.acquire(refs)
checks=[];unchanged=[];facts={}
try:
 source=g.get_buffer(h['caller_source_ref']['path']).decode();tree=ast.parse(source);funcs={x.name:x for x in tree.body if isinstance(x,ast.FunctionDef)}
 prior_tree=ast.parse(g.get_buffer(prior['caller_ref']['path']));oldfuncs={x.name:x for x in prior_tree.body if isinstance(x,ast.FunctionDef)}
 for name in ['strict_json','pin','verify_ref','checked','frozen_plan','selected_registry','qualified_modes','historical_archive_bindings','packet_inventory','strict_pass']:
  assert ast.dump(funcs[name],include_attributes=False)==ast.dump(oldfuncs[name],include_attributes=False);unchanged.append(name)
 # Pure function definitions only, no candidate execute/import or process methods.
 fnames=['require','source_ref','validate_scope','validate_source_review','_lease_active','validate_canon_lease','root_request','validate_sealed_static_table','strict_pass']
 ns={'__file__':h['caller_source_ref']['path'],'datetime':datetime,'timezone':timezone}
 exec(compile(ast.Module(body=[funcs[x] for x in fnames],type_ignores=[]),'<v5-independent-memory-functions>','exec'),ns)
 class MP(PureWindowsPath):
  def resolve(self,*a,**kw):return self
  def exists(self):return False
  def read_bytes(self):return json.dumps(fs[str(self)],ensure_ascii=False).encode()
 root=MP(str(R));source_dir=MP(str(S));docs={};fs={};live={}
 def fakepin(p):return {'path':str(MP(p)),'sha256':live.get(str(MP(p)),'a'*64),'bytes':1}
 def add(name,doc):
  ref=fakepin(MP('Z:/SYNTHETIC_ONLY')/name);docs[ref['path']]=doc;return ref
 fields=next(x for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SCOPE_FIELDS' for t in x.targets))
 exec(compile(ast.Module(body=[fields],type_ignores=[]),'<exact-scope-fields>','exec'),ns)
 ns.update(ROOT=root,SOURCE_DIR=source_dir,Path=MP,ROUTES=('test.research.fixture','test.retrieval'),SOURCE_ACTOR='codex:/root/w09_formal_profile_source_impl',SLICE='C19_MAIN_TWO_DISPATCHERS',LEASE_STATE='ROOT_REGISTERED_PENDING_C19_MAIN_TWO_DISPATCHERS',pin=fakepin,strict_json=json.loads,checked=lambda ref:(docs[ref['path']],ref))
 callerref=fakepin(ns['__file__']);contractref=fakepin(source_dir/'root-calling-contract.source.json');vectorinput=add('source-input-pins.json',{})
 mfref=add('MF.json',{'schema':'researchos.w09-c19-two-consumer-source-manifest.v1','caller_source_ref':callerref,'contract_ref':contractref,'input_vector_ref':vectorinput})
 hdfref=add('HDF.json',{'status':'SOURCE_ONLY_PENDING_ROOT_REGISTRATION','caller_source_ref':callerref,'manifest_ref':mfref,'root_contract_ref':contractref})
 reviewer='codex:/root/native_temp_independent_review'
 source_review={'schema':'researchos.w09-main-c19-two-dispatchers-independent-source-decision.v1','decision':'ACCEPTED_SOURCE_ONLY','actor_id':reviewer,'actor_role':'INDEPENDENT_NON_AUTHOR','source_author_id':ns['SOURCE_ACTOR'],'source_hdf_ref':hdfref,'source_mf_ref':mfref,'caller_ref':callerref,'root_contract_ref':contractref,'SourceAcceptedonly':True,'noactualorformal':True,'actual_dispatcher_run':False,'formal_acceptance':False,'parent_acceptance':False,'formal_case_accepted_delta':0,'execution_grant':False}
 reviewref=add('source-decision.json',source_review)
 outputroot=str(root/'execution/v2.4/receipts/W09/W09-99/SYNTHETIC_AUTHORIZED_ROOT')
 scope={key:fakepin('Z:/SYNTHETIC_ONLY/'+key) for key in ns['SCOPE_FIELDS']}
 scope.update(schema='researchos.w09-c19-main-two-dispatcher-scope.v1',issued_by='codex:/root',slice_id=ns['SLICE'],formal_dispatcher=True,formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0,expected_checkpoint_revision=370,expected_previous_checkpoint_revision=369,expected_path_ownership_revision=174,routes=list(ns['ROUTES']),source_actor=ns['SOURCE_ACTOR'],source_reviewer=reviewer,source_hdf_ref=hdfref,source_mf_ref=mfref,caller_ref=callerref,root_contract_ref=contractref,source_review_ref=reviewref,before_canonical_refs=[fakepin('Z:/SYNTHETIC_ONLY/before-'+n+'.json') for n in names],before_canonical_revisions={'checkpoint':369,'path_ownership':173,'commands':39},authorized_output_root=outputroot)
 scoperef=add('scope-registration.root.json',scope)
 lease={'step_id':'W09-99','slice_id':ns['SLICE'],'state':ns['LEASE_STATE'],'scope_ref':scoperef,'source_handoff_ref':hdfref,'source_review_ref':reviewref,'lease_status':'ACTIVE','lease_expires_at':'2099-01-01T00:00:00Z','output_root':outputroot,'routes':list(ns['ROUTES'])}
 ownerdoc={**lease,'owner_id':'codex:/root','selected_worker_id':'codex:/root'};ownerref=add('owner.json',ownerdoc)
 workerdoc={**lease,'worker_id':'codex:/root','selected_owner_ref':ownerref};workerref=add('worker.json',workerdoc)
 workerrow={**lease,'owner':'codex:/root','selected_owner_ref':ownerref,'worker_document_ref':workerref}
 subtask={**lease,'owner':'codex:/root','current_source_writer':None,'owner_document_ref':ownerref,'worker_document_ref':workerref,'formal_case_accepted_delta':0,'parent_acceptance':False}
 cp={'revision':370,'expected_previous_revision':369,'work_in_progress':{'w09_c19_two_dispatcher_scope_ref':scoperef},'workers':[workerrow]}
 ow={'revision':174,'active_integrator':{'id':'codex:/root'},'card_path_bindings':{'W09-99':{'owner':'codex:/root','subtasks':{'c19_main_two_dispatchers':subtask}}}}
 canon=[root/'execution/v2.4'/(n+'.json') for n in names];fs[str(canon[0])]=cp;fs[str(canon[1])]=ow
 vectorref=add('vector.json',{'schema':'researchos.w09-c19-consumer-current-canonical-vector.v1','checkpoint_revision':370,'path_ownership_revision':174,'refs':[fakepin(p) for p in canon]})
 proofref=add('proof.json',{'issued_by':'codex:/root','scope_ref':scoperef,'current_canonical_vector_ref':vectorref,'previous_checkpoint_revision':369,'registered_checkpoint_revision':370})
 request={'schema':'researchos.w09-c19-two-dispatcher-root-request.v1','issued_by':'codex:/root','formal_acceptance':False,'native_producer_rerun':False,'registry_writes':False,'canonical_writes':False,'go_provider_calls':False,'exact_routes':list(ns['ROUTES']),'scope_ref':scoperef,'source_hdf_ref':hdfref,'source_review_ref':reviewref,'current_canonical_vector_ref':vectorref,'actual_registration_proof_ref':proofref,'current_owner_ref':ownerref,'current_worker_ref':workerref,'output_dir':str(MP(outputroot)/'new-run')}
 def check(name,action,expected=None):
  try:action()
  except ValueError as e:
   assert expected is not None and str(e)==expected,(name,str(e),expected)
   checks.append({'name':name,'observed':str(e),'expected':expected,'pass':True,'kind':'INDEPENDENT_SYNTHETIC_MEMORY'})
  else:
   assert expected is None,(name,'accepted bad input')
   checks.append({'name':name,'observed':'PASS','expected':'PASS','pass':True,'kind':'INDEPENDENT_SYNTHETIC_MEMORY'})
 check('full_bound_acyclic_future_registration_positive',lambda:ns['root_request'](request))
 original_cp=copy.deepcopy(cp);original_ow=copy.deepcopy(ow)
 for label,changed,code in [('missing',[], 'CANON_WORKER_NOT_UNIQUE'),('duplicate',[workerrow,copy.deepcopy(workerrow)],'CANON_WORKER_NOT_UNIQUE')]:
  cp['workers']=changed;check('v4_'+label+'_canonical_worker_closed',lambda:ns['root_request'](request),code)
 cp.clear();cp.update(copy.deepcopy(original_cp))
 conflict={**lease,'step_id':'W05-99','slice_id':'OTHER_SLICE','owner':'other','scope_ref':fakepin('Z:/other-scope'),'worker_document_ref':fakepin('Z:/other-worker'),'selected_owner_ref':fakepin('Z:/other-owner')}
 cp['workers'].append(conflict);check('v4_conflicting_active_worker_output_closed',lambda:ns['root_request'](request),'CANON_WORKER_CONFLICT');cp.clear();cp.update(copy.deepcopy(original_cp))
 ow['card_path_bindings']['W09-99']['subtasks']={}
 check('v4_absent_canon_owner_closed',lambda:ns['root_request'](request),'CANON_SUBTASK_NOT_REGISTERED');ow.clear();ow.update(copy.deepcopy(original_ow))
 for location,label in [(docs[ownerref['path']],'owner_doc'),(docs[workerref['path']],'worker_doc'),(cp['workers'][0],'canon_worker'),(ow['card_path_bindings']['W09-99']['subtasks']['c19_main_two_dispatchers'],'canon_owner')]:
  before=location['lease_expires_at'];location['lease_expires_at']='2000-01-01T00:00:00Z'
  check('expired_'+label,lambda:ns['root_request'](request),'LEASE_EXPIRED');location['lease_expires_at']=before
 review_original=copy.deepcopy(docs[reviewref['path']])
 docs[reviewref['path']]={'reviewer_id':reviewer,'decision':'ACCEPTED_SOURCE_ONLY','formal_acceptance':False}
 check('v4_three_field_unbound_review_closed',lambda:ns['root_request'](request),'SOURCE_REVIEW_NOT_BOUND')
 docs[reviewref['path']]=copy.deepcopy(review_original)
 for field in ['source_hdf_ref','source_mf_ref','caller_ref','root_contract_ref']:
  docs[reviewref['path']][field]=fakepin('Z:/unrelated/'+field)
  check('unrelated_review_'+field,lambda:ns['root_request'](request),'SOURCE_REVIEW_NOT_BOUND')
  docs[reviewref['path']]=copy.deepcopy(review_original)
 docs[reviewref['path']]['actor_id']='codex:/different-reviewer'
 check('scope_reviewer_identity_mismatch',lambda:ns['root_request'](request),'SOURCE_REVIEW_NOT_BOUND');docs[reviewref['path']]=copy.deepcopy(review_original)
 docs[reviewref['path']]['actor_role']='AUTHOR'
 check('author_role_refused',lambda:ns['root_request'](request),'SOURCE_REVIEW_NOT_BOUND');docs[reviewref['path']]=copy.deepcopy(review_original)
 check('requested_actor_id_without_legacy_reviewer_id_positive',lambda:ns['root_request'](request))
 for field in ['current_canonical_vector_ref','future_request_sha256','actual_registration_proof_ref']:
  scope[field]=fakepin('Z:/forbidden/'+field);check('v4_forbidden_scope_'+field,lambda:ns['root_request'](request),'SCOPE_EXACT_FIELDS');del scope[field]
 scope['before_canonical_revisions']['commands']=True
 check('scope_bool_historical_revision_refused',lambda:ns['root_request'](request),'SCOPE_REGISTERED_SLICE');scope['before_canonical_revisions']['commands']=39
 # Independently verify currently stable sealed static pins; time-of-check gap is separate.
 actualtable={x['path'].casefold():x for x in inputs['refs']}
 staticns=dict(ns);staticns.update(Path=Path,ROOT=R,PYTHON=Path('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'),ROUTER=R/'ops/ci/w09_formal_router.py',pin=pin)
 static_assign=next(x for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SEALED_STATIC_PATHS' for t in x.targets))
 exec(compile(ast.Module(body=[static_assign,funcs['validate_sealed_static_table']],type_ignores=[]),'<v6-sealed-static-table>','exec'),staticns)
 check('actual_current_static_inputs_equal_sealed_Source',lambda:staticns['validate_sealed_static_table'](actualtable,h['frozen_plan_ref']))
 for relative in ['execution/command_dispatcher/dispatch.py','execution/toolchains/locked.json','execution/v2.4/commands.json']:
  changed=copy.deepcopy(actualtable);changed[str(R/relative).casefold()]['sha256']='b'*64
  check('static_prior_drift_rejected_'+relative,lambda changed=changed:staticns['validate_sealed_static_table'](changed,h['frozen_plan_ref']),'SEALED_STATIC_INPUT_DRIFT')
 contract=json.loads(g.get_buffer(h['root_contract_ref']['path']))
 assert set(contract['scope_exact_keys'])==ns['SCOPE_FIELDS']
 assert contract['future_source_review']['schema']=='researchos.w09-main-c19-two-dispatchers-independent-source-decision.v1'
 obs=json.loads(g.get_buffer(h['original_observations_ref']['path']))
 assert [x['root_ordinal'] for x in obs['observations']]==[987,991]
 assert obs['observations'][0]['truncated_observation_not_full_origin'] is True
 assert obs['observations'][0]['unobserved_stdout_bytes'] is None
 previous_tree=ast.parse(g.get_buffer(previous5['caller_ref']['path']))
 previous_functions={x.name:x for x in previous_tree.body if isinstance(x,ast.FunctionDef)}
 for name in ['validate_scope','validate_source_review','_lease_active','validate_canon_lease','root_request']:
  assert ast.dump(funcs[name],include_attributes=False)==ast.dump(previous_functions[name],include_attributes=False)
  check('v5_unchanged_qualified_gate_'+name,lambda:None)
 # Replay the v5 check-A/use-B counterexample against exact v6 AST statements.
 temporal=dict(ns);temporal.update(PYTHON=MP('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe'),ROUTER=root/'ops/ci/w09_formal_router.py',DISPATCHER=root/'execution/command_dispatcher/dispatch.py')
 exec(compile(ast.Module(body=[static_assign,funcs['validate_sealed_static_table'],funcs['accepted_static_refs'],funcs['merge_source_refs'],funcs['dispatch_revisions']],type_ignores=[]),'<v6-static-A-memory-functions>','exec'),temporal)
 static_paths=temporal['SEALED_STATIC_PATHS']
 table={str(path.resolve()).casefold():fakepin(path) for path in static_paths}
 accepted=temporal['accepted_static_refs'](table,fakepin(static_paths[-1]))
 assert type(accepted) is tuple and len(accepted)==8 and all(accepted[i] is table[str(path.resolve()).casefold()] for i,path in enumerate(static_paths))
 check('exact_eight_original_A_refs_returned',lambda:None)
 temporal['sealed_static']=accepted;temporal['registry_ref']=accepted[0]
 expected_assign=next(n for n in funcs['execute'].body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='expected_dispatch' for t in n.targets))
 refs_assign=next(n for n in funcs['execute'].body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='refs' for t in n.targets))
 sequence_observations=[]
 for label,target in [('dispatcher',static_paths[1]),('toolchain',static_paths[2])]:
  live[str(target)]='b'*64
  exec(compile(ast.Module(body=[expected_assign],type_ignores=[]),'<v6-exact-expectation-A>','exec'),temporal)
  for node in ast.walk(refs_assign):
   if isinstance(node,ast.Name) and isinstance(node.ctx,ast.Load) and node.id not in temporal:
    temporal[node.id]=[] if node.id=='registration_refs' else fakepin('Z:/SYNTHETIC_ONLY/'+node.id)
  temporal.update(expected_report=MP('Z:/SYNTHETIC_ONLY/report.json'),expected_tool=MP('Z:/SYNTHETIC_ONLY/tool.json'),HELPER=MP('Z:/SYNTHETIC_ONLY/helper.py'),GUARD=MP('Z:/SYNTHETIC_ONLY/guard.py'))
  exec(compile(ast.Module(body=[refs_assign],type_ignores=[]),'<v6-exact-held-list-A-plus-B>','exec'),temporal)
  pins=[x for x in temporal['refs'] if isinstance(x,dict) and x.get('path')==str(target)]
  assert {x['sha256'] for x in pins}=={'a'*64,'b'*64}
  assert temporal['expected_dispatch'][label+'_sha256']=='a'*64
  check('v5_postcheck_'+label+'_A_to_B_now_rejected',lambda:temporal['merge_source_refs'](temporal['refs']),'CONFLICTING_PIN')
  sequence_observations.append({'resource':label,'sealed_sha256':'a'*64,'expected_dispatch_sha256':temporal['expected_dispatch'][label+'_sha256'],'held_input_candidates':pins,'merge_observed':'CONFLICTING_PIN','source_AST_executed_only':True,'filesystem_changed':False,'execute_called':False})
  live.pop(str(target))
 for i,path in enumerate(static_paths):
  live[str(path)]='b'*64
  check('every_frozen_resource_late_B_rejected_'+str(i),lambda path=path:temporal['merge_source_refs']([*accepted,fakepin(path)]),'CONFLICTING_PIN')
  live.pop(str(path))
 merged=temporal['merge_source_refs']([*accepted,*accepted])
 assert merged==list(accepted)
 check('unchanged_A_duplicates_preserve_all_eight_refs',lambda:None)
 execute=funcs['execute']
 merged_assignment=next(n for n in execute.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='held_refs' for t in n.targets))
 assert isinstance(merged_assignment.value,ast.Call) and merged_assignment.value.func.id=='merge_source_refs'
 acquisition=[n for n in ast.walk(execute) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='acquire']
 assert len(acquisition)==1 and isinstance(acquisition[0].args[0],ast.Name) and acquisition[0].args[0].id=='held_refs'
 run_calls=[n for n in ast.walk(execute) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='run_owned']
 assert len(run_calls)==1 and merged_assignment.lineno<acquisition[0].lineno<run_calls[0].lineno
 check('same_merged_A_set_reaches_guard_before_run_owned',lambda:None)
 # All otherwise unchanged boundary functions reuse the v4 exact AST review.
 facts={'v4_request_changes_ref':h['v4_review_ref'],'v4_source_decision_ref':prior['source_decision_ref'],'v4_independent_probes_ref':prior_probe,'old_blockers_closed':['C19-V4-01','C19-V4-02','C19-V4-03','C19-V5-01'],'unchanged_function_ast_refs':unchanged,'historical_cp369_archives':archives,'current_stable_static_input_match':True,'remaining_static_hold_continuity_gap':False,'original_observed_diagnostic_ordinals':[987,991],'original_observed_diagnostic_count':2,'original987_full_untruncated_stdout_available':False,'original_diagnostics_not_reconstructed':True,'author_38_controls_used_as_independent_verdict':False,'Native_rerun':False,'dispatcher_executed':False,'Canon_written':False,'Main_Source_written':False}
finally:
 cleanup=g.close()
cr=save('source-guard.closed.json',cleanup)
assert cleanup['verification']=='PASSED' and cleanup['closed'] and cleanup['retained_handles_count']==0 and not cleanup['errors']
pr=save('independent-regression-checks.json',{'schema':'researchos.c19-v5-independent-source-regression-checks.v1','source_ref':h['caller_source_ref'],'checks':checks,'passed':len(checks),'failed':0,'execute_function_called':False,'Native_dispatcher_provider_calls':0})
ar=save('source-analysis.json',facts)
sr=save('independent-sequence-probes.json',{'schema':'researchos.c19-v6-independent-sequence-probes.v1','classification':'INDEPENDENT_SYNTHETIC_MEMORY_ONLY','source_ref':h['caller_source_ref'],'observations':sequence_observations,'Native_dispatcher_execute_called':False})
fr=save('findings.json',{'decision':'ACCEPTED_SOURCE_ONLY','blocking_findings':[],'closed_prior_findings':facts['old_blockers_closed']})
decision={'schema':'researchos.w09-main-c19-two-dispatchers-independent-source-decision.v1','decision':'ACCEPTED_SOURCE_ONLY','actor_id':'codex:/root/native_temp_independent_review','actor_role':'INDEPENDENT_NON_AUTHOR','source_author_id':h['actor'],'source_hdf_ref':pin(S/'HDF.json'),'source_mf_ref':pin(S/'MF.json'),'caller_ref':h['caller_source_ref'],'root_contract_ref':h['root_contract_ref'],'SourceAcceptedonly':True,'noactualorformal':True,'actual_dispatcher_run':False,'formal_acceptance':False,'parent_acceptance':False,'formal_case_accepted_delta':0,'execution_grant':False,'Native_rerun':False,'source_only':True,'findings_ref':fr,'regression_checks_ref':pr,'sequence_probes_ref':sr,'analysis_ref':ar,'guard_cleanup_ref':cr,'held_inputs':len(cleanup['entries']),'all_handles_closed':True,'retained_handles_count':0,'new_original_failures':[],'preserved_original_diagnostics':[987,991],'reviewed_at':datetime.now(timezone.utc).isoformat()}
# Ensure the actual decision fields satisfy the exact candidate review contract.
ns['validate_source_review'](decision,{'source_reviewer':decision['actor_id']},decision['source_hdf_ref'],decision['source_mf_ref'],decision['caller_ref'],decision['root_contract_ref'])
dr=save('source-decision.json',decision)
report='v6 独立源码复审：ACCEPTED_SOURCE_ONLY。\n\nv4 三项阻断与 v5 静态资源连续性阻断均已关闭。八个封存 A refs 返回并进入最终持锁集合，expected_dispatch 只取 A；独立原 AST 时序反例中 dispatcher/toolchain 在后续变成 B 时均触发 CONFLICTING_PIN，在启动前停止。八项晚到 B 和原 A 去重保留也已独立验证。\n\nCanon Owner/Worker 活动租约、独审身份及四个精确 Source refs、Scope 字段和历史版本的反例回归通过。历史 CP369 档案与未来 CP370 当前向量仍分离；固定模式、TEMP/TMP、命令及进程闭合路径沿已核验的不变源码保留。\n\n决定仅接受本次 Source，不构成 CP370 实际登记、dispatcher 执行或正式验收。没有 Native/dispatcher/provider 调用、Source/Main/Canon 修改或新原错误。原 987/991 保留两条 observed-only；未知原始字节不重建。SourceGuard finally closed、retained=0。\n'
with (O/'REPORT.md').open('x',encoding='utf-8',newline='\n') as f:f.write(report)
mf=save('MF.json',{'schema':'researchos.c19-v6-independent-source-review-manifest.v1','members':[dr,fr,pr,sr,ar,cr,pin(O/'REPORT.md'),pin(O/'review_source.py')],'source_hdf_ref':pin(S/'HDF.json'),'source_mf_ref':pin(S/'MF.json')})
hd=save('HDF.json',{'schema':'researchos.c19-v6-independent-source-review-handoff.v1','decision':'ACCEPTED_SOURCE_ONLY','actor_id':decision['actor_id'],'actor_role':decision['actor_role'],'source_hdf_ref':decision['source_hdf_ref'],'source_mf_ref':decision['source_mf_ref'],'caller_ref':decision['caller_ref'],'root_contract_ref':decision['root_contract_ref'],'SourceAcceptedonly':True,'noactualorformal':True,'source_decision_ref':dr,'manifest_ref':mf,'findings_ref':fr,'guard_cleanup_ref':cr,'blocking_findings':0,'closed_prior_findings':facts['old_blockers_closed'],'independent_regression_checks':len(checks),'held_inputs':len(cleanup['entries']),'all_handles_closed':True,'retained_handles_count':0,'actual_dispatcher_run':False,'Native_rerun':False,'formal_acceptance':False,'parent_acceptance':False,'formal_case_accepted_delta':0,'execution_grant':False,'new_original_failures':[],'preserved_original_diagnostics':[987,991],'STOP':True,'FINAL':True})
for ref in read(mf['path'])['members']:assert pin(ref['path'])==ref
print(json.dumps({'HDF':hd,'MF':mf,'decision':dr,'findings':fr,'guard':cr,'held_inputs':len(cleanup['entries']),'independent_checks':len(checks),'blocking_findings':0,'candidate_decision_contract_validated':True},ensure_ascii=False))
