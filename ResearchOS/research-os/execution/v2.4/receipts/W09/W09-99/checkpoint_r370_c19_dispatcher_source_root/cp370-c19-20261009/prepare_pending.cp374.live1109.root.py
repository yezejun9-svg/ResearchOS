"""Reissue Root-owned references with Windows spelling, preserving all original bytes."""
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
prior=json.loads((N/'pending-diagnostics.cp374.live1107.root.json').read_bytes());rows=list(prior['pending'])
assert [r['ordinal'] for r in rows]==list(range(1097,1107))
def failed1107(call,result):return any(x.get('chunk_id')=='b4825a' for x in outputs(result['payload'].get('output')))
pair=capture(AUDIT,1107,failed1107,root=True);assert pair
last=json.loads(Path(pair[0]['path']).read_bytes().splitlines()[-1])
host=[x for x in outputs(last['payload']['output']) if x.get('chunk_id')=='b4825a'][0]
assert host['exit_code']==1 and 'ROOT_ACTUAL_PYTHON_EXIT=1' in host['output'] and 'REF_DRIFT' in host['output']
new_items=[(1107,*pair,1,1,'Root W09 propose rejected the spelling of three foreign pending refs: same original bytes/SHA, forward slashes differed from strict Windows ref dict. No Source guard/TP/Main/Go/Native/SQL/model started. Original request and failure retained; only new Root-owned refs are reissued.')]
D=B/'schema21_programme_actual_independent_review_codex/actual-old21-20261010-01'
raw_ref=exact(D/'review-6bf827.actual-host.raw.jsonl','d912b58a7725ffcae117fd60209a792d353a6901f1b9153529ec579adb23fd22',35996)
candidates=[p for p in D.glob('*6bf827*binding*.json') if pin(p)['sha256']=='739064dc7a233cb70bf7425b06234ee2997bd4d8d7d15d4b34f692ae07033f9d']
assert len(candidates)==1
binding_ref=exact(candidates[0],'739064dc7a233cb70bf7425b06234ee2997bd4d8d7d15d4b34f692ae07033f9d',1221)
binding=json.loads(Path(binding_ref['path']).read_bytes());lines=Path(raw_ref['path']).read_bytes().splitlines(keepends=True)
assert len(lines)==3 and [len(x) for x in lines]==binding['source_line_bytes']
assert [hashlib.sha256(x).hexdigest() for x in lines]==binding['original_line_sha256']
with Path(binding['source_audit_path']).open('rb') as f:
    for off,line in zip(binding['source_line_offsets'],lines):
        assert off+len(line)<=binding['source_prefix_size_observed'];f.seek(off);assert f.readline()==line
last=json.loads(lines[-1]);host=[x for x in outputs(last['payload']['output']) if x.get('chunk_id')=='6bf827'][0]
assert host['exit_code']==1
new_items.append((1108,raw_ref,binding_ref,1,1,'Independent actual old21 facts review parsed every quoted Go trace token as JSON and failed on a non-JSON cd Windows path. Original retained; 31132 successful checks and closed19461-ref guard preserved; narrow link parser continuation only.'))
for ordinal,raw_ref,binding_ref,outer,python,description in new_items:
    temporary=dict(schema='researchos.root-original-diagnostic-binding.v1',issued_by='codex:/root',
        original_capture_ref=raw_ref,original_source_binding_ref=binding_ref,original_source_binding_selector='$',
        original_ordinal=ordinal,original_bytes_unchanged=True,formal_authority=False)
    ref=save('original%d.standard-binding.before-Windows-live1109.root.json'%ordinal,temporary)
    rows.append(dict(ordinal=ordinal,origin_ref=raw_ref,origin_selector='$',capture_binding_ref=ref,description=description,
        capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',actual_outer_exit=outer,actual_python_exit=python,
        actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
for row in rows:
    original=json.loads(Path(row['capture_binding_ref']['path']).read_bytes())
    source_binding=original['original_source_binding_ref'];raw_before=row['origin_ref']
    normalized_raw=pin(Path(raw_before['path']));normalized_source=pin(Path(source_binding['path']))
    assert (normalized_raw['sha256'],normalized_raw['bytes'])==(raw_before['sha256'],raw_before['bytes'])
    assert (normalized_source['sha256'],normalized_source['bytes'])==(source_binding['sha256'],source_binding['bytes'])
    root_binding=dict(original,original_capture_ref=normalized_raw,original_source_binding_ref=normalized_source,
        prior_Root_binding_ref=row['capture_binding_ref'],original_spelling_capture_ref=raw_before,
        original_spelling_source_binding_ref=source_binding,Root_reference_spelling='WINDOWS_PATH_STRING',original_bytes_unchanged=True)
    row['origin_ref']=normalized_raw
    row['capture_binding_ref']=save('original%d.standard-binding.Windows-live1109.root.json'%row['ordinal'],root_binding)
assert [r['ordinal'] for r in rows]==list(range(1097,1109))
for ref in prior['current_canonical_refs']:exact(Path(ref['path']),ref['sha256'],ref['bytes'])
pending=save('pending-diagnostics.cp374.live1109.root.json',dict(prior,pending=rows,next_original_failure_ordinal=1109,
    registered_in_current_canon=False,counter_reset=False,created_utc=datetime.now(timezone.utc).isoformat()))
print(json.dumps(dict(pending_ref=pending,pending_rows=len(rows),next_original_failure_ordinal=1109,
    foreign_original_files_unchanged=True,Canon_unchanged=True,formal_acceptance=False),ensure_ascii=False,indent=2))
