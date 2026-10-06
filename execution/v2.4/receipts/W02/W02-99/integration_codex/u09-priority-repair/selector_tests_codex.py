"""Receipt-local construction selector regressions; no product acceptance claims."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[6]
parser = argparse.ArgumentParser()
parser.add_argument('--main-root', required=True, type=Path)
parser.add_argument('--output', required=True, type=Path)
args = parser.parse_args()
OUT = args.output.resolve()
if not OUT.is_relative_to(HERE) or OUT.exists():
    raise SystemExit('output must be a new directory beneath this receipt')
OUT.mkdir(parents=True)
MAIN = args.main_root.resolve()
SPEC = MAIN / '.local/worktrees/v24-continuation/spec/v2.4'
PLAN_PATH = SPEC / 'contracts/execution.plan.json'
DELIVERY_PATH = SPEC / 'contracts/delivery.contract.json'
CHECKPOINT_PATH = MAIN / 'execution/v2.4/checkpoint.json'
STATE_PATH = MAIN / 'execution/v2.4/step_state.json'
MODULE_PATH = REPO / 'bootstrap/v24_checkpoint.py'
spec = importlib.util.spec_from_file_location('checkpoint', MODULE_PATH)
cp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cp)


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


PLAN, DELIVERY, CURRENT, STATE = map(load, [PLAN_PATH, DELIVERY_PATH, CHECKPOINT_PATH, STATE_PATH])
ACCEPTED, STATUSES, PLANS = cp.accepted_and_status(STATE, PLAN)
WATCHED = [CHECKPOINT_PATH, STATE_PATH, PLAN_PATH, DELIVERY_PATH,
           SPEC / '17_USER_JOURNEYS_AND_VALUE.md', SPEC / 'tools/task_packet.py',
           MAIN / 'execution/v2.4/path_ownership.json',
           MAIN / 'execution/v2.4/receipts/W02/W02-99/integration_codex/checkpoint204_next_packet.json']
WATCHED += sorted({STATE_PATH.parent / e['path'] for row in STATE['steps'] for e in row.get('evidence', [])})
BEFORE = {str(p): digest(p) for p in WATCHED}
save(OUT / 'protected_inputs_before.json', BEFORE)


def graph():
    def row(sid, deps=(), phase='PARENT_FINAL_GATE', priority=100):
        return {'id': sid, 'parent_task': sid.split('-')[0], 'phase': phase,
                'dependencies': list(deps), 'priority': priority}
    rows = [row('W01-99', ['W03-99']), row('W02-99', ['W04-99']),
            row('W03-99', priority=10), row('W04-99', ['W05-99'], priority=20),
            row('W05-99', priority=30), row('W90-01', phase='IMPLEMENTATION_SLICE', priority=1)]
    plans = {x['id']: x for x in rows}
    statuses = {sid: 'NOT_STARTED' for sid in plans}
    delivery = {'capabilities': [{'id': 'U01', 'task_id': 'W01'}, {'id': 'U02', 'task_id': 'W02'}]}
    return plans, statuses, delivery


class SelectorTests(unittest.TestCase):
    def test_current_complete_dag(self):
        priority = cp.flow_priority(STATUSES, PLANS, DELIVERY)
        self.assertEqual(cp.ready_flows(STATUSES, PLANS, DELIVERY), [])
        first = priority['candidates'][0]
        self.assertEqual((first['capability_id'], first['target_parent'], first['next_step_id']),
                         ('U02', 'W05-99', 'W03-99'))
        self.assertEqual(first['unaccepted_dependency_closure'], ['W03-99', 'W04-99', 'W05-99'])
        self.assertEqual(first['remaining_required_cards'], 3)
        self.assertEqual(first['scope'], 'PREREQUISITE_FOR_USER_FLOW')
        self.assertEqual(priority['candidates'][1]['remaining_required_cards'], 6)
        save(OUT / 'actual_dag_selection.json', priority)

    def test_direct_priority_unchanged(self):
        plans, statuses, delivery = graph()
        plans['W02-01'] = {'id': 'W02-01', 'parent_task': 'W02', 'phase': 'IMPLEMENTATION_SLICE',
                             'priority': 999, 'dependencies': []}
        statuses['W02-01'] = 'IN_PROGRESS'
        result = cp.flow_priority(statuses, plans, delivery)
        self.assertEqual(result['candidates'], cp.ready_flows(statuses, plans, delivery))
        self.assertEqual(result['candidates'][0]['next_step_id'], 'W02-01')
        self.assertEqual(result['required_parent_closures'], [])

    def test_full_closure_length_and_unrelated_expansion(self):
        plans, statuses, delivery = graph()
        result = cp.flow_priority(statuses, plans, delivery)
        self.assertEqual(result['candidates'][0]['capability_id'], 'U01')
        self.assertEqual([r['remaining_required_cards'] for r in result['candidates']], [2, 3])
        self.assertNotIn('W90-01', str(result))

    def test_blocker_free_precedes_shorter_blocked_closure(self):
        plans, statuses, delivery = graph()
        statuses['W01-99'] = 'BLOCKED'
        result = cp.flow_priority(statuses, plans, delivery)
        self.assertEqual(result['candidates'][0]['capability_id'], 'U02')
        self.assertEqual(result['candidates'][1]['blockers'], [{'step_id': 'W01-99', 'status': 'BLOCKED'}])

    def test_nonretryable_statuses_and_unaccepted_dependencies(self):
        for status in ['BLOCKED', 'FAILED', 'CANCELLED', 'EXECUTION_REPORTED']:
            with self.subTest(status=status):
                plans, statuses, delivery = graph()
                statuses['W03-99'] = status
                statuses['W05-99'] = status
                result = cp.flow_priority(statuses, plans, delivery)
                self.assertEqual(result['candidates'], [])
                self.assertEqual(result['blocking_reason'], 'NO_ELIGIBLE_FRONTIER_IN_REQUIRED_PARENT_CLOSURES')
                self.assertEqual(cp.prioritized_step(CURRENT, statuses, plans, delivery, 'W90-01'), None)

    def test_in_progress_frontier_and_stable_ties(self):
        plans, statuses, delivery = graph()
        plans['W02-99']['dependencies'] = ['W04-99']
        plans['W04-99']['dependencies'] = []
        statuses['W03-99'] = 'IN_PROGRESS'
        first = cp.flow_priority(statuses, plans, delivery)['candidates'][0]
        self.assertEqual(first['next_step_id'], 'W03-99')
        self.assertEqual(first['next_step_status'], 'IN_PROGRESS')
        self.assertEqual(cp.flow_priority(statuses, dict(reversed(list(plans.items()))), delivery)['candidates'][0], first)

    def test_unknown_and_cycles_fail_closed(self):
        for dependency in ['MISSING-99', 'W01-99']:
            with self.subTest(dependency=dependency):
                plans, statuses, delivery = graph()
                plans['W03-99']['dependencies'] = [dependency]
                with self.assertRaises(cp.CheckpointError):
                    cp.flow_priority(statuses, plans, delivery)

    def test_shared_update_logic_preserves_observations_and_gates(self):
        source = copy.deepcopy(CURRENT)
        value = cp.update_value(source, ACCEPTED, STATUSES, PLANS, DELIVERY, baseline=False,
                                round_record={'round_id': 'synthetic-selector-test', 'delta': 'INFRASTRUCTURE',
                                              'summary': 'selector fixture only', 'evidence_refs': [], 'event_ref': {}},
                                force=False, reason=None, now='TEST_ONLY')
        self.assertEqual(source, CURRENT)
        self.assertEqual(value['user_flow_candidates'], cp.flow_priority(STATUSES, PLANS, DELIVERY)['candidates'])
        self.assertEqual(value['recommended_flow']['next_step_id'], 'W03-99')
        self.assertTrue(value['pause_nonblocking_expansion'])
        self.assertEqual(value['capabilities_observed'], CURRENT['value_checkpoint']['capabilities_observed'])
        self.assertEqual(value['history'][:-1], CURRENT['value_checkpoint']['history'])
        self.assertFalse(value['history'][-1]['observed_user_capability'])
        self.assertEqual(value['documentation_only_checkpoints'], CURRENT['value_checkpoint']['documentation_only_checkpoints'] + 1)
        self.assertEqual(value['formal_gate']['required_parent_tasks'], 22)
        self.assertEqual(value['formal_gate']['required_formal_cases'], 42)

    def test_pending_threshold_refreshes_recommendation_without_resetting_history(self):
        source = copy.deepcopy(CURRENT)
        source['value_checkpoint']['pending_rounds'] = []
        source['value_checkpoint']['failure_count'] = 7
        value = cp.update_value(source, ACCEPTED, STATUSES, PLANS, DELIVERY, baseline=False,
                                round_record={'round_id': 'synthetic-pending-test', 'delta': 'FIXTURE',
                                              'summary': 'selector fixture only', 'evidence_refs': [], 'event_ref': {}},
                                force=False, reason=None, now='TEST_ONLY')
        self.assertEqual(value['status'], 'PENDING_THRESHOLD')
        self.assertEqual(value['recommended_flow']['next_step_id'], 'W03-99')
        self.assertTrue(value['pause_nonblocking_expansion'])
        for key in ['history', 'documentation_only_checkpoints', 'capabilities_observed', 'failure_count']:
            self.assertEqual(value[key], source['value_checkpoint'][key])

    def cli(self, label, state, checkpoint=CURRENT):
        # Synthetic evidence is explicitly local test data, never a formal receipt.
        folder = OUT / label
        folder.mkdir()
        if state is None:
            state_path, checkpoint_path = STATE_PATH, CHECKPOINT_PATH
        else:
            marker = folder / 'SYNTHETIC_TEST_EVIDENCE.txt'
            marker.write_text('Selector regression fixture only. No product acceptance.\n', encoding='utf-8')
            for row in state['steps']:
                row['evidence'] = [{'path': marker.name, 'sha256': digest(marker)}]
                if row['status'] == 'ACCEPTED':
                    row.update(executor_id='fixture-executor', verifier_id='fixture-verifier')
            state_path, checkpoint_path = folder / 'state.json', folder / 'checkpoint.json'
            save(state_path, state)
            save(checkpoint_path, checkpoint)
        argv = [sys.executable, '-B', '-X', 'utf8', str(MODULE_PATH), '--checkpoint', str(checkpoint_path),
                '--state', str(state_path), '--plan', str(PLAN_PATH), '--delivery', str(DELIVERY_PATH), '--next-packet']
        result = subprocess.run(argv, capture_output=True, timeout=120)
        (folder / 'stdout.txt').write_bytes(result.stdout)
        (folder / 'stderr.txt').write_bytes(result.stderr)
        save(folder / 'invocation.json', {'argv': argv, 'exit_code': result.returncode,
                                        'stdout_sha256': hashlib.sha256(result.stdout).hexdigest(),
                                        'stderr_sha256': hashlib.sha256(result.stderr).hexdigest()})
        self.assertIn(result.returncode, [0, 3], result.stderr.decode('utf-8'))
        return json.loads(result.stdout), result.returncode

    def test_real_cli_readonly_checkpoint205(self):
        result, code = self.cli('actual-readonly', None)
        self.assertEqual(code, 0)
        self.assertEqual(result['step']['id'], 'W03-99')
        self.assertTrue(result['eligible'])
        self.assertEqual(result['state_source'], 'VALIDATED_FILE')
        self.assertEqual(result['value_checkpoint_policy']['selection']['candidates'][0]['capability_id'], 'U02')

    def test_cli_no_frontier_and_all_owners_accepted(self):
        for label, status in [('no-frontier', 'BLOCKED'), ('all-accepted', 'ACCEPTED')]:
            with self.subTest(label=label):
                state = copy.deepcopy(STATE)
                state['steps'] = [{'id': row['id'], 'status': status} for row in PLAN['steps']]
                result, code = self.cli(label, state)
                self.assertEqual(code, 3)
                self.assertIsNone(result['step'])
                self.assertIsNone(result['value_checkpoint_policy']['selected_step_id'])
                self.assertTrue(result['value_checkpoint_policy']['selection']['blocking_reason'])

    def test_cli_pause_false_keeps_frozen_default(self):
        state, checkpoint = copy.deepcopy(STATE), copy.deepcopy(CURRENT)
        state['steps'] = [{'id': row['id'], 'status': 'NOT_STARTED'} for row in PLAN['steps']]
        checkpoint['value_checkpoint']['pause_nonblocking_expansion'] = False
        result, code = self.cli('priority-disabled', state, checkpoint)
        self.assertEqual(code, 0)
        policy = result['value_checkpoint_policy']
        self.assertEqual(policy['selected_step_id'], policy['default_step_id'])
        self.assertIsNone(policy['selection'])


with (OUT / 'unittest.txt').open('w', encoding='utf-8') as stream:
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SelectorTests))
AFTER = {str(p): digest(p) for p in WATCHED}
save(OUT / 'protected_inputs_after.json', AFTER)
manifest = {'scope': 'CONSTRUCTION_SELECTOR_ONLY_NOT_PRODUCT_ACCEPTANCE',
            'source_sha256': digest(MODULE_PATH), 'test_source_sha256': digest(Path(__file__)),
            'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
            'protected_inputs_unchanged': BEFORE == AFTER, 'protected_input_count': len(BEFORE),
            'checkpoint_revision': CURRENT['revision'],
            'artifacts': [{'path': str(p.relative_to(OUT)), 'sha256': digest(p)} for p in sorted(OUT.rglob('*')) if p.is_file()]}
save(OUT / 'manifest.json', manifest)
print(json.dumps({k:v for k,v in manifest.items() if k != 'artifacts'}))
raise SystemExit(0 if result.wasSuccessful() and BEFORE == AFTER else 1)
