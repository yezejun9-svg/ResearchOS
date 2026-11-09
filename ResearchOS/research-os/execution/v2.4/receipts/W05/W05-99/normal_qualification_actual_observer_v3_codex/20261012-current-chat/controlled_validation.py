"""Controlled C-only validation, with no access to the original database."""
import datetime
import hashlib
import importlib.util
import json
import pathlib
import sqlite3
import subprocess

OUT = pathlib.Path(__file__).parent
SOURCE = OUT / 'observe.py'
spec = importlib.util.spec_from_file_location('observer_v3', SOURCE)
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)
observer.PROJECT, observer.SESSION, observer.OWNER = 'fixture-project', 'fixture-session', 'fixture-owner'

request = dict(request_id='fixture-request', project_id=observer.PROJECT,
    session_id=observer.SESSION, model_config_ref='fixture-config', runtime_id='fixture-runtime',
    task_id='fixture-task', plan_hash='sha256:' + 'a' * 64, profile_hash='sha256:' + 'b' * 64,
    authorize_purpose='mu_turn', purpose_seconds=60, owner_host='fixture-host',
    owner_principal=observer.OWNER, owner_root=observer.OWNER,
    session_hash='sha256:' + 'c' * 64, configuration_hash='sha256:' + 'd' * 64,
    issued_at='2026-10-12T00:00:00Z', expires_at='2026-10-12T00:01:00Z')

canonical_checks = []
for label, changes in [('ascii', {}), ('unicode', {'owner_host': '主机\u2028路径😀'}),
                       ('escaped', {'owner_host': 'host<>&"\\\n'})]:
    candidate = {**request, **changes}
    raw = json.dumps(candidate, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    process = subprocess.run([str(OUT / 'go-jcs-oracle/jcs-oracle.exe')], input=raw,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.returncode == 0
    go_digest = process.stdout.decode('utf-8').strip()
    python_digest = observer.qualification_request_digest(candidate)
    assert python_digest == go_digest
    canonical_checks.append({'case': label, 'actual_go_digest': go_digest,
                             'scalar_subset_digest_matches': True, 'exit_code': process.returncode})

cases = []
for label in ['blob-preconfirm', 'text-preconfirm', 'blob-consumed-paused', 'wrong-run-id',
              'wrong-ref-type', 'wrong-profile', 'missing-run', 'wrong-epoch', 'wrong-goal-budget']:
    database = OUT / (label + '.sqlite')
    assert not database.exists()
    with sqlite3.connect(database) as connection:
        connection.executescript('''
        CREATE TABLE client_sessions(id,project_id,revision,writer_epoch,writer_client_id,
          lease_expires_at,workspace_ref,model_config_ref,core_build_id,sealed_at,archived_at);
        CREATE TABLE runtime_qualification_plans(project,task,runtime,plan,plan_hash,author,author_root);
        CREATE TABLE domain_objects(project,kind,id,revision,body);
        CREATE TABLE runtime_qualification_runs(project,task,run,runtime,epoch,plan_hash,profile_hash,
          contract_hash,input_hash,context_bundle,owner_root);
        CREATE TABLE runtime_dispatches(project,run,epoch,dispatch_key,manifest_hash,manifest,state,
          worker,journal_locator,identity,observation_sequence,observation_hash);
        CREATE TABLE resource_effects(project,run,effect_key,sequence,body);
        CREATE TABLE idempotency(principal,project,operation,key,request_hash,body,created_at);
        ''')
        connection.execute('INSERT INTO client_sessions VALUES(?,?,?,?,?,?,?,?,?,?,?)',
            (observer.SESSION, observer.PROJECT, 1, 1, 'fixture-client', '2027-01-01T00:00:00Z',
             'fixture-workspace', request['model_config_ref'], 'fixture-build', None, None))
        policies = [('GLOBAL', '', 'global', None, None),
                    ('PROJECT', observer.PROJECT, observer.PROJECT, observer.PROJECT, 'fixture-GLOBAL'),
                    ('GOAL', observer.PROJECT, 'fixture-goal', observer.PROJECT, 'fixture-PROJECT')]
        for scope, project_column, scope_id, policy_project, parent in policies:
            if label == 'wrong-goal-budget' and scope == 'GOAL':
                scope_id = 'another-goal'
            body = dict(id='fixture-' + scope, scope_type=scope, scope_id=scope_id,
                project_id=policy_project, parent_policy_id=parent, effective_from='2026-01-01T00:00:00Z',
                mode='UNLIMITED_AMOUNT', cap=None, enforcement='ACCOUNTING_ONLY',
                unknown_cost_action='ALLOW_AND_RECORD')
            connection.execute('INSERT INTO domain_objects VALUES(?,?,?,?,?)',
                (project_column, 'BudgetPolicy', body['id'], 1, json.dumps(body)))
        consumed = label not in ['blob-preconfirm', 'text-preconfirm', 'wrong-goal-budget']
        task = dict(id=request['task_id'], project_id=observer.PROJECT, goal_id='fixture-goal',
            active_run_id='fixture-run' if consumed else None)
        connection.execute('INSERT INTO domain_objects VALUES(?,?,?,?,?)',
            (observer.PROJECT, 'Task', task['id'], 1, json.dumps(task).encode()))
        goal = dict(id='fixture-goal', project_id=observer.PROJECT, budget_policy_id='fixture-GOAL',
            status='PAUSED' if consumed else 'ACTIVE')
        connection.execute('INSERT INTO domain_objects VALUES(?,?,?,?,?)',
            (observer.PROJECT, 'Goal', goal['id'], 1, json.dumps(goal)))
        raw_request = json.dumps(request, separators=(',', ':')).encode()
        digest = observer.qualification_request_digest(request)
        connection.execute('INSERT INTO idempotency VALUES(?,?,?,?,?,?,?)',
            (observer.OWNER, observer.PROJECT, 'host:qualification-confirmation', request['request_id'],
             digest, raw_request.decode() if label == 'text-preconfirm' else raw_request,
             '2026-10-12T00:00:00Z'))
        if consumed:
            consume = dict(request_hash=digest, task_id=request['task_id'], runtime_id=request['runtime_id'],
                run_ref=dict(entity_type='Task' if label == 'wrong-ref-type' else 'Run',
                    id='fixture-run', revision=1, content_hash=None))
            connection.execute('INSERT INTO idempotency VALUES(?,?,?,?,?,?,?)',
                (observer.OWNER, observer.PROJECT, 'host:managed-runtime-qualification',
                 request['request_id'], digest, json.dumps(consume).encode(), '2026-10-12T00:00:10Z'))
            connection.execute('INSERT INTO runtime_qualification_runs VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                (observer.PROJECT, request['task_id'], 'fixture-run', request['runtime_id'], 3,
                 request['plan_hash'], 'sha256:' + 'e' * 64 if label == 'wrong-profile' else request['profile_hash'],
                 'fixture-contract', 'fixture-input', 'fixture-context', observer.OWNER))
            if label != 'missing-run':
                run = dict(id='fixture-run', project_id=observer.PROJECT, task_id=request['task_id'],
                    runtime_id=request['runtime_id'], lease_epoch=4 if label == 'wrong-epoch' else 3,
                    context_bundle_id='fixture-context', lease_token_hash='EXCLUDED_FIXTURE_SECRET_HASH',
                    status='SETTLED')
                connection.execute('INSERT INTO domain_objects VALUES(?,?,?,?,?)',
                    (observer.PROJECT, 'Run', run['id'], 2, json.dumps(run)))
    before = hashlib.sha256(database.read_bytes()).hexdigest()
    observer.DATABASE = database
    assert observer.DATABASE.parent == OUT and observer.DATABASE.drive.upper() == 'C:'
    error = None
    result = None
    try:
        result = observer.observe(request['request_id'],
            'another-run' if label == 'wrong-run-id' else 'fixture-run' if consumed else None)
    except AssertionError as exception:
        error = str(exception)
    expected_success = label in ['blob-preconfirm', 'text-preconfirm', 'blob-consumed-paused']
    assert (error is None) == expected_success, (label, error)
    if expected_success:
        assert result['original_request_hash_matches_canonical_request']
        assert result['original_task_goal_budget_binding_validated']
        if consumed:
            assert result['original_request_consume_run_task_binding_validated']
            assert 'lease_token_hash' not in json.loads(result['run'][0]['safe_body'])
        (OUT / (label + '.observed.json')).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    unchanged = before == hashlib.sha256(database.read_bytes()).hexdigest()
    assert unchanged
    cases.append({'case': label, 'accepted_valid_observation': error is None,
                  'expected_success': expected_success, 'rejection': error,
                  'fixture_database_unchanged': unchanged})

report = {'schema': 'researchos.observer-v3-controlled-validation/1',
    'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'canonical_oracle': canonical_checks, 'cases': cases, 'all_expected_outcomes': True,
    'original_database_opened': False, 'real_model_or_tool_requests': 0, 'D_mutations': 0,
    'formal_increment': 0}
target = OUT / 'controlled-validation-result.json'
assert not target.exists()
target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
