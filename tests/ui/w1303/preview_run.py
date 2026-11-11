"""Exercise sealed artifact previews in the actual development Electron app.

The data is an isolated FIXTURE project served by a real control process. This
reports observations only; it is not independent product acceptance.
"""
from __future__ import annotations

import base64
import datetime as dt
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/ui'))
from browser_smoke import api_json, fixture_artifact
from scenarios import pdf_document


def main():
    run_id = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    out = ROOT / 'execution/v2.4/receipts/W13/W13-03' / ('preview-' + run_id)
    out.mkdir(parents=True)
    locked = json.loads((ROOT / 'execution/toolchains/locked.json').read_text(encoding='utf-8-sig'))['tools']
    go, node = Path(locked['go']['path']), Path(locked['node']['path'])
    for name, binary in [('go', go), ('node', node)]:
        if hashlib.sha256(binary.read_bytes()).hexdigest() != locked[name]['sha256']:
            raise RuntimeError(f'{name} tool hash mismatch')
    report = {'schema': 'researchos.desktop-preview-observation.v1', 'step_id': 'W13-03',
              'run_id': run_id, 'status': 'EXECUTING', 'measurement_mode': 'DEVELOPMENT',
              'fixture_measurement_mode': 'FIXTURE', 'provider_calls': 0,
              'formal_cases_accepted': [], 'commands': [], 'limitations': [
                  'Isolated local Owner and SQLite fixture; no LIVE provider call.',
                  'Visual and DOM observations require independent review for acceptance.']}
    temp = Path(tempfile.mkdtemp(prefix='researchos-w13-ui-preview-', dir=ROOT / '.local'))
    environment = dict(os.environ, GOTOOLCHAIN='local', GOENV='off', RESEARCHOS_TASK_ID='W13',
                       RESEARCHOS_DATA_DIR=str(temp / 'data'), RESEARCHOS_WEB_DIR=str(ROOT / 'apps/web/dist'),
                       RESEARCHOS_DESKTOP_USER_DATA=str(temp / 'electron-user-data'),
                       RESEARCHOS_CLI_DISCOVERY=str(temp / 'data/discovery.json'))
    environment.pop('ROS_DESKTOP_SMOKE', None)
    server = trap = log = None
    hits = []

    class Trap(BaseHTTPRequestHandler):
        def do_GET(self):
            hits.append(self.path)
            self.send_response(200)
            self.end_headers()
        def log_message(self, *args):
            pass

    def command(argv, timeout=180):
        result = subprocess.run([str(value) for value in argv], cwd=ROOT, env=environment,
                                capture_output=True, text=True, encoding='utf-8', timeout=timeout)
        report['commands'].append({'argv': [str(value) for value in argv], 'exit_code': result.returncode})
        if result.returncode:
            raise RuntimeError(f'{argv[0]} exited {result.returncode}: {result.stderr[-1200:]}')
        return result.stdout

    try:
        trap = ThreadingHTTPServer(('127.0.0.1', 0), Trap)
        threading.Thread(target=trap.serve_forever, daemon=True).start()
        probe = f'http://127.0.0.1:{trap.server_port}/probe'
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
            'name': 'W13 preview FIXTURE project', 'intent': 'Electron controlled preview observation',
            'facts': [], 'accepted_scope': ['DEVELOPMENT preview fixture'], 'constraints': [],
            'source_configs': [], 'source_document_refs': [], 'read_snapshot_ids': []})
        path = '/p/' + project['project_id']
        source = json.loads(command([provision, project['project_id']], 30))
        malicious = (f'<h1>HTML sandbox fixture</h1><img src="{probe}/image">'
                     f'<script>window.fixtureExecuted=true;parent.document.body.dataset.previewPwned="yes";'
                     f'location.href="{probe}/navigate"</script>')
        png = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WlYg1sAAAAASUVORK5CYII=')
        contents = {
            'html': ('text/html', malicious.encode('utf-8')),
            'text': ('text/plain', '中文 UTF-8 preview ✅\nsecond line'.encode('utf-8')),
            'image': ('image/png', png),
            'pdf': ('application/pdf', pdf_document()),
        }
        artifacts = {}
        for label, (media, content) in contents.items():
            artifact, evidence = fixture_artifact(base, source['token'], source['principal_id'], path,
                                                  media, content, 'W13 preview ' + label)
            artifacts[label] = {'artifact_id': artifact['id'], 'evidence_id': evidence['id'],
                                'content_hash': artifact['content_hash'], 'media_type': media}
        fixture = {'project_id': project['project_id'], 'project_path': path,
                   'discovery_file': str(temp / 'data/discovery.json'), 'artifacts': artifacts}
        input_file = temp / 'preview-input.json'
        input_file.write_text(json.dumps(fixture, ensure_ascii=False), encoding='utf-8')
        report['fixture'] = fixture
        result = subprocess.run([str(node), str(ROOT / 'tests/ui/w1303/preview.cjs'), str(input_file), str(out)],
                                cwd=ROOT, env=environment, capture_output=True, text=True, encoding='utf-8', timeout=240)
        (out / 'preview.stdout.txt').write_text(result.stdout, encoding='utf-8')
        (out / 'preview.stderr.txt').write_text(result.stderr, encoding='utf-8')
        report['commands'].append({'argv': [str(node), 'tests/ui/w1303/preview.cjs', str(input_file), str(out)],
                                   'exit_code': result.returncode})
        report['trap_requests'] = list(hits)
        report['status'] = 'PASS' if result.returncode == 0 and not hits else 'FAIL'
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
        if trap:
            trap.shutdown(); trap.server_close()
        report['temporary_data'] = str(temp)
        report['temporary_data_retained'] = True
        report['finished_at'] = dt.datetime.now(dt.timezone.utc).isoformat()
        (out / 'preview_run.json').write_bytes(json.dumps(report, ensure_ascii=False, indent=2).encode('utf-8'))
    print(json.dumps({'status': report['status'], 'receipt': str(out / 'preview_run.json'),
                      'error': report.get('error')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
