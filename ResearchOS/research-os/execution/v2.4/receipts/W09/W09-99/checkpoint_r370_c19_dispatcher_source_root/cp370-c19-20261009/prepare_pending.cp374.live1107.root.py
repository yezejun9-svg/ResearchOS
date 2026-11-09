"""Keep the complete newly observed diagnostic suffix before W09 registration."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in
    {'pin','save','exact','outputs','capture'}],type_ignores=[]),'Root_helper_functions_only','exec'),globals())
def document(ref):exact(Path(ref['path']),ref['sha256'],ref['bytes']);return json.loads(Path(ref['path']).read_bytes())
def verified_pair(raw_ref,binding_ref):
    binding=document(binding_ref);exact(Path(raw_ref['path']),raw_ref['sha256'],raw_ref['bytes'])
    lines=Path(raw_ref['path']).read_bytes().splitlines(keepends=True)
    assert len(lines)==3 and [len(x) for x in lines]==binding['source_line_bytes']
    assert [hashlib.sha256(x).hexdigest() for x in lines]==binding['original_line_sha256']
    with Path(binding['source_audit_path']).open('rb') as f:
        for off,line in zip(binding['source_line_offsets'],lines):
            assert off+len(line)<=binding['source_prefix_size_observed'];f.seek(off);assert f.readline()==line
    first,last=[json.loads(x) for x in lines[1:]]
    assert first['payload']['call_id']==last['payload']['call_id']==binding['original_call_id']
    return binding,last
prior=json.loads((N/'pending-diagnostics.cp374.live1102.root.json').read_bytes());rows=list(prior['pending'])
assert [r['ordinal'] for r in rows]==list(range(1097,1102))
D=B/'schema21_programme_actual_independent_review_codex/actual-old21-20261010-01'
raw1102=exact(D/'failure-1102.actual-host.raw.jsonl','157a021afbb5efefac8ca9dede18248c4b6b1b45d16a011d43458753ae7a4979',56392)
binding1102=exact(D/'failure-1102.actual-host.binding.json','c9c88e0c89d7268aa130615ab21e8da07959bd317159dc3bf62197089aa0a9a9',1808)
binding,_=verified_pair(raw1102,binding1102)
event_ref=binding['command_event_ref'];event=document(event_ref)
assert event['payload']['item']['exit_code']==1 and event['payload']['item']['status']=='failed'
with Path(binding['source_audit_path']).open('rb') as f:
    f.seek(binding['command_event_offset']);assert f.readline()==Path(event_ref['path']).read_bytes()
items=[(1102,raw1102,binding1102,1,None,'$','Independent actual reviewer treated a genuine top-level inventory list as a dict. Outer1 is bound to the complete original CommandExecution event; the original API omitted chunk and Python marker, both remain NULL.')]
consumer_ref=exact(B/'old21_programme_consumer_readonly_codex/consumer-20261010-01/consumer-readonly-result.json',
    '88ed83568c104afb9f4034695b67dec41f036b97d2edf707394e1947b724bbe0',10619)
consumer=document(consumer_ref)
assert [x['ordinal'] for x in consumer['diagnostics']]==[1103,1104,1105]
for item in consumer['diagnostics']:
    binding,last=verified_pair(item['raw_ref'],item['binding_ref'])
    origin=document(item['origin_ref']);document(item['io_ref'])
    hosts=[x for x in outputs(last['payload']['output']) if x.get('chunk_id')==item['chunk']]
    assert len(hosts)==1 and hosts[0]['exit_code']==origin['actual_outer_exit']==1
    assert origin['actual_python_exit'] is None
    items.append((item['ordinal'],item['raw_ref'],item['binding_ref'],1,None,'$',
        'Read-only programme consumer analysis original '+item['chunk']+': missing tools directory / guessed HDF path / PowerShell parser error. Exact original truncation and unobserved inner/product exits retained; no business calls.'))
def root1106(call,result):return any(x.get('chunk_id')=='c2428f' for x in outputs(result['payload'].get('output')))
pair=capture(AUDIT,1106,root1106,root=True);assert pair
binding,last=verified_pair(*pair)
hosts=[x for x in outputs(last['payload']['output']) if x.get('chunk_id')=='c2428f']
assert len(hosts)==1 and hosts[0]['exit_code']==0 and 'ROOT_SOURCE_PYTHON_EXIT=0' in hosts[0]['output']
items.append((1106,*pair,0,0,'$','Root prematurely enumerated an authorized future diagnostic directory before it existed; the same invocation subsequently read the already-existing command event successfully. Actual host/Python0/0, standalone rg exit not observed; product exits NULL.'))
for ordinal,raw_ref,binding_ref,outer,python,selector,description in items:
    standard=save('original%d.standard-binding.live1107.root.json'%ordinal,dict(schema='researchos.root-original-diagnostic-binding.v1',
        issued_by='codex:/root',original_capture_ref=raw_ref,original_source_binding_ref=binding_ref,
        original_source_binding_selector='$',original_ordinal=ordinal,original_bytes_unchanged=True,formal_authority=False))
    rows.append(dict(ordinal=ordinal,origin_ref=raw_ref,origin_selector=selector,capture_binding_ref=standard,
        description=description,capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',actual_outer_exit=outer,actual_python_exit=python,
        actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
assert [r['ordinal'] for r in rows]==list(range(1097,1107))
assert len({(r['origin_ref']['sha256'],r['origin_selector']) for r in rows})==len(rows)
for ref in prior['current_canonical_refs']:exact(Path(ref['path']),ref['sha256'],ref['bytes'])
pending=save('pending-diagnostics.cp374.live1107.root.json',dict(prior,pending=rows,next_original_failure_ordinal=1107,
    registered_in_current_canon=False,counter_reset=False,created_utc=datetime.now(timezone.utc).isoformat()))
print(json.dumps(dict(pending_ref=pending,pending_rows=len(rows),next_original_failure_ordinal=1107,
    Canon_unchanged=True,formal_acceptance=False),ensure_ascii=False,indent=2))
