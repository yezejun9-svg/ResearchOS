"""Register the verified contiguous diagnostic suffix without changing scopes."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, os, sys, types
R=Path(r'D:\作品集\ResearchOS\research-os');V=R/'execution/v2.4';S=Path(__file__).resolve().parent;W=V/'receipts/W09/W09-99';B=V/'receipts/W05/W05-99'
CORE=W/'w09_nf6_root_registration_source_codex/register-20261010-01/adoption_core.source.py'
GUARD=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
TP=B/'mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'
O=S/'cp389-diagnostics1219-1222-live1223'
def pin(p):
    p=Path(p);b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(p):return json.loads(Path(p).read_bytes())
def module(p,name):
    m=types.ModuleType(name);m.__file__=str(p);sys.modules[name]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def save(p,v):
    b=(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    return pin(p)
current=[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')]
assert current[0]['sha256']=='7bef318e221b4425dca2952103710bad294e9aa0baa8770afac702a648a980ef'
assert current[1]['sha256']=='bfecdb5269bf10d27264cc66bfe92454b3930e11e67b90059385dcf7aafcef01'
assert doc(current[0]['path'])['work_in_progress']['root_next_failure_ordinal_live']==1219
assert pin(CORE)['sha256']=='2c99ef66d3ee2c25302858fef715ad46096c750bd5ebff58faa95f0cdd4ead4f'
assert pin(GUARD)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
assert pin(TP)['sha256']=='094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9'
fixed={n:B/f'public22_to_main23_continuation_independent_review_codex/review-20261010-04-full/original-{n}.binding.json' for n in (1219,1220)}
fixed[1221]=S/'original1221.fixed-actual.binding.root.json'
fixed[1222]=S/'original1222.fixed-actual.binding.root.json'
descriptions={1222:'Root genuine Source04 peer capture rejected real metadata and adjacent Final one-millisecond timestamp difference; original pair and source acceptance retained; no product.',1219:'Independent Source04 review fixture treated persisted failure_counters list as dict; seven successful controls retained.',1220:'Independent Source04 reviewer used typed ref predicate on true Markdown Source publication; twelve generation controls retained; caller unchanged.',1221:'Root BR7 seed process exact TEMP string spelling refused before output or SourceGuard acquisition; no Native; corrected Windows exact parent then completed seed0 with the same unconsumed request.'}
rows=[];refs=[pin(CORE),pin(GUARD),pin(TP),*current[2:]]
for n in range(1219,1223):
    br=pin(fixed[n]);b=doc(fixed[n]);rr=b.get('original_capture_ref',b.get('original_raw_ref'));assert pin(rr['path'])==rr
    raw=Path(rr['path']).read_bytes();lines=raw.splitlines(keepends=True);assert len(lines)==3
    assert [hashlib.sha256(x).hexdigest() for x in lines]==b['original_line_sha256']
    with Path(b['source_audit_path']).open('rb') as f:
        for off,line in zip(b['source_line_offsets'],lines):f.seek(off);assert f.readline()==line
    events=[json.loads(x) for x in lines];assert events[1]['payload']['call_id']==events[2]['payload']['call_id']
    chunk=b.get('actual_host_chunk_id',b.get('actual_chunk_id'));assert type(chunk) is str and chunk
    facts=[br,rr]
    if 'host_event_ref' in b:
        h=b['host_event_ref'];assert pin(h['path'])==h;facts.append(h)
    outer=b['actual_outer_exit'];py=b['actual_python_exit'];assert outer==1
    assert py==1
    rows.append(dict(ordinal=n,origin_ref=rr,origin_selector='actual_host_chunk_id='+chunk,capture_binding_ref=br,description=descriptions[n],capture_completeness='ACTUAL_ORIGINAL_HEADER_CALL_RESULT_3LF_WITH_EXACT_SOURCE_OFFSETS',source_fact_refs=facts,actual_outer_exit=outer,actual_python_exit=py,actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
    refs.extend(facts)
pending=dict(schema='researchos.root-pending-diagnostics.v1',issued_by='codex:/root',counter_reset=False,registered_in_current_canon=False,current_canonical_refs=current,source_cutoff_original_failure_ordinal=1218,next_original_failure_ordinal=1223,pending=rows)
assert not O.exists();O.mkdir();(O/'canonical-journal').mkdir()
pending_ref=save(O/'pending-diagnostics.root.json',pending);refs.append(pending_ref)
refs=list({x['path']:x for x in refs}.values());assert not any(x['path'] in [r['path'] for r in current[:2]] for x in refs)
g=module(GUARD,'root_cp388_diagnostic_guard').SourceReadGuard(per_file_cap=64*1024*1024,total_cap=256*1024*1024)
try:
    g.acquire(refs);core=module(CORE,'root_cp388_diagnostic_core');tp=module(TP,'root_cp388_diagnostic_tp');now=datetime.now(timezone.utc).isoformat()
    def transform(cp,ow):
        assert cp['revision']==388 and ow['revision']==192
        c=copy.deepcopy(cp);o=copy.deepcopy(ow);co=[];oo=[]
        def change(d,ops,path,value):
            exists,before=core.value_at(d,path);ops.append(dict(path=path,before_exists=exists,before=before,after=copy.deepcopy(value)));core.put(d,path,value)
        merged,end=core.merge_pending(cp,pending,current);assert end==1223 and merged[:len(cp['failure_counters'])]==cp['failure_counters']
        change(c,co,['failure_counters'],merged);change(c,co,['work_in_progress','root_next_failure_ordinal_live'],end)
        change(c,co,['work_in_progress','cp389_diagnostic_suffix_registered'],dict(pending_ref=pending_ref,registered_through=1222,live_next_original_failure_ordinal=1223,counter_reset=False,Scope_unchanged=True,formal_acceptance=False))
        for key,val in dict(revision=389,expected_previous_revision=388,updated_at=now,updated_by='codex:/root',note='Append actual diagnostic suffix once; preserve all old scopes and failure rows. Reviewed Main tuple conversion integrated; BR7 Source independent review pending.').items():change(c,co,[key],val)
        for key,val in dict(revision=193,updated_at=now,updated_by='codex:/root').items():change(o,oo,[key],val)
        assert c['workers']==cp['workers'] and o['card_path_bindings']==ow['card_path_bindings']
        assert core.inverse_operations(c,co)==cp and core.inverse_operations(o,oo)==ow
        save(O/'complete-changes-and-inverse.root.json',dict(checkpoint_operations=co,ownership_operations=oo,complete_structural_inverse=True))
        return c,o
    result=tp.update_pair(current[:2],transform,str(O/'canonical-journal'),'close')
    result_ref=save(O/'closure.committed.root.json',dict(result,registered_through=1222,next_original_failure_ordinal=1223,formal_acceptance=False,counter_reset=False,Scope_unchanged=True))
finally:
    closed=g.close();guard_ref=save(O/'source-guard.closed.root.json',closed)
assert closed['closed'] and not closed['errors'] and closed['retained_handles_count']==0
assert all(pin(x['path'])==x for x in current[2:])
print(json.dumps(dict(closure_ref=result_ref,source_guard_closed_ref=guard_ref,after_canonical_refs=[pin(V/n) for n in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')],registered_through=1222,next_original_failure_ordinal=1223,Scope_unchanged=True,formal_acceptance=False),ensure_ascii=False))
