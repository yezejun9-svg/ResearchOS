"""W12 exact development selectors; live model/tool qualification is not waived."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = json.loads((ROOT / 'tests/resources/expected.json').read_text(encoding='utf-8-sig'))
GROUPS = {
    'W12-G01': list(EXPECTED),
    'C11': ['TestW12CrashAndResume', 'TestW12DuplicateCallbacks', 'TestW12SessionIdentity'],
    'C13': ['TestW12Budget', 'TestW12CrashAndResume', 'TestW12ConcurrencyAndQueue', 'TestW12ProgressAndLimits'],
    'C14': ['TestW12Budget', 'TestW12BudgetSettlementChain', 'TestW12BudgetConnections', 'TestW12BudgetPrecisionAndModes', 'TestW12PreparedEffectFences', 'TestW12CancelRetainsAccounting', 'TestW12ExperimentBudgetScopes'],
    'C15': ['TestW12ResourceRoutes', 'TestW12SessionIdentity'],
    'C16': ['TestW12ProgressAndLimits'],
}


def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def main(command_key='test.resources'):
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['fixture', 'live'])
    args = parser.parse_args()
    task, check, case = (os.getenv(k, '') for k in ['RESEARCHOS_TASK_ID', 'RESEARCHOS_CHECK_ID', 'RESEARCHOS_CASE_ID'])
    if task != 'W12' or bool(check) == bool(case) or check and check not in ['W12-G01', 'W12-G02'] or case and case not in ['C11', 'C13', 'C14', 'C15', 'C16']:
        parser.error('W12 requires exactly one known check or owned case selector')
    selector = check or case
    mode = args.mode or ('live' if selector == 'W12-G02' else 'fixture')
    if (mode == 'live') != (selector == 'W12-G02'):
        parser.error('W12-G02 is exclusively live; fixture coverage cannot replace it')
    run_id = str(uuid.uuid4())
    out = ROOT / 'execution/receipts/W12' / run_id
    out.mkdir(parents=True)
    if mode == 'live':
        report = {'task_id': task, 'check_id': check, 'run_id': run_id, 'status': 'BLOCKED', 'assertion_ids': [], 'assertions': 0, 'resource_request_id': 'RQ-W05-CLI-POLICY-001', 'reason': 'W05 live model/tool runtime qualification is policy-blocked; no retry or fixture substitution', 'scope': 'DEVELOPMENT_ONLY', 'executor_status': 'EXECUTION_REPORTED', 'independent_acceptance': 'NOT_REQUESTED'}
        save(out / 'report.json', report)
        print(json.dumps(report))
        return 1
    names = GROUPS[selector]
    expected = [a for n in names for a in EXPECTED[n]]
    if not expected or len(expected) != len(set(expected)):
        raise RuntimeError('empty or duplicate frozen assertion set')
    go = os.getenv('RESEARCHOS_GO') or str(ROOT / '.local/tools/go1.27.1/go/bin/go.exe')
    if not Path(go).is_file():
        parser.error('RESEARCHOS_GO must identify the pinned Go executable')
    env = {k: v for k, v in os.environ.items() if not k.startswith('W12_')}
    env['W12_EVIDENCE_DIR'] = str(out)
    cmd = [go, 'test', './internal/domain', '-v', '-count=1', '-timeout=3m', '-run', '^(' + '|'.join(names) + ')$']
    patterns = ['internal/domain/*.go', 'internal/store/*.go', 'migrations/sqlite/*.sql', 'spec/v2.0/contracts/*.json', 'go.mod', 'go.sum', 'execution/route.json', 'tests/resources/*', 'ops/ci/resources.py', 'ops/checkpoints/*']
    before = {
        'schema': 'GLOBAL_EVIDENCE_V1_CANDIDATE', 'task_id': task, 'check_id': check, 'case_id': case, 'run_id': run_id, 'selector': selector,
        'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'environment_mode': 'FIXTURE_AND_NATIVE_LOCAL_PROCESS', 'os': platform.platform(), 'architecture': platform.machine(), 'timezone': list(time.tzname),
        'executor_identity': os.getenv('RESEARCHOS_EXECUTOR_ID', 'codex:/root/resources'), 'verifier_identity': None,
        'code_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'dirty': subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True),
        'command_key': command_key, 'registered_command_revision': digest(ROOT / 'execution/commands.json').removeprefix('sha256:'), 'argv': cmd, 'cwd': str(ROOT), 'environment_names': sorted(env),
        'version_manifest': {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p) for pattern in patterns for p in ROOT.glob(pattern) if p.is_file()},
        'go_version': subprocess.check_output([go, 'version'], cwd=ROOT, text=True).strip(), 'python_version': platform.python_version(),
        'implementation_model': 'gpt-6-astra', 'reasoning_effort': 'high', 'runtime_model': {'status': 'not_applicable', 'reason': 'explicit local fixture, no provider model invoked'},
        'adapters': 'pinned source tree and local SQLite/HTTP service fixtures', 'rubric': 'frozen acceptance.json expected assertions; deterministic Go checks',
        'scope': 'DEVELOPMENT_ONLY', 'blocked_gate': 'W12-G02 and overall final acceptance depend on W05 live qualification', 'resource_request_id': 'RQ-W05-CLI-POLICY-001',
        'assumptions': ['W06 development gates independently accepted; no live waiver'], 'revalidation_inputs': ['W05 qualified runtime/price upper bound', 'W10 experiment_tasks scope and callback integration'], 'expected_assertion_ids': sorted(expected),
    }
    save(out / 'before.json', before)
    try:
        run = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, timeout=190)
        stdout, stderr, code = run.stdout, run.stderr, run.returncode
    except subprocess.TimeoutExpired as e:
        stdout, stderr, code = e.stdout or b'', e.stderr or b'', 124
    (out / 'stdout.txt').write_bytes(stdout)
    (out / 'stderr.txt').write_bytes(stderr)
    rows, malformed = [], False
    for number, line in enumerate(stdout.decode('utf-8', errors='replace').splitlines(), 1):
        if line.startswith('W12_ASSERTION '):
            try:
                row = json.loads(line[len('W12_ASSERTION '):])
                if not all(k in row for k in ['assertion_id', 'expected', 'actual', 'status', 'evidence']):
                    malformed = True
                row['raw_evidence'] = {'path': 'stdout.txt', 'line': number, 'sha256': digest(out / 'stdout.txt')}
                rows.append(row)
            except ValueError:
                malformed = True
    ids = [r.get('assertion_id') for r in rows]
    passed = code == 0 and not malformed and len(ids) == len(expected) and set(ids) == set(expected) and all(r['status'] == 'PASS' for r in rows)
    index = {str(p.relative_to(out)).replace('\\', '/'): digest(p) for p in out.rglob('*') if p.is_file()}
    report = {'task_id': task, 'check_id': check, 'case_id': case, 'run_id': run_id, 'status': 'PASS' if passed else 'FAIL', 'executor_status': 'EXECUTION_REPORTED', 'exit_code': code, 'assertion_ids': ids, 'expected_assertion_ids': sorted(expected), 'assertions': rows, 'missing': sorted(set(expected) - set(ids)), 'malformed': malformed, 'raw_evidence_hashes': index, 'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'independent_acceptance': 'NOT_REQUESTED', 'scope': 'DEVELOPMENT_ONLY', 'live_qualification': 'BLOCKED', 'blocked_gate': 'W12-G02 / RQ-W05-CLI-POLICY-001'}
    save(out / 'report.json', report)
    print(json.dumps({'status': report['status'], 'assertions': len(rows), 'assertion_ids': ids, 'receipt': str(out / 'report.json')}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
