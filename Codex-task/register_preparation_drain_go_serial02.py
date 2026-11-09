import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;CONTROL=HERE/'product-v1-owned-verification-20261104'
ID='product-v1-native-preparation-drain-tests-02'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
original=CONTROL/'scopes/product-v1-native-preparation-drain-tests-01.json'
assert sha(original)=='b31642826117f2d862dd3a31f13e7eb45602aa00a505fd048a641e16258b72c1'
failed=json.loads((CONTROL/'runs/product-v1-native-preparation-drain-tests-01/RESULT.json').read_bytes())
assert failed['root_exit_code']==1 and failed['stop_proved'] and failed['job_active_zero'] and not failed['input_drift']
scope=json.loads(original.read_bytes());wrapper=HERE/'run_preparation_drain_go_serial02.py'
python=Path('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe')
assert sha(python)=='cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'
assert not (CONTROL/'runs'/ID).exists();out=HERE/(ID+'-registration');sp=CONTROL/'scopes'/(ID+'.json');assert not out.exists() and not sp.exists()
for item in scope['inputs']:assert sha(Path(item['path']))==item['sha256']
go=Path(scope['executable']);assert sha(go)==scope['executable_sha256']
out.mkdir();cache=out/'gocache';tmp=out/'gotmp';cache.mkdir();tmp.mkdir()
scope.update(scope_id=ID,executable=str(python),executable_sha256=sha(python),argv=['-B','-X','utf8',str(wrapper),str(go),*scope['argv']])
scope['env'].update(GOCACHE=str(cache),GOTMPDIR=str(tmp))
scope['inputs'] += [dict(path=str(p),sha256=sha(p)) for p in [wrapper,go,original,Path(__file__)]]
sp.write_bytes((json.dumps(scope,indent=2)+'\n').encode('utf8'))
result=dict(status='REGISTERED_NOT_EXECUTED',scope_id=ID,scope_path=str(sp),scope_sha256=sha(sp),source_manifest_sha256='fff8c3588941e16b7b475d69c32e1410af080fc1b9f12a8c2c6e901a3667c367',original_failed_scope_preserved=True,resource_change='GOMAXPROCS=1 inside pinned wrapper; same original Job/process/memory limits, serial package compilation',new_app_native_model_budget=0,formal_increment=0)
(out/'REGISTRATION.json').write_bytes((json.dumps(result,indent=2)+'\n').encode('utf8'));print(json.dumps(result))
