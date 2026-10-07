"""W11-01 fixture check; all other selectors use the existing W11 harness."""

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid


ROOT = Path(__file__).resolve().parents[3]
KEY = 'test.jev.fixture'
TESTS = ('TestW1101DecisionChain', 'TestW1101Rejections')
EXPECTED = {
    'W11-01-DEFAULT-SHADOW',
    'W11-01-NO-CALLER-MUTATION',
    'W11-01-ORIGINAL-FROZEN',
    'W11-01-ONE-DECISION-CHAIN',
    'W11-01-INDEPENDENT-ADOPTION',
    'W11-01-SELF-SIGN-renamed-verifier',
    'W11-01-SELF-SIGN-delegated-verifier',
    'W11-01-INDEPENDENT-ACCEPTANCE',
    'W11-01-SHADOW-DOES-NOT-OVERRIDE',
    'W11-01-HIGH-SCORE-HARD-FAIL',
    'W11-01-TIMEOUT-ABSTAINS',
    'W11-01-STALE-VERSION-REJECTED',
    'W11-01-CROSS-PURPOSE-NO-GRANT',
    'W11-01-NO-AUTO-WITH-OTHER-KEY',
}


def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def owned():
    go = Path(os.getenv('RESEARCHOS_GO') or ROOT / '.local/tools/go1.27.1/go/bin/go.exe')
    if not go.is_file() or len(EXPECTED) != 14:
        raise RuntimeError('pinned Go and exact nonzero W11-01 inventory required')
    out = ROOT / 'execution/v2.4/receipts/W11/W11-01/dispatched' / str(uuid.uuid4())
    out.mkdir(parents=True, exist_ok=False)
    env = {key: value for key, value in os.environ.items()
           if 'JEV' not in key.upper() and 'TYPESAFE' not in key.upper()}
    cmd = [str(go), 'test', './internal/domain', '-v', '-count=1', '-timeout=2m',
           '-run', '^(' + '|'.join(TESTS) + ')$']
    paths = [ROOT / 'internal/domain/decision.go', ROOT / 'internal/domain/decision_w1101_test.go',
             ROOT / 'internal/domain/decision_test.go',
             ROOT / 'adapters/decision/jev.go', Path(__file__)]
    manifest = {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}
    before = {
        'task_id': 'W11', 'check_id': 'W11-01', 'selector': 'W11-01',
        'started_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'argv': cmd, 'cwd': str(ROOT), 'source_hashes': manifest,
        'expected_assertion_ids': sorted(EXPECTED), 'environment_mode': 'FIXTURE',
        'scope': 'development SQLite decision chain and rejection fixtures',
        'independent_acceptance': 'PENDING_INDEPENDENT_REVIEW',
        'live_qualification': 'NOT_ESTABLISHED', 'automatic_authority': 'NONE',
    }
    write(out / 'before.json', before)
    try:
        run = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, timeout=140)
        stdout, stderr, code, timed_out = run.stdout, run.stderr, run.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, code, timed_out = exc.stdout or b'', exc.stderr or b'', 124, True
    (out / 'stdout.txt').write_bytes(stdout)
    (out / 'stderr.txt').write_bytes(stderr)
    rows = []
    malformed = False
    for line_no, line in enumerate(stdout.decode('utf-8', errors='replace').splitlines(), 1):
        if not line.startswith('W11_ASSERTION '):
            continue
        try:
            row = json.loads(line[len('W11_ASSERTION '):])
            if not all(key in row for key in ('assertion_id', 'expected', 'actual', 'status', 'evidence')):
                malformed = True
            row['raw_evidence'] = {'path': 'stdout.txt', 'line': line_no,
                                   'sha256': digest(out / 'stdout.txt')}
            rows.append(row)
        except ValueError:
            malformed = True
    ids = [row.get('assertion_id') for row in rows]
    drift = [name for name, old in manifest.items() if digest(ROOT / name) != old]
    passed = (code == 0 and not timed_out and not malformed and not drift and
              len(ids) == len(EXPECTED) and set(ids) == EXPECTED and
              all(row['status'] == 'PASS' and row['expected'] == row['actual'] for row in rows))
    report = {
        'task_id': 'W11', 'check_id': 'W11-01', 'status': 'PASS' if passed else 'FAIL',
        'child_exit_code': code, 'timed_out': timed_out, 'malformed': malformed,
        'assertion_ids': ids, 'expected_assertion_ids': sorted(EXPECTED),
        'missing': sorted(EXPECTED - set(ids)), 'unexpected': sorted(set(ids) - EXPECTED),
        'source_drift': drift, 'assertions': rows,
        'raw_evidence_hashes': {'stdout.txt': digest(out / 'stdout.txt'),
                                'stderr.txt': digest(out / 'stderr.txt')},
        'ended_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'environment_mode': 'FIXTURE', 'independent_acceptance': 'PENDING_INDEPENDENT_REVIEW',
        'live_qualification': 'NOT_ESTABLISHED', 'automatic_authority': 'NONE',
    }
    write(out / 'report.json', report)
    print(json.dumps({'status': report['status'], 'assertions': len(rows),
                      'assertion_ids': ids, 'receipt': str(out / 'report.json')}, ensure_ascii=False))
    return 0 if passed else 1


def forward():
    entry = json.loads((ROOT / 'execution/commands.json').read_text(encoding='utf-8'))['commands'][KEY]
    return subprocess.run([sys.executable, *entry['argv']], cwd=ROOT / entry['cwd'],
                          env=os.environ.copy()).returncode


def main():
    task = os.getenv('RESEARCHOS_TASK_ID', '')
    check = os.getenv('RESEARCHOS_CHECK_ID', '')
    case = os.getenv('RESEARCHOS_CASE_ID', '')
    if task == 'W11' and check == 'W11-01' and not case:
        return owned()
    return forward()


if __name__ == '__main__':
    raise SystemExit(main())
