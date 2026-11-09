"""Seal SDK v4 SOURCE_ONLY proposal with whole-file byte inverse."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path("D:/作品集/ResearchOS/research-os")
HERE = Path(__file__).resolve().parent
assert HERE.is_relative_to(ROOT) and HERE.resolve(strict=True).is_relative_to(ROOT.resolve(strict=True))
OLD = ROOT / "execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v3_source_codex/06f264848e274b198f3e03a1c072e44e"
REVIEW = ROOT / "execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v3_independent_source_review_codex/51d6d171418744a5b653c3a03b49d3ae/review.json"
FILE_PAIRS = [
    ("mu_sdk_trial.v3.proposed.py", "mu_sdk_trial.v4.proposed.py"),
    ("internal_host_vault.v3.proposed.go", "internal_host_vault.v4.proposed.go"),
    ("internal_host_host.v3.proposed.go", "internal_host_host.v4.proposed.go"),
    ("apps_control_main.v3.proposed.go", "apps_control_main.v4.proposed.go"),
    ("runtime_qualification.unlimited.v4.proposed.go",
     "runtime_qualification.unlimited.v5.proposed.go"),
    ("input.v3.template.json", "input.v4.template.json"),
]

def pin(path):
    raw = path.read_bytes()
    return {"path": str(path).replace("\\", "/"),
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def put(name, value):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with (HERE / name).open("xb") as out:
        out.write(raw)

def patch(name, before, after, old_name, new_name):
    raw = "".join(difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile="a/" + old_name, tofile="b/" + new_name)).encode("utf-8")
    with (HERE / name).open("xb") as out:
        out.write(raw)

assert pin(REVIEW)["sha256"] == "70bc3bf70b2b9913ce4ec1838ce0c12957b5c697d459874c5ff5098a3a9e2d68"
review = json.loads(REVIEW.read_bytes())
assert review["decision"] == "REQUEST_CHANGES"
assert [x["id"] for x in review["requested_changes"]] == ["R01-v3", "R03-v3"]
review_refs = {Path(ref["path"]).name: ref for ref in review["source_refs"]}
changes = []
for old_name, new_name in FILE_PAIRS:
    old_path, new_path = OLD / old_name, HERE / new_name
    before, after = old_path.read_text(encoding="utf-8"), new_path.read_text(encoding="utf-8")
    if old_name != "input.v3.template.json":
        ref = review_refs[old_name]
        assert pin(old_path)["sha256"] == ref["sha256"] and pin(old_path)["bytes"] == ref["bytes"]
    if new_name.endswith(".py"):
        ast.parse(after, filename=str(new_path))
        compile(after, str(new_path), "exec", dont_inherit=True)
    if new_name.endswith(".json"):
        old_template, new_template = json.loads(before), json.loads(after)
        assert set(new_template) - set(old_template) == {
            "initial_discovery_state", "initial_config_state"}
        assert all(new_template[key] == old_template[key] for key in old_template)
        assert new_template["initial_discovery_state"] is None
        assert new_template["initial_config_state"] is None
    if new_name.endswith(".go"):
        assert before == after
    trace = list(difflib.ndiff(before.splitlines(keepends=True),
                              after.splitlines(keepends=True)))
    assert "".join(difflib.restore(trace, 1)) == before
    assert "".join(difflib.restore(trace, 2)) == after
    forward, inverse = new_name + ".patch", new_name + ".inverse.patch"
    patch(forward, before, after, old_name, new_name)
    patch(inverse, after, before, new_name, old_name)
    changes.append({"before": pin(old_path), "after": pin(new_path),
                    "forward": pin(HERE / forward), "inverse": pin(HERE / inverse),
                    "byte_identical": before == after})
precheck = json.loads((HERE / "precheck.v4.final.json").read_bytes())
io = json.loads((HERE / "precheck.tool-io.json").read_bytes())
assert precheck["source_ast_compile"] and precheck["actual_child_processes"] == 0
assert io["actual_python_exit"] == io["result"]["exit_code"] == 0
origin = HERE / "tool-failure-origin-001.json"
assert json.loads(origin.read_bytes())["counter_increment"] == 1
put("source-inverse.json", {
    "schema": "researchos.mu-sdk-trial-v4-source-inverse.v1",
    "changes": changes, "all_whole_bytes_invertible": True,
    "go_sources_byte_identical": True,
    "candidate_imported_or_executed": False})
report = {
    "schema": "researchos.mu-sdk-trial-v4-source-report.v1",
    "decision": "SOURCE_PREPARATION_ONLY",
    "review_basis_ref": pin(REVIEW),
    "source_ref": pin(HERE / "mu_sdk_trial.v4.proposed.py"),
    "template_ref": pin(HERE / "input.v4.template.json"),
    "inverse_ref": pin(HERE / "source-inverse.json"),
    "precheck_ref": pin(HERE / "precheck.v4.final.json"),
    "precheck_tool_io_ref": pin(HERE / "precheck.tool-io.json"),
    "failure_origins": [pin(origin)], "new_tool_failure_count": 1,
    "R01_v3": {
        "status": "CLOSED_STATIC_ONLY",
        "root_basis_new_fields": ["initial_discovery_state", "initial_config_state"],
        "before_once_and_every_child": "Canonical isolated path and exact actual bytes/absence; executable rehashed immediately before Popen.",
        "finite_config_transition": "init absent→project/workspace-bound zero state; config set-model changes only revision/model using same checked JSONL raw; goal/run preserve state.",
        "original_payload": "The parsed stdout uses the raw bytes that are pinned, and before/after config bytes are copied into exclusive output leaves with exact refs.",
        "next_child": "Always recheck postimage bytes, discovery bytes, argv/cwd/env and executable.",
        "real_root_basis_and_execution": None
    },
    "R03_v3": {
        "status": "CLOSED_STATIC_ONLY",
        "first_cause": "Known nonzero poll/wait fixed inside output context before close; late close/hash failures become secondary.",
        "native_exit_unknown_preserved": True,
        "deadline_before_popen_preserved": True
    },
    "R02_R04_go_sources_unchanged": True,
    "actual_root_registration_or_grant": None,
    "actual_job_lifecycle_and_live_qualification": None,
    "go_cli_sdk_model_executions": 0,
    "main_or_canonical_modified": False,
    "source_acceptance": False, "formal_case_accepted_delta": 0,
    "status": "STOPPED_AFTER_SEAL"}
put("report.json", report)
members = [pin(path) for path in sorted(HERE.iterdir()) if path.is_file()
           and path.name not in {"manifest.json", "handoff.json"}]
put("manifest.json", {"schema": "researchos.mu-sdk-trial-v4-source-manifest.v1",
                      "namespace": str(HERE).replace("\\", "/"),
                      "members": members, "members_count": len(members),
                      "source_only": True, "actual_provider_calls": 0})
put("handoff.json", {
    "schema": "researchos.mu-sdk-trial-v4-source-handoff.v1",
    "decision": "SOURCE_PREPARATION_ONLY",
    "runner_ref": pin(HERE / "mu_sdk_trial.v4.proposed.py"),
    "go_refs": [pin(HERE / new) for old, new in FILE_PAIRS if new.endswith(".go")],
    "template_ref": pin(HERE / "input.v4.template.json"),
    "inverse_ref": pin(HERE / "source-inverse.json"),
    "precheck_ref": pin(HERE / "precheck.v4.final.json"),
    "report_ref": pin(HERE / "report.json"),
    "manifest_ref": pin(HERE / "manifest.json"),
    "failure_origins": [pin(origin)],
    "actual_authority": None, "actual_provider_calls": 0,
    "source_acceptance": False, "formal_case_accepted_delta": 0,
    "status": "STOPPED_AFTER_SEAL"})
print(json.dumps({"report": pin(HERE / "report.json"),
                  "manifest": pin(HERE / "manifest.json"),
                  "handoff": pin(HERE / "handoff.json"),
                  "origin": pin(origin)}, ensure_ascii=False))
