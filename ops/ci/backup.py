"""Strict W18 selectors, native file-backed SQLite and negative recovery evidence."""
import argparse
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

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = json.loads((ROOT / 'tests/backup/expected.json').read_text(encoding='utf-8'))
GROUPS = {
    'W18-G01': ['TestW18NegativeRecovery', 'TestW18Boundaries'],
    'W18-G02': list(EXPECTED),
    'A12': list(EXPECTED),
}


def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['fixture', 'live'])
    args = parser.parse_args()
    task, check, case = (os.getenv(k, '') for k in ['RESEARCHOS_TASK_ID', 'RESEARCHOS_CHECK_ID', 'RESEARCHOS_CASE_ID'])
    if task != 'W18' or bool(check) == bool(case) or check and check not in ['W18-G01', 'W18-G02'] or case and case != 'A12':
        parser.error('exactly one known W18 check or owned A12 selector is required')
    selector = check or case
    mode = args.mode or ('fixture' if selector == 'W18-G01' else 'live')
    if (mode == 'fixture') != (selector == 'W18-G01'):
        parser.error('W18-G01 is FIXTURE; W18-G02 and A12 require LIVE_WINDOWS storage recovery')
    if mode == 'live' and platform.system() != 'Windows':
        parser.error('LIVE_WINDOWS cannot be claimed on another operating system')
    go = os.getenv('RESEARCHOS_GO') or str(ROOT / '.local/tools/go1.27.1/go/bin/go.exe')
    if not Path(go).is_file():
        parser.error('RESEARCHOS_GO must identify the pinned executable')
    names = GROUPS[selector]
    expected = [a for n in names for a in EXPECTED[n]]
    if not expected or len(expected) != len(set(expected)):
        raise RuntimeError('nonempty unique frozen assertion inventory required')
    run_id = str(uuid.uuid4())
    out = ROOT / 'execution/receipts/W18' / run_id
    out.mkdir(parents=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith('W18_')}
    env['RESEARCHOS_GO'] = go
    env['W18_EVIDENCE_DIR'] = str(out)
    command = [go, 'test', './internal/domain', '-v', '-count=1', '-timeout=3m', '-run', '^(' + '|'.join(names) + ')$']
    patterns = ['internal/domain/*.go', 'internal/store/*.go', 'adapters/retrieval/*.go', 'migrations/sqlite/*.sql', 'spec/v2.0/contracts/*.json', 'go.mod', 'go.sum', 'execution/route.json', 'ops/backup/*', 'ops/export/*', 'ops/restore/*', 'tests/backup/*', 'ops/ci/backup.py']
    manifest = {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p) for pattern in patterns for p in ROOT.glob(pattern) if p.is_file()}
    before = {
        'schema': 'GLOBAL_EVIDENCE_V1_CANDIDATE', 'task_id': task, 'check_id': check, 'case_id': case, 'run_id': run_id,
        'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'environment_mode': 'FIXTURE' if mode == 'fixture' else 'LIVE_WINDOWS',
        'os': platform.platform(), 'architecture': platform.machine(), 'timezone': list(time.tzname),
        'executor_identity': os.getenv('RESEARCHOS_EXECUTOR_ID', 'codex:/root/resources'), 'verifier_identity': None,
        'code_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'dirty': subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True),
        'command_key': 'test.backup', 'registered_command_revision': 'ROOT_INTEGRATION_PENDING', 'argv': command, 'cwd': str(ROOT),
        'environment_names': sorted(env), 'version_manifest': manifest,
        'go_version': subprocess.check_output([go, 'version'], cwd=ROOT, text=True).strip(), 'python_version': platform.python_version(),
        'implementation_model': 'gpt-6-astra', 'reasoning_effort': 'high', 'runtime_model': {'status': 'NOT_APPLICABLE', 'reason': 'storage recovery invokes no external model'},
        'adapters': 'real Windows SQLite/WAL and filesystem; synthetic business workload; fixture runtime only',
        'rubric': 'spec/v2.0/contracts/acceptance.json A12-01..04; nonzero frozen subassertions',
        'scope': 'W18 storage recovery qualification only; W05/W12 live model qualification remains blocked',
        'resource_request_id': 'RQ-W05-CLI-POLICY-001', 'expected_assertion_ids': sorted(expected),
        'assumptions': ['local administrative recovery key kept separate', 'protected content backup requires W17 and is refused'],
        'revalidation_inputs': ['schema migrations', 'domain acceptance and recovery semantics', 'W17 protected backup capability', 'W05 live resource qualification'],
    }
    save(out / 'before.json', before)
    try:
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=190)
        stdout, stderr, code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as e:
        stdout, stderr, code = e.stdout or b'', e.stderr or b'', 124
    (out / 'stdout.txt').write_bytes(stdout)
    (out / 'stderr.txt').write_bytes(stderr)
    rows, malformed = [], False
    for number, line in enumerate(stdout.decode('utf-8', errors='replace').splitlines(), 1):
        if line.startswith('W18_ASSERTION '):
            try:
                row = json.loads(line[len('W18_ASSERTION '):])
                if not all(k in row for k in ['assertion_id', 'expected', 'actual', 'status', 'evidence']):
                    malformed = True
                row['raw_evidence'] = {'path': 'stdout.txt', 'line': number, 'sha256': digest(out / 'stdout.txt')}
                rows.append(row)
            except ValueError:
                malformed = True
    ids = [r.get('assertion_id') for r in rows]
    drift = [p for p, h in manifest.items() if not (ROOT / p).is_file() or digest(ROOT / p) != h]
    passed = code == 0 and not malformed and not drift and len(ids) == len(expected) and set(ids) == set(expected) and all(r['status'] == 'PASS' and r['expected'] == r['actual'] for r in rows)
    index = {str(p.relative_to(out)).replace('\\', '/'): digest(p) for p in out.rglob('*') if p.is_file()}
    report = {'task_id': task, 'check_id': check, 'case_id': case, 'run_id': run_id, 'status': 'PASS' if passed else 'FAIL',
              'executor_status': 'EXECUTION_REPORTED', 'exit_code': code, 'assertions': rows, 'assertion_ids': ids,
              'expected_assertion_ids': sorted(expected), 'missing': sorted(set(expected) - set(ids)), 'malformed': malformed, 'source_drift': drift,
              'raw_evidence_hashes': index, 'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'environment_mode': before['environment_mode'], 'independent_acceptance': 'NOT_REQUESTED',
              'scope': before['scope'], 'w05_runtime_qualification': 'BLOCKED_RQ-W05-CLI-POLICY-001',
              'global_evidence': 'CANDIDATE_PENDING_INDEPENDENT_VERIFIER'}
    save(out / 'report.json', report)
    print(json.dumps({'status': report['status'], 'assertions': len(rows), 'receipt': str(out / 'report.json')}))
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
