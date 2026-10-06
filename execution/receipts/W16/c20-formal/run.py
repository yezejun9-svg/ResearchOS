"""Run exactly the three frozen C20 commands, preserving failures and all inputs."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[4]
os.chdir(ROOT)
def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode('utf-8').strip()
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

run = str(uuid.uuid4())
out = ROOT / 'execution/receipts/W16' / run
out.mkdir()
source = git('ls-files', 'adapters', 'internal', 'ops', 'tests', 'apps', 'migrations', 'evaluation', 'go.mod', 'go.sum', 'execution/commands.json', 'execution/command_dispatcher', 'execution/toolchains', 'contracts').splitlines()
before = {'spec_manifest_sha256': sha(ROOT / 'spec/v2.0/PACKAGE_MANIFEST.json'),
          'sampled_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'git_head': git('rev-parse', 'HEAD'),
          'git_status_porcelain': git('status', '--porcelain'), 'tracked_status_porcelain': git('status', '--porcelain', '--untracked-files=no'),
          'working_tree_clean': not git('status', '--porcelain'), 'tracked_source_clean': not git('status', '--porcelain', '--untracked-files=no'),
          'os': platform.system(), 'os_release': platform.release(), 'os_build': platform.version(), 'architecture': platform.machine(),
          'timezone_names': list(time.tzname), 'python_version': platform.python_version(), 'run_id': run,
          'source_sha256': {p: sha(ROOT / p) for p in source}}
assert before['tracked_source_clean'], 'freeze tracked source before formal invocation'
save(out / 'environment-before.json', before)
plan = {'run_id': run, 'base_revision': '6c46c9d', 'invocations': {}, 'adapter': 'Native Windows AppContainer old/new builds and typed loopback Jev; protected synthetic holdout with actual persisted private raw proof',
        'actual_scope': 'FIXTURE', 'verifier_identity': 'codex:/root/evolution_verifier',
        'input_files': ['internal/domain/evolution_holdout.go', 'internal/domain/evolution_holdout_test.go', 'internal/domain/decision_c20_test.go', 'ops/supervisor/holdout_windows.go', 'ops/ci/evolution.py', 'ops/ci/jev.py', 'ops/ci/acceptance_audit.py', 'tests/jev/expected.json'],
        'extra_files': [], 'cases': {'C20': {'invocations': ['test.evolution:C20', 'test.jev.fixture:C20', 'acceptance.audit:C20'],
        'assertion_prefixes': {i: [i] for i in ('C20-01', 'C20-02', 'C20-03')}}},
        'limits': ['C20 FIXTURE only; independent acceptance pending. No actual provider, LIVE model quality, deployment or whole W16 acceptance.',
                   'Frozen synthetic holdout raw inputs, labels and per-question results remain only in the dedicated protected store; ordinary receipts retain hashes and aggregates.',
                   'A16 remains PARTIAL; actual product schema13 and protected service79136 are untouched. Previous policy blocks are unchanged.']}
plan_path = out / 'executor-plan.json'
save(plan_path, plan)
results = {}
env = dict(os.environ, RESEARCHOS_EXECUTOR_ID='codex:/root')
for key in ('test.evolution', 'test.jev.fixture', 'acceptance.audit'):
    command = [sys.executable, '-X', 'utf8', 'execution/command_dispatcher/dispatch.py', key, '--task-id', 'W16', '--case-id', 'C20']
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, encoding='utf-8')
    response = json.loads(result.stdout)
    results[key] = {'exit_code': result.returncode, 'result': response, 'stderr': result.stderr}
    plan['invocations'][key + ':C20'] = response['invocation_id']
    save(out / 'dispatcher-results.json', results)
    save(plan_path, plan)
    print(json.dumps({'key': key, **results[key]}, ensure_ascii=False), flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
    if key in ('test.evolution', 'test.jev.fixture'):
        variable = 'RESEARCHOS_C20_EVOLUTION_RECEIPT' if key == 'test.evolution' else 'RESEARCHOS_C20_JEV_RECEIPT'
        env[variable] = str(ROOT / 'execution/invocations' / response['invocation_id'] / 'receipt.json')
assert all(sha(ROOT / p) == h for p, h in before['source_sha256'].items()), 'source changed during formal invocation'
plan['extra_files'] = [str(p.relative_to(ROOT)).replace('\\', '/') for p in (out / 'dispatcher-results.json', Path(__file__))]
save(plan_path, plan)
print(json.dumps({'status': 'EXECUTION_REPORTED', 'run_id': run, 'plan': str(plan_path), 'source_files': len(source)}), flush=True)
