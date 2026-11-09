"""Retain new original diagnostics without mutating Canon or resetting counters."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, os
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in
    {'pin','save','exact','outputs','capture'}],type_ignores=[]),'Root_helper_functions_only','exec'),globals())
prior=json.loads((N/'pending-diagnostics.cp374.live1098.root.json').read_bytes());rows=list(prior['pending'])
assert [x['ordinal'] for x in rows]==[1097]
review=B/'old21_registered_state_readonly_review_codex/review-reg21-20261010-01'
raw_ref=exact(review/'original-1098.raw.jsonl','99a42f09dd3d3ccb98adea1b700f2886f6f936b917f8a8e37361ba68fd19d58a',43449)
binding_ref=exact(review/'original-1098.binding.json','8b76502edeb78657fbd34df188749f42e0ded9aded11c73bed6fb0a0e9dae340',1585)
binding=json.loads(Path(binding_ref['path']).read_bytes());raw=Path(raw_ref['path']).read_bytes();lines=raw.splitlines(keepends=True)
assert len(lines)==3 and [len(x) for x in lines]==binding['source_line_bytes']
assert [hashlib.sha256(x).hexdigest() for x in lines]==binding.get('original_line_sha256',binding.get('source_line_sha256'))
with Path(binding['source_audit_path']).open('rb') as f:
    for off,line in zip(binding['source_line_offsets'],lines):
        assert off+len(line)<=binding['source_prefix_size_observed'];f.seek(off);assert f.readline()==line
first,last=[json.loads(x) for x in lines[1:]]
assert first['payload']['call_id']==last['payload']['call_id']==binding.get('original_call_id',binding.get('actual_call_id'))
source_hosts=[x for x in outputs(last['payload']['output']) if x.get('chunk_id')=='bb8be2']
assert len(source_hosts)==1 and source_hosts[0]['exit_code']==1 and 'ROOT_SOURCE_PYTHON_EXIT=1' in source_hosts[0]['output']
def match(call,result):return any(x.get('chunk_id')=='d017e8' for x in outputs(result['payload'].get('output')))
root_pair=capture(AUDIT,1099,match,root=True);assert root_pair
root_result=json.loads(Path(root_pair[0]['path']).read_bytes().splitlines()[-1])
root_hosts=[x for x in outputs(root_result['payload']['output']) if x.get('chunk_id')=='d017e8']
assert len(root_hosts)==1 and root_hosts[0]['exit_code']==1
for ordinal,raw_ref,original_binding,python,selector,description in (
    (1098,raw_ref,binding_ref,1,'$','Independent read-only registration reviewer returned a set without converting it to a JSON list; original host/Python1/1 retained; fourteen prior registration checks preserved, zero product calls.'),
    (1099,root_pair[0],root_pair[1],None,'$.payload.output[1].text','Root public-toolchain source search guessed a nonexistent agent_tools.go filename; real rg host exit1, Python/Go/Native/SQL/model not started by this read. Actual old21 build is a separate already-owned invocation.')):
    standard=save('original%d.standard-binding.live1100.root.json'%ordinal,dict(schema='researchos.root-original-diagnostic-binding.v1',
        issued_by='codex:/root',original_capture_ref=raw_ref,original_source_binding_ref=original_binding,
        original_source_binding_selector='$',original_ordinal=ordinal,original_bytes_unchanged=True,formal_authority=False))
    rows.append(dict(ordinal=ordinal,origin_ref=raw_ref,origin_selector=selector,capture_binding_ref=standard,
        description=description,capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',actual_outer_exit=1,actual_python_exit=python,
        actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
assert [x['ordinal'] for x in rows]==list(range(1097,1100))
for ref in prior['current_canonical_refs']:exact(Path(ref['path']),ref['sha256'],ref['bytes'])
pending=save('pending-diagnostics.cp374.live1100.root.json',dict(prior,pending=rows,next_original_failure_ordinal=1100,
    registered_in_current_canon=False,counter_reset=False,created_utc=datetime.now(timezone.utc).isoformat()))
print(json.dumps(dict(pending_ref=pending,pending_rows=len(rows),next_original_failure_ordinal=1100,
    Canon_unchanged=True,formal_acceptance=False),ensure_ascii=False,indent=2))
