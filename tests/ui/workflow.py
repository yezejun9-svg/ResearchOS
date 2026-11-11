"""Populated W13 UI workflows over real APIs, with explicit FIXTURE runtime observations."""
import datetime
import hashlib
import json
import subprocess
import uuid

from scenarios import login, ref, responsive_screen


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')


def contract(expected):
    value = {'contract_revision': 1, 'checks': [{'check_id': 'json-result', 'kind': 'DETERMINISTIC', 'required': True,
             'expected': expected, 'command_key': 'orchestration.json-equals', 'rubric_ref': None, 'qualification_id': None, 'not_applicable_reason': None}],
             'require_independent_verifier': True, 'version_policy': 'EXACT', 'frozen_at': now()}
    value['contract_hash'] = 'sha256:' + hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    return value


def populated_workflow(page, base, project_path, owner, credentials, api, binary, environment, root, report, out):
    project_id = project_path.rsplit('/', 1)[1]
    prefix = project_path.replace('/p/', '/v1/projects/')

    def get(path):
        return api(base, owner, 'GET', prefix + path)

    def post(path, body, subject=None, token=None):
        return api(base, token or owner, 'POST', prefix + path, body, f'"r{(subject or get("/state"))["revision"]}"')

    def provision(command, value=None):
        args = [str(binary), project_id, command]
        if command == 'runtime':
            args.append(value)
        done = subprocess.run(args, input=json.dumps(value) if command != 'runtime' else None, cwd=root, env=environment,
                              text=True, capture_output=True, timeout=30)
        assert done.returncode == 0, done.stderr

    requirement = post('/requirements', {'requirement_key': 'ui-flow-' + uuid.uuid4().hex, 'text': 'Verify real populated UI transitions',
        'basis': 'USER_STATED', 'source_refs': [], 'rationale': 'W13 browser contract', 'supersedes_id': None, 'acceptance_check_ids': []})
    requirement = post('/requirements/' + requirement['id'] + '/actions', {'action': 'ACCEPT', 'reason': 'explicit fixture requirement', 'source_validation_refs': []}, requirement)
    frozen = contract('{"result":"verified"}')
    goal = post('/goals', {'title': 'Populated browser workflow', 'original_intent': 'Distinguish reported and accepted results',
        'scope': 'PROJECT', 'requirement_refs': [ref(requirement, 'Requirement')], 'problem_ids': ['w13-populated'],
        'deliverables': ['Independent checked JSON'], 'acceptance_contract': frozen})
    goal = post('/goals/' + goal['id'] + '/actions', {'action': 'ACTIVATE', 'reason': 'W13 development workflow'}, goal)
    runtime = post('/runtimes', {'name': 'W13 explicit fixture observer', 'adapter': 'fixture', 'adapter_revision': '1',
        'capabilities': ['fixture'], 'platform': 'windows-amd64', 'measurement_mode': 'FIXTURE', 'credential_ref': None})
    provision('runtime', runtime['id'])

    def task(title, expected):
        current_goal = get('/goals/' + goal['id'])
        created = post('/tasks', {'goal_id': goal['id'], 'title': title, 'task_type': 'json-verification', 'stage': 'verification',
            'dependency_task_ids': [], 'requirement_refs': [ref(requirement, 'Requirement')], 'input_refs': [],
            'acceptance_contract': contract(expected), 'origin_problem_id': 'w13-populated', 'candidate_id': title.replace(' ', '-'),
            'stop_policy': {'wall_time_seconds': 60, 'max_attempts': 3, 'max_parallel_runs': 1, 'stop_conditions': ['no progress']}}, current_goal)
        state = get('/state')
        post('/context-bundles', {'task_id': created['id'], 'expected_project_state_revision': state['revision']}, state, credentials['editor_token'])
        current = get('/tasks/' + created['id'])
        return post('/tasks/' + current['id'] + '/actions', {'action': 'SUBMIT', 'reason': 'context frozen'}, current)

    def claim(current):
        response = post('/tasks/' + current['id'] + '/claim', {'runtime_id': runtime['id'], 'executor_principal_id': credentials['editor_id'],
            'context_bundle_id': current['context_bundle_id']}, current, credentials['scheduler_token'])
        run = response['run']
        run = post('/runs/' + run['id'] + '/heartbeat', {'lease_token': response['lease_token'], 'lease_epoch': run['lease_epoch'],
            'external_run_id': 'qualified-' + run['id'], 'checkpoint_artifact_id': None}, run, credentials['editor_token'])
        return response['task'], run, response['lease_token']

    def artifact_for_run(run, text):
        raw = text.encode()
        upload = api(base, credentials['editor_token'], 'POST', prefix + '/content', raw)
        return post('/artifacts', {'run_id': run['id'], 'kind': 'REPORT', 'evidence_kind': 'GENERATED', 'measurement_mode': 'FIXTURE',
            'content_hash': upload['content_hash'], 'storage_key': upload['storage_key'], 'media_type': 'application/json',
            'byte_size': len(raw), 'input_refs': [], 'source_refs': [], 'produced_by': credentials['editor_id'], 'access_class': 'PROJECT'}, token=credentials['editor_token'])

    if report.get('phase') in ('plan', 'contracts', 'recovery'):
        from contract_cases import exact_plan_case
        exact_plan_case(page, base, project_path, owner, credentials, get, post, provision, task, claim, artifact_for_run, report, out)
        return

    initial_progress = get('/progress')
    ready = task('Browser pause resume cancel', '{"result":"verified"}')
    login(page, base, project_path + '/tasks/' + ready['id'], owner)
    page.get_by_role('tab', name='摘要').focus()
    page.keyboard.press('ArrowRight')
    assert page.get_by_role('tab', name='过程').get_attribute('aria-selected') == 'true'
    page.keyboard.press('End')
    assert page.get_by_role('tab', name='检查').get_attribute('aria-selected') == 'true'
    page.keyboard.press('Home')
    page.get_by_role('button', name='暂停', exact=True).click()
    page.get_by_role('button', name='恢复', exact=True).wait_for()
    assert get('/tasks/' + ready['id'])['status'] == 'BLOCKED'
    page.get_by_role('button', name='恢复', exact=True).click()
    page.get_by_role('button', name='暂停', exact=True).wait_for()
    ready = get('/tasks/' + ready['id'])
    assert ready['status'] == 'READY'
    current, run, lease = claim(ready)
    page.get_by_text('运行中', exact=True).wait_for()
    with page.expect_response(lambda response: response.url.endswith('/runs/' + run['id'] + '/cancel')) as cancel_response:
        page.get_by_role('button', name='请求取消').click()
    assert cancel_response.value.status == 200, cancel_response.value.text()
    page.get_by_text('取消已请求，执行器尚未确认。').wait_for()
    run = get('/runs/' + run['id'])
    assert run['status'] == 'CANCEL_REQUESTED' and run['cancel_confirmed_at'] is None
    page.screenshot(path=str(out / 'task-cancel-waiting.png'), full_page=True)
    report['screenshots'].append('task-cancel-waiting.png')
    observation = {'spec': {'run_id': run['id'], 'task_id': current['id'], 'epoch': run['lease_epoch']}, 'state': 'CANCELLED',
                   'children_stopped': True, 'queue_empty': True, 'exit_code': 0, 'ended': now(), 'protocol': {'settled': True}}
    provision('observe', observation)
    artifact = artifact_for_run(run, json.dumps(observation, separators=(',', ':')))
    post('/runs/' + run['id'] + '/cancel-ack', {'lease_token': lease, 'lease_epoch': run['lease_epoch'],
        'children_stopped': True, 'queue_empty': True, 'receipt_artifact_ref': ref(artifact, 'Artifact')}, run, credentials['editor_token'])
    page.get_by_text('已取消', exact=True).first.wait_for()
    report['checks'].append('Real UI pause/resume updates Task BLOCKED/READY; cancel stays CANCEL_REQUESTED until separately observed fixture cancellation is acknowledged')

    replay_baseline = get('/progress')
    releases = []
    for version in (1, 2):
        text = json.dumps({'result': 'verified', 'version': version}, separators=(',', ':'))
        current, run, lease = claim(task('Browser independent result ' + str(version), text))
        artifact = artifact_for_run(run, text)
        provision('observe', {'spec': {'run_id': run['id'], 'task_id': current['id'], 'epoch': run['lease_epoch']}, 'state': 'SETTLED',
            'children_stopped': True, 'queue_empty': True, 'exit_code': 0, 'ended': now(), 'protocol': {'settled': True},
            'artifacts': [{'path': 'result.json', 'content_hash': artifact['content_hash'], 'byte_size': artifact['byte_size']}]})
        post('/runs/' + run['id'] + '/report', {'lease_token': lease, 'lease_epoch': run['lease_epoch'], 'runtime_settled': True,
            'execution_report': 'Result submitted, independent acceptance still required', 'exit_code': 0,
            'result_artifact_ids': [artifact['id']], 'checkpoint_artifact_id': None}, run, credentials['editor_token'])
        current = get('/tasks/' + current['id'])
        assert current['status'] == 'EXECUTION_REPORTED'
        login(page, base, project_path + '/tasks/' + current['id'], owner)
        page.get_by_text('执行结果已经提交，仍需独立验收。').wait_for()
        page.get_by_text('Result submitted, independent acceptance still required', exact=True).wait_for()
        if version == 1:
            page.screenshot(path=str(out / 'task-awaiting-review.png'), full_page=True)
            report['screenshots'].append('task-awaiting-review.png')
        frozen = current['acceptance_contract']
        receipt = post('/acceptances', {'subject_ref': ref(current, 'Task'), 'run_id': run['id'], 'contract_hash': frozen['contract_hash'],
            'input_refs': current['input_refs'], 'artifact_refs': [ref(artifact, 'Artifact')],
            'checks': [{'check_id': 'json-result', 'status': 'NOT_RUN', 'evidence_refs': [], 'command_key': 'orchestration.json-equals',
                        'actual': 'Request independent server computation', 'exit_code': None, 'started_at': None, 'finished_at': None}],
            'verdict': 'PASS', 'executor_principal_ids': [credentials['editor_id']], 'independence_basis': 'DETERMINISTIC_SERVICE',
            'blocking_conflict_ids': [], 'qualification_ids': [], 'policy_revision': get('/state')['policy_revision'],
            'measurement_mode': 'FIXTURE', 'reason': 'Independent server JSON equality check'}, current, credentials['verifier_token'])
        assert receipt['verdict'] == 'PASS', receipt
        page.get_by_text('独立验收已通过。').wait_for()
        release = post('/releases', {'scope': 'PROJECT', 'software_version': None, 'summary': 'Browser release ' + str(version),
            'changes': ['Independent JSON check passed'], 'decision_ids': [], 'artifact_refs': [ref(artifact, 'Artifact')],
            'acceptance_ids': [receipt['id']], 'open_issues': ['Development fixture, no live qualification'],
            'next_steps': ['Independent W13 review'], 'policy_revision': get('/state')['policy_revision'], 'supersedes_id': None}, token=credentials['scheduler_token'])
        releases.append(release)
    report['checks'].append('Real submitted Task stays EXECUTION_REPORTED; independent service checks change it to ACCEPTED and create two distinct sealed milestone releases')
    login(page, base, project_path + '/releases/' + releases[-1]['id'], owner)
    for index in (1, 0, 1):
        page.get_by_label('选择成果版本').select_option(releases[index]['id'])
        page.get_by_role('heading', name='Browser release ' + str(index + 1), exact=True).wait_for()
        page.get_by_role('button', name='受控预览').click()
        page.locator('.preview-text').get_by_text('"version": ' + str(index + 1), exact=False).wait_for()
        assert releases[index]['artifact_refs'][0]['content_hash'] in page.locator('.artifact-preview').inner_text()
    responsive_screen(page, 'release-populated', report, out)
    notices = get('/notifications')['items']
    assert len(notices) == 2 and len({(n['release_id'], n['recipient_id'], n['channel']) for n in notices}) == 2
    page.get_by_role('button', name='打开通知，2 条未读').click()
    assert page.locator('.notice-row').count() == 2
    page.get_by_role('button', name='标记已读').first.click()
    page.get_by_text('已读', exact=True).wait_for()
    page.keyboard.press('Escape')
    assert page.get_by_role('button', name='打开通知，1 条未读').is_visible()
    report['checks'].append('Release version switch 2→1→2 loads exact distinct sealed hashes; two actual release notifications render once each and mark-read persists')
    report['populated_workflow'] = {'release_ids': [r['id'] for r in releases], 'notification_ids': [n['id'] for n in notices], 'runtime_mode': 'FIXTURE', 'runtime_observation_source': 'explicit local Service.ObserveRuntime helper, not an OS process'}

    current_progress = get('/progress')
    initial_planned = sum(stage['planned'] for stage in initial_progress['stages'])
    current_planned = sum(stage['planned'] for stage in current_progress['stages'])
    assert current_planned == initial_planned + 3, (initial_progress, current_progress)
    assert current_progress['plan_revision'] > initial_progress['plan_revision']
    for stage in current_progress['stages']:
        label = {'discovery': '发现', 'verification': '核验', 'experiment': '实验', 'review': '评审', 'delivery': '交付', 'follow_up': '跟踪'}[stage['stage']]
        row = page.locator('.stage-list li').filter(has=page.locator('.stage-title', has_text=label))
        assert row.locator('.stage-count').inner_text() == f"{stage['accepted']} / {stage['planned']} 已验收"
    assert current_progress['plan_change_note'] in page.locator('.progress-rail').inner_text()
    events = [e for e in get('/events')['items'] if e['sequence'] > replay_baseline['as_of_event_sequence']]
    assert any(e.get('aggregate_ref', {}).get('id') in [r['id'] for r in releases] for e in events)
    before_ids = sorted(n['id'] for n in get('/notifications')['items'])
    progress_reads, stream_requests, writes = [], [], []
    def snapshot(route):
        progress_reads.append(route.request.url)
        if len(progress_reads) <= 2:
            route.fulfill(status=200, content_type='application/json', body=json.dumps(replay_baseline))
        else:
            route.continue_()
    def replay(route):
        stream_requests.append(route.request.headers.get('last-event-id'))
        if len(stream_requests) == 1:
            body = ''.join('data: ' + json.dumps(e) + '\n\n' for e in events for _ in range(2))
            route.fulfill(status=200, content_type='text/event-stream', body=body)
        else:
            route.continue_()
    def record(request):
        if prefix in request.url and request.method != 'GET':
            writes.append(request.method + ' ' + request.url)
    page.route('**' + prefix + '/progress', snapshot)
    page.route('**' + prefix + '/events/stream', replay)
    page.on('request', record)
    login(page, base, project_path, owner)
    page.get_by_role('button', name='打开通知，1 条未读').wait_for()
    page.wait_for_timeout(2500)
    page.get_by_role('button', name='打开通知，1 条未读').click()
    assert page.locator('.notice-row').count() == 2
    assert sorted(n['id'] for n in get('/notifications')['items']) == before_ids
    assert not writes, writes
    assert stream_requests[0] == str(replay_baseline['as_of_event_sequence']), stream_requests
    assert len(stream_requests) >= 2, stream_requests
    page.screenshot(path=str(out / 'notification-release-replay.png'), full_page=True)
    report['screenshots'].append('notification-release-replay.png')
    page.unroute('**' + prefix + '/progress', snapshot)
    page.unroute('**' + prefix + '/events/stream', replay)
    page.remove_listener('request', record)
    report['notification_replay'] = {'transport': 'real saved project events replayed twice each through controlled SSE transport',
        'last_event_ids': stream_requests, 'notification_ids_before': before_ids, 'notification_ids_after': before_ids,
        'writes_from_replay': writes, 'plan_revision_before': initial_progress['plan_revision'], 'plan_revision_after': current_progress['plan_revision'],
        'planned_before': initial_planned, 'planned_after': current_planned, 'plan_change_note': current_progress['plan_change_note']}
    report['checks'].append('Real plan mutation updates planned count, revision and reason; replay of actual release events twice preserves notification IDs, unread count and creates no write requests')
