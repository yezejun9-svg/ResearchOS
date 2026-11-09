"""Proposed fixed-path W05/A04 owner profile; read-only and fail-closed.

The integrator must install this as execution/v2.4/formal_profile_w05.py and
independently review the source before any formal owner can be registered.
Receipt code is data, never imported. This module neither runs a product nor
creates a reviewer or Root issuance record.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

PREFIX = 'execution/v2.4/receipts/W05/W05-99/'
MODULE = 'execution/v2.4/formal_profile_w05.py'
IDS = tuple('A04-0' + str(i) for i in range(1, 7))
GATES = ('W05-G01', 'W05-G02', 'W05-H08', 'W05-P01', 'W05-U02')
SCHEMAS = {'context': 'researchos.w05.current-context.v1',
           'review': 'researchos.w05.independent-review.v1',
           'issuance': 'researchos.w05.root-observed-issuance.v1'}
MINIMUM_SOURCE = {MODULE, 'execution/v2.4/formal_case_index.py',
                  'ops/ci/runtime.py', 'ops/ci/runtime_w05_live.py',
                  'tests/runtime/check/main.go', 'tests/runtime/check/legacy.go',
                  'ops/ci/export_a04_live.py'}
SCENARIOS = ('success', 'tool_failed', 'request_timeout',
             'pending_queue_cancel', 'executor_crash')
EXTRA = {'A04-04': 'H08', 'A04-05': 'P01', 'A04-06': 'U02'}


def _ref(api, reader, value, *, locator=False):
    api.fields(value, ('path', 'sha256'), ('locator',) if locator else (), 'W05 ref')
    return reader.ref(value, PREFIX, locator=locator)


def _doc(api, reader, value):
    return reader.read(_ref(api, reader, value))


def _raw(api, reader, value):
    path = _ref(api, reader, value, locator=True)
    location = api.obj(value.get('locator'), 'A04 raw locator')
    content = path.read_bytes()
    if set(location) == {'json_pointer'}:
        pointer = location['json_pointer']
        api.require(type(pointer) is str and (not pointer or pointer.startswith('/')),
                    'RAW_LOCATOR', value['path'])
        current = api.strict_json(content)
        for token in pointer[1:].split('/') if pointer else ():
            api.require(re.search(r'~(?![01])', token) is None, 'RAW_LOCATOR', pointer)
            token = token.replace('~1', '/').replace('~0', '~')
            if type(current) is dict:
                api.require(token in current, 'RAW_LOCATOR_MISSING', pointer)
                current = current[token]
            elif type(current) is list:
                api.require(re.fullmatch(r'0|[1-9][0-9]*', token) is not None and
                            int(token) < len(current), 'RAW_LOCATOR_MISSING', pointer)
                current = current[int(token)]
            else:
                api.require(False, 'RAW_LOCATOR_MISSING', pointer)
    else:
        api.fields(location, ('line_start', 'line_end'), label='A04 line locator')
        lines = content.decode('utf-8').splitlines()
        first, last = location['line_start'], location['line_end']
        api.require(type(first) is int and type(last) is int and
                    1 <= first <= last <= len(lines), 'RAW_LOCATOR_MISSING', value['path'])
        current = '\n'.join(lines[first - 1:last])
    api.require(api.meaningful(current), 'RAW_EMPTY', value['path'])
    return current


def _vector(api, reader, context):
    vector = api.fields(context.get('version_vector'),
                        ('schema', 'package_version', 'spec_files', 'source_files',
                         'input_files', 'lock_files', 'tool_files', 'environment',
                         'components'), label='W05 vector')
    api.require(vector['schema'] == 'researchos.w05.version-vector.v1' and
                vector['package_version'] == '2.4.0', 'SCHEMA', 'W05 vector')
    pinned, paths = {}, set()
    for group in ('spec_files', 'source_files', 'input_files', 'lock_files', 'tool_files'):
        local = set()
        for reference in api.sequence(vector[group], 'W05 ' + group):
            path = reader.ref(reference)
            api.require(path not in local, 'DUPLICATE_REFERENCE', group)
            local.add(path)
            api.require(path not in pinned or pinned[path] == reference['sha256'],
                        'VECTOR_CONFLICT', reference['path'])
            pinned[path] = reference['sha256']
            paths.add(reference['path'])
    api.require(MINIMUM_SOURCE <= {r['path'] for r in vector['source_files']},
                'SOURCE_COVERAGE', 'current A04 handler/profile source missing')
    api.coverage(reader, context['source_coverage'], vector['source_files'])
    for name, digest in api.FROZEN_HASHES.items():
        api.require(any(Path(ref['path']).name == name and ref['sha256'] == digest
                        for ref in vector['spec_files']), 'VECTOR_BASELINE', name)
    for key in ('execution/v2.4/commands.json', 'execution/commands.json',
                'execution/toolchains/locked.json'):
        api.require(key in paths, 'VECTOR_INPUT', key)
    env = api.fields(vector['environment'], ('os', 'arch', 'timezone'), label='environment')
    api.require('windows' in env['os'].casefold() and
                all(api.text(value, key) for key, value in env.items()),
                'ENVIRONMENT', 'A04 requires actual Windows')
    components = api.fields(vector['components'], ('model', 'adapter', 'rubric', 'policy'),
                            label='components')
    for name, value in components.items():
        api.fields(value, ('status', 'version', 'refs'), label=name)
        api.require(value['status'] == 'applicable', 'COMPONENT_STATUS', name)
        api.text(value['version'], name)
        for reference in api.sequence(value['refs'], name):
            api.require(pinned.get(reader.ref(reference)) == reference['sha256'],
                        'COMPONENT_UNPINNED', name)
    return vector, pinned


def _frozen(api, reader, plan_path):
    package_plan = Path(plan_path).resolve(strict=True)
    api.require(package_plan.name == 'execution.plan.json' and
                api.sha256(package_plan) == api.FROZEN_HASHES['execution.plan.json'],
                'FROZEN_BASELINE', 'v2.4 plan')
    plan = reader.read(package_plan)
    step = next(item for item in plan['steps'] if item['id'] == 'W05-99')
    api.require(step['formal_final_cases'] == ['A04'] and
                [row.get('check_id') for row in step['verification_commands'] if row.get('check_id')] == list(GATES) and
                [row.get('case_id') for row in step['verification_commands'] if row.get('case_id')] == ['A04'],
                'FROZEN_OWNER', 'W05-99 binding changed')
    catalog_path = package_plan.parent / 'acceptance.json'
    api.require(catalog_path.is_file() and
                api.sha256(catalog_path) == api.FROZEN_HASHES['acceptance.json'],
                'FROZEN_BASELINE', 'v2.4 acceptance')
    catalog = reader.read(catalog_path)
    case = next(item for item in catalog['cases'] if item['id'] == 'A04')
    api.require(case['final_owner_task'] == 'W05' and case['mode'] == 'LIVE_WINDOWS',
                'FROZEN_OWNER', 'A04')
    api.exact_ids([row['id'] for row in case['assertions']], IDS, 'A04 frozen assertions')
    api.require(case['input']['subcases'] == list(SCENARIOS),
                'FROZEN_OWNER', 'five A04 subcases')
    return case, step


def _invocations(api, reader, context, command):
    api.fields(command, ('schema', 'case_id', 'run_id', 'command_key', 'registered_argv',
                         'invocations'), label='A04 command receipt')
    api.require(command['schema'] == 'researchos.w05.command-receipt.v1' and
                command['case_id'] == 'A04' and command['run_id'] == context['run_id'] and
                command['command_key'] == 'test.runtime' and
                command['registered_argv'] == context['registered_argv'],
                'COMMAND_IDENTITY', 'A04')
    rows = api.sequence(command['invocations'], 'actual A04 invocations')
    api.exact_ids([row['lane'] for row in rows], list(SCENARIOS) + list(EXTRA.values()),
                  'A04 live lanes')
    by_lane = {}
    for row in rows:
        api.fields(row, ('lane', 'invocation_ref', 'scope_ref'), label='lane')
        actual = _doc(api, reader, row['invocation_ref'])
        api.fields(actual, ('schema', 'run_id', 'lane', 'argv', 'cwd', 'env_names',
                            'native_exit', 'started_at', 'ended_at', 'stdout_ref',
                            'stderr_ref', 'root_grant_ref', 'initial_tool_input',
                            'producer_ref'), label='actual invocation')
        api.require(actual['schema'] == 'researchos.w05.live-invocation.v1' and
                    actual['run_id'] == context['run_id'] and actual['lane'] == row['lane'] and
                    actual['root_grant_ref'] == context['root_grant_ref'] and
                    actual['cwd'] == context['worktree'] and
                    type(actual['native_exit']) is int,
                    'INVOCATION_IDENTITY', row['lane'])
        api.interval(actual, row['lane'])
        for key in ('stdout_ref', 'stderr_ref'):
            _ref(api, reader, actual[key])
        scope = _doc(api, reader, row['scope_ref'])
        api.require(scope.get('schema') == 'researchos.w05.a04-live-scope.v1' and
                    scope.get('run_id') == context['run_id'] and
                    scope.get('lane') == row['lane'] and
                    scope.get('root_grant_ref') == context['root_grant_ref'] and
                    scope.get('argv') == actual['argv'] and
                    scope.get('cwd') == actual['cwd'] and
                    scope.get('env_names') == actual['env_names'],
                    'ROOT_SCOPE', row['lane'])
        by_lane[row['lane']] = dict(actual, _scope=scope)
    return by_lane


def _witness(api, reader, row, context, invocations):
    api.fields(row, ('id', 'expected', 'actual', 'status', 'lane',
                     'raw_evidence_refs', 'refusal_evidence_refs', 'command_keys',
                     'product_identity', 'original_witness_ref',
                     'negative_invocation_ref'),
               label='A04 assertion')
    api.require(row['status'] == 'PASS' and api.meaningful(row['actual']) and
                row['command_keys'] == ['test.runtime'], 'ASSERTION_RESULT', row['id'])
    api.require(row['lane'] in invocations and row['lane'] == ASSERTION_LANES[row['id']],
                'ASSERTION_LANE', row['id'])
    _live_gate(api, reader, context, row, invocations[row['lane']])
    values = [_raw(api, reader, ref) for ref in api.sequence(
        row['raw_evidence_refs'], row['id'] + ' original raw evidence')]
    api.require(all(type(value) is dict for value in values),
                'RAW_SEMANTIC_SHAPE', row['id'])
    proof = next((value for value in values if value.get('schema') ==
                  'researchos.w05.a04-raw-observation.v1' and
                  value.get('assertion_id') == row['id'] and
                  value.get('run_id') == context['run_id'] and
                  value.get('lane') == row['lane']), None)
    api.require(proof is not None, 'RAW_SEMANTIC_MISSING', row['id'])
    api.require(proof.get('invocation_ref') == next(
        item['invocation_ref'] for item in context['command_invocations']
        if item['lane'] == row['lane']), 'RAW_INVOCATION', row['id'])
    facts = api.obj(proof.get('facts'), row['id'] + ' facts')
    sources = api.obj(proof.get('fact_source_refs'), row['id'] + ' fact sources')
    api.require(set(sources) == set(facts) and
                all(type(reference) is dict and
                    reference.get('path') in context['product_original_paths'] and
                    reference.get('path') not in
                    {item['path'] for item in row['raw_evidence_refs']} and
                    _raw(api, reader, reference) == facts[key]
                    for key, reference in sources.items()),
                'RAW_FACT_NOT_FROM_PRODUCT_ORIGINAL', row['id'])
    if row['id'] == 'A04-01':
        api.require(facts.get('task_status_after_host') == 'EXECUTION_REPORTED' and
                    facts.get('run_status') == 'SETTLED' and
                    facts.get('host_receipts_complete') is True and
                    facts.get('early_accepted') is False and
                    facts.get('independent_acceptance') == 'NOT_EVALUATED',
                    'A04_COMPLETION', row['id'])
    elif row['id'] == 'A04-02':
        api.require(facts.get('cancel_confirmed') is True and
                    type(facts.get('owned_tool_processes_after')) is int and facts['owned_tool_processes_after'] == 0 and
                    type(facts.get('pending_requests_after')) is int and facts['pending_requests_after'] == 0 and
                    type(facts.get('late_launches')) is int and facts['late_launches'] == 0,
                    'A04_CANCEL', row['id'])
    elif row['id'] == 'A04-03':
        api.require(facts.get('crash_observed') is True and
                    facts.get('timeout_observed') is True and
                    facts.get('worktree_isolated') is True and
                    facts.get('credentials_isolated') is True and
                    facts.get('new_context_bundle_ref') and
                    type(facts.get('blind_retry_count')) is int and facts['blind_retry_count'] == 0 and
                    facts.get('timeout_invocation_ref') == next(
                        item['invocation_ref'] for item in context['command_invocations']
                        if item['lane'] == 'request_timeout') and
                    facts.get('crash_invocation_ref') == next(
                        item['invocation_ref'] for item in context['command_invocations']
                        if item['lane'] == 'executor_crash'),
                    'A04_RECOVERY', row['id'])
    elif row['id'] == 'A04-04':
        api.require(facts.get('parent_run_id') and facts.get('child_run_id') and
                    facts['parent_run_id'] != facts['child_run_id'] and
                    facts.get('tool_effect_id') and
                    facts.get('shared_cancel_scope') is True and
                    facts.get('shared_budget_scope') is True and
                    facts.get('fixed_model_unchanged') is True and
                    facts.get('selected_patches_preserved') is True and
                    facts.get('unsupported_adapters_explicit') is True and
                    facts.get('version_matrix_ref') and
                    _doc(api, reader, facts['version_matrix_ref']).get('selected_runtime') ==
                    context['selected_runtime'],
                    'A04_NESTED', row['id'])
    elif row['id'] == 'A04-05':
        api.require(facts.get('installed_cli') == 'researchos' and
                    facts.get('interactive_task_complete') is True and
                    facts.get('jsonl_stream_valid') is True and
                    facts.get('resume_observed') is True and
                    facts.get('cancel_observed') is True and
                    facts.get('stdout_logs_mixed') is False and
                    facts.get('failure_exit_nonzero') is True and
                    facts.get('exit_zero_auto_accept') is False,
                    'A04_CLI', row['id'])
    else:
        api.require(row['id'] == 'A04-06' and
                    facts.get('issue_id') == 'ISSUE-CONTINUITY-001' and
                    facts.get('selected_by_delivery_contract') is True and
                    type(facts.get('manual_admin_commands')) is int and facts['manual_admin_commands'] == 0 and
                    facts.get('chinese_input') is True and
                    isinstance(facts.get('file_before_sha256'), str) and
                    isinstance(facts.get('file_after_sha256'), str) and
                    api.SHA.fullmatch(facts['file_before_sha256']) and
                    api.SHA.fullmatch(facts['file_after_sha256']) and
                    facts.get('file_before_sha256') != facts.get('file_after_sha256') and
                    type(facts.get('tests_native_exit')) is int and facts['tests_native_exit'] == 0 and
                    facts.get('fixed_model_unchanged') is True and
                    facts.get('model_before') == facts.get('model_after') ==
                    context['fixed_model'] and
                    set(facts.get('cli_handlers', ())) ==
                    {'init', 'run', 'goal', 'resume', 'status', 'cancel', 'doctor',
                     'config', 'interactive', 'jsonl', 'slash'},
                    'A04_REAL_ISSUE', row['id'])
    doc, raw = _profile_io(api, reader, context)
    verify_refusal(doc, raw, context, row)
    api.require(row['actual'] == proof.get('actual'),
                'ASSERTION_RESULT', row['id'])


def _global(api, reader, context, roots, case):
    refs = api.fields(context.get('global_evidence_refs'),
                      ('run_receipt', 'version_manifest', 'command_receipt',
                       'assertion_results'), label='A04 producer GLOBAL evidence')
    paths = [_ref(api, reader, reference) for reference in refs.values()]
    api.require(len(set(paths)) == 4 and roots['review'] not in paths,
                'DUPLICATE_REFERENCE', 'A04 GLOBAL producer files')
    run, version, command, assertions = [reader.read(path) for path in paths]
    api.fields(run, ('schema', 'case_id', 'run_id', 'environment_mode', 'os', 'arch',
                     'timezone', 'started_at', 'ended_at', 'executor_id', 'verifier_id'),
               label='A04 run receipt')
    api.require(run['schema'] == 'researchos.w05.run-receipt.v1' and
                run['case_id'] == 'A04' and run['run_id'] == context['run_id'] and
                run['environment_mode'] == 'LIVE_WINDOWS' and
                run['executor_id'] == context['executor_id'] and
                run['verifier_id'] == reader.read(roots['review'])['reviewer_id'] and
                {key: run[key] for key in ('os', 'arch', 'timezone')} ==
                context['version_vector']['environment'], 'RUN_IDENTITY', 'A04')
    api.interval(run, 'A04 run receipt')
    api.fields(version, ('schema', 'case_id', 'run_id', 'package_version',
                         'code_revision', 'dirty', 'version_vector_ref'),
               label='A04 version manifest')
    api.require(version['schema'] == 'researchos.w05.version-manifest.v1' and
                version['case_id'] == 'A04' and version['run_id'] == context['run_id'] and
                version['package_version'] == '2.4.0' and
                api.COMMIT.fullmatch(version['code_revision']) and
                type(version['dirty']) is bool and
                _doc(api, reader, version['version_vector_ref']) == context['version_vector'],
                'MANIFEST_IDENTITY', 'A04')
    invocations = _invocations(api, reader, context, command)
    api.fields(assertions, ('schema', 'case_id', 'run_id', 'assertions'),
               label='A04 assertion results')
    api.require(assertions['schema'] == 'researchos.w05.assertion-results.v1' and
                assertions['case_id'] == 'A04' and
                assertions['run_id'] == context['run_id'], 'ASSERTION_IDENTITY', 'A04')
    rows = api.sequence(assertions['assertions'], 'A04 assertion results')
    api.exact_ids([row['id'] for row in rows], IDS, 'A04 assertion IDs')
    expected = {row['id']: row['expected'] for row in case['assertions']}
    for row in rows:
        api.require(row['expected'] == expected[row['id']],
                    'FROZEN_ASSERTION', row['id'])
        _witness(api, reader, row, context, invocations)
    return {row['id']: row for row in rows}


def _independent(api, reader, owner, roots, context, results):
    review, issuance = reader.read(roots['review']), reader.read(roots['issuance'])
    api.require(review.get('schema') == SCHEMAS['review'] and
                issuance.get('schema') == SCHEMAS['issuance'],
                'SCHEMA', 'A04 independent documents')
    executor = api.text(context['executor_id'], 'executor')
    reviewer = api.text(review.get('reviewer_id'), 'reviewer')
    api.require(len({executor.casefold(), reviewer.casefold(), 'codex:/root'}) == 3 and
                review.get('executor_id') == executor and
                issuance.get('actor') == 'codex:/root' and
                issuance.get('reviewer_id') == reviewer and
                issuance.get('executor_id') == executor,
                'INDEPENDENT_ACTOR', 'A04')
    for document in (review, issuance):
        api.require(document.get('task_id') == 'W05' and
                    document.get('step_id') == 'W05-99' and
                    document.get('run_id') == context['run_id'] and
                    reader.ref(document['context_ref'], PREFIX) == roots['context'],
                    'REVIEW_IDENTITY', 'A04')
    api.require(_ref(api, reader, issuance['review_ref']) == roots['review'] and
                review.get('decision') == 'ACCEPTED' and
                review.get('missing') == [] and review.get('failed') == [] and
                review.get('version_vector') == context['version_vector'] and
                not review.get('supersedes_review_refs'),
                'REVIEW_VERDICT', 'A04')
    api.require(review.get('acceptance_baseline_ref') == context['acceptance_baseline_ref'] and
                review.get('evidence_index_ref') == review.get('context_ref'),
                'REVIEW_BASELINE', 'A04 fifth GLOBAL part')
    for key, wanted in (('assertion_verdicts', IDS), ('gate_verdicts', GATES)):
        rows = api.sequence(review.get(key), key)
        api.exact_ids([row['id'] for row in rows], wanted, key)
        for row in rows:
            api.require(row.get('status') == 'PASS' and api.meaningful(row.get('actual')) and
                        row.get('raw_evidence_refs'), 'REVIEW_VERDICT', row['id'])
            if key == 'assertion_verdicts':
                api.require(row['raw_evidence_refs'] == results[row['id']]['raw_evidence_refs'],
                            'REVIEW_EVIDENCE', row['id'])
            for reference in row['raw_evidence_refs']:
                _raw(api, reader, reference)
    _delivery_original(api, reader, issuance, review)
    message = _doc(api, reader, issuance['delivery_ref'])
    api.require(message.get('schema') == 'researchos.root-received-independent-message.v1' and
                message.get('recorded_by') == 'codex:/root' and
                message.get('recipient') == 'codex:/root' and
                message.get('sender') == reviewer and
                message.get('review_ref') == issuance['review_ref'],
                'ROOT_OBSERVED_DELIVERY', 'A04')
    content = api.text(message.get('content'), 'original independent message')
    api.require(issuance['review_ref']['sha256'] in content and
                context['global_evidence_refs']['assertion_results']['sha256'] in content,
                'ROOT_OBSERVED_DELIVERY', 'A04 hash names absent')
    api.require(api.stamp(context['created_at'], 'A04 context') <=
                api.stamp(review['issued_at'], 'A04 review') <=
                api.stamp(message['received_at'], 'Root received') <=
                api.stamp(issuance['observed_at'], 'Root observed') <=
                api.stamp(owner['accepted_at'], 'owner accepted'),
                'REGISTERED_TIME_ORDER', 'A04')


def verify_owner(api, reader, owner, roots, plan_path):
    api.require(owner.get('status') == 'ACCEPTED', 'OWNER_NOT_ACCEPTED', 'W05-99')
    context = reader.read(roots['context'])
    api.require(context.get('schema') == SCHEMAS['context'] and
                context.get('task_id') == 'W05' and
                context.get('step_id') == 'W05-99' and
                context.get('case_id') == 'A04' and
                context.get('mode') == 'LIVE_WINDOWS', 'SCHEMA', 'W05 context')
    api.text(context.get('run_id'), 'A04 run')
    api.text(context.get('executor_id'), 'A04 executor')
    accounting = api.fields(context.get('accounting'),
                            ('mode', 'status', 'amount_usd', 'source_refs'),
                            label='A04 original cost accounting')
    api.require(accounting['mode'] in ('UNLIMITED_AMOUNT', 'CAPPED') and
                accounting['status'] in ('UNKNOWN', 'RECORDED') and
                type(accounting['source_refs']) is list and
                ((accounting['status'] == 'UNKNOWN' and
                  accounting['amount_usd'] is None) or
                 (accounting['status'] == 'RECORDED' and
                  type(accounting['amount_usd']) in (int, float) and
                  accounting['amount_usd'] >= 0 and
                  bool(accounting['source_refs']))),
                'COST_ACCOUNTING', 'unknown is null, never inferred zero')
    for reference in accounting['source_refs']:
        _ref(api, reader, reference)
    api.require(reader.ref(context['acceptance_baseline_ref']).name == 'acceptance.json' and
                context['acceptance_baseline_ref']['sha256'] ==
                api.FROZEN_HASHES['acceptance.json'],
                'FROZEN_BASELINE', 'A04')
    case, step = _frozen(api, reader, plan_path)
    vector, pinned = _vector(api, reader, context)
    state = reader.read(reader.path('execution/v2.4/step_state.json'))
    statuses = {row['id']: row['status'] for row in state['steps']}
    api.require(all(statuses.get(key) == 'ACCEPTED' for key in step['dependencies']),
                'DEPENDENCY', 'W05-99')
    _grant_original(api, reader, context)
    grant = _doc(api, reader, context['root_grant_ref'])
    api.require(grant.get('schema') == 'researchos.w05.a04-root-grant.v1' and
                grant.get('decision') == 'GRANTED' and
                grant.get('run_id') == context['run_id'] and
                grant.get('accounting_mode') == accounting['mode'] and
                grant.get('selected_runtime') == context['selected_runtime'] and
                grant.get('fixed_model') == context['fixed_model'],
                'ROOT_GRANT', 'A04')
    originals = api.sequence(context.get('product_original_refs'),
                             'Root captured original product refs')
    original_paths = set()
    for reference in originals:
        path = _ref(api, reader, reference)
        api.require(path not in original_paths, 'DUPLICATE_REFERENCE', 'product original')
        original_paths.add(path)
    context = dict(context, product_original_paths={item['path'] for item in originals})
    command = _doc(api, reader, context['global_evidence_refs']['command_receipt'])
    context = dict(context, command_invocations=command['invocations'])
    results = _global(api, reader, context, roots, case)
    _independent(api, reader, owner, roots, context, results)
    reader.finish()
    return context


# This ABI is a SOURCE proposal. Root must implement and independently review its
# real capture producer; this module never produces those observations.
ASSERTION_LANES = dict(zip(IDS, ('success', 'pending_queue_cancel',
                                'executor_crash', 'H08', 'P01', 'U02')))


def _integer(value, label):
    if type(value) is not int or value < 0:
        raise ValueError('OPEN_TYPED_INTEGER:' + label)
    return value


def _native_exit(value, label):
    if type(value) is not int:
        raise ValueError('OPEN_TYPED_NATIVE_EXIT:' + label)
    return value


def _nonempty(value, label, kind=str):
    if type(value) is not kind or not value:
        raise ValueError('OPEN_REQUIRED_ORIGINAL:' + label)
    return value


def _json_original(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('OPEN_DUPLICATE_ORIGINAL_KEY')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(
                          ValueError('OPEN_NONFINITE_ORIGINAL')))


def _original(doc, raw, reference):
    if type(reference) is not dict or set(reference) != {'path', 'sha256'}:
        raise ValueError('OPEN_WHOLE_ORIGINAL_REQUIRED')
    return doc(reference), raw(reference)


def _root_pair(document, scope):
    if type(document) is not dict or document.get('schema') != 'researchos.w05.original-tool-pair.v2':
        raise ValueError('OPEN_ORIGINAL_ROOT_TOOL_PAIR')
    initial, terminal = document.get('initial'), document.get('terminal')
    for pair in (initial, terminal):
        if type(pair) is not dict or set(pair) != {'tool', 'input', 'result'} or type(pair['input']) is not dict or type(pair['result']) is not dict:
            raise ValueError('OPEN_ORIGINAL_TOOL_INPUT_RESULT')
    if initial['tool'] != 'exec_command' or initial['input'] != scope['initial_tool_input']:
        raise ValueError('OPEN_ROOT_INITIAL_INPUT')
    first = initial['result']
    if type(first.get('session_id')) is int:
        if terminal['tool'] != 'write_stdin' or terminal['input'].get('session_id') != first['session_id'] or terminal['input'].get('chars', '') != '':
            raise ValueError('OPEN_ROOT_TERMINAL_SESSION')
    elif terminal != initial:
        raise ValueError('OPEN_ROOT_SYNCHRONOUS_PAIR')
    _native_exit(terminal['result'].get('exit_code'), 'actual outer exit')
    output = _nonempty(terminal['result'].get('output'), 'original terminal output')
    lines = output.splitlines()
    summaries = [_json_original(line) for line in lines if line.startswith('{')]
    closed = [row for row in summaries if type(row) is dict and 'actual_launcher_native_exit' in row]
    if len(closed) != 1:
        raise ValueError('OPEN_ACTUAL_NATIVE_BRIDGE')
    _native_exit(closed[0]['actual_launcher_native_exit'], 'actual launcher native exit')
    return closed[0]


def _database(raw, identity):
    # Only a Root-materialized complete, quiescent SQLite snapshot is supported.
    if type(raw) is not bytes or not raw.startswith((b'SQLite format 3' + bytes((0,)))):
        raise ValueError('OPEN_COMPLETE_SQLITE_ORIGINAL')
    import sqlite3
    db = sqlite3.connect(':memory:')
    try:
        db.deserialize(raw)
        db.execute('PRAGMA query_only=ON')
        result = {}
        for kind, key, output_key in (('Task', 'task_id', 'Task'), ('Run', 'run_id', 'TaskRun')):
            rows = db.execute('SELECT revision,content_hash,body FROM domain_objects WHERE project=? AND kind=? AND id=?',
                              (identity['project_id'], kind, identity[key])).fetchall()
            if len(rows) != 1:
                raise ValueError('OPEN_DATABASE_CURRENT_IDENTITY')
            result[output_key] = _database_row(kind, *rows[0], identity, identity[key])
        artifact_ids = result['TaskRun']['result_artifact_ids']
        if len(set(artifact_ids)) != len(artifact_ids):
            raise ValueError('OPEN_DUPLICATE_RESULT_ARTIFACT')
        result['Artifacts'] = {}
        for artifact_id in artifact_ids:
            rows = db.execute('SELECT revision,content_hash,body FROM domain_objects WHERE project=? AND kind=\'Artifact\' AND id=?',
                              (identity['project_id'], artifact_id)).fetchall()
            if len(rows) != 1:
                raise ValueError('OPEN_DATABASE_CURRENT_ARTIFACT')
            result['Artifacts'][artifact_id] = _database_row('Artifact', *rows[0], identity, artifact_id)
        result['acceptance_count'] = db.execute(
            "SELECT count(*) FROM domain_objects WHERE project=? AND kind='AcceptanceReceipt' AND json_extract(body,'$.task_id')=?",
            (identity['project_id'], identity['task_id'])).fetchone()[0]
        return result
    finally:
        db.close()


def _jsonl(raw, identity):
    lines = raw.decode('utf-8').splitlines()
    if not lines or any(not line.strip() for line in lines):
        raise ValueError('OPEN_COMPLETE_JSONL')
    frames = [_json_original(line) for line in lines]
    events, finals, event_ids = [], [], set()
    for ordinal, frame in enumerate(frames):
        if type(frame) is not dict:
            raise ValueError('OPEN_JSONL_OBJECT')
        if frame.get('type') == 'session.event':
            if finals:
                raise ValueError('OPEN_EVENT_AFTER_FINAL')
            event = frame.get('event')
            _event_schema(event)
            if event['session_id'] != identity['session_id'] or event['core_build_id'] != identity['core_build_id']:
                raise ValueError('OPEN_EVENT_IDENTITY')
            if event['event_id'] in event_ids:
                raise ValueError('OPEN_DUPLICATE_EVENT_ID')
            event_ids.add(event['event_id'])
            if events and event['sequence'] != events[-1]['sequence'] + 1:
                raise ValueError('OPEN_EVENT_GAP')
            if event['run_id'] not in (None, identity['run_id']):
                raise ValueError('OPEN_FOREIGN_RUN_EVENT')
            if event['kind'] == 'RUN_STATE' and event['payload']['run_id'] != event['run_id']:
                raise ValueError('OPEN_RUN_STATE_EVENT_RUN')
            if event['kind'] == 'GOAL_STATE' and event['payload']['goal_id'] != identity['goal_id']:
                raise ValueError('OPEN_GOAL_STATE_EVENT_GOAL')
            events.append(event)
        elif frame.get('type') == 'session.snapshot':
            raise ValueError('OPEN_EVENT_RESYNC_OR_SNAPSHOT')
        else:
            if ordinal != len(frames)-1 or finals or type(frame.get('execution')) is not dict:
                raise ValueError('OPEN_SINGLE_FINAL_REQUIRED')
            finals.append(frame['execution'])
    if not events or len(finals) != 1:
        raise ValueError('OPEN_ORIGINAL_EVENT_STREAM')
    final = finals[0]
    for key in ('project_id', 'session_id', 'goal_id', 'task_id', 'run_id'):
        if final.get(key) != identity[key]:
            raise ValueError('OPEN_FINAL_IDENTITY')
    _integer(final.get('event_sequence'), 'final event sequence')
    if final['event_sequence'] != events[-1]['sequence'] or final.get('independent_acceptance') != 'NOT_EVALUATED':
        raise ValueError('OPEN_FINAL_CURSOR_ACCEPTANCE')
    _native_exit(final.get('exit_code'), 'actual CLI exit')
    return events, final


def verify_live_originals(doc, raw, context, row, invocation, scope):
    identity = row.get('product_identity')
    keys = {'project_id', 'session_id', 'goal_id', 'task_id', 'run_id', 'core_build_id'}
    if type(identity) is not dict or set(identity) != keys or not all(type(value) is str and value for value in identity.values()):
        raise ValueError('OPEN_ACTUAL_PRODUCT_IDENTITIES')
    if row['lane'] != ASSERTION_LANES[row['id']]:
        raise ValueError('OPEN_FROZEN_ASSERTION_LANE')
    original, _ = _original(doc, raw, row.get('original_witness_ref'))
    if original.get('schema') != 'researchos.w05.a04-whole-originals.v2' or original.get('run_id') != context['run_id'] or original.get('lane') != row['lane'] or original.get('product_identity') != identity:
        raise ValueError('OPEN_WHOLE_ORIGINAL_IDENTITY')
    for key in ('argv', 'cwd', 'env_names', 'initial_tool_input', 'producer_ref'):
        if key not in scope or scope[key] != invocation.get(key):
            raise ValueError('OPEN_COMPLETE_SCOPE_ABI')
    _nonempty(invocation.get('argv'), 'actual argv', list)
    _nonempty(invocation.get('cwd'), 'actual cwd')
    if type(invocation.get('env_names')) is not list or any(type(v) is not str or not v for v in invocation['env_names']):
        raise ValueError('OPEN_ACTUAL_ENV_NAMES')
    _native_exit(invocation.get('native_exit'), 'actual invocation exit')
    capture, _ = _original(doc, raw, original.get('root_tool_pair_ref'))
    closed = _root_pair(capture, scope)
    if closed['actual_launcher_native_exit'] != invocation['native_exit']:
        raise ValueError('OPEN_NATIVE_RESULT_CONFLICT')
    job, _ = _original(doc, raw, original.get('windows_job_ref'))
    if job.get('schema') != 'researchos.w05.windows-job-original.v2' or job.get('run_id') != context['run_id'] or job.get('lane') != row['lane'] or job.get('root_tool_pair_ref') != original['root_tool_pair_ref'] or job.get('producer_ref') != scope['producer_ref'] or job.get('native_exit') != invocation['native_exit']:
        raise ValueError('OPEN_WINDOWS_JOB_BINDING')
    for key in ('owned_processes_before', 'owned_processes_after', 'pending_requests_after', 'launch_events'):
        if type(job.get(key)) is not list:
            raise ValueError('OPEN_COMPLETE_WINDOWS_JOB_EVENTS')
    if job.get('job_closed') is not True or job.get('cleanup_complete') is not True:
        raise ValueError('OPEN_WINDOWS_JOB_NOT_CLOSED')
    objects = _database(raw(original['database_ref']), identity)
    events, final = _jsonl(raw(original['jsonl_ref']), identity)
    if final['exit_code'] != invocation['native_exit']:
        raise ValueError('OPEN_JSONL_NATIVE_CONFLICT')
    task, run = objects['Task'], objects['TaskRun']
    states = [ev.get('payload') for ev in events if ev.get('kind') == 'RUN_STATE' and ev.get('run_id') == identity['run_id']]
    if not states or type(states[-1]) is not dict:
        raise ValueError('OPEN_RUN_STATE_ORIGINAL')
    state = states[-1]
    _integer(state.get('revision'), 'RUN_STATE revision')
    if state.get('revision') != run.get('revision') or state.get('status') != run.get('status') or run.get('children_stopped') is not True or run.get('queue_empty') is not True or state.get('children_stopped') is not True or state.get('queue_empty') is not True:
        raise ValueError('OPEN_RUN_DATABASE_EVENT_BINDING')
    if row['id'] == 'A04-01':
        if task.get('status') != 'EXECUTION_REPORTED' or run.get('status') != 'SETTLED' or objects['acceptance_count'] != 0 or final.get('status') != 'EXECUTION_REPORTED':
            raise ValueError('OPEN_EXECUTION_REPORTED_NOT_ACCEPTED')
        if not run.get('result_artifact_ids') or state.get('settled_at') != run.get('runtime_settled_at'):
            raise ValueError('OPEN_SETTLED_RECEIPTS')
    elif row['id'] == 'A04-02':
        if run.get('status') != 'CANCELLED' or not run.get('cancel_confirmed_at') or state.get('cancel_confirmed_at') != run['cancel_confirmed_at'] or job['owned_processes_after'] or job['pending_requests_after']:
            raise ValueError('OPEN_CANCEL_SETTLEMENT')
        for event in job['launch_events']:
            if type(event) is not dict or event.get('task_id') != identity['task_id'] or type(event.get('after_cancel')) is not bool or event['after_cancel']:
                raise ValueError('OPEN_CANCEL_LATE_OR_FOREIGN_LAUNCH')
    # Recovery/nested SDK/installed interaction/Issue actions require actual
    # producer formats not yet frozen or implemented. Do not let booleans or
    # an arbitrary "facts" export stand in for those missing semantic decoders.
    else:
        for key in ('sdk_jsonl_ref', 'action_jsonl_ref', 'recovery_ref'):
            _original(doc, raw, original.get(key))
        raise ValueError('OPEN_A04_' + row['id'] + '_ACTUAL_PRODUCER_SEMANTIC_DECODER_REQUIRED')
    return original


def verify_refusal(doc, raw, context, row):
    identity = row['product_identity']
    expected = {'run_id': context['run_id'], 'task_id': identity['task_id'],
                'lane': row['lane'], 'assertion_id': row['id'],
                'negative_condition': row['expected'], 'product_identity': identity}
    issuance, _ = _original(doc, raw, context.get('root_grant_issuance_ref'))
    if issuance.get('schema') != 'researchos.w05.original-root-grant-issuance.v2' or issuance.get('actor_id') != 'codex:/root' or issuance.get('run_id') != context['run_id'] or issuance.get('grant_ref') != context['root_grant_ref']:
        raise ValueError('OPEN_NEGATIVE_ROOT_ISSUANCE')
    scope_refs = _nonempty(issuance.get('negative_scope_refs'), 'Root negative scope refs', list)
    if any(type(ref) is not dict or set(ref) != {'path', 'sha256'} for ref in scope_refs) or len({ref['path'] for ref in scope_refs}) != len(scope_refs):
        raise ValueError('OPEN_NEGATIVE_ROOT_SCOPE_REFS')
    original_result = issuance.get('original_result')
    if type(original_result) is not dict or type(original_result.get('exit_code')) is not int or original_result['exit_code'] != 0 or type(original_result.get('output')) is not str:
        raise ValueError('OPEN_NEGATIVE_ROOT_ISSUANCE_RESULT')
    observed = [_json_original(line) for line in original_result['output'].splitlines() if line.startswith('{')]
    if len(observed) != 1 or type(observed[0]) is not dict or observed[0].get('grant_ref') != context['root_grant_ref'] or observed[0].get('negative_scope_refs') != scope_refs:
        raise ValueError('OPEN_NEGATIVE_ROOT_ORIGINAL_SCOPE_BINDING')
    for reference in _nonempty(row.get('refusal_evidence_refs'), 'actual refusal refs', list):
        refusal, _ = _original(doc, raw, reference)
        if refusal.get('schema') != 'researchos.w05.actual-refusal.v2' or refusal.get('rejected') is not True or any(refusal.get(key) != expected[key] for key in ('assertion_id', 'run_id', 'lane', 'task_id', 'negative_condition')):
            raise ValueError('OPEN_ACTUAL_REFUSAL_IDENTITY')
        if refusal.get('invocation_ref') != row['negative_invocation_ref']:
            raise ValueError('OPEN_FROZEN_NEGATIVE_BINDING')
        invocation, _ = _original(doc, raw, refusal['invocation_ref'])
        if invocation.get('schema') != 'researchos.w05.negative-invocation.v3' or any(invocation.get(key) != value for key, value in expected.items()) or invocation.get('root_grant_ref') != context['root_grant_ref']:
            raise ValueError('OPEN_NEGATIVE_INVOCATION_IDENTITY')
        if invocation.get('scope_ref') not in scope_refs:
            raise ValueError('OPEN_NEGATIVE_SCOPE_NOT_ROOT_ISSUED')
        scope, _ = _original(doc, raw, invocation['scope_ref'])
        if scope.get('schema') != 'researchos.w05.a04-negative-scope.v3' or any(scope.get(key) != value for key, value in expected.items()) or scope.get('root_grant_ref') != context['root_grant_ref'] or invocation.get('scope') != scope:
            raise ValueError('OPEN_NEGATIVE_SCOPE_IDENTITY')
        for key in ('argv', 'cwd', 'env_names', 'initial_tool_input', 'producer_ref'):
            if key not in scope or invocation.get(key) != scope[key]:
                raise ValueError('OPEN_NEGATIVE_SCOPE_ABI')
        _nonempty(invocation['argv'], 'negative argv', list)
        _nonempty(invocation['cwd'], 'negative cwd')
        if invocation['cwd'] != context['worktree'] or type(invocation['env_names']) is not list or any(type(v) is not str or not v for v in invocation['env_names']):
            raise ValueError('OPEN_NEGATIVE_CURRENT_WORKTREE')
        _native_exit(invocation.get('native_exit'), 'refusal native exit')
        pair, _ = _original(doc, raw, invocation['root_tool_pair_ref'])
        closed = _root_pair(pair, scope)
        if closed['actual_launcher_native_exit'] != invocation['native_exit'] or invocation['native_exit'] == 0:
            raise ValueError('OPEN_REFUSAL_ACTUAL_NONZERO')
        response, _ = _original(doc, raw, refusal['original_response_ref'])
        if response.get('schema') != 'researchos.w05.original-negative-response.v3' or any(response.get(key) != value for key, value in expected.items()) or response.get('scope_ref') != invocation['scope_ref'] or response.get('status') not in ('REJECTED', 'BLOCKED', 'DENIED'):
            raise ValueError('OPEN_ORIGINAL_REFUSAL_RESPONSE')
        # These fields must occur in the Root-observed terminal stdout itself.
        # The response/scope precede the pair and invocation; no backward hash cycle.
        if closed.get('negative_identity') != expected or closed.get('negative_scope_ref') != invocation['scope_ref'] or closed.get('actual_refusal_response') != response:
            raise ValueError('OPEN_REFUSAL_NOT_FROM_ORIGINAL_TERMINAL')



def _profile_io(api, reader, context):
    paths = context['product_original_paths']
    def raw(reference):
        if type(reference) is not dict or set(reference) != {'path', 'sha256'} or reference['path'] not in paths:
            raise ValueError('OPEN_ROOT_CAPTURED_WHOLE_ORIGINAL')
        return _ref(api, reader, reference).read_bytes()
    def doc(reference):
        return _json_original(raw(reference))
    return doc, raw


def _live_gate(api, reader, context, row, invocation):
    doc, raw = _profile_io(api, reader, context)
    return verify_live_originals(doc, raw, context, row, invocation, invocation['_scope'])


def _grant_original(api, reader, context):
    observation = _doc(api, reader, context['root_grant_issuance_ref'])
    api.require(observation.get('schema') == 'researchos.w05.original-root-grant-issuance.v2' and
                observation.get('actor_id') == 'codex:/root' and
                observation.get('run_id') == context['run_id'] and
                observation.get('grant_ref') == context['root_grant_ref'],
                'OPEN_ORIGINAL_ROOT_GRANT', 'A04')
    api.require(type(observation.get('original_input')) is dict and
                type(observation.get('original_result')) is dict and
                type(observation['original_result'].get('exit_code')) is int and
                observation['original_result']['exit_code'] == 0,
                'OPEN_ORIGINAL_ROOT_GRANT_TOOL_RESULT', 'A04')
    output = api.text(observation['original_result'].get('output'), 'original Root grant output')
    rows = [_json_original(line) for line in output.splitlines() if line.startswith('{')]
    api.require(len(rows) == 1 and rows[0].get('grant_ref') == context['root_grant_ref'],
                'OPEN_ORIGINAL_ROOT_GRANT_OUTPUT', 'A04')
    producer = _ref(api, reader, observation['producer_ref'])
    api.require(any(reader.ref(ref) == producer for ref in context['version_vector']['tool_files']),
                'OPEN_ROOT_GRANT_PRODUCER_PIN', 'A04')


def _delivery_original(api, reader, issuance, review):
    observation = _doc(api, reader, issuance['original_delivery_observation_ref'])
    api.require(observation.get('schema') == 'researchos.w05.original-review-delivery.v2' and
                observation.get('actor_id') == review['reviewer_id'] and
                observation.get('tool') == 'collaboration.send_message' and
                observation.get('review_ref') == issuance['review_ref'],
                'OPEN_ORIGINAL_NONAUTHOR_DELIVERY', 'A04')
    original_input = api.obj(observation.get('original_input'), 'original delivery input')
    original_result = api.obj(observation.get('original_result'), 'original delivery result')
    api.require(original_input.get('target') in ('/root', 'codex:/root') and
                original_result and not original_result.get('isError') and
                issuance['review_ref']['sha256'] in api.text(original_input.get('message'), 'original delivery message'),
                'OPEN_ORIGINAL_NONAUTHOR_DELIVERY_RESULT', 'A04')


def verify_capture_bundle(doc, raw, bundle, selector):
    if selector not in ('A04', *GATES):
        raise ValueError('OPEN_EXACT_SELECTOR')
    if type(bundle) is not dict or bundle.get('schema') != 'researchos.w05.live-dispatch-bundle.v1' or bundle.get('mode') != 'LIVE_WINDOWS' or bundle.get('task_id') != 'W05' or bundle.get('case_id') != 'A04':
        raise ValueError('OPEN_CURRENT_LIVE_BUNDLE')
    context = dict(bundle, product_original_paths={ref['path'] for ref in bundle['product_original_refs']})
    grant = doc(bundle['root_grant_ref'])
    issuance = doc(bundle['root_grant_issuance_ref'])
    if grant.get('run_id') != bundle['run_id'] or grant.get('decision') != 'GRANTED' or grant.get('mode') != 'LIVE_WINDOWS' or grant.get('selected_runtime') != bundle['selected_runtime'] or grant.get('fixed_model') != bundle['fixed_model'] or issuance.get('grant_ref') != bundle['root_grant_ref']:
        raise ValueError('OPEN_ROOT_ORIGINAL_GRANT')
    accounting = bundle.get('accounting')
    if type(accounting) is not dict or set(accounting) != {'mode', 'status', 'amount_usd', 'source_refs'} or accounting['mode'] not in ('UNLIMITED_AMOUNT', 'CAPPED') or type(accounting['source_refs']) is not list or not ((accounting['status'] == 'UNKNOWN' and accounting['amount_usd'] is None) or (accounting['status'] == 'RECORDED' and type(accounting['amount_usd']) in (int, float) and accounting['amount_usd'] >= 0 and accounting['source_refs'])):
        raise ValueError('OPEN_UNKNOWN_AMOUNT_IS_NULL')
    if grant.get('accounting_mode') != accounting['mode'] or issuance.get('schema') != 'researchos.w05.original-root-grant-issuance.v2' or issuance.get('actor_id') != 'codex:/root' or issuance.get('run_id') != bundle['run_id'] or type(issuance.get('original_input')) is not dict or type(issuance.get('original_result')) is not dict or type(issuance['original_result'].get('exit_code')) is not int or issuance['original_result']['exit_code'] != 0:
        raise ValueError('OPEN_ROOT_GRANT_ACTUAL_ISSUANCE')
    observed = [_json_original(line) for line in _nonempty(issuance['original_result'].get('output'), 'Root grant original output').splitlines() if line.startswith('{')]
    if len(observed) != 1 or observed[0].get('grant_ref') != bundle['root_grant_ref']:
        raise ValueError('OPEN_ROOT_GRANT_ORIGINAL_OUTPUT')
    originals = context['product_original_paths']
    if not originals or len(originals) != len(bundle['product_original_refs']):
        raise ValueError('OPEN_WHOLE_ORIGINALS')
    def whole_raw(reference):
        if type(reference) is not dict or set(reference) != {'path', 'sha256'} or reference['path'] not in originals:
            raise ValueError('OPEN_WHOLE_ORIGINAL_MEMBERSHIP')
        return raw(reference)
    def whole_doc(reference):
        return _json_original(whole_raw(reference))
    by_lane = {}
    for item in bundle['invocations']:
        lane = item['lane']
        if lane in by_lane:
            raise ValueError('OPEN_DUPLICATE_LANE')
        invocation, scope = doc(item['invocation_ref']), doc(item['scope_ref'])
        if invocation.get('schema') != 'researchos.w05.live-invocation.v1' or invocation.get('run_id') != bundle['run_id'] or invocation.get('lane') != lane or invocation.get('root_grant_ref') != bundle['root_grant_ref'] or scope.get('schema') != 'researchos.w05.a04-live-scope.v1' or scope.get('root_grant_ref') != bundle['root_grant_ref']:
            raise ValueError('OPEN_CURRENT_INVOCATION')
        by_lane[lane] = (invocation, scope)
    if set(by_lane) != set(SCENARIOS) | set(EXTRA.values()):
        raise ValueError('OPEN_EIGHT_ACTUAL_LANES')
    rows = bundle['assertions']
    if len(rows) != 6 or {row['id'] for row in rows} != set(IDS):
        raise ValueError('OPEN_SIX_FROZEN_ASSERTIONS')
    for row in rows:
        if row.get('status') != 'PASS' or not row.get('actual') or type(row.get('raw_evidence_refs')) is not list or not row['raw_evidence_refs']:
            raise ValueError('OPEN_ASSERTION_RESULT')
        proof = doc(row['raw_evidence_refs'][0])
        if type(proof) is not dict or proof.get('schema') != 'researchos.w05.a04-raw-observation.v1' or proof.get('assertion_id') != row['id'] or proof.get('run_id') != bundle['run_id'] or proof.get('lane') != row['lane'] or type(proof.get('facts')) is not dict or not proof['facts'] or type(proof.get('fact_source_refs')) is not dict or set(proof['facts']) != set(proof['fact_source_refs']):
            raise ValueError('OPEN_EMPTY_OR_UNBOUND_FACT_PROJECTION')
        for key, reference in proof['fact_source_refs'].items():
            if reference.get('path') not in originals or reference.get('path') == row['raw_evidence_refs'][0]['path'] or doc(reference) != proof['facts'][key]:
                raise ValueError('OPEN_UNBOUND_FACT_SOURCE')
        if row['lane'] != ASSERTION_LANES[row['id']]:
            raise ValueError('OPEN_FROZEN_ASSERTION_LANE')
        invocation, scope = by_lane[row['lane']]
        verify_live_originals(whole_doc, whole_raw, context, row, invocation, scope)
        verify_refusal(whole_doc, whole_raw, context, row)
    # These four LIVE decoders are intentionally unsupported until their
    # real producer ABI is frozen; verify_live_originals returns OPEN first.
    # A generic raw gate PASS list can never substitute for them.
    raise ValueError('OPEN_H08_P01_U02_CURRENT_RAW_GATE_DECODERS_REQUIRED')


# Exact public schema assertion closure; SOURCE data, not dynamically loaded code.
PUBLIC_SCHEMAS = {'domain': {'AcceptanceContract': {'type': 'object', 'properties': {'contract_hash': {'$ref': 'domain:Digest'}, 'contract_revision': {'$ref': 'domain:Revision'}, 'checks': {'type': 'array', 'items': {'$ref': 'domain:CheckSpec'}, 'minItems': 1}, 'require_independent_verifier': {'const': True}, 'version_policy': {'const': 'EXACT'}, 'frozen_at': {'$ref': 'domain:UtcTime'}}, 'required': ['contract_hash', 'contract_revision', 'checks', 'require_independent_verifier', 'version_policy', 'frozen_at'], 'additionalProperties': False}, 'Amount': {'type': 'string', 'pattern': '^(0|[1-9][0-9]*)(\\.[0-9]+)?$'}, 'Artifact': {'type': 'object', 'properties': {'id': {'$ref': 'domain:Id'}, 'project_id': {'$ref': 'domain:Id'}, 'revision': {'$ref': 'domain:Revision'}, 'created_at': {'$ref': 'domain:UtcTime'}, 'updated_at': {'$ref': 'domain:UtcTime'}, 'run_id': {'anyOf': [{'$ref': 'domain:Id'}, {'type': 'null'}]}, 'kind': {'type': 'string', 'enum': ['SOURCE_SNAPSHOT', 'CODE', 'REPORT', 'LOG', 'DATASET', 'TEST_RESULT', 'CONTEXT_EXPORT', 'SKILL', 'CHECKPOINT', 'MANIFEST']}, 'evidence_kind': {'$ref': 'domain:EvidenceKind'}, 'validity': {'$ref': 'domain:Validity'}, 'measurement_mode': {'$ref': 'domain:MeasurementMode'}, 'content_hash': {'$ref': 'domain:Digest'}, 'storage_key': {'type': 'string', 'minLength': 1}, 'media_type': {'type': 'string', 'minLength': 1}, 'byte_size': {'type': 'integer', 'minimum': 0}, 'input_refs': {'type': 'array', 'items': {'$ref': 'domain:VersionRef'}, 'minItems': 0}, 'source_refs': {'type': 'array', 'items': {'$ref': 'domain:VersionRef'}, 'minItems': 0}, 'produced_by': {'$ref': 'domain:Id'}, 'sealed_at': {'$ref': 'domain:UtcTime'}, 'access_class': {'type': 'string', 'enum': ['PROJECT', 'VERIFIER_ONLY']}}, 'required': ['id', 'project_id', 'revision', 'created_at', 'updated_at', 'run_id', 'kind', 'evidence_kind', 'validity', 'measurement_mode', 'content_hash', 'storage_key', 'media_type', 'byte_size', 'input_refs', 'source_refs', 'produced_by', 'sealed_at', 'access_class'], 'additionalProperties': False}, 'CheckSpec': {'type': 'object', 'properties': {'check_id': {'$ref': 'domain:Id'}, 'kind': {'type': 'string', 'enum': ['DETERMINISTIC', 'MODEL_RUBRIC', 'PREFERENCE']}, 'required': {'type': 'boolean'}, 'expected': {'type': 'string', 'minLength': 1}, 'command_key': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}, 'rubric_ref': {'anyOf': [{'$ref': 'domain:VersionRef'}, {'type': 'null'}]}, 'qualification_id': {'anyOf': [{'$ref': 'domain:Id'}, {'type': 'null'}]}, 'not_applicable_reason': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}}, 'required': ['check_id', 'kind', 'required', 'expected', 'command_key', 'rubric_ref', 'qualification_id', 'not_applicable_reason'], 'additionalProperties': False}, 'Currency': {'type': 'string', 'pattern': '^[A-Z]{3}$'}, 'Digest': {'type': 'string', 'pattern': '^sha256:[0-9a-f]{64}$'}, 'EvidenceKind': {'type': 'string', 'enum': ['OBSERVED', 'SIMULATED', 'GENERATED']}, 'Id': {'type': 'string', 'minLength': 1, 'maxLength': 160, 'pattern': '^[A-Za-z0-9][A-Za-z0-9_.:-]*$'}, 'MeasurementMode': {'type': 'string', 'enum': ['FIXTURE', 'LIVE']}, 'Money': {'type': 'object', 'properties': {'amount': {'$ref': 'domain:Amount'}, 'currency': {'$ref': 'domain:Currency'}}, 'required': ['amount', 'currency'], 'additionalProperties': False}, 'ProjectBinding': {'type': 'object', 'properties': {'route': {'type': 'string', 'enum': ['MU_FORK', 'PI_COMPOSE', 'GAP_ONLY_COMPOSE']}, 'upstream_project_id': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}, 'upstream_goal_id': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}, 'upstream_task_id': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}}, 'required': ['route', 'upstream_project_id', 'upstream_goal_id', 'upstream_task_id'], 'additionalProperties': False}, 'ResourceRequest': {'type': 'object', 'properties': {'id': {'$ref': 'domain:Id'}, 'project_id': {'$ref': 'domain:Id'}, 'revision': {'$ref': 'domain:Revision'}, 'created_at': {'$ref': 'domain:UtcTime'}, 'updated_at': {'$ref': 'domain:UtcTime'}, 'category': {'type': 'string', 'enum': ['RATE_LIMIT', 'QUOTA', 'CREDENTIAL', 'DEVICE', 'PERMISSION', 'BUSINESS_CHOICE']}, 'account_ref': {'anyOf': [{'$ref': 'domain:Id'}, {'type': 'null'}]}, 'reason_code': {'type': 'string', 'minLength': 1}, 'summary': {'type': 'string', 'minLength': 1}, 'dedup_key': {'$ref': 'domain:Digest'}, 'status': {'type': 'string', 'enum': ['OPEN', 'ACKNOWLEDGED', 'RESOLVED', 'CANCELLED']}, 'blocked_task_ids': {'type': 'array', 'items': {'$ref': 'domain:Id'}, 'minItems': 0}, 'continuable_task_ids': {'type': 'array', 'items': {'$ref': 'domain:Id'}, 'minItems': 0}, 'completed_artifact_refs': {'type': 'array', 'items': {'$ref': 'domain:VersionRef'}, 'minItems': 0}, 'requested_capability': {'type': 'string', 'minLength': 1}, 'estimated_cost': {'anyOf': [{'$ref': 'domain:Money'}, {'type': 'null'}]}, 'cost_known': {'type': 'boolean'}, 'resume_checkpoint_ref': {'anyOf': [{'$ref': 'domain:VersionRef'}, {'type': 'null'}]}, 'resolved_by': {'anyOf': [{'$ref': 'domain:Id'}, {'type': 'null'}]}}, 'required': ['id', 'project_id', 'revision', 'created_at', 'updated_at', 'category', 'account_ref', 'reason_code', 'summary', 'dedup_key', 'status', 'blocked_task_ids', 'continuable_task_ids', 'completed_artifact_refs', 'requested_capability', 'estimated_cost', 'cost_known', 'resume_checkpoint_ref', 'resolved_by'], 'additionalProperties': False}, 'Revision': {'type': 'integer', 'minimum': 1}, 'Run': {'type': 'object', 'properties': {'id': {'$ref': 'domain:Id'}, 'project_id': {'$ref': 'domain:Id'}, 'revision': {'$ref': 'domain:Revision'}, 'created_at': {'$ref': 'domain:UtcTime'}, 'updated_at': {'$ref': 'domain:UtcTime'}, 'task_id': {'$ref': 'domain:Id'}, 'runtime_id': {'$ref': 'domain:Id'}, 'executor_principal_id': {'$ref': 'domain:Id'}, 'attempt': {'type': 'integer', 'minimum': 1}, 'status': {'type': 'string', 'enum': ['QUEUED', 'STARTING', 'RUNNING', 'CANCEL_REQUESTED', 'SETTLED', 'FAILED', 'CANCELLED', 'LOST', 'RECONCILING']}, 'input_refs': {'type': 'array', 'items': {'$ref': 'domain:VersionRef'}, 'minItems': 0}, 'context_bundle_id': {'$ref': 'domain:Id'}, 'external_run_id': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}, 'workspace_snapshot_id': {'$ref': 'domain:Id'}, 'lease_token_hash': {'$ref': 'domain:Digest'}, 'lease_expires_at': {'$ref': 'domain:UtcTime'}, 'heartbeat_at': {'anyOf': [{'$ref': 'domain:UtcTime'}, {'type': 'null'}]}, 'checkpoint_artifact_id': {'anyOf': [{'$ref': 'domain:Id'}, {'type': 'null'}]}, 'result_artifact_ids': {'type': 'array', 'items': {'$ref': 'domain:Id'}, 'minItems': 0}, 'execution_report': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}, 'exit_code': {'anyOf': [{'type': 'integer'}, {'type': 'null'}]}, 'runtime_settled_at': {'anyOf': [{'$ref': 'domain:UtcTime'}, {'type': 'null'}]}, 'cancel_requested_at': {'anyOf': [{'$ref': 'domain:UtcTime'}, {'type': 'null'}]}, 'cancel_confirmed_at': {'anyOf': [{'$ref': 'domain:UtcTime'}, {'type': 'null'}]}, 'children_stopped': {'anyOf': [{'type': 'boolean'}, {'type': 'null'}]}, 'queue_empty': {'anyOf': [{'type': 'boolean'}, {'type': 'null'}]}, 'started_at': {'anyOf': [{'$ref': 'domain:UtcTime'}, {'type': 'null'}]}, 'ended_at': {'anyOf': [{'$ref': 'domain:UtcTime'}, {'type': 'null'}]}, 'lease_epoch': {'type': 'integer', 'minimum': 1}}, 'required': ['id', 'project_id', 'revision', 'created_at', 'updated_at', 'task_id', 'runtime_id', 'executor_principal_id', 'attempt', 'status', 'input_refs', 'context_bundle_id', 'external_run_id', 'workspace_snapshot_id', 'lease_token_hash', 'lease_expires_at', 'heartbeat_at', 'checkpoint_artifact_id', 'result_artifact_ids', 'execution_report', 'exit_code', 'runtime_settled_at', 'cancel_requested_at', 'cancel_confirmed_at', 'children_stopped', 'queue_empty', 'started_at', 'ended_at', 'lease_epoch'], 'additionalProperties': False}, 'Stage': {'type': 'string', 'enum': ['discovery', 'verification', 'experiment', 'review', 'delivery', 'follow_up']}, 'StopPolicy': {'type': 'object', 'properties': {'wall_time_seconds': {'type': 'integer', 'minimum': 1}, 'max_attempts': {'type': 'integer', 'minimum': 1}, 'max_parallel_runs': {'type': 'integer', 'minimum': 1}, 'stop_conditions': {'type': 'array', 'items': {'type': 'string', 'minLength': 1}, 'minItems': 1}}, 'required': ['wall_time_seconds', 'max_attempts', 'max_parallel_runs', 'stop_conditions'], 'additionalProperties': False}, 'Task': {'type': 'object', 'properties': {'id': {'$ref': 'domain:Id'}, 'project_id': {'$ref': 'domain:Id'}, 'revision': {'$ref': 'domain:Revision'}, 'created_at': {'$ref': 'domain:UtcTime'}, 'updated_at': {'$ref': 'domain:UtcTime'}, 'goal_id': {'$ref': 'domain:Id'}, 'title': {'type': 'string', 'minLength': 1}, 'task_type': {'type': 'string', 'minLength': 1}, 'stage': {'$ref': 'domain:Stage'}, 'status': {'$ref': 'domain:TaskStatus'}, 'dependency_task_ids': {'type': 'array', 'items': {'$ref': 'domain:Id'}, 'minItems': 0}, 'requirement_refs': {'type': 'array', 'items': {'$ref': 'domain:VersionRef'}, 'minItems': 0}, 'input_refs': {'type': 'array', 'items': {'$ref': 'domain:VersionRef'}, 'minItems': 0}, 'context_bundle_id': {'anyOf': [{'$ref': 'domain:Id'}, {'type': 'null'}]}, 'acceptance_contract': {'$ref': 'domain:AcceptanceContract'}, 'assigned_principal_id': {'anyOf': [{'$ref': 'domain:Id'}, {'type': 'null'}]}, 'active_run_id': {'anyOf': [{'$ref': 'domain:Id'}, {'type': 'null'}]}, 'output_artifact_ids': {'type': 'array', 'items': {'$ref': 'domain:Id'}, 'minItems': 0}, 'acceptance_id': {'anyOf': [{'$ref': 'domain:Id'}, {'type': 'null'}]}, 'blocking_conflict_ids': {'type': 'array', 'items': {'$ref': 'domain:Id'}, 'minItems': 0}, 'no_progress_record_id': {'$ref': 'domain:Id'}, 'stop_policy': {'$ref': 'domain:StopPolicy'}, 'binding': {'$ref': 'domain:ProjectBinding'}}, 'required': ['id', 'project_id', 'revision', 'created_at', 'updated_at', 'goal_id', 'title', 'task_type', 'stage', 'status', 'dependency_task_ids', 'requirement_refs', 'input_refs', 'context_bundle_id', 'acceptance_contract', 'assigned_principal_id', 'active_run_id', 'output_artifact_ids', 'acceptance_id', 'blocking_conflict_ids', 'no_progress_record_id', 'stop_policy', 'binding'], 'additionalProperties': False}, 'TaskStatus': {'type': 'string', 'enum': ['DRAFT', 'READY', 'RUNNING', 'EXECUTION_REPORTED', 'VERIFYING', 'ACCEPTED', 'FAILED', 'BLOCKED', 'CANCELLED', 'NEEDS_REVALIDATION', 'DEFERRED_NO_PROGRESS']}, 'UtcTime': {'type': 'string', 'format': 'date-time', 'pattern': 'Z$'}, 'Validity': {'type': 'string', 'enum': ['CURRENT', 'STALE', 'REVOKED']}, 'VersionRef': {'type': 'object', 'properties': {'entity_type': {'type': 'string', 'enum': ['ProjectProfile', 'ProjectState', 'Requirement', 'Goal', 'Task', 'Run', 'Artifact', 'Evidence', 'ResearchCycle', 'Experiment', 'DecisionReceipt', 'Qualification', 'ContextBundle', 'ChangeProposal', 'ImpactLink', 'BudgetPolicy', 'RunPolicy', 'ResourceRequest', 'MilestoneRelease', 'ProgressProjection', 'SkillVersion', 'SystemCandidate', 'AcceptanceReceipt', 'AgentMessage', 'SourceCursor', 'BudgetLedgerEntry', 'NoProgressRecord', 'RuntimeRegistration', 'Notification', 'Conflict', 'EventEnvelope']}, 'id': {'$ref': 'domain:Id'}, 'revision': {'$ref': 'domain:Revision'}, 'content_hash': {'anyOf': [{'$ref': 'domain:Digest'}, {'type': 'null'}]}}, 'required': ['entity_type', 'id', 'revision', 'content_hash'], 'additionalProperties': False}}, 'client': {'ArtifactEventPayload': {'type': 'object', 'properties': {'artifact_ref': {'$ref': 'client:ArtifactRef'}, 'availability': {'enum': ['AVAILABLE', 'SUPERSEDED', 'REVOKED']}}, 'required': ['artifact_ref', 'availability'], 'additionalProperties': False}, 'ArtifactRef': {'allOf': [{'$ref': 'domain:VersionRef'}, {'properties': {'entity_type': {'const': 'Artifact'}, 'content_hash': {'type': 'string', 'pattern': '^sha256:[a-f0-9]{64}$'}}}]}, 'BootstrapEventPayload': {'type': 'object', 'properties': {'project_id': {'type': 'string', 'minLength': 1}, 'stage': {'enum': ['LOCAL_INVENTORY', 'RESEARCH', 'REUSE_DECISION', 'IMPLEMENTATION']}, 'status': {'enum': ['STARTED', 'RUNNING', 'BLOCKED', 'COMPLETED', 'FAILED']}, 'task_id': {'type': 'string', 'minLength': 1}, 'artifact_refs': {'type': 'array', 'items': {'$ref': 'client:ArtifactRef'}, 'maxItems': 100}, 'resource_request_id': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}}, 'required': ['project_id', 'stage', 'status', 'task_id', 'artifact_refs', 'resource_request_id'], 'additionalProperties': False}, 'CheckpointEventPayload': {'type': 'object', 'properties': {'checkpoint_artifact_ref': {'$ref': 'client:ArtifactRef'}, 'through_sequence': {'type': 'integer', 'minimum': 0}, 'resume_mode': {'enum': ['NATIVE_RESUME', 'CONTEXT_REBUILD']}, 'requires_explicit_user': {'type': 'boolean'}}, 'required': ['checkpoint_artifact_ref', 'through_sequence', 'resume_mode', 'requires_explicit_user'], 'additionalProperties': False}, 'ErrorEventPayload': {'$ref': 'client:ProtocolError'}, 'GoalStateEventPayload': {'type': 'object', 'properties': {'goal_id': {'type': 'string', 'minLength': 1}, 'status': {'type': 'string', 'enum': ['DRAFT', 'ACTIVE', 'PAUSED', 'VERIFYING', 'ACCEPTED', 'BLOCKED', 'CANCELLED', 'NEEDS_REVALIDATION']}, 'revision': {'type': 'integer', 'minimum': 1}, 'accepted_artifact_refs': {'type': 'array', 'items': {'$ref': 'client:ArtifactRef'}, 'maxItems': 100}}, 'required': ['goal_id', 'status', 'revision', 'accepted_artifact_refs'], 'additionalProperties': False}, 'HandoffEventPayload': {'type': 'object', 'properties': {'previous_client_id': {'type': 'string', 'minLength': 1}, 'target_client_id': {'type': 'string', 'minLength': 1}, 'previous_epoch': {'type': 'integer', 'minimum': 1}, 'writer': {'$ref': 'client:WriterLease'}, 'effective_at': {'type': 'string', 'format': 'date-time'}}, 'required': ['previous_client_id', 'target_client_id', 'previous_epoch', 'writer', 'effective_at'], 'additionalProperties': False}, 'JudgeEventPayload': {'type': 'object', 'properties': {'purpose': {'type': 'string', 'minLength': 1}, 'mode': {'enum': ['SHADOW', 'ADVISORY', 'BOUNDED_AUTO']}, 'actual_status': {'enum': ['NOT_RUN', 'RUNNING', 'SUCCEEDED', 'BLOCKED', 'FAILED']}, 'decision_receipt_ref': {'anyOf': [{'$ref': 'domain:VersionRef'}, {'type': 'null'}]}, 'summary': {'type': 'string'}}, 'required': ['purpose', 'mode', 'actual_status', 'decision_receipt_ref', 'summary'], 'additionalProperties': False}, 'MessageEventPayload': {'type': 'object', 'properties': {'message_id': {'type': 'string', 'minLength': 1}, 'role': {'enum': ['USER', 'ASSISTANT', 'SYSTEM']}, 'phase': {'enum': ['START', 'DELTA', 'END']}, 'part_index': {'type': 'integer', 'minimum': 0}, 'content_offset_utf8_bytes': {'type': 'integer', 'minimum': 0}, 'text': {'type': 'string', 'maxLength': 16384}}, 'required': ['message_id', 'role', 'phase', 'part_index', 'content_offset_utf8_bytes', 'text'], 'additionalProperties': False, 'allOf': [{'if': {'properties': {'phase': {'const': 'START'}}}, 'then': {'properties': {'content_offset_utf8_bytes': {'const': 0}, 'text': {'const': ''}}}}, {'if': {'properties': {'phase': {'const': 'END'}}}, 'then': {'properties': {'text': {'const': ''}}}}, {'if': {'properties': {'phase': {'const': 'DELTA'}}}, 'then': {'properties': {'text': {'type': 'string', 'minLength': 1, 'maxLength': 16384}}}}]}, 'PermissionActionScope': {'type': 'object', 'properties': {'project_id': {'type': 'string', 'minLength': 1}, 'task_id': {'type': 'string', 'minLength': 1}, 'run_id': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}, 'tool_name': {'type': 'string', 'minLength': 1}, 'arguments_artifact_ref': {'$ref': 'client:ArtifactRef'}, 'workspace_ref': {'type': 'string', 'minLength': 1}, 'allowed_relative_paths': {'type': 'array', 'items': {'$ref': 'client:RelativePath'}, 'minItems': 0}, 'input_refs': {'type': 'array', 'items': {'$ref': 'domain:VersionRef'}, 'minItems': 1}, 'model_config_ref': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}, 'issued_at': {'type': 'string', 'format': 'date-time'}, 'expires_at': {'type': 'string', 'format': 'date-time'}, 'max_uses': {'const': 1}, 'authority': {'enum': ['USER_DECIDABLE', 'POLICY_DENIED']}}, 'required': ['project_id', 'task_id', 'run_id', 'tool_name', 'arguments_artifact_ref', 'workspace_ref', 'allowed_relative_paths', 'input_refs', 'model_config_ref', 'issued_at', 'expires_at', 'max_uses', 'authority'], 'additionalProperties': False}, 'PermissionPrompt': {'type': 'object', 'properties': {'request': {'allOf': [{'$ref': 'domain:ResourceRequest'}, {'properties': {'category': {'const': 'PERMISSION'}}}]}, 'task_id': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}, 'run_id': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}, 'action_digest': {'type': 'string', 'pattern': '^sha256:[a-f0-9]{64}$'}, 'action_artifact_ref': {'$ref': 'client:ArtifactRef'}, 'allowed_responses': {'type': 'array', 'items': {'enum': ['ALLOW_ONCE', 'DENY']}, 'maxItems': 2}, 'policy_allows_user_decision': {'type': 'boolean'}, 'action_scope': {'$ref': 'client:PermissionActionScope'}}, 'required': ['request', 'task_id', 'run_id', 'action_digest', 'action_artifact_ref', 'allowed_responses', 'policy_allows_user_decision', 'action_scope'], 'additionalProperties': False}, 'PermissionRequiredEventPayload': {'$ref': 'client:PermissionPrompt'}, 'PermissionResolvedEventPayload': {'$ref': 'client:RespondPermissionResult'}, 'ProtocolError': {'type': 'object', 'properties': {'code': {'enum': ['INVALID_REQUEST', 'UNSUPPORTED_PROTOCOL', 'UNSUPPORTED_METHOD', 'UNAUTHENTICATED', 'FORBIDDEN', 'POLICY_DENIED', 'NOT_FOUND', 'NOT_IMPLEMENTED', 'HOST_UNAVAILABLE', 'STALE_REVISION', 'STALE_WRITER_EPOCH', 'WRITER_BUSY', 'LEASE_EXPIRED', 'SESSION_BUSY', 'SESSION_ARCHIVED', 'COMMAND_ID_CONFLICT', 'COMMAND_PENDING', 'CURSOR_EXPIRED', 'CURSOR_INVALID', 'PATH_OUT_OF_SCOPE', 'WORKSPACE_REVOKED', 'SELECTION_EXPIRED', 'SELECTION_ALREADY_USED', 'CONTENT_CONFLICT', 'CONTENT_TOO_LARGE', 'UNSUPPORTED_CONTENT', 'NOT_A_REPOSITORY', 'EXTERNAL_WRITE_RACE', 'ARTIFACT_IMMUTABLE', 'CREDENTIAL_MISSING', 'CREDENTIAL_REVOKED', 'CONFIG_CONFLICT', 'MODEL_UNAVAILABLE', 'PROVIDER_AUTH_FAILED', 'PROVIDER_RATE_LIMITED', 'PROVIDER_TIMEOUT', 'NETWORK_UNAVAILABLE', 'RESOURCE_BLOCKED', 'CANCEL_UNCONFIRMED', 'ALREADY_TERMINAL', 'INTERNAL_ERROR', 'VERSION_CONFLICT']}, 'message': {'type': 'string', 'minLength': 1}, 'retryable': {'type': 'boolean'}, 'recovery': {'enum': ['FIX_INPUT', 'REAUTHENTICATE_OS_USER', 'REFRESH_SNAPSHOT', 'ACQUIRE_WRITER', 'WAIT_FOR_SETTLEMENT', 'RECONFIGURE', 'RESOLVE_RESOURCE', 'RETRY_SAME_COMMAND', 'STOP_AND_REPORT']}, 'current_revision': {'anyOf': [{'type': 'integer', 'minimum': 1}, {'type': 'null'}]}, 'current_writer_epoch': {'anyOf': [{'type': 'integer', 'minimum': 1}, {'type': 'null'}]}, 'resource_request_id': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}, 'retry_after_ms': {'anyOf': [{'type': 'integer', 'minimum': 0}, {'type': 'null'}]}, 'correlation_id': {'type': 'string', 'minLength': 1}}, 'required': ['code', 'message', 'retryable', 'recovery', 'current_revision', 'current_writer_epoch', 'resource_request_id', 'retry_after_ms', 'correlation_id'], 'additionalProperties': False}, 'RelativePath': {'type': 'string', 'minLength': 1, 'maxLength': 4096, 'pattern': '^(?![\\\\/])(?![A-Za-z]:)(?!.*(?:^|[\\\\/])\\.\\.(?:[\\\\/]|$))(?!.*\\x00).+$'}, 'RespondPermissionResult': {'type': 'object', 'properties': {'request': {'$ref': 'domain:ResourceRequest'}, 'decision': {'enum': ['ALLOW_ONCE', 'DENY']}, 'resolution_artifact_ref': {'$ref': 'client:ArtifactRef'}, 'action_digest': {'type': 'string', 'pattern': '^sha256:[a-f0-9]{64}$'}, 'consumed': {'type': 'boolean'}, 'resumption_scheduled': {'type': 'boolean'}}, 'required': ['request', 'decision', 'resolution_artifact_ref', 'action_digest', 'consumed', 'resumption_scheduled'], 'additionalProperties': False}, 'RunStateEventPayload': {'type': 'object', 'properties': {'run_id': {'type': 'string', 'minLength': 1}, 'status': {'type': 'string', 'enum': ['QUEUED', 'STARTING', 'RUNNING', 'CANCEL_REQUESTED', 'SETTLED', 'FAILED', 'CANCELLED', 'LOST', 'RECONCILING']}, 'revision': {'type': 'integer', 'minimum': 1}, 'cancel_requested_at': {'anyOf': [{'type': 'string', 'format': 'date-time'}, {'type': 'null'}]}, 'cancel_confirmed_at': {'anyOf': [{'type': 'string', 'format': 'date-time'}, {'type': 'null'}]}, 'settled_at': {'anyOf': [{'type': 'string', 'format': 'date-time'}, {'type': 'null'}]}, 'children_stopped': {'anyOf': [{'type': 'boolean'}, {'type': 'null'}]}, 'queue_empty': {'anyOf': [{'type': 'boolean'}, {'type': 'null'}]}}, 'required': ['run_id', 'status', 'revision', 'cancel_requested_at', 'cancel_confirmed_at', 'settled_at', 'children_stopped', 'queue_empty'], 'additionalProperties': False}, 'SessionEvent': {'type': 'object', 'properties': {'event_id': {'type': 'string', 'minLength': 1}, 'session_id': {'type': 'string', 'minLength': 1}, 'sequence': {'type': 'integer', 'minimum': 1}, 'core_build_id': {'type': 'string', 'minLength': 1}, 'protocol_version': {'const': 'researchos-client/2'}, 'run_id': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}, 'command_id': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}, 'domain_event_id': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}, 'kind': {'enum': ['MESSAGE', 'TOOL_STARTED', 'TOOL_RESULT', 'JUDGE_DECISION', 'RUN_STATE', 'GOAL_STATE', 'ARTIFACT', 'USAGE', 'CHECKPOINT', 'CLIENT_HANDOFF', 'BOOTSTRAP_STATE', 'PERMISSION_REQUIRED', 'PERMISSION_RESOLVED', 'ERROR']}, 'payload': {'type': 'object'}}, 'required': ['event_id', 'session_id', 'sequence', 'core_build_id', 'protocol_version', 'run_id', 'command_id', 'domain_event_id', 'kind', 'payload'], 'additionalProperties': False, 'allOf': [{'if': {'properties': {'kind': {'const': 'MESSAGE'}}, 'required': ['kind']}, 'then': {'properties': {'payload': {'$ref': 'client:MessageEventPayload'}}}}, {'if': {'properties': {'kind': {'const': 'TOOL_STARTED'}}, 'required': ['kind']}, 'then': {'properties': {'payload': {'$ref': 'client:ToolStartedEventPayload'}}}}, {'if': {'properties': {'kind': {'const': 'TOOL_RESULT'}}, 'required': ['kind']}, 'then': {'properties': {'payload': {'$ref': 'client:ToolResultEventPayload'}}}}, {'if': {'properties': {'kind': {'const': 'JUDGE_DECISION'}}, 'required': ['kind']}, 'then': {'properties': {'payload': {'$ref': 'client:JudgeEventPayload'}}}}, {'if': {'properties': {'kind': {'const': 'RUN_STATE'}}, 'required': ['kind']}, 'then': {'properties': {'payload': {'$ref': 'client:RunStateEventPayload'}}}}, {'if': {'properties': {'kind': {'const': 'GOAL_STATE'}}, 'required': ['kind']}, 'then': {'properties': {'payload': {'$ref': 'client:GoalStateEventPayload'}}}}, {'if': {'properties': {'kind': {'const': 'ARTIFACT'}}, 'required': ['kind']}, 'then': {'properties': {'payload': {'$ref': 'client:ArtifactEventPayload'}}}}, {'if': {'properties': {'kind': {'const': 'USAGE'}}, 'required': ['kind']}, 'then': {'properties': {'payload': {'$ref': 'client:UsageEventPayload'}}}}, {'if': {'properties': {'kind': {'const': 'CHECKPOINT'}}, 'required': ['kind']}, 'then': {'properties': {'payload': {'$ref': 'client:CheckpointEventPayload'}}}}, {'if': {'properties': {'kind': {'const': 'CLIENT_HANDOFF'}}, 'required': ['kind']}, 'then': {'properties': {'payload': {'$ref': 'client:HandoffEventPayload'}}}}, {'if': {'properties': {'kind': {'const': 'BOOTSTRAP_STATE'}}, 'required': ['kind']}, 'then': {'properties': {'payload': {'$ref': 'client:BootstrapEventPayload'}}}}, {'if': {'properties': {'kind': {'const': 'PERMISSION_REQUIRED'}}, 'required': ['kind']}, 'then': {'properties': {'payload': {'$ref': 'client:PermissionRequiredEventPayload'}}}}, {'if': {'properties': {'kind': {'const': 'PERMISSION_RESOLVED'}}, 'required': ['kind']}, 'then': {'properties': {'payload': {'$ref': 'client:PermissionResolvedEventPayload'}}}}, {'if': {'properties': {'kind': {'const': 'ERROR'}}, 'required': ['kind']}, 'then': {'properties': {'payload': {'$ref': 'client:ErrorEventPayload'}}}}]}, 'ToolResultEventPayload': {'type': 'object', 'properties': {'tool_call_id': {'type': 'string', 'minLength': 1}, 'outcome': {'enum': ['SUCCEEDED', 'FAILED', 'CANCELLED', 'BLOCKED', 'UNKNOWN']}, 'summary': {'type': 'string'}, 'stdout_artifact_ref': {'anyOf': [{'$ref': 'client:ArtifactRef'}, {'type': 'null'}]}, 'stderr_artifact_ref': {'anyOf': [{'$ref': 'client:ArtifactRef'}, {'type': 'null'}]}, 'result_artifact_refs': {'type': 'array', 'items': {'$ref': 'client:ArtifactRef'}, 'maxItems': 100}}, 'required': ['tool_call_id', 'outcome', 'summary', 'stdout_artifact_ref', 'stderr_artifact_ref', 'result_artifact_refs'], 'additionalProperties': False}, 'ToolStartedEventPayload': {'type': 'object', 'properties': {'tool_call_id': {'type': 'string', 'minLength': 1}, 'parent_tool_call_id': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}, 'tool_name': {'type': 'string', 'minLength': 1}, 'input_summary': {'type': 'string'}, 'input_artifact_ref': {'anyOf': [{'$ref': 'client:ArtifactRef'}, {'type': 'null'}]}}, 'required': ['tool_call_id', 'parent_tool_call_id', 'tool_name', 'input_summary', 'input_artifact_ref'], 'additionalProperties': False}, 'UsageEventPayload': {'type': 'object', 'properties': {'ledger_entry_id': {'type': 'string', 'minLength': 1}, 'provider_usage_id': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}, 'input_tokens': {'anyOf': [{'type': 'integer', 'minimum': 0}, {'type': 'null'}]}, 'output_tokens': {'anyOf': [{'type': 'integer', 'minimum': 0}, {'type': 'null'}]}, 'money': {'anyOf': [{'$ref': 'domain:Money'}, {'type': 'null'}]}, 'cost_known': {'type': 'boolean'}}, 'required': ['ledger_entry_id', 'provider_usage_id', 'input_tokens', 'output_tokens', 'money', 'cost_known'], 'additionalProperties': False, 'allOf': [{'if': {'properties': {'cost_known': {'const': True}}}, 'then': {'properties': {'money': {'$ref': 'domain:Money'}}}, 'else': {'properties': {'money': {'type': 'null'}}}}]}, 'WriterLease': {'type': 'object', 'properties': {'client_id': {'type': 'string', 'minLength': 1}, 'epoch': {'type': 'integer', 'minimum': 1}, 'expires_at': {'type': 'string', 'format': 'date-time'}}, 'required': ['client_id', 'epoch', 'expires_at'], 'additionalProperties': False}}, 'persistence': {'AcceptanceContract': {'type': 'object', 'properties': {'contract_hash': {'$ref': 'persistence:Digest'}, 'contract_revision': {'$ref': 'persistence:Revision'}, 'checks': {'type': 'array', 'items': {'$ref': 'persistence:CheckSpec'}, 'minItems': 1}, 'require_independent_verifier': {'const': True}, 'version_policy': {'const': 'EXACT'}, 'frozen_at': {'$ref': 'persistence:UtcTime'}}, 'required': ['contract_hash', 'contract_revision', 'checks', 'require_independent_verifier', 'version_policy', 'frozen_at'], 'additionalProperties': False}, 'CheckSpec': {'type': 'object', 'properties': {'check_id': {'$ref': 'persistence:Id'}, 'kind': {'type': 'string', 'enum': ['DETERMINISTIC', 'MODEL_RUBRIC', 'PREFERENCE']}, 'required': {'type': 'boolean'}, 'expected': {'type': 'string', 'minLength': 1}, 'command_key': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}, 'rubric_ref': {'anyOf': [{'$ref': 'persistence:VersionRef'}, {'type': 'null'}]}, 'qualification_id': {'anyOf': [{'$ref': 'persistence:Id'}, {'type': 'null'}]}, 'not_applicable_reason': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}}, 'required': ['check_id', 'kind', 'required', 'expected', 'command_key', 'rubric_ref', 'qualification_id', 'not_applicable_reason'], 'additionalProperties': False}, 'Digest': {'type': 'string', 'pattern': '^sha256:[0-9a-f]{64}$'}, 'Id': {'type': 'string', 'minLength': 1, 'maxLength': 160, 'pattern': '^[A-Za-z0-9][A-Za-z0-9_.:-]*$'}, 'ProjectBinding': {'type': 'object', 'properties': {'route': {'type': 'string', 'enum': ['MU_FORK', 'PI_COMPOSE', 'GAP_ONLY_COMPOSE']}, 'upstream_project_id': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}, 'upstream_goal_id': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}, 'upstream_task_id': {'anyOf': [{'type': 'string', 'minLength': 1}, {'type': 'null'}]}}, 'required': ['route', 'upstream_project_id', 'upstream_goal_id', 'upstream_task_id'], 'additionalProperties': False}, 'Revision': {'type': 'integer', 'minimum': 1}, 'Stage': {'type': 'string', 'enum': ['discovery', 'verification', 'experiment', 'review', 'delivery', 'follow_up']}, 'StopPolicy': {'type': 'object', 'properties': {'wall_time_seconds': {'type': 'integer', 'minimum': 1}, 'max_attempts': {'type': 'integer', 'minimum': 1}, 'max_parallel_runs': {'type': 'integer', 'minimum': 1}, 'stop_conditions': {'type': 'array', 'items': {'type': 'string', 'minLength': 1}, 'minItems': 1}}, 'required': ['wall_time_seconds', 'max_attempts', 'max_parallel_runs', 'stop_conditions'], 'additionalProperties': False}, 'Task': {'type': 'object', 'properties': {'id': {'$ref': 'persistence:Id'}, 'project_id': {'$ref': 'persistence:Id'}, 'revision': {'$ref': 'persistence:Revision'}, 'created_at': {'$ref': 'persistence:UtcTime'}, 'updated_at': {'$ref': 'persistence:UtcTime'}, 'goal_id': {'$ref': 'persistence:Id'}, 'title': {'type': 'string', 'minLength': 1}, 'task_type': {'type': 'string', 'minLength': 1}, 'stage': {'$ref': 'persistence:Stage'}, 'status': {'$ref': 'persistence:TaskStatus'}, 'dependency_task_ids': {'type': 'array', 'items': {'$ref': 'persistence:Id'}, 'minItems': 0}, 'requirement_refs': {'type': 'array', 'items': {'$ref': 'persistence:VersionRef'}, 'minItems': 0}, 'input_refs': {'type': 'array', 'items': {'$ref': 'persistence:VersionRef'}, 'minItems': 0}, 'context_bundle_id': {'anyOf': [{'$ref': 'persistence:Id'}, {'type': 'null'}]}, 'acceptance_contract': {'$ref': 'persistence:AcceptanceContract'}, 'assigned_principal_id': {'anyOf': [{'$ref': 'persistence:Id'}, {'type': 'null'}]}, 'active_run_id': {'anyOf': [{'$ref': 'persistence:Id'}, {'type': 'null'}]}, 'output_artifact_ids': {'type': 'array', 'items': {'$ref': 'persistence:Id'}, 'minItems': 0}, 'acceptance_id': {'anyOf': [{'$ref': 'persistence:Id'}, {'type': 'null'}]}, 'blocking_conflict_ids': {'type': 'array', 'items': {'$ref': 'persistence:Id'}, 'minItems': 0}, 'no_progress_record_id': {'$ref': 'persistence:Id'}, 'stop_policy': {'$ref': 'persistence:StopPolicy'}, 'binding': {'$ref': 'persistence:ProjectBinding'}}, 'required': ['id', 'project_id', 'revision', 'created_at', 'updated_at', 'goal_id', 'title', 'task_type', 'stage', 'status', 'dependency_task_ids', 'requirement_refs', 'input_refs', 'context_bundle_id', 'acceptance_contract', 'assigned_principal_id', 'active_run_id', 'output_artifact_ids', 'acceptance_id', 'blocking_conflict_ids', 'no_progress_record_id', 'stop_policy', 'binding'], 'additionalProperties': False}, 'TaskStatus': {'type': 'string', 'enum': ['DRAFT', 'READY', 'RUNNING', 'EXECUTION_REPORTED', 'VERIFYING', 'ACCEPTED', 'FAILED', 'BLOCKED', 'CANCELLED', 'NEEDS_REVALIDATION', 'DEFERRED_NO_PROGRESS']}, 'UtcTime': {'type': 'string', 'format': 'date-time', 'pattern': 'Z$'}, 'VersionRef': {'type': 'object', 'properties': {'entity_type': {'type': 'string', 'enum': ['ProjectProfile', 'ProjectState', 'Requirement', 'Goal', 'Task', 'Run', 'Artifact', 'Evidence', 'ResearchCycle', 'Experiment', 'DecisionReceipt', 'Qualification', 'ContextBundle', 'ChangeProposal', 'ImpactLink', 'BudgetPolicy', 'RunPolicy', 'ResourceRequest', 'MilestoneRelease', 'ProgressProjection', 'SkillVersion', 'SystemCandidate', 'AcceptanceReceipt', 'AgentMessage', 'SourceCursor', 'BudgetLedgerEntry', 'NoProgressRecord', 'RuntimeRegistration', 'Notification', 'Conflict', 'EventEnvelope']}, 'id': {'$ref': 'persistence:Id'}, 'revision': {'$ref': 'persistence:Revision'}, 'content_hash': {'anyOf': [{'$ref': 'persistence:Digest'}, {'type': 'null'}]}}, 'required': ['entity_type', 'id', 'revision', 'content_hash'], 'additionalProperties': False}}}

def _public_value(group, name, value):
    # Closed projection of the three pinned public schemas, not receipt code.
    _schema_value(PUBLIC_SCHEMAS[group][name], value, group)


def _schema_value(schema, value, group, depth=0):
    if depth > 128:
        raise ValueError('OPEN_PUBLIC_SCHEMA_DEPTH')
    if '$ref' in schema:
        target_group, name = schema['$ref'].split(':', 1)
        _schema_value(PUBLIC_SCHEMAS[target_group][name], value, target_group, depth+1)
    if 'type' in schema:
        expected = {'object': dict, 'array': list, 'string': str, 'integer': int,
                    'boolean': bool, 'null': type(None)}[schema['type']]
        if type(value) is not expected:
            raise ValueError('OPEN_PUBLIC_SCHEMA_TYPE')
    if 'const' in schema and (type(value) is not type(schema['const']) or value != schema['const']):
        raise ValueError('OPEN_PUBLIC_SCHEMA_CONST')
    if 'enum' in schema and not any(type(value) is type(item) and value == item for item in schema['enum']):
        raise ValueError('OPEN_PUBLIC_SCHEMA_ENUM')
    if 'anyOf' in schema:
        matched = False
        for alternative in schema['anyOf']:
            try:
                _schema_value(alternative, value, group, depth+1)
                matched = True
                break
            except ValueError:
                pass
        if not matched:
            raise ValueError('OPEN_PUBLIC_SCHEMA_ANYOF')
    for child in schema.get('allOf', ()):
        _schema_value(child, value, group, depth+1)
    if 'if' in schema:
        try:
            _schema_value(schema['if'], value, group, depth+1)
            applies = True
        except ValueError:
            applies = False
        branch = 'then' if applies else 'else'
        if branch in schema:
            _schema_value(schema[branch], value, group, depth+1)
    if type(value) is dict:
        props = schema.get('properties', {})
        if not set(schema.get('required', ())) <= set(value):
            raise ValueError('OPEN_PUBLIC_SCHEMA_REQUIRED')
        if schema.get('additionalProperties') is False and not set(value) <= set(props):
            raise ValueError('OPEN_PUBLIC_SCHEMA_EXTRA')
        for key in set(value) & set(props):
            if props[key].get('writeOnly') is True:
                raise ValueError('OPEN_PUBLIC_WRITE_ONLY')
            _schema_value(props[key], value[key], group, depth+1)
    if type(value) is list:
        if len(value) < schema.get('minItems', 0) or ('maxItems' in schema and len(value) > schema['maxItems']):
            raise ValueError('OPEN_PUBLIC_SCHEMA_ARRAY_SIZE')
        for item in value:
            if 'items' in schema:
                _schema_value(schema['items'], item, group, depth+1)
    if type(value) is str:
        if len(value) < schema.get('minLength', 0) or ('maxLength' in schema and len(value) > schema['maxLength']):
            raise ValueError('OPEN_PUBLIC_SCHEMA_STRING_SIZE')
        if 'pattern' in schema and re.search(schema['pattern'], value) is None:
            raise ValueError('OPEN_PUBLIC_SCHEMA_PATTERN')
        if schema.get('format') == 'date-time':
            import datetime
            if re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:[Zz]|[+-][0-9]{2}:[0-9]{2})', value) is None:
                raise ValueError('OPEN_PUBLIC_SCHEMA_DATE_TIME')
            try:
                datetime.datetime.fromisoformat(value.upper().replace('Z', '+00:00'))
            except ValueError:
                raise ValueError('OPEN_PUBLIC_SCHEMA_DATE_TIME') from None
    if type(value) is int and 'minimum' in schema and value < schema['minimum']:
        raise ValueError('OPEN_PUBLIC_SCHEMA_MINIMUM')


def _database_row(kind, revision, digest, body, identity, expected_id):
    _integer(revision, 'database revision')
    if revision < 1 or revision > 9223372036854775807:
        raise ValueError('OPEN_DATABASE_REVISION')
    value = _json_original(body)
    if type(value) is not dict or kind not in ('Task', 'Run', 'Artifact'):
        raise ValueError('OPEN_DATABASE_ENTITY')
    group = 'domain'
    if kind == 'Task':
        route = value.get('binding', {}).get('route') if type(value.get('binding')) is dict else None
        if route in ('MU_FORK', 'PI_COMPOSE', 'GAP_ONLY_COMPOSE'):
            group = 'persistence'
        elif route not in ('PAPERCLIP', 'THIN_CORE'):
            raise ValueError('OPEN_DATABASE_TASK_ROUTE')
    _public_value(group, kind, value)
    if value['id'] != expected_id or value['revision'] != revision or value['project_id'] != identity['project_id']:
        raise ValueError('OPEN_DATABASE_BODY')
    if kind == 'Artifact':
        if type(digest) is not str or re.fullmatch(r'sha256:[0-9a-f]{64}', digest) is None or digest != value['content_hash'] or value['run_id'] != identity['run_id']:
            raise ValueError('OPEN_DATABASE_ARTIFACT_HASH')
    elif digest is not None:
        # store.go:221-235 only sets this column for receipt_hash or Artifact.
        raise ValueError('OPEN_DATABASE_NONHASHED_ENTITY')
    if kind == 'Task' and value['goal_id'] != identity['goal_id']:
        raise ValueError('OPEN_DATABASE_TASK_GOAL')
    if kind == 'Run' and value['task_id'] != identity['task_id']:
        raise ValueError('OPEN_DATABASE_TASK_RUN')
    return value


def _event_schema(event):
    _public_value('client', 'SessionEvent', event)
    sensitive = ('credential_value', 'api_key', 'apikey', 'secret', 'token_value', 'password', 'authorization')
    pending = [event['payload']]
    while pending:
        value = pending.pop()
        if type(value) is dict:
            for key, child in value.items():
                if any(pattern in key.casefold() for pattern in sensitive):
                    raise ValueError('OPEN_SENSITIVE_EVENT_PAYLOAD')
                pending.append(child)
        elif type(value) is list:
            pending.extend(value)

