"""Run the real Electron accessibility probe with an isolated local project."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import uuid
from urllib.request import urlopen
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/ui'))
from browser_smoke import api_json


def main():
    run_id = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    out = ROOT / 'execution/v2.4/receipts/W13/W13-03' / ('accessibility-' + run_id)
    out.mkdir(parents=True)
    locked = json.loads((ROOT / 'execution/toolchains/locked.json').read_text(encoding='utf-8-sig'))['tools']
    go, node = Path(locked['go']['path']), Path(locked['node']['path'])
    for name, binary in [('go', go), ('node', node)]:
        if hashlib.sha256(binary.read_bytes()).hexdigest() != locked[name]['sha256']:
            raise RuntimeError(f'{name} tool hash mismatch')
    dist = ROOT / 'apps/web/dist/index.html'
    if not dist.is_file():
        raise RuntimeError('Electron web/dist build unavailable')
    report = {'schema': 'researchos.desktop-accessibility-observation.v1', 'step_id': 'W13-03',
              'run_id': run_id, 'status': 'EXECUTING', 'measurement_mode': 'DEVELOPMENT',
              'fixture_measurement_mode': 'FIXTURE', 'provider_calls': 0, 'formal_cases_accepted': [],
              'commands': [], 'dist_index_sha256': hashlib.sha256(dist.read_bytes()).hexdigest(),
              'dist_build_declared_by_parent': '1aedb05e',
              'source_hashes': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in [ROOT / 'apps/web/src/main.jsx', ROOT / 'apps/web/src/style.css',
                                          ROOT / 'tests/ui/w1303/accessibility.cjs']},
              'limitations': ['Electron Chromium accessibility snapshot is not a physical NVDA speech test.',
                              'Representative contrast and primary controls only; independent acceptance pending.']}
    temp = Path(tempfile.mkdtemp(prefix='researchos-w13-ui-accessibility-', dir=ROOT / '.local'))
    environment = dict(os.environ, GOTOOLCHAIN='local', GOENV='off', RESEARCHOS_TASK_ID='W13',
                       RESEARCHOS_DATA_DIR=str(temp / 'data'), RESEARCHOS_WEB_DIR=str(ROOT / 'apps/web/dist'),
                       RESEARCHOS_DESKTOP_USER_DATA=str(temp / 'electron-user-data'),
                       RESEARCHOS_CLI_DISCOVERY=str(temp / 'data/discovery.json'))
    environment.pop('ROS_DESKTOP_SMOKE', None)
    server = log = None

    def command(argv, timeout=180):
        result = subprocess.run([str(value) for value in argv], cwd=ROOT, env=environment,
                                capture_output=True, text=True, encoding='utf-8', timeout=timeout)
        report['commands'].append({'argv': [str(value) for value in argv], 'exit_code': result.returncode})
        if result.returncode:
            raise RuntimeError(f'{argv[0]} exited {result.returncode}: {result.stderr[-1200:]}')
        return result.stdout

    try:
        control = temp / 'control.exe'
        command([go, 'build', '-o', control, './apps/control'])
        credential = temp / 'owner.json'
        command([control, '-bootstrap-owner', '-credential-file', credential], 30)
        owner = json.loads(credential.read_text(encoding='utf-8-sig'))
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        environment['RESEARCHOS_LISTEN'] = f'127.0.0.1:{port}'
        base = f'http://127.0.0.1:{port}'
        log = (out / 'service.log').open('w', encoding='utf-8')
        server = subprocess.Popen([str(control)], cwd=ROOT, env=environment, stdout=log, stderr=log)
        for _ in range(100):
            if server.poll() is not None:
                raise RuntimeError('temporary control exited before health probe')
            try:
                with urlopen(base + '/healthz', timeout=.4) as response:
                    if response.status == 200:
                        break
            except Exception:
                time.sleep(.2)
        else:
            raise RuntimeError('temporary control health probe timed out')
        project = api_json(base, owner['token'], 'POST', '/v1/projects', {
            'name': 'W13 accessibility FIXTURE project', 'intent': 'Electron accessibility observation',
            'facts': [], 'accepted_scope': ['DEVELOPMENT accessibility fixture'], 'constraints': [],
            'source_configs': [], 'source_document_refs': [], 'read_snapshot_ids': []})
        fixture = {'project_id': project['project_id'], 'discovery_file': str(temp / 'data/discovery.json')}
        input_file = temp / 'accessibility-input.json'
        input_file.write_bytes(json.dumps(fixture, ensure_ascii=False).encode('utf-8'))
        report['fixture'] = fixture
        result = subprocess.run([str(node), str(ROOT / 'tests/ui/w1303/accessibility.cjs'), str(input_file), str(out)],
                                cwd=ROOT, env=environment, capture_output=True, text=True, encoding='utf-8', timeout=240)
        (out / 'accessibility.stdout.txt').write_bytes(result.stdout.encode('utf-8'))
        (out / 'accessibility.stderr.txt').write_bytes(result.stderr.encode('utf-8'))
        report['commands'].append({'argv': [str(node), 'tests/ui/w1303/accessibility.cjs', str(input_file), str(out)],
                                   'exit_code': result.returncode})
        report['status'] = 'PASS' if result.returncode == 0 else 'FAIL'
    except Exception as error:
        report['status'] = 'FAIL'
        report['error'] = str(error)
    finally:
        if server and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill(); server.wait(timeout=5)
        if log:
            log.close()
        report['temporary_data'] = str(temp)
        report['temporary_data_retained'] = True
        report['finished_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
        (out / 'accessibility_run.json').write_bytes(json.dumps(report, ensure_ascii=False, indent=2).encode('utf-8'))
    print(json.dumps({'status': report['status'], 'receipt': str(out / 'accessibility_run.json'),
                      'error': report.get('error')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
