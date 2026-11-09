"""Retain the strict CLI reference-spelling diagnostic and prepare fresh scope input."""
from pathlib import Path
import ast,hashlib,json,os
N=Path(__file__).resolve().parent;R=Path(r'D:\作品集\ResearchOS\research-os')
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in {'pin','save','exact','outputs','capture'}],type_ignores=[]),'Root_functions_only','exec'),globals())
prior=json.loads((N/'pending-diagnostics.cp375.live1116.root.json').read_bytes())
def failed(call,result):return any(x.get('chunk_id')=='acfadb' for x in outputs(result['payload'].get('output')))
pair=capture(AUDIT,1116,failed,root=True);assert pair
hosts=[x for x in outputs(json.loads(Path(pair[0]['path']).read_bytes().splitlines()[-1])['payload']['output']) if x.get('chunk_id')=='acfadb']
assert len(hosts)==1 and hosts[0]['exit_code']==1 and 'ROOT_ACTUAL_PYTHON_EXIT=1' in hosts[0]['output']
assert 'REF_DRIFT' in hosts[0]['output'] and 'request=doc(request_ref)' in hosts[0]['output']
standard=save('original1116.standard-binding.live1117.root.json',dict(
    schema='researchos.root-original-diagnostic-binding.v1',issued_by='codex:/root',original_capture_ref=pair[0],
    original_source_binding_ref=pair[1],original_source_binding_selector='$',original_ordinal=1116,
    original_bytes_unchanged=True,formal_authority=False))
row=dict(ordinal=1116,origin_ref=pair[0],origin_selector='$',capture_binding_ref=standard,
    description='Root supplied a forward-slash CLI reference path to a caller whose exact dictionary pins use Windows backslashes. REF_DRIFT occurred on reading the request before dependency, guard, output or TP stages. Fresh Root input retains the original and uses the actual Windows path spelling at CLI ref boundaries.',
    capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',actual_outer_exit=1,actual_python_exit=1,
    actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None)
rows=prior['pending']+[row];assert [x['ordinal'] for x in rows]==list(range(1109,1117))
pending=save('pending-diagnostics.cp375.live1117.root.json',dict(prior,pending=rows,next_original_failure_ordinal=1117))
source=(N/'prepare_w09_native_scopes_request_ad02.root.py').read_text(encoding='utf-8')
source=source.replace('pending-diagnostics.cp375.live1114.root.json','pending-diagnostics.cp375.live1117.root.json')
source=source.replace('b8158bb3ee7b4f6b3665d0029935c78620f9c44852851b32c06266bd49f4d8da',pending['sha256'])
source=source.replace(',7790)',','+str(pending['bytes'])+')').replace('range(1109,1114)','range(1109,1117)').replace("']==1114","']==1117")
exec(compile(source,str(Path(__file__)),'exec'),globals())
