import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTROL = HERE/'product-v1-owned-verification-20261104'
CANDIDATE = HERE/'product-v1-native-conditional-poststop-verifier-prep-02'
ID = 'product-v1-native-conditional-poststop-pure-02'
NODE = Path('C:/nvm4w/nodejs/node.exe')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(CONTROL/'owned_run.py') == 'f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'
assert sha(NODE) == '5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
assert sha(CANDIDATE/'MANIFEST.json') == '7264aabe5b673effb669304eea71c1bc0138d35aaf2c40a542c6100f371ca3fe'
manifest = json.loads((CANDIDATE/'MANIFEST.json').read_bytes())
files = [CANDIDATE/row['name'] for row in manifest['files']]
for row in manifest['files']: assert sha(CANDIDATE/row['name']) == row['sha256']
files += [CANDIDATE/'MANIFEST.json', CANDIDATE/'PURE_TEST_SCOPE_REQUIREMENTS.json', CONTROL/'owned_run.py', Path(__file__)]
scopefile = CONTROL/'scopes'/(ID+'.json')
out = HERE/(ID+'-registration')
assert not scopefile.exists() and not out.exists() and not (CONTROL/'runs'/ID).exists()
scope = dict(schema='researchos.owned-windows-run/1', scope_id=ID, purpose='build', authorization='ROOT_REVIEWED_EXACT_COMMAND', controller_sha256=sha(CONTROL/'owned_run.py'), executable=str(NODE), executable_sha256=sha(NODE), argv=['--test', str(CANDIDATE/'pure-verifier.test.mjs')], cwd=str(CANDIDATE), timeout_seconds=90, graceful='none', grace_seconds=0, cleanup_seconds=5, process_limit=8, memory_mib=1024, max_raw_bytes=8388608, inputs=[dict(path=str(p), sha256=sha(p)) for p in files])
out.mkdir()
scopefile.write_bytes((json.dumps(scope, indent=2)+'\n').encode('utf8'))
result = dict(status='REGISTERED_NOT_EXECUTED', scope_id=ID, scope_path=str(scopefile), scope_sha256=sha(scopefile), source_manifest_sha256=sha(CANDIDATE/'MANIFEST.json'), task_native_helper_app_model_budget=0, formal_increment=0, product_increment=0)
(out/'REGISTRATION.json').write_bytes((json.dumps(result, indent=2)+'\n').encode('utf8'))
print(json.dumps(result))
