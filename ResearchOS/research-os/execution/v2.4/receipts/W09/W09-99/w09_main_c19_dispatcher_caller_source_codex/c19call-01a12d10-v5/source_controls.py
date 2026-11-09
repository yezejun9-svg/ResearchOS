"""Synthetic, non-authoritative controls; never calls execute()."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from datetime import datetime, timezone

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

fake_ref = {"path": "SYNTHETIC_NONAUTHORITATIVE", "sha256": "0"*64, "bytes": 0}
output_root = candidate.ROOT / "execution/v2.4/receipts/W09/W09-99/synthetic-future-caller-output"
scope = {key: None for key in candidate.SCOPE_FIELDS}
scope.update({"schema": "researchos.w09-c19-main-two-dispatcher-scope.v1",
              "issued_by": "codex:/root", "slice_id": candidate.SLICE,
              "formal_dispatcher": True, "formal_acceptance": False,
              "parent_acceptance": False, "formal_case_accepted_delta": 0,
              "expected_checkpoint_revision": 370, "expected_path_ownership_revision": 174,
              "expected_previous_checkpoint_revision": 369,
              "before_canonical_revisions": {"checkpoint": 369, "path_ownership": 173, "commands": 39},
              "routes": list(candidate.ROUTES), "source_actor": candidate.SOURCE_ACTOR,
              "source_reviewer": "codex:/root/independent_source_reviewer",
              "authorized_output_root": str(output_root),
              "before_canonical_refs": historical_refs,
              "source_hdf_ref": fake_ref, "source_mf_ref": fake_ref,
              "caller_ref": fake_ref, "root_contract_ref": fake_ref,
              "source_review_ref": fake_ref, "frozen_plan_ref": fake_ref,
              "native_qualified_hdf_ref": fake_ref,
              "native_handoff_ref": fake_ref,
              "native_historical_request_ref": fake_ref})
assert candidate.validate_scope(scope) is None
outcomes.append({"name": "synthetic_exact_future_scope_shape", "pass": True})
bad_scope = copy.deepcopy(scope)
bad_scope["source_reviewer"] = candidate.SOURCE_ACTOR
reject("self_approved_scope", lambda: candidate.validate_scope(bad_scope), "SELF_APPROVAL")
bad_scope = copy.deepcopy(scope)
bad_scope["current_canonical_vector_ref"] = fake_ref
reject("forbidden_future_vector_in_scope", lambda: candidate.validate_scope(bad_scope), "SCOPE_EXACT_FIELDS")
bad_scope = copy.deepcopy(scope)
bad_scope["future_request_sha256"] = "a"*64
reject("forbidden_future_request_in_scope", lambda: candidate.validate_scope(bad_scope), "SCOPE_EXACT_FIELDS")
bad_scope = copy.deepcopy(scope)
bad_scope["before_canonical_revisions"]["checkpoint"] = True
reject("bool_historical_revision", lambda: candidate.validate_scope(bad_scope), "SCOPE_REGISTERED_SLICE")

review = {"schema": "researchos.w09-main-c19-two-dispatchers-independent-source-decision.v1",
          "decision": "ACCEPTED_SOURCE_ONLY", "actor_id": scope["source_reviewer"],
          "actor_role": "INDEPENDENT_NON_AUTHOR", "source_author_id": candidate.SOURCE_ACTOR,
          "source_hdf_ref": fake_ref, "source_mf_ref": fake_ref,
          "caller_ref": fake_ref, "root_contract_ref": fake_ref,
          "SourceAcceptedonly": True, "noactualorformal": True,
          "actual_dispatcher_run": False, "formal_acceptance": False,
          "parent_acceptance": False, "formal_case_accepted_delta": 0,
          "execution_grant": False}
assert candidate.validate_source_review(review, scope, fake_ref, fake_ref, fake_ref, fake_ref) is None
outcomes.append({"name": "synthetic_exact_independent_review_shape", "pass": True})
bad_review = {"reviewer_id": scope["source_reviewer"], "decision": "ACCEPTED_SOURCE_ONLY",
              "formal_acceptance": False}
reject("unbound_three_field_review", lambda: candidate.validate_source_review(
    bad_review, scope, fake_ref, fake_ref, fake_ref, fake_ref), "SOURCE_REVIEW_NOT_BOUND")
bad_review = copy.deepcopy(review)
bad_review["caller_ref"] = {**fake_ref, "sha256": "1"*64}
reject("unrelated_caller_review", lambda: candidate.validate_source_review(
    bad_review, scope, fake_ref, fake_ref, fake_ref, fake_ref), "SOURCE_REVIEW_NOT_BOUND")
bad_review = copy.deepcopy(review)
bad_review["actor_role"] = "AUTHOR"
reject("author_role_review", lambda: candidate.validate_source_review(
    bad_review, scope, fake_ref, fake_ref, fake_ref, fake_ref), "SOURCE_REVIEW_NOT_BOUND")

lease_expiry = "2099-01-01T00:00:00Z"
lease_base = {"step_id": "W09-99", "slice_id": candidate.SLICE,
              "state": candidate.LEASE_STATE, "scope_ref": fake_ref,
              "source_handoff_ref": fake_ref, "source_review_ref": fake_ref,
              "output_root": str(output_root), "routes": list(candidate.ROUTES),
              "lease_status": "ACTIVE", "lease_expires_at": lease_expiry}
owner_doc = {**lease_base, "owner_id": "codex:/root", "selected_worker_id": "codex:/root"}
worker_doc = {**lease_base, "worker_id": "codex:/root", "selected_owner_ref": fake_ref}
subtask = {**lease_base, "owner": "codex:/root", "current_source_writer": None,
           "owner_document_ref": fake_ref, "worker_document_ref": fake_ref,
           "formal_case_accepted_delta": 0, "parent_acceptance": False}
worker_row = {**lease_base, "owner": "codex:/root", "selected_owner_ref": fake_ref,
              "worker_document_ref": fake_ref}
cp_fixture = {"workers": [worker_row]}
ow_fixture = {"active_integrator": {"id": "codex:/root"},
              "card_path_bindings": {"W09-99": {"owner": "codex:/root",
                "subtasks": {"c19_main_two_dispatchers": subtask}}}}
clock = datetime(2026, 10, 9, tzinfo=timezone.utc)
output = output_root / "run-synthetic"
def lease(cp=cp_fixture, ow=ow_fixture, owner=owner_doc, worker=worker_doc):
    return candidate.validate_canon_lease(cp, ow, scope, fake_ref, fake_ref,
                                          fake_ref, fake_ref, fake_ref,
                                          owner, worker, output, clock)
assert lease() is None
outcomes.append({"name": "synthetic_registered_unique_active_canon_lease", "pass": True})
reject("missing_canonical_worker", lambda: lease(cp={"workers": []}), "CANON_WORKER_NOT_UNIQUE")
reject("duplicate_canonical_worker", lambda: lease(cp={"workers": [worker_row, copy.deepcopy(worker_row)]}),
       "CANON_WORKER_NOT_UNIQUE")
expired = copy.deepcopy(owner_doc)
expired["lease_expires_at"] = "2000-01-01T00:00:00Z"
reject("expired_standalone_owner", lambda: lease(owner=expired), "LEASE_EXPIRED")
conflict_worker = {**lease_base, "step_id": "W09-99", "slice_id": "OTHER_ACTIVE_SLICE"}
reject("conflicting_active_worker_output_root", lambda: lease(cp={"workers": [worker_row, conflict_worker]}),
       "CANON_WORKER_CONFLICT")
reject("missing_canonical_owner_subtask", lambda: lease(ow={
    "active_integrator": {"id": "codex:/root"},
    "card_path_bindings": {"W09-99": {"owner": "codex:/root", "subtasks": {}}}}),
    "CANON_SUBTASK_NOT_REGISTERED")

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

static_paths = [candidate.ROOT / "execution/v2.4/commands.json",
                candidate.DISPATCHER, candidate.ROOT / "execution/toolchains/locked.json",
                candidate.ROOT / "execution/v2.4/current_spec.json", candidate.ROUTER,
                candidate.ROOT / "ops/ci/w09_evidence_closure.py", candidate.PYTHON,
                Path(r"D:\作品集\ResearchOS\ResearchOS_Implementation_Package_v2.4\contracts\execution.plan.json")]
static_table = {ref["path"].casefold(): ref for ref in map(candidate.pin, static_paths)}
assert candidate.validate_sealed_static_table(static_table, candidate.frozen_plan()) is None
outcomes.append({"name": "actual_current_static_matches_synthetic_pin_table", "pass": True})
for label, path in (("cm39", static_paths[0]), ("dispatcher", static_paths[1]),
                    ("toolchain", static_paths[2]), ("pointer", static_paths[3])):
    changed = copy.deepcopy(static_table)
    changed[str(path.resolve()).casefold()]["sha256"] = "f"*64
    reject("sealed_" + label + "_byte_drift", lambda changed=changed:
           candidate.validate_sealed_static_table(changed, candidate.frozen_plan()),
           "SEALED_STATIC_INPUT_DRIFT")

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
