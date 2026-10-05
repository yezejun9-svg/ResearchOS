"""Synthetic public aggregation/CAS controls; no product commands or acceptance."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
BASE = HERE.parent
REPO = BASE.parents[5]
sys.path.insert(0, str(BASE))
import test_validate as builder

# Reuse only the frozen fake-data builder. All assertions call the public module.
builder.HERE = HERE
spec = importlib.util.spec_from_file_location("public_formal_case_index", REPO / "execution/v2.4/formal_case_index.py")
public = importlib.util.module_from_spec(spec)
spec.loader.exec_module(public)
STATE = "execution/v2.4/step_state.json"
P, E, I = builder.P, builder.E, builder.I


class GenericControls(unittest.TestCase):
    def setUp(self):
        self.f = builder.Fixture()

    def tearDown(self):
        self.f.close()

    def derive(self):
        return public.derive_formal_cases(self.f.root, self.f.root / STATE,
                                        self.f.spec / "contracts/execution.plan.json")

    def owner(self, result, task="W04"):
        return next(row for row in result["owners"] if row["task_id"] == task)

    def failed_owner(self, code, status=None):
        result = self.derive()
        self.assertEqual(result["formal_cases_accepted"], 0, result["reasons"])
        owner = self.owner(result)
        self.assertEqual(owner["reasons"][0]["code"], code, owner)
        if status:
            self.assertEqual(owner["integrity"], status)
        return result

    def fingerprint(self):
        return {str(path.relative_to(self.f.root)): public.sha256(path)
                for path in self.f.root.rglob("*") if path.is_file()}

    def test_complete_synthetic_registration_contributes_only_three(self):
        result = self.derive()
        self.assertEqual(result["integrity"], "PASS", result["reasons"])
        self.assertEqual(result["accepted_case_ids"], ["A01", "C03", "C04"])
        self.assertEqual(result["formal_cases_accepted"], 3)
        self.assertEqual(len(result["cases"]), 42)
        self.assertEqual(len(result["owners"]), 22)
        self.assertFalse(result["product_business_acceptance_created"])
        self.assertEqual(public.recheck_inputs(result["dependency_snapshot"]), {"status": "PASS"})

    def test_empty_accepted_owners_do_not_create_cases(self):
        self.f.docs[STATE]["steps"][-1]["status"] = "NOT_STARTED"
        self.f.sync()
        result = self.derive()
        self.assertEqual(result["formal_cases_accepted"], 0)
        self.assertTrue(all(self.owner(result, tid)["integrity"] == "EMPTY_OWNER" for tid in ("W00", "W01", "W02", "W03")))

    def test_nonaccepted_owner_does_not_scan_valid_candidate_evidence(self):
        self.f.docs[STATE]["steps"][-1]["status"] = "EXECUTION_REPORTED"
        self.f.sync()
        result = self.derive()
        self.assertEqual(result["formal_cases_accepted"], 0)
        self.assertEqual(self.owner(result)["integrity"], "PENDING_OWNER_ACCEPTANCE")

    def test_valid_files_without_canonical_registration_do_not_promote(self):
        self.f.docs[STATE]["steps"][-1]["evidence"].pop()
        self.f.sync()
        self.failed_owner("MISSING_REGISTERED_GLOBAL_ROOT", "PARTIAL")

    def test_reading_is_byte_for_byte_read_only(self):
        before = self.fingerprint()
        self.derive()
        self.assertEqual(before, self.fingerprint())

    def test_source_change_invalidates_without_erasing_history(self):
        self.assertEqual(self.derive()["formal_cases_accepted"], 3)
        review = self.f.root / (P + "independent_review.json")
        digest = public.sha256(review)
        state = public.sha256(self.f.root / STATE)
        self.f.write_bytes("source/product.go", b"// changed synthetic source\n")
        self.failed_owner("NEEDS_REVALIDATION", "NEEDS_REVALIDATION")
        self.assertEqual(public.sha256(review), digest)
        self.assertEqual(public.sha256(self.f.root / STATE), state)

    def test_added_applicable_source_invalidates(self):
        self.f.write_bytes("source/new.go", b"// new applicable file\n")
        self.failed_owner("NEEDS_REVALIDATION", "NEEDS_REVALIDATION")

    def test_removed_applicable_source_invalidates(self):
        (self.f.root / "source/product.go").unlink()
        self.failed_owner("NEEDS_REVALIDATION", "NEEDS_REVALIDATION")

    def test_unrelated_source_extension_does_not_invalidate(self):
        self.f.write_bytes("source/notes.md", b"synthetic excluded extension")
        self.assertEqual(self.derive()["formal_cases_accepted"], 3)

    def test_raw_hash_tampering_fails_closed(self):
        self.f.write_bytes(E + "C03/observations.json", b'{"observation":"tampered"}')
        self.failed_owner("HASH_MISMATCH")

    def test_mode_downgrade_fails_closed(self):
        self.f.docs[P + "independent_review.json"]["owned_case_verdicts"][0]["mode"] = "MOCK"
        self.f.sync()
        result = self.derive()
        self.assertEqual(result["formal_cases_accepted"], 0)
        self.assertEqual(self.owner(result)["integrity"], "INVALID")

    def test_wrong_final_owner_fails_closed(self):
        self.f.docs[P + "independent_review.json"]["owned_case_verdicts"][0]["final_owner_task"] = "W05"
        self.f.sync()
        self.assertEqual(self.derive()["formal_cases_accepted"], 0)

    def test_missing_assertion_fails_closed(self):
        self.f.docs[P + "independent_review.json"]["owned_case_verdicts"][0]["assertion_ids"].pop()
        self.f.sync()
        self.assertEqual(self.derive()["formal_cases_accepted"], 0)

    def test_self_review_fails_closed(self):
        self.f.docs[P + "independent_review.json"]["verifier_id"] = builder.EX
        self.f.sync()
        self.assertEqual(self.derive()["formal_cases_accepted"], 0)

    def test_unobserved_identity_string_fails_closed(self):
        self.f.docs[I + "message.json"]["sender"] = "synthetic:someone-else"
        self.f.sync()
        self.assertEqual(self.derive()["formal_cases_accepted"], 0)

    def test_conflicting_registered_review_fails_closed(self):
        other = P + "another-review.json"
        self.f.docs[other] = copy.deepcopy(self.f.docs[P + "independent_review.json"])
        self.f.docs[STATE]["steps"][-1]["evidence"].append(builder.ref(other.removeprefix("execution/v2.4/")))
        self.f.sync()
        self.failed_owner("CONFLICTING_REVIEW")

    def test_unregistered_extra_review_is_not_discovered_by_glob(self):
        self.f.write_bytes(P + "unregistered-review.json", b'{"schema":"researchos.w04.independent-review.v1","invalid":true}')
        self.assertEqual(self.derive()["formal_cases_accepted"], 3)

    def test_duplicate_global_state_id_invalidates_entire_aggregate(self):
        self.f.docs[STATE]["steps"].append(copy.deepcopy(self.f.docs[STATE]["steps"][-1]))
        self.f.sync()
        result = self.derive()
        self.assertEqual(result["integrity"], "INVALID")
        self.assertEqual(result["formal_cases_accepted"], 0)
        self.assertEqual(result["reasons"][0]["code"], "STATE_IDS")

    def test_unknown_global_state_id_invalidates_entire_aggregate(self):
        self.f.docs[STATE]["steps"].append({"id": "W99-99", "status": "ACCEPTED"})
        self.f.sync()
        self.assertEqual(self.derive()["integrity"], "INVALID")

    def test_corrupted_frozen_catalog_invalidates_entire_aggregate(self):
        with (self.f.spec / "contracts/acceptance.json").open("ab") as stream:
            stream.write(b" ")
        result = self.derive()
        self.assertEqual(result["integrity"], "INVALID")
        self.assertEqual(result["formal_cases_accepted"], 0)
        self.assertEqual(result["reasons"][0]["code"], "FROZEN_BASELINE")

    def test_unsupported_owner_cannot_erase_valid_w04_cases(self):
        self.f.docs[STATE]["steps"].append({"id": "W05-99", "status": "ACCEPTED", "evidence": []})
        self.f.sync()
        result = self.derive()
        self.assertEqual(result["integrity"], "PARTIAL")
        self.assertEqual(result["formal_cases_accepted"], 3)
        self.assertEqual(self.owner(result, "W05")["reasons"][0]["code"], "UNSUPPORTED_PROTOCOL")

    def test_cas_catches_changed_file_after_derivation(self):
        snapshot = self.derive()["dependency_snapshot"]
        self.f.write_bytes("source/product.go", b"// changed after derive\n")
        self.assertEqual(public.recheck_inputs(snapshot)["status"], "INVALID")

    def test_cas_catches_added_source_after_derivation(self):
        snapshot = self.derive()["dependency_snapshot"]
        self.f.write_bytes("source/added.py", b"# added after derive\n")
        self.assertEqual(public.recheck_inputs(snapshot)["status"], "INVALID")

    def test_cas_catches_removed_source_after_derivation(self):
        snapshot = self.derive()["dependency_snapshot"]
        (self.f.root / "source/product.go").unlink()
        self.assertEqual(public.recheck_inputs(snapshot)["status"], "INVALID")

    def test_cas_catches_canonical_state_change_after_derivation(self):
        snapshot = self.derive()["dependency_snapshot"]
        with (self.f.root / STATE).open("ab") as stream:
            stream.write(b" ")
        self.assertEqual(public.recheck_inputs(snapshot)["status"], "INVALID")

    def change_live_registry(self, mutate):
        path = self.f.root / "execution/v2.4/commands.json"
        registry = json.loads(path.read_text(encoding="utf-8"))
        mutate(registry)
        path.write_text(json.dumps(registry), encoding="utf-8")

    def test_unrelated_new_registry_entry_preserves_retained_evidence(self):
        self.change_live_registry(lambda registry: registry["commands"].update({"unrelated.future.key": {"synthetic": True}}))
        result = self.derive()
        self.assertEqual(result["formal_cases_accepted"], 3, result["reasons"])

    def test_changed_used_registry_entry_needs_revalidation(self):
        key = self.f.bindings[0]["key"]
        self.change_live_registry(lambda registry: registry["commands"][key].update({"argv": ["changed-driver"]}))
        self.failed_owner("NEEDS_REVALIDATION", "NEEDS_REVALIDATION")

    def test_removed_used_registry_entry_needs_revalidation(self):
        key = self.f.bindings[0]["key"]
        self.change_live_registry(lambda registry: registry["commands"].pop(key))
        self.failed_owner("NEEDS_REVALIDATION", "NEEDS_REVALIDATION")


if __name__ == "__main__":
    unittest.main(verbosity=2)
