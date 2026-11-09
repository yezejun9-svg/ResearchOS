"""Add the latest independent diagnostic and issue a fresh complete Root request."""
from pathlib import Path
import ast,hashlib,json,os
N=Path(__file__).resolve().parent;R=Path(r'D:\作品集\ResearchOS\research-os')
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in {'pin','save','exact','outputs'}],type_ignores=[]),'Root_functions_only','exec'),globals())
prior=json.loads((N/'pending-diagnostics.cp375.live1114.root.json').read_bytes())
review=R/'execution/v2.4/receipts/W05/W05-99/schema21_programme_root_binding_independent_review_codex/bind-old21-20261010-01'
origin=exact(review/'review-ef73f6.actual-host.raw.jsonl','a420db4bf5c145d398f5fc568bd7ed6f086c10d065b08143a0ef207ed79b8336',46221)
binding=exact(review/'review-ef73f6.actual-host.binding.json','9808a2718c77b8a0893f00e6f12d4f1e498e2021e8a9db2c416904bdf9643618',1226)
b=json.loads(Path(binding['path']).read_bytes());lines=Path(origin['path']).read_bytes().splitlines(keepends=True)
assert len(lines)==3 and [len(x) for x in lines]==b['source_line_bytes']
assert [hashlib.sha256(x).hexdigest() for x in lines]==b['original_line_sha256']
with Path(b['source_audit_path']).open('rb') as f:
    for off,line in zip(b['source_line_offsets'],lines):f.seek(off);assert f.readline()==line
first,last=[json.loads(x) for x in lines[1:]]
assert first['payload']['call_id']==last['payload']['call_id']==b['original_call_id']
hosts=[x for x in outputs(last['payload']['output']) if x.get('chunk_id')=='ef73f6']
assert len(hosts)==1 and hosts[0]['exit_code']==1 and 'ROOT_SOURCE_PYTHON_EXIT=1' in hosts[0]['output']
standard=save('original1114.standard-binding.live1115.root.json',dict(
    schema='researchos.root-original-diagnostic-binding.v1',issued_by='codex:/root',original_capture_ref=origin,
    original_source_binding_ref=binding,original_source_binding_selector='$',original_ordinal=1114,
    original_bytes_unchanged=True,formal_authority=False))
row=dict(ordinal=1114,origin_ref=origin,origin_selector='$',capture_binding_ref=standard,
    description='Independent Root programme-binding reviewer applied a complete JSON parser to the already retained truncated initial observer API text. Three hundred binding checks preserved; only original-truncation and original1111 tail continued. Actual Root compact observation and programme qualification unchanged; no Go or Native rerun.',
    capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',actual_outer_exit=1,actual_python_exit=1,
    actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None)
rows=prior['pending']+[row];assert [x['ordinal'] for x in rows]==list(range(1109,1115))
pending=save('pending-diagnostics.cp375.live1115.root.json',dict(prior,pending=rows,next_original_failure_ordinal=1115))
source=(N/'prepare_w09_native_scopes_request_ad02.root.py').read_text(encoding='utf-8')
source=source.replace('pending-diagnostics.cp375.live1114.root.json','pending-diagnostics.cp375.live1115.root.json')
source=source.replace('b8158bb3ee7b4f6b3665d0029935c78620f9c44852851b32c06266bd49f4d8da',pending['sha256'])
source=source.replace(',7790)',','+str(pending['bytes'])+')').replace('range(1109,1114)','range(1109,1115)').replace("']==1114","']==1115")
exec(compile(source,str(Path(__file__)),'exec'),globals())
