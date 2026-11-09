"""Pure IO SOURCE_ONLY seal; candidate is parsed but never imported or run."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
OLD = ROOT / "execution/v2.4/receipts/W05/W05-99/wholeGo_root_cap_producer_source_revision_codex/034e52a7a96f4fb6a5f2e90b9e6a6b32/wholego_cap_metadata.v2.proposed.py"
REVIEW = ROOT / "execution/v2.4/receipts/W05/W05-99/wholeGo_root_cap_producer_independent_source_review_codex/7dc91c6f9eb1467da6d0bb68d05123d4/review.json"
NEW = HERE / "wholego_cap_metadata.v3.proposed.py"
OLD_SHA = "f55db499cb42401a260614b05902a5ab7f5639c7270fecac87a6e95dc9a74b54"
REVIEW_SHA = "72da2646d0c10e28afc94a5610aaf53f5b17cbc92e6a0b60e0dba7d02503f1b9"

def pin(path):
    raw = path.read_bytes()
    return {"path": str(path).replace("\\", "/"), "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw)}

def put(name, value):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with (HERE / name).open("xb") as handle:
        handle.write(raw)

assert pin(OLD)["sha256"] == OLD_SHA and pin(REVIEW)["sha256"] == REVIEW_SHA
old_text, new_text = OLD.read_text(encoding="utf-8"), NEW.read_text(encoding="utf-8")
tree = ast.parse(new_text, filename=str(NEW))
compile(tree, str(NEW), "exec", dont_inherit=True)
assert "def verified_raw(" in new_text and "def verified_json(" in new_text
assert "read_pin(" not in new_text and "observed_windows_process" in new_text
assert "CANONICAL_CHECKPOINT_REQUIRED" in new_text and "ROOT_STAGE_OUTPUT_NOT_FRESH" in new_text
assert "POSTRUN_FINAL_RESOURCE_ORIGINS_FOREIGN" in new_text

def write_patch(name, before, after, fromfile, tofile):
    raw = "".join(difflib.unified_diff(before.splitlines(keepends=True),
                                       after.splitlines(keepends=True),
                                       fromfile=fromfile, tofile=tofile)).encode("utf-8")
    with (HERE / name).open("xb") as handle:
        handle.write(raw)

write_patch("forward.v2-to-v3.patch", old_text, new_text,
            "a/wholego_cap_metadata.v2.proposed.py", "b/wholego_cap_metadata.v3.proposed.py")
write_patch("inverse.v3-to-v2.patch", new_text, old_text,
            "a/wholego_cap_metadata.v3.proposed.py", "b/wholego_cap_metadata.v2.proposed.py")

keys = set()
for node in ast.walk(tree):
    if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and
            node.value.id == "source" and isinstance(node.slice, ast.Constant) and
            isinstance(node.slice.value, str)):
        keys.add(node.slice.value)
keys |= {"schema", "source_commit", "actor_id", "run_uuid", "owner", "worktree",
         "project_id", "output_root", "root_allocation_ref", "root_allocation_review_ref",
         "controller_actual_receipt_ref", "controller_actual_review_ref"}
template = {key: None for key in sorted(keys)}
template.update({"schema": "researchos.whole-go-root-cap-input.v1",
                 "source_commit": "e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7",
                 "actor_id": "codex:/root", "worktree": str(ROOT).replace("\\", "/")})
put("root-input.v3.template.json", template)
precheck = json.loads((HERE / "precheck.v3.final.json").read_bytes())
assert precheck["python_ast_compile"] and not precheck["go_or_product_executed"]
review = json.loads(REVIEW.read_bytes())
assert review["decision"] == "REQUEST_CHANGES" and len(review["requested_changes"]) == 5
report = {
    "schema": "researchos.whole-go-root-cap-v3-source-report.v1",
    "decision": "SOURCE_PREPARATION_ONLY",
    "basis": {"previous_source": pin(OLD), "independent_request": pin(REVIEW)},
    "fixes": {
        "CAP2-R01": "verified_raw reads Go/Python bytes only; verified_json parses only JSON",
        "CAP2-R02": "single verified_raw read supplies bytes/hash and verified_json parser",
        "CAP2-R03": "canonical checkpoint and selected contract/source pins; Root allocation/current lease; live Windows PID creation and membership; pinned heartbeat/controller actual receipt plus non-author review; 13 DECLARED and six typed runtime observations",
        "CAP2-R04": "close binds original report/terminal to allocated run output, authority bundle, preflight/final resources, actual exit and monotonic deadline/cleanup; incomplete remains incomplete",
        "CAP2-R05": "before output, canonical reparse/alias check and Root allocation/review exact stage namespace"
    },
    "abi": {"argv": "PinnedPython -I -S -X utf8 candidate.py attest|scope|arm|close INPUT OUTDIR INPUT_SHA256",
            "positive_future_chain": "Root allocation -> actual Go tree native hash -> attestation -> non-author review -> scope -> Root registration/lease/checkpoint/grant/controller -> arm -> once runner -> close",
            "future_actual_values": None,
            "root_controller_adoption": "OPEN",
            "candidate_cannot_issue_grant": True},
    "precheck_ref": pin(HERE / "precheck.v3.final.json"),
    "source_acceptance": False, "actual_grant": False,
    "go_or_product_executions": 0, "model_requests": 0,
    "formal_case_accepted_delta": 0, "new_tool_failure_count": 0,
    "status": "STOPPED_AFTER_SEAL"
}
put("report.json", report)
members = [pin(path) for path in sorted(HERE.iterdir()) if path.is_file()
           and path.name not in {"manifest.json", "handoff.json"}]
put("manifest.json", {"schema": "researchos.whole-go-root-cap-v3-source-members.v1",
                      "namespace": str(HERE).replace("\\", "/"),
                      "count": len(members), "members": members,
                      "source_only": True, "actual_grant": False})
handoff = {"schema": "researchos.whole-go-root-cap-v3-source-handoff.v1",
           "decision": "SOURCE_PREPARATION_ONLY", "manifest_ref": pin(HERE / "manifest.json"),
           "report_ref": pin(HERE / "report.json"), "source_ref": pin(NEW),
           "forward_ref": pin(HERE / "forward.v2-to-v3.patch"),
           "inverse_ref": pin(HERE / "inverse.v3-to-v2.patch"),
           "root_input_template_ref": pin(HERE / "root-input.v3.template.json"),
           "precheck_ref": pin(HERE / "precheck.v3.final.json"),
           "actual_source_acceptance": False, "whole_suite_qualified": False,
           "formal_case_accepted_delta": 0, "status": "STOPPED_AFTER_SEAL"}
put("handoff.json", handoff)
print(json.dumps({"report": pin(HERE / "report.json"), "manifest": pin(HERE / "manifest.json"),
                  "handoff": pin(HERE / "handoff.json"), "members": len(members)}, ensure_ascii=False))
