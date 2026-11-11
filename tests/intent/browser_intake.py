"""Visible browser + actual temporary control API; no provider or production DB."""
import json
from contextlib import closing
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import tempfile
import time
import uuid
from urllib.request import urlopen
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
GO = Path(os.environ.get('RESEARCHOS_GO', r'D:\作品集\ResearchOS\research-os\.local\tools\go1.27.1\go\bin\go.exe'))


def main():
    out = ROOT / 'execution/receipts/W14/intent-planning' / ('browser-' + uuid.uuid4().hex)
    out.mkdir(parents=True)
    local = (ROOT / '.local').resolve()
    local.mkdir(exist_ok=True)
    report = {'scope': 'VISIBLE_BROWSER_TEMPORARY_REAL_API', 'checks': [], 'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'live_provider': False, 'independent_acceptance': 'PENDING'}
    server = None
    try:
        with tempfile.TemporaryDirectory(prefix='intent-browser-', dir=local) as temporary:
            temp = Path(temporary).resolve()
            assert temp.parent == local and temp.name.startswith('intent-browser-')
            env = dict(os.environ, GOENV='off', GOTOOLCHAIN='local', RESEARCHOS_DATA_DIR=str(temp / 'data'), RESEARCHOS_WEB_DIR=str(ROOT / 'apps/web/dist'))
            binary = temp / 'control.exe'
            subprocess.run([str(GO), 'build', '-o', str(binary), './apps/control'], cwd=ROOT, env=env, check=True, capture_output=True, timeout=120)
            credential = temp / 'owner.json'
            subprocess.run([str(binary), '-bootstrap-owner', '-credential-file', str(credential)], cwd=ROOT, env=env, check=True, capture_output=True, timeout=30)
            token = json.loads(credential.read_text(encoding='utf-8'))['token']
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            base = f'http://127.0.0.1:{port}'
            env['RESEARCHOS_LISTEN'] = f'127.0.0.1:{port}'
            with (out / 'service.log').open('w', encoding='utf-8') as log:
                server = subprocess.Popen([str(binary)], cwd=ROOT, env=env, stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW)
                try:
                    for _ in range(60):
                        try:
                            with urlopen(base + '/healthz', timeout=.5) as response:
                                if response.status == 200:
                                    break
                        except Exception:
                            time.sleep(.2)
                    else:
                        raise AssertionError('temporary service unavailable')
                    with sync_playwright() as p:
                        browser = p.chromium.launch(headless=False)
                        page = browser.new_page(viewport={'width': 1280, 'height': 900})
                        errors, mutations = [], []
                        page.on('pageerror', lambda error: errors.append(str(error)))
                        page.on('request', lambda req: mutations.append({'path': req.url.removeprefix(base), 'body': req.post_data_json}) if req.method == 'POST' and '/v1/' in req.url else None)

                        def login():
                            page.get_by_label('访问令牌').fill(token)
                            page.get_by_role('button', name='打开工作台').click()

                        page.goto(base)
                        login()
                        page.get_by_label('项目名称').fill('I1 自然想法浏览器验证')
                        page.get_by_label('要解决的问题').fill('验证真实意图保存与可靠重试')
                        page.get_by_label('首个明确范围').fill('临时本机夹具')
                        page.get_by_role('button', name='创建项目').click()
                        page.get_by_role('heading', name='I1 自然想法浏览器验证').wait_for()
                        project_id = page.url.rsplit('/', 1)[1]
                        page.get_by_role('button', name='提出新想法').click()
                        raw = '帮我跟踪有出处的新研究。\n保留“尚不清楚”的地方。'
                        page.get_by_label('你希望推进什么？').fill(raw)
                        assert page.locator('.form-block [required]').count() == 1
                        assert page.get_by_label('已登记命令键').count() == 0
                        page.reload()
                        login()
                        page.get_by_label('你希望推进什么？').wait_for()
                        assert page.get_by_label('你希望推进什么？').input_value() == raw
                        report['checks'].append('one natural-language required input; unsubmitted draft survives reload')
                        page.screenshot(path=str(out / 'natural-draft.png'), full_page=True)

                        lost = {'done': False}

                        def lose_acceptance_ack(route):
                            if route.request.method == 'POST' and not lost['done']:
                                lost['done'] = True
                                response = route.fetch()
                                assert response.status == 200
                                route.abort('failed')
                            else:
                                route.continue_()

                        page.route('**/requirements/*/actions', lose_acceptance_ack)
                        page.get_by_role('button', name='确认原话并开始规划').click()
                        page.get_by_role('alert').filter(has_text='原话仍保留').wait_for()
                        page.unroute('**/requirements/*/actions', lose_acceptance_ack)
                        page.reload()
                        login()
                        assert page.get_by_label('你希望推进什么？').input_value() == raw
                        assert page.get_by_label('你希望推进什么？').is_disabled()
                        page.get_by_role('button', name='继续提交').click()
                        page.get_by_role('heading', name='规划：' + raw).wait_for()
                        report['checks'].append('committed ACCEPT response deliberately lost; reload retries same persisted submission and idempotency identity')
                        with closing(sqlite3.connect(temp / 'data/researchos.sqlite')) as db:
                            binding = db.execute('SELECT requirement,accepted_revision,planning_goal,planning_task FROM intent_plan_bindings WHERE project=?', (project_id,)).fetchall()
                            assert len(binding) == 1 and binding[0][1] == 2
                            objects = {kind: [json.loads(row[0]) for row in db.execute('SELECT body FROM domain_objects WHERE project=? AND kind=?', (project_id, kind))] for kind in ('Requirement', 'Goal', 'Task', 'ResourceRequest')}
                        assert all(len(values) == 1 for values in objects.values())
                        assert objects['Requirement'][0]['text'] == raw
                        assert objects['Task'][0]['status'] == 'BLOCKED'
                        assert objects['Task'][0]['task_type'] == 'intent_planning'
                        assert objects['ResourceRequest'][0]['status'] == 'OPEN'
                        assert not any(item['path'].endswith('/goals') for item in mutations)
                        assert all('acceptance_contract' not in item['body'] for item in mutations if item['body'])
                        report['checks'].append('real SQLite contains exactly one unchanged accepted Requirement, planning Goal, BLOCKED Task and OPEN resource request; frontend sends no fabricated contract')
                        page.get_by_role('heading', name='意图规划', exact=True).wait_for()
                        assert page.get_by_text('业务任务 0', exact=True).count() == 1
                        page.screenshot(path=str(out / 'planning-blocked-desktop.png'), full_page=True)
                        page.set_viewport_size({'width': 390, 'height': 844})
                        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                        page.screenshot(path=str(out / 'planning-blocked-mobile.png'), full_page=True)
                        report['checks'].append('planning status visible separately from business accepted count; mobile viewport has no horizontal overflow')
                        assert not errors, errors
                        report.update(status='PASS', project_id=project_id, binding=binding[0], browser=browser.version, page_errors=errors, mutations=mutations, screenshots=['natural-draft.png', 'planning-blocked-desktop.png', 'planning-blocked-mobile.png'])
                        browser.close()
                finally:
                    server.terminate()
                    server.wait(timeout=10)
                    server = None
    except Exception as error:
        report.update(status='FAIL', error=str(error))
        raise
    finally:
        if server is not None:
            server.terminate()
            server.wait(timeout=10)
        (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'status': report.get('status'), 'checks': len(report['checks']), 'report': str(out / 'report.json')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
