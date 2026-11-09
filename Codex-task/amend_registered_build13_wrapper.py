import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
CONTROL=HERE/'product-v1-owned-verification-20261104'
ROOT=Path('D:/作品集/ResearchOS/research-os')
BASE=ROOT/'execution/product-v1/receipts/single-harness-20261104/build13-scope'
original=CONTROL/'scopes/product-v1-build-13.json'
effective=CONTROL/'scopes/product-v1-build-13-effective-v1.json'
wrapper=HERE/'build_desktop_serial13.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(original)=='413a76de6c3e42a1eeb18de4aa0b463ead69262af88348c9898057fa71abf59a'
assert sha(wrapper)=='c7dd00bd70bdef1f9c3d4f7d392562c5fe991dae987bb7fe0a87130ef4ff4ec6'
assert not (CONTROL/'runs/product-v1-build-13').exists()
assert not effective.exists() and not (BASE/'registration.effective-v1.json').exists()
scope=json.loads(original.read_bytes())
assert scope['scope_id']=='product-v1-build-13'
assert scope['argv'][3]==str(HERE/'build_desktop_serial12.py')
assert scope['argv'][4]==str(ROOT/'.local/worktrees/product-v1-build-13-20261105/apps/desktop/build-development.py')
assert scope['argv'][scope['argv'].index('--qualification-helper')+1]==str(HERE/'product-v1-native-helper-build01/buildout/qualification-helper.exe')
scope['argv'][3]=str(wrapper)
for path in [wrapper,original,Path(__file__)]:
    scope['inputs'].append(dict(path=str(path),sha256=sha(path)))
effective.write_bytes((json.dumps(scope,indent=2)+'\n').encode('utf8'))
result=dict(status='REGISTERED_NOT_EXECUTED_ORIGINAL_PRESERVED',scope_id=scope['scope_id'],scope_path=str(effective),scope_sha256=sha(effective),original_scope_path=str(original),original_scope_sha256=sha(original),wrapper_path=str(wrapper),wrapper_sha256=sha(wrapper),reason='Root pre-execution check found build13 registrar retained serial12 filename. Correct the exact wrapper reference before first execution; no consumed scope or output is reused.',original_scope_executed=False,task_native_model_calls=0,formal_increment=0)
(BASE/'registration.effective-v1.json').write_bytes((json.dumps(result,indent=2)+'\n').encode('utf8'))
print(json.dumps(result))
