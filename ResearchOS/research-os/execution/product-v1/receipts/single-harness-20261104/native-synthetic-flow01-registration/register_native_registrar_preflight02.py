import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;D=Path('D:/作品集/ResearchOS/research-os');CONTROL=HERE/'product-v1-owned-verification-20261104';ID='product-v1-native-synthetic-registrar-preflight-02'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
candidate=HERE/'product-v1-native-synthetic-flow-01-registrar-candidate-rev2'
assert sha(candidate/'MANIFEST.json')=='fe5b27f60423bad9357a3a35b84ae9609d7177f5fadaab76380b6870402292dd'
assert sha(CONTROL/'owned_run.py')=='f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'
python=Path('C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe');assert sha(python)=='cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'
base=D/'execution/product-v1/receipts/single-harness-20261104/build13-scope';reg=read(base/'registration.json');bundle=Path(reg['bundle']);wt=Path(reg['clean_worktree'])
files=[candidate/'MANIFEST.json',candidate/'register_product_v1_native_synthetic_flow01.py',HERE/'preflight_native_synthetic_registrar02.py',HERE/'product-v1-build13-root-postcheck.json',HERE/'product-v1-native-conditional-controller-security-review-02/REVIEW.json',HERE/'product-v1-native-conditional-poststop-security-review-02/REVIEW.json',CONTROL/'owned_run.py',Path(__file__),bundle/'development-manifest.json',bundle/'apps/desktop/resources/control/researchos-control.exe',base/'registration.json',base/'registration.effective-v1.json',CONTROL/'runs/product-v1-build-13/RESULT.json',CONTROL/'scopes/product-v1-build-13-effective-v1.json']+[wt/ref for ref in reg['source_sha256']]
scopefile=CONTROL/'scopes'/(ID+'.json');out=HERE/(ID+'-registration');assert not scopefile.exists() and not out.exists() and not (CONTROL/'runs'/ID).exists()
scope=dict(schema='researchos.owned-windows-run/1',scope_id=ID,purpose='build',authorization='ROOT_REVIEWED_EXACT_COMMAND',controller_sha256=sha(CONTROL/'owned_run.py'),executable=str(python),executable_sha256=sha(python),argv=['-B','-X','utf8',str(HERE/'preflight_native_synthetic_registrar02.py')],cwd=str(HERE),timeout_seconds=120,graceful='none',grace_seconds=0,cleanup_seconds=5,process_limit=8,memory_mib=1024,max_raw_bytes=2097152,inputs=[dict(path=str(p),sha256=sha(p)) for p in files])
out.mkdir();scopefile.write_bytes((json.dumps(scope,indent=2)+'\n').encode('utf8'))
result=dict(status='REGISTERED_NOT_EXECUTED',scope_path=str(scopefile),scope_sha256=sha(scopefile),actual_flow_id_unconsumed=True,app_helper_native_model_task_budget=0)
(out/'REGISTRATION.json').write_bytes((json.dumps(result,indent=2)+'\n').encode('utf8'));print(json.dumps(result))
