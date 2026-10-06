"""Ten synthetic registration-boundary controls; no product execution."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
BASE = HERE.parent
REPO = BASE.parents[5]
sys.path.insert(0, str(BASE))
import validate as local
import test_validate as builder

builder.HERE = HERE  # Every synthetic write stays in this owned directory.
spec = importlib.util.spec_from_file_location("registration_repair_public", REPO / "execution/v2.4/formal_case_index.py")
public = importlib.util.module_from_spec(spec)
spec.loader.exec_module(public)
DISPATCHER = "execution/command_dispatcher/dispatch.py"
STATE = "execution/v2.4/step_state.json"
I, E = builder.I, builder.E


class RegistrationRepairControls(unittest.TestCase):
    def setUp(self):
        self.f = builder.Fixture()
        vector = self.f.docs[E + "vector.json"]
        vector["source_files"] = [r for r in vector["source_files"] if r["path"] != DISPATCHER]
        self.f.context["version_vector"] = copy.deepcopy(vector)
        self.f.context["source_coverage"]["exact_files"] = []
        self.f.sync()

    def tearDown(self):
        self.f.close()

    def read(self, reader):
        if reader == "local":
            return self.f.check("registered")
        return public.derive_formal_cases(self.f.root, self.f.root / STATE,
                                          self.f.spec / "contracts/execution.plan.json")

    def positive(self, reader):
        result = self.read(reader)
        if reader == "local":
            self.assertEqual(result["formal_accepted_count"], 3)
        else:
            self.assertEqual(result["integrity"], "PASS", result["reasons"])
            self.assertEqual(result["accepted_case_ids"], ["A01", "C03", "C04"])
        # Registration-only dispatcher bytes must be tracked despite their
        # deliberate absence from the earlier synthetic product source vector.
        self.assertNotIn(DISPATCHER, [r["path"] for r in self.f.context["version_vector"]["source_files"]])
        self.assertEqual(result["input_hashes"][str(self.f.root / DISPATCHER)], local.sha256(self.f.root / DISPATCHER))
        return result

    def rejected(self, reader, code):
        if reader == "local":
            with self.assertRaises(local.InvalidEvidence) as caught:
                self.read(reader)
            self.assertEqual(caught.exception.code, code)
        else:
            result = self.read(reader)
            self.assertEqual(result["formal_cases_accepted"], 0, result)
            owner = next(x for x in result["owners"] if x["task_id"] == "W04")
            self.assertEqual(owner["reasons"][0]["code"], code, owner)

    def control(self, reader, scenario):
        initial = self.positive(reader)
        observation = "native/current dispatcher matched without an earlier product pin"
        if scenario == "wrong_native_hash":
            path = I + "dispatch-1.json"
            self.f.docs[path]["dispatcher_sha256"] = "f" * 64
            self.f.override.add((path, "dispatcher_sha256"))
            self.f.sync()
            self.rejected(reader, "DISPATCHER_CHANGED")
            observation = "wrong native receipt digest refused as DISPATCHER_CHANGED"
        elif scenario == "changed_current_bytes":
            self.f.write_bytes(DISPATCHER, b"# changed synthetic dispatcher; never executed\n")
            self.rejected(reader, "DISPATCHER_CHANGED")
            observation = "current dispatcher bytes differing from native receipt refused"
        elif scenario == "post_read_change":
            if reader == "local":
                finish = local.Reader.finish
                injected = []
                def change_before_finish(instance):
                    path = self.f.root / DISPATCHER
                    self.assertIn(path, instance.read_hashes)
                    if not injected:
                        self.f.write_bytes(DISPATCHER, b"# synthetic mutation after registered reads\n")
                        injected.append(True)
                    return finish(instance)
                with patch.object(local.Reader, "finish", change_before_finish):
                    self.rejected(reader, "INPUT_CHANGED_DURING_READ")
                self.assertEqual(injected, [True])
                observation = "Reader.finish refused dispatcher change after registered reads"
            else:
                snapshot = initial["dependency_snapshot"]
                self.assertIn(str(self.f.root / DISPATCHER), snapshot["files"])
                self.assertEqual(public.recheck_inputs(snapshot), {"status": "PASS"})
                self.f.write_bytes(DISPATCHER, b"# synthetic mutation after aggregation\n")
                result = public.recheck_inputs(snapshot)
                self.assertEqual(result["status"], "INVALID")
                self.assertIn("INPUT_CHANGED_DURING_READ", result["reason"])
                observation = "recheck_inputs refused dispatcher change after aggregation"
        elif scenario == "child_input_unpinned":
            vector = self.f.docs[E + "vector.json"]
            vector["source_files"] = [r for r in vector["source_files"] if r["path"] != "source/driver.py"]
            self.f.context["version_vector"] = copy.deepcopy(vector)
            self.f.context["source_coverage"]["roots"] = [{"path": "source", "patterns": ["*.go"]}]
            self.f.sync()
            self.rejected(reader, "DISPATCH_INPUT_UNPINNED")
            observation = "child input still requires earlier product pin"
        elif scenario != "dispatcher_not_in_product_vector":
            self.fail("unknown control")
        print("REGISTRATION_REPAIR_CONTROL " + json.dumps({"reader": reader, "scenario": scenario,
              "status": "PASS", "observation": observation, "scope": "SYNTHETIC_INTEGRITY_ONLY",
              "real_formal_case_count_delta": 0, "product_commands_executed": 0}))


def make_control(reader, scenario):
    def test(self):
        self.control(reader, scenario)
    return test

for _reader in ("local", "public"):
    for _scenario in ("dispatcher_not_in_product_vector", "wrong_native_hash", "changed_current_bytes",
                      "post_read_change", "child_input_unpinned"):
        setattr(RegistrationRepairControls, "test_" + _reader + "_" + _scenario, make_control(_reader, _scenario))

if __name__ == "__main__":
    unittest.main(verbosity=2)
