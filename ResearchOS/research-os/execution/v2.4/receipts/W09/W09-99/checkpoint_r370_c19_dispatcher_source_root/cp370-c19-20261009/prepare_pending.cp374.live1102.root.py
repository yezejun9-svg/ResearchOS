"""Extend the retained contiguous pending suffix with the actual reviewer diagnostic."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99'
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in
    {'pin','save','exact','outputs'}],type_ignores=[]),'Root_helper_functions_only','exec'),globals())
prior=json.loads((N/'pending-diagnostics.cp374.live1101.root.json').read_bytes())
assert [r['ordinal'] for r in prior['pending']]==list(range(1097,1101))
D=B/'schema21_programme_actual_independent_review_codex/actual-old21-20261010-01'
raw_ref=exact(D/'failure-befa0c.actual-host.raw.jsonl','26ddeae04bcdded1c2d8a8c1e7a5125cfd97106ecdd7c594b538511d7f5581bc',24305)
binding_ref=exact(D/'failure-befa0c.actual-host.binding.json','4893fc5a20924f84909b14ffe71fbc64a189ccc79d4173366318574c83ec9516',1242)
binding=json.loads(Path(binding_ref['path']).read_bytes());lines=Path(raw_ref['path']).read_bytes().splitlines(keepends=True)
assert len(lines)==3 and [len(x) for x in lines]==binding['source_line_bytes']
assert [hashlib.sha256(x).hexdigest() for x in lines]==binding['original_line_sha256']
with Path(binding['source_audit_path']).open('rb') as f:
    for off,line in zip(binding['source_line_offsets'],lines):
        assert off+len(line)<=binding['source_prefix_size_observed'];f.seek(off);assert f.readline()==line
first,last=[json.loads(x) for x in lines[1:]]
assert first['payload']['call_id']==last['payload']['call_id']==binding['original_call_id']
hosts=[x for x in outputs(last['payload']['output']) if x.get('chunk_id')=='befa0c']
assert len(hosts)==1 and hosts[0]['exit_code']==1 and binding['python_exit'] is None
standard=save('original1101.standard-binding.live1102.root.json',dict(schema='researchos.root-original-diagnostic-binding.v1',
    issued_by='codex:/root',original_capture_ref=raw_ref,original_source_binding_ref=binding_ref,
    original_source_binding_selector='$',original_ordinal=1101,original_bytes_unchanged=True,formal_authority=False))
row=dict(ordinal=1101,origin_ref=raw_ref,origin_selector='$',capture_binding_ref=standard,
    description='Independent actual old21 reviewer guessed the frozen manifest list key; genuine key is objects. Outer1 and unobserved PythonNULL preserved; actual build and prior reads retained, no product rerun.',
    capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',actual_outer_exit=1,actual_python_exit=None,
    actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None)
for ref in prior['current_canonical_refs']:exact(Path(ref['path']),ref['sha256'],ref['bytes'])
pending=save('pending-diagnostics.cp374.live1102.root.json',dict(prior,pending=prior['pending']+[row],
    next_original_failure_ordinal=1102,registered_in_current_canon=False,counter_reset=False,created_utc=datetime.now(timezone.utc).isoformat()))
print(json.dumps(dict(pending_ref=pending,pending_rows=5,next_original_failure_ordinal=1102,Canon_unchanged=True),ensure_ascii=False,indent=2))
