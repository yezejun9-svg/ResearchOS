"""Explicit handler stubs; these unit tests never constitute LIVE positives."""
import importlib.util
import json
import sqlite3
import hashlib
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("w07_sources_gate", ROOT / "ops/ci/sources.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
spec = importlib.util.spec_from_file_location("w07_forward", Path(__file__).with_name("main.py"))
forward = importlib.util.module_from_spec(spec)
spec.loader.exec_module(forward)


class ParentGateTests(unittest.TestCase):
    def test_zero_missing_or_skipped_tests_cannot_pass(self):
        for result in ({"exit_code": 0, "passed": [], "missing": []},
                       {"exit_code": 0, "passed": sorted(gate.EXPECTED - {next(iter(gate.EXPECTED))}), "missing": []},
                       {"exit_code": 0, "passed": sorted(gate.EXPECTED), "missing": [], "timed_out": True}):
            self.assertFalse(gate.fixture_ok(result))

    def test_missing_report_and_injected_positive_cannot_pass_live(self):
        self.assertFalse(gate.validate_source_report({"scope": "LIVE_SERVICE", "items": [{}]}))
        self.assertFalse(gate.validate_source_report({"scope": "INJECTED", "items": [{}]}))
        self.assertFalse(gate.x_claim_has_primary_lineage({"claim_check": {"conclusion": "SUPPORTED_NARROW_SCOPE", "adoption_authority": True}}))

    def test_exact_h07_forward_and_mixed_selector_refusal(self):
        class Result:
            stdout = '{"status":"BLOCKED","assertion_ids":[]}\n'
            returncode = 1
        with patch.object(forward.subprocess, "run", return_value=Result()) as run:
            report, code = forward.forward("W07", "W07-H07", "")
            self.assertEqual(run.call_args.kwargs["env"]["RESEARCHOS_SOURCE_MODE"], "live")
            self.assertEqual(code, 1)
            self.assertEqual(report["status"], "BLOCKED")
        for check, case in (("W07-H07", "A05"), ("unknown", "")):
            with patch.dict(os.environ, {"RESEARCHOS_TASK_ID": "W07", "RESEARCHOS_CHECK_ID": check, "RESEARCHOS_CASE_ID": case, "RESEARCHOS_SOURCE_MODE": "live"}):
                with self.assertRaises(NotImplementedError): gate.main()

    def test_one_failed_source_does_not_suppress_other_sources(self):
        calls = []
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            directory = Path(temporary)
            def child(argv, evidence, stem, **kwargs):
                calls.append(stem)
                out, err = directory / (stem + ".stdout"), directory / (stem + ".stderr")
                out.write_text("explicit unit stub\n", encoding="utf-8")
                err.write_text("", encoding="utf-8")
                if stem == "build":
                    Path(argv[argv.index("-o") + 1]).write_bytes(b"explicit unit stub")
                    return 0, out, err, False
                return 1, out, err, False
            with patch.object(gate, "run_process", side_effect=child), patch.dict(os.environ, {"RESEARCHOS_BROWSER_ACT": "", "RESEARCHOS_BROWSER_ID": ""}):
                result = gate.live("explicit-unit-go-stub", directory, {})
            self.assertEqual(calls, ["build", "github", "paper", "x"])
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(set(result["assertions"]), {"A05-0" + str(n) for n in range(1, 6)})
            self.assertFalse(any(result["assertions"].values()))

    def test_report_selected_post_must_equal_sealed_disposition(self):
        # Explicit checker fixture: actual SQLite, but not a LIVE capture.
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            path=Path(temporary)/"checker.sqlite"
            db=sqlite3.connect(path)
            db.executescript("CREATE TABLE domain_objects(project,kind,id,body); CREATE TABLE uploaded_content(project,storage_key,bytes);")
            project="checker-fixture"
            def insert(kind,obj):
                db.execute("INSERT INTO domain_objects VALUES(?,?,?,?)",(project,kind,obj["id"],json.dumps(obj)))
            def artifact(id,body,refs):
                raw=body if isinstance(body,bytes) else json.dumps(body).encode()
                a={"id":id,"revision":1,"content_hash":"sha256:"+hashlib.sha256(raw).hexdigest(),"storage_key":id,"source_refs":refs,"input_refs":refs}
                insert("Artifact",a);db.execute("INSERT INTO uploaded_content VALUES(?,?,?)",(project,id,raw))
                return gate.manifest_artifact_ref(a)
            bodyref=artifact("body",b"public uncorroborated claim",[])
            ev={"id":"actual-selected-second-post","revision":1,"content_hash":None,"source_kind":"X","stance":"CONTEXT","verification_status":"UNVERIFIED","snapshot_artifact_ref":bodyref}
            insert("Evidence",ev);xref=gate.domain_ref(ev,"Evidence")
            claim={"conclusion":"NOT_CORROBORATED","adoption_authority":False,"reason":"fixture primary unavailable","x_evidence_ref":xref,"x_snapshot_ref":bodyref,"primary_evidence_ref":None}
            ref=artifact("disposition",claim,[xref]);db.commit();db.close()
            report={"scope":"FIXTURE","project_id":project,"db_path":str(path.relative_to(ROOT)),"items":[{"evidence_id":"unrelated-first"},{"evidence_id":ev["id"]}],"claim_check":dict(claim,artifact_ref=ref)}
            self.assertTrue(gate.x_claim_has_primary_lineage(report))
            bad=copy.deepcopy(report);bad["claim_check"]["x_evidence_ref"]["id"]="wrong-selected-post"
            self.assertFalse(gate.x_claim_has_primary_lineage(bad))
            bad=copy.deepcopy(report);bad["items"]=[{"evidence_id":"unrelated-first"}]
            self.assertFalse(gate.x_claim_has_primary_lineage(bad))
            bad=copy.deepcopy(report);bad["claim_check"]["primary_evidence_ref"]={"id":"fake-primary"}
            self.assertFalse(gate.x_claim_has_primary_lineage(bad))

    def test_no_typed_h07_rows_cannot_pass(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            directory = Path(temporary)
            (directory / "fixture.stdout").write_text('{"Action":"pass"}\n', encoding="utf-8")
            self.assertFalse(gate.verify_h07_evidence(directory))


if __name__ == "__main__":
    unittest.main()
