import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid
if sys.flags.optimize != 0: raise RuntimeError('Optimized Python prohibited')
ROOT=Path.cwd().resolve()
OUT=Path(__file__).resolve().parent
BASE=ROOT/'execution/v2.4'
RECEIPTS=BASE/'receipts/W05/W05-99'
CANON=[BASE/name for name in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']]
READS={}
def ref(path,expected=None):
 p=Path(path)
 if not p.is_absolute():p=ROOT/p
 p=p.resolve();assert p.is_relative_to(ROOT)
 raw=p.read_bytes();digest=hashlib.sha256(raw).hexdigest();assert expected is None or digest==expected,str(p)
 if p in READS:assert READS[p]==raw
 READS[p]=raw
 return {'path':p.relative_to(ROOT).as_posix(),'sha256':digest,'bytes':len(raw)}
def read(path):
 r=ref(path);return READS[ROOT/r['path']]
def save(name,obj):
 p=OUT/name
 with p.open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
 return ref(p)
lock=json.loads(read(BASE.parent/'toolchains/locked.json'))['tools']
assert Path(sys.executable).resolve()==Path(lock['python']['path']).resolve()
assert hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest()==lock['python']['sha256']
git=lock['git']['path'];assert hashlib.sha256(Path(git).read_bytes()).hexdigest()==lock['git']['sha256']
before=[ref(p) for p in CANON]
expected=['0adc6e940240fa65007c5599fbb7c11a63f3138c8cc0e8ed8e9d64a7044036f3','0781e26a3ffdda21e5886448fa7498b041cad91777f1c05875557d529ef9904a','fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149','b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129']
assert [r['sha256'] for r in before]==expected
cp,ow=[json.loads(read(p)) for p in CANON[:2]];assert [cp['revision'],ow['revision'],len(cp['failure_counters'])]==[303,131,338]
head=subprocess.check_output([git,'rev-parse','HEAD'],cwd=ROOT).decode().strip();status=subprocess.check_output([git,'status','--porcelain=v1','--untracked-files=no'],cwd=ROOT)
assert head==cp['head']=='2cdb0d43d5a600eef13c8f1735946a9adf52d079';assert hashlib.sha256(status).hexdigest()=='e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4'
def rp(name):return RECEIPTS/name
pins={
 'previous_handoff':ref(rp('integration_codex/finite-cli-and-review-progress-r303/handoff-r303-running.json'),'2255e00a9540143ee538b8a8e54f25b54d2215f96ddef1ec441ade6308d2262f'),
 'AE_audit':ref(rp('handler38_independent_replay_codex/363d72047db247eea2a76e91be26ed8c/AE.independent_audit.json'),'710b0a7080ad09107629f93de17b13df303e83f9ee6678896d5d86ac98e8f791'),
 'AE_manifest':ref(rp('handler38_independent_replay_codex/363d72047db247eea2a76e91be26ed8c/manifest.json'),'046fc849ab56ae1dc35451285f96e78e1284f1e2a87963fd0f784b6bc9961b42'),
 'C09_handoff':ref(rp('handler38_independent_replay_codex/c09-a0163b5c32ed44f7aca7730f3834e009/handoff.json'),'25739f088d438f0c74a6c584c6b4ee3b3cd7a900a4f56621dd08c93610891ef7'),
 'C09_review':ref(rp('handler38_independent_replay_codex/c09-a0163b5c32ed44f7aca7730f3834e009/source_review.json'),'72b37ba2e5039e94bcbf014a88be20ac0e09b9f85be539a87313adb2f3d49ab6'),
 'C09_failure':ref(rp('handler38_independent_replay_codex/c09-a0163b5c32ed44f7aca7730f3834e009/failure_origins.json'),'77b9576789a62b84f787ff6dde287c8d0406fd3c868e2d933faf2151e4003dda'),
 'C09_manifest':ref(rp('handler38_independent_replay_codex/c09-a0163b5c32ed44f7aca7730f3834e009/manifest.json'),'fd12cb76cf053707efa748db0862690c6400a0e01aed7f33f5524aca6f1c084f'),
 'C09_supplement':ref(rp('handler38_independent_replay_codex/c09-constructor-supplement-7d063beb/supplement.json'),'1cc239be8695e11061477b8ab5da86e4fc9b9f6250b33166fa032075b81a5e9d'),
 'C09_supplement_manifest':ref(rp('handler38_independent_replay_codex/c09-constructor-supplement-7d063beb/manifest.json'),'15fc21d9145849e07ea2ffcd6e5eefd80f6dcbccbc9c7c66dbb48cf4f980dcd3'),
 'C09_correction_review':ref(rp('handler_c09_fixture_correction_scope_review_codex/528ded309b3d463c81752469f0bb8c67/scope_review.json'),'108eabbacce80debdb5ab9f0eaa2de005ef9670924a5f8d6445cf72da0015997'),
 'C09_correction_manifest':ref(rp('handler_c09_fixture_correction_scope_review_codex/528ded309b3d463c81752469f0bb8c67/manifest.json'),'025a3517118ec73247b10d22c29aa71407d4ff3aaa9cdf3d05633f3a32e93a48'),
 'G2_root_review':ref(rp('integration_codex/provider-g2-finite-scope-review-r303/review.json'),'d3435cebd60f92e3f828acae493a4b9b4da534612dc6800d70165a1ce5976bf5'),
 'G2_root_conditions':ref(rp('integration_codex/provider-g2-finite-scope-review-r303/mandatory_conditions.json'),'c9593443afe4186d67978b632c0b790247b76680346e99d798a231b4dd3ffe10'),
 'G2_root_manifest':ref(rp('integration_codex/provider-g2-finite-scope-review-r303/manifest.json'),'c3d2bb9fc26d7ad3fde60c9fe8776b4b46af8f1cec2ee0c5698e6f85c06fa47d'),
 'cli_scope':ref(rp('integration_codex/finite-cli-and-review-progress-r303/cli_implementation_scope.json'),'c1414d67432e9217a6cf185a67532a171815bc08a95649b6e8b70c8715f07304'),
 'packet_next_invocation':ref(rp('integration_codex/finite-cli-and-review-progress-r303/task-packet-next.invocation.json')),
 'packet_next_stdout':ref(rp('integration_codex/finite-cli-and-review-progress-r303/task-packet-next.stdout.raw')),
 'packet_next_stderr':ref(rp('integration_codex/finite-cli-and-review-progress-r303/task-packet-next.stderr.raw')),
}
manifest_audit=[]
for key in ['AE_manifest','C09_manifest','C09_supplement_manifest','C09_correction_manifest','G2_root_manifest']:
 mfpath=ROOT/pins[key]['path'];obj=json.loads(read(mfpath));rows=obj.get('entries',obj.get('files'));assert isinstance(rows,list)
 for row in rows:
  p=Path(row['path'])
  if not p.is_absolute():p=(ROOT/p) if row['path'].startswith('execution/') else mfpath.parent/p
  p=p.resolve();assert p.is_relative_to(mfpath.parent),str(p)
  actual=ref(p,row['sha256']);assert actual['bytes']==row['bytes']
 manifest_audit.append({'name':key,'ref':pins[key],'listed':len(rows),'bad':0})
assert [row['listed'] for row in manifest_audit]==[754,44,2,27,4]
AE=json.loads(read(pins['AE_audit']['path']));assert [r['batch'] for r in AE['counts']]==list('ABCDE');assert [r['test_events']['pass'] for r in AE['counts']]==[189,10,1,1,294];assert all(r['exit']==0 and r['test_events']['fail']==r['test_events']['skip']==0 for r in AE['counts']);assert AE['input_count']==42940 and AE['input_drift'] is False
for key in ['before','after','source38']:
 row=AE[key];actual=ref(row['path'],row['sha256']);assert actual['bytes']==row['bytes']
for row in AE['counts']:
 for key in ['raw','invocation']:
  item=row[key];actual=ref(item['path'],item['sha256']);assert actual['bytes']==item['bytes']
review=json.loads(read(pins['C09_correction_review']['path']));assert review['decision']=='SOURCE_SCOPE_READY_WITH_CONDITIONS' and review['product_acceptance'] is False;assert len(review['future_execution']['cases'])==6
old_failure=json.loads(read(pins['C09_failure']['path']));assert len(old_failure)==1;case_origin=old_failure[0];assert case_origin['actual_native_exit']==case_origin['outer_driver_exit']==1 and case_origin['counter_increment']==1
hold_path=ROOT/'.local/worktrees/codex-w0599-cli-contract-repair-r303/execution/v2.4/receipts/W05/W05-99/cli_protocol_exact8_executor_codex/32000aadb56142468ad17096b4d18953/attach-producer-hold.json'
hold_ref=ref(hold_path,'1b3ba4bbcf3048cf58f8468a43cefb19bcadf0c743312e792f8d97a39e64cfd2');hold_raw=read(hold_path)
with (OUT/'cli-attach-producer-hold.original.json').open('xb') as f:f.write(hold_raw)
pins['cli_attach_hold']=ref(OUT/'cli-attach-producer-hold.original.json',hold_ref['sha256'])
origins=[
 {'origin_key':'handler38-c09-readonly-3bac0f','actor':'codex:/root/w05_merge_review','actual_outer_exit_code':1,'kind':'READONLY_TOOL_LOCATOR','reason':'guessed SQL23 name, actual0023_host_model_configuration corrected readonly','evidence_ref':ref(rp('handler38_independent_replay_codex/363d72047db247eea2a76e91be26ed8c/C09-readonly-tool-original-3bac0f.json'),'94b605d1275c0171d58486f8769535a63a1cc0944dfce4634c7dfe4ce38703c1')},
 {'origin_key':'root-readonly-resume-boundary-b8925d','actor':'codex:/root','actual_outer_exit_code':1,'kind':'READONLY_TOOL_LOCATOR','reason':'guessed nonexistent client_sessions.go; actualclient_protocol_sessions.go corrected readonly','evidence_ref':ref(rp('integration_codex/resume-producer-boundary-continuation-r303-13e38ae8b7ab4f32b3b7336836e2b6d5/tool_failure_origin.json'),'0df7d3e913544bfa0dad21dded1849d0aa8786c22e6231bfb3e0036a10db50c4')},
 {'origin_key':case_origin['origin_id'],'actor':'codex:/root/w05_merge_review','actual_outer_exit_code':1,'actual_native_exit_code':1,'kind':'C09_INDEPENDENT_TEST_HARNESS_PRECONDITION','reason':case_origin['reason'],'failed_leaf_cases':1,'failed_parent_tests':1,'one_invocation_not_two_events':True,'remaining_NOT_RUN':5,'evidence_ref':pins['C09_failure']},
 {'origin_key':'command-c09-readonly-locator-269db7','actor':'codex:/root/command_queue_impl','actual_outer_exit_code':1,'kind':'READONLY_TOOL_LOCATOR','reason':'Root supplied unverified nested C09 directory; actual sibling receipt corrected readonly','evidence_ref':ref(rp('handler_c09_fixture_correction_scope_review_codex/528ded309b3d463c81752469f0bb8c67/tool_diagnostics.json'))},
 {'origin_key':'root-readonly-provider-stage-locator-46193d','actor':'codex:/root','actual_outer_exit_code':1,'kind':'READONLY_TOOL_LOCATOR','reason':'guessed nonexistent runtime_launch_windows.go; actual coordinator stages retained','evidence_ref':ref(rp('integration_codex/provider-g2-finite-scope-review-r303/tool_failure_origin.json'),'f2fef555dcae313c0d7191a3384c3026939bbbce55865751215093abaef03cfe')},
]
assert len({r['origin_key'] for r in origins})==5 and not ({r['origin_key'] for r in origins}&{r.get('origin_key') for r in cp['failure_counters']})
new_id=uuid.uuid4().hex
scope={'actor':'codex:/root','owner':'codex:/root/w05_merge_review','status':'AUTHORIZED_BY_CAS304_ONLY_NOT_EXECUTED','candidate':'22752a6a41732c8c158d7d7e1b8932ec958f8cb8','checkout':'.local/independent-handler38-a639cfcf','new_receipt_namespace':f'execution/v2.4/receipts/W05/W05-99/handler38_independent_replay_codex/c09-attach-correction-r304-{new_id}','new_work_namespace':f'.local/independent-handler38-a639cfcf/.local/c09-attach-correction-r304-{new_id}','previous_failed_cohort':pins['C09_handoff'],'nonauthor_correction_review_ref':pins['C09_correction_review'],'constructor_supplement_ref':pins['C09_supplement'],'virtual_test':'internal/domain/handler_configuration_independent_review_test.go','selector':'^TestIndependentHandlerConfigurationC09$','cases':review['future_execution']['cases'],'mandatory_scope_conditions':review,'change_surface':review['allowed_future_change_surface'],'fixture_sha256':review['future_execution']['fixture_sha256'],'first_unexpected_stop':True,'A_E_rerun':False,'product38_SQL_SDK_Main_canonical_writes':0,'paid_model_HTTP_Node_worker_private_calls':0,'source_ready':False,'formal_increment':0,'old_failed_invocations_preserved':1,'automatic_same_input_retry':False,'control_qualification':'Actual domain configuration guard over known original public SQLite; residual permission/nonheadRun SYNTHETIC injections, not real lifecycle/runtime qualification. Actual lease/journal ACK is not CLI COMPLETED.'}
pins['C09_corrected_execution_scope']=save('c09_corrected_execution_scope.json',scope)
rootreview={'actor':'codex:/root','decision':'C09_TWO_CONSTRUCTOR_FIXES_AND_EXPLICIT_EVIDENCE_HOOKS_BOUND_BY_NONAUTHOR_REVIEW','C09_source_ready':False,'AE':'Five original distinct batches actual0 independently audited, no repeat or formal promotion; C09 needed separately.','CLI':'Exact8author continues P01/P03/P04; actualwriteattach completion positive scenarios HOLD per realproducer, valid selfwriter/read/refusal and explicit typedprotocolfixture controls remain. Original37 rows not silently demoted or declared fullyexecuted.','G2':'Finite29 exacttest2 SOURCE_SCOPE_READY_WITH_MANDATORY_IMPLEMENTATION_CONDITIONS nonauthorRootreview recorded, no edit/executionlease until free slot/separateCAS.','old338_prefix_unchanged':True,'failure_origins_after':343,'formal_increment':0}
rootreview_ref=save('root_scope_review.json',rootreview)
audit_ref=save('audit.json',{'canonical_before':before,'head':head,'git_status_sha256':hashlib.sha256(status).hexdigest(),'refs':pins,'manifests':manifest_audit,'origins':origins,'old_failure_count':338,'new_origin_count':5,'AE_separate_counts':AE['counts'],'C09_original_failure_not_product_predicate':True,'counter_reset':False,'formal_increment':0})
assert all(p.read_bytes()==raw for p,raw in READS.items())
prepared=save('prepared_refs.json',{'pins':pins,'audit_ref':audit_ref,'root_review_ref':rootreview_ref,'all_verified_refs':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)} for p,raw in sorted(READS.items(),key=lambda row:str(row[0]))],'canonical_before':before,'head':head,'git_status_sha256':hashlib.sha256(status).hexdigest(),'new_origin_count':5})
print(json.dumps({'prepared':prepared,'audit':audit_ref,'C09_scope':pins['C09_corrected_execution_scope'],'verified_ref_count':len(READS),'failure_origins':5,'registration_executed':False},ensure_ascii=True))
