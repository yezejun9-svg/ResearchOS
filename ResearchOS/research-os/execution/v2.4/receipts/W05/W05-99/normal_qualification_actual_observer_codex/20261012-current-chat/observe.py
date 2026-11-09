"""Read-only, bounded evidence observer for the preserved normal desktop session."""
import argparse
import datetime
import hashlib
import json
import pathlib
import sqlite3

ROOT = pathlib.Path('D:/作品集/ResearchOS/research-os')
DATABASE = ROOT / '.local/live/current-chat-normal-desktop-first-use-20261012/data/researchos.sqlite'
PROJECT = 'a7ebcf2a322c6abcf87e043f601ee804'
SESSION = 'a09d4435036b2b32a0d7076bfc53fd93'
OWNER = 'owner-95f641f393696f7d1439dc36ae99935d'
REQUEST_FIELDS = {
    'request_id', 'project_id', 'session_id', 'model_config_ref', 'runtime_id',
    'task_id', 'plan_hash', 'profile_hash', 'authorize_purpose', 'purpose_seconds',
    'owner_host', 'owner_principal', 'owner_root', 'session_hash',
    'configuration_hash', 'issued_at', 'expires_at',
}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def rows(connection, sql, parameters=()):
    result = [dict(row) for row in connection.execute(sql, parameters)]
    if len(result) > 1000:
        raise ValueError('EVIDENCE_ROW_BOUND_EXCEEDED')
    for row in result:
        for name, value in row.items():
            if isinstance(value, bytes):
                row[name] = {'bytes': len(value), 'sha256': sha(value), 'encoding': 'BINARY_NOT_DUMPED'}
    return result

def observe(request_id=None, run_id=None):
    result = {
        'schema': 'researchos.original-session-readonly-observation/1',
        'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'database': str(DATABASE), 'database_uri_mode': 'ro', 'query_only': True,
        'project_id': PROJECT, 'session_id': SESSION, 'original_request_id': request_id,
        'original_run_id': run_id, 'mutations': 0, 'api_requests': 0,
        'observer_does_not_assert_model_call_count_from_empty_logs': True,
        'formal_increment': 0,
        'not_observed': ['private_management_stdout_frames', 'native_verifier_process_stderr',
                         'native_verifier_numeric_process_wait_status'],
    }
    with sqlite3.connect(DATABASE.as_uri() + '?mode=ro', uri=True, timeout=3) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA query_only=ON')
        assert connection.execute('PRAGMA query_only').fetchone()[0] == 1
        connection.execute('BEGIN')
        result['session'] = rows(connection, '''SELECT id,project_id,revision,writer_epoch,
            writer_client_id,lease_expires_at,workspace_ref,model_config_ref,core_build_id,
            sealed_at,archived_at FROM client_sessions WHERE id=? AND project_id=?''', (SESSION, PROJECT))
        assert len(result['session']) == 1
        result['plans'] = rows(connection, '''SELECT project,task,runtime,plan,plan_hash,author,
            author_root FROM runtime_qualification_plans WHERE project=?''', (PROJECT,))
        result['budgets'] = rows(connection, '''SELECT id,revision,body FROM domain_objects
            WHERE kind='BudgetPolicy' AND (project=? OR project='' OR project IS NULL) ORDER BY id''', (PROJECT,))
        assert {'GLOBAL', 'PROJECT', 'GOAL'} <= {json.loads(row['body'])['scope_type'] for row in result['budgets']}, 'BUDGET_ANCESTRY_INCOMPLETE'
        result['counts'] = {}
        for table in ['runtime_qualification_runs', 'runtime_dispatches', 'resource_effects']:
            result['counts'][table] = connection.execute(f'SELECT COUNT(*) FROM {table} WHERE project=?', (PROJECT,)).fetchone()[0]
        result['private_confirmation_count_for_project'] = connection.execute('''SELECT COUNT(*) FROM idempotency
            WHERE principal=? AND project=? AND operation='host:qualification-confirmation' ''', (OWNER, PROJECT)).fetchone()[0]
        if request_id:
            result['request_rows'] = rows(connection, '''SELECT principal,project,operation,key,
                request_hash,body,created_at FROM idempotency WHERE principal=? AND project=? AND key=?
                AND operation IN ('host:qualification-confirmation','host:managed-runtime-qualification')''',
                (OWNER, PROJECT, request_id))
            original = [row for row in result['request_rows'] if row['operation'] == 'host:qualification-confirmation']
            assert len(original) == 1, 'EXACT_ORIGINAL_PREPARE_REQUIRED'
            raw_body = original[0]['body']
            assert isinstance(raw_body, str)
            request = json.loads(raw_body)
            assert set(request) == REQUEST_FIELDS
            assert request['request_id'] == request_id and request['project_id'] == PROJECT and request['session_id'] == SESSION
            assert request['owner_principal'] == request['owner_root'] == OWNER
            result['original_request'] = request
            result['original_request_body_sha256'] = sha(raw_body.encode('utf-8'))
            result['original_request_hash_matches_stored_body'] = result['original_request_body_sha256'] == original[0]['request_hash']
            assert result['original_request_hash_matches_stored_body'], 'ORIGINAL_REQUEST_HASH_MISMATCH'
            expires = datetime.datetime.fromisoformat(request['expires_at'].replace('Z', '+00:00'))
            result['original_request_seconds_remaining_at_observation'] = (expires - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
            result['consume_rows'] = [row for row in result['request_rows'] if row['operation'] == 'host:managed-runtime-qualification']
            assert len(result['consume_rows']) <= 1
            result['task'] = rows(connection, '''SELECT id,revision,body FROM domain_objects
                WHERE project=? AND kind='Task' AND id=?''', (PROJECT, request['task_id']))
            assert len(result['task']) == 1
            task = json.loads(result['task'][0]['body'])
            goal_id = task['goal_id']
            result['goal_linkage'] = rows(connection, '''SELECT id,revision,
                json_extract(body,'$.project_id') AS project_id,
                json_extract(body,'$.budget_policy_id') AS budget_policy_id,
                json_extract(body,'$.status') AS status FROM domain_objects
                WHERE project=? AND kind='Goal' AND id=?''', (PROJECT, goal_id))
            assert len(result['goal_linkage']) == 1
            goal = result['goal_linkage'][0]
            assert goal['project_id'] == PROJECT and goal['status'] == 'ACTIVE'
            policies = {row['id']: json.loads(row['body']) for row in result['budgets']}
            policy_id = goal['budget_policy_id']
            chain = []
            seen = set()
            observed_time = datetime.datetime.now(datetime.timezone.utc)
            while policy_id:
                assert policy_id not in seen and len(chain) < 20, 'BUDGET_ANCESTRY_CYCLE_OR_BOUND'
                seen.add(policy_id)
                policy = policies[policy_id]
                assert datetime.datetime.fromisoformat(policy['effective_from'].replace('Z', '+00:00')) <= observed_time, 'FUTURE_POLICY_REQUIRES_SEPARATE_EFFECTIVE_REVISION_OBSERVATION'
                assert policy['mode'] == 'UNLIMITED_AMOUNT' and policy['cap'] is None
                assert policy['enforcement'] == 'ACCOUNTING_ONLY' and policy['unknown_cost_action'] == 'ALLOW_AND_RECORD'
                if policy['scope_type'] == 'GOAL':
                    assert policy['scope_id'] == goal_id and policy['project_id'] == PROJECT
                elif policy['scope_type'] == 'PROJECT':
                    assert policy['scope_id'] == PROJECT and policy['project_id'] == PROJECT
                elif policy['scope_type'] == 'GLOBAL':
                    assert policy['scope_id'] == 'global' and policy['project_id'] is None
                else:
                    raise ValueError('UNEXPECTED_ORIGINAL_QUALIFICATION_BUDGET_SCOPE')
                chain.append(policy)
                policy_id = policy['parent_policy_id']
            assert [policy['scope_type'] for policy in chain] == ['GOAL', 'PROJECT', 'GLOBAL']
            result['original_task_goal_effective_budget_chain'] = chain
            result['original_task_goal_budget_binding_validated'] = True
            if result['consume_rows']:
                consumed = result['consume_rows'][0]
                consumed_body = json.loads(consumed['body'])
                assert consumed['request_hash'] == original[0]['request_hash']
                assert consumed_body['request_hash'] == original[0]['request_hash']
                assert consumed_body['task_id'] == request['task_id'] and consumed_body['runtime_id'] == request['runtime_id']
                result['consumed_run_ref'] = consumed_body['run_ref']
        if run_id:
            assert request_id and len(result['consume_rows']) == 1, 'ORIGINAL_REQUEST_CONSUMPTION_REQUIRED_FOR_RUN'
            assert result['consumed_run_ref']['id'] == run_id, 'RUN_NOT_BOUND_TO_ORIGINAL_REQUEST'
            result['qualification_runs'] = rows(connection, '''SELECT project,task,run,runtime,epoch,
                plan_hash,profile_hash,contract_hash,input_hash,context_bundle,owner_root
                FROM runtime_qualification_runs WHERE project=? AND run=?''', (PROJECT, run_id))
            assert len(result['qualification_runs']) == 1
            qualified = result['qualification_runs'][0]
            assert qualified['task'] == request['task_id'] and qualified['runtime'] == request['runtime_id']
            assert qualified['owner_root'] == request['owner_root'] and qualified['plan_hash'] == request['plan_hash']
            result['dispatches'] = rows(connection, '''SELECT project,run,epoch,dispatch_key,manifest_hash,
                manifest,state,worker,journal_locator,identity,observation_sequence,observation_hash
                FROM runtime_dispatches WHERE project=? AND run=?''', (PROJECT, run_id))
            result['resource_effects'] = rows(connection, '''SELECT rowid,project,run,effect_key,sequence,body
                FROM resource_effects WHERE project=? AND run=? ORDER BY effect_key,sequence''', (PROJECT, run_id))
            result['run'] = rows(connection, '''SELECT id,revision,json_remove(body,'$.lease_token_hash') AS safe_body
                FROM domain_objects WHERE project=? AND kind='Run' AND id=?''', (PROJECT, run_id))
            result['ledger_entries'] = rows(connection, '''SELECT id,revision,body FROM domain_objects
                WHERE project=? AND kind='BudgetLedgerEntry' AND json_extract(body,'$.run_id')=? ORDER BY id''', (PROJECT, run_id))
            result['acceptance_receipts'] = rows(connection, '''SELECT id,revision,body FROM domain_objects
                WHERE project=? AND kind='AcceptanceReceipt' AND json_extract(body,'$.run_id')=? ORDER BY id''', (PROJECT, run_id))
        connection.execute('ROLLBACK')
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--request-id')
    parser.add_argument('--run-id')
    args = parser.parse_args()
    target = pathlib.Path(args.out).resolve()
    receipt_root = ROOT / 'execution/v2.4/receipts/W05/W05-99'
    assert target.is_relative_to(receipt_root.resolve())
    assert not target.exists(), 'APPEND_ONLY_OBSERVATION_REQUIRED'
    value = observe(args.request_id, args.run_id)
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    assert len(raw) <= 2 * 1024 * 1024, 'EVIDENCE_BYTE_BOUND_EXCEEDED'
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(raw)
    print(json.dumps({'path': str(target), 'sha256': sha(raw), 'bytes': len(raw),
        'counts': value['counts'], 'formal_increment': 0, 'mutations': 0}))
