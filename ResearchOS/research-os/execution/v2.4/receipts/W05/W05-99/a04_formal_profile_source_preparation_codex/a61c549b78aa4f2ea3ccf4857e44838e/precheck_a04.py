"""Pure in-memory A04 assertion controls; never import or run product code."""
import ast
import copy
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
HERE = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_preparation_codex/a61c549b78aa4f2ea3ccf4857e44838e')
tree = ast.parse((HERE / 'formal_profile_w05.proposed.py').read_text(encoding='utf-8'))
node = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == '_witness')
space = {'EXTRA': {'A04-04': 'H08', 'A04-05': 'P01', 'A04-06': 'U02'}}
exec(compile(ast.Module(body=[node], type_ignores=[]), '<selected-pure-A04-witness>', 'exec'), space)
witness = space['_witness']


class API:
    SHA = re.compile(r'^[0-9a-f]{64}$')

    @staticmethod
    def require(ok, code, detail):
        if not ok:
            raise ValueError(code + ':' + detail)

    @staticmethod
    def fields(value, required, optional=(), label='object'):
        API.require(type(value) is dict and set(required) <= set(value) and
                    set(value) <= set(required) | set(optional), 'FIELDS', label)
        return value

    @staticmethod
    def obj(value, label):
        API.require(type(value) is dict, 'OBJECT', label)
        return value

    @staticmethod
    def sequence(value, label):
        API.require(type(value) is list and bool(value), 'SEQUENCE', label)
        return value

    @staticmethod
    def meaningful(value):
        return value is not None and value != '' and value != [] and value != {}


LANES = {'A04-01': 'success', 'A04-02': 'pending_queue_cancel',
         'A04-03': 'executor_crash', 'A04-04': 'H08',
         'A04-05': 'P01', 'A04-06': 'U02'}
INV = [{'lane': lane, 'invocation_ref': {'path': 'inv-' + lane, 'sha256': 'a' * 64}}
       for lane in ('success', 'tool_failed', 'request_timeout',
                    'pending_queue_cancel', 'executor_crash', 'H08', 'P01', 'U02')]
facts = {
    'A04-01': {'task_status_after_host': 'EXECUTION_REPORTED', 'run_status': 'SETTLED',
               'host_receipts_complete': True, 'early_accepted': False,
               'independent_acceptance': 'NOT_EVALUATED'},
    'A04-02': {'cancel_confirmed': True, 'owned_tool_processes_after': 0,
               'pending_requests_after': 0, 'late_launches': 0},
    'A04-03': {'crash_observed': True, 'timeout_observed': True,
               'worktree_isolated': True, 'credentials_isolated': True,
               'new_context_bundle_ref': {'path': 'bundle', 'sha256': 'b' * 64},
               'blind_retry_count': 0, 'timeout_invocation_ref': INV[2]['invocation_ref'],
               'crash_invocation_ref': INV[4]['invocation_ref']},
    'A04-04': {'parent_run_id': 'Rparent', 'child_run_id': 'Rchild',
               'tool_effect_id': 'Etool', 'shared_cancel_scope': True,
               'shared_budget_scope': True, 'fixed_model_unchanged': True,
               'selected_patches_preserved': True,
               'unsupported_adapters_explicit': True,
               'version_matrix_ref': {'path': 'matrix', 'sha256': 'c' * 64}},
    'A04-05': {'installed_cli': 'researchos', 'interactive_task_complete': True,
               'jsonl_stream_valid': True, 'resume_observed': True,
               'cancel_observed': True, 'stdout_logs_mixed': False,
               'failure_exit_nonzero': True, 'exit_zero_auto_accept': False},
    'A04-06': {'issue_id': 'ISSUE-CONTINUITY-001',
               'selected_by_delivery_contract': True, 'manual_admin_commands': 0,
               'chinese_input': True, 'file_before_sha256': 'a' * 64,
               'file_after_sha256': 'b' * 64, 'tests_native_exit': 0,
               'fixed_model_unchanged': True,
               'model_before': 'opencode-go/deepseek-v4.1-flash',
               'model_after': 'opencode-go/deepseek-v4.1-flash',
               'cli_handlers': ['init', 'run', 'goal', 'resume', 'status',
                                'cancel', 'doctor', 'config', 'interactive',
                                'jsonl', 'slash']},
}
context = {'run_id': 'run-current', 'selected_runtime': 'mu',
           'fixed_model': 'opencode-go/deepseek-v4.1-flash',
           'command_invocations': INV,
           'product_original_paths': {'raw-' + cid for cid in facts}}
raw_values = copy.deepcopy(facts)
proofs = {}
for cid, value in facts.items():
    lane = LANES[cid]
    proof = {'schema': 'researchos.w05.a04-raw-observation.v1',
             'assertion_id': cid, 'run_id': context['run_id'], 'lane': lane,
             'invocation_ref': next(i['invocation_ref'] for i in INV if i['lane'] == lane),
             'facts': value, 'actual': 'observed-' + cid,
             'fact_source_refs': {
                 key: {'path': 'raw-' + cid, 'sha256': 'd' * 64,
                       'locator': {'json_pointer': '/facts/' + key}}
                 for key in value}}
    proofs[cid] = proof


def raw(_api, _reader, reference):
    path = reference['path']
    if path.startswith('obs-'):
        return proofs[path[4:]]
    if path.startswith('raw-'):
        return raw_values[path[4:]][reference['locator']['json_pointer'][7:]]
    if path.startswith('refusal-'):
        return {'rejected': True}
    raise ValueError('UNKNOWN_RAW')


def document(_api, _reader, reference):
    if reference.get('path') == 'matrix':
        return {'selected_runtime': 'mu'}
    raise ValueError('UNKNOWN_DOC')


space['_raw'] = raw
space['_doc'] = document


def row(cid):
    return {'id': cid, 'expected': 'frozen-' + cid,
            'actual': 'observed-' + cid, 'status': 'PASS', 'lane': LANES[cid],
            'raw_evidence_refs': [{'path': 'obs-' + cid, 'sha256': 'e' * 64,
                                   'locator': {'json_pointer': ''}}],
            'refusal_evidence_refs': [{'path': 'refusal-' + cid,
                                       'sha256': 'f' * 64,
                                       'locator': {'json_pointer': ''}}],
            'command_keys': ['test.runtime']}


checks = []
for cid in facts:
    witness(API, None, row(cid), context, {lane: {} for lane in LANES.values()})
    checks.append({'id': cid, 'outcome': 'PASS'})


def rejects(name, callback):
    try:
        callback()
    except (ValueError, KeyError, TypeError):
        checks.append({'id': name, 'outcome': 'REJECT'})
        return
    raise AssertionError(name + ' was accepted')


for cid in facts:
    broken = row(cid)
    broken['status'] = 'BLOCKED'
    rejects(cid + ' BLOCKED cannot pass',
            lambda broken=broken: witness(API, None, broken, context,
                                           {lane: {} for lane in LANES.values()}))
    broken = row(cid)
    broken['lane'] = 'success' if LANES[cid] != 'success' else 'P01'
    rejects(cid + ' foreign lane',
            lambda broken=broken: witness(API, None, broken, context,
                                           {lane: {} for lane in LANES.values()}))
    original = raw_values[cid][next(iter(facts[cid]))]
    raw_values[cid][next(iter(facts[cid]))] = 'forged'
    rejects(cid + ' claimed fact differs from raw original',
            lambda cid=cid: witness(API, None, row(cid), context,
                                    {lane: {} for lane in LANES.values()}))
    raw_values[cid][next(iter(facts[cid]))] = original

prior = facts['A04-06']['file_after_sha256']
facts['A04-06']['file_after_sha256'] = facts['A04-06']['file_before_sha256']
raw_values['A04-06']['file_after_sha256'] = facts['A04-06']['file_after_sha256']
rejects('U02 unchanged file cannot pass',
        lambda: witness(API, None, row('A04-06'), context,
                        {lane: {} for lane in LANES.values()}))
facts['A04-06']['file_after_sha256'] = prior
raw_values['A04-06']['file_after_sha256'] = prior

with (HERE / 'precheck.a04.json').open('xb') as out:
    out.write((json.dumps({'schema': 'researchos.a04-pure-io-controls.v1',
                           'checks': checks, 'count': len(checks),
                           'candidate_executions': 0, 'native_calls': 0,
                           'model_calls': 0, 'formal_increment': 0},
                          ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
print('A04_PURE_IO_CONTROLS=' + str(len(checks)) + ' FAIL=0')
