"""Focused UI contract fixtures; authority comes from the loopback service."""
import json
from scenarios import login, ref
from workflow import now


def exact_plan_case(page, base, project_path, owner, credentials, get, post, provision, task, claim, artifact_for_run, report, out):
    reported = []
    accepted = []
    for index in range(6):
        text = json.dumps({'C18': index}, separators=(',', ':'))
        current, run, lease = claim(task('C18 task ' + str(index), text))
        artifact = artifact_for_run(run, text)
        provision('observe', {'spec': {'run_id': run['id'], 'task_id': current['id'], 'epoch': run['lease_epoch']},
            'state': 'SETTLED', 'children_stopped': True, 'queue_empty': True, 'exit_code': 0, 'ended': now(),
            'protocol': {'settled': True}, 'artifacts': [{'path': 'result.json', 'content_hash': artifact['content_hash'], 'byte_size': artifact['byte_size']}]})
        post('/runs/' + run['id'] + '/report', {'lease_token': lease, 'lease_epoch': run['lease_epoch'], 'runtime_settled': True,
            'execution_report': 'C18 actual reported result', 'exit_code': 0, 'result_artifact_ids': [artifact['id']],
            'checkpoint_artifact_id': None}, run, credentials['editor_token'])
        current = get('/tasks/' + current['id'])
        if index >= 4:
            reported.append(current['id'])
            continue
        receipt = post('/acceptances', {'subject_ref': ref(current, 'Task'), 'run_id': run['id'],
            'contract_hash': current['acceptance_contract']['contract_hash'], 'input_refs': current['input_refs'],
            'artifact_refs': [ref(artifact, 'Artifact')],
            'checks': [{'check_id': 'json-result', 'status': 'NOT_RUN', 'evidence_refs': [], 'command_key': 'orchestration.json-equals',
                        'actual': 'Request independent server computation', 'exit_code': None, 'started_at': None, 'finished_at': None}],
            'verdict': 'PASS', 'executor_principal_ids': [credentials['editor_id']], 'independence_basis': 'DETERMINISTIC_SERVICE',
            'blocking_conflict_ids': [], 'qualification_ids': [], 'policy_revision': get('/state')['policy_revision'],
            'measurement_mode': 'FIXTURE', 'reason': 'C18 actual independent equality check'}, current, credentials['verifier_token'])
        accepted.append({'task_id': current['id'], 'acceptance_id': receipt['id'], 'artifact_ref': ref(artifact, 'Artifact')})
    provision('verifying', reported)
    first = get('/progress')
    first_stage = next(stage for stage in first['stages'] if stage['stage'] == 'verification')
    assert [first_stage[k] for k in ('planned', 'accepted', 'pending_review', 'blocked', 'active')] == [6, 4, 2, 0, 0]
    login(page, base, project_path, owner)
    page.locator('.stage-count', has_text='4 / 6 已验收').wait_for()
    assert page.locator('.stage-extra', has_text='2 待评审').is_visible()
    page.screenshot(path=str(out / 'plan-before-desktop.png'), full_page=False)
    report['screenshots'].append('plan-before-desktop.png')
    ready = [task('C18 added ready ' + str(index), '{}') for index in range(3)]
    second = get('/progress')
    second_stage = next(stage for stage in second['stages'] if stage['stage'] == 'verification')
    assert [second_stage[k] for k in ('planned', 'accepted', 'pending_review', 'blocked', 'active')] == [9, 4, 2, 0, 0]
    assert second['plan_revision'] > first['plan_revision']
    page.locator('.stage-count', has_text='4 / 9 已验收').wait_for()
    assert page.locator('.stage-extra', has_text='2 待评审').is_visible()
    assert second['plan_change_note'] in page.locator('.progress-rail').inner_text()
    assert all(item['status'] == 'READY' for item in ready)
    page.get_by_text('待执行 3', exact=True).wait_for()
    page.screenshot(path=str(out / 'plan-after-desktop.png'), full_page=False)
    report['screenshots'].append('plan-after-desktop.png')
    # A delayed obsolete projection must not replace an already observed revision.
    prefix = project_path.replace('/p/', '/v1/projects/')
    def obsolete(route):
        route.fulfill(status=200, content_type='application/json', body=json.dumps(first))
    page.route('**' + prefix + '/progress', obsolete)
    with page.expect_response(lambda response: response.url.endswith('/progress')):
        post('/requirements', {'requirement_key': 'C18-stale-refresh', 'text': 'Trigger a snapshot refresh without changing the plan',
            'basis': 'USER_STATED', 'source_refs': [], 'rationale': 'C18 old projection recovery', 'supersedes_id': None, 'acceptance_check_ids': []})
    page.wait_for_timeout(300)
    assert page.locator('.stage-count', has_text='4 / 9 已验收').count() == 1, 'obsolete projection rolled back the displayed plan'
    assert second['plan_change_note'] in page.locator('.progress-rail').inner_text()
    page.unroute('**' + prefix + '/progress', obsolete)
    page.set_viewport_size({'width': 390, 'height': 844})
    page.get_by_role('button', name='打开阶段进度').click()
    assert page.locator('.stage-count', has_text='4 / 9 已验收').is_visible()
    page.wait_for_function("document.querySelector('.progress-rail').getBoundingClientRect().right <= innerWidth + 1")
    page.screenshot(path=str(out / 'plan-after-mobile.png'), full_page=False)
    report['screenshots'].append('plan-after-mobile.png')
    page.keyboard.press('Escape')
    report['plan_contract'] = {'before': first, 'after': second, 'accepted_receipts': accepted, 'verifying_task_ids': reported,
        'ready_task_ids': [item['id'] for item in ready], 'transient_fixture': 'Only EXECUTION_REPORTED -> VERIFYING is seeded; all four ACCEPTED tasks have actual independent service receipts',
        'plan_revision_rule': 'One revision per actual task creation/planning-field change; revisions are server generated, not rewritten to 1/2', 'old_projection_ignored': True}
    report['checks'].append('C18 actual independent receipts produce 4/6 accepted and 2 verifying, then 4/9 with three READY tasks; stale projection cannot roll back desktop/mobile counts or plan reason')

    if report.get('phase') == 'contracts':
        state_matrix(page, base, project_path, owner, get, post, report, out, accepted[0])
        notification_case(page, base, project_path, owner, credentials, get, post, report, out, accepted[0])
    elif report.get('phase') == 'recovery':
        notification_case(page, base, project_path, owner, credentials, get, post, report, out, accepted[0])


def state_matrix(page, base, project_path, owner, get, post, report, out, accepted):
    import jsonschema
    from pathlib import Path
    schema = json.loads((Path(__file__).resolve().parents[2] / 'spec/v2.0/contracts/domain.schema.json').read_text(encoding='utf-8'))
    task = get('/tasks/' + accepted['task_id'])
    run = get('/runs/' + task['active_run_id'])
    task_labels = {'DRAFT':'草稿','READY':'待执行','RUNNING':'执行中','EXECUTION_REPORTED':'结果已提交','VERIFYING':'验收中','ACCEPTED':'已验收','FAILED':'失败','BLOCKED':'受阻','CANCELLED':'已取消','NEEDS_REVALIDATION':'需重验','DEFERRED_NO_PROGRESS':'无进展延期'}
    run_labels = {'QUEUED':'排队','STARTING':'启动中','RUNNING':'运行中','CANCEL_REQUESTED':'取消请求中','SETTLED':'执行已结束','FAILED':'执行失败','CANCELLED':'已取消','LOST':'连接丢失','RECONCILING':'恢复对账中'}
    prefix = project_path.replace('/p/', '/v1/projects/')
    response = {'task': task, 'run': run, 'error': None, 'hold': False, 'pending': []}
    def task_reply(route):
        if response['hold']:
            response['pending'].append(route)
        elif response['error']:
            route.fulfill(status=response['error'], content_type='application/json', body=json.dumps({'code':'UI_CONTRACT_FIXTURE','message':'Controlled state fixture','correlation_id':'w13-state-fixture'}))
        else:
            route.fulfill(status=200, content_type='application/json', body=json.dumps(response['task']))
    def run_reply(route):
        route.fulfill(status=200, content_type='application/json', body=json.dumps(response['run']))
    def disconnected_stream(route):
        route.abort('failed')
    page.route('**' + prefix + '/events/stream', disconnected_stream)
    page.route('**' + prefix + '/tasks/' + task['id'], task_reply)
    page.route('**' + prefix + '/runs/' + run['id'], run_reply)
    page.set_viewport_size({'width':1440,'height':1000})
    for status, label in task_labels.items():
        response['task'] = dict(task, status=status)
        jsonschema.validate(response['task'], {'$ref':'#/$defs/Task','$defs':schema['$defs']})
        login(page, base, project_path + '/tasks/' + task['id'], owner)
        page.locator('.page-heading .tag', has_text=label).wait_for()
        if status == 'VERIFYING':
            page.get_by_text('检查正在进行，尚未计入已验收。', exact=True).wait_for()
            page.screenshot(path=str(out / 'task-verifying.png'), full_page=False)
            report['screenshots'].append('task-verifying.png')
    for status, label in run_labels.items():
        response['task'] = dict(task, status='RUNNING')
        response['run'] = dict(run, status=status)
        jsonschema.validate(response['run'], {'$ref':'#/$defs/Run','$defs':schema['$defs']})
        login(page, base, project_path + '/tasks/' + task['id'], owner)
        page.locator('.meta-line .tag', has_text=label).wait_for()
        if status == 'CANCEL_REQUESTED':
            page.get_by_text('取消已请求，执行器尚未确认。', exact=True).wait_for()
    errors = {403:'无权访问',404:'记录不存在',429:'请求被限流',503:'服务能力尚未提供',500:'读取失败',412:'版本已变化'}
    response['task'], response['run'] = task, run
    for status, label in errors.items():
        response['error'] = status
        login(page, base, project_path + '/tasks/' + task['id'], owner)
        page.locator('.state-notice', has_text=label).wait_for()
        assert 'w13-state-fixture' in page.locator('.state-notice').first.inner_text()
        response['error'] = None
        page.get_by_role('button', name='重新读取', exact=True).first.click()
        page.get_by_role('heading', name=task['title'], exact=True).wait_for()
    response['hold'] = True
    login(page, base, project_path + '/tasks/' + task['id'], owner)
    page.locator('.loading-state').first.wait_for()
    assert response['pending']
    page.screenshot(path=str(out / 'task-loading.png'), full_page=False)
    report['screenshots'].append('task-loading.png')
    response['hold'] = False
    for request in response['pending']:
        request.fulfill(status=200, content_type='application/json', body=json.dumps(task))
    page.get_by_role('heading', name=task['title'], exact=True).wait_for()
    page.unroute('**' + prefix + '/tasks/' + task['id'], task_reply)
    page.unroute('**' + prefix + '/runs/' + run['id'], run_reply)
    page.unroute('**' + prefix + '/events/stream', disconnected_stream)
    page.set_viewport_size({'width':768,'height':1024})
    for label in ['工作台','研究周期','成果审查','来源证据','实验评测','知识技能','团队运行器','费用资源','设置设备']:
        assert page.get_by_role('navigation', name='主导航').get_by_role('link', name=label, exact=True).count() == 1
    report['state_matrix'] = {'task_states':list(task_labels), 'run_states':list(run_labels), 'http_errors_recovered':list(errors),
        'loading_recovered':True,'source':'Schema-validated fixed HTTP response fixtures based on real Task/Run; no runtime transitions or acceptances fabricated by these cases', 'tablet_navigation_accessible_names':True}
    report['checks'].append('C23 fixed backend matrix renders all 11 Task/9 Run states, distinguishes VERIFYING, recovers six HTTP errors and pending loading; tablet icon navigation retains accessible names')


def notification_case(page, base, project_path, owner, credentials, get, post, report, out, accepted):
    prefix = project_path.replace('/p/', '/v1/projects/')
    page.set_viewport_size({'width':390,'height':844})
    login(page, base, project_path, owner)
    page.get_by_role('button', name='打开通知，0 条未读').wait_for()
    baseline = get('/progress')
    page.context.set_offline(True)
    page.locator('.connection-banner').wait_for()
    release = post('/releases', {'scope':'PROJECT','software_version':None,'summary':'C17 offline release',
        'changes':['Independent fixture acceptance'], 'decision_ids':[], 'artifact_refs':[accepted['artifact_ref']],
        'acceptance_ids':[accepted['acceptance_id']], 'open_issues':['No live provider qualification'], 'next_steps':['Review captured evidence'],
        'policy_revision':get('/state')['policy_revision'],'supersedes_id':None}, token=credentials['scheduler_token'])
    event_page = get('/events?after_sequence=' + str(baseline['as_of_event_sequence']) + '&limit=100')
    events = event_page['items']
    assert not event_page['next_cursor'], 'single release unexpectedly exceeds the replay batch'
    assert events and all(event['sequence'] > baseline['as_of_event_sequence'] for event in events)
    assert any(event.get('aggregate_ref', {}).get('id') == release['id'] for event in events)
    notices = get('/notifications')['items']
    assert len(notices) == 1 and notices[0]['release_id'] == release['id']
    stream_calls, writes, replay_frames = [], [], []
    def replay(route):
        stream_calls.append(route.request.headers.get('last-event-id'))
        if len(stream_calls) == 1:
            body = ''.join('data: ' + json.dumps(event) + '\n\n' for event in events for _ in range(5))
            body += ''.join('data: ' + json.dumps(event) + '\n\n' for event in reversed(events))
            route.fulfill(status=200, content_type='text/event-stream', body=body)
            replay_frames.extend([event['id'] for event in events for _ in range(5)])
            replay_frames.extend([event['id'] for event in reversed(events)])
        else:
            route.continue_()
    def record(request):
        if prefix in request.url and request.method != 'GET': writes.append(request.method + ' ' + request.url)
    page.route('**' + prefix + '/events/stream', replay)
    page.on('request', record)
    page.context.set_offline(False)
    page.locator('.connection-banner').wait_for(state='hidden', timeout=15000)
    page.get_by_role('button', name='打开通知，1 条未读').wait_for()
    page.wait_for_timeout(2500)
    page.get_by_role('button', name='打开通知，1 条未读').click()
    assert page.locator('.notice-row').count() == 1
    link = page.get_by_role('link', name='查看成果', exact=True)
    assert link.get_attribute('href') == project_path + '/releases/' + release['id']
    assert not writes, writes
    assert len(replay_frames) == 6 * len(events) and stream_calls, (replay_frames, stream_calls)
    page.remove_listener('request', record)
    page.get_by_role('button', name='标记已读', exact=True).click()
    page.get_by_text('已读', exact=True).wait_for()
    current = get('/notifications')['items'][0]
    post('/notifications/' + current['id'] + '/read', {'reason':'C17 repeated read is idempotent'}, current)
    assert len(get('/notifications')['items']) == 1 and get('/notifications')['items'][0]['status'] == 'READ'
    link.click()
    page.get_by_role('heading', name='C17 offline release', exact=True).wait_for()
    assert accepted['artifact_ref']['content_hash'] in page.locator('.artifact-preview').inner_text()
    assert accepted['acceptance_id'][:12] in page.locator('main').inner_text()
    page.get_by_role('button', name='受控预览').click()
    page.locator('.preview-text').get_by_text('"C18": 0', exact=False).wait_for()
    page.evaluate('scrollTo(0,0)')
    page.screenshot(path=str(out / 'notification-offline-deeplink-mobile.png'), full_page=False)
    report['screenshots'].append('notification-offline-deeplink-mobile.png')
    page.unroute('**' + prefix + '/events/stream', replay)
    report['notification_contract'] = {'release_id':release['id'],'artifact_ref':accepted['artifact_ref'],'acceptance_id':accepted['acceptance_id'],
        'notification_id':current['id'],'copies_per_event':5,'reversed_old_events':len(events),'replay_frame_count':len(replay_frames),'replay_event_ids':replay_frames,'stream_last_event_ids':stream_calls,'writes_from_replay':writes,
        'offline_delivery_recovered':True,'read_twice_same_logical_notification':True,'physical_phone':False}
    report['checks'].append('C17/C26 mobile viewport recovers a release created while offline, replays each saved event five times plus reversed older events without writes/duplicate cards, preserves idempotent read and exact release/hash/acceptance deep link')

    before_freeze = get('/progress')
    session = page.context.new_cdp_session(page)
    session.send('Page.setWebLifecycleState', {'state':'frozen'})
    post('/requirements', {'requirement_key':'C26-frozen-resume','text':'Server changed during browser lifecycle freeze','basis':'USER_STATED',
        'source_refs':[],'rationale':'C26 browser freeze recovery','supersedes_id':None,'acceptance_check_ids':[]})
    after_freeze = get('/progress')
    session.send('Page.setWebLifecycleState', {'state':'active'})
    page.wait_for_function('(sequence) => document.querySelector(".progress-rail").textContent.includes("事件水位 " + sequence)', arg=after_freeze['as_of_event_sequence'])
    assert after_freeze['as_of_event_sequence'] > before_freeze['as_of_event_sequence']
    report['browser_freeze'] = {'transport':'Chromium Page.setWebLifecycleState frozen -> active',
        'sequence_before':before_freeze['as_of_event_sequence'],'sequence_after':after_freeze['as_of_event_sequence'],'physical_os_sleep':False}
    report['checks'].append('C26 actual Chromium page freeze/active resumes to server watermark after a real change during suspension; this is browser lifecycle evidence, not physical OS sleep')
    sidebar_chain(page, base, project_path, owner, report, out)


def sidebar_chain(page, base, project_path, token, report, out):
    expected = report['notification_contract']
    page.set_viewport_size({'width': 1440, 'height': 1000})
    login(page, base, project_path, token)
    rail = page.locator('.rail-release[href="' + project_path + '/releases/' + expected['release_id'] + '"]')
    rail.wait_for()
    rail.click()
    page.get_by_role('heading', name='C17 offline release', exact=True).wait_for()
    assert page.url == base + project_path + '/releases/' + expected['release_id']
    page.get_by_text('查看实际检查与命令', exact=True).click()
    page.locator('.raw-details pre').filter(has_text=expected['acceptance_id']).wait_for()
    assert expected['artifact_ref']['content_hash'] in page.locator('.artifact-preview').inner_text()
    page.get_by_role('button', name='受控预览').click()
    page.locator('.preview-text').get_by_text('"C18": 0', exact=False).wait_for()
    page.screenshot(path=str(out / 'sidebar-exact-chain.png'), full_page=True)
    report['screenshots'].append('sidebar-exact-chain.png')
    report['sidebar_chain'] = {'release_id': expected['release_id'], 'artifact_ref': expected['artifact_ref'],
        'acceptance_id': expected['acceptance_id'], 'clicked_actual_sidebar_link': True,
        'expanded_full_receipt': True, 'hash_checked_content_rendered': True}
    report['checks'].append('Actual sidebar release preserves the full release ID, artifact ref/hash, full acceptance ID and content from the offline notification deep link')
