from pathlib import Path, PureWindowsPath
import json,hashlib,ast,types,datetime,copy
R=Path('D:/作品集/ResearchOS/research-os')
S=R/'execution/v2.4/receipts/W09/W09-99/w09_main_c19_dispatcher_caller_source_codex/c19call-01a12d10-v4'
O=R/'execution/v2.4/receipts/W09/W09-99/main_c19_dispatcher_caller_independent_review_codex/c19v4-review-20261009'
def pin(p):
 p=Path(p);raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(p):return json.loads(Path(p).read_bytes())
def save(name,data):
 p=O/name
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 return pin(p)
h=read(S/'HDF.json');m=read(S/'MF.json')
assert pin(S/'HDF.json')['sha256']=='ba0714afe290547830a7434ad6e86cc14561ca384ad80dca1e8aee8bf8e47a29'
assert pin(S/'MF.json')['sha256']=='5578a2d9106bb19bcfafa7417a120cfb03d187ecde52363239b8cb6198ae5749'
inputs=read(m['input_vector_ref']['path'])
nh=read(h['native_handoff_ref']['path']);ready=read(nh['prepare_ready_ref']['path'])
choice=read(ready['source_choice_ref']['path'])
names=['checkpoint','path_ownership','step_state','commands']
oldpaths={str(R/('execution/v2.4/'+n+'.json')).casefold() for n in names}
refs=[x for x in inputs['refs'] if x['path'].casefold() not in oldpaths]
refs += [pin(S/'HDF.json'),pin(S/'MF.json'),m['input_vector_ref'],h['source_guard_cleanup_ref'],nh['prepare_ready_ref'],nh['producer_closed_ref'],nh['native_packet_ref'],ready['source_choice_ref']]
refs += ready['source21']
refs += [x for x in choice['main_seven_after_refs'] if x['path'].casefold() not in oldpaths]
archives=[]
for n,old in zip(names,ready['canonical_vector']['refs']):
 ar=pin(Path(h['native_handoff_ref']['path']).parent/('historical.cp369.'+n+'.json'))
 assert ar['sha256']==old['sha256'] and ar['bytes']==old['bytes']
 archives.append(ar);refs.append(ar)
guardref=next(x for x in refs if Path(x['path']).name=='source_read_guard.py')
guardraw=Path(guardref['path']).read_bytes()
assert hashlib.sha256(guardraw).hexdigest()==guardref['sha256']
gm=types.ModuleType('independent_guard');exec(compile(guardraw,guardref['path'],'exec'),gm.__dict__)
g=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
g.acquire(refs)
probes=[];checks=[];coverage={}
try:
 src=g.get_buffer(h['caller_source_ref']['path']).decode()
 tree=ast.parse(src);funcs={x.name:x for x in tree.body if isinstance(x,ast.FunctionDef)}
 # Execute only these dependency-free function ASTs against an in-memory filesystem.
 selected=[funcs[x] for x in ['require','source_ref','root_request','strict_pass']]
 ns={'__file__':h['caller_source_ref']['path']}
 exec(compile(ast.Module(body=selected,type_ignores=[]),'<independent-memory-only-selected-functions>','exec'),ns)
 class MP(PureWindowsPath):
  def resolve(self,*a,**kw):return self
  def is_relative_to(self,p):return PureWindowsPath(self).is_relative_to(p)
  def exists(self):return False
  def read_bytes(self):return json.dumps(fs[str(self)],ensure_ascii=False).encode()
 ROOT=MP(str(R));ns.update(ROOT=ROOT,Path=MP,ROUTES=('test.research.fixture','test.retrieval'),SOURCE_ACTOR='codex:/root/w09_formal_profile_source_impl')
 def fakepin(p):return {'path':str(MP(p)),'sha256':'a'*64,'bytes':1}
 docs={};fs={}
 def add(name,doc):
  ref=fakepin(MP('Z:/SYNTHETIC_ONLY')/name);docs[ref['path']]=doc;return ref
 callerref=fakepin(ns['__file__'])
 mfref=add('MF.json',{'schema':'researchos.w09-c19-two-consumer-source-manifest.v1','caller_source_ref':callerref})
 hdfref=add('HDF.json',{'status':'SOURCE_ONLY_PENDING_ROOT_REGISTRATION','caller_source_ref':callerref,'manifest_ref':mfref})
 reviewref=add('review.json',{'reviewer_id':'codex:/independent-mock','decision':'ACCEPTED_SOURCE_ONLY','formal_acceptance':False})
 scope={'issued_by':'codex:/root','formal_dispatcher':True,'formal_acceptance':False,'parent_acceptance':False,'formal_case_accepted_delta':0,'expected_checkpoint_revision':370,'expected_path_ownership_revision':174,'expected_previous_checkpoint_revision':369,'routes':list(ns['ROUTES']),'source_actor':ns['SOURCE_ACTOR'],'source_reviewer':'codex:/different-independent-mock','source_hdf_ref':hdfref,'source_review_ref':reviewref}
 scoperef=add('scope-registration.root.json',scope)
 canonical=[ROOT/'execution/v2.4'/(n+'.json') for n in names]
 cp={'revision':370,'expected_previous_revision':369,'work_in_progress':{'w09_c19_two_dispatcher_scope_ref':scoperef},'workers':[]}
 ow={'revision':174,'card_path_bindings':[],'path_lease_transfers':[]}
 fs[str(canonical[0])]=cp;fs[str(canonical[1])]=ow
 vectorref=add('vector.json',{'schema':'researchos.w09-c19-consumer-current-canonical-vector.v1','checkpoint_revision':370,'path_ownership_revision':174,'refs':[fakepin(p) for p in canonical]})
 proofref=add('proof.json',{'issued_by':'codex:/root','scope_ref':scoperef,'current_canonical_vector_ref':vectorref,'previous_checkpoint_revision':369,'registered_checkpoint_revision':370})
 ownerref=add('owner.json',{'scope_ref':scoperef,'owner_id':'codex:/root','selected_worker_id':'codex:/root','lease_state':'EXPIRED'})
 workerref=add('worker.json',{'scope_ref':scoperef,'worker_id':'codex:/root','selected_owner_ref':ownerref,'lease_state':'EXPIRED'})
 req={'schema':'researchos.w09-c19-two-dispatcher-root-request.v1','issued_by':'codex:/root','formal_acceptance':False,'native_producer_rerun':False,'registry_writes':False,'canonical_writes':False,'go_provider_calls':False,'exact_routes':list(ns['ROUTES']),'scope_ref':scoperef,'source_hdf_ref':hdfref,'source_review_ref':reviewref,'current_canonical_vector_ref':vectorref,'actual_registration_proof_ref':proofref,'current_owner_ref':ownerref,'current_worker_ref':workerref,'output_dir':str(ROOT/'execution/v2.4/receipts/W09/W09-99/SYNTHETIC_NOT_CREATED')}
 ns['pin']=fakepin;ns['strict_json']=json.loads;ns['checked']=lambda ref:(docs[ref['path']],ref)
 ns['root_request'](req)
 probes.append({'name':'absent_canonical_workers_leases_and_expired_standalone_documents','observed':'ACCEPTED_BY_ROOT_REQUEST','expected':'REJECT','synthetic_memory_only':True,'cp_workers':cp['workers'],'ow_card_path_bindings':ow['card_path_bindings'],'ow_path_lease_transfers':ow['path_lease_transfers'],'source_lines':[123,152]})
 probes.append({'name':'unbound_review_missing_schema_role_and_all_source_refs_with_mismatched_scope_reviewer','observed':'ACCEPTED_BY_ROOT_REQUEST','expected':'REJECT','synthetic_memory_only':True,'review':copy.deepcopy(docs[reviewref['path']]),'scope_source_reviewer':scope['source_reviewer'],'source_lines':[109,122]})
 cp['workers']=[{'worker_id':'unrelated-active-worker','status':'ACTIVE'},{'worker_id':'unrelated-active-worker','status':'ACTIVE'}]
 ow['card_path_bindings']=[{'owner':'other','status':'ACTIVE'},{'owner':'other','status':'ACTIVE'}]
 ns['root_request'](req)
 probes.append({'name':'conflicting_duplicate_canonical_workers_and_owners','observed':'ACCEPTED_BY_ROOT_REQUEST','expected':'REJECT','synthetic_memory_only':True})
 scope['current_canonical_vector_ref']=vectorref;scope['future_request_sha256']='b'*64
 ns['root_request'](req)
 probes.append({'name':'scope_contains_forbidden_future_vector_and_request_fields','observed':'ACCEPTED_BY_ROOT_REQUEST','expected':'REJECT_BY_CYCLE_CONTRACT','synthetic_memory_only':True})
 del scope['current_canonical_vector_ref'];del scope['future_request_sha256']
 docs[reviewref['path']]={'schema':'researchos.independent-source-review.v1','decision':'ACCEPTED_SOURCE_ONLY','actor_id':'codex:/independent-mock','actor_role':'INDEPENDENT_NON_AUTHOR','source_hdf_ref':hdfref,'source_mf_ref':mfref,'caller_ref':callerref,'root_contract_ref':fakepin('Z:/SYNTHETIC_ONLY/contract.json'),'SourceAcceptedonly':True,'noactualorformal':True,'formal_acceptance':False}
 try:ns['root_request'](req)
 except ValueError as e:
  assert str(e)=='SOURCE_NOT_INDEPENDENTLY_ACCEPTED'
  probes.append({'name':'requested_actor_id_decision_contract_without_reviewer_id_alias','observed':str(e),'expected':'ACTOR_CONTRACT_SHOULD_BE_SUPPORTED_AND_EXACTLY_BOUND','synthetic_memory_only':True})
 else:raise AssertionError('actor contract mismatch probe unexpected')
 res={'actual_exit':0,'timed_out':False,'error':None,'owned_child_pid':12345,'creation_time_100ns':134039000000000001,'job_cleanup':{'unnamed_exclusive_job':True,'kill_on_job_close_configured':True,'assigned_before_resume':True,'primary_exit_confirmed':True,'job_idle_confirmed':True,'active_processes_last_observed':0,'handles_closed':True,'errors':[]}}
 expected={'registry_sha256':'a'*64,'dispatcher_sha256':'b'*64,'toolchain_sha256':'c'*64,'router_sha256':'d'*64}
 receipt={'status':'PASS','exit_code':0,'child_exit_code':0,'command_key':'test.research.fixture','selectors':{'task_id':'W09','check_id':'','case_id':'C19'},'registry_spec':'v2.4','assertion_ids':['C19-01','C19-02','C19-03'],'registered_command_revision':'a'*64,'dispatcher_sha256':'b'*64,'toolchain_revision':'c'*64,'input_versions':[{'path':'ops/ci/w09_formal_router.py','sha256':'d'*64}]}
 ns['strict_pass'](res,receipt,'test.research.fixture',expected)
 probes.append({'name':'FILETIME_above_JS_safe_integer_preserved_in_Python','observed':res['creation_time_100ns'],'expected':134039000000000001,'pass':True,'synthetic_memory_only':True})
 for name,mutation,code in [
  ('bool_child_exit',lambda r,t:t.update(child_exit_code=False),'DISPATCH_RECEIPT_NOT_PASS'),
  ('unknown_child_exit',lambda r,t:t.update(child_exit_code=None),'DISPATCH_RECEIPT_NOT_PASS'),
  ('live_descendant',lambda r,t:r['job_cleanup'].update(active_processes_last_observed=1),'OWNED_DESCENDANTS_NOT_CLOSED'),
  ('unknown_creation_FILETIME',lambda r,t:r.update(creation_time_100ns=None),'PRIMARY_IDENTITY_UNKNOWN')]:
  rr=copy.deepcopy(res);tt=copy.deepcopy(receipt);mutation(rr,tt)
  try:ns['strict_pass'](rr,tt,'test.research.fixture',expected)
  except ValueError as e:assert str(e)==code;probes.append({'name':name,'observed':str(e),'expected':code,'pass':True,'synthetic_memory_only':True})
  else:raise AssertionError(name+' accepted')
 for name in ['root_request','historical_archive_bindings','qualified_modes','packet_inventory','strict_pass','execute']:
  node=funcs[name];checks.append({'function':name,'start':node.lineno,'end':node.end_lineno,'ast_sha256':hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest()})
 # Source-only facts from exact immutable Native documents; no Native execution.
 src21=ready['source21'];assert len(src21)==21
 for ref in src21:assert hashlib.sha256(g.get_buffer(ref['path'])).hexdigest()==ref['sha256']
 sixmain=[x for x in choice['main_seven_after_refs'] if x['path'].casefold() not in oldpaths]
 assert len(sixmain)==6 and all(x in src21 for x in sixmain)
 coverage={'source21_count':21,'main_seven_six_source_members_are_source21':True,'main_seven_registry_is_historical_commands':choice['main_seven_after_refs'][-1],'historical_archive_refs':archives,'historical_archives_match_native_cp369_bytes':True,'source_main_writes':False,'source_canonical_writes':False,'source_import_spawns_process':False,'root_request_requires_actual_CP370_WIP_scope':True,'actual_canonical_owner_worker_uniqueness_checked':False,'separate_registration_proof_and_current_vector':True,'one_way_owner_worker_reference':True,'actual_native_run_id_fixed':'9e912dfc1058454da08ae7f93f4de24d','MR2_hdf_exact_sha_enforced':True,'native_handoff_request_exact_sha_enforced':True,'two_mode_decisions_distinct':True,'TEMP_TMP_exact':True,'frozen_no_spec_argv':True,'auto_v24_pointer_and_plan_hash':True,'raw_inventory_all_files_no_suffix_filter':True,'original_and_archive_members_unique_casefolded':True,'symlink_check_and_held_guard_final_path_check':True,'two_sequential_owned_jobs_first_failure_stops':True,'outer_primary_FILETIME_remains_Python_int':True,'unobserved_descendant_identity_null':True,'dispatcher_receipt_checks_registry_dispatcher_toolchain_router_and_child_exit':True,'formal_acceptance':False,'author_controls_used_as_independent_verdict':False}
finally:
 closed=g.close()
cr=save('source-guard.closed.json',closed)
assert closed['verification']=='PASSED' and closed['closed'] and closed['retained_handles_count']==0 and closed['errors']==[]
findings=[
 {'id':'C19-V4-01','priority':1,'title':'Canon实际Owner/Worker租约未核验','file_ref':h['caller_source_ref'],'lines':[123,152],'evidence':'Current Canon is checked for revision and one WIP scope link, but OW binding/lease records and CP workers are never inspected. Standalone Owner/Worker refs can satisfy the gate even when Canon has no registrations, duplicate conflicting workers, or documents marked expired.','fix':'Bind and validate exact active Canon Owner lease and CP Worker records for the scope, task, route/output path and actor, including uniqueness and no conflicting active ownership. Retain Owner.selected_worker_id -> Worker.selected_owner_ref acyclic order.','counterexamples':['absent_canonical_workers_leases_and_expired_standalone_documents','conflicting_duplicate_canonical_workers_and_owners']},
 {'id':'C19-V4-02','priority':1,'title':'独审决定未与本次Source四个精确ref及身份闭合','file_ref':h['caller_source_ref'],'lines':[109,122],'evidence':'The review gate reads reviewer_id/decision/formal_acceptance only. It neither validates schema/actor_role nor requires reviewer equality with scope.source_reviewer nor binds source_hdf_ref/source_mf_ref/caller_ref/root_contract_ref. The requested actor_id decision schema without legacy reviewer_id is rejected, while a three-field unrelated review is accepted.','fix':'Specify a single independent decision schema and consume actor_id/actor_role plus SourceAcceptedonly/noactualorformal; require non-author identity equality across scope and decision, and exact HDF/MF/caller/root-contract refs. Include the root contract in held refs and reconcile it with HDF/MF, rather than only checking caller bytes.','counterexamples':['unbound_review_missing_schema_role_and_all_source_refs_with_mismatched_scope_reviewer','requested_actor_id_decision_contract_without_reviewer_id_alias']},
 {'id':'C19-V4-03','priority':2,'title':'Scope禁止未来vector/request字段只写在合同中','file_ref':h['caller_source_ref'],'lines':[100,110],'evidence':'root_request accepts additional scope.current_canonical_vector_ref and scope.future_request_sha256 fields although contract line29 explicitly excludes current CP370 vector/proof/future request to avoid a reference cycle. before_canonical_revisions is also not checked.','fix':'Enforce a precise Scope schema or reject forbidden forward-reference fields and validate historical revision declarations. Keep actual_registration_proof_ref and current vector exclusively in the post-registration request.','counterexamples':['scope_contains_forbidden_future_vector_and_request_fields']}
]
pr=save('independent-memory-probes.json',{'schema':'researchos.c19-v4-independent-memory-probes.v1','source_ref':h['caller_source_ref'],'classification':'INDEPENDENT_SYNTHETIC_LOGIC_PROBES_NOT_ACTUAL_AUTHORITY','execute_function_called':False,'native_processes':0,'dispatcher_processes':0,'provider_calls':0,'probes':probes})
fr=save('findings.json',{'decision':'REQUEST_CHANGES','blocking_findings':findings})
ar=save('source-analysis.json',{'source_ref':h['caller_source_ref'],'function_ast_checks':checks,'coverage':coverage,'qualification_limits':['No future Root request or CP370 registration was created or accepted.','The 17 author synthetic controls were inspected only and not treated as independent evidence.','This review does not rerun Native producer, dispatcher consumers or prior full actual inventory review.','Main source21 and six adopted source files are pinned by runtime Native ready traversal; current CM39 is separately current-vector guarded. Revised caller should explicitly reconcile its current registry and dispatcher/toolchain pins with accepted Source inputs when claiming accepted-input continuity.'],'all_previous_source_namespaces_untouched':True,'inverse':'All reviewer writes are confined to this new review namespace; no existing Source/Main/Canon bytes changed.'})
decision={'schema':'researchos.w09-c19-two-consumer-independent-source-decision.v1','decision':'REQUEST_CHANGES','actor_id':'codex:/root/native_temp_independent_review','actor_role':'INDEPENDENT_NON_AUTHOR','source_author_id':h['actor'],'source_hdf_ref':pin(S/'HDF.json'),'source_mf_ref':pin(S/'MF.json'),'caller_ref':h['caller_source_ref'],'root_contract_ref':h['root_contract_ref'],'SourceAcceptedonly':False,'noactualorformal':True,'formal_acceptance':False,'parent_acceptance':False,'formal_case_accepted_delta':0,'execution_grant':False,'source_only':True,'actual_dispatcher_run':False,'Native_rerun':False,'findings_ref':fr,'independent_probes_ref':pr,'source_analysis_ref':ar,'guard_cleanup_ref':cr,'held_inputs':len(closed['entries']),'all_handles_closed':True,'retained_handles_count':0,'new_original_failures':[],'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
dr=save('source-decision.json',decision)
report='v4 独立源码审查：REQUEST_CHANGES，尚不能用于 CP370 后的实际调用。\n\n1. Canon 的实际 Owner/Worker/lease 唯一登记未检查；空登记、冲突登记和过期独立文档均可通过 root_request。\n2. 独审决定缺少 schema/actor_role/源 HDF、MF、caller、contract 精确绑定，scope reviewer 与 decision reviewer 也未一致核验；actor_id 合同与 reviewer_id 实现不一致。\n3. Scope 禁止未来 vector/request/proof 引用的循环约束仅为合同文字，当前实现接收这些额外字段。\n\n历史 CP369 四档案与 Native 原 hash/bytes 相符；Main source21 与六个已采用源码成员已验证，其他通过项及当前 registry 连续性限制见 source-analysis.json。独立反例只在内存中调用 AST 提取的纯函数，不构造实际授权、不执行 execute，不运行 Native/dispatcher/provider。SourceGuard closed、retained=0。正式验收增量 0；原 Source v1–v4 均未改动。\n'
with (O/'REPORT.md').open('x',encoding='utf-8',newline='\n') as f:f.write(report)
mf=save('MF.json',{'schema':'researchos.c19-v4-independent-source-review-manifest.v1','members':[dr,fr,pr,ar,cr,pin(O/'REPORT.md'),pin(O/'review_source.py')],'source_hdf_ref':pin(S/'HDF.json'),'source_mf_ref':pin(S/'MF.json')})
hd=save('HDF.json',{'schema':'researchos.c19-v4-independent-source-review-handoff.v1','decision':'REQUEST_CHANGES','actor_id':decision['actor_id'],'actor_role':decision['actor_role'],'source_hdf_ref':decision['source_hdf_ref'],'source_mf_ref':decision['source_mf_ref'],'caller_ref':decision['caller_ref'],'root_contract_ref':decision['root_contract_ref'],'SourceAcceptedonly':False,'noactualorformal':True,'source_decision_ref':dr,'manifest_ref':mf,'findings_ref':fr,'guard_cleanup_ref':cr,'blocking_findings':len(findings),'held_inputs':len(closed['entries']),'all_handles_closed':True,'retained_handles_count':0,'formal_acceptance':False,'parent_acceptance':False,'formal_case_accepted_delta':0,'execution_grant':False,'new_original_failures':[],'STOP':True,'FINAL':True})
for ref in read(mf['path'])['members']:assert pin(ref['path'])==ref
print(json.dumps({'HDF':hd,'MF':mf,'decision':dr,'findings':fr,'probes':pr,'guard':cr,'held_inputs':len(closed['entries']),'blocking_findings':len(findings)},ensure_ascii=False))

