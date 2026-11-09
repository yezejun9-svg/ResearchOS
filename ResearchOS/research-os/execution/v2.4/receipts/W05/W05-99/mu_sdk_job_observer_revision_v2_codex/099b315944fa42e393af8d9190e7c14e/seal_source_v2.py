"""Seal only the new source proposal; do not execute observer/controller."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
P05 = HERE.parent.parent
V1 = P05 / "mu_sdk_job_observer_source_codex/8cf71287160941f3b841945dc02be134"
REVIEW = P05 / "mu_sdk_controller_observer_independent_source_review_codex/da1388ae95d14653a26a1f167574d251"
ROOT_V2 = P05 / "mu_sdk_controller_revision_v2_codex/6a02e12c83da4d4c80fc3f322fe8d397"


def pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def put(name, value):
    path = HERE / name
    with path.open("xb") as handle:
        handle.write((json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode())
    return pin(path)


def main():
    old_path = V1 / "mu_sdk_job_observer.proposed.py"
    source = HERE / "mu_sdk_job_observer.v2.proposed.py"
    old_raw, raw = old_path.read_bytes(), source.read_bytes()
    assert hashlib.sha256(old_raw).hexdigest() == "b062be8b68d1b31b658ba79a20c890ce895009fc135c80ae8d33ed5b78d01fd0"
    assert pin(V1 / "manifest.json")["sha256"] == "b55317c49d092422b07854c8ee43d10fd9fd9c4b7bde40d600e03e3fa23e3de6"
    assert pin(V1 / "handoff.json")["sha256"] == "c360d417200a3ddba076a022494b1d1e028f025d74174a75fa486bab1b94c9d7"
    manifest = json.loads((V1 / "manifest.json").read_bytes())
    assert len(manifest["members"]) == 14
    for member in manifest["members"]:
        assert pin(Path(member["path"])) == member
    assert {path.name for path in V1.iterdir()} == {Path(row["path"]).name for row in manifest["members"]} | {"manifest.json", "handoff.json"}
    review_ref = pin(REVIEW / "independent-source-review.json")
    assert review_ref["sha256"] == "254f7ea04fb7bffdf4725d5ddb8063350ada69376e4ae8759263aeac32f75c08"
    assert json.loads((REVIEW / "independent-source-review.json").read_bytes())["decision"] == "REQUEST_CHANGES"
    old_tree, tree = ast.parse(old_raw), ast.parse(raw)
    funcs = lambda t: {node.name: ast.dump(node, include_attributes=False) for node in t.body if isinstance(node, ast.FunctionDef)}
    old_funcs, new_funcs = funcs(old_tree), funcs(tree)
    changed = sorted(name for name in old_funcs if old_funcs[name] != new_funcs.get(name))
    added = sorted(set(new_funcs) - set(old_funcs))
    assert changed == sorted(("phase_projection", "validate_source_review", "validate_context", "observe_callback_frame", "observe_assigned_before_resume"))
    assert added == sorted(("validate_public_environment", "validate_launch_inputs", "validate_callback_launch"))
    assert not (set(old_funcs) - set(new_funcs))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            ast.literal_eval(node.value)
        else:
            assert isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef)) or (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))
    compile(raw, str(source), "exec", dont_inherit=True)
    controls = json.loads((HERE / "pure-controls.v2.report.json").read_bytes())
    assert controls["source_ref"] == pin(source) and controls["count"] == 46 and controls["failed"] == 0
    expected_cases = {"FRAME_POSITIVE_EXACT_REVIEWED_LAUNCH", "FRAME_FOREIGN_ARGV_NOW_REJECTED",
                      "FRAME_FOREIGN_CWD_NOW_REJECTED", "FRAME_EXTRA_ENV_EVEN_WHEN_CONTEXT_MATCHES_NOW_REJECTED",
                      "reject-worker-bytes", "reject-Python-bytes", "REVIEW_OLD_FOUR_SOURCE_READY_REJECTED"}
    assert expected_cases <= {row["name"] for row in controls["checks"] if row["passed"]}
    patch = "".join(difflib.unified_diff(old_raw.decode().splitlines(True), raw.decode().splitlines(True),
                                       fromfile="v1/mu_sdk_job_observer.proposed.py", tofile="v2/mu_sdk_job_observer.v2.proposed.py"))
    with (HERE / "v1-to-v2.diff").open("xb") as handle:
        handle.write(patch.encode())
    frozen = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)}
    template_ref = put("independent-source-review.v2.template.json", {
        "schema": "researchos.mu-sdk-controller-observer-independent-source-review.v2", "decision": None, "actor_id": None,
        "observer_source_ref": pin(source), "runner_source_ref": frozen["RUNNER_REF"],
        "controller_source_ref": None, "hooks_source_ref": None,
        "phase_worker_source_ref": None, "python_binary_ref": None,
        "callback_contract": "REAL_ASSIGNED_SUSPENDED_FRAME_BEFORE_FIRST_RESUME", "formal_acceptance": False,
        "execution_grant_issued": False, "note": "Unissued input template. Missing future controller/worker/Python refs require actual independent review."})
    report_ref = put("source-preparation.v2.json", {
        "schema": "researchos.mu-sdk-observer-source-revision.v2", "decision": "SOURCE_PREPARATION_ONLY_WITH_OPEN",
        "actor_id": "codex:/root/w05_merge_review", "source_ref": pin(source),
        "previous_source_ref": pin(old_path), "previous_manifest_ref": pin(V1 / "manifest.json"),
        "previous_handoff_ref": pin(V1 / "handoff.json"), "previous_inventory_verified": 16,
        "request_changes_ref": review_ref, "addressed_scope": ["CTRL-R06 observer launch tuple", "CTRL-R04 observer extra-env"],
        "changed_functions": changed, "new_functions": added,
        "unchanged_functions": sorted(name for name in old_funcs if old_funcs[name] == new_funcs.get(name)),
        "controls_ref": pin(HERE / "pure-controls.v2.report.json"), "controls": 46, "failed": 0,
        "diff_ref": pin(HERE / "v1-to-v2.diff"), "unissued_review_template_ref": template_ref,
        "root_partial_v2_provenance_only": pin(ROOT_V2 / "handoff.json"),
        "root_partial_v2_is_execution_authority": False,
        "open": ["CTRL-R02 canonical transaction ownership", "CTRL-R05 independent absolute Job watchdog",
                 "future controller must supply reviewed worker/Python pins and close execution-load immutability",
                 "independent complete source review", "actual Windows callback", "trusted qualification Host", "phase seed"],
        "main_writes": 0, "canonical_writes": 0, "target_native_calls": 0, "WinAPI_calls": 0,
        "actual_observer_calls": 0, "provider_requests": 0, "formal_acceptance_delta": 0,
        "source_runtime_qualification": False, "execution_grant_issued": False,
        "evidence_scope": "Pure source/AST/frame/byte-buffer controls only; no live process observation"})
    members = [pin(path) for path in sorted(HERE.iterdir()) if path.is_file() and path.name not in ("manifest.json", "handoff.json")]
    manifest_ref = put("manifest.json", {"schema": "researchos.source-preparation-manifest.v1", "members": members,
                     "excluded": ["manifest.json", "handoff.json"], "inventory_scope": "All direct files except manifest and subsequent handoff"})
    handoff_ref = put("handoff.json", {"schema": "researchos.mu-sdk-observer-source-handoff.v2",
                    "decision": "SOURCE_PREPARATION_ONLY_WITH_OPEN", "source_ref": pin(source),
                    "report_ref": report_ref, "manifest_ref": manifest_ref, "review_template_ref": template_ref,
                    "target_native_calls": 0, "provider_requests": 0, "formal_acceptance_delta": 0,
                    "source_author": "codex:/root/w05_merge_review", "stop_source_writes": True})
    print(json.dumps({"source": pin(source), "report": report_ref, "manifest": manifest_ref, "handoff": handoff_ref,
                      "members": len(members), "controls": 46}, ensure_ascii=False))


if __name__ == "__main__":
    main()
