"""Read committed Root registration, retain the latest diagnostic, prepare build observation."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, os, sys, types
R=Path(r'D:\作品集\ResearchOS\research-os'); N=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in
    {'pin','save','exact','outputs','capture'}],type_ignores=[]),'Root_helper_functions_only','exec'),globals())
p=B/'schema21_root_caller_registration_source_codex/s21root-20261010-03/old21_root.source.py'
exact(p,'b538b9b543ac0d45140834d52b0a209dc47546ac7c007ec9aaeda9e8602a1b06',65191)
caller=types.ModuleType('root_old21_live_lease_readback');caller.__file__=str(p);sys.modules[caller.__name__]=caller
exec(compile(p.read_bytes(),str(p),'exec'),caller.__dict__)
q=json.loads((N/'old21.v3.registration-request.actual.root.json').read_bytes())
reg=Path(q['registration_root']); activation=json.loads((reg/'activate.result.json').read_bytes())
refs=[pin(R/'execution/v2.4'/name) for name in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
assert [(x['sha256'],x['bytes']) for x in refs]==[
    ('95dc8e16e0e10ee17ad784143da840eacdfc16664c30454621e5badc83bdc8ee',4711819),
    ('3404ddde0aa94524402a6e5d899b783d3b84b0355610a46692034d2cd3c08edd',216742),
    ('fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),
    ('28b4ba18ce2ab3ce03287651e311ae2bd36293b53fd8c298e5bf1f231f56d027',68968)]
actual=dict(scope_ref=activation['scope_ref'],facts_ref=activation['facts_ref'],case_request_ref=q['case_request_ref'],
    registration_result_ref=pin(reg/'activate.result.json'),runtime_qualification_ref=q['runtime_qualification_ref'],current_canonical_refs=refs)
scope,facts,_,current=caller.live_lease(actual,require_new=True)
assert activation['complete_inverse'] is True and activation['SS_CM_unchanged'] is True
journal=json.loads((Path(activation['transaction']['transaction_journal'])/'committed.json').read_bytes())
assert journal['both_verified_while_exclusively_held'] is True and journal['written_indices']==[0,1]
assert len(journal['after_refs'])==2 and all(caller.same_ref(a,b) for a,b in zip(journal['after_refs'],refs[:2]))
assert current['documents'][0]['work_in_progress']['root_next_failure_ordinal_live']==1097
identity=exact(R/'execution/project_identity.json','03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec',420)
for ref,name in zip(refs,('checkpoint','path_ownership','step_state','commands')):
    with (N/('historical.cp374.before-old21.'+name+'.json')).open('xb') as f:
        f.write(Path(ref['path']).read_bytes());f.flush();os.fsync(f.fileno())
def failed(call,result):return any(x.get('chunk_id')=='d1d7a7' for x in outputs(result['payload'].get('output')))
original=capture(AUDIT,1097,failed,root=True);assert original
bound=json.loads(Path(original[1]['path']).read_bytes())
last=json.loads(Path(original[0]['path']).read_bytes().splitlines()[-1])
hosts=[x for x in outputs(last['payload']['output']) if x.get('chunk_id')=='d1d7a7']
assert len(hosts)==1 and hosts[0]['exit_code']==1
standard=save('original1097.standard-binding.live1098.root.json',dict(schema='researchos.root-original-diagnostic-binding.v1',
    issued_by='codex:/root',original_capture_ref=original[0],original_source_binding_ref=original[1],
    original_source_binding_selector='$',original_ordinal=1097,original_bytes_unchanged=True,formal_authority=False))
row=dict(ordinal=1097,origin_ref=original[0],origin_selector='$',capture_binding_ref=standard,
    description='Root read actual old21 Source successfully, then guessed a nonexistent old Main23 preparer filename. Host exited1; no Python/Go/Native/SQL/TP/model started.',
    capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',actual_outer_exit=1,actual_python_exit=None,
    actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None)
pending=save('pending-diagnostics.cp374.live1098.root.json',dict(schema='researchos.root-pending-diagnostics.v1',issued_by='codex:/root',
    counter_reset=False,source_cutoff_original_failure_ordinal=1096,next_original_failure_ordinal=1098,
    registered_in_current_canon=False,pending=[row],current_canonical_refs=refs))
context=save('old21.v3.build-prerequisites.context.actual.root.json',dict(actual,
    registration_request_ref=pin(N/'old21.v3.registration-request.actual.root.json'),expected_revisions=current['revisions'],
    builder_review_refs=q['builder_review_refs'],identity_ref=identity,created_utc=datetime.now(timezone.utc).isoformat()))
observed=[actual[k] for k in ('scope_ref','facts_ref','registration_result_ref','runtime_qualification_ref')]+list(q['builder_review_refs'].values())+refs
observer=save('old21.v3.build-prerequisites.observer-input.actual.root.json',dict(operation='OLD21_BUILD_PREREQUISITES',observed_refs=observed,peer_actor=None))
resume=save('RESUME.cp374-old21-registration.live1098.root.json',dict(schema='researchos.root-execution-resume.v1',issued_by='codex:/root',
    root_thread_id=THREAD,created_utc=datetime.now(timezone.utc).isoformat(),canonical_refs=refs,expected_revisions=current['revisions'],pending_ref=pending,
    canonical_next_failure_ordinal=1097,next_original_failure_ordinal=1098,counter_reset=False,Main23='QUALIFIED_CURRENT_MAIN23_BUILD',
    old21='SOURCE03_RUNTIME_QUALIFIED_ACTUAL_ROOT_TP_COMMITTED_BUILD_PREREQUISITES_READY_BUILD_NOT_STARTED',old21_context_ref=context,
    W09='ROOT_ADOPTION_SOURCE_INDEPENDENTLY_ACCEPTED_AND_ACTUAL_PEER_DELIVERIES_VALIDATED_ACTUAL_ADOPTION_NOT_STARTED_CM39',
    goal_status='ACTIVE',formal_cases_current_accepted=0,formal_cases_required=42,parent_tasks_required=22,formal_acceptance=False,parent_acceptance=False,
    prior_resume_ref=pin(N/'RESUME.cp373-source-adoptions.live1097.root.json')))
handoff=R/'execution/v2.4/HANDOFF_RESUME_PACK.md';old=handoff.read_bytes()
with (N/'historical.HANDOFF.before-live1098.root.md').open('xb') as f:f.write(old);f.flush();os.fsync(f.fileno())
prefix=('# Current Root continuation: CP374 / OW178 / CM39 / live next1098\n\n'
    'Old21 Root registration actually committed; Sources and runtime qualified; actual build not started. W09 adoption Source independently accepted and actual peer deliveries validated. Main23 programme qualified. Goal ACTIVE; formal0/42. Diagnostics1067..1096 registered once; original1097 pending; counters and old body preserved.\n\n'
    'Current resume: '+resume['path']+'\nSHA256 '+resume['sha256']+' bytes '+str(resume['bytes'])+'\n\n'
    'Pending diagnostics: '+pending['path']+'\nSHA256 '+pending['sha256']+' bytes '+str(pending['bytes'])+'\n\n').encode()
with handoff.open('wb') as f:f.write(prefix+old);f.flush();os.fsync(f.fileno())
assert handoff.read_bytes().endswith(old)
print(json.dumps(dict(context_ref=context,observer_input_ref=observer,pending_ref=pending,resume_ref=resume,
    current_canonical_refs=refs,actual_revisions=current['revisions'],Root_TP_committed=True,
    actual_old21_build_started=False,Canon_unchanged=True,formal_acceptance=False),ensure_ascii=False,indent=2))
