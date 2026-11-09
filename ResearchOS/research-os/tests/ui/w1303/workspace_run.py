"""Observe actual Electron file controls against an isolated production Host.

The native selection callback and local profile are FIXTURE data. No provider
is invoked, and this report does not issue independent acceptance.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import tempfile
import threading
import uuid

ROOT = Path(__file__).resolve().parents[3]


def main():
    run_id = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    out = ROOT / 'execution/v2.4/receipts/W13/W13-03' / ('workspace-' + run_id)
    out.mkdir(parents=True)
    temp = Path(tempfile.mkdtemp(prefix='researchos-w13-ui-workspace-', dir=ROOT / '.local'))
    locked = json.loads((ROOT / 'execution/toolchains/locked.json').read_text(encoding='utf-8-sig'))['tools']
    go = Path(os.environ.get('RESEARCHOS_GO') or locked['go']['path'])
    node = Path(locked['node']['path'])
    report = {'schema': 'researchos.desktop-workspace-observation.v1', 'step_id': 'W13-03',
              'run_id': run_id, 'status': 'EXECUTING', 'measurement_mode': 'DEVELOPMENT',
              'provider_calls': 0, 'formal_cases_accepted': [], 'commands': [], 'source_hashes': {},
              'limitations': ['Native directory selection uses an explicit fixture callback.',
                              'Local profile metadata is not a provider qualification.',
                              'Root observations require independent review for acceptance.']}
    environment = dict(os.environ, GOTOOLCHAIN='local', GOENV='off', RESEARCHOS_TASK_ID='W13',
                       RESEARCHOS_DESKTOP_USER_DATA=str(temp / 'electron-user-data'))
    environment.pop('ROS_DESKTOP_SMOKE', None)
    helper = log = None

    def command(argv, name, timeout=180):
        result = subprocess.run([str(arg) for arg in argv], cwd=ROOT, env=environment,
                                capture_output=True, text=True, encoding='utf-8', timeout=timeout)
        (out / (name + '.stdout.txt')).write_text(result.stdout, encoding='utf-8')
        (out / (name + '.stderr.txt')).write_text(result.stderr, encoding='utf-8')
        report['commands'].append({'argv': [str(arg) for arg in argv], 'exit_code': result.returncode})
        if result.returncode:
            raise RuntimeError(f'{name} exited {result.returncode}; see preserved logs')
        return result.stdout

    try:
        for name, binary in [('go', go), ('node', node)]:
            if hashlib.sha256(binary.read_bytes()).hexdigest() != locked[name]['sha256']:
                raise RuntimeError(f'{name} tool hash mismatch')
        for folder in ['apps/web/src', 'apps/desktop/main', 'apps/desktop/preload', 'tests/ui/w1303',
                       'internal/domain', 'internal/api', 'internal/host', 'apps/control']:
            for file in sorted((ROOT / folder).rglob('*')):
                if file.is_file() and file.suffix in ['.js', '.jsx', '.css', '.cjs', '.py', '.go']:
                    report['source_hashes'][file.relative_to(ROOT).as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
        command([node, ROOT / 'apps/web/node_modules/vite/bin/vite.js', 'build', ROOT / 'apps/web'], 'web-build')
        binary = temp / 'workspace-fixture.exe'
        command([go, 'build', '-o', binary, './tests/ui/w1303/workspace_fixture'], 'fixture-build')
        log = (out / 'service.log').open('w', encoding='utf-8')
        helper = subprocess.Popen([str(binary), '--dir', str(temp / 'service')], cwd=ROOT, env=environment,
                                  stdout=subprocess.PIPE, stderr=log, text=True, encoding='utf-8')
        lines = queue.Queue()
        threading.Thread(target=lambda: lines.put(helper.stdout.readline()), daemon=True).start()
        ready = lines.get(timeout=60)
        fixture = json.loads(ready)
        for field in ['base_url', 'discovery_file', 'project_id', 'session_id', 'workspace_ref', 'workspace_root']:
            if not fixture.get(field):
                raise RuntimeError(f'fixture omitted {field}')
        report['fixture'] = fixture
        input_file = temp / 'workspace-input.json'
        input_file.write_text(json.dumps(fixture, ensure_ascii=False, indent=2), encoding='utf-8')
        environment.update(RESEARCHOS_CLI_DISCOVERY=fixture['discovery_file'],
                           RESEARCHOS_PROJECT_ID=fixture['project_id'])
        command([node, ROOT / 'tests/ui/w1303/workspace.cjs', input_file, out], 'workspace', 180)
        report['status'] = 'PASS'
    except Exception as error:
        report['status'], report['error'] = 'FAIL', str(error)
    finally:
        if helper and helper.poll() is None:
            helper.terminate()
            try:
                helper.wait(timeout=10)
            except subprocess.TimeoutExpired:
                helper.kill(); helper.wait(timeout=5)
        if log:
            log.close()
        report['temporary_data'], report['temporary_data_retained'] = str(temp), True
        report['finished_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
        (out / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'receipt': str(out / 'run.json'), 'error': report.get('error')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
