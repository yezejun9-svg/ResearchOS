"""Independent public-only admission audit; no provider or service operations."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
BASE = ROOT / 'execution/receipts/W11' / OUT.name

def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(v):
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

checked = {}
def checkhash(name, expected):
    p = (ROOT / name).resolve()
    assert p.is_relative_to(ROOT), name
    actual = sha(p)
    assert actual == expected.removeprefix('sha256:'), name
    checked[name] = actual

receipt = read(BASE/'receipt.json')
assert receipt['receipt_hash'] == 'sha256:686beb548a8407df99cb84d6374407a011d9c545c78ee4117491bc92e222bb0d'
assert receipt['receipt_hash'] == 'sha256:' + hashlib.sha256(canonical({k:v for k,v in receipt.items() if k != 'receipt_hash'})).hexdigest()
manifest = read(BASE/'artifacts.json')
assert sha(BASE/'artifacts.json') == receipt['artifact_manifest_hash']
assert len(manifest['files']) == len({x['path'] for x in manifest['files']}) == 252
for item in manifest['files']: checkhash(item['path'],item['sha256'])
environment = read(BASE/'environment-before.json')
source_checks = []
for name, expected in environment['source_sha256'].items():
    raw = subprocess.run(['git','show',receipt['code_revision']+':'+name],cwd=ROOT,check=True,capture_output=True).stdout
    assert hashlib.sha256(raw).hexdigest() == expected, name
    checkhash(name,expected)
    source_checks.append(name)

# Import only the inspected read-only class, deliberately avoid main() output
# outside the owned verifier folder and avoid any network/service operation.
spec = importlib.util.spec_from_file_location('w11_admission',ROOT/'tests/jev/admit_frozen_live.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
admission = module.Admission(ROOT); admission.run()
# Normalize in-memory tuples to their emitted JSON array representation.
admission.checks = json.loads(json.dumps(admission.checks))
assert len(admission.checks) == len({x['assertion_id'] for x in admission.checks}) == 240
assert all(x['status']=='PASS' and x['expected']==x['actual'] for x in admission.checks)
assert all(x['current_matches_frozen'] for x in admission.original['source_continuity'])
rows_by_invocation = {}
bindings = []
expected_modes={'W11-G02':'LIVE_SERVICE','W11-G03':'LIVE_SERVICE','W11-G04':'FIXTURE','A08':'LIVE_SERVICE'}
assert len(receipt['verification_results'])==4
for command in receipt['verification_results']:
    inv = read(ROOT/command['actual_invocation_reference'])
    label = inv['selectors']['check_id'] or inv['selectors']['case_id']
    assert inv['selectors']['task_id']=='W11' and label in expected_modes
    assert command['mode']==expected_modes[label]
    assert inv['code_revision']==receipt['code_revision']
    assert inv['status']==command['status']==command['actual_dispatch_status']=='PASS'
    assert inv['exit_code']==command['exit_code']==0
    assert len(inv['assertion_ids'])==len(set(inv['assertion_ids']))==240
    assert inv['assertion_ids']==command['assertion_ids']==[x['assertion_id'] for x in admission.checks]
    for field in ['command_key','registered_command_revision','started_at','ended_at']:
        assert inv[field]==command[field]
    for field in ['stdout','stderr']: checkhash(inv[field]['path'],inv[field]['sha256'])
    stdout=read(ROOT/inv['stdout']['path']); report=read(stdout['receipt'])
    assert report['assertions']==admission.checks
    assert report['measurement_mode']=='READ_ONLY_ADMISSION_OF_PAST_LIVE'
    assert report['new_provider_calls']==0 and report['private_body_or_labels_read'] is False
    assert report['service_operations']==[] and report['whole_W11_accepted'] is False
    assert report['original_provenance']['original_modes'][label]==expected_modes[label]
    rows_by_invocation[command['actual_invocation_reference']]={x['assertion_id']:x for x in report['assertions']}
    bindings.append({'selector':label,'contract_mode':command['mode'],'execution_mode':report['measurement_mode'],'invocation':command['actual_invocation_reference']})
assert {x['selector'] for x in bindings}==set(expected_modes)

case = read(BASE/'A08.json')
frozen=next(c for c in read(ROOT/'spec/v2.0/contracts/acceptance.json')['cases'] if c['id']=='A08')
assert case['global_evidence_id']=='GLOBAL_EVIDENCE_V1'
assert case['run_receipt']['environment_mode']==frozen['mode']=='LIVE_SERVICE'
assert case['run_receipt']['executor_identity']!=case['run_receipt']['independent_verifier_identity']=='codex:/root/workbench_verifier'
assert [x['assertion_id'] for x in case['assertion_results']]==[x['id'] for x in frozen['assertions']]
for row, expected in zip(case['assertion_results'],frozen['assertions']):
    assert row['expected']==expected['expected'] and row['status']=='PASS' and row['actual']
    for actual in row['actual']:
        ref=actual['invocation_reference']
        assert {k:v for k,v in actual.items() if k!='invocation_reference'}==rows_by_invocation[ref][actual['assertion_id']]
    for ref in row['raw_evidence']:checkhash(ref['path'],ref['sha256'])
for row in case['supplemental_assertions']:
    assert {k:v for k,v in row.items() if k!='invocation_reference'}==rows_by_invocation[row['invocation_reference']][row['assertion_id']]
for field in ['lock_files','input_snapshots','policy_versions']:
    for ref in case['version_manifest'][field]:checkhash(ref['path'],ref['sha256'])
checkhash(case['version_manifest']['preflight_reference']['path'],case['version_manifest']['preflight_reference']['sha256'])
checkhash(receipt['owned_acceptance_evidence']['A08']['path'],receipt['owned_acceptance_evidence']['A08']['sha256'])

product=ROOT/'execution/verifier/W11/product-live-591d16e'
summary=read(ROOT/'execution/verifier/W11/frozen-live-ac9d6153/aggregate.stdout.json')
native=read(ROOT/'execution/verifier/W11/formal-object-boundary/native-results.json')
product_receipts=[]
for lang in ['zh','zh-en']:
    r=read(product/(lang+'-independent-acceptance.response.json'))
    assert r['receipt_hash']=='sha256:'+hashlib.sha256(canonical({k:v for k,v in r.items() if k!='receipt_hash'})).hexdigest()
    assert r['subject_ref']['id']==read(product/(lang+'-qualification-result.response.json'))['id']
    assert r['artifact_refs'][0]['content_hash']=='sha256:'+sha(product/(lang+'-public-summary-content.response.json'))
    assert r['verifier_principal_id'] not in r['executor_principal_ids']
    product_receipts.append({'language':lang,'id':r['id'],'receipt_hash':r['receipt_hash'],'created_at':r['created_at']})
assert case['run_receipt']['started_at']==summary['frozen_run']['frozen_at']
assert case['run_receipt']['ended_at']==max(x['created_at'] for x in product_receipts)
assert native['checked_at']>case['run_receipt']['ended_at']
assert case['run_receipt']['admission_verified_at']>native['checked_at']
prior=read(ROOT/'execution/verifier/W11/8a5ca295-69c0-4ebd-9ae3-8a8e266bc942.json')
assert {(x['case_id'],x['verdict']) for x in prior['owned_case_verdicts']}=={('C07','PASS'),('C08','PASS')}

report={'status':'PASS','reviewed_at':datetime.now(timezone.utc).isoformat(),
 'executor_receipt_jcs_hash':receipt['receipt_hash'],'manifest_files_verified':252,
 'unique_public_file_hashes_verified':len(checked),'source_git_and_worktree_hashes_verified':len(source_checks),
 'admission_checks_recomputed':len(admission.checks),'command_bindings':bindings,
 'frozen_case_assertions_verified':[x['id'] for x in frozen['assertions']],
 'product_acceptance_jcs_hashes':product_receipts,'per_key_metrics':admission.metrics,
 'original_live_interval':{k:case['run_receipt'][k] for k in ['started_at','ended_at']},
 'supplemental_native_boundary_checked_at':native['checked_at'],
 'time_interpretation':'Original interval describes frozen service to product acceptance, not all supplemental verification; actual formal file DENY occurred later and retains its own timestamp.',
 'new_provider_calls':0,'service_operations':[],'private_body_read':False,
 'whole_W11_accepted':False,'hashes':checked}
(OUT/'audit-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'recomputed-admission-checks.json').write_text(json.dumps(admission.checks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['hashes','per_key_metrics','command_bindings']},ensure_ascii=False))
