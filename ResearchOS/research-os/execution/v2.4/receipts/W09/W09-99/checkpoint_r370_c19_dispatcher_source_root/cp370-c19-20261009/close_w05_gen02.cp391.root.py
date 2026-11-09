"""Consume completed GEN02 and append its actual diagnostic suffix once."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, os, sys, types
S=Path(__file__).resolve().parent;V=S.parents[4];W=S.parents[1];B=V/'receipts/W05/W05-99'
CORE=W/'w09_nf6_root_registration_source_codex/register-20261010-01/adoption_core.source.py'
GUARD=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
TP=B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'
CASE=B/'integration_codex/public22-continuation-862bd0e97cad44eab8e28b37f8063f20/case.closed.json'
O=S/'cp392-w05-gen02-consumed-diagnostics1236-live1237'
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def checked(r):
    p=Path(r['path']);assert pin(p)==r;return p.read_bytes()
def doc(r):return json.loads(checked(r))
def save(p,v):
    raw=(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
    with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return pin(p)
def module(p,n):
    m=types.ModuleType(n);m.__file__=str(p);sys.modules[n]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
assert len(sys.argv)==2
q=json.loads(Path(sys.argv[1]).read_bytes());assert q['issued_by']=='codex:/root' and q['formal_acceptance'] is False
current=[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
assert current[0]['sha256']=='39b39df749a254c0d7fec9d3681c9cbf8823020777b707703e16f6ffe53c2914'
assert current[1]['sha256']=='84fe1993de7695b46a815e5835273e660b890d5b1c46800c875c49e7e3f68a72'
for p,h in ((CORE,'2c99ef66d3ee2c25302858fef715ad46096c750bd5ebff58faa95f0cdd4ead4f'),(GUARD,'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'),(TP,'094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9')):assert pin(p)['sha256']==h
case_ref=pin(CASE);assert case_ref['sha256']=='2fe607aa52fe6beceaa45e2791d56f8d9d2825e074fbd4ea3ed0bcb6444bd70a';case=doc(case_ref)
assert case['status']=='THREE_PUBLIC_PHASES_OBSERVED_PENDING_INDEPENDENT_REVIEW' and case['new_native_children_attempted']==3
assert case['first_failure'] is None and not case['secondary_errors'] and case['original_four_children_replayed'] is False
assert case['full20to24']=='OPEN' and case['formal_acceptance'] is case['parent_acceptance'] is False
assert [c['phase'] for c in case['calls']]==['upgrade22to23','backup23','verify23']
for c in case['calls']:
    assert c['actual_exit']==c['observation']['actual_exit']==0 and not c['observation']['timed_out'] and c['observation']['error'] is None
    j=c['observation']['job_cleanup'];assert j['assigned_before_resume'] and j['job_idle_confirmed'] and j['primary_exit_confirmed'] and j['handles_closed'] and j['active_processes_last_observed']==0 and not j['errors']
closed=case['source_guard_cleanup'];assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
for k in ('review_decision_ref','review_hdf_ref','review_mf_ref','review_delivery_audit_ref','pending_diagnostics_ref'):checked(q[k])
review=doc(q['review_decision_ref']);assert review['verdict']==q['expected_review_decision']=='QUALIFIED_COMPONENT_ONLY' and review['formal_acceptance'] is False
assert review['independent_non_author'] is True and review['backend_actor_id']=='/root/full_w09_source_review' and review['source_author']=='codex:/root/attach_restore_independent_review'
assert review['actual_case_closed_ref']==case_ref and review['current4_at_independent_review']==current and review['generation']=='GEN02'
for r in review['source_review_refs']:checked(r)
audit=doc(q['review_delivery_audit_ref']);assert audit['actor_id']=='codex:/root/full_w09_source_review'
raw_ref=audit['original_capture_ref'];raw=checked(raw_ref);lines=raw.splitlines(keepends=True);assert len(lines)==3
assert [hashlib.sha256(x).hexdigest() for x in lines]==audit['original_line_sha256']
events=[json.loads(x) for x in lines];assert events[1]['type']=='inter_agent_communication_metadata' and events[2]['payload']['author']=='/root/full_w09_source_review'
assert events[2]['ordinal']==events[1]['ordinal']+1 and events[2]['metadata']['client_authored'] is False and events[2]['timestamp']==events[1]['timestamp']
for k in ('review_decision_ref','review_hdf_ref','review_mf_ref'):assert q[k]['sha256'] in lines[2].decode('utf-8')
with Path(audit['source_audit_path']).open('rb') as f:
    for off,line in zip(audit['source_line_offsets'],lines):f.seek(off);assert f.readline()==line
pending=doc(q['pending_diagnostics_ref']);assert pending['current_canonical_refs']==current
refs=[pin(CORE),pin(GUARD),pin(TP),case_ref,raw_ref,*current[2:],*review['source_review_refs'],*[q[k] for k in ('review_decision_ref','review_hdf_ref','review_mf_ref','review_delivery_audit_ref','pending_diagnostics_ref')]]
for row in pending['pending']:
    for r in row['source_fact_refs']:checked(r);refs.append(r)
for name in ('w05-gen02-native-initial.host-pair.root.json','w05-gen02-native-complete.host-pair.root.json'):
    r=pin(S/name);d=doc(r);assert d['actual_outer_exit']==0 if 'complete' in name else d['actual_outer_exit'] is None
    refs.extend((r,d['original_capture_ref']))
refs=list({r['path']:r for r in refs}.values());assert not O.exists();O.mkdir();(O/'canonical-journal').mkdir()
g=module(GUARD,'root_gen02_close_guard').SourceReadGuard(per_file_cap=64*1024*1024,total_cap=256*1024*1024)
try:
    g.acquire(refs);core=module(CORE,'root_gen02_close_core');tp=module(TP,'root_gen02_close_tp');now=datetime.now(timezone.utc).isoformat()
    def transform(cp,ow):
        assert cp['revision']==391 and ow['revision']==195
        c=copy.deepcopy(cp);o=copy.deepcopy(ow);co=[];oo=[]
        def change(d,ops,path,value):
            exists,before=core.value_at(d,path);ops.append(dict(path=path,before_exists=exists,before=before,after=copy.deepcopy(value)));core.put(d,path,value)
        merged,end=core.merge_pending(cp,pending,current);assert end==1237 and merged[:len(cp['failure_counters'])]==cp['failure_counters']
        change(c,co,['failure_counters'],merged);change(c,co,['work_in_progress','root_next_failure_ordinal_live'],end)
        workers=copy.deepcopy(cp['workers']);matches=[x for x in workers if x.get('slice_id')=='PUBLIC22_TO_MAIN23_CONTINUATION_GEN02'];assert len(matches)==1
        worker=matches[0];key='public22_to_main23_continuation_gen02';sub=copy.deepcopy(ow['card_path_bindings']['W05-99']['subtasks'][key]);assert worker['scope_ref']==sub['scope_ref']
        assert worker['state']==sub['state']=='ROOT_REGISTERED_PUBLIC22_TO_MAIN23_CONTINUATION' and worker['lease_status']==sub['lease_status']=='ACTIVE'
        actual=dict(case_closed_ref=case_ref,independent_component_decision_ref=q['review_decision_ref'],independent_delivery_audit_ref=q['review_delivery_audit_ref'],actual_outer_exit=0,actual_python_exit=0,actual_native_exits=[0,0,0],Native_children_attempted=3,original_four_children_replayed=False,Source_guard_closed_zero=True,full20to24='OPEN',formal_acceptance=False)
        values=dict(state='CLOSED_ACTUAL_THREE_PUBLIC_PHASES_COMPONENT_REVIEWED',closed_at=now,lease_status='CONSUMED',one_shot_consumed=True,future_execution_permitted=False,actual_closed=actual,formal_acceptance=False)
        worker.update(values);sub.update(values);change(c,co,['workers'],workers);change(o,oo,['card_path_bindings','W05-99','subtasks',key],sub)
        change(c,co,['work_in_progress','cp392_w05_gen02_component_closed'],dict(actual_closed=actual,pending_ref=q['pending_diagnostics_ref'],registered_through=1236,live_next_original_failure_ordinal=1237,counter_reset=False,formal_acceptance=False))
        change(c,co,['work_in_progress','original1224_diagnosis_correction'],dict(first_rejected_pointer='/dependency_snapshot/audit_ranges/0',cause='TYPED_AUDIT_RANGE_PROMOTED_TO_WHOLE_FILE_REFERENCE',resource_marker_was_not_first_rejected=True,original_failure_retained=True))
        for k,v in dict(revision=392,expected_previous_revision=391,updated_at=now,updated_by='codex:/root',note='Consume completed W05 GEN02 after actual independent component review; preserve all prior failures and append the actual suffix once. Formal acceptance remains unchanged.').items():change(c,co,[k],v)
        for k,v in dict(revision=196,updated_at=now,updated_by='codex:/root').items():change(o,oo,[k],v)
        assert core.inverse_operations(c,co)==cp and core.inverse_operations(o,oo)==ow
        save(O/'complete-changes-and-inverse.root.json',dict(checkpoint_operations=co,ownership_operations=oo,complete_structural_inverse=True))
        return c,o
    result=tp.update_pair(current[:2],transform,str(O/'canonical-journal'),'close')
    receipt=save(O/'closure.committed.root.json',dict(result,registered_through=1236,next_original_failure_ordinal=1237,formal_acceptance=False,counter_reset=False))
finally:
    closed=g.close();gr=save(O/'source-guard.closed.root.json',closed)
assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
assert all(pin(Path(x['path']))==x for x in current[2:])
print(json.dumps(dict(closure_ref=receipt,source_guard_closed_ref=gr,after_canonical_refs=[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')],formal_acceptance=False),ensure_ascii=False))
