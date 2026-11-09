"""Synthetic, non-authoritative controls; never calls execute()."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile

HERE = Path(__file__).resolve().parent
SRC = HERE / "main_c19_consumer_caller.source.py"
spec = importlib.util.spec_from_file_location("c19_source_candidate", SRC)
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)
outcomes = []


def reject(name, action, code):
    try:
        action()
    except ValueError as exc:
        if str(exc) != code:
            raise AssertionError((name, "wrong_rejection", str(exc), code)) from exc
        outcomes.append({"name": name, "observed": code, "pass": True})
    else:
        raise AssertionError((name, "accepted_bad_input"))


assert candidate.frozen_plan()["sha256"] == "a6669dd94b16bc833526f569c3c86ab08180ff6a39087ca9921ea898817eea17"
assert len(candidate.selected_registry(candidate.frozen_plan())) == 2
outcomes.append({"name": "actual_auto_registry_v24_selected_read_only", "pass": True})
interface, _, qualified = candidate.qualified_modes()
assert len(qualified) == 2 and qualified[0][1] != qualified[1][1]
outcomes.append({"name": "two_distinct_actual_mode_refs_read_only", "pass": True})

for label, value in (("bool_exit", False), ("float_exit", 0.0), ("null_exit", None)):
    reject(label, lambda value=value: candidate.strict_pass({"actual_exit": value}, {}, candidate.ROUTES[0], {}),
           "OUTER_JOB_FAILED")

reject("unclosed_job", lambda: candidate.strict_pass(
    {"actual_exit": 0, "timed_out": False, "error": None, "job_cleanup": {}}, {}, candidate.ROUTES[0], {}),
    "OWNED_DESCENDANTS_NOT_CLOSED")

synthetic_result = {"actual_exit": 0, "timed_out": False, "error": None,
                    "owned_child_pid": 1234, "creation_time_100ns": 987654321,
                    "job_cleanup": {"unnamed_exclusive_job": True,
                                    "kill_on_job_close_configured": True,
                                    "assigned_before_resume": True, "primary_exit_confirmed": True,
                                    "job_idle_confirmed": True, "active_processes_last_observed": 0,
                                    "handles_closed": True, "errors": []}}
synthetic_expected = {"registry_sha256": "a"*64, "dispatcher_sha256": "b"*64,
                      "toolchain_sha256": "c"*64, "router_sha256": "d"*64}
synthetic_receipt = {"status": "PASS", "exit_code": 0, "child_exit_code": 0,
                     "command_key": candidate.ROUTES[0],
                     "selectors": {"task_id": "W09", "check_id": "", "case_id": "C19"},
                     "registry_spec": "v2.4", "assertion_ids": ["C19-01", "C19-02", "C19-03"],
                     "registered_command_revision": "a"*64, "dispatcher_sha256": "b"*64,
                     "toolchain_revision": "c"*64,
                     "input_versions": [{"path": "ops/ci/w09_formal_router.py", "sha256": "d"*64}]}
assert candidate.strict_pass(synthetic_result, synthetic_receipt, candidate.ROUTES[0], synthetic_expected) is None
outcomes.append({"name": "synthetic_receipt_shape_only", "pass": True})
wrong_receipt = copy.deepcopy(synthetic_receipt)
wrong_receipt["registered_command_revision"] = "e"*64
reject("registry_revision_drift", lambda: candidate.strict_pass(
    synthetic_result, wrong_receipt, candidate.ROUTES[0], synthetic_expected),
    "DISPATCH_INPUT_REVISION_CHANGED")
wrong_receipt = copy.deepcopy(synthetic_receipt)
wrong_receipt["child_exit_code"] = 1
reject("child_exit_independent_from_outer", lambda: candidate.strict_pass(
    synthetic_result, wrong_receipt, candidate.ROUTES[0], synthetic_expected),
    "DISPATCH_RECEIPT_NOT_PASS")

historical_names = ("checkpoint", "path_ownership", "step_state", "commands")
historical_refs = [{"path": str((candidate.ROOT / "execution/v2.4" / (name + ".json")).resolve()),
                    "sha256": "a"*64, "bytes": 1} for name in historical_names]
historical_doc = {"source_refs": historical_refs}
reject("missing_historical_archive", lambda: candidate.historical_archive_bindings(
    {"historical_cp369_archives": []}, {"before_canonical_refs": historical_refs},
    (historical_doc,)), "HISTORICAL_ARCHIVE_REFS")
conflict = copy.deepcopy(historical_doc)
conflict["source_refs"][0]["sha256"] = "b"*64
reject("conflicting_historical_canon_pin", lambda: candidate.historical_archive_bindings(
    {"historical_cp369_archives": []}, {"before_canonical_refs": historical_refs},
    (historical_doc, conflict)), "HISTORICAL_CANON_CONFLICT")

reject("nonroot_request", lambda: candidate.root_request({
    "schema": "researchos.w09-c19-two-dispatcher-root-request.v1",
    "issued_by": "codex:/root/w09_formal_profile_source_impl", "formal_acceptance": False}),
    "ROOT_REQUEST_AUTHORITY")

original_source_ref = candidate.source_ref
try:
    scope = {"issued_by": "codex:/root", "formal_dispatcher": True,
             "formal_acceptance": False, "parent_acceptance": False, "formal_case_accepted_delta": 0,
             "expected_checkpoint_revision": 370, "expected_path_ownership_revision": 174,
             "expected_previous_checkpoint_revision": 369, "routes": list(candidate.ROUTES),
             "source_actor": candidate.SOURCE_ACTOR, "source_reviewer": candidate.SOURCE_ACTOR}
    candidate.source_ref = lambda *_: (scope, {"path": "synthetic", "sha256": "0"*64, "bytes": 0})
    reject("self_approved_scope", lambda: candidate.root_request({
        "schema": "researchos.w09-c19-two-dispatcher-root-request.v1",
        "issued_by": "codex:/root", "formal_acceptance": False,
        "native_producer_rerun": False, "registry_writes": False,
        "canonical_writes": False, "go_provider_calls": False,
        "exact_routes": list(candidate.ROUTES), "scope_ref": {}}), "SELF_APPROVAL")
finally:
    candidate.source_ref = original_source_ref

original_checked = candidate.checked
try:
    wrong = copy.deepcopy(interface)
    wrong["modes"][0]["route"][0] = "test.security"
    candidate.checked = lambda ref: (wrong, ref) if ref.get("path") == str(candidate.INTERFACE.resolve()) else original_checked(ref)
    reject("wrong_route_mode", candidate.qualified_modes, "MODE_ROUTE_OR_ENV")
finally:
    candidate.checked = original_checked

original_strict_json = candidate.strict_json
frozen_ref = candidate.frozen_plan()
try:
    calls = [0]
    def bad_pointer(raw):
        data = original_strict_json(raw)
        calls[0] += 1
        if calls[0] == 1:
            data["pointer"] = "v2.0"
        return data
    candidate.strict_json = bad_pointer
    reject("auto_registry_pointer_downgrade", lambda: candidate.selected_registry(frozen_ref),
           "AUTO_REGISTRY_NOT_FROZEN_V24")
finally:
    candidate.strict_json = original_strict_json

with tempfile.TemporaryDirectory(prefix="SYNTHETIC_NONAUTHORITATIVE_", dir=HERE) as temporary:
    tmp = Path(temporary)
    original, archive = tmp / "original", tmp / "archive"
    original.mkdir()
    archive.mkdir()
    (original / "owned.raw").write_bytes(b"owned")
    (archive / "owned.raw").write_bytes(b"owned")
    mapping = {"raw_copy_mapping": [{"original_ref": candidate.pin(original / "owned.raw"),
                                     "archive_ref": candidate.pin(archive / "owned.raw")}]}
    (original / "extra.RaW").write_bytes(b"extra")
    reject("case_variant_extra_raw", lambda: candidate.packet_inventory(mapping), "NATIVE_TREE_MEMBER_DRIFT")
    (original / "extra.RaW").unlink()
    (archive / "owned.raw").write_bytes(b"changed")
    reject("changed_archive_bytes", lambda: candidate.packet_inventory(mapping), "REF_CHANGED")

result = {"schema": "researchos.w09-c19-two-consumer-source-controls.v1",
          "synthetic_non_authoritative": True, "actual_consumer_executed": False,
          "formal_acceptance": False, "formal_case_accepted_delta": 0,
          "controls": outcomes, "passed": len(outcomes), "failed": 0}
(HERE / "source-controls.result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"source_controls_passed": len(outcomes), "synthetic_non_authoritative": True}))
