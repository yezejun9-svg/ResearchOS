"""Preserve the actual W09 path diagnostic and committed CP375 continuation."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, os

R=Path(r'D:\作品集\ResearchOS\research-os'); N=Path(__file__).resolve().parent
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in
    {'pin','save','exact','outputs','capture'}],type_ignores=[]),'Root_functions_only','exec'),globals())
current=[exact(R/'execution/v2.4'/name,sha,size) for name,sha,size in (
    ('checkpoint.json','e75f9146266ce896a1eebd2fd4e6d1869bd4aadc6767d6e2b64c7344949d7fad',4739207),
    ('path_ownership.json','c064f519b5e6c10d64f54ae3d88260c33e00bdb20a4f1ed99dca156d6c21c91f',219480),
    ('step_state.json','fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149',257446),
    ('commands.json','12141a8ba01d34c7181ee35e054f4762732ca8627cbee87271610e65d6f28b97',67323))]
docs=[json.loads(Path(x['path']).read_bytes()) for x in current]
assert [x.get('revision') for x in docs]==[375,179,None,40]
assert docs[0]['work_in_progress']['root_next_failure_ordinal_live']==1109
for ref,name in zip(current,('checkpoint','path_ownership','step_state','commands')):
    with (N/('historical.cp375.before-native.'+name+'.json')).open('xb') as f:
        f.write(Path(ref['path']).read_bytes());f.flush();os.fsync(f.fileno())
def match(call,result):return any(x.get('chunk_id')=='b312e8' for x in outputs(result['payload'].get('output')))
pair=capture(AUDIT,1109,match,root=True);assert pair
event=json.loads(Path(pair[0]['path']).read_bytes().splitlines()[-1])
host=[x for x in outputs(event['payload']['output']) if x.get('chunk_id')=='b312e8']
assert len(host)==1 and host[0]['exit_code']==1 and 'ROOT_SOURCE_PYTHON_EXIT=1' in host[0]['output']
assert 'REGULAR_LOCAL_PATH' in host[0]['output']
binding=save('original1109.standard-binding.live1110.root.json',dict(
    schema='researchos.root-original-diagnostic-binding.v1',issued_by='codex:/root',
    original_capture_ref=pair[0],original_source_binding_ref=pair[1],original_source_binding_selector='$',
    original_ordinal=1109,original_bytes_unchanged=True,formal_authority=False))
row=dict(ordinal=1109,origin_ref=pair[0],origin_selector='$',capture_binding_ref=binding,
    description='Actual W09 NATIVE_SCOPES propose rejected legitimate R/.local scratch paths because the Source predicate rejected a device-path substring anywhere. Host/Python1/1; no Source guard, TP, Go, Native, SQL or model started. Minimal Source repair preserves other gates.',
    capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',actual_outer_exit=1,actual_python_exit=1,
    actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None)
pending=save('pending-diagnostics.cp375.live1110.root.json',dict(
    schema='researchos.root-pending-diagnostics.v1',issued_by='codex:/root',counter_reset=False,
    source_cutoff_original_failure_ordinal=1108,next_original_failure_ordinal=1110,
    registered_in_current_canon=False,pending=[row],current_canonical_refs=current))
profile=exact(R/'execution/v2.4/formal_profile_w09.py','d44500a9fceb9633109884f3860390e5d10bc877b4f3a66986ffd6e2038dc35f',71397)
W=R/'execution/v2.4/receipts/W09/W09-99'
commit=exact(W/'w09_profile_nf3_root_adoption_root/b97a3739b43c4118984b4a6d2a2d0d10/apply-profile.completed.json',
    '0300932c5dd55fc068db4046d15b54bc027b6c9f62170290e871685bf227d35b',3873)
failed_request=exact(N/'w09.native-scopes.3973828e064e4d7dbf9d1559c436340d.request.actual.root.json',
    '2c6ee6e7901b0e70a089a7454b2557ff86f3ed7b70922543c74e0b9f910b57b3',8158)
resume=save('RESUME.cp375-w09-profile-adopted.live1110.root.json',dict(
    schema='researchos.root-execution-resume.v1',issued_by='codex:/root',root_thread_id=THREAD,
    created_utc=datetime.now(timezone.utc).isoformat(),canonical_refs=current,expected_revisions=[375,179,None,40],
    pending_ref=pending,canonical_next_failure_ordinal=1109,next_original_failure_ordinal=1110,counter_reset=False,
    prior_resume_ref=pin(N/'RESUME.cp374-old21-registration.live1098.root.json'),
    Main23='QUALIFIED_CURRENT_MAIN23_BUILD',old21='ACTUAL_NINE_GO_PHASES_ZERO_NON_AUTHOR_PROGRAMME_REVIEW_DELIVERED_PENDING_ROOT_BINDING',
    W09='PROFILE_MAIN_AND_CM40_ACTUALLY_ADOPTED_NATIVE_SCOPES_PROPOSE_FAILED_BEFORE_GO_SOURCE_PATH_REPAIR_IN_PROGRESS',
    adopted_profile_ref=profile,profile_commit_ref=commit,failed_native_request_ref=failed_request,
    registered_new_diagnostics_once=list(range(1097,1109)),pending_diagnostic_ordinals=[1109],
    active_construction_parents=['W05','W09'],goal_status='ACTIVE',formal_cases_current_accepted=0,
    formal_cases_required=42,parent_tasks_required=22,formal_acceptance=False,parent_acceptance=False,
    next_actions=['Independently review minimal Source path-prefix repair, capture actual author and reviewer deliveries.',
                  'Bind old21 actual programme review through an actual Root observer; no formal case acceptance.',
                  'Register repaired W09 Native scopes, capture actual scope activations, then run the three reviewed selectors once.']))
handoff=R/'execution/v2.4/HANDOFF_RESUME_PACK.md'; old=handoff.read_bytes()
with (N/'historical.HANDOFF.before-live1110.root.md').open('xb') as f:f.write(old);f.flush();os.fsync(f.fileno())
prefix=('# Current Root continuation: CP375 / OW179 / CM40 / live next1110\n\n'
    'W09 profile and CM40 actually adopted. Native scope proposal failed on the legitimate .local path before any product process; minimal Source repair in progress. Old21 nine Go phases passed and independent programme review delivered; Root binding pending. Goal ACTIVE; formal0/42. Diagnostics1097..1108 registered once; original1109 pending; old failures and body preserved.\n\n'
    'Current resume: '+resume['path']+'\nSHA256 '+resume['sha256']+' bytes '+str(resume['bytes'])+'\n\n'
    'Pending diagnostics: '+pending['path']+'\nSHA256 '+pending['sha256']+' bytes '+str(pending['bytes'])+'\n\n').encode()
with handoff.open('wb') as f:f.write(prefix+old);f.flush();os.fsync(f.fileno())
assert handoff.read_bytes().endswith(old) and [pin(Path(x['path'])) for x in current]==current
print(json.dumps(dict(resume_ref=resume,pending_ref=pending,current_canonical_refs=current,
    original1109_retained=True,next_original_failure_ordinal=1110,Canon_unchanged=True,formal_acceptance=False),ensure_ascii=False,indent=2))
