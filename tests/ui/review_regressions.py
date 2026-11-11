"""W13 targeted development regressions: URL selection, typography, API timeout."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import tempfile
import time
import traceback
from urllib.parse import parse_qs, urlsplit
from urllib.request import urlopen

from playwright.sync_api import sync_playwright
from browser_smoke import api_json, fixture_artifact
from scenarios import login

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def selected(page, evidence, report, step):
    page.locator('.split-content > section').last.get_by_text(evidence['claim'], exact=True).first.wait_for()
    focus = parse_qs(urlsplit(page.url).query).get('focus', [])
    assert focus == [evidence['id']], (step, page.url)
    report.setdefault('selection', []).append({'step': step, 'focus': focus[0], 'claim': evidence['claim'], 'url': page.url})


def typography(page, report, label):
    measured = page.evaluate("""() => {
      const important = ['.tag', '.stage-count', '.stage-extra'];
      const auxiliary = ['.bottom-nav a', '.sidebar-head', '.stage-number', '.event-list time'];
      const fonts = [...important, ...auxiliary].flatMap(selector => [...document.querySelectorAll(selector)]
        .filter(el => el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden' && !el.closest('[inert]'))
        .map(el => ({ selector, text: el.textContent.trim(), size: parseFloat(getComputedStyle(el).fontSize),
          minimum: important.includes(selector) ? 13 : 12, left: el.getBoundingClientRect().left, right: el.getBoundingClientRect().right })));
      return { fonts, innerWidth, outerWidth, devicePixelRatio, scale: visualViewport.scale,
        overflow: document.documentElement.scrollWidth > innerWidth + 1 };
    }""")
    assert measured['fonts'], (label, 'no measured text')
    assert all(row['size'] >= row['minimum'] for row in measured['fonts']), (label, measured)
    assert all(row['left'] >= -1 and row['right'] <= measured['innerWidth'] + 1 for row in measured['fonts']), (label, measured)
    assert not measured['overflow'], (label, measured)
    measured['label'] = label
    report.setdefault('typography', []).append(measured)
    return measured


def browser_regressions(page, base, project_path, token, refs, report, out):
    a, b = refs
    login(page, base, project_path + '/evidence?probe=preserved&focus=' + a['id'], token)
    selected(page, a, report, 'deep-link-A')
    page.locator('.list-panel .record-row').filter(has_text=b['id'][:12]).click()
    selected(page, b, report, 'list-click-B')
    assert parse_qs(urlsplit(page.url).query)['probe'] == ['preserved']
    page.go_back(wait_until='domcontentloaded')
    selected(page, a, report, 'history-back-A')
    page.go_forward(wait_until='domcontentloaded')
    selected(page, b, report, 'history-forward-B')
    page.reload(wait_until='domcontentloaded')
    page.get_by_label('访问令牌').fill(token)
    page.get_by_role('button', name='打开工作台').click()
    selected(page, b, report, 'refresh-reauth-B')
    page.locator('.list-panel .record-row').filter(has_text=a['id'][:12]).click()
    selected(page, a, report, 'before-server-search-A')
    page.get_by_label('检索词').fill(b['claim'])
    page.get_by_role('button', name='服务端检索', exact=True).click()
    page.get_by_role('button', name='定位证据', exact=True).first.wait_for()
    page.get_by_role('button', name='定位证据', exact=True).first.click()
    selected(page, b, report, 'server-hit-B')
    assert page.get_by_label('检索词').input_value() == b['claim']
    assert page.get_by_role('button', name='定位证据', exact=True).count() > 0
    page.go_back(wait_until='domcontentloaded')
    selected(page, a, report, 'server-hit-back-A')
    page.go_forward(wait_until='domcontentloaded')
    selected(page, b, report, 'server-hit-forward-B')
    page.locator('.sidebar').get_by_role('link', name='来源证据', exact=True).click()
    page.get_by_text('选择一条证据查看原文和哈希。', exact=True).wait_for()
    assert 'focus' not in parse_qs(urlsplit(page.url).query)
    page.go_back(wait_until='domcontentloaded')
    selected(page, b, report, 'query-removal-back-B')
    typography(page, report, 'desktop-1440')
    page.screenshot(path=str(out / 'evidence-route-desktop.png'), full_page=False)
    page.set_viewport_size({'width': 320, 'height': 780})
    selected(page, b, report, 'mobile-320-B')
    typography(page, report, 'mobile-320')
    page.locator('.split-content > section').last.locator('.meta-line').scroll_into_view_if_needed()
    page.screenshot(path=str(out / 'evidence-320.png'), full_page=False)
    page.get_by_role('button', name='打开阶段进度').click()
    page.get_by_role('button', name='关闭进度').wait_for()
    page.wait_for_function("Math.abs(document.querySelector('.progress-rail.drawer-open').getBoundingClientRect().right - innerWidth) < 1")
    drawer = typography(page, report, 'mobile-320-stage-drawer')
    assert len([row for row in drawer['fonts'] if row['selector'] == '.stage-count']) == 6
    page.screenshot(path=str(out / 'stage-counts-320.png'), full_page=False)
    page.keyboard.press('Escape')
    assert page.evaluate('document.activeElement.getAttribute("aria-label")') == '打开阶段进度'

    # Chromium's real zoom setting changes layout viewport and DPR, not CSS zoom.
    page.set_viewport_size({'width': 640, 'height': 1560})
    page.goto('chrome://settings', wait_until='domcontentloaded')
    zoom = page.evaluate('async()=>{await chrome.settingsPrivate.setDefaultZoom(2);return await chrome.settingsPrivate.getDefaultZoom()}')
    assert zoom == 2
    login(page, base, project_path + '/evidence?focus=' + b['id'], token)
    selected(page, b, report, 'native-200-percent-B')
    zoomed = typography(page, report, 'native-200-percent-outer640-inner320')
    assert (zoomed['innerWidth'], zoomed['outerWidth'], zoomed['devicePixelRatio'], zoomed['scale']) == (320, 640, 2, 1), zoomed
    page.locator('.split-content > section').last.locator('.meta-line').scroll_into_view_if_needed()
    page.screenshot(path=str(out / 'evidence-native-200-percent.png'), full_page=False)
    page.get_by_role('button', name='打开阶段进度').click()
    page.get_by_role('button', name='关闭进度').wait_for()
    page.wait_for_function("Math.abs(document.querySelector('.progress-rail.drawer-open').getBoundingClientRect().right - innerWidth) < 1")
    typography(page, report, 'native-200-percent-stage-drawer')
    page.screenshot(path=str(out / 'stage-counts-native-200-percent.png'), full_page=False)
    page.keyboard.press('Escape')
    page.goto('chrome://settings', wait_until='domcontentloaded')
    page.evaluate('chrome.settingsPrivate.setDefaultZoom(1)')
    page.set_viewport_size({'width': 1440, 'height': 1000})

    # Hold one actual read at the transport boundary; no response data is forged.
    pattern = '**' + project_path.replace('/p/', '/v1/projects/') + '/budget-policy'
    held = []
    hold = lambda route: held.append(route)
    page.route(pattern, hold)
    login(page, base, project_path + '/resources', token)
    page.locator('main .loading-state').wait_for()
    started = time.monotonic()
    page.locator('main .state-notice').filter(has_text='请求超时').wait_for(timeout=35000)
    elapsed = time.monotonic() - started
    assert 27 <= elapsed <= 35, elapsed
    assert not page.locator('main .loading-state').count()
    assert page.get_by_role('button', name='重新读取', exact=True).is_visible()
    report['timeout'] = {'seconds': elapsed, 'held_requests': len(held), 'loading_ended': True,
                         'visible_error': page.locator('main .state-notice').inner_text(), 'retry_visible': True}
    page.screenshot(path=str(out / 'bounded-read-timeout.png'), full_page=False)
    page.unroute_all(behavior='ignoreErrors')
    for route in held:
        try:
            route.abort('timedout')
        except Exception:
            pass  # Browser may already have cancelled this timed-out request.
    page.get_by_role('button', name='重新读取', exact=True).click()
    page.get_by_role('button', name='保存上限', exact=True).wait_for()
    assert not page.locator('main .state-notice,main .loading-state').count()
    report['timeout']['retry_succeeded'] = True
    page.screenshot(path=str(out / 'bounded-read-retry.png'), full_page=False)

    # Navigation cancellation must not surface as a timeout in the next screen.
    held.clear()
    page.route(pattern, hold)
    page.locator('.sidebar').get_by_role('link', name='来源证据', exact=True).click()
    page.locator('.sidebar').get_by_role('link', name='费用资源', exact=True).click()
    page.locator('main .loading-state').wait_for()
    page.locator('.sidebar').get_by_role('link', name='来源证据', exact=True).click()
    page.get_by_role('heading', name='来源证据', exact=True).wait_for()
    page.locator('.list-panel .record-row').first.wait_for()
    assert not page.locator('main .state-notice').count()
    report['navigation_abort'] = {'held_requests': len(held), 'next_screen_error_count': 0}
    page.unroute_all(behavior='ignoreErrors')
    for route in held:
        try:
            route.abort('aborted')
        except Exception:
            pass


def main():
    if os.environ.get('RESEARCHOS_TASK_ID') != 'W13':
        raise SystemExit('RESEARCHOS_TASK_ID=W13 required')
    locked = json.loads((ROOT / 'execution/toolchains/locked.json').read_text(encoding='utf-8'))
    go, node = [locked['tools'][name]['path'] for name in ('go', 'node')]
    sources = [*sorted((ROOT / 'apps/web/src').glob('*')), Path(__file__), ROOT / 'tests/ui/browser_smoke.py', ROOT / 'tests/ui/provision/main.go']
    manifest = {str(path.relative_to(ROOT)).replace('\\', '/'): digest(path) for path in sources if path.is_file()}
    run_id = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = ROOT / 'execution/receipts/W13/review-fixes' / run_id
    out.mkdir(parents=True)
    report = {'scope': 'DEVELOPMENT_ONLY_BROWSER', 'status': 'FAIL', 'execution_status': 'EXECUTION_REPORTED',
              'source_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'source_hashes': manifest, 'platform': platform.platform(), 'commands': [],
              'limitations': ['Temporary local SQLite and explicit public fixtures; no formal AcceptanceReceipt',
                              'No physical mobile device; Chromium layout and native browser zoom only',
                              'Pending ordinary read is an injected transport fault; retry uses the actual service',
                              'Playwright may emit route-handler cancellation callbacks when timed-out intercepted requests are disposed; application pageerror is checked separately']}
    temp = Path(tempfile.mkdtemp(prefix='researchos-w13-ui-review-')).resolve()
    assert temp.parent == Path(tempfile.gettempdir()).resolve() and temp.name.startswith('researchos-w13-ui-review-')
    server = None
    log = None
    def run(name, command, environment):
        result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True,
                                encoding='utf-8', errors='replace', timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
        report['commands'].append({'name': name, 'argv': command, 'exit': result.returncode})
        if name not in ('bootstrap-owner', 'provision-fixture'):
            (out / (name + '.stdout.log')).write_text(result.stdout, encoding='utf-8')
            (out / (name + '.stderr.log')).write_text(result.stderr, encoding='utf-8')
        assert result.returncode == 0, (name, result.stderr[-1200:])
        return result.stdout
    try:
        environment = {k: v for k, v in os.environ.items() if 'TYPESAFE' not in k.upper() and 'JEV' not in k.upper()}
        environment.update(GOTOOLCHAIN='local', GOENV='off', RESEARCHOS_TASK_ID='W13', RESEARCHOS_DATA_DIR=str(temp / 'data'), RESEARCHOS_WEB_DIR=str(ROOT / 'apps/web/dist'))
        run('web-build', [node, str(ROOT / 'apps/web/node_modules/vite/bin/vite.js'), 'build', 'apps/web'], environment)
        binary, provision, credential = temp / 'control.exe', temp / 'provision.exe', temp / 'owner.json'
        run('control-build', [go, 'build', '-o', str(binary), './apps/control'], environment)
        run('provision-build', [go, 'build', '-o', str(provision), './tests/ui/provision'], environment)
        run('bootstrap-owner', [str(binary), '-bootstrap-owner', '-credential-file', str(credential)], environment)
        owner = json.loads(credential.read_text(encoding='utf-8'))
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        environment['RESEARCHOS_LISTEN'] = f'127.0.0.1:{port}'
        base = f'http://127.0.0.1:{port}'
        log = (out / 'service.log').open('w', encoding='utf-8')
        server = subprocess.Popen([str(binary)], cwd=ROOT, env=environment, stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW)
        for _ in range(60):
            try:
                with urlopen(base + '/healthz', timeout=.5) as response:
                    if response.status == 200:
                        break
            except Exception:
                time.sleep(.2)
        else:
            raise RuntimeError('local server did not start')
        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(str(temp / 'chromium-profile'), channel='chromium', headless=True, viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
            try:
                page = context.pages[0]
                errors, responses = [], []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('response', lambda response: responses.append({'path': urlsplit(response.url).path, 'status': response.status}) if '/v1/' in response.url else None)
                report['browser_version'] = context.browser.version if context.browser else 'persistent chromium'
                login(page, base, '/', owner['token'])
                page.get_by_role('heading', name='项目入口').wait_for()
                page.get_by_label('项目名称').fill('W13 定向回归')
                page.get_by_label('要解决的问题').fill('验证证据路由、状态文字与超时恢复')
                page.get_by_label('首个明确范围').fill('本地公开开发夹具')
                page.get_by_role('button', name='创建项目', exact=True).click()
                page.get_by_role('heading', name='W13 定向回归', exact=True).wait_for()
                project_path = urlsplit(page.url).path
                creds = json.loads(run('provision-fixture', [str(provision), project_path.rsplit('/', 1)[1]], environment))
                refs = [fixture_artifact(base, creds['token'], creds['principal_id'], project_path, 'text/plain', marker.encode(), marker)[1]
                        for marker in ('Regression original A', 'Regression original B')]
                report['fixture_evidence_ids'] = [item['id'] for item in refs]
                browser_regressions(page, base, project_path, owner['token'], refs, report, out)
                report['http_responses'] = responses
                report['browser_errors'] = errors
                assert not errors, errors
                report['status'] = 'PASS'
            except Exception:
                report['failure_traceback'] = traceback.format_exc(limit=8)
                try:
                    report['failure_dom'] = page.locator('main').inner_text(timeout=1000)[:12000]
                    page.screenshot(path=str(out / 'failure.png'), full_page=True)
                except Exception:
                    pass
                raise
            finally:
                context.close()
    except Exception as error:
        report['failure'] = str(error)[:1800]
        report.setdefault('failure_traceback', traceback.format_exc(limit=8))
    finally:
        if server:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
        if log:
            log.close()
        # Only this newly created task-specific temporary directory is removed.
        assert temp.parent == Path(tempfile.gettempdir()).resolve() and temp.name.startswith('researchos-w13-ui-review-')
        shutil.rmtree(temp)
        current = {str(path.relative_to(ROOT)).replace('\\', '/'): digest(path) for path in sources if path.is_file()}
        report['source_unchanged'] = current == manifest
        if not report['source_unchanged']:
            report['status'] = 'FAIL'
        report['screenshot_hashes'] = {p.name: digest(p) for p in sorted(out.glob('*.png'))}
        (out / 'report.json').write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode())
    print(json.dumps({'status': report['status'], 'receipt': str(out), 'failure': report.get('failure')}))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
