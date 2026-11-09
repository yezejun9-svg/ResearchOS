"""Preserve one original Root diagnostic and the completed Native continuation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, re

N = Path(__file__).resolve().parent
R = Path(r'D:\作品集\ResearchOS\research-os')
W = R/'execution/v2.4/receipts/W09/W09-99'
AUDIT = Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'

def pin(p):
    p = Path(p); raw = p.read_bytes()
    return dict(path=str(p), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def save(name, value, binary=False):
    raw = value if binary else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with (N/name).open('xb') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    return pin(N/name)

def documents(v):
    if isinstance(v,dict):
        yield v
        for x in v.values(): yield from documents(x)
    elif isinstance(v,list):
        for x in v: yield from documents(x)
    elif isinstance(v,str):
        try: v=json.loads(v)
        except ValueError: return
        yield from documents(v)

calls = {}; found = []
with AUDIT.open('rb') as f:
    header=f.readline()
    assert json.loads(header)['payload']['id']==THREAD
    f.seek(0,2); prefix=f.tell(); f.seek(max(len(header),prefix-32*1024*1024))
    if f.tell()>len(header): f.readline()
    while f.tell()<prefix:
        off=f.tell(); raw=f.readline(); e=json.loads(raw); p=e.get('payload',{})
        if e.get('type')!='response_item' or not isinstance(p,dict): continue
        if p.get('type') in ('function_call','custom_tool_call'):
            calls[p.get('call_id')]=(off,raw)
        elif p.get('type') in ('function_call_output','custom_tool_call_output') and p.get('call_id') in calls:
            hits=[x for x in documents(p.get('output')) if x.get('chunk_id')=='37dbc2']
            if hits:
                assert len(hits)==1
                found.append((calls[p['call_id']],(off,raw),hits[0]))
assert len(found)==1
(co,call),(ro,result),observation=found[0]
lines=[header,call,result]; offsets=[0,co,ro]
with AUDIT.open('rb') as f:
    for off,line in zip(offsets,lines): f.seek(off); assert f.readline()==line
marks=re.findall(r'(?m)^ROOT_SOURCE_PYTHON_EXIT=(-?\d+)\s*$',observation['output'])
assert observation['exit_code']==1 and marks==['1']
raw_ref=save('original1131.actual-host.raw.jsonl',b''.join(lines),True)
binding_ref=save('original1131.actual-host.binding.json',dict(
    schema='researchos.root-native-original-host-binding.v1',actor_id='codex:/root',
    Root_thread_id=THREAD,original_failure_ordinal=1131,original_chunk_id='37dbc2',
    source_audit_path=str(AUDIT),source_prefix_size_observed=prefix,
    source_line_offsets=offsets,original_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],
    original_capture_ref=raw_ref,actual_outer_exit=1,marked_actual_python_exit=1,
    actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,
    actual_dispatcher_exit=None,actual_model_exit=None,automatic_retry=False,counter_reset=False,
    diagnosis='Readonly shape query called .get on the actual failure_counters list. No mutation or product call.'))
prior_ref=pin(N/'RESUME.cp376-w09-G02-running.live1119.root.json')
prior=json.loads(Path(prior_ref['path']).read_bytes())
current=prior['canonical_refs']
assert all(pin(x['path'])==x for x in current)
nf=W/'full_w09_main_native_producer_source_codex/fullw09-20261010-03'
r2=W/'full_w09_actual_native_independent_review_codex/actual-three-20261010-01'
native={}
for selector,runid,actual,ordinal in [
    ('W09-G01','4fd62ca511684dc39d62c5571d8ddaf5',0,None),
    ('W09-G02','28aa266121d24ad2988d578df02d23a4',1,1121),
    ('A06','ba9a185f551c4d4caf123da7eafb4245',1,1125)]:
    p=nf/('actual-'+selector+'-'+runid)/'producer/validation.closed.json'
    v=json.loads(p.read_bytes())
    assert v['all_guards_closed'] and v['all_owned_jobs_closed'] and not v['cleanup_errors']
    native[selector]=dict(run_id=runid,validation_closed_ref=pin(p),
        actual_outer_exit=actual,actual_python_exit=actual,actual_Go_test_exit=actual,
        original_failure_ordinal=ordinal,all_guards_closed=True,all_owned_jobs_closed=True,
        one_shot_used=True,automatic_retry=False,current_formal_acceptance=False)
review_ref=pin(r2/'HDF.json')
assert review_ref['sha256']=='8736edead7afeab47341b2f8e484c469e4c24aa86c31244f03109afc96152233'
resume_ref=save('RESUME.cp376-w09-all-closed.live1134.root.json',dict(prior,
    created_utc=datetime.now(timezone.utc).isoformat(),prior_resume_ref=prior_ref,
    next_original_failure_ordinal=1134,registered_through_original_ordinal=1116,
    pending_original_ordinals=list(range(1117,1134)),Root_original1131_ref=raw_ref,
    Root_original1131_binding_ref=binding_ref,
    pending_foreign_capture_delivery_ordinals=[1132,1133],
    W09='THREE_NATIVE_CLOSED_G01_QUALIFIED_G02_A06_FAILED_LEGACY_FIXTURE_SOURCE_ACCEPTED',
    native_processes=native,no_inflight_native_sessions=True,
    actual_review_handoff_ref=review_ref,
    actual_review_Final_capture_ref=pin(N/'w09.current-three-native-review.actual-audit.root.json'),
    public21_leaf02_review_Final_capture_ref=pin(N/'w09.public21-source-review-v2.actual-audit.root.json'),
    fixture_proposal_ref=pin(N/'legacy-fixture-repair-20261010-01/proposal.json'),
    Main_fixture_adopted=False,Source21_after_adoption_requires_new_evidence=True,
    old_C19_consumers_are_historical_after_source_change=True,
    Source_bridge01_execution_permitted=False,
    Source_bridge02_status='IN_PROGRESS_TASK95_SOURCE_ONLY',
    public21_caller_status='TASK91_SOURCE_ONLY_IN_PROGRESS',
    model_branch='BILLING_AND_SERVER_TERMINATION_UNRESOLVED_NO_NEW_PAID_CALL',
    formal_case_accepted_count=0,formal_case_total=42,parent_total=22,
    goal_status='ACTIVE',counter_reset=False,
    next_actions=['Adopt only independently reviewed legacy test fixture under Root ownership.',
      'Close three consumed Native scopes and register contiguous diagnostic suffix using current CP/OW CAS.',
      'Prepare independently qualified current Source Native producer, including C19, and fresh current CM40 consumers.',
      'Continue independently accepted public21 Source caller without borrowing historical Root scope.']))
handoff=R/'execution/v2.4/HANDOFF_RESUME_PACK.md'; old=handoff.read_bytes()
save('historical.HANDOFF.before-native-closed.cp376.live1134.root.md',old,True)
prefix=('# Current Root continuation: CP376 / OW180 / CM40 / live next1134\n\n'
    'All three Native jobs ended and all guards/jobs closed. G01 independently qualified for its existing source; G02/A06 actual Go1 caused by gapped legacy fixture. The corrected fixture has independent Source review and awaits Main adoption. New Source21 evidence is required after adoption. Formal0/42; Goal ACTIVE; no counter reset.\n\n'
    'Current resume: '+resume_ref['path']+'\nSHA256 '+resume_ref['sha256']+' bytes '+str(resume_ref['bytes'])+'\n\n').encode()
with handoff.open('wb') as f:
    f.write(prefix+old);f.flush();os.fsync(f.fileno())
assert handoff.read_bytes().endswith(old) and all(pin(x['path'])==x for x in current)
print(json.dumps(dict(original1131_raw_ref=raw_ref,original1131_binding_ref=binding_ref,
    resume_ref=resume_ref,canonical_unchanged=True,no_inflight_native_sessions=True,
    formal_acceptance=False,counter_reset=False),ensure_ascii=False))
