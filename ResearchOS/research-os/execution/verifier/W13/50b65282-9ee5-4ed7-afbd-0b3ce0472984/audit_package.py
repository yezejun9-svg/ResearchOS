"""Check immutable GLOBAL package and mapping; never mutate executor evidence."""
from pathlib import Path
import collections
import hashlib
import io
import json
import subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'execution/receipts/W13' / OUT.name

def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(p, h): assert sha(p) == h.removeprefix('sha256:'), str(p)
def canonical(v):
    # This receipt has only integers, strings, booleans, arrays and objects.
    def validate(x):
        assert not isinstance(x, float)
        if isinstance(x, int): assert abs(x) <= 9007199254740991
        if isinstance(x, dict):
            assert all(all(ord(c) < 65536 for c in k) for k in x)
            for value in x.values(): validate(value)
        if isinstance(x, list):
            for value in x: validate(value)
    validate(v)
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

r = read(BASE / 'receipt.json'); manifest = read(BASE / 'artifacts.json')
want = 'sha256:9c78c06a1682162d54d58b10f3683d6160cd7d3b80947b83ee0aa9f3878bfe49'
assert r['receipt_hash'] == want == 'sha256:' + hashlib.sha256(canonical({k:v for k,v in r.items() if k != 'receipt_hash'})).hexdigest()
check(BASE / 'artifacts.json', r['artifact_manifest_hash'])
assert len(manifest['files']) == 544 and len({x['path'] for x in manifest['files']}) == 544
for item in manifest['files']:
    path = (ROOT / item['path']).resolve(); assert path.is_relative_to(ROOT)
    check(path, item['sha256'])
assert r['executor_identity'] == 'codex:/root' and r['verifier_identity'] is None
assert r['status'] == 'EXECUTION_REPORTED'
frozen = {x['id']:x for x in read(ROOT / 'spec/v2.0/contracts/acceptance.json')['cases']}
actual_rows = {}
invocations = {}
for command in r['verification_results']:
    ref = command['actual_invocation_reference']; inv = read(ROOT / ref)
    assert inv['status'] == command['status'] == command['actual_dispatch_status'] == 'PASS'
    assert inv['exit_code'] == command['exit_code'] == 0 and inv['assertion_ids'] == command['assertion_ids']
    for key in ['command_key', 'registered_command_revision', 'started_at', 'ended_at']:
        assert command[key] == inv[key], (ref, key)
    for field in ['stdout','stderr']: check(ROOT / inv[field]['path'], inv[field]['sha256'])
    invocations[ref] = inv
    stdout = read(ROOT / inv['stdout']['path'])
    if 'receipt' in stdout:
        report = read(stdout['receipt'])
        for row in report.get('assertions', []):
            actual_rows[(ref, row['assertion_id'])] = row

case_checks = []
for id in ['C17','C18','C23','C24','C25']:
    ref = r['owned_acceptance_evidence'][id]; check(ROOT / ref['path'], ref['sha256']); case = read(ROOT / ref['path'])
    assert case['global_evidence_id'] == 'GLOBAL_EVIDENCE_V1'
    assert case['run_receipt']['case_id'] == id and case['run_receipt']['run_id'] == OUT.name
    assert case['run_receipt']['environment_mode'] == 'FIXTURE'
    assert case['run_receipt']['executor_identity'] != case['run_receipt']['independent_verifier_identity'] == 'codex:/root/workbench_verifier'
    assert case['acceptance_receipt']['status'] == 'PENDING_INDEPENDENT_VERIFIER'
    assert [x['assertion_id'] for x in case['assertion_results']] == [x['id'] for x in frozen[id]['assertions']]
    mapping = {}
    for row, expected in zip(case['assertion_results'], frozen[id]['assertions']):
        assert row['expected'] == expected['expected'] and row['status'] == 'PASS' and row['actual']
        mapping[row['assertion_id']] = []
        for actual in row['actual']:
            key = (actual['invocation_reference'], actual['assertion_id'])
            assert {k:v for k,v in actual.items() if k != 'invocation_reference'} == actual_rows[key], key
            mapping[row['assertion_id']].append(actual['assertion_id'])
        for reference in row['raw_evidence']: check(ROOT / reference['path'], reference['sha256'])
    for command in case['command_receipt']:
        check(ROOT / command['reference'], command['sha256']); source = invocations[command['reference']]
        for k,v in command.items():
            if k not in ['reference','sha256']: assert v == source[k], (id,k)
    vm = case['version_manifest']
    check(ROOT / vm['preflight_reference']['path'], vm['preflight_reference']['sha256'])
    check(ROOT / 'spec/v2.0/PACKAGE_MANIFEST.json', vm['spec_manifest_sha256'])
    check(ROOT / 'spec/v2.0/contracts/tasks.json', vm['task_gates_sha256'])
    for item in vm['lock_files'] + vm['input_snapshots']: check(ROOT / item['path'], item['sha256'])
    case_checks.append({'case_id':id,'frozen_assertions':len(mapping),'mapping':mapping,'sha256':sha(ROOT/ref['path'])})

build_ref = 'execution/invocations/2459b83f-ff85-46c4-827a-4e63a881a35a/receipt.json'
build = invocations[build_ref]; assert build['code_revision'] == '69509c240fdbb4922b27a009155099cc983bbc11'
assert len(build['assertion_ids']) == 9
data = read(ROOT / build['stdout']['path']); assert data['status'] == 'PASS' and data['error'] is None
assert all(x['exit_code'] == 0 for x in data['commands'])
go = next(x for x in data['commands'] if x['name'] == 'go-test')
events = [json.loads(line) for line in go['stdout'].splitlines() if line.strip()]
assert events and not any(x['Action']=='fail' for x in events)
passed_packages = [x['Package'] for x in events if x['Action']=='pass' and 'Test' not in x]
env = read(BASE/'build-fe89c18d-0f3b-47b7-94d9-9fd35ca84a5c-before.json')
assert env['git_head'] == build['code_revision']
assert len(env['source_sha256']) == 263
paths = list(env['source_sha256'])
batch = subprocess.run(['git','cat-file','--batch'], cwd=ROOT, input=''.join(f"{env['git_head']}:{p}\n" for p in paths).encode(), capture_output=True, check=True)
stream=io.BytesIO(batch.stdout)
for path in paths:
    h=stream.readline().split(); assert len(h)==3 and h[1]==b'blob', path
    blob=stream.read(int(h[2])); assert stream.read(1)==b'\n'
    assert hashlib.sha256(blob).hexdigest()==env['source_sha256'][path],path

audit={'status':'PASS','executor_receipt_sha256':sha(BASE/'receipt.json'),'executor_receipt_jcs_hash':want,
       'manifest_sha256':sha(BASE/'artifacts.json'),'artifact_count_verified':544,'case_checks':case_checks,
       'build':{'invocation':build_ref,'code_revision':build['code_revision'],'assertions':9,'successful_go_packages':passed_packages,'frozen_source_files':263},
       'fixture_69509c2':'Two provider fixtures now use the existing readiness-only fresh-listener helper. Reserved404 guard precedes called/bodySent changes and parsing. Actual business requests and all prompt/fallback/hard-gate expectations remain unchanged.',
       'stage_accepted':False,'C26_accepted':False,'W13_G03_accepted':False,
       'input_audit_reference':str((OUT/'input-audit.json').relative_to(ROOT)).replace('\\','/'),
       'input_audit_sha256':sha(OUT/'input-audit.json')}
(OUT/'envelope-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':audit['status'],'artifacts':544,'formal_cases':len(case_checks),'assertions':sum(x['frozen_assertions'] for x in case_checks),'build_assertions':9,'go_packages':len(passed_packages)}))
