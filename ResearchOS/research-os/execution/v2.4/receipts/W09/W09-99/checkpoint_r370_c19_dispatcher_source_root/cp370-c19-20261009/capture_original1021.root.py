"""Capture the Root read query that included one absent, guessed file path."""
from pathlib import Path
import ast, hashlib, json, os
N=Path(__file__).resolve().parent
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path(r'C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
tree=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
definitions=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[])
exec(compile(definitions,'root_capture_definitions','exec'),globals())
def match(call,result):
    return any(x.get('chunk_id')=='bcb8fe' for x in outputs(result['payload'].get('output')))
captured=capture(AUDIT,1021,match,root=True)
assert captured is not None
origin,binding=captured
print(json.dumps(dict(ordinal=1021,origin_ref=origin,capture_binding_ref=binding,
    actual_outer_exit=0,actual_python_exit=None,actual_native_exit=None,
    actual_dispatcher_exit=None,actual_model_exit=None,
    description='Root Source read included guessed absent actual-identities.json with SilentlyContinue; exact complete original outer pair retained. Other two Source reads succeeded. Inner error text and exit unobserved NULL.',
    capture_completeness='ROOT_AUDIT_COMPLETE_ORIGINAL_HOST_PAIR',
    next_original=1022),ensure_ascii=False),flush=True)
