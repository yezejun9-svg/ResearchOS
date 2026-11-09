"""Candidate security controls only; no product execution or acceptance issuance."""
import copy
import hashlib
import json
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest
import uuid


CANDIDATE = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[4]
EVIDENCE = REPO / "execution/v2.4/receipts/W09/W09-99/resume_cp398_formal_audit_codex/20261012-current-chat"
CERT_PATH = EVIDENCE / "header-correction.candidate-v2.json"


class CorrectionControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = runpy.run_path(str(CANDIDATE / "execution/v2.4/formal_case_index.py"), run_name="candidate_index")
        cls.api = cls.index["_profile_api"]()
        cls.m = runpy.run_path(str(CANDIDATE / "execution/v2.4/w09_header_correction.py"), run_name="candidate_recovery")
        cls.profile = runpy.run_path(str(CANDIDATE / "execution/v2.4/formal_profile_w09.py"), run_name="candidate_profile")
        cls.cert = json.loads(CERT_PATH.read_text(encoding="utf-8"))
        cls.roots = {k: REPO / v["path"] for k, v in cls.cert["original_roots"].items()}
        cls.cert_ref = {"path": CERT_PATH.relative_to(REPO).as_posix(),
                        "sha256": hashlib.sha256(CERT_PATH.read_bytes()).hexdigest(),
                        "bytes": CERT_PATH.stat().st_size}
        cls.old = (REPO / cls.cert["audit_bindings"][0]["original_capture_ref"]["path"]).read_bytes().splitlines(keepends=True)[0]
        with Path(cls.m["OLD_LOG"]).open("rb") as stream:
            cls.current = stream.readline()
        cls.roles = json.loads((REPO / cls.cert["role_registry_ref"]["path"]).read_text(encoding="utf-8"))

    def reader(self):
        reader = self.api.Reader(REPO)
        reader.w09_audit_ranges = []
        return reader

    def refused(self, code, function, *args):
        with self.assertRaises(self.api.InvalidEvidence) as raised:
            function(*args)
        self.assertEqual(raised.exception.code, code)

    def evidence(self, cert=None):
        reader = self.reader()
        self.m["certificate_evidence"](self.api, reader, cert or self.cert, self.roots)
        reader.finish()
        return reader

    def test_actual_certificate_evidence_and_range_recheck(self):
        reader = self.evidence()
        self.assertEqual(len(reader.w09_audit_ranges), 18)
        snapshot = {"files": {str(p): digest for p, digest in reader.read_hashes.items()},
                    "audit_ranges": reader.w09_audit_ranges, "inventories": []}
        self.assertEqual(self.index["recheck_inputs"](snapshot), {"status": "PASS"})

    def test_exact_observed_header_delta(self):
        self.m["header_delta"](self.api, self.old, self.current)
        result = self.m["audit_line"](self.api, self.cert, 0, self.m["OLD_HEADER_SHA"], self.old, self.current)
        self.assertEqual(result["sha256"], self.m["NEW_HEADER_SHA"])

    def test_header_requires_explicit_authority(self):
        self.refused("CORRECTION_EVENT_CHANGED", self.m["audit_line"], self.api, None,
                     0, self.m["OLD_HEADER_SHA"], self.old, self.current)

    def test_second_header_field_refused(self):
        changed = json.loads(self.current)
        changed["payload"]["originator"] = "SYNTHETIC_NEGATIVE_CONTROL"
        self.refused("CORRECTION_HEADER_DELTA", self.m["header_delta"], self.api,
                     self.old, json.dumps(changed).encode())

    def test_removed_header_field_refused(self):
        changed = json.loads(self.current)
        del changed["payload"]["cwd"]
        self.refused("CORRECTION_HEADER_DELTA", self.m["header_delta"], self.api,
                     self.old, json.dumps(changed).encode())

    def test_different_provider_transition_refused(self):
        changed = json.loads(self.current)
        changed["payload"]["model_provider"] = "another-provider"
        self.refused("CORRECTION_HEADER_DELTA", self.m["header_delta"], self.api,
                     self.old, json.dumps(changed).encode())

    def test_json_equivalent_but_different_header_bytes_refused(self):
        changed = json.dumps(json.loads(self.current), indent=2).encode() + b"\n"
        self.refused("CORRECTION_HEADER_PIN", self.m["audit_line"], self.api, self.cert,
                     0, self.m["OLD_HEADER_SHA"], self.old, changed)

    def test_changed_frozen_header_refused(self):
        self.refused("CORRECTION_HEADER_PIN", self.m["audit_line"], self.api, self.cert,
                     0, self.m["OLD_HEADER_SHA"], b" " + self.old, self.current)

    def test_nonzero_offset_cannot_use_header_correction(self):
        self.refused("CORRECTION_EVENT_CHANGED", self.m["audit_line"], self.api, self.cert,
                     1, self.m["OLD_HEADER_SHA"], self.old, self.current)

    def test_each_actual_role_call_result_must_remain_exact(self):
        for binding in self.cert["audit_bindings"][:-1]:
            lines = (REPO / binding["original_capture_ref"]["path"]).read_bytes().splitlines(keepends=True)
            for i in (1, 2):
                with self.subTest(role=binding["role"], line=i):
                    self.refused("CORRECTION_EVENT_CHANGED", self.m["audit_line"], self.api, self.cert,
                                 binding["source_line_offsets"][i], binding["original_line_sha256"][i],
                                 lines[i], b" " + lines[i])

    def test_actual_formal_delivery_must_remain_exact(self):
        binding = self.cert["audit_bindings"][-1]
        lines = (REPO / binding["original_capture_ref"]["path"]).read_bytes().splitlines(keepends=True)
        for i in (1, 2):
            with self.subTest(line=i):
                self.refused("CORRECTION_EVENT_CHANGED", self.m["audit_line"], self.api, self.cert,
                             binding["source_line_offsets"][i], binding["original_line_sha256"][i],
                             lines[i], b" " + lines[i])

    def test_certificate_hash_drift_refused(self):
        scratch = CANDIDATE / "tests" / ("pin-drift-" + uuid.uuid4().hex + ".json")
        try:
            scratch.write_bytes(CERT_PATH.read_bytes())
            ref = dict(self.cert_ref, path=scratch.relative_to(REPO).as_posix())
            self.m["pinned"](self.api, self.reader(), ref)
            scratch.write_bytes(scratch.read_bytes() + b" ")
            self.refused("HASH_MISMATCH", self.m["pinned"], self.api, self.reader(), ref)
        finally:
            # Only this exact newly created leaf is removed; no recursive cleanup.
            scratch.unlink(missing_ok=True)

    def test_current_header_certificate_pin_cannot_be_replaced(self):
        changed = copy.deepcopy(self.cert)
        changed["new_header_sha256"] = "0" * 64
        self.refused("CORRECTION_SCOPE", self.evidence, changed)

    def test_missing_formal_delivery_binding_refused(self):
        changed = copy.deepcopy(self.cert)
        changed["audit_bindings"].pop()
        self.refused("CORRECTION_AUDIT_BINDINGS", self.evidence, changed)

    def test_foreign_project_refused(self):
        changed = copy.deepcopy(self.cert)
        changed["project_id"] = "SYNTHETIC_OTHER_PROJECT"
        self.refused("CORRECTION_PROJECT", self.evidence, changed)

    def test_current_chat_cannot_impersonate_historical_chat(self):
        changed = copy.deepcopy(self.cert)
        changed["prepared_in_thread"] = self.m["OLD_THREAD"]
        self.refused("CORRECTION_SCOPE", self.evidence, changed)

    def test_business_source_cannot_use_interpreter_compatibility(self):
        changed = copy.deepcopy(self.cert)
        changed["new_profile_ref"]["path"] = "internal/domain/retrieval_test.go"
        self.refused("CORRECTION_INTERPRETER_SCOPE", self.evidence, changed)

    def test_unmodified_index_pin_is_required(self):
        changed = copy.deepcopy(self.cert)
        changed["index_ref"]["sha256"] = "0" * 64
        self.refused("CORRECTION_INTERPRETER_SCOPE", self.evidence, changed)

    def review_fixture(self, actor):
        # Pure claim fixture. It is never written or represented as a real peer message.
        return {"schema": "researchos.w09.correction-independent-review.v1",
                "scope": "INTERPRETER_RECOVERY_ONLY", "decision": "ACCEPTED_RECOVERY_SOURCE_ONLY",
                "reviewer_id": actor, "author_id": self.m["AUTHOR"], "issued_at": self.cert["created_at"],
                "certificate_ref": self.cert_ref,
                "checks": {name: "PASS" for name in self.m["REVIEW_CHECKS"]}, "evidence_refs": []}

    def test_candidate_author_and_executor_cannot_approve(self):
        for actor in (self.m["AUTHOR"], "codex:" + self.m["AUTHOR"], "CODEX:/ROOT/RESUME_AUDIT",
                      "/root", "codex:/root", self.roles["roles"]["source_authors"][0]):
            with self.subTest(actor=actor):
                self.refused("CORRECTION_REVIEW", self.m["review_claim"], self.api, self.cert,
                             self.cert_ref, self.roles, self.review_fixture(actor))

    def test_missing_review_control_cannot_be_pass(self):
        review = self.review_fixture("/root/synthetic_non_author")
        review["checks"].pop("negative_controls")
        self.refused("CORRECTION_REVIEW", self.m["review_claim"], self.api, self.cert,
                     self.cert_ref, self.roles, review)

    def test_canonical_authority_is_absent(self):
        self.assertIsNone(self.profile["_header_correction"](self.api, self.reader(), self.roots))

    def test_receipt_python_cannot_replace_fixed_module(self):
        authority = {"schema": "researchos.w09.header-correction-authority.v1",
                     "certificate_ref": {}, "review_ref": {}, "delivery_ref": {},
                     "verifier_module_ref": {"path": "execution/v2.4/receipts/evil.py", "sha256": "0" * 64, "bytes": 1}}
        fixture_reader = SimpleNamespace(path=lambda value: Path(value),
                                         read=lambda value: {"work_in_progress": {"w09_header_metadata_correction": authority}})
        self.refused("CORRECTION_MODULE", self.profile["_header_correction"], self.api, fixture_reader, self.roots)


if __name__ == "__main__":
    unittest.main(verbosity=2)
