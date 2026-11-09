"""Seal this SOURCE_ONLY proposal; never import or execute a product candidate."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
OLD = ROOT / "execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_executable_source_codex/1b8bc13521764e508f540dc2399ac33d"
REVIEW = ROOT / "execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_independent_source_review_codex/33477ff3f8a94e57b4d9fdaabf3aa19e/review.json"
EXPECTED_REVIEW = "e21645fd05b1d4266ce4a30a326c4796e93b8065b5bce446965aa4bb864deb8d"
EXPECTED_OLD_RUNNER = "690621499a4a64e80a8cde472ef9653856af2fabc3bb55d8bed7ea379872989d"

def pin(path):
    raw = path.read_bytes()
    return {"path": str(path).replace("\\", "/"), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def write(name, value):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with (HERE / name).open("xb") as stream:
        stream.write(raw)

def patch(old, new, from_name, to_name):
    return "".join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                        fromfile=from_name, tofile=to_name))

assert pin(REVIEW)["sha256"] == EXPECTED_REVIEW
old_runner = OLD / "mu_sdk_trial.proposed.py"
new_runner = HERE / "mu_sdk_trial.v2.proposed.py"
assert pin(old_runner)["sha256"] == EXPECTED_OLD_RUNNER
old_text, new_text = old_runner.read_text(encoding="utf-8"), new_runner.read_text(encoding="utf-8")
ast.parse(new_text, filename=str(new_runner))
assert "def command_once(" in new_text and "def complete_sse(" in new_text
with (HERE / "mu_sdk_trial.v2.proposed.py.patch").open("xb") as stream:
    stream.write(patch(old_text, new_text, "a/mu_sdk_trial.proposed.py", "b/mu_sdk_trial.v2.proposed.py").encode("utf-8"))
with (HERE / "mu_sdk_trial.v2.proposed.py.inverse.patch").open("xb") as stream:
    stream.write(patch(new_text, old_text, "a/mu_sdk_trial.v2.proposed.py", "b/mu_sdk_trial.proposed.py").encode("utf-8"))

template = json.loads((HERE / "input.v2.template.json").read_bytes())
assert template["source_commit"] == "e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7"
assert template["maximum_provider_requests"] == 3 and template["requested_output_tokens_total"] == 8192
assert template["total_wall_seconds"] == 300 and template["root_grant"] is None
precheck = json.loads((HERE / "precheck-results.seal.json").read_bytes())
assert precheck["candidate_imported"] is False and precheck["product_or_child_started"] is False
origins = [HERE / ("tool-failure-origin-%03d.json" % i) for i in (1, 2, 3)]
for origin in origins:
    content = json.loads(origin.read_bytes())
    assert content["counts_as_one_tool_failure"] is True
    assert content["full_tool_result"]["exit_code"] == 1

review_pin = pin(REVIEW)
source_inputs = {
    "review_request_changes": review_pin,
    "previous_runner": pin(old_runner),
    "previous_qualification": pin(OLD / "runtime_qualification.unlimited.v2.proposed.go"),
    "previous_control": pin(OLD / "apps_control_main.go.proposed.go"),
    "previous_host": pin(OLD / "internal_host_host.go.proposed.go"),
    "previous_vault": pin(OLD / "internal_host_vault.go.proposed.go")
}
changes = [
    "R01 exact Root registration/review/grant/lease/checkpoint/source/profile/route/current Job/once guards before product IO; actual producer remains OPEN",
    "R02 current qualification marker/plan/binding/sealed profile plus project-scoped effects and exact MODEL UNKNOWN ledger/SSE facts",
    "R03 one monotonic Root deadline with pre-Popen reserve, original raw, nullable exit and first-cause receipt for child and parse failures",
    "R04 trial vault/data isolation on Control and Host construction before lease/Open/mkdir; original nontrial branch preserved",
    "UNLIMITED_AMOUNT null/UNKNOWN path unchanged; CAPPED positive upper-bound/reserve path unchanged"
]
report = {
    "schema": "researchos.mu-sdk-real-trial-revision-source-report.v1",
    "decision": "SOURCE_PREPARATION_ONLY",
    "source_inputs": source_inputs,
    "changes": changes,
    "future_root_requirements": ["Root-produced current registration and grant", "non-author scope review",
                                 "single-use CAS/lease", "Windows Job controller and independent lifecycle review",
                                 "exact pinned tool/route/profile and separate actual runtime qualification"],
    "future_later_values": "NULL until Root producer and independent source review",
    "precheck": pin(HERE / "precheck-results.seal.json"),
    "static_verification": "Python AST parse; pure AST/IO negative tests; Go source text/inverse only; Go compile NOT_RUN",
    "failure_origins": [pin(path) for path in origins],
    "failure_count_increment": 3,
    "tool_input_completeness": "First two exact cmd strings lost after context compaction; original full exec wrapper preserved, input_exact NULL. Third input exact.",
    "actual_sdk_calls": 0, "actual_provider_calls": 0, "candidate_executions": 0,
    "source_acceptance_increment": 0, "formal_acceptance_increment": 0,
    "fixed_codex_live_cases": "HOLD_UNCHANGED",
    "status": "STOPPED_AFTER_SEAL"
}
write("report.json", report)
members = sorted(path for path in HERE.iterdir() if path.is_file() and path.name not in {"manifest.json", "handoff.json"})
manifest = {"schema": "researchos.mu-sdk-real-trial-revision-source-manifest.v1",
            "root": str(HERE).replace("\\", "/"), "members": [pin(path) for path in members],
            "members_count": len(members), "candidate_executions": 0}
write("manifest.json", manifest)
handoff = {"schema": "researchos.mu-sdk-real-trial-revision-source-handoff.v1",
           "decision": "SOURCE_PREPARATION_ONLY", "manifest_ref": pin(HERE / "manifest.json"),
           "report_ref": pin(HERE / "report.json"), "candidate_runner": pin(new_runner),
           "candidate_go": [pin(HERE / name) for name in (
               "runtime_qualification.unlimited.v3.proposed.go", "internal_host_vault.v2.proposed.go",
               "internal_host_host.v2.proposed.go", "apps_control_main.v2.proposed.go")],
           "input_template": pin(HERE / "input.v2.template.json"),
           "python_forward": pin(HERE / "mu_sdk_trial.v2.proposed.py.patch"),
           "python_inverse": pin(HERE / "mu_sdk_trial.v2.proposed.py.inverse.patch"),
           "go_forward_inverse": [pin(HERE / name) for name in (
               "runtime_qualification.unlimited.v3.proposed.go.patch",
               "runtime_qualification.unlimited.v3.proposed.go.inverse.patch",
               "internal_host_vault.v2.proposed.go.patch", "internal_host_vault.v2.proposed.go.inverse.patch",
               "internal_host_host.v2.proposed.go.patch", "internal_host_host.v2.proposed.go.inverse.patch",
               "apps_control_main.v2.proposed.go.patch", "apps_control_main.v2.proposed.go.inverse.patch")],
           "precheck_ref": pin(HERE / "precheck-results.seal.json"),
           "failure_origins": [pin(path) for path in origins],
           "root_execution_authorized": False, "source_acceptance": False,
           "formal_acceptance_increment": 0, "status": "STOPPED_AFTER_SEAL"}
write("handoff.json", handoff)
print(json.dumps({"report": pin(HERE / "report.json"), "manifest": pin(HERE / "manifest.json"),
                  "handoff": pin(HERE / "handoff.json"), "members": len(members)}, ensure_ascii=False))
