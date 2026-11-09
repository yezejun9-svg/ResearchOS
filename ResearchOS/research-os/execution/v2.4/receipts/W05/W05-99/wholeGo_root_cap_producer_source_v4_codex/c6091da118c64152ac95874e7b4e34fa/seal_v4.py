"""Seal the narrow CAP3-R01 SOURCE_ONLY revision; never import the candidate."""
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
OLD_NS = ROOT / "execution/v2.4/receipts/W05/W05-99/wholeGo_root_cap_producer_source_v3_codex/baa0423d87784ee0bbf526de45a20a8c"
REVIEW = ROOT / "execution/v2.4/receipts/W05/W05-99/wholeGo_root_cap_producer_v3_independent_source_review_codex/e0f3d1b2e33542769c412519ad579ad1/review.json"
OLD = OLD_NS / "wholego_cap_metadata.v3.proposed.py"
NEW = HERE / "wholego_cap_metadata.v4.proposed.py"
TEMPLATE_OLD = OLD_NS / "root-input.v3.template.json"
TEMPLATE_NEW = HERE / "root-input.v4.template.json"

def pin(path):
    raw = path.read_bytes()
    return {"path": str(path).replace("\\", "/"),
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def put(name, value):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with (HERE / name).open("xb") as out:
        out.write(raw)

assert pin(OLD)["sha256"] == "fa5380cffcf56d3e5b78cd963cd6d97ff81cc30c09528a6730952d58863913b7"
assert pin(REVIEW)["sha256"] == "cf335b405c7e850ca75356a88893a700075555b7ca58b9b81d0ae60d4db5b275"
review = json.loads(REVIEW.read_bytes())
assert review["decision"] == "REQUEST_CHANGES"
assert [row["id"] for row in review["requested_changes"]] == ["CAP3-R01"]
assert TEMPLATE_OLD.read_bytes() == TEMPLATE_NEW.read_bytes()
before, after = OLD.read_text(encoding="utf-8"), NEW.read_text(encoding="utf-8")
old_tree, new_tree = ast.parse(before), ast.parse(after)
compile(new_tree, str(NEW), "exec", dont_inherit=True)
assert len(old_tree.body) == len(new_tree.body)
for prior, current in zip(old_tree.body, new_tree.body):
    if isinstance(prior, ast.FunctionDef) and prior.name == "observed_windows_process":
        assert isinstance(current, ast.FunctionDef) and current.name == prior.name
    else:
        assert ast.dump(prior, include_attributes=False) == ast.dump(current, include_attributes=False)
precheck = json.loads((HERE / "precheck.v4.json").read_bytes())
io = json.loads((HERE / "precheck.tool-io.json").read_bytes())
assert precheck["candidate_imported"] is False and precheck["actual_os_probe_count"] == 0
assert precheck["all_cases_close_handle"] is True and io["actual_python_exit"] == 0
assert io["result"]["exit_code"] == 0 and io["result"].get("session_id") is None
forward = "".join(difflib.unified_diff(before.splitlines(keepends=True),
    after.splitlines(keepends=True), fromfile="a/wholego_cap_metadata.v3.proposed.py",
    tofile="b/wholego_cap_metadata.v4.proposed.py"))
inverse = "".join(difflib.unified_diff(after.splitlines(keepends=True),
    before.splitlines(keepends=True), fromfile="a/wholego_cap_metadata.v4.proposed.py",
    tofile="b/wholego_cap_metadata.v3.proposed.py"))
with (HERE / "forward.v3-to-v4.patch").open("xb") as out:
    out.write(forward.encode("utf-8"))
with (HERE / "inverse.v4-to-v3.patch").open("xb") as out:
    out.write(inverse.encode("utf-8"))
report = {
    "schema": "researchos.whole-go-cap-v4-source-report.v1",
    "decision": "SOURCE_PREPARATION_ONLY",
    "review_basis_ref": pin(REVIEW), "old_source_ref": pin(OLD), "source_ref": pin(NEW),
    "template_identical_to_v3": True, "template_ref": pin(TEMPLATE_NEW),
    "forward_ref": pin(HERE / "forward.v3-to-v4.patch"),
    "inverse_ref": pin(HERE / "inverse.v4-to-v3.patch"),
    "precheck_ref": pin(HERE / "precheck.v4.json"),
    "precheck_tool_io_ref": pin(HERE / "precheck.tool-io.json"),
    "CAP3_R01": {
        "status": "CLOSED_STATIC_ONLY",
        "query": "GetProcessTimes success + expected Job membership + GetExitCodeProcess success + STILL_ACTIVE=259 + zero exit FILETIME before returning creation",
        "positive_fake_kernel": "live/suspended process with creation identity accepted",
        "negative_fake_kernel": ["retained exited handle rejected", "259 with nonzero exit FILETIME rejected",
                                 "exit-code query failure rejected", "process-times query failure rejected"],
        "cleanup": "CloseHandle in original finally remains intact",
        "observation_semantics": "point-in-time only; future Root controller and final close prove lifecycle"
    },
    "all_other_functions_ast_unchanged": True,
    "actual_os_probe": None, "actual_root_grant": None, "actual_go_suite": None,
    "new_tool_failure_count": 0, "source_acceptance": False,
    "whole_suite_qualified": False, "formal_case_accepted_delta": 0,
    "status": "STOPPED_AFTER_SEAL"
}
put("report.json", report)
members = [pin(p) for p in sorted(HERE.iterdir()) if p.is_file()
           and p.name not in {"manifest.json", "handoff.json"}]
put("manifest.json", {"schema": "researchos.whole-go-cap-v4-source-manifest.v1",
                      "namespace": str(HERE).replace("\\", "/"),
                      "members": members, "members_count": len(members),
                      "source_only": True, "actual_os_probe_count": 0})
put("handoff.json", {
    "schema": "researchos.whole-go-cap-v4-source-handoff.v1",
    "decision": "SOURCE_PREPARATION_ONLY",
    "report_ref": pin(HERE / "report.json"),
    "manifest_ref": pin(HERE / "manifest.json"),
    "source_ref": pin(NEW),
    "template_ref": pin(TEMPLATE_NEW),
    "forward_ref": pin(HERE / "forward.v3-to-v4.patch"),
    "inverse_ref": pin(HERE / "inverse.v4-to-v3.patch"),
    "precheck_ref": pin(HERE / "precheck.v4.json"),
    "actual_root_authority": None, "source_acceptance": False,
    "formal_case_accepted_delta": 0, "status": "STOPPED_AFTER_SEAL"
})
print(json.dumps({"report": pin(HERE / "report.json"),
                  "manifest": pin(HERE / "manifest.json"),
                  "handoff": pin(HERE / "handoff.json")}, ensure_ascii=False))
