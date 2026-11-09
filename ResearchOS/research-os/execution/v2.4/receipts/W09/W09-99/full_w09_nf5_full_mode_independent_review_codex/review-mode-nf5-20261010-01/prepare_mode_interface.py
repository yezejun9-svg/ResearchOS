"""Read the current Main Mode/role interface. No future qualification is emitted."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,types
R=Path(r'D:\作品集\ResearchOS\research-os');W=R/'execution/v2.4/receipts/W09/W09-99';D=Path(__file__).resolve().parent
p=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/review_support.py';s=types.ModuleType('review_support');s.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),s.__dict__);s.D=D
paths={'closure':R/'ops/ci/w09_evidence_closure.py','router':R/'ops/ci/w09_formal_router.py','profile':R/'execution/v2.4/formal_profile_w09.py','formal_index':R/'execution/v2.4/formal_case_index.py','locked_toolchain':R/'execution/toolchains/locked.json','project_AGENTS':R/'AGENTS.md','prior_readiness':W/'w09_formal_consumer_readiness_readonly_codex/readiness-20261010-01/readiness.json'}
refs={k:s.pin(v) for k,v in paths.items()};g=s.guard();result=None
try:
 g.acquire(list(refs.values()))
 router=ast.parse(g.get_buffer(str(paths['router'])));profile=ast.parse(g.get_buffer(str(paths['profile'])));closure=ast.parse(g.get_buffer(str(paths['closure'])))
 constants={}
 for n in router.body:
  if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('NATIVE','FORMAL','SELECTED','SCOPES'):
   constants[n.targets[0].id]=ast.literal_eval(n.value)
 routes=[]
 for route,ids in constants['NATIVE'].items():
  routes.append(dict(route=list(route),selector=route[2] or route[3],mode='LIVE_WINDOWS' if route[2]=='W09-G02' else 'FIXTURE',native_assertion_ids=list(ids),formal_assertion_ids=list(constants['FORMAL'][route]),selected_tests=list(constants['SELECTED'][route])))
 commands_path=R/'execution/v2.4/commands.json';cm_raw=commands_path.read_bytes();cm=json.loads(cm_raw);cm_ref=dict(path=str(commands_path),sha256=hashlib.sha256(cm_raw).hexdigest(),bytes=len(cm_raw))
 command_shapes={}
 for name in sorted({r['route'][0] for r in routes}):
  value=cm['commands'][name];command_shapes[name]={'keys':list(value),'complete_current_binding':value}
 functions=[]
 for label,tree,names in [('closure',closure,{'verify_mode','verify_native','verify_owned','verify_c19','verify_a06'}),('profile',profile,{'_role_audit','_native','_role_registry','_route_execution_actor'})]:
  text=g.get_buffer(str(paths[label])).decode('utf-8');lines=text.splitlines()
  for n in tree.body:
   if isinstance(n,ast.FunctionDef) and n.name in names:functions.append(dict(module=label,function=n.name,line=n.lineno,end_line=n.end_lineno,source='\n'.join(lines[n.lineno-1:n.end_lineno])))
 assert len(routes)==6 and {r['selector'] for r in routes}=={'W09-G01','W09-G02','C19','A06'} and cm['revision']==40
 result={'schema':'researchos.w09-nf5-mode-independent-review-readiness.v1','status':'OPEN_WAITING_FOUR_CLOSED_NATIVE_AND_INDEPENDENT_FACT_QUALIFICATION','created_utc':datetime.now(timezone.utc).isoformat(),'review_actor_id':'/root/full_w09_source_review','canonical_review_author':'codex:/root/full_w09_source_review','reviewer_thread_id':'01a1215b-7210-7613-b033-756b9d553b83','root_thread_id':'01a11007-5233-7ca1-b71f-9e9e5ce84c98','producer_id':'codex:/root','source_author_expected':'codex:/root/attach_restore_independent_review','current_Main_refs':refs,'commands_ref':cm_ref,'commands_revision':cm['revision'],'routes':routes,'current_command_bindings':command_shapes,'interface_source_excerpts':functions,'independent_review_schema':{'schema':'researchos.w09-independent-mode-review.v1','required_fields':['actor_id','actor_role','producer_id','run_id','report_sha256','source_sha256','go_executable','run_os','run_os_release','decision'],'actor_id':'/root/full_w09_source_review','actor_role':'INDEPENDENT_NON_AUTHOR','decision_emitted':False},'mode_decision_schema':{'schema':'researchos.w09-mode-decision.v2','required_fields':['route','mode','run_id','report_ref','report_sha256','stdout_sha256','source_sha256','go_executable','producer_id','reviewer_id','reviewer_role','decision','independent_review_ref'],'reviewer_id':'/root/full_w09_source_review','issuer_id':'/root/full_w09_source_review','producer_id':'codex:/root','reviewer_role':'INDEPENDENT_NON_AUTHOR','independent_review_ref':'exact repo-relative POSIX path/sha256/int bytes; reviewer namespace is outside the producer report directory','decision_emitted':False},'fixture_specific_fields':['input_origin=OWNED_TEMP_DIR','actual in-process HTTptest delivery events','actual state root beneath the consumer inherited tempfile.gettempdir()'],'live_windows_specific_fields':['locked_go_sha256','host_witness','junction_witness','witness_allowlist exactly these two distinct pins','junction_root_path','junction_target_path','actual Windows11 x64 plus exported Go windows/amd64 branch','actual mklink /J command exit0 and exact raw output pin'],'needed_actual_inputs':['four original NF5 validation.closed.json and native public-index/report/tool refs','Root real prepare/run complete hostpairs with original header/offset/sha/bytes','current source21/compiler resource qualification and closed jobs/guards','Backup independent fact qualification original typed Final/full refs','G02 actual host/junction exported raw member pins','new current consumer/assembler Scope and later real reviewer role peer proof issued by Root separately'],'reuse_policy':'Trust completed Source/NF3/NF5 controls and prior distinct resource proofs; verify exact actual current refs and only new Mode facts. Do not rerun Native, Go, dispatcher, model or Source control suites.','formal_role_identity_gate':{'actual_backend_payload_author_must_equal':'/root/full_w09_source_review','canonical_label_is_metadata_only':True,'metadata_and_Final_must_be_adjacent':True,'current_Main_timestamp_predicate':'metadata.timestamp == Final.timestamp','self_Final_timestamp_relationship_is_not_predicted':True,'actual_role_audit_and_raw_source_readback_required':True},'mode_qualification_emitted':False,'Root_scope_or_lease_issued':False,'actual_products_or_Root_stages_called':0,'formal_acceptance':False,'execution_grant':False}
finally:
 closed=g.close();guard=s.write('mode-interface.guard.closed.json',closed)
 assert closed['verification']=='PASSED' and closed['closed'] is True and closed['retained_handles_count']==0 and not closed['errors']
if result is not None:
 result['guard_ref']=guard;out=s.write('mode-interface.readiness.json',result)
 print(json.dumps(dict(readiness_ref=out,guard_ref=guard,route_count=len(routes),mode_qualification_emitted=False,closed=True,retained_handles_count=0,formal_acceptance=False,execution_grant=False),ensure_ascii=False))
