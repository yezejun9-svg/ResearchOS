"""W16 exact selector development runner; never grants LIVE or independent acceptance."""
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
CASE_ASSERTIONS = {
    'C09': ['C09-REQUIRED', 'C09-01', 'C09-02'],
    'C10': ['C10-01', 'C10-02', 'C10-03'],
    'C12': ['C12-ADMITTED', 'C12-01', 'C12-02', 'C12-03', 'C12-STABLE'],
    'C20': ['C20-01', 'C20-02', 'C20-03', 'C20-PRIVATE-MISSING', 'C20-PRIVATE-TAMPER', 'C20-PRIVATE-REVOKED', 'C20-PRIVATE-GRANT-REMOVED', 'C20-PRIVATE-REMOTE-DENIED'],
    'A16': ['A16-PARTIAL-' + v for mode in ('canary_startup_failure', 'canary_hang')
            for v in (mode, 'STABLE-' + mode)],
}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def verify(stdout, code, expected):
    rows, malformed = [], False
    for n, line in enumerate(stdout.decode('utf-8', errors='replace').splitlines(), 1):
        if line.startswith('W16_ASSERTION '):
            try:
                row = json.loads(line[len('W16_ASSERTION '):])
                if not isinstance(row, dict) or not all(k in row for k in ('assertion_id', 'expected', 'actual', 'status', 'evidence', 'scope')):
                    malformed = True
                    continue
                row['raw'] = {'path': 'stdout.txt', 'line': n}
                rows.append(row)
            except (ValueError, TypeError):
                malformed = True
    ids = [r.get('assertion_id') for r in rows]
    passed = (code == 0 and bool(expected) and len(set(expected)) == len(expected)
              and not malformed and len(ids) == len(expected) and set(ids) == set(expected)
              and all(r['status'] == 'PASS' and r['scope'] == 'W16_G02_FIXTURE_ONLY'
                      and r['expected'] == r['actual'] for r in rows))
    return passed, rows


def main(command_key='test.evolution'):
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('auto', 'fixture'), default='auto')
    args = parser.parse_args()
    task, check, case = (os.getenv(k, '') for k in ('RESEARCHOS_TASK_ID', 'RESEARCHOS_CHECK_ID', 'RESEARCHOS_CASE_ID'))
    selector = check or case
    if task != 'W16' or bool(check) == bool(case) or (check and check != 'W16-G02') or (case and case not in CASE_ASSERTIONS):
        parser.error('exact W16-G02 check or one C09/C10/C12/C20/A16 case required; G01/G03 not qualified')
    go = os.getenv('RESEARCHOS_GO')
    if not go:
        go = json.loads((ROOT / 'execution/toolchains/locked.json').read_text(encoding='utf-8'))['tools']['go']['path']
    if not Path(go).is_file():
        parser.error('pinned RESEARCHOS_GO executable is required')
    cases = list(CASE_ASSERTIONS) if check else [case]
    expected = [a for c in cases for a in CASE_ASSERTIONS[c]]
    tests = ['TestW16' + ('A16Partial' if c == 'A16' else c) for c in cases]
    if 'C20' in cases:
        tests.extend(('TestW16C20PrivateProofMissing', 'TestW16C20PrivateProofTampered',
                      'TestW16C20PrivateVerifierRevoked', 'TestW16C20PrivateVerifierGrantRemoved',
                      'TestW16C20PrivateRemoteVerifier'))
    out = ROOT / 'execution/receipts/W16' / ('c20-private' if 'C20' in cases else '') / str(uuid.uuid4())
    out.mkdir(parents=True)
    env = {k: v for k, v in os.environ.items() if k.upper() in ('SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP', 'PATH', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'COMSPEC', 'PATHEXT')}
    env.update(GOTOOLCHAIN='local', GOENV='off', GOFLAGS='-mod=readonly', RESEARCHOS_GO=go, W16_EVIDENCE_DIR=str(out))
    protected_root = None
    if 'C20' in cases:
        common = Path(subprocess.check_output(['git', 'rev-parse', '--git-common-dir'], cwd=ROOT, text=True, encoding='utf-8').strip())
        if not common.is_absolute():
            common = ROOT / common
        protected_parent = common.resolve().parent.parent / 'verifier-evidence' / 'W16' / 'c20'
        protected_parent.mkdir(parents=True, exist_ok=True)
        protected_root = protected_parent / out.name
        if protected_root.exists():
            parser.error('new C20 protected evidence directory already exists')
        env['W16_PROTECTED_EVIDENCE_DIR'] = str(protected_root)
    cmd = [go, 'test', './internal/domain', '-v', '-count=1', '-timeout=3m', '-run', '^(' + '|'.join(tests) + ')$']
    files = sorted({p for pattern in ('internal/domain/*.go', 'migrations/sqlite/*.sql', 'ops/supervisor/*.go', 'ops/canary/fixture/*.go', 'evaluation/evolution/*.go', 'ops/experiment_sandbox/*.go', 'ops/ci/evolution.py', 'tests/evolution/*', 'go.mod', 'go.sum', 'spec/v2.0/contracts/*.json') for p in ROOT.glob(pattern) if p.is_file()})
    before = {
        'run_receipt': {'task_id': task, 'check_id': check or None, 'case_id': case or None, 'run_id': out.name, 'started_at': now(), 'environment_mode': 'FIXTURE_WITH_NATIVE_APPCONTAINER', 'os': platform.platform(), 'architecture': platform.machine(), 'timezone': time.tzname, 'executor_identity': os.getenv('RESEARCHOS_EXECUTOR_ID', 'codex:/root/experiments'), 'independent_verifier_identity': None},
        'version_manifest': {'code_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, encoding='utf-8').strip(), 'dirty': subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True, encoding='utf-8').strip(), 'files': {str(p.relative_to(ROOT)): digest(p) for p in files}, 'model': 'NONE; public deterministic executable', 'suite_revision': 'public-system-regression-v1', 'formal_holdout': 'NOT_RUN', 'private_fixture_store': str(protected_root) if protected_root else None},
        'command_receipt': {'command_key': command_key, 'argv': cmd, 'cwd': str(ROOT), 'environment_names': sorted(env), 'requested_mode': args.mode, 'resolved_mode': 'fixture'},
        'expected_assertion_ids': expected, 'scope': 'W16_G02_FIXTURE_ONLY', 'execution_status': 'EXECUTION_REPORTED',
        'acceptance_receipt': {'status': 'NOT_REQUESTED', 'verifier_identity': None},
    }
    (out / 'before.json').write_text(json.dumps(before, ensure_ascii=False, indent=2), encoding='utf-8')
    try:
        result = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, timeout=195)
        stdout, stderr, code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, code = exc.stdout or b'', exc.stderr or b'', 124
    (out / 'stdout.txt').write_bytes(stdout)
    (out / 'stderr.txt').write_bytes(stderr)
    passed, rows = verify(stdout, code, expected)
    objective_code = None
    if protected_root is not None:
        objective = subprocess.run([go, 'test', './ops/supervisor', '-run', '^TestObjectiveHoldoutGain$', '-v', '-count=1'], cwd=ROOT, env=env, capture_output=True, timeout=90)
        objective_code = objective.returncode
        (out / 'objective-gain-stdout.txt').write_bytes(objective.stdout)
        (out / 'objective-gain-stderr.txt').write_bytes(objective.stderr)
        passed = passed and objective_code == 0 and protected_root.is_dir() and any(protected_root.glob('*.bin'))
    ids = [row['assertion_id'] for row in rows]
    report = {'schema': 'GLOBAL_EVIDENCE_V1_CANDIDATE', 'status': ('PARTIAL' if selector == 'A16' else 'PASS') if passed else 'FAIL', 'fixture_assertion_status': 'PASS' if passed else 'FAIL', 'execution_status': 'EXECUTION_REPORTED', 'scope': 'W16_G02_FIXTURE_ONLY', 'selector': selector, 'exit_code': code, 'objective_gain_test_exit_code': objective_code, 'protected_store_locator': str(protected_root) if protected_root else None, 'assertion_ids': ids, 'assertions': rows, 'missing': sorted(set(expected) - set(ids)), 'unexpected': sorted(set(ids) - set(expected)), 'ended_at': now(), 'hashes': {str(p.relative_to(out)): digest(p) for p in out.rglob('*') if p.is_file()}, 'independent_acceptance': 'NONE', 'formal_A16': 'PARTIAL_FIXTURE_ONLY', 'W16_G01': 'NOT_ACCEPTED', 'W16_G03': 'BLOCKED_W14_LIVE', 'production_scheduler_upgrade': 'NOT_CONNECTED', 'independent_OS_service': 'NOT_QUALIFIED', 'host_crash_restart_reconciliation': 'NOT_TESTED', 'migration_scope': 'NEW_TEMP_SQLITE_ONLY', 'rollback_scope': 'W18 actual isolated data restore and exact stable native health; production data not switched'}
    (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'fixture_assertion_status': report['fixture_assertion_status'], 'assertions': len(rows), 'assertion_ids': ids, 'receipt': str(out / 'report.json')}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
