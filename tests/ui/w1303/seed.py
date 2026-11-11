"""Seed a temporary W13 project through the real v1 API.

All execution observations are explicit FIXTURE inputs to the local W13 helper.
The returned object contains public record IDs and provenance, never credentials.
"""

import datetime as dt
import hashlib
import json
import subprocess
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def _now():
    return dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')


def _ref(value, kind):
    return {'entity_type': kind, 'id': value['id'], 'revision': value['revision'],
            'content_hash': value.get('content_hash')}


def _contract(expected):
    value = {'contract_revision': 1, 'checks': [{'check_id': 'json-result', 'kind': 'DETERMINISTIC',
        'required': True, 'expected': expected, 'command_key': 'orchestration.json-equals',
        'rubric_ref': None, 'qualification_id': None, 'not_applicable_reason': None}],
        'require_independent_verifier': True, 'version_policy': 'EXACT', 'frozen_at': _now()}
    packed = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    value['contract_hash'] = 'sha256:' + hashlib.sha256(packed).hexdigest()
    return value


def _experiment_contract():
    value = _contract('{"expected_case_ids":["fixture-case-1","fixture-case-2"]}')
    value['checks'][0]['command_key'] = 'experiments.paired-mean-v1'
    del value['contract_hash']
    packed = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    value['contract_hash'] = 'sha256:' + hashlib.sha256(packed).hexdigest()
    return value


def seed(base, owner_token, project_id, provision_binary, environment, root, out):
    """Create a reviewable fixture. ``out`` is reserved for the caller's captures."""
    prefix = '/v1/projects/' + project_id

    def api(token, method, path, body=None, etag=None):
        data = None if body is None else body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        headers = {'Authorization': 'Bearer ' + token, 'Accept': 'application/json'}
        if data is not None:
            headers['Content-Type'] = 'application/octet-stream' if isinstance(body, bytes) else 'application/json'
        if method != 'GET':
            headers['Idempotency-Key'] = uuid.uuid4().hex
        if etag is not None:
            headers['If-Match'] = '"r' + str(etag['revision']) + '"'
        try:
            with urlopen(Request(base + prefix + path, data=data, headers=headers, method=method), timeout=20) as response:
                return json.loads(response.read())
        except HTTPError as error:
            # API errors are safe to report; credentials and subprocess output are not.
            raise RuntimeError(f'{method} {path} returned HTTP {error.code}: {error.read()[:300]!r}') from error

    def get(path, token=owner_token):
        return api(token, 'GET', path)

    def post(path, body, subject=None, token=owner_token):
        return api(token, 'POST', path, body, subject or get('/state'))

    def provision(command=None, value=None):
        args = [str(provision_binary), project_id]
        if command:
            args.append(command)
        if command == 'runtime':
            args.append(value)
        done = subprocess.run(args, input=json.dumps(value) if command == 'observe' else None,
                              cwd=root, env=environment, text=True, capture_output=True, timeout=30)
        if done.returncode:
            raise RuntimeError(f'W13 provision {command or "principals"} failed (exit {done.returncode}); private diagnostic withheld')
        return json.loads(done.stdout) if not command else None

    credentials = provision()
    profile = get('/profile')
    requirement = post('/requirements', {'requirement_key': 'w1303-fixture-' + uuid.uuid4().hex,
        'text': 'Review an explicit local fixture from requirement to sealed release', 'basis': 'USER_STATED',
        'source_refs': [], 'rationale': 'W13-03 UI review fixture', 'supersedes_id': None,
        'acceptance_check_ids': []})
    requirement = post('/requirements/' + requirement['id'] + '/actions',
        {'action': 'ACCEPT', 'reason': 'explicit local fixture requirement', 'source_validation_refs': []}, requirement)
    expected = '{"result":"w1303-fixture"}'
    goal = post('/goals', {'title': 'W13-03 review fixture goal',
        'original_intent': 'Trace a local fixture through independent service acceptance',
        'scope': 'PROJECT', 'requirement_refs': [_ref(requirement, 'Requirement')],
        'problem_ids': ['w1303-fixture'], 'deliverables': ['Sealed JSON result'],
        'acceptance_contract': _contract(expected)})
    goal = post('/goals/' + goal['id'] + '/actions', {'action': 'ACTIVATE', 'reason': 'W13-03 fixture'}, goal)
    runtime = post('/runtimes', {'name': 'W13-03 explicit fixture observer', 'adapter': 'fixture',
        'adapter_revision': '1', 'capabilities': ['fixture'], 'platform': 'windows-amd64',
        'measurement_mode': 'FIXTURE', 'credential_ref': None})
    provision('runtime', runtime['id'])

    goal = get('/goals/' + goal['id'])
    task = post('/tasks', {'goal_id': goal['id'], 'title': 'Verify a sealed fixture JSON result',
        'task_type': 'json-verification', 'stage': 'verification', 'dependency_task_ids': [],
        'requirement_refs': [_ref(requirement, 'Requirement')], 'input_refs': [],
        'acceptance_contract': _contract(expected), 'origin_problem_id': 'w1303-fixture',
        'candidate_id': 'w1303-fixture-result', 'stop_policy': {'wall_time_seconds': 60,
            'max_attempts': 1, 'max_parallel_runs': 1, 'stop_conditions': ['fixture complete']}}, goal)
    state = get('/state')
    post('/context-bundles', {'task_id': task['id'], 'expected_project_state_revision': state['revision']},
         state, credentials['editor_token'])
    task = get('/tasks/' + task['id'])
    task = post('/tasks/' + task['id'] + '/actions', {'action': 'SUBMIT', 'reason': 'context frozen'}, task)
    claim = post('/tasks/' + task['id'] + '/claim', {'runtime_id': runtime['id'],
        'executor_principal_id': credentials['editor_id'], 'context_bundle_id': task['context_bundle_id']},
        task, credentials['scheduler_token'])
    run = claim['run']
    run = post('/runs/' + run['id'] + '/heartbeat', {'lease_token': claim['lease_token'],
        'lease_epoch': run['lease_epoch'], 'external_run_id': 'w1303-' + run['id'],
        'checkpoint_artifact_id': None}, run, credentials['editor_token'])
    payload = expected.encode()
    upload = api(credentials['editor_token'], 'POST', '/content', payload)
    artifact = post('/artifacts', {'run_id': run['id'], 'kind': 'REPORT', 'evidence_kind': 'GENERATED',
        'measurement_mode': 'FIXTURE', 'content_hash': upload['content_hash'],
        'storage_key': upload['storage_key'], 'media_type': 'application/json',
        'byte_size': len(payload), 'input_refs': [], 'source_refs': [],
        'produced_by': credentials['editor_id'], 'access_class': 'PROJECT'},
        token=credentials['editor_token'])
    provision('observe', {'spec': {'run_id': run['id'], 'task_id': task['id'], 'epoch': run['lease_epoch']},
        'state': 'SETTLED', 'children_stopped': True, 'queue_empty': True, 'exit_code': 0,
        'ended': _now(), 'protocol': {'settled': True},
        'artifacts': [{'path': 'result.json', 'content_hash': artifact['content_hash'],
                       'byte_size': artifact['byte_size']}]})
    post('/runs/' + run['id'] + '/report', {'lease_token': claim['lease_token'],
        'lease_epoch': run['lease_epoch'], 'runtime_settled': True,
        'execution_report': 'Explicit fixture result submitted for independent service check',
        'exit_code': 0, 'result_artifact_ids': [artifact['id']],
        'checkpoint_artifact_id': None}, run, credentials['editor_token'])
    task = get('/tasks/' + task['id'])
    if task['status'] != 'EXECUTION_REPORTED':
        raise RuntimeError('Task did not reach EXECUTION_REPORTED before independent acceptance')
    receipt = post('/acceptances', {'subject_ref': _ref(task, 'Task'), 'run_id': run['id'],
        'contract_hash': task['acceptance_contract']['contract_hash'], 'input_refs': task['input_refs'],
        'artifact_refs': [_ref(artifact, 'Artifact')], 'checks': [{'check_id': 'json-result',
            'status': 'NOT_RUN', 'evidence_refs': [], 'command_key': 'orchestration.json-equals',
            'actual': 'Request independent server computation', 'exit_code': None,
            'started_at': None, 'finished_at': None}], 'verdict': 'PASS',
        'executor_principal_ids': [credentials['editor_id']], 'independence_basis': 'DETERMINISTIC_SERVICE',
        'blocking_conflict_ids': [], 'qualification_ids': [],
        'policy_revision': get('/state')['policy_revision'], 'measurement_mode': 'FIXTURE',
        'reason': 'Independent service verifies frozen fixture JSON'}, task, credentials['verifier_token'])
    if receipt['verdict'] != 'PASS' or get('/tasks/' + task['id'])['status'] != 'ACCEPTED':
        raise RuntimeError('Independent service did not accept the fixture Task')
    release = post('/releases', {'scope': 'PROJECT', 'software_version': None,
        'summary': 'W13-03 sealed fixture release', 'changes': ['Independent JSON check passed'],
        'decision_ids': [], 'artifact_refs': [_ref(artifact, 'Artifact')],
        'acceptance_ids': [receipt['id']], 'open_issues': ['Local fixture only; no live qualification'],
        'next_steps': ['Review W13-03 screens'], 'policy_revision': get('/state')['policy_revision'],
        'supersedes_id': None}, token=credentials['scheduler_token'])

    # A separate READY task lets the task detail show the next actionable state.
    goal = get('/goals/' + goal['id'])
    ready_task = post('/tasks', {'goal_id': goal['id'], 'title': 'Review next fixture decision',
        'task_type': 'json-verification', 'stage': 'review', 'dependency_task_ids': [],
        'requirement_refs': [_ref(requirement, 'Requirement')], 'input_refs': [],
        'acceptance_contract': _contract('{"result":"pending-review"}'),
        'origin_problem_id': 'w1303-fixture', 'candidate_id': 'w1303-next-review',
        'stop_policy': {'wall_time_seconds': 60, 'max_attempts': 1,
                        'max_parallel_runs': 1, 'stop_conditions': ['fixture only']}}, goal)
    state = get('/state')
    post('/context-bundles', {'task_id': ready_task['id'],
        'expected_project_state_revision': state['revision']}, state, credentials['editor_token'])
    ready_task = get('/tasks/' + ready_task['id'])
    ready_task = post('/tasks/' + ready_task['id'] + '/actions',
        {'action': 'SUBMIT', 'reason': 'context frozen'}, ready_task)

    window_to = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1)
    cycle = post('/research-cycles', {'trigger': 'SCHEDULE',
        'window_from': (window_to - dt.timedelta(days=7)).isoformat().replace('+00:00', 'Z'),
        'window_to': window_to.isoformat().replace('+00:00', 'Z'),
        'profile_revision': profile['revision']})
    checkpoint_bytes = b'{"fixture":"w1303-cycle","coverage":"no external sources queried"}'
    checkpoint_upload = api(credentials['editor_token'], 'POST', '/content', checkpoint_bytes)
    checkpoint = post('/artifacts', {'run_id': None, 'kind': 'REPORT',
        'evidence_kind': 'GENERATED', 'measurement_mode': 'FIXTURE',
        'content_hash': checkpoint_upload['content_hash'],
        'storage_key': checkpoint_upload['storage_key'], 'media_type': 'application/json',
        'byte_size': len(checkpoint_bytes), 'input_refs': [], 'source_refs': [],
        'produced_by': credentials['editor_id'], 'access_class': 'PROJECT'},
        token=credentials['editor_token'])
    cycle = post('/research-cycles/' + cycle['id'] + '/checkpoint',
        {'source_coverage': cycle['source_coverage'], 'candidate_evidence_ids': [],
         'required_experiment_ids': [], 'decision_ids': [], 'follow_up_task_ids': [],
         'checkpoint_artifact_id': checkpoint['id']}, cycle, credentials['scheduler_token'])
    # This project has no configured external sources. Keep the checkpointed
    # cycle RUNNING instead of claiming a completed source investigation.

    source = b'{"fixture":"w1303-source","provenance":"simulated"}'
    upload = api(credentials['token'], 'POST', '/content', source)
    source_artifact = post('/artifacts', {'run_id': None, 'kind': 'SOURCE_SNAPSHOT',
        'evidence_kind': 'SIMULATED', 'measurement_mode': 'FIXTURE',
        'content_hash': upload['content_hash'], 'storage_key': upload['storage_key'],
        'media_type': 'application/json', 'byte_size': len(source), 'input_refs': [],
        'source_refs': [], 'produced_by': credentials['principal_id'], 'access_class': 'PROJECT'},
        token=credentials['token'])
    # Seal a source-attributed SKILL document. This remains an unqualified
    # CANDIDATE: the source is simulated, rights are unknown, and no skill
    # acceptance, activation, or execution is part of this UI fixture.
    source_ref = _ref(source_artifact, 'Artifact')
    skill_document = {'format': 'researchos.skill.v1',
        'project_state': 'CURRENT_PROJECTION',
        'inputs': ['current project state', 'simulated source snapshot'],
        'outputs': ['attributed fixture research note'],
        'applicable_tasks': ['fixture research review'],
        'limitations': ['W13-03 simulated source only; no external research or qualification'],
        'side_effects': [],
        'claims': [{'text': 'This W13-03 source is simulated fixture data.',
                    'locator': 'provenance', 'source_ref': source_ref}],
        'conflicts': [],
        'extraction': [{'source_id': source_artifact['id'], 'processed': True, 'failure': ''}],
        'suite_case_ids': ['w1303-fixture-case'],
        'negative_case_ids': ['w1303-fixture-negative']}
    skill_bytes = json.dumps(skill_document, ensure_ascii=False, separators=(',', ':')).encode()
    skill_upload = api(credentials['editor_token'], 'POST', '/content', skill_bytes)
    skill_artifact = post('/artifacts', {'run_id': None, 'kind': 'SKILL',
        'evidence_kind': 'GENERATED', 'measurement_mode': 'FIXTURE',
        'content_hash': skill_upload['content_hash'], 'storage_key': skill_upload['storage_key'],
        'media_type': 'application/json', 'byte_size': len(skill_bytes),
        'input_refs': [source_ref], 'source_refs': [],
        'produced_by': credentials['editor_id'], 'access_class': 'PROJECT'},
        token=credentials['editor_token'])
    skill = post('/skills', {'skill_name': 'w1303-fixture-research-note',
        'version': '0.1.0-fixture', 'scope': 'PROJECT',
        'content_artifact_ref': _ref(skill_artifact, 'Artifact'),
        'source_refs': [source_ref], 'expected_source_ids': [source_artifact['id']],
        'processed_source_ids': [source_artifact['id']], 'failed_source_ids': [],
        'conflict_ids': [], 'license_expression': None,
        'required_variables': [], 'allowed_capabilities': [],
        'baseline_skill_id': None, 'experiment_id': None},
        token=credentials['editor_token'])
    if skill['status'] != 'CANDIDATE':
        raise RuntimeError('Fixture SkillVersion did not remain CANDIDATE')
    evidence = post('/evidence', {'claim': 'W13-03 simulated source snapshot', 'stance': 'CONTEXT',
        'evidence_kind': 'SIMULATED', 'source_kind': 'SIMULATION', 'canonical_url': None,
        'publisher': None, 'upstream_revision': None, 'published_at': None, 'modified_at': None,
        'retrieved_at': _now(), 'time_status': 'UNKNOWN',
        'snapshot_artifact_ref': _ref(source_artifact, 'Artifact'), 'locator': 'body',
        'independence_key': 'sha256:' + hashlib.sha256(source).hexdigest(),
        'origin_evidence_id': None, 'discovery_urls': [], 'license_status': 'UNKNOWN',
        'license_expression': None}, token=credentials['token'])
    experiment = post('/experiments', {'cycle_id': None, 'scope': 'PROJECT',
        'hypothesis': 'Fixture comparison remains a draft until evaluated',
        'candidate_ref': _ref(artifact, 'Artifact'), 'baseline_refs': [_ref(source_artifact, 'Artifact')],
        'input_refs': [_ref(source_artifact, 'Artifact')],
        'metrics': [{'metric_id': 'quality', 'description': 'Frozen fixture metric', 'unit': 'score',
            'operator': 'GTE', 'target': '1', 'upper_target': None, 'mandatory': True}],
        'acceptance_contract': _experiment_contract(),
        'stop_policy': {'wall_time_seconds': 60, 'max_attempts': 1, 'max_parallel_runs': 1,
                        'stop_conditions': ['fixture limit']},
        'budget_policy_id': profile['budget_policy_id'], 'measurement_mode': 'FIXTURE'},
        token=credentials['editor_token'])
    policy = get('/budget-policy')
    run_policy = get('/run-policy')
    runtime = get('/runtimes/' + runtime['id'])
    state = get('/state')
    return {
        'project_id': project_id,
        'objects': {'requirement': requirement['id'], 'goal': goal['id'], 'task': task['id'],
                'ready_task': ready_task['id'],
                'run': run['id'], 'runtime': runtime['id'], 'artifact': artifact['id'],
                'source_artifact': source_artifact['id'], 'skill_artifact': skill_artifact['id'],
                'skill': skill['id'], 'checkpoint_artifact': checkpoint['id'],
                'evidence': evidence['id'],
                'acceptance': receipt['id'], 'release': release['id'], 'cycle': cycle['id'],
                'experiment': experiment['id']},
        'routes': {'S00': '/', 'S01': '/p/' + project_id,
                   'S02': '/p/' + project_id + '/cycles/' + cycle['id'],
                   'S03': '/p/' + project_id + '/tasks/' + ready_task['id'],
                   'S04': '/p/' + project_id + '/releases/' + release['id'],
                   'S05': '/p/' + project_id + '/evidence',
                   'S06': '/p/' + project_id + '/experiments/' + experiment['id'],
                   'S07': '/p/' + project_id + '/knowledge',
                   'S08': '/p/' + project_id + '/team',
                   'S09': '/p/' + project_id + '/resources',
                   'S10': '/p/' + project_id + '/settings'},
        'service_evidence': {'task_status': get('/tasks/' + task['id'])['status'],
                             'acceptance_verdict': receipt['verdict'],
                             'release_sequence': release['sequence'],
                             'cycle_status': cycle['status'],
                             'experiment_status': experiment['status'],
                             'skill_status': skill['status'],
                             'runtime_status': runtime['status'],
                             'project_state_revision': state['revision'],
                             'budget_policy_id': policy['id'],
                             'run_policy_id': run_policy['id']},
        'provenance': ['Records persisted through real API into temporary SQLite',
                       'Runtime observation supplied by explicit local FIXTURE helper, not an OS process',
                       'Source snapshot is SIMULATED; no external source was queried',
                       'SkillVersion remains CANDIDATE with unknown source rights; no qualification or activation',
                       'Experiment remains DRAFT; no evaluation or holdout ran',
                       'Task acceptance was independently recomputed by the service over FIXTURE bytes',
                       'Release is sealed from the FIXTURE task receipt; no live qualification or paid call']}
