"""W13 development browser smoke over a real loopback server and temporary SQLite."""
import hashlib
import base64
import datetime
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
import uuid
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright
from workflow import populated_workflow
from scenarios import draft_conflict, preview_formats, partial_cycle, event_recovery, responsive_screen, preview_switch, native_browser_checks, pdf_document

ROOT = Path(__file__).resolve().parents[2]
GO = Path(os.environ.get('RESEARCHOS_GO') or json.loads((ROOT / 'execution/toolchains/locked.json').read_text(encoding='utf-8'))['tools']['go']['path'])
VIEWPORTS = [(320, 780), (390, 844), (768, 1024), (1024, 768), (1440, 1000), (1920, 1080)]


def contrast(a, b):
    def lightness(value):
        channels = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        values = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in channels]
        return .2126 * values[0] + .7152 * values[1] + .0722 * values[2]
    left, right = sorted([lightness(a), lightness(b)], reverse=True)
    return round((left + .05) / (right + .05), 2)


def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def api_json(base, token, method, path, body=None, etag=None):
    data = None if body is None else body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode('utf-8')
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    if data is not None:
        headers['Content-Type'] = 'application/octet-stream' if isinstance(body, bytes) else 'application/json'
    if method != 'GET':
        headers['Idempotency-Key'] = uuid.uuid4().hex
    if etag:
        headers['If-Match'] = etag
    try:
        with urlopen(Request(base + path, data=data, headers=headers, method=method), timeout=20) as response:
            return json.loads(response.read())
    except HTTPError as error:
        raise RuntimeError(f'{method} {path} -> {error.code}: {error.read()[:350]!r}') from error
    except Exception as error:
        raise RuntimeError(f'{method} {path} -> {type(error).__name__}: {error}') from error


def fixture_artifact(base, token, principal, project_path, media, content, label):
    upload = api_json(base, token, 'POST', project_path.replace('/p/', '/v1/projects/') + '/content', content)
    project_api = project_path.replace('/p/', '/v1/projects/')
    state = api_json(base, token, 'GET', project_api + '/state')
    artifact = api_json(base, token, 'POST', project_api + '/artifacts', {
        'run_id': None, 'kind': 'SOURCE_SNAPSHOT', 'evidence_kind': 'SIMULATED', 'measurement_mode': 'FIXTURE',
        'content_hash': upload['content_hash'], 'storage_key': upload['storage_key'], 'media_type': media,
        'byte_size': len(content), 'input_refs': [], 'source_refs': [], 'produced_by': principal,
        'access_class': 'PROJECT'}, f'"r{state["revision"]}"')
    state = api_json(base, token, 'GET', project_api + '/state')
    now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
    evidence = api_json(base, token, 'POST', project_api + '/evidence', {
        'claim': label, 'stance': 'CONTEXT', 'evidence_kind': 'SIMULATED', 'source_kind': 'SIMULATION',
        'canonical_url': None, 'publisher': None, 'upstream_revision': None, 'published_at': None,
        'modified_at': None, 'retrieved_at': now, 'time_status': 'UNKNOWN',
        'snapshot_artifact_ref': {'entity_type': 'Artifact', 'id': artifact['id'], 'revision': artifact['revision'], 'content_hash': artifact['content_hash']},
        'locator': 'body', 'independence_key': 'sha256:' + hashlib.sha256(label.encode()).hexdigest(),
        'origin_evidence_id': None, 'discovery_urls': [], 'license_status': 'UNKNOWN', 'license_expression': None
    }, f'"r{state["revision"]}"')
    return artifact, evidence


def main():
    if os.environ.get('RESEARCHOS_TASK_ID') != 'W13':
        raise SystemExit('RESEARCHOS_TASK_ID=W13 required')
    if not GO.is_file():
        raise SystemExit('pinned Go executable unavailable')
    run_id = uuid.uuid4().hex
    phase = os.environ.get('RESEARCHOS_UI_PHASE', 'core')
    out = ROOT / ('execution/receipts/W13/c26-recovery/browser' if phase == 'recovery' else 'execution/receipts/W13/frontend') / run_id
    out.mkdir(parents=True)
    report = {'task_id': 'W13', 'run_id': run_id, 'scope': 'DEVELOPMENT_ONLY_BROWSER', 'os': platform.platform(),
              'checks': [], 'screenshots': [], 'limitations': ['Temporary local Owner and SQLite fixture; not a live provider qualification', 'No physical mobile device', 'This phase is not native zoom evidence; see the separately recorded native phase', 'Independent verifier pending', 'Individual checks report execution evidence; independent contract acceptance remains pending']}
    report['execution_status'] = 'EXECUTION_REPORTED'
    report['scenario'] = os.environ.get('RESEARCHOS_UI_RECOVERY_SCENARIO', 'all')
    report['dirty_before'] = subprocess.check_output(['git', 'status', '--short', '--untracked-files=all'], cwd=ROOT, text=True).splitlines()
    if phase == 'recovery':
        report.update(qualification_status='PARTIAL', physical_os_sleep=False, physical_phone=False, independent_acceptance='PENDING')
    report['source_hashes'] = {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p) for p in [*sorted((ROOT / 'apps/web/src').glob('*')), ROOT / 'internal/api/server.go', ROOT / 'ops/ci/ui.py', *sorted((ROOT / 'tests/ui').rglob('*.py')), *sorted((ROOT / 'tests/ui').rglob('*.go'))] if p.is_file()}
    report['cwd'] = str(ROOT)
    report['command'] = ['python', 'tests/ui/browser_smoke.py']
    report['head'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    report['project_identity'] = json.loads((ROOT / 'execution/project_identity.json').read_text(encoding='utf-8'))
    tokens = json.loads((ROOT / 'spec/v2.0/ui/design-tokens.json').read_text(encoding='utf-8'))
    report['contrast_ratios'] = {}
    for theme, colors in tokens['themes'].items():
        measured = {f'{front}/{back}': contrast(colors[front], colors[back]) for front, back, minimum in tokens['contrast_pairs']}
        assert all(measured[f'{front}/{back}'] >= minimum for front, back, minimum in tokens['contrast_pairs']), f'{theme} token contrast failed'
        report['contrast_ratios'][theme] = measured
    server = None
    server_log = None
    temp_path = None
    try:
        with tempfile.TemporaryDirectory(prefix='researchos-w13-ui-', ignore_cleanup_errors=True) as temp:
            temp = Path(temp)
            temp_path = temp
            binary = temp / 'researchos-control.exe'
            environment = dict(os.environ, GOTOOLCHAIN='local', GOENV='off', RESEARCHOS_DATA_DIR=str(temp / 'data'), RESEARCHOS_WEB_DIR=str(ROOT / 'apps/web/dist'))
            build = subprocess.run([str(GO), 'build', '-o', str(binary), './apps/control'], cwd=ROOT, env=environment, capture_output=True, text=True, timeout=180)
            if build.returncode:
                raise RuntimeError('Go build failed: ' + build.stderr[-1200:])
            provision_binary = temp / 'provision.exe'
            provision_build = subprocess.run([str(GO), 'build', '-o', str(provision_binary), './tests/ui/provision'], cwd=ROOT, env=environment, capture_output=True, text=True, timeout=180)
            if provision_build.returncode:
                raise RuntimeError('fixture provision build failed: ' + provision_build.stderr[-1200:])
            credential = temp / 'owner.json'
            bootstrap = subprocess.run([str(binary), '-bootstrap-owner', '-credential-file', str(credential)], cwd=ROOT, env=environment, capture_output=True, text=True, timeout=30)
            if bootstrap.returncode:
                raise RuntimeError('Owner bootstrap failed: ' + bootstrap.stderr[-1200:])
            owner = json.loads(credential.read_text(encoding='utf-8'))
            token, principal = owner['token'], owner['principal_id']
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            environment['RESEARCHOS_LISTEN'] = f'127.0.0.1:{port}'
            server_log = (out / 'service.log').open('w', encoding='utf-8')
            server = subprocess.Popen([str(binary)], cwd=ROOT, env=environment, stdout=server_log, stderr=server_log)
            base = f'http://127.0.0.1:{port}'
            for _ in range(60):
                try:
                    with urlopen(base + '/healthz', timeout=.5) as response:
                        if response.status == 200:
                            break
                except Exception:
                    time.sleep(.2)
            else:
                raise RuntimeError('loopback server did not become ready')
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                report['browser_version'] = browser.version
                page = browser.new_page(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
                errors = []
                responses = []
                external_requests = []
                external_responses = []
                external_failures = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.on('response', lambda response: responses.append({'path': urlsplit(response.url).path, 'status': response.status}) if '/v1/' in response.url else None)
                page.on('response', lambda response: external_responses.append(response.url) if 'invalid.test' in response.url else None)
                page.on('request', lambda request: external_requests.append(request.url) if 'invalid.test' in request.url else None)
                page.on('requestfailed', lambda request: external_failures.append({'url': request.url, 'reason': request.failure}) if 'invalid.test' in request.url else None)
                page.goto(base + '/', wait_until='domcontentloaded')
                page.get_by_label('访问令牌').fill(token)
                page.get_by_role('button', name='打开工作台').click()
                page.get_by_role('heading', name='项目入口').wait_for()
                report['checks'].append('Owner login rendered project entry')
                page.get_by_label('项目名称').fill('W13 浏览器验收')
                page.get_by_label('要解决的问题').fill('验证工作台真实 API 流')
                page.get_by_label('首个明确范围').fill('本地浏览器夹具')
                page.get_by_role('button', name='创建项目').click()
                page.get_by_role('heading', name='W13 浏览器验收').wait_for(timeout=15000)
                project_path = page.url.split(base, 1)[1]
                assert project_path.startswith('/p/'), project_path
                report['checks'].append('Project created through browser and persisted by API')
                phase = os.environ.get('RESEARCHOS_UI_PHASE', 'core')
                report['phase'] = phase
                if phase == 'recovery' and report['scenario'] == 'freshness':
                    from recovery_cases import recovery_cases
                    recovery_cases(page, base, project_path, token, api_json, report, out, freshness_only=True)
                    assert not errors, f'browser errors: {errors}'
                    report['checks'].append('Recovery browser has no unhandled exceptions')
                elif phase in ('workflow', 'plan', 'contracts', 'recovery'):
                    environment['RESEARCHOS_TASK_ID'] = 'W13'
                    provision = subprocess.run([str(provision_binary), project_path.rsplit('/', 1)[1]], cwd=ROOT, env=environment, capture_output=True, text=True, timeout=30)
                    if provision.returncode:
                        raise RuntimeError('workflow provision failed: ' + provision.stderr[-1200:])
                    source = json.loads(provision.stdout)
                    populated_workflow(page, base, project_path, token, source, api_json, provision_binary, environment, ROOT, report, out)
                    if phase == 'recovery':
                        from recovery_cases import recovery_cases
                        recovery_cases(page, base, project_path, token, api_json, report, out)
                        assert not errors, f'browser errors: {errors}'
                        report['checks'].append('Recovery browser has no unhandled exceptions')
                elif phase == 'content':
                    environment['RESEARCHOS_TASK_ID'] = 'W13'
                    provision = subprocess.run([str(provision_binary), project_path.rsplit('/', 1)[1]], cwd=ROOT, env=environment, capture_output=True, text=True, timeout=30)
                    if provision.returncode:
                        raise RuntimeError('content provision failed: ' + provision.stderr[-1200:])
                    from content_cases import content_cases
                    content_cases(page, base, project_path, token, json.loads(provision.stdout), api_json, fixture_artifact, provision_binary, environment, ROOT, report, out)
                elif phase == 'native':
                    environment['RESEARCHOS_TASK_ID'] = 'W13'
                    provision = subprocess.run([str(provision_binary), project_path.rsplit('/', 1)[1]], cwd=ROOT, env=environment, capture_output=True, text=True, timeout=30)
                    if provision.returncode:
                        raise RuntimeError('native provision failed: ' + provision.stderr[-1200:])
                    source = json.loads(provision.stdout)
                    artifact, evidence = fixture_artifact(base, source['token'], source['principal_id'], project_path, 'application/pdf', pdf_document(), 'Native PDF document')
                    report['pdf_fixture'] = {'artifact_id': artifact['id'], 'evidence_id': evidence['id'], 'content_hash': artifact['content_hash']}
                    native_browser_checks(p, temp / 'chromium-profile', base, project_path, token, report, out)
                elif phase == 'core':
                    page.get_by_role('button', name='提出新想法').click()
                    page.get_by_label('你希望推进什么？').fill('建立可验收的研究目标')
                    page.get_by_role('button', name='确认原话并开始规划').click()
                    page.get_by_role('heading', name='规划：建立可验收的研究目标').wait_for(timeout=15000)
                    report['checks'].append('Original natural-language Requirement accepted and bounded planning Goal/Task created through browser')
                    project_api = project_path.replace('/p/', '/v1/projects/')
                    page.get_by_role('button', name='提出新想法').click()
                    page.get_by_label('你希望推进什么？').fill('冲突后保留的用户目标')
                    injected = {'done': False}
                    def conflict_once(route):
                        if route.request.method == 'POST' and not injected['done']:
                            injected['done'] = True
                            state = api_json(base, token, 'GET', project_api + '/state')
                            api_json(base, token, 'POST', project_api + '/requirements', {
                                'requirement_key': 'fixture-' + uuid.uuid4().hex, 'text': '并发独立需求', 'basis': 'USER_STATED',
                                'source_refs': [], 'rationale': '测试并发状态更新', 'supersedes_id': None, 'acceptance_check_ids': []
                            }, f'"r{state["revision"]}"')
                        route.continue_()
                    page.route('**/requirements', conflict_once)
                    page.get_by_role('button', name='确认原话并开始规划').click()
                    page.get_by_text('版本已变化，请核对原话后重试').wait_for(timeout=15000)
                    assert page.get_by_label('你希望推进什么？').input_value() == '冲突后保留的用户目标'
                    page.get_by_role('button', name='核对后重试').click()
                    page.get_by_role('heading', name='规划：冲突后保留的用户目标').wait_for(timeout=15000)
                    page.unroute('**/requirements', conflict_once)
                    report['checks'].append('Actual 412 conflict preserved draft and reconciled against current state before retry')
                    environment['RESEARCHOS_TASK_ID'] = 'W13'
                    provision = subprocess.run([str(provision_binary), project_path.rsplit('/', 1)[1]], cwd=ROOT, env=environment, capture_output=True, text=True, timeout=30)
                    if provision.returncode:
                        raise RuntimeError('source fixture provision failed: ' + provision.stderr[-1200:])
                    source = json.loads(provision.stdout)
                    source_token, source_principal = source['token'], source['principal_id']
                    attack = b'<script>window.fixtureAttack=true</script><img src="https://invalid.test/private"><h1>Untrusted HTML</h1>'
                    html_artifact, html_evidence = fixture_artifact(base, source_token, source_principal, project_path, 'text/html', attack, 'HTML sandbox fixture')
                    page.goto(base + project_path + '/evidence?focus=' + html_evidence['id'], wait_until='domcontentloaded')
                    page.get_by_label('访问令牌').fill(token)
                    page.get_by_role('button', name='打开工作台').click()
                    page.get_by_role('button', name='受控预览').click()
                    page.frame_locator('iframe.preview-frame').get_by_role('heading', name='Untrusted HTML').wait_for()
                    frame = page.locator('iframe.preview-frame').element_handle().content_frame()
                    assert not frame.evaluate('window.fixtureAttack === true')
                    assert not external_responses and all('csp' in item['reason'].lower() for item in external_failures), (external_responses, external_failures)
                    report['preview_external_network'] = {'requests_attempted': len(external_requests), 'responses_received': len(external_responses), 'failures': external_failures}
                    assert page.locator('iframe.preview-frame').get_attribute('sandbox') == ''
                    page.screenshot(path=str(out / 'preview-html-sandbox.png'), full_page=True)
                    report['screenshots'].append('preview-html-sandbox.png')
                    markdown = b'# Fixture\n<script>window.fixtureMarkdownAttack=true</script>\n- safe list'
                    _, markdown_evidence = fixture_artifact(base, source_token, source_principal, project_path, 'text/markdown', markdown, 'Markdown untrusted HTML fixture')
                    page.locator('.list-panel .record-row').filter(has_text=markdown_evidence['id'][:12]).click()
                    page.get_by_role('button', name='受控预览').wait_for()
                    assert page.locator('iframe.preview-frame').count() == 0
                    page.get_by_role('button', name='受控预览').click()
                    page.locator('.preview-markdown').get_by_text('Fixture', exact=True).wait_for()
                    assert page.locator('.preview-markdown script').count() == 0
                    assert 'fixtureMarkdownAttack' in page.locator('.preview-markdown').inner_text()
                    large = (b'a,b\n' * (2 * 1024 * 1024))
                    _, large_evidence = fixture_artifact(base, source_token, source_principal, project_path, 'text/csv', large, 'Large preview fixture')
                    page.locator('.list-panel .record-row').filter(has_text=large_evidence['id'][:12]).click()
                    page.get_by_role('button', name='受控预览').wait_for()
                    assert page.locator('.preview-markdown').count() == 0
                    page.get_by_role('button', name='受控预览').click()
                    page.get_by_text('超过 5 MiB 行内上限').wait_for()
                    assert page.get_by_role('button', name='受控下载').is_visible()
                    report['checks'].append('Real sealed HTML/Markdown/large Artifact previews enforce sandbox, escaped text, and download fallback')
                    preview_formats(page, base, project_path, token, source, fixture_artifact, report, out)
                    preview_switch(page, base, project_path, token, source, fixture_artifact, report)
                    draft_conflict(page, base, project_path, token, source, api_json, report, out)
                    other_project = partial_cycle(page, base, token, api_json, provision_binary, environment, ROOT, report, out)
                    event_recovery(page, base, project_path, token, api_json, report, out, other_project)
                    sections = [('cycles', '选择研究周期'), ('tasks', '选择任务'), ('releases', '选择成果'),
                                ('evidence', '来源证据'), ('experiments', '选择实验'), ('knowledge', '知识与技能'),
                                ('team', '团队与运行器'), ('resources', '费用与资源'), ('settings', '设置与设备')]
                    for path, heading in sections:
                        page.goto(base + project_path + '/' + path, wait_until='domcontentloaded')
                        page.get_by_label('访问令牌').fill(token)
                        page.get_by_role('button', name='打开工作台').click()
                        page.get_by_role('heading', name=heading).wait_for(timeout=15000)
                        page.screenshot(path=str(out / f'screen-{path}.png'), full_page=True)
                        report['screenshots'].append(f'screen-{path}.png')
                        responsive_screen(page, path, report, out)
                    report['checks'].append('All 11 screen entry points render from real deep links')
                    page.goto(base + project_path, wait_until='domcontentloaded')
                    page.get_by_label('访问令牌').fill(token)
                    page.get_by_role('button', name='打开工作台').click()
                    page.get_by_role('heading', name='W13 浏览器验收').wait_for()
                    page.get_by_role('button', name='打开通知，0 条未读').click()
                    page.get_by_label('通知列表').wait_for()
                    page.keyboard.press('Escape')
                    page.get_by_label('通知列表').wait_for(state='hidden')
                    assert not page.get_by_label('通知列表').count()
                    report['checks'].append('Notification drawer opens and closes with Escape')
                    for width, height in VIEWPORTS:
                        page.set_viewport_size({'width': width, 'height': height})
                        page.wait_for_timeout(240)
                        page.screenshot(path=str(out / f'workbench-{width}.png'), full_page=width >= 768)
                        overflow = page.evaluate('document.documentElement.scrollWidth > innerWidth + 1')
                        assert not overflow, f'horizontal overflow at {width}px'
                        report['screenshots'].append(f'workbench-{width}.png')
                        if width <= 390:
                            metrics = page.evaluate("""() => ({closedNav: {visible: getComputedStyle(document.querySelector('.sidebar')).visibility, inert: document.querySelector('.sidebar').inert}, closedRail: {visible: getComputedStyle(document.querySelector('.progress-rail')).visibility, inert: document.querySelector('.progress-rail').inert}, topTargets: [...document.querySelectorAll('.topbar button')].map(b => ({name:b.getAttribute('aria-label') || b.textContent.trim(), width:b.getBoundingClientRect().width, height:b.getBoundingClientRect().height}))})""")
                            assert metrics['closedNav'] == {'visible': 'hidden', 'inert': True}, metrics
                            assert metrics['closedRail'] == {'visible': 'hidden', 'inert': True}, metrics
                            assert all(x['width'] >= 44 and x['height'] >= 44 for x in metrics['topTargets']), metrics
                            report.setdefault('mobile_metrics', {})[str(width)] = metrics
                    page.set_viewport_size({'width': 640, 'height': 900})
                    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth + 1'), 'overflow at additional 640px viewport'
                    page.set_viewport_size({'width': 390, 'height': 844})
                    page.get_by_role('button', name='打开导航').click()
                    assert page.get_by_label('主导航').is_visible()
                    assert page.evaluate('document.activeElement.getAttribute("aria-label")') == '关闭导航'
                    page.keyboard.press('Escape')
                    assert page.evaluate('document.activeElement.getAttribute("aria-label")') == '打开导航'
                    page.get_by_role('button', name='打开阶段进度').click()
                    assert page.get_by_role('complementary', name='阶段进度').is_visible()
                    assert page.evaluate('document.activeElement.getAttribute("aria-label")') == '关闭进度'
                    page.keyboard.press('Escape')
                    report['checks'].append('Mobile drawers and Escape restore focus; additional 640px viewport has no overflow')
                    page.get_by_role('button', name='切换为深色主题').click()
                    page.wait_for_timeout(240)
                    page.screenshot(path=str(out / 'workbench-dark-390.png'), full_page=False)
                    report['screenshots'].append('workbench-dark-390.png')
                    assert page.evaluate('document.documentElement.dataset.theme') == 'dark'
                    report['rendered_tokens'] = {theme: {name: colors[name] for name in ('background', 'surface', 'text', 'muted', 'accent')} for theme, colors in tokens['themes'].items()}
                    for name in ('background', 'surface', 'text', 'muted', 'accent'):
                        actual = page.evaluate('(name) => getComputedStyle(document.documentElement).getPropertyValue("--" + name).trim()', name)
                        assert actual.lower() == tokens['themes']['dark'][name].lower(), (name, actual)
                    page.emulate_media(reduced_motion='reduce')
                    reduced = page.evaluate("getComputedStyle(document.querySelector('.nav-link')).transitionDuration")
                    assert reduced in ('0s', '0ms')
                    report['reduced_motion_transition'] = reduced
                    report['checks'].append('Six responsive viewports and dark theme render without horizontal overflow')
                    assert not errors, f'browser errors: {errors}'
                    report['checks'].append('No unhandled browser exceptions')
                    native_browser_checks(p, temp / 'chromium-profile', base, project_path, token, report, out)
                else:
                    raise ValueError('Unknown UI phase: ' + phase)
                report['http_responses'] = responses
                browser.close()
            server.terminate()
            server.wait(timeout=5)
            server = None
            final_source_hashes = {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p) for p in [*sorted((ROOT / 'apps/web/src').glob('*')), ROOT / 'internal/api/server.go', ROOT / 'ops/ci/ui.py', *sorted((ROOT / 'tests/ui').rglob('*.py')), *sorted((ROOT / 'tests/ui').rglob('*.go'))] if p.is_file()}
            if final_source_hashes != report['source_hashes']:
                report['source_changed_during_run'] = [name for name, value in final_source_hashes.items() if report['source_hashes'].get(name) != value]
                raise RuntimeError('Source changed during browser run; evidence is not a frozen-source pass')
            report['screenshot_hashes'] = {name: digest(out / name) for name in report['screenshots']}
            report['check_count'] = len(report['checks'])
            report['responsive_case_count'] = len(report.get('responsive_matrix', []))
            report['status'] = 'PASS'
    except Exception as error:
        report['status'] = 'FAIL'
        report['failure'] = str(error)[:1800]
        report['failure_traceback'] = traceback.format_exc(limit=8)
        try:
            report['failure_dom'] = page.locator('main').inner_text(timeout=1000)[:12000]
            page.screenshot(path=str(out / 'failure.png'), full_page=True)
        except Exception:
            pass
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
        if server_log is not None:
            server_log.close()
            if report['status'] == 'PASS' and phase != 'recovery':
                (out / 'service.log').unlink()
            else:
                report['service_log'] = 'service.log'
        if temp_path is not None:
            shutil.rmtree(temp_path, ignore_errors=True)
        (out / 'report.json').write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    print(json.dumps({'status': report['status'], 'report': str(out / 'report.json'), 'failure': report.get('failure')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
