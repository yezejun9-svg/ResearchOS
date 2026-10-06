"""Local tooling tests using copies of actual W07 raw and SQLite evidence.

These tests never create product LIVE acceptance. Supply an immutable collection
directory with W07_ACTUAL_PROOF_DIR; no browser/provider/model calls are made.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import timedelta
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent


def trusted(name):
    path = HERE / (name + ".py")
    spec = importlib.util.spec_from_file_location("test_trusted_" + name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


API = trusted("formal_case_index")
PROFILE = trusted("formal_profile_w07")


class W07RawControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        supplied = os.environ.get("W07_ACTUAL_PROOF_DIR")
        if not supplied:
            raise ValueError("W07_ACTUAL_PROOF_DIR must name a recorded real collection; tests cannot fabricate LIVE")
        cls.original = Path(supplied).resolve(strict=True)
        cls.template = API.strict_json((cls.original / "proof.json").read_bytes())
        cls.source_root = next(p for p in cls.original.parents if
                               cls.original.is_relative_to(p / PROFILE.PREFIX))
        cls.tmp = tempfile.TemporaryDirectory(prefix="researchos-w07-tooling-controls-")
        cls.repo = Path(cls.tmp.name)
        relative = cls.original.relative_to(cls.source_root)
        cls.collection = cls.repo / relative
        cls.collection.mkdir(parents=True)
        cls.copied = {}

        def copy_ref(ref):
            path = ref["path"]
            if path not in cls.copied:
                src = cls.source_root / path
                expected = PROFILE._digest(ref["sha256"])
                if hashlib.sha256(src.read_bytes()).hexdigest() != expected:
                    raise ValueError("original evidence drift: " + path)
                dst = cls.repo / path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
                cls.copied[path] = expected
        for row in cls.template["source_invocations"]:
            for key in ("stdout_ref", "stderr_ref", "report_ref", "db_snapshot_ref", "request_inputs_ref"):
                copy_ref(row[key])
        for row in cls.template["h07_invocations"]:
            for key in ("stdout_ref", "stderr_ref", "assertions_ref"):
                copy_ref(row[key])
            for ref in row["db_snapshots"]:
                copy_ref(ref)
        copy_ref(cls.template["live_binary_ref"])
        for key in ("source_before_ref", "source_after_ref", "version_vector_ref", "build_invocation_ref", "compilation_inputs_ref"):
            copy_ref(cls.template[key])
        cls.compilation_ref = {"path": (cls.original / "go-list.invocation.json").relative_to(cls.source_root).as_posix(),
                               "sha256": hashlib.sha256((cls.original / "go-list.invocation.json").read_bytes()).hexdigest()}
        copy_ref(cls.compilation_ref)
        for invocation_ref in (cls.compilation_ref, cls.template["build_invocation_ref"]):
            invocation = API.strict_json((cls.source_root / invocation_ref["path"]).read_bytes())
            for key in ("stdout_ref", "stderr_ref"):
                copy_ref(invocation[key])
        locked = cls.repo / "execution/toolchains/locked.json"
        locked.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(cls.source_root / "execution/toolchains/locked.json", locked)
        cls.source_before = API.strict_json((cls.source_root / cls.template["source_before_ref"]["path"]).read_bytes())
        for name, digest in cls.source_before.items():
            copy_ref({"path": name, "sha256": digest})
        baseline_source = Path(os.environ["W07_ACCEPTANCE_BASELINE_PATH"]).resolve(strict=True)
        if hashlib.sha256(baseline_source.read_bytes()).hexdigest() != API.FROZEN_HASHES["acceptance.json"]:
            raise ValueError("changed frozen acceptance baseline")
        baseline_destination = cls.repo / "spec/v2.4/contracts/acceptance.json"
        baseline_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(baseline_source, baseline_destination)
        cls.baseline_ref = {"path": "spec/v2.4/contracts/acceptance.json", "sha256": API.FROZEN_HASHES["acceptance.json"]}
        manifest_source = baseline_source.parent.parent / "PACKAGE_MANIFEST.json"
        if hashlib.sha256(manifest_source.read_bytes()).hexdigest() != "4666920727e189ed91dc84dae919f7ab9e52a2f9c45efd697ecdd790107d3964":
            raise ValueError("changed frozen package manifest")
        manifest_destination = cls.repo / "spec/v2.4/PACKAGE_MANIFEST.json"
        shutil.copyfile(manifest_source, manifest_destination)
        cls.package_ref = {"path": "spec/v2.4/PACKAGE_MANIFEST.json", "sha256": hashlib.sha256(manifest_source.read_bytes()).hexdigest()}
        report_source = cls.original / "report.json"
        cls.execution_report_ref = {"path": report_source.relative_to(cls.source_root).as_posix(),
                                    "sha256": hashlib.sha256(report_source.read_bytes()).hexdigest()}
        copy_ref(cls.execution_report_ref)
        copy_ref({"path": (cls.original / "proof.json").relative_to(cls.source_root).as_posix(),
                  "sha256": hashlib.sha256((cls.original / "proof.json").read_bytes()).hexdigest()})
        cls.bounds = API.interval(cls.template, "actual proof")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def reader(self):
        return API.Reader(self.repo)

    def rejects(self, fn, codes):
        with self.assertRaises(API.InvalidEvidence) as caught:
            fn()
        self.assertIn(caught.exception.code, codes)

    def test_actual_three_source_graphs(self):
        reader = self.reader()
        for row in self.template["source_invocations"]:
            with self.subTest(kind=row["kind"]):
                report = PROFILE._source(API, reader, row, self.bounds, {}, self.template["live_binary_ref"])
                self.assertGreaterEqual(len(report["items"]), 1)
        reader.finish()

    def test_actual_h07_thirteen_snapshots(self):
        reader = self.reader()
        rows = PROFILE._h07(API, reader, self.template["h07_invocations"][0], self.bounds)
        self.assertEqual(len(rows), 13)
        reader.finish()

    def test_actual_compilation_inputs_cover_source(self):
        tools = API.strict_json((self.repo / self.template["version_vector_ref"]["path"]).read_bytes())["tool"]
        reader = self.reader()
        PROFILE._compiled_inputs(API, reader, {"compilation_invocation_ref": self.compilation_ref},
                                 self.template, self.source_before, tools, self.bounds)
        reader.finish()

    def product_control(self):
        """Actual product evidence; this context is never registered or accepted."""
        proof_path = self.collection / "proof.json"
        context = {"executor_id": self.template["executor_id"], "run_id": self.template["run_id"],
                   "proof_ref": {"path": proof_path.relative_to(self.repo).as_posix(), "sha256": hashlib.sha256(proof_path.read_bytes()).hexdigest()},
                   "version_vector": {"source_files": [{"path": name, "sha256": PROFILE._digest(digest)} for name, digest in self.source_before.items()],
                                      "input_files": [], "lock_files": []},
                   "compilation_invocation_ref": self.compilation_ref, "acceptance_baseline_ref": self.baseline_ref}
        tools = API.strict_json((self.repo / "execution/toolchains/locked.json").read_bytes())["tools"]
        return context, tools

    def test_actual_full_product_proof_at_frozen_baseline(self):
        context, tools = self.product_control()
        reader = self.reader()
        proof, reports = PROFILE.product(API, reader, context, tools)
        self.assertEqual(set(reports), {"GITHUB", "PAPER", "X"})
        self.assertEqual([r["id"] for r in proof["assertion_rows"]], list(PROFILE.IDS))
        reader.finish()
        self.rejects(lambda: PROFILE.verify_owner(API, self.reader(), {"status": "IN_PROGRESS"}, {}, Path("unused")), {"OWNER_NOT_ACCEPTED"})

    def test_product_tool_vector_cannot_be_empty(self):
        context, tools = self.product_control()
        proof = deepcopy(self.template)
        vector = PROFILE._document(API, self.reader(), proof["version_vector_ref"])
        vector["tool"] = {}
        proof["version_vector_ref"] = self.write_control("empty-product-tools.json", vector)
        context["proof_ref"] = self.write_control("empty-tools-proof.json", proof)
        self.rejects(lambda: PROFILE.product(API, self.reader(), context, tools), {"TOOL_LOCK"})

    def test_compiled_source_cannot_be_removed(self):
        tools = API.strict_json((self.repo / self.template["version_vector_ref"]["path"]).read_bytes())["tool"]
        before = dict(self.source_before)
        del before["internal/domain/operations.go"]
        self.rejects(lambda: PROFILE._compiled_inputs(API, self.reader(), {"compilation_invocation_ref": self.compilation_ref},
                       self.template, before, tools, self.bounds), {"SOURCE_COVERAGE"})

    def inventory_control(self, mutation):
        context, tools = self.product_control()
        proof = deepcopy(self.template)
        invocation = PROFILE._document(API, self.reader(), self.compilation_ref)
        text = PROFILE._bytes(API, self.reader(), invocation["stdout_ref"]).decode("utf-8")
        decoder, offset, packages = json.JSONDecoder(), 0, []
        while offset < len(text):
            if text[offset].isspace():
                offset += 1
                continue
            package, offset = decoder.raw_decode(text, offset)
            packages.append(package)
        packages = mutation(packages)
        invocation["stdout_ref"] = proof["compilation_inputs_ref"] = self.write_bytes("changed-inventory.jsonl",
                            b"\n".join(json.dumps(package).encode("utf-8") for package in packages))
        context["compilation_invocation_ref"] = self.write_control("changed-inventory-invocation.json", invocation)
        before = dict(self.source_before)
        before.pop("internal/canonical/jcs.go")
        proof["source_before_ref"] = self.write_control("omitted-source-before.json", before)
        proof["source_after_ref"] = self.write_control("omitted-source-after.json", before)
        vector = PROFILE._document(API, self.reader(), proof["version_vector_ref"])
        vector["source"] = before
        proof["version_vector_ref"] = self.write_control("omitted-product-vector.json", vector)
        context["proof_ref"] = self.write_control("omitted-package-proof.json", proof)
        return context, tools

    def test_whole_compiled_package_omission_rejected(self):
        name = "researchos.local/research-os/internal/canonical"
        context, tools = self.inventory_control(lambda packages: [p for p in packages if p.get("ImportPath") != name])
        self.rejects(lambda: PROFILE.product(API, self.reader(), context, tools), {"SOURCE_COVERAGE"})

    def test_omission_with_deleted_dependency_links_rejected(self):
        name = "researchos.local/research-os/internal/canonical"
        def mutate(packages):
            for package in packages:
                for key in ("Imports", "Deps"):
                    if key in package:
                        package[key] = [p for p in package[key] if p != name]
            return [p for p in packages if p.get("ImportPath") != name]
        context, tools = self.inventory_control(mutate)
        self.rejects(lambda: PROFILE.product(API, self.reader(), context, tools), {"SOURCE_COVERAGE"})

    def test_compiled_package_cannot_alias_another_directory(self):
        name = "researchos.local/research-os/internal/canonical"
        def mutate(packages):
            for package in packages:
                if package.get("ImportPath") == name:
                    package["Dir"] = str(Path(self.template["h07_invocations"][0]["cwd"]) / "internal/domain")
                    package["GoFiles"] = []
            return packages
        context, tools = self.inventory_control(mutate)
        self.rejects(lambda: PROFILE.product(API, self.reader(), context, tools), {"SOURCE_COVERAGE"})

    def test_receipt_selected_gofiles_cannot_hide_production_imports(self):
        name = "researchos.local/research-os/internal/canonical"
        recorded_root = Path(self.template["h07_invocations"][0]["cwd"])
        def mutate(packages):
            for package in packages:
                for key in ("Imports", "Deps"):
                    if key in package:
                        package[key] = [p for p in package[key] if p != name]
                if package.get("ImportPath", "").startswith("researchos.local/research-os/") and package.get("ImportPath") != name:
                    relative = Path(package["Dir"]).relative_to(recorded_root)
                    remaining = [f for f in package.get("GoFiles", []) if name.encode("utf-8") not in (self.repo / relative / f).read_bytes()]
                    if remaining:
                        package["GoFiles"] = remaining
            return [p for p in packages if p.get("ImportPath") != name]
        context, tools = self.inventory_control(mutate)
        self.rejects(lambda: PROFILE.product(API, self.reader(), context, tools), {"SOURCE_COVERAGE"})

    def test_h07_forged_command_rejected(self):
        row = deepcopy(self.template["h07_invocations"][0])
        row["actualargv"] = ["C:/missing/forged-python.exe", "--claim-success"]
        self.rejects(lambda: PROFILE._h07(API, self.reader(), row, self.bounds), {"H07_COMMAND"})

    def test_h07_removed_lifecycle_rejected(self):
        row = deepcopy(self.template["h07_invocations"][0])
        events = [API.strict_json(line) for line in PROFILE._bytes(API, self.reader(), row["stdout_ref"]).splitlines()]
        events = [e for e in events if e["Action"] not in {"run", "start"} and not (e["Action"] == "pass" and not e.get("Test"))]
        row["stdout_ref"] = self.write_bytes("no-lifecycle.jsonl", b"\n".join(json.dumps(e).encode("utf-8") for e in events))
        self.rejects(lambda: PROFILE._h07(API, self.reader(), row, self.bounds), {"H07_TEST_RESULTS"})

    def test_h07_duplicate_pass_rejected(self):
        row = deepcopy(self.template["h07_invocations"][0])
        content = PROFILE._bytes(API, self.reader(), row["stdout_ref"])
        event = next(API.strict_json(line) for line in content.splitlines() if API.strict_json(line).get("Action") == "pass")
        row["stdout_ref"] = self.write_bytes("duplicate-pass.jsonl", content + json.dumps(event).encode("utf-8") + b"\n")
        self.rejects(lambda: PROFILE._h07(API, self.reader(), row, self.bounds), {"H07_TEST_RESULTS"})

    def test_h07_cached_command_rejected(self):
        row = deepcopy(self.template["h07_invocations"][0])
        row["actualargv"].remove("-count=1")
        self.rejects(lambda: PROFILE._h07(API, self.reader(), row, self.bounds), {"H07_COMMAND"})

    def test_query_declarations_cannot_replace_sealed_query(self):
        row = deepcopy(self.template["source_invocations"][0])
        report = PROFILE._document(API, self.reader(), row["report_ref"])
        inputs = PROFILE._document(API, self.reader(), row["request_inputs_ref"])
        report["query"] = inputs["query"] = "forged unrelated query that never ran"
        row["report_ref"] = row["stdout_ref"] = self.write_control("forged-query-report.json", report)
        row["request_inputs_ref"] = self.write_control("forged-query-inputs.json", inputs)
        self.rejects(lambda: PROFILE._source(API, self.reader(), row, self.bounds, {}, self.template["live_binary_ref"]), {"DB_HEALTH_BINDING"})

    def test_fixture_x_cannot_satisfy_positive(self):
        row = deepcopy(next(r for r in self.template["source_invocations"] if r["kind"] == "X"))
        row["measurement_mode"] = "FIXTURE"
        self.rejects(lambda: PROFILE._source(API, self.reader(), row, self.bounds, {}, self.template["live_binary_ref"]), {"COMMAND_EXIT"})

    def test_nonzero_exit_cannot_satisfy_positive(self):
        row = deepcopy(self.template["source_invocations"][0]); row["exit_code"] = 1
        self.rejects(lambda: PROFILE._source(API, self.reader(), row, self.bounds, {}, self.template["live_binary_ref"]), {"COMMAND_EXIT"})

    def test_timeout_cannot_satisfy_positive(self):
        row = deepcopy(self.template["source_invocations"][0]); row["timed_out"] = True
        self.rejects(lambda: PROFILE._source(API, self.reader(), row, self.bounds, {}, self.template["live_binary_ref"]), {"COMMAND_EXIT"})

    def test_input_window_mismatch_rejected(self):
        row = deepcopy(self.template["source_invocations"][0])
        value = PROFILE._document(API, self.reader(), row["request_inputs_ref"])
        value["window_from"] = "2020-01-01T00:00:00Z"
        row["request_inputs_ref"] = self.write_control("bad-window.json", value)
        self.rejects(lambda: PROFILE._source(API, self.reader(), row, self.bounds, {}, self.template["live_binary_ref"]), {"SOURCE_REQUEST"})

    def test_wrong_browser_rejected(self):
        row = deepcopy(next(r for r in self.template["source_invocations"] if r["kind"] == "X"))
        value = PROFILE._document(API, self.reader(), row["request_inputs_ref"])
        value["browser_id"] = "unregistered-browser"
        row["request_inputs_ref"] = self.write_control("bad-browser.json", value)
        self.rejects(lambda: PROFILE._source(API, self.reader(), row, self.bounds, {}, self.template["live_binary_ref"]), {"AUTHORIZED_BROWSER"})

    def test_missing_raw_rejected(self):
        row = deepcopy(self.template["source_invocations"][0])
        row["stdout_ref"]["path"] = PROFILE.PREFIX + "absent.stdout"
        self.rejects(lambda: PROFILE._source(API, self.reader(), row, self.bounds, {}, self.template["live_binary_ref"]), {"FILE_MISSING"})

    def test_forged_database_hash_rejected(self):
        row = deepcopy(self.template["source_invocations"][0]); row["db_snapshot_ref"]["sha256"] = "0" * 64
        self.rejects(lambda: PROFILE._source(API, self.reader(), row, self.bounds, {}, self.template["live_binary_ref"]), {"HASH_MISMATCH"})

    def test_uncheckpointed_database_rejected(self):
        ref = self.template["source_invocations"][0]["db_snapshot_ref"]
        path = Path(str(self.repo / ref["path"]) + "-wal")
        path.write_bytes(b"nonempty unresolved WAL")
        try:
            self.rejects(lambda: PROFILE.Graph(API, self.reader(), ref, True), {"DB_SNAPSHOT"})
        finally:
            path.unlink()

    def test_database_must_be_closed(self):
        ref = self.template["source_invocations"][0]["db_snapshot_ref"]
        self.rejects(lambda: PROFILE.Graph(API, self.reader(), ref, False), {"DB_SNAPSHOT"})

    def test_raw_locator_is_bounded(self):
        ref = dict(self.template["source_invocations"][0]["report_ref"], locator={"json_pointer": ""})
        self.assertTrue(PROFILE.raw(API, self.reader(), ref)["items"])
        ref["locator"] = {"json_pointer": "/"}
        self.rejects(lambda: PROFILE.raw(API, self.reader(), ref), {"RAW_LOCATOR_MISSING"})

    def test_raw_path_traversal_rejected(self):
        ref = {"path": PROFILE.PREFIX + "../other.json", "sha256": "0" * 64, "locator": {"json_pointer": ""}}
        self.rejects(lambda: PROFILE.raw(API, self.reader(), ref), {"PATH_ESCAPE"})

    def test_w04_raw_boundary_stays_separate(self):
        ref = dict(self.template["source_invocations"][0]["report_ref"], locator={"json_pointer": ""})
        ref["sha256"] = PROFILE._digest(ref["sha256"])
        self.rejects(lambda: self.reader().raw(ref), {"PATH_SCOPE"})

    def test_same_source_wrong_x_item_rejected(self):
        row = next(r for r in self.template["source_invocations"] if r["kind"] == "X")
        reader = self.reader(); report = PROFILE._document(API, reader, row["report_ref"])
        report["items"][0]["evidence_id"] = "unrelated-X-item"
        graph = PROFILE.Graph(API, reader, row["db_snapshot_ref"], True)
        try:
            self.rejects(lambda: PROFILE._claim(API, graph, report), {"X_SELECTED_ITEM"})
        finally: graph.close()

    def test_x_cannot_gain_adoption_authority(self):
        row = next(r for r in self.template["source_invocations"] if r["kind"] == "X")
        reader = self.reader(); report = PROFILE._document(API, reader, row["report_ref"])
        report["claim_check"]["adoption_authority"] = True
        graph = PROFILE.Graph(API, reader, row["db_snapshot_ref"], True)
        try:
            self.rejects(lambda: PROFILE._claim(API, graph, report), {"X_ADOPTION"})
        finally: graph.close()

    def test_report_cannot_change_selected_x_reference(self):
        row = next(r for r in self.template["source_invocations"] if r["kind"] == "X")
        reader = self.reader(); report = PROFILE._document(API, reader, row["report_ref"])
        report["claim_check"]["x_evidence_ref"]["id"] = "wrong-selected-post"
        graph = PROFILE.Graph(API, reader, row["db_snapshot_ref"], True)
        try:
            self.rejects(lambda: PROFILE._claim(API, graph, report), {"X_SELECTED_ITEM"})
        finally: graph.close()

    def test_synthetic_h07_labels_without_raw_rejected(self):
        row = deepcopy(self.template["h07_invocations"][0])
        rows = PROFILE._document(API, self.reader(), row["assertions_ref"])
        rows[0]["status"] = "FAIL"
        row["assertions_ref"] = self.write_control("fake-h07-labels.json", rows)
        self.rejects(lambda: PROFILE._h07(API, self.reader(), row, self.bounds), {"H07_RAW_ROWS"})

    def test_zero_tests_rejected(self):
        row = deepcopy(self.template["h07_invocations"][0])
        row["stdout_ref"] = self.write_bytes("zero-tests.jsonl", b'{"Action":"pass","Package":"fixture"}\n')
        self.rejects(lambda: PROFILE._h07(API, self.reader(), row, self.bounds), {"H07_TEST_RESULTS"})

    def test_skipped_test_rejected(self):
        row = deepcopy(self.template["h07_invocations"][0])
        content = PROFILE._bytes(API, self.reader(), row["stdout_ref"])
        content += b'{"Action":"skip","Package":"fixture","Test":"must-not-skip"}\n'
        row["stdout_ref"] = self.write_bytes("skipped-tests.jsonl", content)
        self.rejects(lambda: PROFILE._h07(API, self.reader(), row, self.bounds), {"H07_TEST_RESULTS"})

    def test_input_mutation_after_read_rejected(self):
        ref = self.write_control("mutating.json", {"before": True})
        reader = self.reader(); PROFILE._document(API, reader, ref)
        (self.repo / ref["path"]).write_bytes(b'{"after":true}')
        self.rejects(reader.finish, {"INPUT_CHANGED_DURING_READ"})

    def test_conflicting_roots_rejected(self):
        evidence = []
        for key, schema in PROFILE.SCHEMAS.items():
            ref = self.write_control(key + "-root.json", {"schema": schema})
            evidence.append(dict(ref, path=ref["path"][len("execution/v2.4/"):]))
        ref = self.write_control("duplicate-review.json", {"schema": PROFILE.SCHEMAS["review"]})
        evidence.append(dict(ref, path=ref["path"][len("execution/v2.4/"):]))
        self.rejects(lambda: API._registered_roots(self.reader(), {"evidence": evidence}, "W07"), {"CONFLICTING_REVIEW"})

    def test_unregistered_roots_rejected(self):
        ref = self.write_control("unregistered-root.json", {"schema": "irrelevant.v1"})
        self.rejects(lambda: API._registered_roots(self.reader(), {"evidence": [dict(ref, path=ref["path"][len("execution/v2.4/"):])]}, "W07"), {"MISSING_REGISTERED_GLOBAL_ROOT"})

    def test_future_owner_has_no_profile(self):
        self.rejects(lambda: API._registered_roots(self.reader(), {"evidence": []}, "W08"), {"UNSUPPORTED_PROTOCOL"})

    def test_pending_owner_cannot_accept(self):
        self.rejects(lambda: PROFILE.verify_owner(API, self.reader(), {"status": "IN_PROGRESS"}, {}, Path("unused")), {"OWNER_NOT_ACCEPTED"})

    def test_tooling_source_never_loaded_from_receipts(self):
        # A receipt-supplied module is inert; fixed repository module is absent.
        with tempfile.TemporaryDirectory(prefix="researchos-w07-receipt-inert-") as folder:
            repo = Path(folder)
            foreign = repo / PROFILE.PREFIX / "formal_profile_w07.py"
            foreign.parent.mkdir(parents=True)
            foreign.write_bytes(b'raise RuntimeError("receipt executed")\n')
            self.rejects(lambda: API._w07_profile(API.Reader(repo)), {"FILE_MISSING"})

    def test_five_ids_required(self):
        self.rejects(lambda: API.exact_ids(list(PROFILE.IDS[:-1]), PROFILE.IDS, "A05"), {"ID_SET"})

    def test_protected_w04_prefix_is_unchanged(self):
        actual = (HERE / "formal_case_index.py").read_bytes()[:51719]
        self.assertEqual(hashlib.sha256(actual).hexdigest(), "92341c7d3a49a4d2ee9e3519ff2897e1950c33aff2876124c11e556b78e134e1")

    def vector_control(self, missing_module=False):
        refs = []
        for name in sorted(PROFILE.MINIMUM_SOURCE):
            if missing_module and name == PROFILE.MODULE:
                continue
            source = HERE / Path(name).name if name in {PROFILE.MODULE, "execution/v2.4/formal_case_index.py"} else self.source_root / name
            destination = self.repo / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            content = source.read_bytes()
            destination.write_bytes(content)
            refs.append({"path": name, "sha256": hashlib.sha256(content).hexdigest()})
        anchor = self.template["source_invocations"][0]["report_ref"]
        anchor = dict(anchor, sha256=PROFILE._digest(anchor["sha256"]))
        vector = {"schema": "researchos.w07.version-vector.v1", "package_version": "2.4.0",
                  "spec_files": [anchor], "source_files": refs, "input_files": [anchor], "lock_files": [anchor],
                  "tool_files": [anchor], "environment": {}, "components": {}}
        return {"version_vector": vector, "source_coverage": {"roots": [{"path": "execution/v2.4", "patterns": ["*.py"]}],
                 "exact_files": [r["path"] for r in refs], "paths_sha256": API.object_sha256(sorted(r["path"] for r in refs))}}

    def test_source_inventory_cannot_omit_profile_module(self):
        context = self.vector_control(missing_module=True)
        self.rejects(lambda: PROFILE._vector(API, self.reader(), context), {"SOURCE_COVERAGE"})

    def test_changed_module_needs_revalidation(self):
        context = self.vector_control()
        (self.repo / PROFILE.MODULE).write_bytes(b'"changed tooling module"\n')
        self.rejects(lambda: PROFILE._vector(API, self.reader(), context), {"NEEDS_REVALIDATION"})

    def independent_control(self, *, same_actor=False, delivery=True, reverse_time=False, proof_mismatch=False):
        """Synthetic issuance shape control, never registered on any parent."""
        proof_path = self.collection / "proof.json"
        proof_ref = {"path": proof_path.relative_to(self.repo).as_posix(), "sha256": hashlib.sha256(proof_path.read_bytes()).hexdigest()}
        ended = self.bounds[1]
        executor = "fixture-executor"
        reviewer = executor if same_actor else "fixture-independent-reviewer"
        context = {"schema": PROFILE.SCHEMAS["context"], "task_id": "W07", "step_id": "W07-99",
                   "executor_id": executor, "run_id": self.template["run_id"], "version_vector": {},
                   "acceptance_baseline_ref": {"path": PROFILE.PREFIX + "unread-baseline-shape-control.json", "sha256": API.FROZEN_HASHES["acceptance.json"]},
                   "proof_ref": proof_ref, "created_at": (ended + timedelta(seconds=1)).isoformat()}
        context_ref = self.write_control("independent-context.json", context)
        raw_ref = dict(self.template["source_invocations"][0]["report_ref"], locator={"json_pointer": ""})
        review = {"schema": PROFILE.SCHEMAS["review"], "task_id": "W07", "step_id": "W07-99",
                  "executor_id": executor, "reviewer_id": reviewer, "run_id": context["run_id"],
                  "context_ref": context_ref, "proof_ref": proof_ref, "decision": "ACCEPTED", "missing": [], "failed": [],
                  "acceptance_baseline_ref": context["acceptance_baseline_ref"], "evidence_index_ref": context_ref,
                  "version_vector": {}, "issued_at": (ended + timedelta(seconds=2)).isoformat(),
                  "assertion_verdicts": [{"id": ident, "status": "PASS", "actual": {"scope": "LOCAL_SYNTHETIC_SHAPE"}, "raw_evidence_refs": [raw_ref]} for ident in PROFILE.IDS],
                  "gate_verdicts": [{"id": ident, "status": "PASS", "actual": {"scope": "LOCAL_SYNTHETIC_SHAPE"}, "raw_evidence_refs": [raw_ref]} for ident in PROFILE.GATES]}
        if proof_mismatch: review["proof_ref"] = dict(proof_ref, sha256="0" * 64)
        review_ref = self.write_control("independent-review.json", review)
        message = {"schema": "researchos.root-received-independent-message.v1", "recorded_by": "codex:/root",
                   "recipient": "codex:/root", "sender": reviewer, "event_type": "MESSAGE", "review_ref": review_ref,
                   "received_at": (ended + timedelta(seconds=3)).isoformat(),
                   "content": "Local synthetic shape control; review " + review_ref["sha256"] + "; proof " + proof_ref["sha256"]}
        if not delivery: message["sender"] = "fixture-executor-authored-claim"
        message_ref = self.write_control("independent-message.json", message)
        issuance = {"schema": PROFILE.SCHEMAS["issuance"], "task_id": "W07", "step_id": "W07-99",
                    "actor": "codex:/root", "executor_id": executor, "reviewer_id": reviewer,
                    "run_id": context["run_id"], "context_ref": context_ref, "review_ref": review_ref,
                    "delivery_ref": message_ref, "observed_at": (ended + timedelta(seconds=4)).isoformat()}
        issuance_ref = self.write_control("independent-issuance.json", issuance)
        accepted = ended + timedelta(seconds=0 if reverse_time else 5)
        return ({"accepted_at": accepted.isoformat()}, self.repo / context_ref["path"], self.repo / review_ref["path"],
                self.repo / issuance_ref["path"], context)

    def test_distinct_actor_without_received_review_is_rejected(self):
        args = self.independent_control(delivery=False)
        self.rejects(lambda: PROFILE._independent(API, self.reader(), *args), {"ROOT_OBSERVED_DELIVERY"})

    def test_executor_cannot_review_itself(self):
        args = self.independent_control(same_actor=True)
        self.rejects(lambda: PROFILE._independent(API, self.reader(), *args), {"INDEPENDENT_ACTOR"})

    def test_actor_case_variant_cannot_review_itself(self):
        args = self.independent_control()
        review_path = args[2]
        review = API.strict_json(review_path.read_bytes())
        review["reviewer_id"] = args[-1]["executor_id"].upper()
        review_path.write_bytes(json.dumps(review).encode("utf-8"))
        self.rejects(lambda: PROFILE._independent(API, self.reader(), *args), {"INDEPENDENT_ACTOR"})

    def test_observer_cannot_be_reviewer(self):
        args = self.independent_control()
        review = API.strict_json(args[2].read_bytes())
        review["reviewer_id"] = "codex:/root"
        args[2].write_bytes(json.dumps(review).encode("utf-8"))
        self.rejects(lambda: PROFILE._independent(API, self.reader(), *args), {"INDEPENDENT_ACTOR"})

    def test_reversed_acceptance_time_is_rejected(self):
        args = self.independent_control(reverse_time=True)
        self.rejects(lambda: PROFILE._independent(API, self.reader(), *args), {"REGISTERED_TIME_ORDER"})

    def test_review_of_another_proof_is_rejected(self):
        args = self.independent_control(proof_mismatch=True)
        self.rejects(lambda: PROFILE._independent(API, self.reader(), *args), {"REVIEW_PROOF"})

    def test_issuance_shape_control_without_registration(self):
        args = self.independent_control()
        reader = self.reader()
        PROFILE._independent(API, reader, *args)
        reader.finish()
        # This low-level shape result cannot move canonical parent acceptance.
        self.rejects(lambda: PROFILE.verify_owner(API, reader, {"status": "IN_PROGRESS"}, {}, Path("unused")), {"OWNER_NOT_ACCEPTED"})

    def test_missing_global_evidence_files_rejected(self):
        self.rejects(lambda: PROFILE._global(API, self.reader(), {}, self.template, None), {"TYPE_OBJECT", "MISSING_FIELD"})

    def global_control(self):
        """Local GLOBAL shape with actual raw evidence; no registered commands/acceptance."""
        context, _ = self.product_control()
        vector = context["version_vector"]
        vector["environment"] = {"os": "Windows", "arch": "amd64", "timezone": "Asia/Shanghai"}
        vector["spec_files"] = [self.package_ref, self.baseline_ref]
        context["registered_commands"] = []  # Full owner validation independently refuses this.
        context["execution_report_ref"] = self.execution_report_ref
        review_ref = self.write_control("global-shape-review.json", {"reviewer_id": "local-shape-verifier", "scope": "LOCAL_GLOBAL_SHAPE_ONLY"})
        proof, execution = self.template, PROFILE._document(API, self.reader(), self.execution_report_ref)
        run = {"schema": "researchos.w07.run-receipt.v1", "case_id": "A05", "run_id": context["run_id"],
               "environment_mode": "LIVE_SERVICE", **vector["environment"], "started_at": proof["started_at"], "ended_at": proof["ended_at"],
               "executor_id": context["executor_id"], "verifier_id": "local-shape-verifier"}
        manifest = {"schema": "researchos.w07.version-manifest.v1", "case_id": "A05", "run_id": context["run_id"],
                    "package_version": "2.4.0", "package_manifest_ref": self.package_ref, "code_revision": execution["execution_head"],
                    "dirty": bool(execution["dirty_before"]), "version_vector_ref": self.write_control("global-shape-vector.json", vector),
                    "product_version_vector_ref": proof["version_vector_ref"]}
        command = {"schema": "researchos.w07.command-receipt.v1", "case_id": "A05", "run_id": context["run_id"],
                   "registered_commands": [], "source_invocations": proof["source_invocations"], "h07_invocations": proof["h07_invocations"],
                   "build_invocation_ref": proof["build_invocation_ref"]}
        refusal = dict(proof["h07_invocations"][0]["assertions_ref"], locator={"json_pointer": "/0"})
        assertions = {"schema": "researchos.w07.assertion-results.v1", "case_id": "A05", "run_id": context["run_id"],
                      "assertions": [dict(row, refusal_evidence_refs=[refusal], command_keys=["test.sources.live"]) for row in proof["assertion_rows"]]}
        context["global_evidence_refs"] = {name: self.write_control("global-shape-" + name + ".json", value) for name, value in
                  (("run_receipt", run), ("version_manifest", manifest), ("command_receipt", command), ("assertion_results", assertions))}
        return context, self.repo / review_ref["path"]

    def test_global_shape_closes_actual_product_refs_without_accepting_owner(self):
        context, review_path = self.global_control()
        reader = self.reader()
        PROFILE._global(API, reader, context, self.template, review_path)
        reader.finish()
        self.rejects(lambda: PROFILE.verify_owner(API, self.reader(), {"status": "IN_PROGRESS"}, {}, Path("unused")), {"OWNER_NOT_ACCEPTED"})

    def test_global_capture_commit_cannot_be_replaced(self):
        context, review_path = self.global_control()
        manifest = PROFILE._document(API, self.reader(), context["global_evidence_refs"]["version_manifest"])
        manifest["code_revision"] = "0" * 40
        context["global_evidence_refs"]["version_manifest"] = self.write_control("wrong-global-commit.json", manifest)
        self.rejects(lambda: PROFILE._global(API, self.reader(), context, self.template, review_path), {"CODE_REVISION"})

    def test_global_missing_refusal_evidence_rejected(self):
        context, review_path = self.global_control()
        assertions = PROFILE._document(API, self.reader(), context["global_evidence_refs"]["assertion_results"])
        assertions["assertions"][0]["refusal_evidence_refs"] = []
        context["global_evidence_refs"]["assertion_results"] = self.write_control("missing-global-refusal.json", assertions)
        self.rejects(lambda: PROFILE._global(API, self.reader(), context, self.template, review_path), {"TYPE_ARRAY"})

    def test_global_evidence_files_must_be_distinct(self):
        ref = self.template["source_invocations"][0]["report_ref"]
        context = {"global_evidence_refs": {name: ref for name in ("run_receipt", "version_manifest", "command_receipt", "assertion_results")}}
        self.rejects(lambda: PROFILE._global(API, self.reader(), context, self.template, None), {"DUPLICATE_REFERENCE"})

    def write_control(self, name, value):
        return self.write_bytes(name, (json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8"))

    def write_bytes(self, name, content):
        path = self.collection / ("control-" + name)
        path.write_bytes(content)
        return {"path": path.relative_to(self.repo).as_posix(), "sha256": hashlib.sha256(content).hexdigest()}


if __name__ == "__main__":
    unittest.main(verbosity=2)
