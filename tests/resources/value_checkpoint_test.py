"""Focused U09 construction checkpoint tests; no product state or holdout is used."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


MODULE = Path(__file__).resolve().parents[2] / "bootstrap" / "v24_checkpoint.py"
spec = importlib.util.spec_from_file_location("v24_checkpoint", MODULE)
checkpoint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checkpoint)


class ValueCheckpointTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        folder = self.root / "execution" / "v2.4"
        folder.mkdir(parents=True)
        self.cp = folder / "checkpoint.json"
        self.state = folder / "step_state.json"
        self.plan = self.root / "plan.json"
        self.delivery = self.root / "delivery.json"
        steps = [{"id": f"W{i:02d}-99", "phase": "PARENT_FINAL_GATE"} for i in range(22)]
        steps += [{"id": "W00-01", "phase": "IMPLEMENTATION_SLICE", "parent_task": "W00", "dependencies": []}]
        steps += [{"id": f"W01-{i:02d}", "phase": "IMPLEMENTATION_SLICE", "parent_task": "W01",
                   "dependencies": ["W00-01"]} for i in range(1, 4)]
        steps += [{"id": "W17-02", "phase": "IMPLEMENTATION_SLICE", "parent_task": "W17",
                   "dependencies": ["W00-01"], "priority": 10},
                  {"id": "W17-03", "phase": "IMPLEMENTATION_SLICE", "parent_task": "W17",
                   "dependencies": ["W17-02"], "priority": 20}]
        self.write(self.plan, {"steps": steps})
        self.plan_hash = checkpoint.sha(self.plan.read_bytes())
        self.write(self.delivery, {"capabilities": [
            {"id": "U01", "task_id": "W17", "title": "first use"},
            {"id": "U09", "task_id": "W12", "title": "direction gate"}],
            "value_checkpoint": {"after_step_count": 3, "no_user_capability_rounds": 2,
                                 "no_value_checkpoints_before_replan": 2,
                                 "new_candidates_alone_count_as_value": False,
                                 "does_not_lower_product_acceptance": True}})
        self.write(self.state, {"plan_sha256": self.plan_hash,
                                "steps": [{"id": "W00-01", "status": "ACCEPTED"},
                                          {"id": "W00-99", "status": "ACCEPTED"}]})
        self.write(self.cp, {"revision": 4, "expected_previous_revision": 3,
                             "plan_sha256": self.plan_hash, "status": "IN_PROGRESS",
                             "failure_counters": [{"origin_key": "same-failure", "attempt": 2}],
                             "no_progress_rounds": 2, "accepted_steps": ["W00-01", "W00-99"],
                             "parent_tasks_accepted": ["W00"], "source_hashes": {"original": "keep"},
                             "value_checkpoint": {"status": "NOT_RUN", "capabilities_observed": [],
                                                  "documentation_only_checkpoints": 0}})

    def write(self, path, value):
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def call(self, revision, **kwargs):
        return checkpoint.update_file(self.cp, self.state, self.plan, self.delivery,
                                      revision, **kwargs)

    def round(self, name, delta="DOCUMENTATION", capability=None):
        evidence = self.root / (name + ".txt")
        evidence.write_text("actual evidence for " + name, encoding="utf-8")
        event = {"schema": checkpoint.ROUND_SCHEMA, "round_id": name, "delta": delta,
                 "summary": "observed " + name,
                 "evidence_refs": [{"path": evidence.name, "sha256": checkpoint.sha(evidence.read_bytes())}]}
        if capability is not None:
            event["capability_observed"] = capability
        event_path = self.root / (name + ".json")
        self.write(event_path, event)
        return event_path

    def test_baseline_uses_actual_state_and_does_not_invent_history(self):
        result = self.call(4, baseline=True)
        value = result["value_checkpoint"]
        self.assertEqual(value["history"], [])
        self.assertEqual(value["historical_observation"], "NOT_RECONSTRUCTED")
        self.assertEqual(value["baseline_accepted_implementation_card_ids"], ["W00-01"])
        self.assertEqual(value["formal_gate"]["accepted_parent_step_ids"], ["W00-99"])
        self.assertEqual(value["formal_gate"]["required_formal_cases"], 42)
        self.assertEqual(value["formal_gate"]["formal_cases_accepted"], "NOT_DERIVABLE_FROM_STEP_STATE")
        self.assertEqual(value["user_flow_candidates"][0]["next_step_id"], "W17-02")
        self.assertEqual(result["failure_counters"], [{"origin_key": "same-failure", "attempt": 2}])
        self.assertEqual(result["no_progress_rounds"], 2)
        self.assertEqual(result["source_hashes"], {"original": "keep"})
        self.assertEqual(result["status"], "IN_PROGRESS")

    def test_stale_revision_and_unverified_event_leave_bytes_unchanged(self):
        self.call(4, baseline=True)
        before = self.cp.read_bytes()
        with self.assertRaisesRegex(checkpoint.CheckpointError, "CAS revision mismatch"):
            self.call(4, event_path=self.round("stale"))
        self.assertEqual(self.cp.read_bytes(), before)
        bad = self.round("bad")
        payload = json.loads(bad.read_text(encoding="utf-8"))
        payload["evidence_refs"][0]["sha256"] = "0" * 64
        self.write(bad, payload)
        with self.assertRaisesRegex(checkpoint.CheckpointError, "evidence hash mismatch"):
            self.call(5, event_path=bad)
        self.assertEqual(self.cp.read_bytes(), before)

    def test_three_accepted_cards_trigger_one_checkpoint_without_formal_acceptance(self):
        self.call(4, baseline=True)
        state = json.loads(self.state.read_text(encoding="utf-8"))
        state["steps"] += [{"id": f"W01-{i:02d}", "status": "ACCEPTED"} for i in range(1, 4)]
        self.write(self.state, state)
        result = self.call(5, event_path=self.round("cards"))
        value = result["value_checkpoint"]
        self.assertEqual(len(value["history"]), 1)
        self.assertEqual(value["history"][0]["trigger"], "THREE_ACCEPTED_IMPLEMENTATION_CARDS")
        self.assertEqual(value["history"][0]["new_accepted_implementation_card_ids"],
                         ["W01-01", "W01-02", "W01-03"])
        self.assertEqual(value["formal_gate"]["overall"], "OPEN_PENDING_INDEPENDENT_FORMAL_CASE_EVIDENCE")
        self.assertEqual(result["accepted_steps"], ["W00-01", "W00-99"])

    def test_two_rounds_make_checkpoint_two_scaffolding_checkpoints_reprioritize(self):
        self.call(4, baseline=True)
        first = self.call(5, event_path=self.round("r1", "DOCUMENTATION"))
        self.assertEqual(first["value_checkpoint"]["status"], "PENDING_THRESHOLD")
        second = self.call(6, event_path=self.round("r2", "FIXTURE"))
        self.assertEqual(second["value_checkpoint"]["history"][0]["trigger"],
                         "TWO_ROUNDS_WITHOUT_USER_CAPABILITY")
        self.assertEqual(second["value_checkpoint"]["documentation_only_checkpoints"], 1)
        self.call(7, event_path=self.round("r3", "INFRASTRUCTURE"))
        fourth = self.call(8, event_path=self.round("r4", "FIXTURE"))
        value = fourth["value_checkpoint"]
        self.assertEqual(value["documentation_only_checkpoints"], 2)
        self.assertEqual(value["status"], "PRIORITIZE_USER_FLOW")
        self.assertTrue(value["pause_nonblocking_expansion"])
        self.assertEqual(value["recommended_flow"]["next_step_id"], "W17-02")
        self.assertEqual(fourth["no_progress_rounds"], 2)
        self.assertEqual(len(value["history"]), 2)

    def test_real_observation_can_be_early_checkpoint_without_claiming_acceptance(self):
        self.call(4, baseline=True)
        result = self.call(5, event_path=self.round("http", "USER_FLOW", "HTTP resource request returns next step"),
                           force=True, reason="W12 resource HTTP client increment observed")
        value = result["value_checkpoint"]
        self.assertEqual(value["history"][0]["trigger"], "MANUAL_EARLY")
        self.assertEqual(value["documentation_only_checkpoints"], 0)
        self.assertEqual(value["capabilities_observed"][0]["authority"], "DEVELOPMENT_OBSERVATION_ONLY")
        self.assertEqual(value["formal_gate"]["overall"], "OPEN_PENDING_INDEPENDENT_FORMAL_CASE_EVIDENCE")

    def test_next_selection_consumes_priority_and_never_retries_failed_cards(self):
        current = {"value_checkpoint": {"pause_nonblocking_expansion": True}}
        plan = json.loads(self.plan.read_text(encoding="utf-8"))
        state = json.loads(self.state.read_text(encoding="utf-8"))
        delivery = json.loads(self.delivery.read_text(encoding="utf-8"))
        _, statuses, plans = checkpoint.accepted_and_status(state, plan)
        self.assertEqual(checkpoint.prioritized_step(current, statuses, plans, delivery, "W01-01"), "W17-02")
        for blocked in ("FAILED", "CANCELLED", "BLOCKED", "EXECUTION_REPORTED"):
            statuses["W17-02"] = blocked
            self.assertIsNone(checkpoint.prioritized_step(current, statuses, plans, delivery, "W01-01"))
        current["value_checkpoint"]["pause_nonblocking_expansion"] = False
        self.assertEqual(checkpoint.prioritized_step(current, statuses, plans, delivery, "W01-01"), "W01-01")


if __name__ == "__main__":
    cases = {
        "test_baseline_uses_actual_state_and_does_not_invent_history": "W1202-U09-BASELINE-GATES",
        "test_stale_revision_and_unverified_event_leave_bytes_unchanged": "W1202-U09-CAS-EVIDENCE",
        "test_three_accepted_cards_trigger_one_checkpoint_without_formal_acceptance": "W1202-U09-THREE-CARDS",
        "test_two_rounds_make_checkpoint_two_scaffolding_checkpoints_reprioritize": "W1202-U09-TWO-ROUNDS-REPLAN",
        "test_real_observation_can_be_early_checkpoint_without_claiming_acceptance": "W1202-U09-EARLY-OBSERVATION",
        "test_next_selection_consumes_priority_and_never_retries_failed_cards": "W1202-U09-PRIORITY-CONSUMED",
    }
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ValueCheckpointTest)
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
    passed = result.wasSuccessful() and result.testsRun == len(cases) and not result.skipped
    report = {"status": "PASS" if passed else "FAIL",
              "assertion_ids": list(cases.values()) if passed else [],
              "assertions": len(cases) if passed else 0,
              "scope": "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE"}
    print(json.dumps(report, ensure_ascii=False))
    raise SystemExit(0 if passed else 1)
