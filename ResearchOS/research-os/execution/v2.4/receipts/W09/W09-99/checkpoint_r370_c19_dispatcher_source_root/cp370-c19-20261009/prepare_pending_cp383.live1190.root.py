"""Preserve five original observations; no product execution or Canon writes."""
from pathlib import Path
import hashlib,json,os,re,sys,types
S=Path(__file__).resolve().parent
R=Path(r'D:\作品集\ResearchOS\research-os');W=R/'execution/v2.4/receipts/W09/W09-99'
V=R/'execution/v2.4'
def pin(p):
    b=Path(p).read_bytes();return dict(path=str(Path(p)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(p):return json.loads(Path(p).read_bytes())
def docs(v):
    if isinstance(v,dict):
        yield v
        for x in v.values():yield from docs(x)
    elif isinstance(v,list):
        for x in v:yield from docs(x)
    elif isinstance(v,str):
        try:yield from docs(json.loads(v))
        except ValueError:pass
def save(p,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return pin(p)
q=W/'w09_nf6_root_registration_root/e38d72def3e1427cb9ef0b49dc130ba1/native.canonical-vector.json'
current=doc(q)['refs'];assert [pin(x['path']) for x in current]==current
assert doc(current[0]['path'])['revision']==383
refs={1185:(W/'w09_formal_root_bridge_source_codex/bridge-20261010-05/original-1185.binding.json',1,None,'Full Source-only rg queried an absent ops/ci/formal_case_index.py; no product invocation.'),
      1186:(W/'w09_formal_root_bridge_independent_source_review_codex/review-20261010-05-attach/original-1186.binding.json',0,None,'Independent Source review read an absent calling-contract.json instead of the published root-calling-contract.source.json; PowerShell host returned0 with read error.'),
      1187:(W/'w09_formal_root_bridge_independent_source_review_codex/review-20261010-05-attach/original-1187.binding.json',0,None,'Independent Source review passed an unexpanded wildcard path to rg; path error123 retained although compound PowerShell host returned0.'),
      1188:(W/'w09_formal_root_bridge_independent_source_review_codex/review-20261010-05-attach/original-1188.binding.json',1,1,'Independent Source review original-observation sealer misidentified its initial call; successful prior pure controls retained, corrected seal separately.'),
      1189:(S/'original1189.actual-root.binding.json',1,None,'Root read-only rg query included an absent producer-choice.json; rg path error2, no Python or product invocation.')}
rows=[];facts=[]
for ordinal,(path,outer,py,description) in refs.items():
    br=pin(path);b=doc(path);assert b['original_ordinal']==ordinal and b['actual_outer_exit']==outer and b['actual_python_exit']==py
    rr=b.get('original_raw_ref',b.get('original_capture_ref'));assert rr and pin(rr['path'])==rr
    raw=Path(rr['path']).read_bytes();lines=raw.splitlines(keepends=True);assert len(lines)==3
    assert [hashlib.sha256(x).hexdigest() for x in lines]==b['original_line_sha256']
    sizes=b.get('original_line_bytes',b.get('source_line_bytes'));assert sizes==[len(x) for x in lines]
    events=[json.loads(x) for x in lines];assert events[0]['payload']['id']==b.get('actor_thread_id',b.get('root_thread_id'))
    assert events[1]['payload']['call_id']==events[2]['payload']['call_id']==b.get('actual_call_id',b.get('original_call_id'))
    with Path(b['source_audit_path']).open('rb') as f:
        for offset,line in zip(b['source_line_offsets'],lines):
            assert offset+len(line)<=b['source_prefix_size_observed'];f.seek(offset);assert f.readline()==line
        host=b.get('host_event_ref')
        if host:
            assert pin(host['path'])==host
            event_raw=Path(host['path']).read_bytes();f.seek(b['host_event_offset']);assert f.readline()==event_raw
            assert json.loads(event_raw)['ordinal']==b['host_event_ordinal']
            facts.append(host)
    if not host:
        chunk=b.get('actual_chunk_id',b.get('actual_host_chunk_id'))
        hosts=[x for x in docs(events[2]['payload'].get('output')) if x.get('chunk_id')==chunk]
        assert len(hosts)==1 and hosts[0]['exit_code']==outer
    values=dict(actual_outer_exit=outer,actual_python_exit=py,actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None)
    rows.append(dict(ordinal=ordinal,origin_ref=rr,origin_selector='$',capture_binding_ref=br,description=description,capture_completeness='ACTUAL_ORIGINAL_3LF_WITH_SEPARATE_SAVED_HOST_EVENT' if host else 'ACTUAL_HOST_ORIGINAL_PAIR',source_fact_refs=[br,rr]+([host] if host else []),**values))
    facts.extend([br,rr])
pending=dict(schema='researchos.root-pending-diagnostics.v1',issued_by='codex:/root',counter_reset=False,registered_in_current_canon=False,current_canonical_refs=current,source_cutoff_original_failure_ordinal=1184,next_original_failure_ordinal=1190,pending=rows)
core_path=W/'w09_nf6_root_registration_source_codex/register-20261010-01/adoption_core.source.py'
assert pin(core_path)['sha256']=='2c99ef66d3ee2c25302858fef715ad46096c750bd5ebff58faa95f0cdd4ead4f'
core=types.ModuleType('root_pending_cp383');core.__file__=str(core_path);sys.modules[core.__name__]=core
exec(compile(core_path.read_bytes(),str(core_path),'exec'),core.__dict__)
cp=doc(current[0]['path']);merged,stop=core.merge_pending(cp,pending,current)
assert merged[:len(cp['failure_counters'])]==cp['failure_counters'] and len(merged)==len(cp['failure_counters'])+5 and stop==1190
pr=save(S/'pending-diagnostics.cp383.live1190.root.json',pending)
vr=save(S/'pending-diagnostics.cp383.live1190.verified.root.json',dict(schema='researchos.root-original-diagnostic-suffix-verification.v1',issued_by='codex:/root',pending_ref=pr,complete_original_3LF_verified=True,separate_host_events_verified=True,source_fact_refs=facts,old_counter_prefix_unchanged=True,registered=False,Canon_written=False,product_calls=0))
print(json.dumps(dict(pending_ref=pr,verification_ref=vr,next_original_failure_ordinal=1190,Canon_written=False),ensure_ascii=False))
