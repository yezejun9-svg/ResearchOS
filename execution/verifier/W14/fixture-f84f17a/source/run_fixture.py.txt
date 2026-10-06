"""W14-G01: real loopback HTTP and SQLite, explicitly synthetic provider/runtime data."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import time
import traceback
import uuid

ROOT = Path(__file__).resolve().parents[2]


def digest(path: Path) -> str:
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if os.environ.get('RESEARCHOS_TASK_ID') != 'W14':
        raise SystemExit('RESEARCHOS_TASK_ID=W14 required')
    locked = json.loads((ROOT / 'execution/toolchains/locked.json').read_text(encoding='utf-8'))
    go = Path(os.environ.get('RESEARCHOS_GO', locked['tools']['go']['path']))
    if not go.is_file():
        raise SystemExit('Locked Go executable unavailable')
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    out = ROOT / 'execution/receipts/W14/fixture' / run_id
    out.mkdir(parents=True)
    report = {
        'task_id': 'W14', 'gate_id': 'W14-G01', 'run_id': run_id, 'scope': 'FIXTURE_SYNTHETIC',
        'execution_status': 'EXECUTION_REPORTED', 'status': 'FAIL', 'cwd': str(ROOT), 'os': platform.platform(),
        'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'command': ['python', 'tests/e2e_cycle/run_fixture.py'], 'commands': [], 'error': None,
        'project_identity': json.loads((ROOT / 'execution/project_identity.json').read_text(encoding='utf-8')),
        'limitations': [
            'No A13/G02 or real provider, Jev, executor, host isolation, UI, or product qualification claim.',
            'Package-local sourceFixtureAdapter returns synthetic pages; production source sealing writes LIVE metadata even in this injected fixture. These records remain FIXTURE_SYNTHETIC evidence.',
            'ObserveRuntime is an explicit synthetic fixture observation, not an OS process observation.',
            'Independent acceptance is the real deterministic product service; construction acceptance requires the external verifier.',
            'New-process continuation proves persisted API state and next-step continuity, not an autonomous agent session.',
        ],
    }
    tracked = subprocess.check_output(['git', 'ls-files', 'internal/domain', 'internal/store', 'adapters', 'migrations/sqlite', 'spec/v2.0/contracts', 'go.mod', 'go.sum'], cwd=ROOT, text=True).splitlines()
    paths = [ROOT / name for name in tracked]
    paths.extend(p for p in (ROOT / 'tests/e2e_cycle').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    report['source_hashes'] = {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p) for p in sorted(set(paths))}
    report['go_tool'] = {'path': str(go), 'sha256': digest(go)}
    contract_path = ROOT / 'evaluation/project_cycle/fixture_contract.json'
    contract = json.loads(contract_path.read_text(encoding='utf-8'))
    report['fixture_contract_sha256'] = digest(contract_path)
    start = time.monotonic()

    def command(name: str, argv: list[str], env: dict[str, str], timeout: int = 120) -> None:
        began = time.monotonic()
        result = subprocess.run(argv, cwd=ROOT / 'internal/domain', env=env, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=timeout)
        (out / f'{name}.stdout.txt').write_text(result.stdout, encoding='utf-8')
        (out / f'{name}.stderr.txt').write_text(result.stderr, encoding='utf-8')
        report['commands'].append({'name': name, 'argv': argv, 'cwd': str(ROOT / 'internal/domain'),
                                   'exit_code': result.returncode, 'elapsed_seconds': round(time.monotonic() - began, 3)})
        if result.returncode:
            raise RuntimeError(f'{name} failed ({result.returncode}); see raw stdout/stderr')

    try:
        with tempfile.TemporaryDirectory(prefix='researchos-w14-') as temporary:
            temp = Path(temporary).resolve()
            overlay = {'Replace': {str(ROOT / 'internal/domain/w14_cycle_overlay_test.go'): str(ROOT / 'tests/e2e_cycle/_fixture/cycle_test.go')}}
            overlay_path = temp / 'overlay.json'
            overlay_path.write_text(json.dumps(overlay, ensure_ascii=False), encoding='utf-8')
            (out / 'overlay.json').write_bytes(overlay_path.read_bytes())
            report['overlay_sha256'] = digest(overlay_path)
            executable = temp / 'w14-fixture.test.exe'
            env = dict(os.environ, GOTOOLCHAIN='local', GOENV='off', W14_DATABASE=str(temp / 'domain.sqlite'),
                       W14_EVIDENCE_DIR=str(out), W14_PHASE='build')
            command('build', [str(go), 'test', '-c', '-overlay', str(overlay_path), '-o', str(executable), '.'], env, 180)
            report['test_binary_sha256'] = digest(executable)
            for phase, test in [('vertical', 'TestW14VerticalCycle'), ('resume', 'TestW14SessionResume'), ('missing-source', 'TestW14MissingSource')]:
                command(phase, [str(executable), '-test.run', '^' + test + '$', '-test.v', '-test.timeout', '90s'], dict(env, W14_PHASE=phase))
            report['database_sha256_before_cleanup'] = digest(temp / 'domain.sqlite')
        report['temporary_database_removed'] = not temp.exists()
        entries = [json.loads(line) for p in sorted(out.glob('*.jsonl')) for line in p.read_text(encoding='utf-8').splitlines()]
        assertions = [e for e in entries if e['record_type'] == 'assertion']
        assert {e['assertion_id'] for e in assertions} == set(contract['required_assertions'])
        assert all(e['status'] == 'PASS' for e in assertions)
        assert len({e['assertion_id'] for e in assertions}) == len(assertions)
        report['status'] = 'PASS'
    except Exception:
        report['error'] = traceback.format_exc()
    finally:
        entries = [json.loads(line) for p in sorted(out.glob('*.jsonl')) for line in p.read_text(encoding='utf-8').splitlines()]
        assertions = [e for e in entries if e['record_type'] == 'assertion']
        report['assertions'] = assertions
        report['assertion_count'] = len(assertions)
        report['http_count'] = sum(e['record_type'] == 'http' for e in entries)
        report['rejected_http_count'] = sum(e['record_type'] == 'http' and 400 <= e['status'] < 500 for e in entries)
        report['elapsed_seconds'] = round(time.monotonic() - start, 3)
        report['files'] = {p.name: digest(p) for p in sorted(out.iterdir()) if p.is_file() and p.name != 'report.json'}
        (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'scope': report['scope'], 'assertions': report.get('assertion_count', 0),
                      'report': str(out / 'report.json')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
