"""Isolated synthetic actual checkpoint writes and CAS rejection controls."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

from test_generic import builder, public, REPO, STATE, E

spec = importlib.util.spec_from_file_location("synthetic_checkpoint", REPO / "bootstrap/v24_checkpoint.py")
checkpoint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checkpoint)


class CheckpointIntegrationControls(unittest.TestCase):
    def setUp(self):
        self.f = builder.Fixture()
        self.cp = self.f.root / "execution/v2.4/checkpoint.json"
        self.plan = self.f.spec / "contracts/execution.plan.json"
        self.delivery = self.f.spec / "contracts/delivery.contract.json"
        shutil.copyfile(builder.REAL_SPEC / "contracts/delivery.contract.json", self.delivery)
        shutil.copyfile(REPO / "execution/v2.4/formal_case_index.py", self.f.root / "execution/v2.4/formal_case_index.py")
        self.write(self.cp, {"revision": 1, "plan_sha256": public.sha256(self.plan),
                            "status": "SYNTHETIC_ONLY", "historical_root_field": {"preserve": True},
                            "value_checkpoint": {"status": "NOT_RUN", "capabilities_observed": [],
                                                 "documentation_only_checkpoints": 0}})

    def tearDown(self):
        self.f.close()

    def write(self, path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def call(self, revision, **kwargs):
        return checkpoint.update_file(self.cp, self.f.root / STATE, self.plan, self.delivery,
                                      revision, actor="synthetic:integration-control", **kwargs)

    def event(self, ident):
        path = self.f.root / (ident + ".json")
        self.write(path, {"schema": checkpoint.ROUND_SCHEMA, "round_id": ident,
                          "delta": "DOCUMENTATION", "summary": "SYNTHETIC integration-only observation",
                          "evidence_refs": [{"path": E + "C03/observations.json",
                                             "sha256": public.sha256(self.f.root / (E + "C03/observations.json"))}]})
        return path

    def test_actual_update_derives_three_and_preserves_history(self):
        baseline = self.call(1, baseline=True)
        self.assertEqual(baseline["value_checkpoint"]["formal_gate"]["formal_cases_accepted"], 3)
        first = self.call(2, event_path=self.event("synthetic-round-1"), force=True, reason="synthetic integration")
        old_history = copy.deepcopy(first["value_checkpoint"]["history"])
        self.assertEqual(len(old_history), 1)
        second = self.call(3, event_path=self.event("synthetic-round-2"), force=True, reason="synthetic integration")
        self.assertEqual(second["value_checkpoint"]["history"][:1], old_history)
        self.assertEqual(len(second["value_checkpoint"]["history"]), 2)
        self.assertEqual(second["value_checkpoint"]["formal_gate"]["accepted_case_ids"], ["A01", "C03", "C04"])
        self.assertEqual(second["historical_root_field"], {"preserve": True})
        self.assertEqual(second["revision"], 4)
        self.assertEqual(json.loads(self.cp.read_text(encoding="utf-8")), second)

    def test_actual_update_rejects_post_derive_raw_and_inventory_changes(self):
        self.call(1, baseline=True)
        original_loader = checkpoint.formal_reader
        raw_path = self.f.root / (E + "C03/observations.json")
        raw_before = raw_path.read_bytes()
        added_path = self.f.root / "source/new-after-derive.go"
        for mutation in ("raw", "inventory"):
            with self.subTest(mutation=mutation):
                observed = []
                def injected_loader(root):
                    module = original_loader(root)
                    derive = module.derive_formal_cases
                    def mutate_after_derive(*args, **kwargs):
                        result = derive(*args, **kwargs)
                        observed.append(result["formal_cases_accepted"])
                        if mutation == "raw":
                            raw_path.write_bytes(b'{"observation":"post-derive tamper"}')
                        else:
                            added_path.write_bytes(b"// SYNTHETIC covered file after derivation\n")
                        return result
                    module.derive_formal_cases = mutate_after_derive
                    return module
                before = self.cp.read_bytes()
                event = self.event("synthetic-cas-" + mutation)
                with patch.object(checkpoint, "formal_reader", side_effect=injected_loader):
                    with self.assertRaisesRegex(checkpoint.CheckpointError, "formal evidence changed before replace"):
                        self.call(2, event_path=event)
                self.assertEqual(observed, [3])
                self.assertEqual(self.cp.read_bytes(), before)
                self.assertFalse(self.cp.with_name(self.cp.name + ".value.lock").exists())
                self.assertEqual(list(self.cp.parent.glob("checkpoint.json.value.*.tmp")), [])
                raw_path.write_bytes(raw_before)
                if added_path.exists():
                    assert added_path.resolve().is_relative_to(self.f.root.resolve())
                    added_path.unlink()


if __name__ == "__main__":
    unittest.main(verbosity=2)
