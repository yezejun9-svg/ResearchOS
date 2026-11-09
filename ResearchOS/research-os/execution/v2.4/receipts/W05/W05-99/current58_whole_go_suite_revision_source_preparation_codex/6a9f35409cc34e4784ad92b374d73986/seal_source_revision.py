"""Final source-only audit and one-shot exclusive evidence sealing."""
import ast
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

here = Path(__file__).resolve().parent
root = here.parents[6]
old_ns = root / "execution/v2.4/receipts/W05/W05-99/current58_whole_go_suite_source_preparation_codex/bbeb0e9d8d1b4c8fb367a5c45d80adea"
review_ns = root / "execution/v2.4/receipts/W05/W05-99/current58_whole_go_suite_independent_source_review_codex/59a0746af051498fb71c1160ec6cec7a"
finite_path = old_ns / "whole58-finite.contract.proposed.json"
old_runner = old_ns / "whole58_finite_runner.proposed.py"
review_path = review_ns / "review.json"
gate_path = here / "whole58_gate.v3.proposed.py"
runner_path = here / "whole58_finite_runner.v4.proposed.py"
contract_path = here / "whole58-execution.contract.proposed.json"
interface_path = here / "authority-interface.proposed.json"

def ref(path):
    raw = path.read_bytes()
    return {"path": str(path.resolve(strict=True)),
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def write(name, value):
    path = here / name
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with path.open("xb") as handle:
        handle.write(raw)
    return ref(path)

# Complete static checks occur before any report/manifest/handoff is written.
assert ref(finite_path)["sha256"] == "52828991f4f23d6957a3f7aa6343b50d8840efbe0ca42121871aa6bc8ce8c904"
assert ref(finite_path)["bytes"] == 275734
assert ref(old_runner)["sha256"] == "4078ff600bc92e569c0e6f99c7716f0a7ebeb820ccc54efd974daa26aae2fe6c"
assert ref(review_path)["sha256"] == "db95d413687ec1f28a84e2da3292cfad48d868a1ed4657fb9cc55376150e6e3b"
finite = json.loads(finite_path.read_bytes())
execution = json.loads(contract_path.read_bytes())
interface = json.loads(interface_path.read_bytes())
assert finite["source_commit"] == execution["frozen_finite_contract"]["source_commit"]
assert finite["all_platform_top_tests"] == 745 and len(finite["packages"]) == 58
assert finite["packages_without_top_tests"] == 31
assert finite["lane_counts"] == {"STATIC_NO_RESOURCE_SIGNAL_REVIEW": 520,
    "LOCAL_HTTP_FIXTURE_REVIEW": 112, "LOCAL_NATIVE_CHILD": 77,
    "CONDITIONAL_SKIP_REVIEW": 4, "LOCAL_NODE_MU_TLS": 30,
    "REAL_MODEL_B01_HOLD": 2}
all_ids = [item for package in finite["packages"] for item in package["all_platform_top_test_ids"]]
lane_ids = [item for package in finite["packages"] for lane in package["lanes"].values()
            for item in lane["test_ids"]]
assert len(all_ids) == len(set(all_ids)) == 745
assert len(lane_ids) == len(set(lane_ids)) == 745 and set(all_ids) == set(lane_ids)
assert len({package["directory"] for package in finite["packages"]}) == 58
local_lanes = set(execution["allowed_local_lanes"])
assert len(local_lanes) == 6 and "REAL_MODEL_B01_HOLD" not in local_lanes
calls = 58 + sum(1 for package in finite["packages"] for lane in local_lanes
                 if lane in package["lanes"] and
                 (package["lanes"][lane]["windows_candidate_names"] or lane == "BUILD_ONLY_NO_TOP_TEST"))
assert calls == 136
old_tree = ast.parse(old_runner.read_bytes(), filename=str(old_runner))
gate_tree = ast.parse(gate_path.read_bytes(), filename=str(gate_path))
runner_tree = ast.parse(runner_path.read_bytes(), filename=str(runner_path))
def funcs(tree):
    return {node.name: ast.dump(node, include_attributes=False)
            for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
old_funcs, new_funcs = funcs(old_tree), funcs(runner_tree)
preserved = [name for name in ("sha", "pin", "pinned_file", "source_closure")
             if old_funcs.get(name) == new_funcs.get(name)]
assert preserved == ["sha", "pin", "pinned_file", "source_closure"]
assert {"validate", "validate_go_tree", "curated_go_tree", "recheck_before_launch"} <= set(funcs(gate_tree))
assert {"guarded_wall", "run_one", "bounded_json", "evaluate_run", "main"} <= set(new_funcs)
assert interface["future_root_literals_assigned"] is False
assert execution["qualification"]["source_acceptance"] is False
assert not any((here / name).exists() for name in
               ("source-review.json", "actual-go-result.json", "actual-root-grant.json"))

inverse = {
    "schema": "researchos.current58-whole-go-source-inverse.v1",
    "baseline_runner_ref": ref(old_runner), "baseline_finite_contract_ref": ref(finite_path),
    "revision_runner_ref": ref(runner_path), "revision_gate_ref": ref(gate_path),
    "preserved_runner_function_AST_exact": preserved,
    "removed_legacy_runner_functions": sorted(set(old_funcs)-set(new_funcs)),
    "new_or_changed_runner_functions": sorted(name for name in new_funcs
        if name not in old_funcs or new_funcs[name] != old_funcs[name]),
    "product_files_modified": [], "canonical_files_modified": [],
    "inverse_operation": "Discard this exclusive source-preparation namespace; the old runner and frozen finite contract were not modified.",
    "no_source_acceptance_or_formal_case_result": True
}
report = {
    "schema": "researchos.current58-whole-go-source-revision-report.v1",
    "stage": "SOURCE_PREPARATION_ONLY", "decision": "READY_FOR_INDEPENDENT_SOURCE_REVIEW",
    "baseline_review_ref": ref(review_path), "baseline_runner_ref": ref(old_runner),
    "baseline_finite_contract_ref": ref(finite_path),
    "revision_runner_ref": ref(runner_path), "revision_gate_ref": ref(gate_path),
    "execution_contract_ref": ref(contract_path), "authority_interface_ref": ref(interface_path),
    "static_checks": {"runner_AST": "PASS", "gate_AST": "PASS",
        "frozen_contract_SHA_bytes": "PASS", "review_SHA": "PASS",
        "source_commit": finite["source_commit"], "package_directories": 58,
        "top_test_IDs_unique_and_partitioned_once": 745,
        "build_only_directories": 31, "local_lanes": 6,
        "local_plan_primary_go_calls_if_all_six_selected": calls,
        "real_model_test_IDs_held": 2,
        "capped_static_callgraphs_from_original_review": 383,
        "candidate_imported_or_executed": False, "Go_Node_model_Git_CAS_calls": 0},
    "R01": "Monotonic absolute phase deadline starts before preflight; per-call wall is bounded by remaining minus explicit reserves. Kill/wait, daemon drain join and receipt/report IO are bounded. First cause, secondary causes, raw hash availability and nullable child exit remain explicit. Aggregate file is always provisional; successful return requires final after-write deadline check and a completed terminal receipt. Root outer Job remains necessary for descendants and blocked system IO.",
    "R02": "W14_GO_TOOLCHAIN is a typed canonical directory, never a file member. The gate checks the exact curated checkTree membership and bytes, go.exe build hash and lock, plus a separately reviewed actual FrozenGoToolchainHash attestation. Node and Mu retain file pins; missing W14 on native lane fails before launch.",
    "R03": "The gate reads exact current Root checkpoint, registration, grant, owner lease, non-author review, source manifest, finite contract, runner, environment, runtime catalog, Go tree, actual outer Job and meter receipts before any Popen. Claimed controller facts still require Root's real producer and independent verification; a JSON claim alone is insufficient.",
    "future_actual_inputs_open": ["fresh Root UUID and registration", "active checkpoint/lease and separate grant",
        "independent source and cap-controller review", "actual Windows Job with descendant deadline",
        "live nested-process/local-HTTP/provider-zero meter", "frozen Go tree and actual native hash attestation",
        "current 639-source closure, fresh output/cache/temp roots and exact env",
        "actual 58-package list rosters and selected lane results", "source acceptance consumer"],
    "execution_route": "Root must adopt this gate and runner from their immutable candidate paths after a fresh scope; do not run -list as a source-only probe because it executes Go test init/TestMain.",
    "model_B01": "Two real-model tests and unproven provider effects remain held; model cost and external-effect-zero stay NULL.",
    "whole58_suite_qualified": False, "source_acceptance": False,
    "formal_case_accepted_delta": 0, "candidate_run_count": 0,
    "failure_origins_this_source_revision": [ref(here / "failure-origin-1.json"),
                                            ref(here / "failure-origin-2.json")],
    "root_fixed_fourth_cut_48_to_580_unchanged": True
}
inverse_ref = write("source-inverse.json", inverse)
report["source_inverse_ref"] = inverse_ref
report_ref = write("report.json", report)
primary = [runner_path, gate_path, contract_path, finite_path]
extra = [interface_path, here / "source-inverse.json", here / "report.json",
         here / "failure-origin-1.json", here / "failure-origin-2.json"]
members = [ref(path) for path in primary + extra]
assert len({row["path"].casefold() for row in members}) == len(members)
manifest = {"schema": "researchos.current58-whole-go-source-preparation-manifest.v1",
            "stage": "SOURCE_PREPARATION_ONLY", "members": members,
            "member_count": len(members), "source_review_open": True,
            "execution_authorized": False, "actual_result_count": 0}
manifest_ref = write("manifest.json", manifest)
handoff = {"schema": "researchos.current58-whole-go-source-revision-handoff.v1",
           "stage": "STOPPED_SOURCE_PREPARATION_ONLY", "decision": "REVIEW_REQUESTED",
           "report_ref": report_ref, "manifest_ref": manifest_ref,
           "source_inverse_ref": inverse_ref, "runner_ref": ref(runner_path),
           "gate_ref": ref(gate_path), "execution_contract_ref": ref(contract_path),
           "authority_interface_ref": ref(interface_path),
           "baseline_review_ref": ref(review_path),
           "new_failure_origin_refs": [ref(here / "failure-origin-1.json"),
                                       ref(here / "failure-origin-2.json")],
           "root_canonical_unchanged": True,
           "source_acceptance": False, "formal_case_accepted_delta": 0}
handoff_ref = write("handoff.json", handoff)
print(json.dumps({"report": report_ref, "manifest": manifest_ref,
                  "handoff": handoff_ref, "inverse": inverse_ref}, ensure_ascii=False))
