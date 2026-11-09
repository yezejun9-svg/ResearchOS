import hashlib
import json
from pathlib import Path
import subprocess
import sys
if sys.flags.optimize != 0: raise RuntimeError('Optimized Python prohibited')
ROOT=Path.cwd().resolve();OUT=Path(__file__).resolve().parent;BASE=ROOT/'execution/v2.4';RECEIPTS=BASE/'receipts/W05/W05-99'
CANON=[BASE/name for name in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']];READS={}
def ref(path,expected=None):
 p=Path(path)
 if not p.is_absolute():p=ROOT/p
 p=p.resolve();assert p.is_relative_to(ROOT)
 raw=p.read_bytes();digest=hashlib.sha256(raw).hexdigest();assert expected is None or digest==expected,str(p)
 if p in READS:assert READS[p]==raw
 READS[p]=raw
 return {'path':p.relative_to(ROOT).as_posix(),'sha256':digest,'bytes':len(raw)}
def read(path):
 row=ref(path);return READS[ROOT/row['path']]
def save(name,obj):
 p=OUT/name
 with p.open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
 return ref(p)
def verify_row(row,base=ROOT):
 p=Path(row['path']);p=p if p.is_absolute() else base/p
 actual=ref(p,row['sha256']);assert 'bytes' not in row or actual['bytes']==row['bytes'];return actual
def collect(obj,base):
 if isinstance(obj,dict):
  if isinstance(obj.get('path'),str) and isinstance(obj.get('sha256'),str):verify_row(obj,base)
  else:
   for value in obj.values():collect(value,base)
 elif isinstance(obj,list):
  for value in obj:collect(value,base)
lock=json.loads(read(ROOT/'execution/toolchains/locked.json'))['tools'];git=lock['git']['path']
assert Path(sys.executable).resolve()==Path(lock['python']['path']).resolve()
assert hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest()==lock['python']['sha256']
assert hashlib.sha256(Path(git).read_bytes()).hexdigest()==lock['git']['sha256']
before=[ref(p) for p in CANON]
assert [v['sha256'] for v in before]==['bfe7c0acbe956d6ef36a9b5f30563d8e90e5147fafafb29c51a89b02a05de51b','c93b5f247c44fb2cfa8625befbc8f66ad827d3cacc7f2aa6b06b204a1a0ff514','fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149','b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129']
cp,ow=[json.loads(read(p)) for p in CANON[:2]];assert [cp['revision'],ow['revision'],len(cp['failure_counters'])]==[304,132,343]
head=subprocess.check_output([git,'rev-parse','HEAD'],cwd=ROOT).decode().strip();status=subprocess.check_output([git,'status','--porcelain=v1','--untracked-files=no'],cwd=ROOT)
assert head==cp['head']=='2cdb0d43d5a600eef13c8f1735946a9adf52d079';assert hashlib.sha256(status).hexdigest()=='e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
source_root=ROOT/'.local/worktrees/codex-w0599-cli-contract-repair-r303';source_ns=source_root/'execution/v2.4/receipts/W05/W05-99/cli_protocol_exact8_executor_codex/32000aadb56142468ad17096b4d18953'
review_ns=RECEIPTS/'cli_create_owned_lease_scope_review_codex/318624160041472d8e73ce5de71149a0'
pins={
 'previous_handoff':ref(RECEIPTS/'integration_codex/c09-correction-and-progress-r304/handoff-r304-running.json','cbe0f28e4f168f40da5d44803f19c4cf26aa2f2cbfca9e383e795da3aeaee1a4'),
 'parent_cli_scope':ref(RECEIPTS/'integration_codex/finite-cli-and-review-progress-r303/cli_implementation_scope.json','c1414d67432e9217a6cf185a67532a171815bc08a95649b6e8b70c8715f07304'),
 'amendment_nonauthor_review':ref(review_ns/'scope_review.json','ca7e6a22856add5d859bac7489e02ccd02f6c17330be06bb78f966dba5e1050e'),
 'amendment_review_manifest':ref(review_ns/'manifest.json','20de6c68f8a9bd91c08ad4c101051cf7ae0a00e1865e8d6c39affb51aed263b5'),
 'amendment_review_handoff':ref(review_ns/'handoff.json','1422ac4a7d1c1762aa8b98189e0af6e6a2a118db1501d71bf9bdad1b305456b1'),
 'source_pre_amendment_handoff':ref(source_ns/'pre-amendment-handoff/handoff.json','8572b544f7ba1b1c7d90df00197203a66170dfe5663a791c95e656ea9ec99339'),
 'source_pre_amendment_manifest':ref(source_ns/'pre-amendment-handoff/manifest.json','31487906553ffe7c8ee15479a8f77106c3966443b5f1545df70c48e466b959ed'),
 'source_pre_amendment_failures':ref(source_ns/'pre-amendment-handoff/failure_origins.json','80d6c47fc978d060c39332e23042b3e57227f14404d1ea8b520dacd27ba7a81b'),
 'source_amendment_proposal':ref(source_ns/'create-owned-lease-amendment-proposal.json','9485b0a7ab5ccb9f494740ff57d015de0e03558d3945af66e7fcbfefe08b9bc1')}
manifest_audit=[]
for key,base,parent in [('amendment_review_manifest',ROOT,review_ns),('source_pre_amendment_manifest',source_root,source_ns/'pre-amendment-handoff')]:
 mf=json.loads(read(pins[key]['path']));rows=mf.get('entries',mf.get('files'));assert isinstance(rows,list)
 for row in rows:
  actual=verify_row(row,base);assert (ROOT/actual['path']).is_relative_to(parent)
 manifest_audit.append({'name':key,'ref':pins[key],'listed':len(rows),'bad':0})
assert [m['listed'] for m in manifest_audit]==[23,6]
review=json.loads(read(pins['amendment_nonauthor_review']['path']));assert review['decision']=='SOURCE_SCOPE_READY_WITH_CONDITIONS' and review['implementation_accepted'] is False
assert review['exact_future_source_boundary']['same8'] is True and review['exact_future_source_boundary']['outside_same8_changes']==0
assert [c['id'] for c in review['mandatory_conditions']]==['C'+str(i).zfill(2) for i in range(1,11)]
assert [v['id'] for v in review['row_delta']]==['P01-04','P01-05','P01-07']
pre=json.loads(read(pins['source_pre_amendment_handoff']['path']));assert pre['status']=='PRE_AMENDMENT_DEVELOPMENT_EVIDENCE_NO_SOURCE_READY' and len(pre['runs'])==2
collect(pre,source_root)
assert [v['leaf_pass'] for v in pre['runs']]==[57,10] and all(v['exit']==0 and v['leaf_fail']==v['leaf_skip']==0 and v['drift'] is False for v in pre['runs'])
failure=json.loads(read(pins['source_pre_amendment_failures']['path']));assert failure['new_origin_count']==len(failure['origins'])==5
collect(failure,source_root)
assert [(v['actual_outer_exit'],v['actual_native_exit']) for v in failure['origins']]==[(1,None),(1,None),(1,None),(0,2),(1,1)]
origins=[]
for row in failure['origins']:
 v={'origin_key':row['id'],'actor':'codex:/root/sources_parent_impl','kind':row['kind'],'reason':row['cause'],'actual_outer_exit_code':row['actual_outer_exit'],'actual_native_exit_code':row['actual_native_exit'],'source_failure_origin_ref':pins['source_pre_amendment_failures'],'source_origin':row,'evidence_ref':verify_row(row.get('evidence_ref',row.get('invocation_ref')),source_root)}
 origins.append(v)
assert len({v['origin_key'] for v in origins})==5 and not ({v['origin_key'] for v in origins}&{v.get('origin_key') for v in cp['failure_counters']})
for key,name in [('source_amendment_proposal','create-owned-lease-amendment-proposal.original.json'),('source_pre_amendment_failures','cli-pre-amendment-failures.original.json'),('source_pre_amendment_handoff','cli-pre-amendment-handoff.original.json')]:
 raw=read(pins[key]['path'])
 with (OUT/name).open('xb') as f:f.write(raw)
 pins[key+'_root_original']=ref(OUT/name,pins[key]['sha256'])
parent=json.loads(read(pins['parent_cli_scope']['path']))
scope={'actor':'codex:/root','owner':'codex:/root/sources_parent_impl','status':'AUTHORIZED_BY_CAS305_ONLY_NOT_EXECUTED','base_commit':'22752a6a41732c8c158d7d7e1b8932ec958f8cb8','worktree':source_root.relative_to(ROOT).as_posix(),'parent_scope_ref':pins['parent_cli_scope'],'same8':True,'amendment_source_paths':['apps/cli/cli_verbs.go','apps/cli/cli_sessions_test.go','apps/cli/cli_stream_test.go'],'future_boundary':review['exact_future_source_boundary'],'mandatory_conditions':review['mandatory_conditions'],'row_delta':review['row_delta'],'nonauthor_review_ref':pins['amendment_nonauthor_review'],'proposal_original_ref':pins['source_amendment_proposal_root_original'],'pre_amendment_evidence_ref':pins['source_pre_amendment_handoff_root_original'],'fresh_exact_leaf_freeze_full_compile_and_new_executables_required':True,'pre_amendment_results_not_inherited_for_new_source_acceptance':True,'actual_attach_acquire_renewal_and_P02_fullformal':'HOLD','domain_SQL_provider_Main_frozen_contract_writes':0,'external_model_SDK_paid_calls':0,'source_ready':False,'formal_increment':0,'all_original_scope_conditions_remain':True,'first_unexpected_stop':True}
pins['cli_create_owned_lease_amendment_scope']=save('cli_create_owned_lease_amendment_scope.json',scope)
root_review_ref=save('root_scope_review.json',{'actor':'codex:/root','decision':'SAME8_NEW_CREATE_ORIGINAL_COMPLETED_VALIDATED_OWN_LEASE_DIRECT_SEND_NARROW_AMENDMENT_NONAUTHOR_REVIEW_BOUND','nonauthor_review_ref':pins['amendment_nonauthor_review'],'mandatory_conditions':10,'row_delta':['P01-04','P01-05','P01-07'],'actual_attach_producer_gap_not_fixed':True,'pre_amendment_two_batches':'AUTHOR_REPORTED_NATIVE0_57_AND10_LEAF_DEVELOPMENT_ONLY_NO_SOURCE_ACCEPTANCE','old343_failure_prefix_unchanged':True,'new_origins':5,'formal_increment':0})
audit_ref=save('audit.json',{'canonical_before':before,'head':head,'git_status_sha256':hashlib.sha256(status).hexdigest(),'refs':pins,'manifests':manifest_audit,'origins':origins,'old_failure_count':343,'new_origin_count':5,'author_pre_amendment_runs':pre['runs'],'pre_amendment_results_not_inherited':True,'counter_reset':False,'formal_increment':0})
assert all(p.read_bytes()==raw for p,raw in READS.items())
prepared=save('prepared_refs.json',{'pins':pins,'audit_ref':audit_ref,'root_review_ref':root_review_ref,'all_verified_refs':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)} for p,raw in sorted(READS.items(),key=lambda v:str(v[0]))],'canonical_before':before,'head':head,'git_status_sha256':hashlib.sha256(status).hexdigest(),'new_origin_count':5})
print(json.dumps({'prepared':prepared,'audit':audit_ref,'scope':pins['cli_create_owned_lease_amendment_scope'],'verified_ref_count':len(READS),'registration_executed':False},ensure_ascii=True))
