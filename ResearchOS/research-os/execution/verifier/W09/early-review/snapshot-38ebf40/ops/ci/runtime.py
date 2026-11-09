"""W05 executable assertions; live execution is explicit and never replaced by fixtures."""
import datetime
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_IDS = {
    'W05-G01-SETTLED', 'W05-G01-FAKE-SUCCESS', 'W05-G01-DUPLICATE',
    'W05-G01-TOOL-FAILED', 'W05-G01-REDACTION', 'W05-G01-NESTED-JOB-TREE',
    'W05-G01-STALE-CANCEL', 'W05-G01-CANCELLED', 'W05-G01-QUEUE',
    'W05-G01-NO-LATE-LAUNCH', 'W05-G01-RECONCILE-CANCEL', 'W05-G01-TIMEOUT',
    'W05-G01-CRASH-UNKNOWN', 'W05-G01-NO-BLIND-RETRY', 'W05-G01-FAILED-QUEUE',
    'W05-G01-CANCEL-WRITE-FAIL', 'W05-G01-SERVICE-REPORTED', 'W05-G01-NO-SELF-ACCEPT',
    'W05-G01-CONTEXT-SCOPE', 'W05-G01-SCOPED-DENIALS', 'W05-G01-REVOKED', 'W05-G01-UNKNOWN-FENCE',
    'W05-G01-MISSING-OUTPUT', 'W05-G01-LOG-NOT-OUTPUT',
    'W05-G01-TOOL-POLICY-FAILURE', 'W05-G01-ACTIVE-BEGIN-FENCE',
    'W05-G01-INSPECTION-UNKNOWN',
    'W05-G01-MANIFEST-EXTRA', 'W05-G01-MANIFEST-SUBSTITUTE', 'W05-G01-MANIFEST-MISSING',
    'W05-G01-MANIFEST-DUPLICATE', 'W05-G01-MANIFEST-EXACT',
    'W05-G01-MANIFEST-CHECKPOINT-SCOPE',
}
LIVE_IDS = {'A04-01-SUCCESS', 'A04-01-TOOL-FAILED', 'A04-03-TIMEOUT', 'A04-02-CANCEL', 'A04-03-CRASH', 'A04-03-CONTEXT-REBUILD', 'W05-LIVE-CLI-QUEUE-CANCEL'}

def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('fixture', 'live'), required=True)
    parser.add_argument('--subcase', choices=('success', 'tool_failed', 'request_timeout', 'pending_queue_cancel', 'executor_crash'))
    args = parser.parse_args()
    mode = args.mode
    if args.subcase and mode != 'live':
        parser.error('subcase requires live mode')
    task = os.getenv('RESEARCHOS_TASK_ID', 'W05')
    check = os.getenv('RESEARCHOS_CHECK_ID', '')
    case = os.getenv('RESEARCHOS_CASE_ID', '')
    if task != 'W05' or check not in ('', 'W05-G01', 'W05-G02') or case not in ('', 'A04') or (not check and not case) or (case and check == 'W05-G01') or (mode == 'fixture' and (check != 'W05-G01' or case)) or (mode == 'live' and check == 'W05-G01'):
        print('invalid or empty W05 selector', file=sys.stderr)
        return 2
    live = mode == 'live'
    if live and os.getenv('RESEARCHOS_RUNTIME_LIVE') != '1':
        print('A04 requires explicit RESEARCHOS_RUNTIME_LIVE=1 and authorized Codex credentials', file=sys.stderr)
        return 2
    go = os.getenv('RESEARCHOS_GO') or str(ROOT / '.local/tools/go1.27.1/go/bin/go.exe')
    if not Path(go).exists():
        print('set RESEARCHOS_GO to the pinned Go executable', file=sys.stderr)
        return 2
    out = ROOT / 'execution/receipts/W05' / str(uuid.uuid4())
    out.mkdir(parents=True)
    env = os.environ.copy()
    env['W05_EVIDENCE_DIR'] = str(out)
    packages = ['./adapters/runtime', './internal/domain']
    pattern = '^TestW05Live' if live else '^TestW05(Protocol|Windows|Service|Scope|Unknown)'
    if args.subcase:
        pattern = '^TestW05Live/' + args.subcase + '$'
    cmd = [go, 'test', *packages, '-v', '-count=1', '-timeout=15m', '-run', pattern]
    before = {
        'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'os': platform.platform(), 'timezone': list(__import__('time').tzname),
        'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'dirty': subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True),
        'files': {str(p.relative_to(ROOT)): digest(p) for group in ('adapters/runtime/*', 'internal/domain/runtime*', 'spec/v2.0/contracts/*.json', 'go.mod', 'go.sum') for p in ROOT.glob(group) if p.is_file()},
        'argv': cmd, 'cwd': str(ROOT), 'environment_names': sorted(env), 'mode': 'LIVE_WINDOWS_AND_SERVICE' if live else 'FIXTURE_AND_NATIVE_WINDOWS',
    }
    (out / 'before.json').write_text(json.dumps(before, ensure_ascii=False, indent=2), encoding='utf-8')
    run = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, timeout=920)
    (out / 'stdout.txt').write_bytes(run.stdout)
    (out / 'stderr.txt').write_bytes(run.stderr)
    rows = []
    for line in run.stdout.decode('utf-8', errors='replace').splitlines():
        if line.startswith('W05_ASSERTION '):
            row = json.loads(line[len('W05_ASSERTION '):])
            row['raw'] = 'stdout.txt'
            rows.append(row)
    ids = [x['assertion_id'] for x in rows]
    expected = LIVE_IDS if live else FIXTURE_IDS
    if args.subcase:
        expected = {'success': {'A04-01-SUCCESS'}, 'tool_failed': {'A04-01-TOOL-FAILED'}, 'request_timeout': {'A04-03-TIMEOUT'}, 'pending_queue_cancel': {'W05-LIVE-CLI-QUEUE-CANCEL', 'A04-02-CANCEL'}, 'executor_crash': {'A04-03-CRASH', 'A04-03-CONTEXT-REBUILD'}}[args.subcase]
    passed = run.returncode == 0 and len(ids) == len(expected) and set(ids) == expected and all(x['status'] == 'PASS' for x in rows)
    status = 'PASS' if passed else ('BLOCKED' if run.returncode == 0 and len(ids) == len(expected) and set(ids) == expected and any(x['status'] == 'BLOCKED' for x in rows) else 'FAIL')
    report = {'task': task, 'check': check, 'case': case, 'status': status, 'exit': run.returncode, 'assertion_ids': ids, 'expected_assertion_ids': sorted(expected), 'assertions': rows, 'passed': passed, 'independent_acceptance': 'NOT_REQUESTED', 'stdout_hash': digest(out/'stdout.txt'), 'stderr_hash': digest(out/'stderr.txt')}
    report['scope'] = 'SUBCASE_ONLY:' + args.subcase if args.subcase else 'SELECTED_GATE'
    (out/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'passed': passed, 'assertions': len(rows), 'assertion_ids': ids, 'receipt': str(out/'report.json')}))
    return 0 if passed else 1

if __name__ == '__main__':
    raise SystemExit(main())
