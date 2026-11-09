import hashlib
import json
from pathlib import Path
import subprocess
import sys
if sys.flags.optimize != 0: raise RuntimeError('Optimized Python prohibited')
ROOT=Path.cwd().resolve();OUT=Path(__file__).resolve().parent;BASE=ROOT/'execution/v2.4';R=BASE/'receipts/W05/W05-99';READS={}
CANON=[BASE/n for n in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']]
def ref(path,expected=None):
 p=Path(path);p=p if p.is_absolute() else ROOT/p;p=p.resolve();assert p.is_relative_to(ROOT)
 raw=p.read_bytes();sha=hashlib.sha256(raw).hexdigest();assert expected is None or sha==expected,str(p)
 if p in READS:assert READS[p]==raw
 READS[p]=raw;return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha,'bytes':len(raw)}
def read(path):
 row=ref(path);return READS[ROOT/row['path']]
def save(name,obj):
 with (OUT/name).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
 return ref(OUT/name)
def collect(obj,base=ROOT):
 if isinstance(obj,dict):
  if isinstance(obj.get('path'),str) and isinstance(obj.get('sha256'),str) and len(obj['sha256'])==64:
   p=Path(obj['path']);p=p if p.is_absolute() else base/p;v=ref(p,obj['sha256']);assert 'bytes' not in obj or v['bytes']==obj['bytes']
  else:
   for v in obj.values():collect(v,base)
 elif isinstance(obj,list):
  for v in obj:collect(v,base)
lock=json.loads(read(ROOT/'execution/toolchains/locked.json'))['tools'];git=lock['git']['path']
assert Path(sys.executable).resolve()==Path(lock['python']['path']).resolve() and hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest()==lock['python']['sha256'];assert hashlib.sha256(Path(git).read_bytes()).hexdigest()==lock['git']['sha256']
before=[ref(p) for p in CANON];assert [v['sha256'] for v in before]==['586d88ba0bfee13778f9a8968ac39e5f6f4120557ce46477c0012c27aac63d85','97dccd1403612c6751f4018f514dc12ece9bcc2a4ba59d3aac61e1398221fb27','fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149','b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129']
cp,ow=[json.loads(read(p)) for p in CANON[:2]];assert [cp['revision'],ow['revision'],len(cp['failure_counters'])]==[305,133,348]
head=subprocess.check_output([git,'rev-parse','HEAD'],cwd=ROOT).decode().strip();status=subprocess.check_output([git,'status','--porcelain=v1','--untracked-files=no'],cwd=ROOT);assert head==cp['head']=='2cdb0d43d5a600eef13c8f1735946a9adf52d079' and hashlib.sha256(status).hexdigest()=='e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
handler=R/'handler38_independent_replay_codex/c09-attach-correction-r304-0acd8177a821441395e8902ba16def0c';listreview=R/'session_list_identity_contract_independent_review_codex/ac4d06bc817e49afbaa4cf0c29274113';proposal=R/'session_list_identity_fix_scope_codex/cb78a3d4ca0c444bb170527667bf9afc';review=R/'session_list_identity_fix_scope_independent_review_codex/0107b7eea38b4c8ea6af0c1ce7b39cca';lease=R/'attach_lease_producer_scope_independent_review_codex/0303da054a7b449689f84aed9a043b04';sr=ROOT/'.local/worktrees/codex-w0599-cli-contract-repair-r303';sn=sr/'execution/v2.4/receipts/W05/W05-99/cli_protocol_exact8_executor_codex/32000aadb56142468ad17096b4d18953'
pins={
 'previous_handoff':ref(R/'integration_codex/cli-created-owner-amendment-r305/handoff-r305-running.json','e8063718be66b788a066cc44f10e800f9bb7bf3f6a3087107394adb94bdb3d34'),
 'handler_final_review':ref(handler/'source_review.json','7fdf7f2ced5d29adb4ba7c8e420e0d0235c74f7227fe500fa7a1d547f9958680'),
 'handler_manifest':ref(handler/'manifest.json','3a0b905af7e5eea89653ca609ae9bf5bfc83b8f88baa93f2bd10ce7f97f29748'),
 'handler_handoff':ref(handler/'handoff.json','40672e45344323fa3b0b4beca2a143d4760416ba37dc54df8ab540a288c49917'),
 'handler_final_failure':ref(handler/'failure_origins.json','2fe27767a608f3360a06046f66fa7de378958e84dfec449510c4967d21a169fd'),
 'list_adverse_nonauthor_review':ref(listreview/'review.json','fd5d40e2e4dc95a7ee34faf7a5db993364cfdbba8afaf4b441a61791832b41de'),
 'list_adverse_manifest':ref(listreview/'manifest.json','51b7f3ecd1f4d712667d77acae991daf7105f6e1a4eb86514b9e4d975a77d3d2'),
 'lease_revision_correction':ref(listreview/'lease_revision_correction.json','0a69cdd53225dc462cd86ae72612cd1b9b8adfa4b8e2cdc803424b0e5bac49ab'),
 'lease_original_proposal':ref(lease/'scope_proposal.json','eb789dcde14ffa0ac00514c061d1e743a1205cea7f68c3703dae328fb43f81b4'),
 'lease_manifest':ref(lease/'manifest.json','9d3ca6a8cec88e2b44fc0e6876977eb481337cc7adf52d0dc267364f10feb585'),
 'lease_diagnostics':ref(lease/'tool_diagnostics.json','1861df807a04dd16500d31161dba748c9df5fc2ac2442798c909a3173757023b'),
 'list_fix_proposal':ref(proposal/'scope_proposal.json','bc3512a43e0fb31118eea7e4b5233350e9ab06401391aaf2add1ebd7bd86e5d7'),
 'list_fix_manifest':ref(proposal/'manifest.json','fcc633e069de8d58b6880f09fcec8ee5aacfec5502bbbb5d0f709de4fb916bde'),
 'list_fix_handoff':ref(proposal/'handoff.json','7a2fd09380441ca7e95f292e148bbcca83d66100fee61ccfdbf6fb8271b3c1ab'),
 'list_fix_scope_review':ref(review/'scope_review.json','4b9b24563f575b19856a18c3877f2dcbdd0c081078ed774ce191f8ce9a9b4f61'),
 'list_fix_conditions':ref(review/'conditions.json','1340d57a0ed0f99f9a9997c31ff9a8c5b762210cc8dca4a80b744f23b1acca53'),
 'list_fix_review_manifest':ref(review/'manifest.json','731cf75e6daa8952d47397054b759827fbf4a05329df617fd824ab112f13eff0'),
 'protected_resources':ref(R/'integration_codex/handler38-main-integration-resources-r305/protected.before.json','9fc873ba22e42246466e1e499076c4959ca95e804e58f2445833267239261269'),
 'root_resume_findings':ref(R/'integration_codex/pause-resume-readonly-continuation-r305/findings.json','41cfa2b422f535fd0e4ca1aadeea636e8a87b78766f25c92802161b1cb279a13'),
 'root_resume_manifest':ref(R/'integration_codex/pause-resume-readonly-continuation-r305/manifest.json','f40ab565173c33167cbd44f9a44f9ca0fc8f893dadb04d6054a7fb3412577417'),
 'root_resume_failure':ref(R/'integration_codex/pause-resume-readonly-continuation-r305/tool_failure_origin.json','f6c68ed64b871e7965264f67a5835c714baac433f8ee070a232cfff0507438f6'),
 'unused_main_integration_executor':ref(OUT/'integrate_main.py','9271e9438a0de8fb6fb799792d8fef3b400a242c0dec108a94201a57d4e029af')}
manifest_audit=[]
for key in ['handler_manifest','list_adverse_manifest','lease_manifest','list_fix_manifest','list_fix_review_manifest','root_resume_manifest']:
 p=ROOT/pins[key]['path'];obj=json.loads(read(p));rows=obj.get('entries',obj.get('files'));assert isinstance(rows,list)
 for row in rows:
  target=Path(row['path']);target=target if target.is_absolute() else (ROOT/target if row['path'].startswith('execution/') else p.parent/target);actual=ref(target,row['sha256']);assert 'bytes' not in row or actual['bytes']==row['bytes']
 manifest_audit.append({'name':key,'listed':len(rows),'bad':0,'ref':pins[key]})
assert manifest_audit[0]['listed']==169
hf=json.loads(read(pins['handler_final_review']['path']));assert hf['decision']=='SOURCE_READY_HANDLER38_WITH_DECLARED_OPEN_PRODUCT_GATES';collect(hf)
lr=json.loads(read(pins['list_adverse_nonauthor_review']['path']));assert lr['decision']=='CONFIRMED_RESPONSE_IDENTITY_BOUNDARY_DEFECT_MAIN_INTEGRATION_HOLD'
reviewobj=json.loads(read(pins['list_fix_scope_review']['path']));assert reviewobj['decision']=='SOURCE_SCOPE_READY_WITH_MANDATORY_WIRE_CLASSIFICATION'
pp=json.loads(read(pins['list_fix_proposal']['path']));cond=json.loads(read(pins['list_fix_conditions']['path']))
ph=json.loads(read(pins['list_fix_handoff']['path']));collect(ph)
resources=json.loads(read(pins['protected_resources']['path']));assert resources['count']==35784 and resources['bytes']==746008339 and resources['new_original_inputs_without_AE_reference']==0
source_refs=[];origins=[]
def addorigin(actor,key,outer,native,kind,reason,evidence,original):
 origins.append({'origin_key':key,'actor':actor,'actual_outer_exit_code':outer,'actual_native_exit_code':native,'kind':kind,'reason':reason,'evidence_ref':evidence,'source_origin':original})
for name,sha in [('r305-first-failure','e01b53e84bc862703c616f9ac6bae79bf68944c938761eacc20b82258aa8a8c9'),('r305-second-failure','c197690f827d09f62216cb8ab75cbe0ebe4c8596d91d12cf41634050b49d2572'),('r305-read-atomic-failure','bdc45baceaee88ca2a70f47260ea90257c0d9a7456da6b7fa1ea42b665da42f4'),('r305-read-config-failure','afc0a3f16d1f76eb673b14797fd4dab61a25dbdbef2cead79e16585f5b5fe06c'),('r305-admitted-disconnect-failure','2bd625eda2392e581ccb56b64abb74dafe35740eed5e80e2727e59bed170250d')]:
 pinrow=ref(sn/name/'handoff.json',sha);pins['CLI_'+name]=pinrow;source_refs.append(pinrow);x=json.loads(read(pinrow['path']));collect(x,sr)
 rows=x.get('origins',[x])
 for row in rows:
  outer=row['outer_exit'];native=row.get('native_exit',row.get('native_test_exit'));assert outer==1 and native in [None,1]
  addorigin('codex:/root/sources_parent_impl','cli-r305-'+row['tool_chunk'],outer,native,row.get('kind','TEST_BATCH'),row['cause'],pinrow,row)
assert len(origins)==9
f=json.loads(read(pins['handler_final_failure']['path']))
for row in f['new_origins']:
 assert row['actual_outer_exit']==1
 addorigin('codex:/root/w05_merge_review','handler38-final-'+row['origin'],1,None,row['kind'],row.get('error',row.get('action')),pins['handler_final_failure'],row)
ld=json.loads(read(pins['lease_diagnostics']['path']));assert len(ld['new_failure_origins'])==1 and ld['non_failure_diagnostics'][0]['actual_outer_exit']==0
row=ld['new_failure_origins'][0];addorigin('codex:/root/w05_merge_review','lease-scope-'+row['origin'],row['actual_outer_exit'],None,'READONLY_TOOL_LOCATOR',row['cause'],pins['lease_diagnostics'],row)
row=json.loads(read(pins['root_resume_failure']['path']));addorigin('codex:/root',row['origin_key'],row['actual_outer_exit_code'],row['actual_native_exit_code'],row['kind'],row['reason'],pins['root_resume_failure'],row)
cf=json.loads(read(ph['failure_origins']['path']));assert len(cf['new_origins'])==1
row=cf['new_origins'][0];assert [row['actual_outer_exit'],row['actual_child_exit']]==[0,128];collect(row)
addorigin('codex:/root/command_queue_impl','list-fix-scope-'+row['origin'],0,128,row['kind'],row['cause'],ref(ph['failure_origins']['path'],ph['failure_origins']['sha256']),row)
assert len(origins)==len({v['origin_key'] for v in origins})==14 and not ({v['origin_key'] for v in origins}&{v.get('origin_key') for v in cp['failure_counters']})
pending=ref(sn/'r305-cursor-failure/handoff.json','2d30e7c118ed497c989faddac761eb411d0a25a8cb9ee96d5bb954a215ff0f94');pins['pending_postcut_cursor_failure']=pending
main_hold={'status':'HOLD_CONFIRMED_PUBLIC_SESSION_LIST_IDENTITY500','Main_source_writes_authorized':False,'handler_historical_ready_ref':pins['handler_final_review'],'adverse_nonauthor_review_ref':pins['list_adverse_nonauthor_review'],'protected_resources_ref':pins['protected_resources'],'draft_executor_ref':pins['unused_main_integration_executor'],'guard':'Never execute the old pinned22752 integration while current producer defect remains. A repaired candidate, nonauthor evidence and new Root scope/CAS are required.','formal_increment':0}
pins['main_integration_hold']=save('main_integration_hold.json',main_hold)
scope={'actor':'codex:/root','owner':'codex:/root/command_queue_impl','status':'AUTHORIZED_BY_CAS306_ONLY_NOT_EXECUTED','base_commit':'22752a6a41732c8c158d7d7e1b8932ec958f8cb8','worktree':'.local/worktrees/codex-w0599-session-list-identity-r306','branch':'work/codex-w0599-session-list-identity-r306','source_paths':['internal/domain/client_protocol_sessions.go','internal/api/v2_sessions_test.go'],'source_proposal_ref':pins['list_fix_proposal'],'mandatory_source_proposal':pp,'nonauthor_scope_review_ref':pins['list_fix_scope_review'],'mandatory_wire_conditions_ref':pins['list_fix_conditions'],'mandatory_wire_conditions':cond,'finite_cases_ref':ph['finite_cases'],'cases':14,'maximum_loopback_HTTP':224,'SDK_worker_model_external_paid_calls':0,'new_full_graph_schema_module_stdlib_generated_testmain_importcfg_tool_and_NEW_exe_required':True,'before_after_full_frozen_input_and_alltable_schema_multiset_and_closed_DB_required':True,'first_unexpected_stop':True,'Source_cli8_frozen_handler_author_Main_canonical_writes':0,'old_journal_backfill_or_globalidentity_schema_weakening':False,'source_ready':False,'Main_integration_hold_ref':pins['main_integration_hold'],'formal_increment':0,'sameprincipal_differentwriter_positive_required':True,'L05_L06_L14_wire_is_existing_short_error_wrapper_not_fullschema':True}
pins['list_identity_fix_execution_scope']=save('list_identity_fix_execution_scope.json',scope)
rootref=save('root_scope_review.json',{'decision':'ACTUAL_PUBLIC_LIST_IDENTITY500_SUSPENDS_MAIN_INTEGRATION_AND_EXACT2_NONAUTHOR_REVIEW_BOUND_REPAIR_SCOPE_AUTHORIZED','handler_original7fdf_not_rewritten':True,'old_AE_C09_green_and_old_failed_raw_preserved':True,'list_defect_review_ref':pins['list_adverse_nonauthor_review'],'list_fix_nonauthor_review_ref':pins['list_fix_scope_review'],'all14_future_cases':'NOT_RUN','max_active_construction_after_grant':2,'new_registered_origin_count':14,'counter_reset':False,'pending_after_cut':pending,'formal_increment':0})
audit=save('audit.json',{'canonical_before':before,'head':head,'git_status_sha256':hashlib.sha256(status).hexdigest(),'refs':pins,'manifests':manifest_audit,'origins':origins,'old_failure_count':348,'new_origin_count':14,'after':362,'pending_postcut_cursor_ref':pending,'main_integration_authorized':False,'list_source2_only_authorized':True,'formal_increment':0,'counter_reset':False})
assert all(p.read_bytes()==raw for p,raw in READS.items())
prepared=save('prepared_refs.json',{'pins':pins,'audit_ref':audit,'root_review_ref':rootref,'all_verified_refs':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)} for p,raw in sorted(READS.items(),key=lambda v:str(v[0]))],'canonical_before':before,'head':head,'git_status_sha256':hashlib.sha256(status).hexdigest(),'new_origin_count':14})
print(json.dumps({'prepared':prepared,'audit':audit,'scope':pins['list_identity_fix_execution_scope'],'verified_ref_count':len(READS),'registration_executed':False},ensure_ascii=True))
