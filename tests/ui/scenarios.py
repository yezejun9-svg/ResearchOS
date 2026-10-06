"""Additional real-browser cases. Injected transport faults remain explicit fixtures."""
import base64
import hashlib
import json
import uuid
import datetime
import subprocess
import time


def login(page, base, path, token):
    page.goto(base + path, wait_until='domcontentloaded')
    page.get_by_label('访问令牌').fill(token)
    page.get_by_role('button', name='打开工作台').click()


def seal(api, base, token, principal, project_api, text):
    content = json.dumps(text, ensure_ascii=False).encode()
    upload = api(base, token, 'POST', project_api + '/content', content)
    state = api(base, token, 'GET', project_api + '/state')
    return api(base, token, 'POST', project_api + '/artifacts', {
        'run_id': None, 'kind': 'REPORT', 'evidence_kind': 'GENERATED', 'measurement_mode': 'FIXTURE',
        'content_hash': upload['content_hash'], 'storage_key': upload['storage_key'], 'byte_size': len(content),
        'media_type': 'application/json', 'input_refs': [], 'source_refs': [], 'produced_by': principal,
        'access_class': 'PROJECT'}, f'"r{state["revision"]}"')


def ref(value, kind):
    return {'entity_type': kind, 'id': value['id'], 'revision': value['revision'], 'content_hash': value.get('content_hash')}


def pdf_document():
    objects = [b'<</Type/Catalog/Pages 2 0 R>>', b'<</Type/Pages/Count 1/Kids[3 0 R]>>',
               b'<</Type/Page/Parent 2 0 R/MediaBox[0 0 500 300]/Resources<</Font<</F1 5 0 R>>>>/Contents 4 0 R>>']
    stream = b'BT /F1 24 Tf 50 230 Td (PDF preview fixture) Tj ET'
    objects += [b'<</Length ' + str(len(stream)).encode() + b'>>\nstream\n' + stream + b'\nendstream',
                b'<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>']
    raw, offsets = b'%PDF-1.4\n', [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(raw))
        raw += str(index).encode() + b' 0 obj\n' + obj + b'\nendobj\n'
    start = len(raw)
    raw += b'xref\n0 6\n0000000000 65535 f \n' + b''.join(f'{value:010d} 00000 n \n'.encode() for value in offsets[1:])
    return raw + b'trailer<</Size 6/Root 1 0 R>>\nstartxref\n' + str(start).encode() + b'\n%%EOF'


def change_background(api, base, credentials, project_api, text, owner_token):
    token = credentials['editor_token']
    artifact = seal(api, base, token, credentials['editor_id'], project_api, text)
    profile = api(base, token, 'GET', project_api + '/profile')
    state = api(base, token, 'GET', project_api + '/state')
    body = {'title': 'External fixture background revision', 'reason': 'Independent concurrent browser scenario',
            'base_state_revision': state['revision'],
            'edits': [{'target_ref': ref(profile, 'ProjectProfile'), 'field': 'intent', 'proposed_value_artifact_ref': ref(artifact, 'Artifact'), 'reason': 'External edit'}],
            'migration_steps': [], 'test_check_ids': ['context.inputs-frozen', 'context.impact-exact', 'context.authority-independent'],
            'rollback_steps': ['Submit independently accepted reversal']}
    proposal = api(base, token, 'POST', project_api + '/change-proposals', body, f'"r{state["revision"]}"')
    frozen = {key: proposal[key] for key in ('edits', 'base_state_revision', 'test_check_ids', 'migration_steps', 'rollback_steps')}
    frozen['rules'] = 'W04-change-1'
    contract_hash = 'sha256:' + hashlib.sha256(json.dumps(frozen, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    state = api(base, token, 'GET', project_api + '/state')
    receipt = api(base, credentials['verifier_token'], 'POST', project_api + '/acceptances', {
        'subject_ref': ref(proposal, 'ChangeProposal'), 'run_id': None, 'contract_hash': contract_hash,
        'input_refs': [ref(proposal, 'ChangeProposal')], 'artifact_refs': [],
        'checks': [{'check_id': 'server-recomputes', 'status': 'NOT_RUN', 'evidence_refs': [], 'command_key': None,
                    'actual': 'Server must recompute actual checks', 'exit_code': None, 'started_at': None, 'finished_at': None}],
        'verdict': 'BLOCKED', 'executor_principal_ids': [], 'independence_basis': 'DETERMINISTIC_SERVICE',
        'blocking_conflict_ids': [], 'qualification_ids': [], 'policy_revision': state['policy_revision'],
        'measurement_mode': 'FIXTURE', 'reason': 'Independent verifier service runs actual change checks'}, f'"r{proposal["revision"]}"')
    assert receipt['verdict'] == 'PASS', receipt
    state = api(base, token, 'GET', project_api + '/state')
    api(base, credentials['scheduler_token'], 'POST', project_api + '/change-proposals/' + proposal['id'] + '/apply',
        {'acceptance_id': receipt['id'], 'expected_project_state_revision': state['revision']}, f'"r{proposal["revision"]}"')
    return artifact


def draft_conflict(page, base, project_path, owner_token, credentials, api, report, out):
    project_api = project_path.replace('/p/', '/v1/projects/')
    login(page, base, project_path + '/settings', owner_token)
    page.get_by_role('button', name='编辑项目背景草稿').click()
    page.get_by_label('本地背景草稿').fill('Owner retained draft')
    page.get_by_role('button', name='封存候选并请求重验').click()
    page.get_by_text('当前身份没有候选封存权限。', exact=False).wait_for()
    assert page.get_by_label('本地背景草稿').input_value() == 'Owner retained draft'
    with page.expect_download() as download:
        page.get_by_role('button', name='导出保留的草稿').click()
    retained = json.loads(open(download.value.path(), encoding='utf-8').read())
    assert retained['draft'] == 'Owner retained draft'
    report['checks'].append('Ordinary Owner receives actual 403 and can export intact draft; no role escalation')

    login(page, base, project_path + '/settings', credentials['editor_token'])
    page.get_by_role('button', name='编辑项目背景草稿').click()
    page.get_by_label('本地背景草稿').fill('Local draft must survive conflict')
    original = api(base, credentials['editor_token'], 'GET', project_api + '/profile')
    external = change_background(api, base, credentials, project_api, 'External accepted background', owner_token)
    page.get_by_role('button', name='封存候选并请求重验').click()
    page.get_by_text('背景版本冲突，请保留双方并显式合并').wait_for(timeout=15000)
    assert page.get_by_label('本地背景草稿').input_value() == 'Local draft must survive conflict'
    assert page.get_by_label('外部背景版本').input_value() == 'External accepted background'
    assert page.get_by_label('人工合并后的背景').input_value() == ''
    assert page.get_by_role('button', name='保存双方并提交合并候选').is_disabled()
    page.screenshot(path=str(out / 'draft-conflict.png'), full_page=True)
    report['screenshots'].append('draft-conflict.png')
    page.get_by_label('人工合并后的背景').fill('Merged local and external background after review')
    page.get_by_role('button', name='保存双方并提交合并候选').click()
    page.get_by_text('候选已提交，等待独立验收。', exact=False).wait_for(timeout=15000)
    assert api(base, credentials['editor_token'], 'GET', project_api + '/profile')['intent'] == 'External accepted background'
    artifacts = api(base, credentials['editor_token'], 'GET', project_api + '/artifacts')['items']
    required = ['Local draft must survive conflict', 'External accepted background', 'Merged local and external background after review']
    hashes = {item['content_hash'] for item in artifacts}
    for text in required:
        expected = 'sha256:' + hashlib.sha256(json.dumps(text, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
        assert expected in hashes, text
    sealed = api(base, credentials['editor_token'], 'GET', project_api + '/artifacts/' + external['id'])
    assert sealed['content_hash'] == external['content_hash'] and sealed['revision'] == external['revision']
    report['draft_conflict'] = {'original_profile_revision': original['revision'], 'retained_candidate_hashes': [item['content_hash'] for item in artifacts if item['kind'] == 'REPORT'], 'sealed_original_unchanged': True}
    report['checks'].append('Actual 412 on frozen profile revision preserves both drafts, explicit merge seals three candidates and creates pending ChangeProposal without replacing accepted profile')


def preview_formats(page, base, project_path, token, credentials, fixture_artifact, report, out):
    formats = [
        ('application/json', b'{"fixture":true,"value":42}', '.preview-text', '"value": 42'),
        ('text/csv', b'name,value\nfixture,42', '.preview-text', 'fixture,42'),
        ('text/javascript', b'const fixture = "code-preview";', '.preview-text', 'code-preview'),
        ('image/png', base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j+WQAAAAASUVORK5CYII='), '.preview-image', None),
        ('application/pdf', pdf_document(), 'iframe[title="PDF 预览"]', None),
    ]
    for media, content, selector, expected in formats:
        artifact, evidence = fixture_artifact(base, credentials['token'], credentials['principal_id'], project_path, media, content, media + ' fixture')
        login(page, base, project_path + '/evidence?focus=' + evidence['id'], token)
        page.get_by_role('button', name='受控预览').click()
        page.locator(selector).wait_for()
        if expected:
            assert expected in page.locator(selector).inner_text()
        if media == 'image/png':
            page.wait_for_function('document.querySelector(".preview-image")?.naturalWidth > 0')
        assert artifact['content_hash'] in page.locator('.artifact-preview').inner_text()
        with page.expect_download() as download:
            page.get_by_role('link', name='下载已核对的内容').click()
        assert hashlib.sha256(open(download.value.path(), 'rb').read()).hexdigest() == artifact['content_hash'].split(':')[1]
        report['checks'].append(f'{media} real sealed content hash and controlled download verified; browser preview mounted')
        if media == 'application/pdf':
            report['pdf_fixture'] = {'artifact_id': artifact['id'], 'evidence_id': evidence['id'], 'content_hash': artifact['content_hash']}
    report.setdefault('limitations', []).append('PDF sandbox iframe mounted and downloaded bytes verified; browser PDF document rendering is not certified by this fixture')


def preview_switch(page, base, project_path, token, credentials, fixture_artifact, report):
    first_content = b'{"version":"old pending preview"}'
    first, first_evidence = fixture_artifact(base, credentials['token'], credentials['principal_id'], project_path, 'application/json', first_content, 'pending preview A')
    second, second_evidence = fixture_artifact(base, credentials['token'], credentials['principal_id'], project_path, 'application/json', b'{"version":"new fixed preview"}', 'pending preview B')
    login(page, base, project_path + '/evidence?focus=' + first_evidence['id'], token)
    held = []
    def delayed(route):
        held.append(route)
    pattern = '**/artifacts/' + first['id'] + '/content'
    page.route(pattern, delayed)
    page.get_by_role('button', name='受控预览').click()
    page.get_by_text('正在读取并核对哈希…').wait_for()
    page.locator('.list-panel .record-row').filter(has_text=second_evidence['id'][:12]).click()
    page.get_by_role('button', name='受控预览').click()
    page.locator('.preview-text').get_by_text('new fixed preview', exact=False).wait_for()
    assert held, 'first request was not actually delayed'
    for route in held:
        route.fulfill(status=200, content_type='application/json', body=first_content)
    page.wait_for_timeout(120)
    assert 'old pending preview' not in page.locator('.artifact-preview').inner_text()
    assert second['content_hash'] in page.locator('.artifact-preview').inner_text()
    page.unroute(pattern, delayed)
    report['checks'].append('Switch during an in-flight Artifact content request aborts the old reader; late bytes cannot overwrite the newly selected fixed hash')


def partial_cycle(page, base, token, api, provision_binary, environment, root, report, out):
    source_id = uuid.uuid4().hex
    profile = api(base, token, 'POST', '/v1/projects', {
        'name': 'X missing coverage fixture', 'intent': 'Persist and display the true source gap',
        'facts': [], 'accepted_scope': ['W13 development coverage display'], 'constraints': [],
        'source_document_refs': [], 'read_snapshot_ids': [],
        'source_configs': [{'source_id': source_id, 'kind': 'X', 'required': True, 'enabled': False,
                            'query': 'research agents', 'allowed_origins': ['https://x.com'], 'credential_ref': None}]})
    project_id = profile['project_id']
    project_api = '/v1/projects/' + project_id
    issued = subprocess.run([str(provision_binary), project_id], cwd=root, env=environment, capture_output=True, text=True, timeout=30)
    assert issued.returncode == 0, issued.stderr
    credentials = json.loads(issued.stdout)
    now = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1)
    state = api(base, token, 'GET', project_api + '/state')
    cycle = api(base, token, 'POST', project_api + '/research-cycles', {
        'trigger': 'SCHEDULE', 'window_from': (now - datetime.timedelta(days=7)).isoformat().replace('+00:00', 'Z'),
        'window_to': now.isoformat().replace('+00:00', 'Z'), 'profile_revision': profile['revision']}, f'"r{state["revision"]}"')
    checkpoint = seal(api, base, credentials['editor_token'], credentials['editor_id'], project_api,
                      'Local checkpoint: X credentials missing; user-facing coverage remains incomplete')
    cycle = api(base, credentials['scheduler_token'], 'POST', project_api + '/research-cycles/' + cycle['id'] + '/checkpoint',
                {'source_coverage': cycle['source_coverage'], 'candidate_evidence_ids': [], 'required_experiment_ids': [],
                 'decision_ids': [], 'follow_up_task_ids': [], 'checkpoint_artifact_id': checkpoint['id']}, f'"r{cycle["revision"]}"')
    cycle = api(base, credentials['scheduler_token'], 'POST', project_api + '/research-cycles/' + cycle['id'] + '/close',
                {'requested_status': 'PARTIAL', 'outcome_summary': 'X missing; retain true partial coverage'}, f'"r{cycle["revision"]}"')
    assert cycle['status'] == 'PARTIAL', cycle
    assert cycle['source_coverage'][0]['status'] == 'NOT_CONFIGURED'
    for suffix, name in [('', 'dashboard'), ('/cycles/' + cycle['id'], 'detail')]:
        login(page, base, '/p/' + project_id + suffix, token)
        page.get_by_text('PARTIAL', exact=True).wait_for()
        page.get_by_text('NOT_CONFIGURED', exact=True).first.wait_for()
        assert cycle['source_coverage'][0]['gap_reason'] in page.locator('main').inner_text()
        page.screenshot(path=str(out / f'partial-cycle-{name}.png'), full_page=True)
        report['screenshots'].append(f'partial-cycle-{name}.png')
    report['checks'].append('Real API creates, checkpoints, and closes missing-X cycle as PARTIAL; dashboard and cycle detail show NOT_CONFIGURED and actual reason after active_cycle_id clears')
    return project_id


def event_recovery(page, base, project_path, token, api, report, out, other_project, other_name="X missing coverage fixture", other_status="PARTIAL"):
    project_id = project_path.rsplit('/', 1)[1]
    project_api = project_path.replace('/p/', '/v1/projects/')
    initial = api(base, token, 'GET', project_api + '/progress')
    state = api(base, token, 'GET', project_api + '/state')
    api(base, token, 'POST', project_api + '/requirements', {
        'requirement_key': 'event-' + uuid.uuid4().hex, 'text': 'Actual event for replay transport fixture',
        'basis': 'USER_STATED', 'source_refs': [], 'rationale': 'W13 recovery', 'supersedes_id': None,
        'acceptance_check_ids': []}, f'"r{state["revision"]}"')
    events = api(base, token, 'GET', project_api + '/events?after_sequence=' + str(initial['as_of_event_sequence']) + '&limit=100')['items']
    new_events = [event for event in events if int(event['sequence']) > int(initial['as_of_event_sequence'])]
    assert new_events, 'real replay event missing'
    event = new_events[0]
    requests, progress_reads = [], []
    initial_reads = {'count': 0}
    def progress(route):
        initial_reads['count'] += 1
        progress_reads.append(initial_reads['count'])
        if initial_reads['count'] <= 2:
            route.fulfill(status=200, content_type='application/json', body=json.dumps(initial))
        else:
            route.continue_()
    def stream(route):
        requests.append(route.request.headers.get('last-event-id'))
        if len(requests) == 1:
            foreign = dict(event, id='foreign-frame', project_id=other_project)
            gap = dict(event, id='gap-frame', sequence=int(event['sequence']) + 2)
            body = ''.join('data: ' + json.dumps(value) + '\n\n' for value in [foreign, event, event, gap])
            route.fulfill(status=200, content_type='text/event-stream', body=body)
        elif len(requests) == 2:
            route.fulfill(status=410, content_type='application/json', body=json.dumps({'code': 'CURSOR_EXPIRED', 'message': 'W13 injected cursor expiry'}))
        else:
            route.continue_()
    page.add_init_script("""window.readerEvidence={opened:0,cancelled:0,released:0};
      const original=ReadableStream.prototype.getReader;
      ReadableStream.prototype.getReader=function(...args){const r=original.apply(this,args);window.readerEvidence.opened++;
        const cancel=r.cancel.bind(r), release=r.releaseLock.bind(r);
        r.cancel=(...a)=>{window.readerEvidence.cancelled++;return cancel(...a)};
        r.releaseLock=(...a)=>{window.readerEvidence.released++;return release(...a)};return r};""")
    page.route('**' + project_api + '/progress', progress)
    page.route('**' + project_api + '/events/stream', stream)
    login(page, base, project_path, token)
    page.wait_for_function('window.readerEvidence.released >= 1', timeout=15000)
    deadline = time.monotonic() + 15
    while len(requests) < 3 and time.monotonic() < deadline:
        page.wait_for_timeout(100)
    assert len(requests) >= 3, requests
    current = api(base, token, 'GET', project_api + '/progress')
    assert requests[0] == str(initial['as_of_event_sequence']), requests
    assert requests[1] == str(current['as_of_event_sequence']) and requests[2] == requests[1], requests
    assert not page.locator('.connection-banner').count(), 'reconnected stream must clear offline banner even without new events'
    assert str(current['as_of_event_sequence']) in page.locator('.progress-rail').inner_text()
    readers = page.evaluate('window.readerEvidence')
    assert readers['cancelled'] >= 1 and readers['released'] >= 1, readers
    report['event_recovery'] = {'transport': 'injected duplicate, foreign, gap, 410 frames over real server snapshots', 'last_event_ids': requests.copy(), 'snapshot_reads': len(progress_reads), 'reader_cleanup': readers}
    page.unroute('**' + project_api + '/progress', progress)
    page.unroute('**' + project_api + '/events/stream', stream)
    page.context.set_offline(True)
    page.locator('.connection-banner').wait_for()
    assert '最后同步' in page.locator('.connection-banner').inner_text()
    page.screenshot(path=str(out / 'offline-last-sync.png'), full_page=True)
    report['screenshots'].append('offline-last-sync.png')
    page.context.set_offline(False)
    page.locator('.connection-banner').wait_for(state='hidden', timeout=15000)
    assert page.evaluate('window.readerEvidence.opened - window.readerEvidence.released') <= 1
    page.get_by_role('link', name='W13 浏览器验收 切换项目').click()
    page.get_by_role('link').filter(has_text=other_name).click()
    page.get_by_role('heading', name=other_name).wait_for()
    assert '建立可验收的研究目标' not in page.locator('main').inner_text()
    if other_status:
        page.get_by_text(other_status, exact=True).wait_for()
    report['checks'].append('Browser SSE deduplicates real replay event, ignores foreign project frame, cancels gap reader, resets 410 cursor from server snapshot; offline last-sync and project switch remain isolated')


def responsive_screen(page, path, report, out):
    for theme in ('light', 'dark'):
        if page.evaluate('document.documentElement.dataset.theme') != theme:
            page.get_by_role('button', name='切换为' + ('深色' if theme == 'dark' else '浅色') + '主题').click()
        for width, height in [(320, 780), (390, 844), (768, 1024), (1024, 768), (1440, 1000), (1920, 1080)]:
            page.set_viewport_size({'width': width, 'height': height})
            page.wait_for_timeout(50)
            result = page.evaluate("""() => ({overflow:document.documentElement.scrollWidth>innerWidth+1,
              targets:[...document.querySelectorAll('button,a,input,select,textarea,summary')].filter(el=>{
                const s=getComputedStyle(el);return s.visibility==='visible' && el.getClientRects().length && !el.closest('[inert]')
              }).map(el=>({name:el.getAttribute('aria-label')||el.textContent.trim().slice(0,40),width:el.getBoundingClientRect().width,height:el.getBoundingClientRect().height}))})""")
            assert not result['overflow'], (path, theme, width, 'overflow')
            if width <= 390:
                small = [target for target in result['targets'] if target['width'] < 44 or target['height'] < 44]
                assert not small, (path, theme, width, small)
            report.setdefault('responsive_matrix', []).append({'screen': path, 'theme': theme, 'width': width, 'height': height, 'no_overflow': True, 'mobile_targets_44px': True if width <= 390 else None})
            if width in (320, 390, 768, 1024, 1440):
                name = f'{path}-{theme}-{width}.png'
                page.evaluate('scrollTo(0, 0)')
                page.screenshot(path=str(out / name), full_page=width >= 768)
                report['screenshots'].append(name)
    page.set_viewport_size({'width': 1440, 'height': 1000})
    page.get_by_role('button', name='切换为浅色主题').click()


def native_browser_checks(playwright, profile_dir, base, project_path, token, report, out):
    context = playwright.chromium.launch_persistent_context(str(profile_dir), channel='chromium', headless=True,
                                                           viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
    page = context.pages[0]
    try:
        page.goto('chrome://settings', wait_until='domcontentloaded')
        zoom = page.evaluate('async()=>{await chrome.settingsPrivate.setDefaultZoom(2);return await chrome.settingsPrivate.getDefaultZoom()}')
        assert zoom == 2
        for suffix in ['', '/cycles', '/tasks', '/releases', '/evidence', '/experiments', '/knowledge', '/team', '/resources', '/settings']:
            login(page, base, project_path + suffix, token)
            page.locator('main h1').wait_for()
            metrics = page.evaluate('({innerWidth,outerWidth,devicePixelRatio,scale:visualViewport.scale,overflow:document.documentElement.scrollWidth>innerWidth+1})')
            assert metrics == {'innerWidth': 720, 'outerWidth': 1440, 'devicePixelRatio': 2, 'scale': 1, 'overflow': False}, metrics
            boxes = page.evaluate('''() => [...document.querySelectorAll('button,a,input,select,textarea,summary')].filter(e=>getComputedStyle(e).visibility==='visible' && e.getClientRects().length && !e.closest('[inert]')).map(e=>({name:e.getAttribute('aria-label')||e.textContent.trim().slice(0,50),left:e.getBoundingClientRect().left,right:e.getBoundingClientRect().right,width:e.getBoundingClientRect().width}))''')
            assert all(box['left'] >= -1 and box['right'] <= metrics['innerWidth'] + 1 for box in boxes), (suffix, boxes)
            report.setdefault('browser_zoom_200_percent', []).append({'path': suffix or 'workbench', **metrics, 'controls_within_viewport': boxes})
        page.get_by_role('button', name='打开导航').click()
        page.get_by_role('button', name='关闭导航').wait_for()
        page.keyboard.press('Escape')
        assert page.evaluate('document.activeElement.getAttribute("aria-label")') == '打开导航'
        page.get_by_role('button', name='编辑项目背景草稿').click()
        page.get_by_label('本地背景草稿').fill('200 percent zoom draft remains usable')
        assert page.get_by_label('本地背景草稿').input_value() == '200 percent zoom draft remains usable'
        page.evaluate('scrollTo(0,0)')
        page.screenshot(path=str(out / 'settings-real-browser-200-percent.png'), full_page=False)
        report['screenshots'].append('settings-real-browser-200-percent.png')
        report['checks'].append('Real Chromium default zoom preference 2.0 renders ten project screens at outerWidth1440/innerWidth720/DPR2/visualScale1 without whole-page overflow')
        report['limitations'] = [value for value in report['limitations'] if not value.startswith('Actual 200% browser zoom')]
        page.goto('chrome://settings', wait_until='domcontentloaded')
        page.evaluate('chrome.settingsPrivate.setDefaultZoom(1)')
        login(page, base, project_path + '/evidence?focus=' + report['pdf_fixture']['evidence_id'], token)
        page.get_by_role('button', name='受控预览').click()
        page.wait_for_timeout(1800)
        viewer = next((frame for frame in page.frames if frame.url.startswith('chrome-extension://')), None)
        assert viewer is not None, [(frame.url) for frame in page.frames]
        viewer.locator('pdf-viewer').wait_for()
        page.screenshot(path=str(out / 'pdf-native-rendered.png'), full_page=True)
        report['screenshots'].append('pdf-native-rendered.png')
        report['native_pdf'] = {'viewer_extension_loaded': True, 'viewer_origin': viewer.url, 'pdf_viewer_enabled': page.evaluate('navigator.pdfViewerEnabled'), 'viewer_controls': viewer.locator('input').evaluate_all('(elements)=>elements.map(e=>({id:e.id,value:e.value,title:e.title}))')}
        report['checks'].append('Full Chromium native PDF viewer loads the one-page sealed PDF; actual page pixels and viewer controls captured for visual review')
        report['limitations'] = [value for value in report['limitations'] if not value.startswith('PDF sandbox iframe')]
    finally:
        context.close()
