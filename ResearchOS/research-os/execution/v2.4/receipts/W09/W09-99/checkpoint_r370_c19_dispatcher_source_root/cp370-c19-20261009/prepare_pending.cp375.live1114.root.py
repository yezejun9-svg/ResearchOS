"""Complete the new contiguous diagnostic suffix, preserving every original byte."""
from pathlib import Path
import ast,hashlib,json,os,re
N=Path(__file__).resolve().parent;R=Path(r'D:\作品集\ResearchOS\research-os')
W=R/'execution/v2.4/receipts/W09/W09-99';THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in {'pin','save','exact','outputs','capture'}],type_ignores=[]),'Root_functions_only','exec'),globals())
prior=json.loads((N/'pending-diagnostics.cp375.live1113.root-prefix.root.json').read_bytes());rows=list(prior['pending'])
assert [x['ordinal'] for x in rows]==[1109,1110,1111]
review=W/'w09_profile_nf3_root_adoption_independent_review_codex/review-adopt-20261010-02'
raw_ref=exact(review/'original-1112.raw.jsonl','20f6e63c2c10f8543adc48feb9b772fd873c185baf9d9eb1b65f919b5bcc2639',40372)
original_binding=exact(review/'original-1112.binding.json','21ba84c4df0808aa753feeed8ac3bce1e3b1fc5ea0172f47f4de4cabdee1cf18',3049)
bound=json.loads(Path(original_binding['path']).read_bytes());lines=Path(raw_ref['path']).read_bytes().splitlines(keepends=True)
assert len(lines)==3 and [len(x) for x in lines]==bound['source_line_bytes']
assert [hashlib.sha256(x).hexdigest() for x in lines]==bound['source_line_sha256']
with Path(bound['source_audit_path']).open('rb') as f:
    for off,line in zip(bound['source_line_offsets'],lines):f.seek(off);assert f.readline()==line
first,last=[json.loads(x) for x in lines[1:]]
assert first['payload']['call_id']==last['payload']['call_id']==bound['actual_call_id']
hosts=[x for x in outputs(last['payload']['output']) if x.get('chunk_id')=='745e8a']
assert len(hosts)==1 and hosts[0]['exit_code']==1 and bound['outer_tool_exit']==bound['python_exit']==1
assert re.search(r'(?i)python_exit\s*=\s*1',hosts[0]['output'])
def failed1113(call,result):return any(x.get('chunk_id')=='ceae6e' for x in outputs(result['payload'].get('output')))
pair=capture(AUDIT,1113,failed1113,root=True);assert pair
for ordinal,origin,original,selector,python,description in (
    (1112,raw_ref,original_binding,'$',1,'Independent AD02 delta reviewer recursively counted later copies of the actual Root1109 receipt; original unique assertion failed after forty successful checks. Exact original callid/offset continuation passed without repeating successful controls; Source and product failure not inferred.'),
    (1113,pair[0],pair[1],'$.payload.output[0].text',None,'Root read guessed a nonexistent Main formal_profile_w05.py filename. rg host1; Python/Go/Native/SQL/model not started by this read. Existing W05 prepared Source profiles remain protected.')):
    standard=save('original%d.standard-binding.live1114.root.json'%ordinal,dict(
        schema='researchos.root-original-diagnostic-binding.v1',issued_by='codex:/root',original_capture_ref=origin,
        original_source_binding_ref=original,original_source_binding_selector='$',original_ordinal=ordinal,
        original_bytes_unchanged=True,formal_authority=False))
    rows.append(dict(ordinal=ordinal,origin_ref=origin,origin_selector=selector,capture_binding_ref=standard,
        description=description,capture_completeness='ACTUAL_HOST_ORIGINAL_PAIR',actual_outer_exit=1,actual_python_exit=python,
        actual_native_exit=None,actual_Go_exit=None,actual_SQLite_exit=None,actual_dispatcher_exit=None,actual_model_exit=None))
assert [x['ordinal'] for x in rows]==list(range(1109,1114))
for ref in prior['current_canonical_refs']:exact(Path(ref['path']),ref['sha256'],ref['bytes'])
pending=save('pending-diagnostics.cp375.live1114.root.json',dict(
    schema='researchos.root-pending-diagnostics.v1',issued_by='codex:/root',counter_reset=False,
    source_cutoff_original_failure_ordinal=1108,next_original_failure_ordinal=1114,registered_in_current_canon=False,
    pending=rows,current_canonical_refs=prior['current_canonical_refs']))
print(json.dumps(dict(pending_ref=pending,rows=5,next_original_failure_ordinal=1114,Canon_unchanged=True,
    original_bytes_unchanged=True,formal_acceptance=False),ensure_ascii=False,indent=2))
