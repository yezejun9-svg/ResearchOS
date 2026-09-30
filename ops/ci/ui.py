"""Run one frozen W13 browser phase and bind its raw evidence to a selector."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / 'apps/web'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['core', 'contracts', 'workflow', 'content', 'recovery'], default='core')
    phase = parser.parse_args().phase
    check, case = os.getenv('RESEARCHOS_CHECK_ID', ''), os.getenv('RESEARCHOS_CASE_ID', '')
    allowed = {'core': ['W13-G02', 'C24'], 'contracts': ['W13-G01', 'C17', 'C18'], 'workflow': ['C23'], 'content': ['C25'], 'recovery': ['C26']}
    if os.getenv('RESEARCHOS_TASK_ID') != 'W13' or bool(check) == bool(case) or (check or case) not in allowed[phase]:
        parser.error('one matching W13 task gate or case selector required')
    expected = json.loads((ROOT / 'tests/ui/expected.json').read_text(encoding='utf-8'))[phase]
    if not expected or len(expected) != len(set(expected)):
        raise RuntimeError('empty or duplicate expected browser checks')
    run_id = str(uuid.uuid4())
    out = ROOT / ('execution/receipts/W13/c26-recovery/registered' if phase == 'recovery' else 'execution/receipts/W13/registered') / run_id
    out.mkdir(parents=True)
    def digest(path):
        return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()
    def save(name, value):
        (out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    patterns = ['apps/control/*.go', 'apps/web/src/*', 'apps/web/package*.json', 'apps/web/index.html',
                'internal/**/*.go', 'adapters/**/*.go', 'migrations/sqlite/*.sql', 'spec/v2.0/contracts/*.json',
                'spec/v2.0/ui/*.json', 'tests/ui/**/*.go', 'tests/ui/*.py', 'tests/ui/expected.json',
                'ops/ci/ui.py', 'execution/commands.json', 'go.mod', 'go.sum', 'execution/toolchains/locked.json']
    sources = {p.relative_to(ROOT).as_posix(): digest(p) for pattern in patterns for p in ROOT.glob(pattern) if p.is_file()}
    before = {'task_id': 'W13', 'run_id': run_id, 'phase': phase, 'check_id': check, 'case_id': case,
              'code_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'source_manifest': sources,
              'executor_identity': os.getenv('RESEARCHOS_EXECUTOR_ID', 'local:operator'), 'expected_checks': expected,
              'scope': 'REAL_WINDOWS_BROWSER_WITH_EXPLICIT_SQLITE_FIXTURES', 'physical_phone': False, 'physical_os_sleep': False}
    before['dirty_before'] = subprocess.check_output(['git', 'status', '--short', '--untracked-files=all'], cwd=ROOT, text=True).splitlines()
    save('before.json', before)
    locked = json.loads((ROOT / 'execution/toolchains/locked.json').read_text(encoding='utf-8'))
    node = Path(locked['tools']['node']['path'])
    vite = WEB / 'node_modules/vite/bin/vite.js'
    if not node.is_file() or not vite.is_file():
        raise SystemExit('pinned Node or npm ci dependencies unavailable')
    build_command = [str(node), str(vite), 'build']
    command = [sys.executable, '-X', 'utf8', str(ROOT / 'tests/ui/browser_smoke.py')]
    save('commands.json', [{'argv': build_command, 'cwd': str(WEB)}, {'argv': command, 'cwd': str(ROOT), 'phase': phase}])
    build = subprocess.run(build_command, cwd=WEB, capture_output=True, timeout=120)
    (out / 'build.stdout.txt').write_bytes(build.stdout)
    (out / 'build.stderr.txt').write_bytes(build.stderr)
    code, report, child = build.returncode, {}, None
    if code == 0:
        try:
            run = subprocess.run(command, cwd=ROOT, env=dict(os.environ, RESEARCHOS_UI_PHASE=phase), capture_output=True, timeout=480)
            stdout, stderr, code = run.stdout, run.stderr, run.returncode
        except subprocess.TimeoutExpired as error:
            stdout, stderr, code = error.stdout or b'', error.stderr or b'', 124
        (out / 'browser.stdout.txt').write_bytes(stdout)
        (out / 'browser.stderr.txt').write_bytes(stderr)
        for line in reversed(stdout.decode('utf-8', errors='replace').splitlines()):
            try:
                value = json.loads(line)
            except ValueError:
                continue
            if isinstance(value, dict) and 'report' in value:
                child = Path(value['report']).resolve()
                if not child.is_relative_to(ROOT / ('execution/receipts/W13/c26-recovery/browser' if phase == 'recovery' else 'execution/receipts/W13/frontend')):
                    raise RuntimeError('browser receipt escaped evidence directory')
                report = json.loads(child.read_text(encoding='utf-8'))
                break
    actual = report.get('checks', [])
    drift = [p for p, h in sources.items() if not (ROOT / p).is_file() or digest(ROOT / p) != h]
    passed = code == 0 and report.get('status') == 'PASS' and report.get('phase') == phase and actual == expected and not drift
    if child:
        for name, h in report.get('screenshot_hashes', {}).items():
            if digest(child.parent / name) != h:
                passed = False
    rows = [{'assertion_id': f'W13-UI-{phase.upper()}-{i+1:02}', 'expected': value,
             'actual': actual[i] if i < len(actual) else None, 'status': 'PASS' if passed else 'FAIL',
             'evidence': {'report': child.relative_to(ROOT).as_posix() if child else None, 'check_index': i}}
            for i, value in enumerate(expected)]
    hashes = {p.name: digest(p) for p in out.iterdir() if p.is_file()}
    save('report.json', {'task_id': 'W13', 'run_id': run_id, 'phase': phase, 'status': 'PASS' if passed else 'FAIL',
                         'exit_code': code, 'assertions': rows, 'assertion_ids': [r['assertion_id'] for r in rows],
                         'expected_checks': expected, 'actual_checks': actual, 'source_drift': drift,
                         'child_report': child.relative_to(ROOT).as_posix() if child else None,
                         'child_report_hash': digest(child) if child else None, 'raw_evidence_hashes': hashes,
                         'scope': before['scope'], 'independent_acceptance': 'PENDING',
                         'qualification_status': 'PARTIAL' if phase == 'recovery' else 'NOT_ASSESSED',
                         'physical_os_sleep': False, 'physical_phone': False,
                         'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    print(json.dumps({'status': 'PASS' if passed else 'FAIL', 'assertions': len(rows), 'assertion_ids': [r['assertion_id'] for r in rows], 'receipt': str(out / 'report.json')}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())

