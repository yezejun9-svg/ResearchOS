"""W13 real HTTP/SQLite backend subset; never signs browser or final acceptance."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = json.loads((ROOT / 'tests/ui-backend/expected.json').read_text(encoding='utf-8'))
SUITES = {
    'all': list(EXPECTED),
    'C17': ['TestW13Milestones', 'TestW13MilestoneGates', 'TestW13GoalMilestone'],
    'C18': ['TestW13Progress'],
    'C25': ['TestW13PreviewAndFiltering'],
    'C26': ['TestW13EventStream', 'TestW13StreamExpiryAndAuthorization', 'TestW13PreviewAndFiltering'],
}


def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--suite', choices=list(SUITES), default='all')
    args = parser.parse_args()
    if os.getenv('RESEARCHOS_TASK_ID') != 'W13':
        parser.error('RESEARCHOS_TASK_ID=W13 required')
    go = os.getenv('RESEARCHOS_GO') or str(ROOT / '.local/tools/go1.27.1/go/bin/go.exe')
    if not Path(go).is_file():
        parser.error('RESEARCHOS_GO must point to the pinned Go executable')
    run_id = str(uuid.uuid4())
    out = ROOT / 'execution/receipts/W13/backend' / run_id
    out.mkdir(parents=True)
    names = SUITES[args.suite]
    expected = [v for name in names for v in EXPECTED[name]]
    if not expected or len(expected) != len(set(expected)):
        raise RuntimeError('empty or duplicate expected assertions')
    env = dict(os.environ)
    env['W13_EVIDENCE_DIR'] = str(out)
    cmd = [go, 'test', './internal/domain', '-v', '-count=1', '-timeout=3m', '-run', '^(' + '|'.join(names) + ')$']
    patterns = ['internal/domain/*.go', 'internal/store/*.go', 'migrations/sqlite/*.sql', 'spec/v2.0/contracts/*.json', 'go.mod', 'go.sum', 'ops/ci/ui_backend.py', 'tests/ui-backend/*']
    manifest = {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p) for pattern in patterns for p in ROOT.glob(pattern) if p.is_file()}
    before = {
        'schema': 'GLOBAL_EVIDENCE_V1_CANDIDATE', 'task_id': 'W13', 'run_id': run_id,
        'suite': args.suite, 'scope': 'DEVELOPMENT_ONLY_BACKEND_SUBSET',
        'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'code_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'dirty': subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True),
        'argv': cmd, 'cwd': str(ROOT), 'os': platform.platform(),
        'go_version': subprocess.check_output([go, 'version'], cwd=ROOT, text=True).strip(),
        'python_version': platform.python_version(), 'source_manifest': manifest,
        'implementation_model': 'gpt-6-astra', 'reasoning_effort': 'high',
        'executor_identity': 'codex:/root/resources', 'verifier_identity': None,
        'environment': 'real loopback HTTP and local SQLite; explicit deterministic fixtures',
        'expected_assertion_ids': expected,
        'limitations': ['No browser screenshots or interactions in this suite', 'No mobile/remote-device qualification', 'W05 live gate remains blocked', 'VERIFYING states and invalidation/old-event faults are explicitly identified fixture setup'],
    }
    save(out / 'before.json', before)
    try:
        run = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, timeout=190)
        stdout, stderr, code = run.stdout, run.stderr, run.returncode
    except subprocess.TimeoutExpired as e:
        stdout, stderr, code = e.stdout or b'', e.stderr or b'', 124
    (out / 'stdout.txt').write_bytes(stdout)
    (out / 'stderr.txt').write_bytes(stderr)
    rows, raw, malformed = [], [], False
    for line_no, line in enumerate(stdout.decode('utf-8', errors='replace').splitlines(), 1):
        if not line.startswith('W13_ASSERTION '):
            continue
        value = line.removeprefix('W13_ASSERTION ')
        raw.append(value)
        try:
            row = json.loads(value)
            if not all(k in row for k in ['assertion_id', 'expected', 'actual', 'status', 'evidence']):
                malformed = True
            row['raw_evidence'] = {'path': 'stdout.txt', 'line': line_no, 'sha256': digest(out / 'stdout.txt')}
            rows.append(row)
        except ValueError:
            malformed = True
    (out / 'assertions.jsonl').write_text('\n'.join(raw) + ('\n' if raw else ''), encoding='utf-8')
    ids = [r.get('assertion_id') for r in rows]
    changed = [name for name, h in manifest.items() if not (ROOT / name).is_file() or digest(ROOT / name) != h]
    passed = code == 0 and not malformed and not changed and len(ids) == len(expected) and set(ids) == set(expected) and all(r['status'] == 'PASS' for r in rows)
    hashes = {str(p.relative_to(out)).replace('\\', '/'): digest(p) for p in out.rglob('*') if p.is_file()}
    report = {
        'task_id': 'W13', 'run_id': run_id, 'suite': args.suite, 'backend_status': 'PASS' if passed else 'FAIL',
        'scope': 'DEVELOPMENT_ONLY_BACKEND_SUBSET', 'executor_status': 'EXECUTION_REPORTED',
        'independent_acceptance': 'NOT_REQUESTED', 'formal_cases': 'PARTIAL_REQUIRES_BROWSER_EVIDENCE',
        'exit_code': code, 'assertions': rows, 'assertion_ids': ids, 'missing': sorted(set(expected) - set(ids)),
        'malformed': malformed, 'changed_during_run': changed, 'raw_evidence_hashes': hashes,
        'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'blocked_gate': 'W05 live qualification / final W13 dependencies',
    }
    save(out / 'report.json', report)
    print(json.dumps({'backend_status': report['backend_status'], 'assertions': len(rows), 'receipt': str(out / 'report.json'), 'formal_cases': report['formal_cases']}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
