from pathlib import Path
import ast,json,hashlib,os
N=Path(__file__).resolve().parent
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
tree=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ('pin','save','outputs','capture')],type_ignores=[]),'<Root-original-capture-functions>','exec'),globals())
def match(call,result):return any(x.get('chunk_id')=='8470d5' for x in outputs(result['payload'].get('output')))
raw,binding=capture(AUDIT,106001,match,root=True)
observed=json.loads((N/'public22.readonly.activation.before.observed.root.json').read_bytes())
ref=save('public22.readonly.activation-envelope.actual.root.json',dict(
    issued_by='codex:/root',facts_ref=observed['facts_ref'],before_canonical_refs=observed['before_canonical_refs'],actual_audit_ref=binding))
print(json.dumps(dict(activation_ref=ref,capture_binding_ref=binding),ensure_ascii=False))

