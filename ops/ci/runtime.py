"""W05 executable assertions; live execution is explicit and never replaced by fixtures."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]

def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    task = os.getenv('RESEARCHOS_TASK_ID', 'W05')
    check = os.getenv('RESEARCHOS_CHECK_ID', '')
    case = os.getenv('RESEARCHOS_CASE_ID', '')
    if task != 'W05' or check not in ('', 'W05-G01', 'W05-G02') or case not in ('', 'A04') or (case and check == 'W05-G01'):
        print('invalid or empty W05 selector', file=sys.stderr)
        return 2
    live = check == 'W05-G02' or case == 'A04'
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
    passed = run.returncode == 0 and bool(rows) and all(x['status'] == 'PASS' for x in rows)
    report = {'task': task, 'check': check, 'case': case, 'exit': run.returncode, 'assertions': rows, 'passed': passed, 'independent_acceptance': 'NOT_REQUESTED', 'stdout_hash': digest(out/'stdout.txt'), 'stderr_hash': digest(out/'stderr.txt')}
    (out/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'passed': passed, 'assertions': len(rows), 'receipt': str(out/'report.json')}))
    return 0 if passed else 1

if __name__ == '__main__':
    raise SystemExit(main())
