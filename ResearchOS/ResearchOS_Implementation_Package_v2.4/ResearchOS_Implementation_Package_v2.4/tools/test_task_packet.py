"""Small fixture checks for read-only routing; no model or product execution."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
import task_packet as router


def card(sid, dependencies):
    return dict(
        id=sid, parent_task=sid[:3], title='只读测试卡', dependencies=dependencies,
        read_refs=[{'path': '08_AGENT_EXECUTION_GOAL.md', 'selector': 'full'}],
        write_scope=['execution/v2.4/**'], actions=['fixture action'], deliverables=['fixture artifact'],
        checks=[{'id': sid + '-OUTPUT', 'expected': 'fixture output'}],
        verification_commands=[{'key': 'fixture.check', 'cwd': 'SPEC', 'binding': 'fixture only', 'argv_template': ['python', 'fixture.py']}],
        affected_formal_cases=['A01'], resource_requirements=[], limits=['do not execute this fixture'],
        rollback='discard fixture only', handoff=dict(state='execution/v2.4/step_state.json',
            checkpoint='execution/v2.4/checkpoint.json', receipt_directory='receipts/' + sid,
            independent_review_required=True),
    )


class TaskPacketChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='researchos-task-packet-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan_path = self.root / 'plan.json'
        self.state_path = self.root / 'state.json'
        self.plan = {'package_version': '2.4.0', 'artifact_kind': 'EXECUTION_PLAN',
                     'steps': [card('W00-01', []), card('W00-02', ['W00-01'])]}
        self.write(self.plan_path, self.plan)
        self.evidence = self.root / 'review.json'
        self.evidence.write_text('Independent-review fixture; not a real acceptance.', encoding='utf-8')
        self.accepted = {'id': 'W00-01', 'status': 'ACCEPTED', 'executor_id': 'executor-fixture',
                         'verifier_id': 'independent-verifier-fixture',
                         'evidence': [{'path': 'review.json', 'sha256': router.digest(self.evidence)}]}
        self.state = {'schema_version': '1.0', 'package_version': '2.4.0',
                      'plan_sha256': router.digest(self.plan_path), 'steps': [self.accepted]}

    def write(self, path, value):
        path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')

    def test_missing_state_and_accepted_dependency_select_next(self):
        plan = router.load_plan(self.plan_path)
        state, source = router.load_state(self.state_path, self.plan_path, plan)
        self.assertEqual(source, 'MISSING_ASSUMED_EMPTY')
        self.assertEqual(router.select_next(plan, state)['id'], 'W00-01')
        self.assertFalse(self.state_path.exists())
        self.write(self.state_path, self.state)
        before = self.state_path.read_bytes()
        state, source = router.load_state(self.state_path, self.plan_path, plan)
        self.assertEqual(source, 'VALIDATED_FILE')
        self.assertEqual(router.select_next(plan, state)['id'], 'W00-02')
        self.assertEqual(before, self.state_path.read_bytes())

    def test_rejects_forged_acceptance_and_bad_state(self):
        bad_states = []
        for change in (
            {'executor_id': ''}, {'verifier_id': 'EXECUTOR-FIXTURE'}, {'evidence': []},
            {'evidence': [{'path': 'absent.json', 'sha256': '0' * 64}]},
            {'evidence': [{'path': 'review.json', 'sha256': '0' * 64}]},
            {'evidence': [{'path': '../review.json', 'sha256': '0' * 64}]},
            {'status': 'DONE'}, {'id': 'W99-99'}, {'status': ['ACCEPTED']},
        ):
            state = copy.deepcopy(self.state)
            state['steps'][0].update(change)
            bad_states.append(state)
        missing_identity = copy.deepcopy(self.state)
        del missing_identity['steps'][0]['verifier_id']
        bad_states.append(missing_identity)
        missing_dependency = copy.deepcopy(self.state)
        missing_dependency['steps'][0]['id'] = 'W00-02'
        bad_states.append(missing_dependency)
        duplicate = copy.deepcopy(self.state)
        duplicate['steps'].append(copy.deepcopy(duplicate['steps'][0]))
        bad_states.append(duplicate)
        stale_plan = copy.deepcopy(self.state)
        stale_plan['plan_sha256'] = '0' * 64
        bad_states.append(stale_plan)
        for number, state in enumerate(bad_states):
            with self.subTest(number=number):
                self.write(self.state_path, state)
                with self.assertRaises(ValueError):
                    router.load_state(self.state_path, self.plan_path, self.plan)
        self.state_path.write_text('{"steps": [], "steps": []}', encoding='utf-8')
        with self.assertRaises(ValueError):
            router.load_state(self.state_path, self.plan_path, self.plan)

    def test_bad_plan_and_nonready_status(self):
        for variant in ('duplicate', 'unknown_dependency', 'cycle', 'missing_field', 'illegal_id'):
            plan = copy.deepcopy(self.plan)
            if variant == 'duplicate':
                plan['steps'].append(copy.deepcopy(plan['steps'][0]))
            elif variant == 'unknown_dependency':
                plan['steps'][0]['dependencies'] = ['W21-99']
            elif variant == 'cycle':
                plan['steps'][0]['dependencies'] = ['W00-02']
            elif variant == 'missing_field':
                del plan['steps'][0]['actions']
            else:
                plan['steps'][0]['id'] = 'W00-00'
            with self.subTest(variant=variant):
                self.write(self.plan_path, plan)
                with self.assertRaises(ValueError):
                    router.load_plan(self.plan_path)
        for status in ('EXECUTION_REPORTED', 'BLOCKED', 'FAILED', 'CANCELLED'):
            self.assertIsNone(router.select_next(self.plan, {'W00-01': {'status': status}}))

    def test_cli_unknown_id_and_missing_state(self):
        command = [sys.executable, '-B', str(Path(router.__file__)), '--plan', str(self.plan_path)]
        result = subprocess.run(command + ['next', '--state', str(self.state_path)], capture_output=True,
                                text=True, encoding='utf-8', timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output['step']['id'], 'W00-01')
        self.assertEqual(output['state_source'], 'MISSING_ASSUMED_EMPTY')
        self.assertEqual(output['product_acceptance'], 'NOT_ASSERTED')
        self.assertFalse(self.state_path.exists())
        result = subprocess.run(command + ['show', 'W99-99'], capture_output=True,
                                text=True, encoding='utf-8', timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertIn('TASK_PACKET_REJECTED', result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
