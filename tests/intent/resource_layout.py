"""Only the 320px resource layout regression, with real API-created data."""
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
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/ui'))
from browser_smoke import api_json, GO


def main():
    out = ROOT / 'execution/receipts/W14/intent-planning' / ('resources-320-' + uuid.uuid4().hex)
    out.mkdir(parents=True)
    local = (ROOT / '.local').resolve()
    report = {'scope': 'SINGLE_RESOURCE_VIEWPORT_REGRESSION', 'status': 'FAIL'}
    try:
        with tempfile.TemporaryDirectory(prefix='intent-layout-', dir=local) as directory:
            temp = Path(directory).resolve()
            assert temp.parent == local
            env = dict(os.environ, GOENV='off', GOTOOLCHAIN='local', RESEARCHOS_DATA_DIR=str(temp / 'data'), RESEARCHOS_WEB_DIR=str(ROOT / 'apps/web/dist'))
            exe = temp / 'control.exe'
            subprocess.run([str(GO), 'build', '-o', str(exe), './apps/control'], cwd=ROOT, env=env, check=True, capture_output=True)
            credential = temp / 'owner.json'
            subprocess.run([str(exe), '-bootstrap-owner', '-credential-file', str(credential)], cwd=ROOT, env=env, check=True, capture_output=True)
            token = json.loads(credential.read_text(encoding='utf-8'))['token']
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            env['RESEARCHOS_LISTEN'] = f'127.0.0.1:{port}'
            base = f'http://127.0.0.1:{port}'
            with (out / 'service.log').open('w', encoding='utf-8') as log:
                server = subprocess.Popen([str(exe)], cwd=ROOT, env=env, stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW)
                try:
                    for _ in range(60):
                        try:
                            with urlopen(base + '/healthz', timeout=.5):
                                break
                        except Exception:
                            time.sleep(.1)
                    project = api_json(base, token, 'POST', '/v1/projects', {'name': '资源换行验证', 'intent': '只验证资源页窄视口', 'facts': [], 'accepted_scope': ['本机夹具'], 'constraints': [], 'source_configs': [], 'source_document_refs': [], 'read_snapshot_ids': []})
                    api = '/v1/projects/' + project['project_id']
                    state = api_json(base, token, 'GET', api + '/state')
                    req = api_json(base, token, 'POST', api + '/requirements', {'requirement_key': 'INTENT-' + uuid.uuid4().hex, 'text': '研究新方法，保留未知项。', 'basis': 'USER_STATED', 'source_refs': [], 'rationale': 'layout fixture', 'supersedes_id': None, 'acceptance_check_ids': []}, f'"r{state["revision"]}"')
                    api_json(base, token, 'POST', api + '/requirements/' + req['id'] + '/actions', {'action': 'ACCEPT', 'reason': 'layout fixture confirms original intent', 'source_validation_refs': []}, f'"r{req["revision"]}"')
                    with sync_playwright() as p:
                        browser = p.chromium.launch(headless=False)
                        page = browser.new_page(viewport={'width': 320, 'height': 780})
                        page.goto(base + '/p/' + project['project_id'] + '/resources')
                        page.get_by_label('访问令牌').fill(token)
                        page.get_by_role('button', name='打开工作台').click()
                        page.locator('.request-row').wait_for()
                        assert page.locator('.request-row').count() == 1
                        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                        page.screenshot(path=str(out / 'resources-light-320.png'), full_page=True)
                        report.update(status='PASS', checks=['real INTENT resource reason wraps at 320px with no horizontal overflow'], browser=browser.version, project_id=project['project_id'])
                        browser.close()
                finally:
                    server.terminate()
                    server.wait(timeout=10)
    finally:
        (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'status': report['status'], 'report': str(out / 'report.json')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
