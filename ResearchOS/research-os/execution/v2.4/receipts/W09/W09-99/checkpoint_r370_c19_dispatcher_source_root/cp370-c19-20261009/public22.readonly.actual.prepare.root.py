from pathlib import Path
import ast,json,hashlib,os
N=Path(__file__).resolve().parent
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
tree=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ('pin','save','outputs','capture')],type_ignores=[]),'<Root-capture-functions>','exec'),globals())
def match(call,result):return any(x.get('chunk_id')=='28ef15' for x in outputs(result['payload'].get('output')))
raw,binding=capture(AUDIT,106002,match,root=True)
o=json.loads((N/'public22.readonly.activation.after.observed.root.json').read_bytes())
q=json.loads((N/'public22.readonly.registration-request.actual.root.json').read_bytes())
a=json.loads(Path(o['registration_result_ref']['path']).read_bytes())
fref=a['facts_ref']
for ref in o['current_canonical_refs']:
    actual=pin(Path(ref['path']));assert (actual['sha256'],actual['bytes'])==(ref['sha256'],ref['bytes'])
ref=save('public22.readonly.actual-request.root.json',dict(
    schema='researchos.root-public22-existing-actual-request.v1',issued_by='codex:/root',formal_acceptance=False,
    facts_ref=fref,scope_ref=o['scope_ref'],case_request_ref=q['case_request_ref'],current_canonical_refs=o['current_canonical_refs'],
    registration_result_ref=o['registration_result_ref'],activation_audit_ref=binding))
print(json.dumps(dict(actual_request_ref=ref),ensure_ascii=False))

