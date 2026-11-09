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
    # In-memory deserialization prevents mutation or WAL omission of a live path.
    # Only a Root-materialized complete, quiescent SQLite snapshot is supported.
    if type(raw) is not bytes or not raw.startswith((b'SQLite format 3' + bytes((0,)))):
        raise ValueError('OPEN_COMPLETE_SQLITE_ORIGINAL')
    import sqlite3
    db = sqlite3.connect(':memory:')
    try:
        db.deserialize(raw)
        db.execute('PRAGMA query_only=ON')
        result = {}
        for kind, key in (('Task', 'task_id'), ('TaskRun', 'run_id')):
            rows = db.execute('SELECT revision,content_hash,body FROM domain_objects WHERE project=? AND kind=? AND id=?',
                              (identity['project_id'], kind, identity[key])).fetchall()
            if len(rows) != 1:
                raise ValueError('OPEN_DATABASE_CURRENT_IDENTITY')
            revision, digest, body = rows[0]
            _integer(revision, 'database revision')
            if revision < 1 or type(digest) is not str or not re.fullmatch('[0-9a-f]{64}', digest):
                raise ValueError('OPEN_DATABASE_REF')
            value = _json_original(body)
            if value.get('id') != identity[key] or value.get('revision') != revision:
                raise ValueError('OPEN_DATABASE_BODY')
            result[kind] = value
        if result['TaskRun'].get('task_id') != identity['task_id']:
            raise ValueError('OPEN_DATABASE_TASK_RUN')
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
    events, finals = [], []
    for ordinal, frame in enumerate(frames):
        if type(frame) is not dict:
            raise ValueError('OPEN_JSONL_OBJECT')
        if frame.get('type') == 'session.event':
            if finals:
                raise ValueError('OPEN_EVENT_AFTER_FINAL')
            event = frame.get('event')
            if type(event) is not dict or event.get('session_id') != identity['session_id'] or event.get('protocol_version') != 'researchos-client/2' or event.get('core_build_id') != identity['core_build_id']:
                raise ValueError('OPEN_EVENT_IDENTITY')
            _integer(event.get('sequence'), 'event sequence')
            if events and event['sequence'] != events[-1]['sequence'] + 1:
                raise ValueError('OPEN_EVENT_GAP')
            if event.get('run_id') not in (None, identity['run_id']):
                raise ValueError('OPEN_FOREIGN_RUN_EVENT')
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
    if final.get('event_sequence') != events[-1]['sequence'] or final.get('independent_acceptance') != 'NOT_EVALUATED':
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
    if state.get('revision') != run.get('revision') or state.get('status') != run.get('status') or run.get('children_stopped') is not True or run.get('queue_empty') is not True:
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
    for reference in _nonempty(row.get('refusal_evidence_refs'), 'actual refusal refs', list):
        refusal, _ = _original(doc, raw, reference)
        if refusal.get('schema') != 'researchos.w05.actual-refusal.v2' or refusal.get('assertion_id') != row['id'] or refusal.get('run_id') != context['run_id'] or refusal.get('lane') != row['lane'] or refusal.get('task_id') != row['product_identity']['task_id'] or refusal.get('rejected') is not True:
            raise ValueError('OPEN_ACTUAL_REFUSAL_IDENTITY')
        if refusal.get('negative_condition') != row['expected'] or refusal.get('invocation_ref') != row['negative_invocation_ref']:
            raise ValueError('OPEN_FROZEN_NEGATIVE_BINDING')
        invocation, _ = _original(doc, raw, refusal['invocation_ref'])
        _native_exit(invocation.get('native_exit'), 'refusal native exit')
        pair, _ = _original(doc, raw, invocation['root_tool_pair_ref'])
        closed = _root_pair(pair, invocation['scope'])
        if closed['actual_launcher_native_exit'] != invocation['native_exit'] or invocation['native_exit'] == 0:
            raise ValueError('OPEN_REFUSAL_ACTUAL_NONZERO')
        response, _ = _original(doc, raw, refusal['original_response_ref'])
        if response.get('status') not in ('REJECTED', 'BLOCKED', 'DENIED') or response.get('task_id') != row['product_identity']['task_id']:
            raise ValueError('OPEN_ORIGINAL_REFUSAL_RESPONSE')



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
        if row['lane'] != ASSERTION_LANES[row['id']]:
            raise ValueError('OPEN_FROZEN_ASSERTION_LANE')
        invocation, scope = by_lane[row['lane']]
        verify_live_originals(whole_doc, whole_raw, context, row, invocation, scope)
        verify_refusal(whole_doc, whole_raw, context, row)
    # These four LIVE decoders are intentionally unsupported until their
    # real producer ABI is frozen; verify_live_originals returns OPEN first.
    # A generic raw gate PASS list can never substitute for them.
    raise ValueError('OPEN_H08_P01_U02_CURRENT_RAW_GATE_DECODERS_REQUIRED')
