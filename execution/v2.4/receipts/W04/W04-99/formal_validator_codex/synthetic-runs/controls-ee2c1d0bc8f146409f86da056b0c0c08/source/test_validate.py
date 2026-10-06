"""Purely synthetic integrity controls. No product commands or real acceptance."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import validate as v


HERE = Path(__file__).resolve().parent
REAL_REPO = HERE.parents[5]
REAL_SPEC = REAL_REPO / ".local/worktrees/v24-continuation/spec/v2.4"
P = v.PREFIX
E = P + "executor_codex/synthetic/"
I = v.ROOT_INPUT_PREFIX
RUN = "SYNTHETIC_CONTROL_NOT_PRODUCT_RUN"
EX = "synthetic:executor"
VE = "synthetic:independent-verifier"
AT = "2026-10-01T01:00:00+00:00"
END = "2026-10-01T01:01:00+00:00"
ISSUED = "2026-10-01T01:02:00+00:00"
OBSERVED = "2026-10-01T01:03:00+00:00"
CODE = "1" * 40


def ref(path):
    return {"path": path, "sha256": "0" * 64}


def raw(path, pointer="/observation"):
    return {**ref(path), "locator": {"json_pointer": pointer}}


class Fixture:
    """An explicit fake root authority in an isolated sandbox, never main state."""

    def __init__(self):
        scratch = HERE / ".synthetic-work"
        scratch.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="control-", dir=scratch)
        self.root = Path(self.temp.name).resolve()
        assert self.root.is_relative_to(scratch.resolve())
        self.docs = {}
        self.override = set()
        self.spec = self.root / "frozen"
        (self.spec / "contracts").mkdir(parents=True)
        for filename in v.FROZEN_HASHES:
            shutil.copyfile(REAL_SPEC / "contracts" / filename, self.spec / "contracts" / filename)
        accepted = json.loads((self.spec / "contracts/acceptance.json").read_text(encoding="utf-8"))
        tasks = json.loads((self.spec / "contracts/tasks.json").read_text(encoding="utf-8"))
        self.case_specs = {row["id"]: row for row in accepted["cases"] if row["id"] in v.CASE_IDS}
        self.bindings = [row for row in tasks["verification_command_selection"]["formal_case_bindings"] if row["task_id"] == "W04"]
        self.gates = [row for row in tasks["verification_command_selection"]["parent_check_bindings"] if row["task_id"] == "W04"]
        self.write_bytes("source/product.go", b"// SYNTHETIC inert source\n")
        self.write_bytes("source/driver.py", b"# SYNTHETIC inert driver\n")
        self.write_bytes("execution/command_dispatcher/dispatch.py", b"# SYNTHETIC inert dispatcher\n")
        self.write_bytes("inputs/scenario.json", b'{"scope":"SYNTHETIC_ONLY"}\n')
        self.write_bytes("tools/python.exe", b"SYNTHETIC inert tool bytes; never executed")
        self.write_bytes("tools/go.exe", b"SYNTHETIC inert Go tool bytes; never executed")
        tool_path = str(self.root / "tools/python.exe")
        tool_hash = v.sha256(self.root / "tools/python.exe")
        self.docs["execution/toolchains/locked.json"] = {
            "tools": {"python": {"path": tool_path, "sha256": tool_hash, "version_output": "synthetic-tool-1"},
                      "go": {"path": str(self.root / "tools/go.exe"), "sha256": v.sha256(self.root / "tools/go.exe"),
                             "version_output": "synthetic-go-1"}}
        }
        self.docs[E + "tool_identity.json"] = {
            "schema": "researchos.w04.tool-identity.v1", "locked_ref": ref("execution/toolchains/locked.json"),
            "tools": [{"name": "python", "version": "synthetic-tool-1", "path": tool_path, "sha256": tool_hash},
                      {"name": "go", "version": "synthetic-go-1", "path": str(self.root / "tools/go.exe"),
                       "sha256": v.sha256(self.root / "tools/go.exe")}]
        }
        self.docs[E + "vector.json"] = {
            "schema": "researchos.w04.version-vector.v1", "package_version": "2.4.0",
            "spec_files": [ref("frozen/contracts/" + name) for name in v.FROZEN_HASHES],
            "source_files": [ref(x) for x in ("source/product.go", "source/driver.py", "execution/command_dispatcher/dispatch.py")],
            "input_files": [ref("inputs/scenario.json")], "lock_files": [ref("execution/toolchains/locked.json")],
            "tool_files": [ref(E + "tool_identity.json")],
            "environment": {"os": "Windows", "arch": "amd64", "timezone": "UTC"},
            "components": {k: {"status": "not_applicable", "reason": "Synthetic parser controls do not execute " + k}
                           for k in ("model", "adapter", "rubric", "policy")}
        }
        self.docs["execution/v2.4/commands.json"] = {"revision": 999, "commands": {
            key: {"state": "BOUND", "cwd": ".", "executable_tool": "python", "argv": ["-B", "source/driver.py", key],
                  "selectors": {"task_id": ["W04"], "case_id": list(v.CASE_IDS), "check_id": list(v.GATE_IDS)}}
            for key in ("test.context", "test.domain", "package.validate")}}
        for tool, arguments in (("go", ["test", "-count=1", "-json", "./synthetic"]),
                                ("python", ["-B", "-X", "utf8", "frozen/tools/validate_package.py"])):
            self.docs[E + "source-" + tool + ".json"] = {
                "schema": "researchos.w04.source-invocation.v1", "status": "PASS", "mode": "FIXTURE",
                "actual_argv": [str(self.root / ("tools/" + tool + ".exe"))] + arguments, "cwd": str(self.root),
                "environment_variable_names": [], "exit_code": 0, "executable_sha256": v.sha256(self.root / ("tools/" + tool + ".exe")),
                "started_at": AT, "ended_at": END, "stdout": ref(E + "source-" + tool + ".stdout"),
                "stderr": ref(E + "source-" + tool + ".stderr"), "version_vector_ref": ref(E + "vector.json")}
            self.write_bytes(E + "source-" + tool + ".stderr", b"")
        events = [{"Action": "start", "Package": "synthetic"},
                  {"Action": "run", "Package": "synthetic", "Test": "TestSyntheticInert"},
                  {"Action": "pass", "Package": "synthetic", "Test": "TestSyntheticInert"},
                  {"Action": "pass", "Package": "synthetic"}]
        self.write_bytes(E + "source-go.stdout", ("\n".join(json.dumps(x) for x in events) + "\n").encode())
        self.docs[E + "source-python.stdout"] = {"status": "PASS", "scope": "SPECIFICATION_PACKAGE_ONLY", "product_tests": "NOT_RUN",
                                                  "package_version": "2.4.0", "checks": ["synthetic_marker"], "errors": []}
        self.docs[E + "execution_index.json"] = {
            "schema": "researchos.w04.execution-index.v1", "task_id": "W04", "step_id": "W04-99", "run_id": RUN,
            "executor_id": EX, "cases": {}, "parent_gates": {}}
        self.index = self.docs[E + "execution_index.json"]
        for cid in v.CASE_IDS:
            case = self.case_specs[cid]
            self.index["cases"][cid] = {part: ref(E + cid + "/" + part + ".json")
                                       for part in ("run_receipt", "version_manifest", "command_receipt", "assertion_results")}
            self.docs[E + cid + "/run_receipt.json"] = {
                "schema": "researchos.w04.run-receipt.v1", "case_id": cid, "run_id": RUN, "environment_mode": "FIXTURE",
                "os": "Windows", "arch": "amd64", "timezone": "UTC", "started_at": AT, "ended_at": END,
                "executor_id": EX, "verifier_id": VE}
            self.docs[E + cid + "/version_manifest.json"] = {
                "schema": "researchos.w04.version-manifest.v1", "case_id": cid, "run_id": RUN,
                "code_revision": CODE, "dirty": False, "version_vector_ref": ref(E + "vector.json")}
            commands = [self.command(b, "case_id") for b in self.bindings if b["case_id"] == cid]
            self.docs[E + cid + "/command_receipt.json"] = {
                "schema": "researchos.w04.command-receipt.v1", "case_id": cid, "run_id": RUN, "commands": commands}
            raw_path = E + cid + "/observations.json"
            self.docs[raw_path] = {"scope": "SYNTHETIC_ONLY", "observation": {"inert_marker": cid}}
            self.docs[E + cid + "/assertion_results.json"] = {
                "schema": "researchos.w04.assertion-results.v1", "case_id": cid, "run_id": RUN,
                "assertions": [{"id": a["id"], "expected": a["expected"], "actual": {"synthetic": True}, "status": "PASS",
                                "command_keys": case["command_keys"], "raw_evidence_refs": [raw(raw_path)]}
                               for a in case["assertions"]],
                "scenario": {"expected": {"synthetic": True}, "actual": {"synthetic": True}, "raw_evidence_refs": [raw(raw_path)]}}
        for binding in self.gates:
            path = E + binding["check_id"] + "/command.json"
            self.docs[path] = self.command(binding, "check_id")
            self.index["parent_gates"][binding["check_id"]] = ref(path)
        self.docs[I + "current.json"] = {
            "schema": "researchos.w04.current-context.v1", "scope": "ROOT_CURRENT_APPLICABILITY", "task_id": "W04", "step_id": "W04-99",
            "execution_index": ref(E + "execution_index.json"), "version_vector": copy.deepcopy(self.docs[E + "vector.json"]),
            "execution_source_snapshot": {"code_revision": CODE, "dirty": False, "version_vector_sha256": "0" * 64},
            "source_coverage": {"roots": [{"path": "source", "patterns": ["*.go", "*.py"]}],
                                "exact_files": ["execution/command_dispatcher/dispatch.py"], "paths_sha256": "0" * 64},
            "registry_ref": ref("execution/v2.4/commands.json"), "registered_dispatches": []}
        self.context = self.docs[I + "current.json"]
        for number, binding in enumerate(self.bindings + self.gates, 1):
            self.dispatch(number, binding)
        self.docs[P + "independent_review.json"] = {
            "schema": "researchos.w04.independent-review.v1", "scope": "EXTERNAL_FIXTURE_VERIFICATION", "task_id": "W04", "step_id": "W04-99",
            "executor_id": EX, "verifier_id": VE, "issued_at": ISSUED, "acceptance_baseline_ref": ref("frozen/contracts/acceptance.json"),
            "evidence_index_ref": ref(E + "execution_index.json"), "current_context_ref": ref(I + "current.json"),
            "owned_case_verdicts": [{"case_id": cid, "final_owner_task": "W04", "mode": "FIXTURE",
                                     "assertion_ids": [a["id"] for a in self.case_specs[cid]["assertions"]], "status": "PASS",
                                     "evidence_pointer": "/cases/" + cid,
                                     "semantic_review": {"status": "CONFIRMED", "statement": "SYNTHETIC control, no product review occurred",
                                                         "raw_evidence_refs": [raw(E + cid + "/observations.json")]}}
                                    for cid in v.CASE_IDS],
            "parent_gate_verdicts": [{"check_id": gid, "mode": "FIXTURE", "status": "PASS", "command_ref": ref(E + gid + "/command.json")}
                                     for gid in v.GATE_IDS], "open_blockers": [], "construction_decision": "ACCEPTED"}
        self.docs[I + "message.json"] = {"sender": VE, "message_id": "synthetic-message", "review_sha256": "0" * 64,
                                          "content": "SYNTHETIC_CONTROL_NOT_REAL_ISSUANCE"}
        self.docs[I + "issuance.json"] = {
            "schema": "researchos.w04.root-observed-issuance.v1", "scope": "ROOT_OBSERVED_INDEPENDENT_ISSUANCE",
            "observer_id": "synthetic:root-observer", "observed_at": OBSERVED, "issuer_id": VE,
            "review_ref": ref(P + "independent_review.json"), "current_context_ref": ref(I + "current.json"),
            "channel": "independent_agent_message", "message_id": "synthetic-message", "message_ref": ref(I + "message.json")}
        plan = json.loads((self.spec / "contracts/execution.plan.json").read_text(encoding="utf-8"))
        planned = {s["id"]: s for s in plan["steps"]}
        dependencies = set()
        def collect(sid):
            for dependency in planned[sid]["dependencies"]:
                if dependency not in dependencies:
                    dependencies.add(dependency)
                    collect(dependency)
        collect("W04-99")
        for dependency in dependencies:
            self.docs[I + "dependencies/" + dependency + ".json"] = {"scope": "SYNTHETIC_DEPENDENCY_ONLY"}
        self.docs["execution/v2.4/step_state.json"] = {
            "schema_version": "1.0", "package_version": "2.4.0", "plan_sha256": v.FROZEN_HASHES["execution.plan.json"],
            "steps": [{"id": d, "status": "ACCEPTED", "executor_id": "synthetic:dependency-executor", "verifier_id": "synthetic:dependency-verifier",
                       "evidence": [{"path": (I + "dependencies/" + d + ".json").removeprefix("execution/v2.4/"), "sha256": "0" * 64}]}
                      for d in sorted(dependencies)] + [
                {"id": "W04-99", "status": "ACCEPTED", "executor_id": EX, "verifier_id": VE, "accepted_at": OBSERVED,
                 "evidence": [{"path": path.removeprefix("execution/v2.4/"), "sha256": "0" * 64}
                              for path in (P + "independent_review.json", I + "current.json", I + "issuance.json")]}]}
        self.sync()

    def command(self, binding, selector_key):
        ident, key = binding[selector_key], binding["key"]
        directory = E + ident + "/" + key + "/"
        self.docs[directory + "stdout.json"] = {"task_id": "W04", selector_key: ident, "mode": "FIXTURE", "status": "PASS",
                                               "assertion_ids": binding["expected_assertion_ids"], "assertions": len(binding["expected_assertion_ids"])}
        self.write_bytes(directory + "stderr.txt", b"")
        return {"schema": "researchos.w04.command.v1", "command_key": key, "task_id": "W04", "mode": "FIXTURE",
                "run_id": RUN, "executor_id": EX, "selector": {selector_key: ident}, "invocation_kind": "DIRECT_DRIVER",
                "registered_command_revision": None, "actual_argv": [str(self.root / "tools/python.exe"), "source/driver.py", key],
                "cwd": str(self.root), "environment_variable_names": ["ProgramFiles(x86)"], "started_at": AT, "ended_at": END,
                "exit_code": 0, "stdout": ref(directory + "stdout.json"), "stderr": ref(directory + "stderr.txt"),
                "source_invocation_refs": [ref(E + "source-go.json"), ref(E + "source-python.json")]}

    def dispatch(self, number, binding):
        selector_key = "case_id" if "case_id" in binding else "check_id"
        ident, key = binding[selector_key], binding["key"]
        invocation = f"00000000-0000-4000-8000-{number:012d}"
        directory = "execution/invocations/" + invocation + "/"
        self.docs[directory + "stdout.txt"] = {"status": "PASS", "task_id": "W04", selector_key: ident, "mode": "FIXTURE",
                                                "assertion_ids": binding["expected_assertion_ids"],
                                                "execution_index_ref": ref(E + "execution_index.json")}
        self.write_bytes(directory + "stderr.txt", b"")
        receipt_path = I + f"dispatch-{number}.json"
        self.docs[receipt_path] = {
            "invocation_id": invocation, "command_key": key, "started_at": AT, "ended_at": END,
            "status": "PASS", "exit_code": 0, "child_exit_code": 0, "assertion_ids": binding["expected_assertion_ids"],
            "selectors": {"task_id": "W04", "case_id": "", "check_id": "", selector_key: ident},
            "scope": "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE", "registry_spec": "v2.4", "registered_command_revision": "0" * 64,
            "toolchain_revision": "0" * 64, "dispatcher_sha256": "0" * 64,
            "input_versions": [ref("source/driver.py")], "code_revision": "2" * 40,
            "argv": [str(self.root / "tools/python.exe"), "-B", "source/driver.py", key], "cwd": str(self.root),
            "environment_names": ["ProgramFiles(x86)"], "stdout": ref(directory + "stdout.txt"), "stderr": ref(directory + "stderr.txt")}
        self.context["registered_dispatches"].append({"command_key": key, selector_key: ident, "mode": "FIXTURE", "receipt_ref": ref(receipt_path)})

    def write_bytes(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def sync(self):
        complete, active = set(), set()

        def visit(path):
            if path in complete or path not in self.docs:
                return
            assert path not in active, "synthetic generator cycle: " + path
            active.add(path)
            value = self.docs[path]

            def refresh(item):
                if type(item) is list:
                    for entry in item:
                        refresh(entry)
                elif type(item) is dict:
                    if {"path", "sha256"} <= set(item) <= {"path", "sha256", "locator"}:
                        target = item["path"]
                        if path == "execution/v2.4/step_state.json":
                            target = "execution/v2.4/" + target
                        visit(target)
                        if (path, "ref:" + target) not in self.override:
                            item["sha256"] = v.sha256(self.root / target)
                    else:
                        for child in item.values():
                            refresh(child)
            refresh(value)
            if path == I + "current.json":
                if (path, "vector_digest") not in self.override:
                    value["execution_source_snapshot"]["version_vector_sha256"] = v.object_sha256(value["version_vector"])
                if (path, "paths_digest") not in self.override:
                    value["source_coverage"]["paths_sha256"] = v.object_sha256(sorted(x["path"] for x in value["version_vector"]["source_files"]))
            if path.startswith(I + "dispatch-"):
                for field, target in (("registered_command_revision", "execution/v2.4/commands.json"),
                                      ("toolchain_revision", "execution/toolchains/locked.json"),
                                      ("dispatcher_sha256", "execution/command_dispatcher/dispatch.py")):
                    visit(target)
                    if (path, field) not in self.override:
                        value[field] = v.sha256(self.root / target)
            if path == I + "message.json" and (path, "review_sha256") not in self.override:
                visit(P + "independent_review.json")
                value["review_sha256"] = v.sha256(self.root / (P + "independent_review.json"))
            self.write_bytes(path, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())
            active.remove(path)
            complete.add(path)
        for path in self.docs:
            visit(path)

    def check(self, phase="registered"):
        return v.check(self.root, "execution/v2.4/step_state.json", "frozen", I + "current.json",
                       P + "independent_review.json", I + "issuance.json", phase)

    def close(self):
        assert self.root.is_relative_to((HERE / ".synthetic-work").resolve())
        self.temp.cleanup()


class IntegrityControls(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()

    def tearDown(self):
        self.f.close()

    def reject(self, code, phase="registered"):
        self.f.sync()
        with self.assertRaises(v.InvalidEvidence) as caught:
            self.f.check(phase)
        self.assertEqual(caught.exception.code, code, str(caught.exception))

    def test_complete_synthetic_registered_control(self):
        result = self.f.check()
        self.assertEqual((result["assertion_count"], result["executed_case_count"], result["parent_gate_count"], result["formal_accepted_count"]), (10, 3, 5, 3))
        self.assertFalse(result["product_business_acceptance_created"])

    def test_execution_never_promotes_formal_cases(self):
        result = self.f.check("execution")
        self.assertEqual(result["formal_accepted_count"], 0)
        self.assertEqual(result["eligible_owned_case_count"], 0)

    def test_reviewed_before_state_acceptance_avoids_cycle(self):
        self.f.docs["execution/v2.4/step_state.json"]["steps"][-1]["status"] = "IN_PROGRESS"
        self.f.sync()
        result = self.f.check("reviewed")
        self.assertEqual((result["eligible_owned_case_count"], result["formal_accepted_count"]), (3, 0))

    def test_truthful_dirty_snapshot_is_allowed(self):
        self.f.context["execution_source_snapshot"]["dirty"] = True
        for cid in v.CASE_IDS:
            self.f.docs[E + cid + "/version_manifest.json"]["dirty"] = True
        self.f.sync()
        self.assertEqual(self.f.check()["formal_accepted_count"], 3)

    def test_check_is_read_only(self):
        before = {p.relative_to(self.f.root).as_posix(): v.sha256(p) for p in self.f.root.rglob("*") if p.is_file()}
        self.f.check()
        after = {p.relative_to(self.f.root).as_posix(): v.sha256(p) for p in self.f.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_duplicate_json_key(self):
        self.f.write_bytes(I + "current.json", b'{"a":1,"a":2}')
        with self.assertRaisesRegex(v.InvalidEvidence, "JSON_DUPLICATE_KEY"):
            self.f.check()

    def test_nonfinite_and_overflow_json(self):
        for token in ("NaN", "Infinity", "-Infinity", "1e9999"):
            with self.subTest(token=token), self.assertRaisesRegex(v.InvalidEvidence, "JSON_NONFINITE"):
                v.strict_json('{"value":' + token + '}')

    def test_wrong_frozen_baseline(self):
        (self.f.spec / "contracts/tasks.json").write_bytes(b"{}")
        with self.assertRaisesRegex(v.InvalidEvidence, "FROZEN_BASELINE"):
            self.f.check()

    def test_missing_owned_case(self):
        del self.f.index["cases"]["C04"]
        self.reject("MISSING_FIELD")

    def test_missing_global_part(self):
        del self.f.index["cases"]["C03"]["command_receipt"]
        self.reject("MISSING_FIELD")

    def test_missing_gate(self):
        del self.f.index["parent_gates"]["W04-H01"]
        self.reject("MISSING_FIELD")

    def test_duplicate_assertion(self):
        rows = self.f.docs[E + "C03/assertion_results.json"]["assertions"]
        rows[2] = copy.deepcopy(rows[1])
        self.reject("DUPLICATE_ID")

    def test_split_case_ids_between_commands(self):
        output = self.f.docs[E + "C03/test.context/stdout.json"]
        output["assertion_ids"] = ["C03-01"]
        output["assertions"] = 1
        self.reject("ID_SET")

    def test_missing_second_command(self):
        self.f.docs[E + "C03/command_receipt.json"]["commands"].pop()
        self.reject("ID_SET")

    def test_boolean_exit(self):
        self.f.docs[E + "C03/command_receipt.json"]["commands"][0]["exit_code"] = False
        self.reject("COMMAND_EXIT")

    def test_nonzero_exit(self):
        self.f.docs[E + "C03/command_receipt.json"]["commands"][0]["exit_code"] = 1
        self.reject("COMMAND_EXIT")

    def test_raw_failed_while_receipt_claims_success(self):
        self.f.docs[E + "C03/test.context/stdout.json"]["status"] = "FAIL"
        self.reject("COMMAND_OUTPUT")

    def test_empty_actual_assertion(self):
        self.f.docs[E + "C03/assertion_results.json"]["assertions"][0]["actual"] = {}
        self.reject("ASSERTION_ACTUAL")

    def test_lowered_expected(self):
        self.f.docs[E + "C03/assertion_results.json"]["assertions"][0]["expected"] = "easier synthetic threshold"
        self.reject("ASSERTION_EXPECTED")

    def test_missing_raw_locator(self):
        del self.f.docs[E + "C03/assertion_results.json"]["assertions"][0]["raw_evidence_refs"][0]["locator"]
        self.reject("RAW_LOCATOR")

    def test_out_of_range_raw_locator(self):
        self.f.docs[E + "C03/assertion_results.json"]["assertions"][0]["raw_evidence_refs"][0]["locator"] = {"json_pointer": "/missing"}
        self.reject("RAW_LOCATOR_MISSING")

    def test_hash_tamper(self):
        self.f.write_bytes(E + "C03/observations.json", b'{"forged":true}')
        with self.assertRaisesRegex(v.InvalidEvidence, "HASH_MISMATCH"):
            self.f.check()

    def test_path_traversal(self):
        self.f.context["execution_index"] = {"path": "../outside.json", "sha256": "0" * 64}
        # Skip synthetic graph repair: the traversal must fail before a file read.
        self.f.write_bytes(I + "current.json", json.dumps(self.f.context).encode())
        with self.assertRaisesRegex(v.InvalidEvidence, "PATH_ESCAPE"):
            self.f.check()

    def test_added_applicable_source(self):
        self.f.write_bytes("source/added.go", b"// unpinned new source")
        self.reject("SOURCE_COVERAGE")

    def test_changed_current_source(self):
        self.f.write_bytes("source/product.go", b"// changed")
        with self.assertRaisesRegex(v.InvalidEvidence, "HASH_MISMATCH"):
            self.f.check()

    def test_stale_case_vector(self):
        self.f.context["version_vector"]["environment"]["timezone"] = "Asia/Shanghai"
        for cid in v.CASE_IDS:
            self.f.docs[E + cid + "/run_receipt.json"]["timezone"] = "Asia/Shanghai"
        self.reject("STALE_VECTOR")

    def test_unconfirmed_dirty_snapshot(self):
        self.f.docs[E + "C03/version_manifest.json"]["dirty"] = True
        self.reject("ROOT_SOURCE_SNAPSHOT")

    def test_na_component_without_reason(self):
        del self.f.context["version_vector"]["components"]["model"]["reason"]
        self.reject("MISSING_FIELD")

    def test_tool_binary_drift(self):
        self.f.write_bytes("tools/python.exe", b"changed inert tool")
        with self.assertRaisesRegex(v.InvalidEvidence, "TOOL_CHANGED"):
            self.f.check()

    def test_wrong_mode(self):
        self.f.docs[E + "C03/run_receipt.json"]["environment_mode"] = "DEVELOPMENT"
        self.reject("MODE")

    def test_parent_accepted_does_not_replace_missing_cases(self):
        self.f.docs[P + "independent_review.json"]["owned_case_verdicts"] = []
        self.reject("TYPE_ARRAY")

    def test_wrong_final_owner(self):
        self.f.docs[P + "independent_review.json"]["owned_case_verdicts"][1]["final_owner_task"] = "W03"
        self.reject("CASE_OWNER_MODE")

    def test_self_review(self):
        self.f.docs[P + "independent_review.json"]["verifier_id"] = EX
        self.reject("SELF_REVIEW")

    def test_missing_independent_semantic_review(self):
        self.f.docs[P + "independent_review.json"]["owned_case_verdicts"][0]["semantic_review"]["status"] = "NOT_RUN"
        self.reject("SEMANTIC_REVIEW")

    def test_issuance_identity_string_not_enough(self):
        self.f.docs[I + "message.json"]["sender"] = "synthetic:someone-else"
        self.reject("ISSUANCE_MESSAGE")

    def test_issuer_cannot_be_root_observer(self):
        self.f.docs[I + "issuance.json"]["observer_id"] = VE
        self.reject("ISSUANCE_OBSERVER")

    def test_missing_state_registration(self):
        self.f.docs["execution/v2.4/step_state.json"]["steps"][-1]["evidence"].pop()
        self.reject("UNREGISTERED_REFERENCE")

    def test_state_owner_not_accepted(self):
        self.f.docs["execution/v2.4/step_state.json"]["steps"][-1]["status"] = "IN_PROGRESS"
        self.reject("OWNER_NOT_REGISTERED")

    def test_missing_dependency(self):
        self.f.docs["execution/v2.4/step_state.json"]["steps"][0]["status"] = "IN_PROGRESS"
        self.reject("DEPENDENCY")

    def test_duplicate_registered_dispatch(self):
        self.f.context["registered_dispatches"][-1] = copy.deepcopy(self.f.context["registered_dispatches"][0])
        self.reject("DUPLICATE_ID")

    def test_registered_child_boolean_exit(self):
        self.f.docs[I + "dispatch-1.json"]["child_exit_code"] = False
        self.reject("COMMAND_EXIT")

    def test_registered_raw_mode_drift(self):
        self.f.docs["execution/invocations/00000000-0000-4000-8000-000000000001/stdout.txt"]["mode"] = "DEVELOPMENT"
        self.reject("COMMAND_OUTPUT")

    def test_registered_registry_hash_drift(self):
        self.f.docs[I + "dispatch-1.json"]["registered_command_revision"] = "0" * 64
        self.f.override.add((I + "dispatch-1.json", "registered_command_revision"))
        self.reject("COMMAND_REVISION")

    def test_registered_unbound_selector(self):
        self.f.docs["execution/v2.4/commands.json"]["commands"]["test.context"]["selectors"]["case_id"] = ["A01", "C04"]
        self.reject("COMMAND_UNBOUND")

    def test_registered_argv_drift(self):
        self.f.docs[I + "dispatch-1.json"]["argv"].append("--unrecorded")
        self.reject("DISPATCH_ARGV")

    def test_registered_proof_link_missing(self):
        del self.f.docs["execution/invocations/00000000-0000-4000-8000-000000000001/stdout.txt"]["execution_index_ref"]
        self.reject("DISPATCH_EXECUTION_LINK")

    def test_conflicting_registered_review(self):
        other = P + "independent_review_other.json"
        self.f.docs[other] = copy.deepcopy(self.f.docs[P + "independent_review.json"])
        self.f.docs["execution/v2.4/step_state.json"]["steps"][-1]["evidence"].append({"path": other.removeprefix("execution/v2.4/"), "sha256": "0" * 64})
        self.reject("CONFLICTING_REVIEW")

    def test_explicit_hash_bound_supersession(self):
        other = P + "independent_review_previous.json"
        previous = copy.deepcopy(self.f.docs[P + "independent_review.json"])
        previous["issued_at"] = END
        self.f.docs[other] = previous
        current = self.f.docs[P + "independent_review.json"]
        current["supersedes_review_refs"] = [ref(other)]
        current["supersession_reason"] = "SYNTHETIC explicit newer independent review"
        self.f.docs["execution/v2.4/step_state.json"]["steps"][-1]["evidence"].append({"path": other.removeprefix("execution/v2.4/"), "sha256": "0" * 64})
        self.f.sync()
        self.assertEqual(self.f.check()["formal_accepted_count"], 3)

    def test_unregistered_supersession_rejected(self):
        other = P + "independent_review_previous.json"
        self.f.docs[other] = copy.deepcopy(self.f.docs[P + "independent_review.json"])
        self.f.docs[P + "independent_review.json"]["supersedes_review_refs"] = [ref(other)]
        self.f.docs[P + "independent_review.json"]["supersession_reason"] = "SYNTHETIC"
        self.reject("UNREGISTERED_SUPERSESSION")

    def test_source_go_empty_tests(self):
        self.f.write_bytes(E + "source-go.stdout", b'{"Action":"start","Package":"synthetic"}\n{"Action":"pass","Package":"synthetic"}\n')
        self.reject("SOURCE_EMPTY_TESTS")

    def test_source_go_failed_event(self):
        self.f.write_bytes(E + "source-go.stdout", b'{"Action":"fail","Package":"synthetic","Test":"TestSyntheticInert"}\n')
        self.reject("SOURCE_GO_FAILURE")

    def test_source_exit_boolean(self):
        self.f.docs[E + "source-go.json"]["exit_code"] = False
        self.reject("SOURCE_EXIT")

    def test_package_validator_cannot_claim_product_pass(self):
        self.f.docs[E + "source-python.stdout"]["product_tests"] = "PASS"
        self.reject("SOURCE_PACKAGE_OUTPUT")

    def test_package_validator_skip_manifest_rejected(self):
        self.f.docs[E + "source-python.json"]["actual_argv"].append("--skip-manifest")
        self.reject("SOURCE_PACKAGE_INVOCATION")

    def test_source_proof_pair_required(self):
        self.f.docs[E + "C03/command_receipt.json"]["commands"][0]["source_invocation_refs"].pop()
        self.reject("ID_SET")

    def test_source_vector_digest_tamper(self):
        self.f.context["execution_source_snapshot"]["version_vector_sha256"] = "0" * 64
        self.f.override.add((I + "current.json", "vector_digest"))
        self.reject("ROOT_SOURCE_SNAPSHOT")

    def test_source_coverage_digest_tamper(self):
        self.f.context["source_coverage"]["paths_sha256"] = "0" * 64
        self.f.override.add((I + "current.json", "paths_digest"))
        self.reject("SOURCE_COVERAGE_DIGEST")


if __name__ == "__main__":
    unittest.main(verbosity=2)
