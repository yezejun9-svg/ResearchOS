from pathlib import Path, PureWindowsPath
from datetime import datetime,timezone
import json,hashlib,ast,types,copy
R=Path('D:/作品集/ResearchOS/research-os')
S=R/'execution/v2.4/receipts/W09/W09-99/w09_main_c19_dispatcher_caller_source_codex/c19call-01a12d10-v5'
O=R/'execution/v2.4/receipts/W09/W09-99/main_c19_dispatcher_caller_independent_review_codex/c19v5-review-20261009'
def pin(p):
 p=Path(p);raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(p):return json.loads(Path(p).read_bytes())
def save(name,data):
 p=O/name
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 return pin(p)
h=read(S/'HDF.json');m=read(S/'MF.json')
assert pin(S/'HDF.json')['sha256']=='f190cd2105fc9d74c953be99e654b487b29047f4cfbf693dd5015e5b3759b204'
assert pin(S/'MF.json')['sha256']=='c271cd4db0324a9e53e37bb82b66daf835b7cfb341235a3bc714dee6594be911'
prior=read(h['v4_review_ref']['path']);prior_m=read(prior['manifest_ref']['path'])
prior_probe=next(x for x in prior_m['members'] if Path(x['path']).name=='independent-memory-probes.json')
inputs=read(m['input_vector_ref']['path']);nh=read(h['native_handoff_ref']['path']);ready=read(nh['prepare_ready_ref']['path']);choice=read(ready['source_choice_ref']['path'])
names=['checkpoint','path_ownership','step_state','commands'];oldpaths={str(R/('execution/v2.4/'+n+'.json')).casefold() for n in names}
refs=[x for x in inputs['refs'] if x['path'].casefold() not in oldpaths]
refs += [pin(S/'HDF.json'),pin(S/'MF.json'),m['input_vector_ref'],h['source_guard_cleanup_ref'],h['original_observations_ref'],h['v4_review_ref'],prior['manifest_ref'],prior['source_decision_ref'],prior['findings_ref'],prior_probe,prior['caller_ref'],nh['prepare_ready_ref'],nh['producer_closed_ref'],nh['native_packet_ref'],ready['source_choice_ref']]
refs += ready['source21'];refs += [x for x in choice['main_seven_after_refs'] if x['path'].casefold() not in oldpaths]
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
 exec(compile(ast.Module(body=[funcs['validate_sealed_static_table']],type_ignores=[]),'<v5-sealed-static-table>','exec'),staticns)
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
 sequence=read(O/'independent-sequence-probe.original-tool-io.json')
 assert sequence['output']['exit_code']==0
 observed=json.loads(sequence['output']['output'])
 assert observed['result']=='SEALED_A_NOT_IN_FINAL_HELD_REFS'
 # All otherwise unchanged boundary functions reuse the v4 exact AST review.
 facts={'v4_request_changes_ref':h['v4_review_ref'],'v4_source_decision_ref':prior['source_decision_ref'],'v4_independent_probes_ref':prior_probe,'old_blockers_closed':['C19-V4-01','C19-V4-02','C19-V4-03'],'unchanged_function_ast_refs':unchanged,'historical_cp369_archives':archives,'current_stable_static_input_match':True,'remaining_static_hold_continuity_gap':True,'original_observed_diagnostic_ordinals':[987,991],'original_observed_diagnostic_count':2,'original987_full_untruncated_stdout_available':False,'original_diagnostics_not_reconstructed':True,'author_36_controls_used_as_independent_verdict':False,'Native_rerun':False,'dispatcher_executed':False,'Canon_written':False,'Main_Source_written':False}
finally:
 cleanup=g.close()
cr=save('source-guard.closed.json',cleanup)
assert cleanup['verification']=='PASSED' and cleanup['closed'] and cleanup['retained_handles_count']==0 and not cleanup['errors']
pr=save('independent-regression-checks.json',{'schema':'researchos.c19-v5-independent-source-regression-checks.v1','source_ref':h['caller_source_ref'],'checks':checks,'passed':len(checks),'failed':0,'execute_function_called':False,'Native_dispatcher_provider_calls':0})
ar=save('source-analysis.json',facts)
finding={'id':'C19-V5-01','priority':1,'file_ref':h['caller_source_ref'],'lines':[337,351],'related_lines':[[506,510],[544,581]],'title':'封存静态资源验证后未以原exact refs持锁，dispatcher/toolchain可在窗口内换成新字节','evidence':'sealed_static_refs validates the eight sealed resource refs but returns only the input-vector file ref. execute then repins dispatcher/toolchain for expected_dispatch and final held refs. The independent source-AST sequence confirms sealed A can pass, followed by a simulated dispatcher change to B, after which both receipt expectation and final held refs contain B and no A resource ref. Holding the vector metadata alone does not hold its members.','fix':'Return the exact eight static resource refs with the vector ref, include all eight in final SourceReadGuard input, and derive expected_dispatch from those accepted refs. Keep conflict detection so any later dynamic pin differing from A fails before launch. Alternatively acquire and validate exact sealed refs before subsequent pin/use. No Main/Canon/Native change required.','probe_ref':pin(O/'independent-sequence-probe.original-tool-io.json'),'scope':'Source logic only; no real file was changed and no dispatcher was executed.'}
fr=save('findings.json',{'decision':'REQUEST_CHANGES','blocking_findings':[finding],'closed_v4_findings':facts['old_blockers_closed']})
decision={'schema':'researchos.w09-main-c19-two-dispatchers-independent-source-decision.v1','decision':'REQUEST_CHANGES','actor_id':'codex:/root/native_temp_independent_review','actor_role':'INDEPENDENT_NON_AUTHOR','source_author_id':h['actor'],'source_hdf_ref':pin(S/'HDF.json'),'source_mf_ref':pin(S/'MF.json'),'caller_ref':h['caller_source_ref'],'root_contract_ref':h['root_contract_ref'],'SourceAcceptedonly':False,'noactualorformal':True,'actual_dispatcher_run':False,'formal_acceptance':False,'parent_acceptance':False,'formal_case_accepted_delta':0,'execution_grant':False,'Native_rerun':False,'source_only':True,'findings_ref':fr,'regression_checks_ref':pr,'analysis_ref':ar,'guard_cleanup_ref':cr,'held_inputs':len(cleanup['entries']),'all_handles_closed':True,'retained_handles_count':0,'new_original_failures':[],'preserved_original_diagnostics':[987,991],'reviewed_at':datetime.now(timezone.utc).isoformat()}
dr=save('source-decision.json',decision)
text='v5 独立源码审查：REQUEST_CHANGES。\n\nv4 三项实际反例均已关闭：Canon 实际登记与活动租约、精确独审绑定、Scope 精确字段集合。独立全 root_request 内存正例和针对性反例通过，当前静态输入与封存表也相符。\n\n仍有一个连续性阻断：sealed_static_refs 只返回表文件 ref，未把表内八个已封存资源 ref 放入最终 SourceReadGuard。dispatcher/toolchain 在验证后又重新 pin，独立 AST 时序反例证明 A 检查通过后可把 B 当成实际期望和持锁输入。应返回并持有八个原 exact refs，expected_dispatch 直接从它们取值；后续漂移须在启动前失败。\n\n原诊断 987/991 共两条保持 observed-only，987 不完整 stdout 未重建。没有新增原工具失败，没有 Native/dispatcher/provider 执行，没有 Source/Main/Canon 修改。SourceGuard finally closed、retained=0，正式验收增量 0。\n'
with (O/'REPORT.md').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
mf=save('MF.json',{'schema':'researchos.c19-v5-independent-source-review-manifest.v1','members':[dr,fr,pr,ar,cr,pin(O/'REPORT.md'),pin(O/'review_source.py'),pin(O/'independent-sequence-probe.original-tool-io.json')],'source_hdf_ref':pin(S/'HDF.json'),'source_mf_ref':pin(S/'MF.json')})
hd=save('HDF.json',{'schema':'researchos.c19-v5-independent-source-review-handoff.v1','decision':'REQUEST_CHANGES','actor_id':decision['actor_id'],'actor_role':decision['actor_role'],'source_hdf_ref':decision['source_hdf_ref'],'source_mf_ref':decision['source_mf_ref'],'caller_ref':decision['caller_ref'],'root_contract_ref':decision['root_contract_ref'],'SourceAcceptedonly':False,'noactualorformal':True,'source_decision_ref':dr,'manifest_ref':mf,'findings_ref':fr,'guard_cleanup_ref':cr,'blocking_findings':1,'v4_closed_findings':facts['old_blockers_closed'],'independent_regression_checks':len(checks),'held_inputs':len(cleanup['entries']),'all_handles_closed':True,'retained_handles_count':0,'formal_acceptance':False,'parent_acceptance':False,'formal_case_accepted_delta':0,'execution_grant':False,'new_original_failures':[],'preserved_original_diagnostics':[987,991],'STOP':True,'FINAL':True})
for ref in read(mf['path'])['members']:assert pin(ref['path'])==ref
print(json.dumps({'HDF':hd,'MF':mf,'decision':dr,'findings':fr,'guard':cr,'held_inputs':len(cleanup['entries']),'independent_checks':len(checks),'blocking_findings':1},ensure_ascii=False))

