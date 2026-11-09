from pathlib import Path
import ast,json,hashlib,os
N=Path(__file__).resolve().parent
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in ('pin','save','outputs','capture')],type_ignores=[]),'<Root-original-functions>','exec'),globals())
def match(call,result):return any(x.get('chunk_id')=='5919f2' for x in outputs(result['payload'].get('output')))
pair=capture(AUDIT,106011,match,root=True)
print(json.dumps(dict(scope_original_raw_ref=pair[0],scope_original_binding_ref=pair[1]),ensure_ascii=False))
