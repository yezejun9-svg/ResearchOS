"""Archive the registered pair and bind the actual Root build request."""
from pathlib import Path
import json,hashlib,os
N=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os');V=R/'execution/v2.4'
reg=V/'receipts/W05/W05-99/integration_codex/fresh-main23-registration-3ef8ee61a94e4adca86a00f55a8b7a13'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def exact(p,sha,size):
    a=pin(p);assert (a['sha256'],a['bytes'])==(sha,size);return a
def save(name,v):
    p=N/name
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return pin(p)
activate_ref=exact(reg/'activate.result.json','95df4764c2114a86d2fb15cdad578c9f99efb378f6585fec84afb3e6aee0cb25',3261)
activation=json.loads(Path(activate_ref['path']).read_bytes())
cleanup=json.loads((reg/'activate.guard-cleanup.json').read_bytes())
assert cleanup['closed'] and cleanup['retained_handles_count']==0 and not cleanup['errors']
assert activation['complete_inverse'] and activation['SS_CM_unchanged'] and activation['mode']=='activate'
refs=[];docs=[];archives=[]
for name in ('checkpoint','path_ownership','step_state','commands'):
    p=V/(name+'.json');raw=p.read_bytes();refs.append(pin(p));docs.append(json.loads(raw))
    archive=N/('historical.cp373.'+name+'.json')
    with archive.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    archives.append(pin(archive))
assert [d.get('revision') for d in docs]==[373,177,None,39]
assert len(docs[0]['failure_counters'])==1064 and docs[0]['work_in_progress']['root_next_failure_ordinal_live']==1067
assert refs[:2]==activation['proposed_after_refs']
scope_ref=activation['scope_ref'];facts_ref=activation['facts_ref']
scope=json.loads(Path(scope_ref['path']).read_bytes())
q=json.loads(Path(scope['registration_request_ref']['path']).read_bytes())
assert refs[2:]==q['before_canonical_refs'][2:]
intent=save('main23.v4.actual.host-call-intent.root.json',dict(
    issued_by='codex:/root',root_thread_id=THREAD,kind='ACTUAL_HOST_CALL_INTENT',
    external_hostpair_required=True,scope_ref=scope_ref,case_request_ref=q['case_request_ref']))
actual=save('main23.v4.actual-request.root.json',dict(
    schema='researchos.root-main23-actual-request.v1',issued_by='codex:/root',formal_acceptance=False,
    scope_ref=scope_ref,facts_ref=facts_ref,case_request_ref=q['case_request_ref'],
    current_canonical_refs=refs,registration_result_ref=activate_ref,host_call_intent_ref=intent,
    runtime_qualification_ref=q['runtime_qualification_ref']))
observed=save('main23.v4.activation-after.current4.actual.root.json',dict(
    issued_by='codex:/root',root_thread_id=THREAD,current_canonical_refs=refs,archive_refs=archives,
    expected_revisions=dict(checkpoint=373,path_ownership=177,step_state=None,commands=39),
    activation_result_ref=activate_ref,scope_ref=scope_ref,facts_ref=facts_ref,
    actual_request_ref=actual,original_next_failure_ordinal=1067,formal_acceptance=False))
print(json.dumps(dict(actual_request_ref=actual,observed_ref=observed,current_canonical_refs=refs,
    scope_ref=scope_ref,facts_ref=facts_ref,original_next_failure_ordinal=1067),ensure_ascii=False,indent=2))
