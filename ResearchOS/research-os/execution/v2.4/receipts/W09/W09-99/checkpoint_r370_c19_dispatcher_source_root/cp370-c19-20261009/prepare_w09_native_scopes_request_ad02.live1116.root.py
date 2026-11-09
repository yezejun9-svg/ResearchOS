"""Preserve the last independent tail diagnostic before registering Native scopes."""
from pathlib import Path
import ast,hashlib,json,os
N=Path(__file__).resolve().parent;R=Path(r'D:\作品集\ResearchOS\research-os')
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in {'pin','save','exact','outputs'}],type_ignores=[]),'Root_functions_only','exec'),globals())
prior=json.loads((N/'pending-diagnostics.cp375.live1115.root.json').read_bytes())
P=R/'execution/v2.4/receipts/W05/W05-99/schema21_programme_root_binding_independent_review_codex/bind-old21-20261010-01'
origin=exact(P/'review-0f6974.actual-host.raw.jsonl','5c05a408dc8a7a750c37eff8963937680a033c4b35362643a3c58ba82c13d32f',31773)
binding=exact(P/'review-0f6974.actual-host.binding.json','7760ebfd5dba969b1e4f8881de17436df11a2645ba3287b4c5ef6e1ceb220862',1228)
b=json.loads(Path(binding['path']).read_bytes());lines=Path(origin['path']).read_bytes().splitlines(keepends=True)
assert len(lines)==3 and [len(x) for x in lines]==b['source_line_bytes']
assert [hashlib.sha256(x).hexdigest() for x in lines]==b['original_line_sha256']
with Path(b['source_audit_path']).open('rb') as f:
    for off,line in zip(b['source_line_offsets'],lines):f.seek(off);assert f.readline()==line
first,last=[json.loads(x) for x in lines[1:]]
assert first['payload']['call_id']==last['payload']['call_id']==b['original_call_id']
hosts=[x for x in outputs(last['payload']['output']) if x.get('chunk_id')=='0f6974']
assert len(hosts)==1 and hosts[0]['exit_code']==1 and b['python_exit'] is None
standard=save('original1115.standard-binding.live1116.root.json',dict(
    schema='researchos.root-original-diagnostic-binding.v1',issued_by='codex:/root',original_capture_ref=origin,
    original_source_binding_ref=binding,original_source_binding_selector='$',original_ordinal=1115,
    original_bytes_unchanged=True,formal_authority=False))
row=dict(ordinal=1115,origin_ref=origin,origin_selector='$',capture_binding_ref=standard,
    description='Independent programme binding tail reader configured per-file cap greater than total cap; SourceReadGuard rejected construction before acquisition. Actual host1 and original Python marker unobserved NULL preserved. New necessary cap-only continuation57 checks passed; no successful prefix or product rerun.',
    capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',actual_outer_exit=1,actual_python_exit=None,
    actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None)
rows=prior['pending']+[row];assert [x['ordinal'] for x in rows]==list(range(1109,1116))
pending=save('pending-diagnostics.cp375.live1116.root.json',dict(prior,pending=rows,next_original_failure_ordinal=1116))
source=(N/'prepare_w09_native_scopes_request_ad02.root.py').read_text(encoding='utf-8')
source=source.replace('pending-diagnostics.cp375.live1114.root.json','pending-diagnostics.cp375.live1116.root.json')
source=source.replace('b8158bb3ee7b4f6b3665d0029935c78620f9c44852851b32c06266bd49f4d8da',pending['sha256'])
source=source.replace(',7790)',','+str(pending['bytes'])+')').replace('range(1109,1114)','range(1109,1116)').replace("']==1114","']==1116")
exec(compile(source,str(Path(__file__)),'exec'),globals())
