"""W13-03 actual Electron matrix over an isolated, real local API.

Runtime observations used to seed content are explicitly FIXTURE. No provider
inference, existing database, protected corpus, or installed app is touched.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/ui'))
from browser_smoke import api_json
from seed import seed


def main():
    run_id = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    out = ROOT / 'execution/v2.4/receipts/W13/W13-03' / run_id
    out.mkdir(parents=True)
    locked = json.loads((ROOT / 'execution/toolchains/locked.json').read_text(encoding='utf-8-sig'))['tools']
    go = Path(os.environ.get('RESEARCHOS_GO') or locked['go']['path'])
    node = Path(locked['node']['path'])
    for name, binary in [('go', go), ('node', node)]:
        assert hashlib.sha256(binary.read_bytes()).hexdigest() == locked[name]['sha256'], f'{name} tool hash mismatch'
    report = {'schema': 'researchos.desktop-ui-matrix.v1', 'step_id': 'W13-03', 'run_id': run_id,
              'measurement_mode': 'DEVELOPMENT', 'surface': 'WINDOWS_ELECTRON', 'status': 'EXECUTING',
              'provider_calls': 0, 'formal_cases_accepted': [], 'source_hashes': {}, 'commands': []}
    for folder in ['apps/web/src', 'apps/desktop/main', 'apps/desktop/preload', 'tests/ui/w1303', 'internal/domain', 'internal/host', 'internal/api', 'apps/control']:
        for file in sorted((ROOT / folder).rglob('*')):
            if file.is_file() and file.suffix in ['.js', '.jsx', '.css', '.py', '.cjs', '.html', '.go']:
                report['source_hashes'][file.relative_to(ROOT).as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
    for name in ['internal/domain/store.go', 'internal/domain/client_session_fence.go']:
        report['source_hashes'][name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    environment = dict(os.environ, GOTOOLCHAIN='local', GOENV='off', RESEARCHOS_TASK_ID='W13')
    server = None
    log = None
    # Keep failed private fixtures under .local for diagnosis; never commit credentials.
    temp = Path(tempfile.mkdtemp(prefix='researchos-w13-ui-', dir=ROOT / '.local'))
    environment.update(RESEARCHOS_DATA_DIR=str(temp / 'data'), RESEARCHOS_WEB_DIR=str(ROOT / 'apps/web/dist'))
    def command(argv, timeout=180, capture=False):
        result = subprocess.run([str(arg) for arg in argv], cwd=ROOT, env=environment,
                                capture_output=True, text=True, encoding='utf-8', timeout=timeout)
        report['commands'].append({'argv': [str(arg) for arg in argv], 'exit_code': result.returncode})
        if result.returncode:
            raise RuntimeError(f'command failed: {argv[0]} ({result.returncode}): {result.stderr[-1600:]}')
        return result.stdout if capture else None
    try:
        command([node, ROOT / 'apps/web/node_modules/vite/bin/vite.js', 'build', ROOT / 'apps/web'])
        report['built_assets'] = {file.relative_to(ROOT).as_posix(): hashlib.sha256(file.read_bytes()).hexdigest()
                                  for file in sorted((ROOT / 'apps/web/dist').rglob('*')) if file.is_file()}
        control, provision = temp / 'control.exe', temp / 'provision.exe'
        command([go, 'build', '-o', control, './apps/control'])
        command([go, 'build', '-o', provision, './tests/ui/provision'])
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
            'name': 'W13 Desktop FIXTURE 项目', 'intent': '验证真实桌面中的页面与恢复',
            'facts': [], 'accepted_scope': ['DEVELOPMENT UI fixture'], 'constraints': [],
            'source_configs': [], 'source_document_refs': [], 'read_snapshot_ids': []})
        empty_project = api_json(base, owner['token'], 'POST', '/v1/projects', {
            'name': 'W13 成功空集项目', 'intent': '验证成功读取但没有业务记录的界面',
            'facts': [], 'accepted_scope': ['DEVELOPMENT empty-state fixture'], 'constraints': [],
            'source_configs': [], 'source_document_refs': [], 'read_snapshot_ids': []})
        fixture = seed(base, owner['token'], project['project_id'], provision, environment, ROOT, out)
        fixture['empty_project_id'] = empty_project['project_id']
        session_fixture = temp / 'session-fixture.exe'
        command([go, 'build', '-o', session_fixture, './tests/ui/w1303/session_fixture'])
        fixture['sessions'] = json.loads(command([session_fixture, '--data-dir', temp / 'data',
            '--project-id', project['project_id'], '--owner-id', owner['principal_id'],
            '--artifact-id', fixture['objects']['artifact']], capture=True))
        fixture.update(base_url=base, discovery_file=str(temp / 'data/discovery.json'))
        fixture_file = temp / 'matrix-input.json'
        fixture_file.write_text(json.dumps(fixture, ensure_ascii=False, indent=2), encoding='utf-8')
        report['fixture'] = fixture
        environment['RESEARCHOS_CLI_DISCOVERY'] = str(temp / 'data/discovery.json')
        environment['RESEARCHOS_PROJECT_ID'] = project['project_id']
        environment.pop('ROS_DESKTOP_SMOKE', None)
        environment['RESEARCHOS_DESKTOP_USER_DATA'] = str(temp / 'electron-user-data')
        result = subprocess.run([str(node), str(ROOT / 'tests/ui/w1303/matrix.cjs'), str(fixture_file), str(out)],
                                cwd=ROOT, env=environment, capture_output=True, text=True, encoding='utf-8', timeout=600)
        (out / 'matrix.stdout.txt').write_text(result.stdout, encoding='utf-8')
        (out / 'matrix.stderr.txt').write_text(result.stderr, encoding='utf-8')
        report['commands'].append({'argv': [str(node), 'tests/ui/w1303/matrix.cjs', str(fixture_file), str(out)], 'exit_code': result.returncode})
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
        (out / 'run.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'receipt': str(out / 'run.json'), 'error': report.get('error')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
