"""Read frozen C20 remote-principal delta and existing author log only."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
SOURCE = 'b91d3ea9f1329333e22ae88e4a46040f33337917'
RAW = 'c2d098ba4d639c3ddb9918ebe87f168f34735f03'
PREFIX = 'execution/receipts/W16/c20-private/remote-recheck-b91d3ea/'
PRIOR = ROOT / 'execution/verifier/W16/c20-private-4eb84a3'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def git(commit, path):
    return subprocess.check_output(['git', 'show', commit + ':' + path], cwd=ROOT)

raw_files = {name:git(RAW, PREFIX+name) for name in ['receipt.json','stdout.txt']}
receipt = json.loads(raw_files['receipt.json'])
log = raw_files['stdout.txt'].decode()
source_files = ['internal/domain/evolution_holdout.go','internal/domain/evolution_holdout_test.go','ops/ci/evolution.py','internal/domain/remote_auth.go']
sources = {name:git(SOURCE,name) for name in source_files}
delta = subprocess.check_output(['git','diff','4eb84a3',SOURCE,'--',*source_files],cwd=ROOT)
old = json.loads((PRIOR/'evidence-index.json').read_bytes())
assertions = [json.loads(line.split(' ',1)[1]) for line in log.splitlines() if line.startswith('W16_ASSERTION ')]
checks = {
    'prior_index_unchanged':sha((PRIOR/'evidence-index.json').read_bytes()) == '4ac5713dc3a5de3591dc948fcca960f56ccf07e9b5b80d815180a0c81eb9e211',
    'prior_files_unchanged':all('sha256:'+sha((PRIOR/name).read_bytes()) == h for name,h in old['files'].items()),
    'source_commit_bound':receipt['source_commit'] == SOURCE,
    'author_stdout_hash_matches':sha(raw_files['stdout.txt']) == receipt['stdout_sha256'],
    'author_exit_zero':receipt['exit_code'] == 0,
    'single_target_test_pass_no_fail_skip':log.count('=== RUN   ') == 1 and log.count('--- PASS: ') == 1 and '--- PASS: TestW16C20PrivateRemoteVerifier ' in log and '--- FAIL:' not in log and '--- SKIP:' not in log,
    'single_remote_denial_assertion_pass':len(assertions) == 1 and assertions[0]['assertion_id'] == 'C20-PRIVATE-REMOTE-DENIED' and assertions[0]['actual'] is True and assertions[0]['expected'] is True and assertions[0]['status'] == 'PASS',
    'fixture_scope_retained':receipt['scope'] == 'W16_G02_FIXTURE_ONLY' and receipt['measurement_mode'] == 'FIXTURE' and receipt['independent_acceptance'] == 'NONE',
    'existing_remote_constraint_helper_unchanged':sources['internal/domain/remote_auth.go'] == git('4eb84a3','internal/domain/remote_auth.go'),
    'prior_gain_and_private_proof_algorithm_unchanged':git(SOURCE,'ops/supervisor/holdout_windows.go') == git('4eb84a3','ops/supervisor/holdout_windows.go') and git(SOURCE,'evaluation/evolution/holdout.go') == git('4eb84a3','evaluation/evolution/holdout.go'),
}
result = {'verdict':'PASS_READONLY_REMOTE_PRINCIPAL_DELTA' if all(checks.values()) else 'NEEDS_REVIEW','source_commit':SOURCE,'author_raw_commit':RAW,'prior_review_index_sha256':sha((PRIOR/'evidence-index.json').read_bytes()),'checks':checks,'source_sha256':{name:sha(raw) for name,raw in sources.items()},'author_raw_sha256':{name:sha(raw) for name,raw in raw_files.items()},'new_execution_by_verifier':False,'formal_C20_gate':'PENDING_ALL_REQUIRED_COMMAND_KEYS'}
(OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
(OUT/'source-diff.patch').write_bytes(delta)
for name,raw in raw_files.items():
    (OUT/('author-'+name)).write_bytes(raw)
print(json.dumps({'verdict':result['verdict'],'checks':len(checks),'failed':[k for k,v in checks.items() if not v]}))
