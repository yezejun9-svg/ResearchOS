"""W06-01 handler for the v2.4 registry key `test.orchestration`.

Why this file exists instead of a direct binding to ops/ci/orchestration.py:
  * dispatch.py:65 prefers the v2.4 registry as soon as the KEY exists there, so binding test.orchestration in
    v2.4 re-routes every selector of that key, not only W06-01. ops/ci/orchestration.py refuses check ids
    outside ('W06-G01','W06-G02','W06-G03') at line 44, so W06-01 needs a handler, and editing that accepted
    harness is outside this card's write_scope.
  * The accepted pattern (test.context / test.resources / test.runtime / test.ui.routes) is a check program in
    the binding card's own scope that runs the new selector itself and forwards every other selector unchanged.
    That is what this file does.

Forwarding is not a copy of the legacy command line: the argv and cwd are read from the v2.0 registry entry at
run time, so what the accepted harness does, the forwarded selectors keep doing even if that entry moves.
"""
import json
import hashlib
import os
import pathlib
import subprocess
import sys
import uuid
import datetime

ROOT = pathlib.Path(__file__).resolve().parents[3]
LEGACY_REGISTRY = ROOT / 'execution/commands.json'
EXPECTED = json.loads((ROOT / 'tests/orchestration/expected.json').read_text(encoding='utf-8'))
KEY = 'test.orchestration'
OWNED_TASK, OWNED_CHECK = 'W06', 'W06-01'


def registry_entry(path):
    return json.loads(path.read_text(encoding='utf-8'))['commands'][KEY]


def owned_group():
    names = sorted(k for k, ids in EXPECTED.items() if any(str(i).startswith('W06-01-') for i in ids))
    ids = [str(i) for name in names for i in EXPECTED[name]]
    if not names or not ids or len(ids) != len(set(ids)):
        raise RuntimeError('empty or duplicate W06-01 frozen assertion set')
    return names, ids


def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def run_owned(out):
    names, expected = owned_group()
    go = os.getenv('RESEARCHOS_GO') or str(ROOT / '.local/tools/go1.27.1/go/bin/go.exe')
    if not pathlib.Path(go).is_file():
        raise SystemExit('RESEARCHOS_GO must locate the pinned Go executable')
    env = {k: v for k, v in os.environ.items() if not k.startswith('W06_')}
    env['W06_EVIDENCE_DIR'] = str(out)
    cmd = [go, 'test', './internal/domain', '-v', '-count=1', '-timeout=2m',
           '-run', '^(' + '|'.join(names) + ')$']
    before = {
        'selector': 'W06-01', 'owner': 'W06-01', 'argv': cmd, 'cwd': str(ROOT),
        'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=str(ROOT), text=True).strip(),
        'code_tree': subprocess.check_output(['git', 'write-tree'], cwd=str(ROOT), text=True).strip(),
        'dirty': subprocess.check_output(['git', 'status', '--porcelain'], cwd=str(ROOT), text=True),
        'executor': os.getenv('RESEARCHOS_EXECUTOR_ID', 'local:operator'),
        'expected_assertion_ids': sorted(expected), 'owned_tests': names,
        'scope': 'DEVELOPMENT_ONLY',
    }
    (out / 'before.json').write_text(json.dumps(before, ensure_ascii=False, indent=2), encoding='utf-8')
    timed_out = False
    try:
        run = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, timeout=200)
        stdout, stderr, code = run.stdout, run.stderr, run.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, code, timed_out = exc.stdout or b'', exc.stderr or b'', 124, True
    (out / 'stdout.txt').write_bytes(stdout)
    (out / 'stderr.txt').write_bytes(stderr)
    rows, malformed = [], False
    for line_number, line in enumerate(stdout.decode('utf-8', errors='replace').splitlines(), 1):
        if line.startswith('W06_ASSERTION '):
            try:
                row = json.loads(line[len('W06_ASSERTION '):])
                if not all(k in row for k in ('assertion_id', 'expected', 'actual', 'status', 'evidence')):
                    malformed = True
                row['raw'] = {'path': 'stdout.txt', 'line': line_number}
                rows.append(row)
            except ValueError:
                malformed = True
    ids = [row.get('assertion_id') for row in rows]
    passed = (code == 0 and not malformed and len(ids) == len(expected) and set(ids) == set(expected)
              and all(row['status'] == 'PASS' for row in rows))
    report = {
        'task': OWNED_TASK, 'check': OWNED_CHECK, 'case': '', 'status': 'PASS' if passed else 'FAIL',
        'exit': code, 'assertion_ids': ids, 'expected_assertion_ids': sorted(expected), 'assertions': rows,
        'missing': sorted(set(expected) - set(ids)),
        'unexpected': sorted(str(x) for x in set(ids) - set(expected)),
        'timeout': timed_out, 'malformed': malformed,
        'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'hashes': {p.name: digest(p) for p in out.iterdir() if p.is_file()},
        'independent_acceptance': 'NOT_REQUESTED', 'scope': 'DEVELOPMENT_ONLY',
        'live_qualification': 'NOT_THIS_SELECTOR',
    }
    (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'assertions': len(rows), 'assertion_ids': ids,
                      'selector': 'W06-01', 'routing': 'owned-by-tests/orchestration/check/main.py',
                      'receipt': str(out / 'report.json')}, ensure_ascii=False))
    return 0 if passed else 1


def forward(mode_override=None):
    legacy = registry_entry(LEGACY_REGISTRY)
    argv = list(legacy['argv'])
    if mode_override:
        argv = [a for a in argv if a not in ('fixture', 'live')] + ['--mode', mode_override]
    proc = subprocess.run([sys.executable] + argv, cwd=str(ROOT / legacy.get('cwd', '.')), env=os.environ.copy())
    return proc.returncode


def main():
    task = os.getenv('RESEARCHOS_TASK_ID', '')
    check = os.getenv('RESEARCHOS_CHECK_ID', '')
    case = os.getenv('RESEARCHOS_CASE_ID', '')
    if task == OWNED_TASK and check == OWNED_CHECK and not case:
        out = ROOT / 'execution/v2.4/receipts/W06/W06-01/dispatched' / str(uuid.uuid4())
        out.mkdir(parents=True, exist_ok=False)
        return run_owned(out)
    return forward()


if __name__ == '__main__':
    raise SystemExit(main())
