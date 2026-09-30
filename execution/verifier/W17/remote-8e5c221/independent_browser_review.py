"""W17 real browser + real control/SQLite; polling metadata is explicit fixture.
No public tunnel, physical phone, formal holdout or live acceptance is asserted.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import traceback
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/ui'))
from browser_smoke import api_json
from scenarios import login


def main():
    run = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = ROOT / 'execution/verifier/W17/independent-browser' / run
    out.mkdir(parents=True)
    report = {'status': 'RUNNING', 'scope': 'DEVELOPMENT_ONLY_BROWSER', 'checks': [], 'http': [],
              'limitations': ['390px Chromium browser emulates a phone; no physical device', 'Polling transport metadata supplied by browser route fixture; gateway boundary tested separately', 'No public tunnel started; actual TLS and cross-network A10/A11 remain NOT_RUN', 'No formal holdout accessed; C22 complete host/filesystem boundary is not asserted'],
              'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()}
    sources = [*sorted((ROOT / 'apps/web/src').glob('*')), *sorted((ROOT / 'internal/domain').glob('*.go')), *sorted((ROOT / 'migrations/sqlite').glob('*.sql')), ROOT / 'internal/api/server.go', ROOT / 'apps/control/main.go', ROOT / 'spec/v2.0/contracts/domain.schema.json', ROOT / 'spec/v2.0/contracts/openapi.json', ROOT / 'contracts/operation_coverage.json', Path(__file__)]
    report['source_hashes'] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources if p.is_file()}
    temp = Path(tempfile.mkdtemp(prefix='researchos-w17-browser-'))
    server = None
    stream = None
    secrets = []
    try:
        tool = json.loads((ROOT / 'execution/toolchains/locked.json').read_text(encoding='utf-8'))['tools']
        env = dict(os.environ, GOTOOLCHAIN='local', GOENV='off', RESEARCHOS_DATA_DIR=str(temp / 'data'), RESEARCHOS_WEB_DIR=str(ROOT / 'apps/web/dist'))
        commands = [[tool['node']['path'], tool['npm_cli']['path'], 'run', 'build', '--prefix', 'apps/web'],
                    [tool['go']['path'], 'build', '-o', str(temp / 'control.exe'), './apps/control']]
        for index, cmd in enumerate(commands):
            result = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8', timeout=180)
            (out / f'build-{index}.log').write_text(result.stdout + result.stderr, encoding='utf-8')
            assert result.returncode == 0, f'build {index} failed'
        credentials = temp / 'owner.json'
        result = subprocess.run([str(temp / 'control.exe'), '-bootstrap-owner', '-credential-file', str(credentials)], cwd=ROOT, env=env, capture_output=True, timeout=30)
        assert result.returncode == 0, 'Owner bootstrap failed'
        owner = json.loads(credentials.read_text(encoding='utf-8'))['token']
        secrets.append(owner)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
        base = f'http://127.0.0.1:{port}'
        env['RESEARCHOS_LISTEN'] = f'127.0.0.1:{port}'
        stream = (out / 'service.log').open('w', encoding='utf-8')
        server = subprocess.Popen([str(temp / 'control.exe')], cwd=ROOT, env=env, stdout=stream, stderr=stream)
        for _ in range(50):
            try:
                with urlopen(base + '/healthz', timeout=.5) as response:
                    if response.status == 200: break
            except Exception: time.sleep(.1)
        else: raise RuntimeError('control listener unavailable')
        project = api_json(base, owner, 'POST', '/v1/projects', {'name': 'W17 双端监督开发夹具', 'intent': '验证真实配对与撤销', 'facts': [], 'accepted_scope': ['development fixture'], 'constraints': [], 'source_configs': [], 'source_document_refs': [], 'read_snapshot_ids': []})['project_id']
        prefix = '/v1/projects/' + project
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            desktop = browser.new_context(viewport={'width': 1440, 'height': 1000}, permissions=['clipboard-read', 'clipboard-write'])
            phone = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
            phone.route('**/remote-info', lambda route: route.fulfill(status=200, content_type='application/json', body='{"remote":true,"events":"poll"}'))
            def short_expiry(route):
                response = route.fetch()
                body = response.json()
                body['access_expires_at'] = '2000-01-01T00:00:00Z'
                route.fulfill(response=response, json=body)
            phone.route('**/v1/device-pairings/redeem', short_expiry)
            page = desktop.new_page(); mobile = phone.new_page()
            refresh_results = []
            def slow_refresh(route):
                response = route.fetch()
                refresh_results.append(response.status)
                # Server already rotated old access; delay only delivery of real response.
                mobile.wait_for_timeout(3500)
                route.fulfill(response=response)
            phone.route('**/v1/device-sessions/refresh', slow_refresh)
            errors = []
            for tab in [page, mobile]: tab.on('pageerror', lambda error: errors.append(str(error)))
            mobile.on('response', lambda response: report['http'].append({'path': response.url.split(base)[-1].split('?')[0], 'status': response.status}) if '/v1/' in response.url else None)
            login(page, base, '/p/' + project + '/settings', owner)
            page.get_by_role('button', name='生成只读配对链接').wait_for()
            with page.expect_response(lambda r: r.url.endswith('/v1/device-pairings') and r.request.method == 'POST') as response:
                page.get_by_role('button', name='生成只读配对链接').click()
            challenge = response.value.json(); assert response.value.status == 201
            secrets.append(challenge['pairing_token'])
            page.get_by_role('button', name='复制配对链接').click()
            page.get_by_text('链接已复制，请仅发给要配对的设备。', exact=True).wait_for()
            link = page.evaluate('navigator.clipboard.readText()')
            assert link == base + '/pair#' + challenge['challenge_id'] + '.' + challenge['pairing_token']
            page.screenshot(path=str(out / 'desktop-pairing.png'), full_page=True)
            mobile.goto(link, wait_until='domcontentloaded')
            mobile.get_by_role('button', name='配对并打开工作台').wait_for()
            assert mobile.evaluate('location.hash') == ''
            mobile.screenshot(path=str(out / 'phone-pairing.png'))
            with mobile.expect_response(lambda r: r.url.endswith('/v1/device-pairings/redeem')) as response:
                mobile.get_by_role('button', name='配对并打开工作台').click()
            session = response.value.json(); assert response.value.status == 200
            secrets += [session['access_token'], session['refresh_token']]
            assert session['device']['role'] == 'READER' and session['device']['project_ids'] == [project]
            mobile.wait_for_url(base + '/p/' + project)
            mobile.locator('.connection-text').filter(has_text='已连接').wait_for(state='attached')
            mobile.wait_for_timeout(1000)
            mobile.get_by_text('此设备为只读监督；控制操作需要电脑显式授权。', exact=True).wait_for()
            report['checks'].append('Desktop generated/copies real one-use link; phone consumes through actual API; fragment removed before submit; explicit READER project scope')
            assert not mobile.evaluate('document.documentElement.scrollWidth > innerWidth + 1')
            stored = mobile.evaluate('JSON.stringify({local:{...localStorage}, session:{...sessionStorage}})')
            dom = mobile.locator('body').inner_text()
            assert all(secret not in stored and secret not in dom for secret in secrets)
            nav = phone.new_cdp_session(mobile).send('Page.getNavigationHistory')
            report['history_secret_fields'] = [{'entry': i, 'field': key, 'secret_index': n} for i, entry in enumerate(nav['entries']) for key, value in entry.items() for n, secret in enumerate(secrets) if secret in str(value)]
            report['history_url_secret_free'] = all(secret not in entry['url'] for entry in nav['entries'] for secret in secrets)
            mobile.wait_for_timeout(11000)
            report['refresh_results'] = refresh_results
            report['after_refresh_workbench_visible'] = mobile.locator('.topbar').count() == 1
            report['after_refresh_pairing_error_visible'] = mobile.get_by_text('设备会话已过期或被撤销，请在电脑重新配对。', exact=True).count() > 0
            mobile.screenshot(path=str(out / 'refresh-race.png'))
            report['fixture'] = 'Only redeem access_expires_at moved into past to trigger renew timer; actual refresh API response delivered 3.5 seconds after server rotation; no auth or event response mocked.'
            assert refresh_results == [200], refresh_results
            assert report['after_refresh_workbench_visible'], 'Successful refresh incorrectly lost the authenticated page after old-token 401'
            report['checks'].append('Successful rotation survives old-token 401 while fresh credential response is in flight')
            assert not errors, errors
            report['browser_errors'] = errors
            report['browser_version'] = browser.version
            browser.close()
        report['status'] = 'PASS'
    except Exception as error:
        report['status'] = 'FAIL'
        report['failure'] = str(error)
        report['traceback'] = traceback.format_exc(limit=5)
    finally:
        if server:
            server.terminate()
            try: server.wait(timeout=5)
            except subprocess.TimeoutExpired: server.kill(); server.wait(timeout=5)
        if stream: stream.close()
        for file in out.glob('*.log'):
            content = file.read_text(encoding='utf-8')
            if any(secret in content for secret in secrets): report['status'] = 'FAIL'; report['failure'] = 'secret appeared in service/build log'
        report['screenshots'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.png')}
        report['source_unchanged'] = report['source_hashes'] == {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources if p.is_file()}
        if not report['source_unchanged']: report['status'] = 'FAIL'; report['failure'] = 'source changed during run'
        # Remove only this newly-created, validated temporary fixture directory.
        assert temp.resolve().parent == Path(tempfile.gettempdir()).resolve() and temp.name.startswith('researchos-w17-browser-')
        shutil.rmtree(temp)
        (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'report': str(out / 'report.json'), 'failure': report.get('failure')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__': raise SystemExit(main())
