"""Pure JSON/AST checks of the v6 draft and new-Goal graph; no product import."""
import ast
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v6_source_codex/e8d350ed0ed34a2c939f8cb894de2feb')
tree = ast.parse((HERE / 'mu_sdk_trial.v6.graph.proposed.py').read_text(encoding='utf-8'))
names = {'require', 'strict_consumed_json', 'verified_cli_draft_goal_transition',
         'object_by_id', 'budget_chain', 'verify_ordinary_goal_graph'}
nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
assert {node.name for node in nodes} == names
space = {'json': json, 'datetime': datetime, 'timezone': timezone}
exec(compile(ast.Module(body=nodes, type_ignores=[]), '<selected-pure-AST>', 'exec'), space)
checks = []


def passes(name, fn):
    fn()
    checks.append({'name': name, 'decision': 'PASS'})


def rejects(name, fn):
    try:
        fn()
    except (ValueError, KeyError, TypeError, AssertionError):
        checks.append({'name': name, 'decision': 'REJECT'})
        return
    raise AssertionError(name + ' was accepted')


old_context = {'project_id': 'P', 'session_id': '', 'session_revision': 0,
               'writer_epoch': 0, 'updated_by': ''}
saved = {'project_id': 'P', 'session_id': 'S', 'session_revision': 1,
         'writer_epoch': 1, 'updated_by': 'W'}
snapshot = {'project_id': 'P', 'session_id': 'S', 'revision': 1,
            'goal_id': 'G0', 'goal_status': 'DRAFT',
            'writer': {'epoch': 1, 'client_id': 'W'}}
draft_row = {'command': 'goal', 'status': 'GOAL_DRAFT_CREATED', 'exit_code': 0,
             'client_id': 'W', 'session_id': 'S', 'saved_context': saved,
             'goal': {'goal_id': 'G0', 'goal_revision': 1},
             'execution': {'status': 'NOT_STARTED', 'independent_acceptance': 'NOT_EVALUATED'},
             'operations': [{'method': 'goal.start', 'status': 'COMPLETED', 'exit_code': 0,
                             'result': {'goal_id': 'G0', 'goal_revision': 1,
                                        'goal_status': 'DRAFT', 'snapshot': snapshot}}]}
post = json.dumps(dict(old_context, **saved)).encode('utf-8')
draft = space['verified_cli_draft_goal_transition']
passes('actual-shaped draft created with real saved context',
       lambda: draft({'_init_project_id': 'P'}, old_context, [draft_row], post))
for name, mutate in (
    ('non-draft bootstrap execution', lambda d: d.update(status='EXECUTION_REPORTED')),
    ('forged started execution', lambda d: d['execution'].update(status='EXECUTION_REPORTED')),
    ('foreign draft goal', lambda d: d['goal'].update(goal_id='Gforeign')),
    ('changed writer epoch', lambda d: d['saved_context'].update(writer_epoch=2)),
):
    bad = copy.deepcopy(draft_row)
    mutate(bad)
    rejects(name, lambda bad=bad: draft({'_init_project_id': 'P'}, old_context, [bad], post))
rejects('draft emits a second stream row',
        lambda: draft({'_init_project_id': 'P'}, old_context, [draft_row, draft_row], post))
rejects('postimage not actual saved context',
        lambda: draft({'_init_project_id': 'P'}, old_context, [draft_row],
                      json.dumps(dict(old_context, session_id='Sforeign')).encode('utf-8')))


def policy(identity, parent, scope):
    return {'id': identity, 'revision': 1, 'parent_policy_id': parent,
            'scope_type': scope, 'project_id': None if scope == 'GLOBAL' else 'P',
            'mode': 'UNLIMITED_AMOUNT', 'cap': None,
            'unknown_cost_action': 'ALLOW_AND_RECORD',
            'enforcement': 'ACCOUNTING_ONLY', 'effective_from': '2020-01-01T00:00:00Z'}


objects = {
    ('Goal', 'G0'): {'id': 'G0', 'status': 'DRAFT', 'budget_policy_id': 'B0'},
    ('Goal', 'G1'): {'id': 'G1', 'status': 'ACTIVE', 'budget_policy_id': 'B1'},
    ('Task', 'T1'): {'id': 'T1', 'goal_id': 'G1', 'active_run_id': 'R1',
                     'status': 'EXECUTION_REPORTED', 'output_artifact_ids': ['A1']},
    ('Run', 'R1'): {'id': 'R1', 'task_id': 'T1', 'runtime_id': 'MU',
                   'status': 'SETTLED', 'revision': 2, 'children_stopped': True,
                   'queue_empty': True, 'runtime_settled_at': '2026-10-08T00:00:00Z',
                   'execution_report': 'settled', 'exit_code': 0,
                   'result_artifact_ids': ['A1']},
    ('Artifact', 'A1'): {'id': 'A1'},
    ('BudgetPolicy', 'B0'): policy('B0', 'BP', 'GOAL'),
    ('BudgetPolicy', 'B1'): policy('B1', 'BP', 'GOAL'),
    ('BudgetPolicy', 'BP'): policy('BP', 'BG', 'PROJECT'),
    ('BudgetPolicy', 'BG'): policy('BG', None, 'GLOBAL'),
}


class FakeDB:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, query, args):
        if query.startswith('SELECT id FROM domain_objects'):
            project, kind = args
            assert project == 'P'
            return [(identity,) for (typ, identity) in self.rows if typ == kind]
        if query.startswith('SELECT body FROM domain_objects'):
            kind, identity, *project = args
            assert not project or project == ['P']
            value = self.rows.get((kind, identity))
            return [(json.dumps(value),)] if value is not None else []
        raise AssertionError('unmodeled SQL')


host = {'status': 'SETTLED', 'revision': 2, 'children_stopped': True,
        'queue_empty': True, 'runtime_settled_at': '2026-10-08T00:00:00Z',
        'execution_report': 'settled', 'result_artifact_ids': ['A1']}
summary = {'execution': {'goal_id': 'G1', 'task_id': 'T1', 'run_id': 'R1',
                         'exit_code': 0, 'host_execution': host}}
doc = {'project_id': 'P', 'goal_id': 'G0', 'runtime_id': 'MU'}
before = {'Goal': {'G0'}, 'Task': set(), 'Run': set()}
draft_policies = space['budget_chain'](FakeDB(objects), 'P', 'G0', 'DRAFT')
graph = space['verify_ordinary_goal_graph']


def examine(rows, original=summary, admission=None, draft_basis=draft_policies):
    return graph(FakeDB(rows), doc, before, original, {'goal_id': 'G0'},
                 admission or {'goal_id': 'G1'}, draft_basis)


passes('new Goal Task Run and Artifact exact graph', lambda: examine(objects))
rejects('old Goal reused by session.send',
        lambda: examine(objects, admission={'goal_id': 'G0'}))
for name, kind, identity, field, value in (
    ('foreign Task goal', 'Task', 'T1', 'goal_id', 'Gforeign'),
    ('foreign Run task', 'Run', 'R1', 'task_id', 'Tforeign'),
    ('foreign Run runtime', 'Run', 'R1', 'runtime_id', 'OtherRuntime'),
    ('missing Run output artifact', 'Run', 'R1', 'result_artifact_ids', []),
    ('foreign Task artifact', 'Task', 'T1', 'output_artifact_ids', ['Aforeign']),
    ('wrong new Goal budget parent', 'BudgetPolicy', 'B1', 'parent_policy_id', 'Other'),
):
    bad = copy.deepcopy(objects)
    bad[(kind, identity)][field] = value
    rejects(name, lambda bad=bad: examine(bad))
bad = copy.deepcopy(objects)
del bad[('Artifact', 'A1')]
rejects('missing actual project Artifact', lambda: examine(bad))
bad = copy.deepcopy(objects)
bad[('Goal', 'G1')]['status'] = 'DRAFT'
rejects('ordinary Goal still DRAFT', lambda: examine(bad))
bad = copy.deepcopy(summary)
bad['execution']['host_execution']['result_artifact_ids'] = ['Aforeign']
rejects('CLI original host artifact diverges',
        lambda: examine(objects, original=bad))
with (HERE / 'precheck.v6.graph.json').open('xb') as out:
    out.write(json.dumps({'schema': 'researchos.mu-sdk-v6-pure-io-graph-check.v1',
                          'checks': checks, 'count': len(checks), 'candidate_execution': 0,
                          'go_calls': 0, 'sdk_calls': 0, 'provider_requests': 0},
                         ensure_ascii=False, indent=2).encode('utf-8'))
print('PURE_IO_CHECKS=' + str(len(checks)) + ' FAIL=0')
