"""Consume the observed failed one-shot W05 scope and append true diagnostics."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, os, sys, types
R=Path(r'D:\作品集\ResearchOS\research-os');V=R/'execution/v2.4';S=Path(__file__).resolve().parent;W=V/'receipts/W09/W09-99';B=V/'receipts/W05/W05-99'
CORE=W/'w09_nf6_root_registration_source_codex/register-20261010-01/adoption_core.source.py'
GUARD=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
TP=B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'
CASE=B/'integration_codex/public22-continuation-fe9482816efe4843ba728962d99ee06c/case.closed.json'

def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def doc(p):return json.loads(Path(p).read_bytes())
def module(p,name):
    m=types.ModuleType(name);m.__file__=str(p);sys.modules[name]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def save(p,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return pin(p)

current=[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
assert current[0]['sha256']=='43d5bcd2b12d45d0438b091a318c4c7552bccdda7cce141d4d37220b2f45d986'
assert current[1]['sha256']=='17c507bf39e0890c244eb318ae27d3f24fe87a2aa884986f6191e10963ae305a'
cp=doc(current[0]['path']);assert cp['revision']==385 and cp['work_in_progress']['root_next_failure_ordinal_live']==1192
case_ref=pin(CASE);assert case_ref['sha256']=='b663b3b63259da289805e01d948887777ff36bcefd8cdf7bcc174fd496aacb6c'
case=doc(CASE);closed=case['source_guard_cleanup']
assert case['status']=='STOPPED_AT_FIRST_FAILURE' and case['first_failure']['phase']=='prepare' and case['first_failure']['message']=='COPIED22_LOGICAL_STATE'
assert case['calls']==[] and case['new_native_children_attempted']==0 and case['original_four_children_replayed'] is False
assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
assert pin(CORE)['sha256']=='2c99ef66d3ee2c25302858fef715ad46096c750bd5ebff58faa95f0cdd4ead4f'
assert pin(GUARD)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
assert pin(TP)['sha256']=='094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9'
fixed={n:S/f'original{n}.fixed-actual.binding.root.json' for n in (1192,1193,1196,1200,1203,1204)}
fixed.update({1194:S/'w09.original1194-bundle-metadata.actual-audit.root.json',1195:S/'w09.original1195-closure-metadata.actual-audit.root.json',1199:S/'w09.original1199-request-metadata.actual-audit.root.json',1202:S/'w09.original1202-capture-metadata.actual-audit.root.json',1201:S/'w05-continuation-fe948281-execute-completed.host-pair.root.json'})
A=W/'w09_br6_seed_input_preparation_codex/prepare-20261010-01'
fixed.update({n:A/f'original-{n}.binding.json' for n in (1197,1198)})
descriptions={1192:'Reviewer extra completion-publication assumption rejected; successful G01 prefix retained.',1193:'Read-only rg unescaped regex; PowerShell outer0, rg inner unknown.',1194:'Root metadata wrong published reviewer filename; no product calls.',1195:'Root closure metadata expected original_error instead of actual exception; before any TP mutation.',1196:'Reviewer progress recursive JSON duplicate assumption; successful prefix retained.',1197:'Read-only seed input wrong filename/parent path; no product calls.',1198:'Read-only seed input used W05 instead of published W09 folder; no product calls.',1199:'Root request metadata stdout JSON framing assumption; no request or product calls.',1200:'Reviewer SourceGuard constructor cap mismatch before acquire or Mode publication.',1201:'W05 actual prepare stopped at COPIED22_LOGICAL_STATE; zero Native children; old scope consumed.',1202:'Root capture stdout framing assumption; actual initial capture retained.',1203:'Root capture matched diagnostic JSON instead of typed actual host; no product calls.',1204:'Root artifact audit binding rejected unmatched digest; invalid artifact authority is excluded.'}
rows=[];refs=[case_ref,pin(CORE),pin(GUARD),pin(TP),*current[2:]]
py_exits={1192:1,1193:None,1194:1,1195:1,1196:1,1197:None,1198:None,1199:1,1200:None,1201:1,1202:None,1203:1,1204:1}
outer_exits={n:(0 if n==1193 else 1) for n in range(1192,1205)}
for n in range(1192,1205):
    b_ref=pin(fixed[n]);b=doc(fixed[n]);raw_ref=b.get('original_capture_ref',b.get('original_raw_ref'));assert pin(raw_ref['path'])==raw_ref
    lines=Path(raw_ref['path']).read_bytes().splitlines(keepends=True);assert len(lines)==3
    assert [hashlib.sha256(x).hexdigest() for x in lines]==b['original_line_sha256']
    with Path(b['source_audit_path']).open('rb') as f:
        for offset,line in zip(b['source_line_offsets'],lines):f.seek(offset);assert f.readline()==line
    events=[json.loads(x) for x in lines];assert events[1]['payload']['call_id']==events[2]['payload']['call_id']
    facts=[b_ref,raw_ref]
    if 'host_event_ref' in b:
        h=b['host_event_ref'];assert pin(h['path'])==h;facts.append(h)
    if n==1201:facts.extend([case_ref,pin(S/'w05-continuation-fe948281-execute-initial.host-pair.root.json')])
    rows.append(dict(ordinal=n,origin_ref=raw_ref,origin_selector='$',capture_binding_ref=b_ref,description=descriptions[n],capture_completeness='ACTUAL_ORIGINAL_HEADER_CALL_RESULT_3LF_WITH_EXACT_SOURCE_OFFSETS',source_fact_refs=facts,actual_outer_exit=outer_exits[n],actual_python_exit=py_exits[n],actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
    refs.extend(facts)
pending=dict(schema='researchos.root-pending-diagnostics.v1',issued_by='codex:/root',counter_reset=False,registered_in_current_canon=False,current_canonical_refs=current,source_cutoff_original_failure_ordinal=1191,next_original_failure_ordinal=1205,pending=rows)
O=S/'cp386-w05-failed-scope-consumed-live1206';assert not O.exists();O.mkdir();(O/'canonical-journal').mkdir()
pending_ref=save(O/'pending-diagnostics.root.json',pending);refs.append(pending_ref)
refs=list({x['path']:x for x in refs}.values());assert not any(x['path'] in [r['path'] for r in current[:2]] for x in refs)
g=module(GUARD,'root_w05_failed_scope_guard').SourceReadGuard(per_file_cap=64*1024*1024,total_cap=256*1024*1024)
try:
    g.acquire(refs);core=module(CORE,'root_w05_failed_scope_core');tp=module(TP,'root_w05_failed_scope_tp');now=datetime.now(timezone.utc).isoformat()
    def transform(cp,ow):
        assert cp['revision']==385 and ow['revision']==189
        c=copy.deepcopy(cp);o=copy.deepcopy(ow);co=[];oo=[]
        def change(d,ops,path,value):
            exists,before=core.value_at(d,path);ops.append(dict(path=path,before_exists=exists,before=before,after=copy.deepcopy(value)));core.put(d,path,value)
        merged,end=core.merge_pending(cp,pending,current);assert end==1205 and merged[:len(cp['failure_counters'])]==cp['failure_counters']
        change(c,co,['failure_counters'],merged);change(c,co,['work_in_progress','root_next_failure_ordinal_live'],end)
        workers=copy.deepcopy(cp['workers']);matches=[x for x in workers if x.get('slice_id')=='PUBLIC22_TO_MAIN23_CONTINUATION'];assert len(matches)==1
        worker=matches[0];key='public22_to_main23_continuation';sub=copy.deepcopy(ow['card_path_bindings']['W05-99']['subtasks'][key]);assert worker['scope_ref']==sub['scope_ref']
        assert worker['state']==sub['state']=='ROOT_REGISTERED_PUBLIC22_TO_MAIN23_CONTINUATION'
        actual=dict(case_closed_ref=case_ref,actual_request_ref=case['actual_request_ref'],completed_Root_host_capture_ref=pin(fixed[1201]),actual_outer_exit=1,actual_python_exit=1,actual_native_exit=None,Native_children_attempted=0,first_failure_original_ordinal=1201,first_failure=case['first_failure'],Source_guard_closed_zero=True,automatic_retry=False,formal_acceptance=False)
        values=dict(state='CLOSED_ACTUAL_PREPARE_FAILED_NO_NATIVE',closed_at=now,lease_status='CONSUMED',one_shot_consumed=True,future_execution_permitted=False,actual_closed=actual,formal_acceptance=False)
        worker.update(values);sub.update(values);change(c,co,['workers'],workers);change(o,oo,['card_path_bindings','W05-99','subtasks',key],sub)
        change(c,co,['work_in_progress','cp386_w05_failed_scope_consumed'],dict(actual_closed=actual,pending_ref=pending_ref,registered_through=1204,canonical_next_original_failure_ordinal=1205,live_next_original_failure_ordinal=1206,original1205_pending_source_capture=True,counter_reset=False,formal_acceptance=False))
        for key,val in dict(revision=386,expected_previous_revision=385,updated_at=now,updated_by='codex:/root',note='Consume W05 actual prepare failure with zero Native children; preserve original diagnostics once and allow only a new reviewed Source/new Root scope.').items():change(c,co,[key],val)
        for key,val in dict(revision=190,updated_at=now,updated_by='codex:/root').items():change(o,oo,[key],val)
        assert core.inverse_operations(c,co)==cp and core.inverse_operations(o,oo)==ow
        save(O/'complete-changes-and-inverse.root.json',dict(checkpoint_operations=co,ownership_operations=oo,complete_structural_inverse=True))
        return c,o
    result=tp.update_pair(current[:2],transform,str(O/'canonical-journal'),'close')
    result_ref=save(O/'closure.committed.root.json',dict(result,registered_through=1204,next_original_failure_ordinal=1205,live_next_original_failure_ordinal=1206,formal_acceptance=False,counter_reset=False))
finally:
    closed=g.close();guard_ref=save(O/'source-guard.closed.root.json',closed)
assert closed['closed'] and not closed['errors'] and closed['retained_handles_count']==0
assert all(pin(x['path'])==x for x in current[2:])
print(json.dumps(dict(closure_ref=result_ref,source_guard_closed_ref=guard_ref,after_canonical_refs=[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')],registered_through=1204,next_original_failure_ordinal=1205,live_next_original_failure_ordinal=1206,formal_acceptance=False),ensure_ascii=False))
