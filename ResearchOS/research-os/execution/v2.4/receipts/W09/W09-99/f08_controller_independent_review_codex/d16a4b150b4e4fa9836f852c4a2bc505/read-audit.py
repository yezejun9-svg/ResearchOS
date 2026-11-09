from __future__ import annotations
import ast
import hashlib
import json
import re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("D:/作品集/ResearchOS/research-os")
BUNDLE = ROOT / "execution/v2.4/receipts/W09/W09-99/finite_controller_preparation_codex/2098f8232b5a4331b0cac70eccd32ce0"
OWN = ROOT / "execution/v2.4/receipts/W09/W09-99/f08_controller_independent_review_codex/d16a4b150b4e4fa9836f852c4a2bc505"
PRIOR = ROOT / "execution/v2.4/receipts/W05/W05-99/f08_next_ready_gates_readonly_codex/ad2dc8822ba647b79b84664f8ee93078/handoff.json"
WORKTREE = ROOT / ".local/worktrees/codex-w0999-causal-controls-r320-9a15d49131e8"
ACTOR = "codex:/root/f08_i17_binding_impl"
inputs = []

def pin(path):
    p = Path(path)
    raw = p.read_bytes()
    result = {"path": p.as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    inputs.append(result)
    return result

def load(path):
    p = Path(path)
    pin(p)
    return json.loads(p.read_bytes())

def check_ref(ref):
    observed = pin(ref["path"])
    match = all(observed[k] == ref[k] for k in ["sha256", "bytes"])
    return {"original_ref": ref, "observed_ref": observed, "matched": match}

def create(name, value):
    p = OWN / name
    if p.exists():
        raise ValueError("New review artifact already exists")
    p.write_bytes((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8"))
    return pin(p)

prior = load(PRIOR)
fixed = prior["candidate_original_refs"]
fixed_checks = [check_ref(v) for v in fixed.values()]
manifest = load(BUNDLE / "manifest.json")
member_checks = [check_ref(v) for v in manifest["members"]]
spec = load(BUNDLE / "spec.json")
finite = load(BUNDLE / "finite-roster.json")
review = load(Path(fixed["source_independent_review"]["path"]))
source_checks = []
for v in spec["exact4_pins"]:
    r = pin(WORKTREE / v["path"])
    source_checks.append({"logical_path": v["path"], "source_ref": r, "matched": r["sha256"] == v["sha256"] and r["bytes"] == v["bytes"]})
syntax = []
anchors = []
for name in ["controller.py", "controller_common.py", "case_worker.py", "launch.py", "seal_readonly.py", "windows_debug_job_tree.py", "inputs/2-windows_owned_process.py"]:
    p = BUNDLE / name
    raw = p.read_bytes()
    tree = ast.parse(raw)
    functions = [{"name": n.name, "start": n.lineno, "end": n.end_lineno} for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    imports = [ast.unparse(n) for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    syntax.append({"ref": pin(p), "syntax": "PARSED_ONLY_NOT_IMPORTED", "functions": functions, "imports": imports})
    lines = raw.decode("utf-8").splitlines()
    if name == "controller_common.py":
        for a,z in [(58,94),(96,100),(150,171)]:
            anchors.append({"file": p.as_posix(), "start": a, "end": z, "raw_lines": lines[a-1:z]})
    if name == "controller.py":
        for a,z in [(47,87),(161,184),(185,212),(214,234)]:
            anchors.append({"file": p.as_posix(), "start": a, "end": z, "raw_lines": lines[a-1:z]})
    if name == "seal_readonly.py":
        anchors.append({"file": p.as_posix(), "start": 19, "end": 40, "raw_lines": lines[18:40]})
    if name == "windows_debug_job_tree.py":
        for a,z in [(298,330),(332,423),(517,570)]:
            anchors.append({"file": p.as_posix(), "start": a, "end": z, "raw_lines": lines[a-1:z]})
rows = spec["roster"]
counts = {"total": len(rows), "new": sum(x["new"] for x in rows), "original": sum(not x["new"] for x in rows),
          "resource_free": sum(not x["requires_resource"] for x in rows), "OS_dependent": sum(bool(x["requires_resource"]) for x in rows),
          "expected_run": sum(len(x["expected_records"]["run_records"]) for x in rows),
          "expected_pass": sum(len(x["expected_records"]["pass_records"]) for x in rows),
          "expected_leaf": sum(len(x["expected_records"]["leaf_records"]) for x in rows),
          "new_domain_closed": sum(x["new"] and x["file"].startswith("internal/domain/") for x in rows),
          "four_table_driver_JSON": sum(bool(x["four_table_evidence_file"]) for x in rows)}
selector_checks = [{"id":x["id"], "selector":x["selector"],
    "anchored_selector_correct": x["test_run"] == "/".join("^" + re.escape(p) + "$" for p in x["selector"].split("/")),
    "selected_is_expected_run_pass_leaf": all(x["selector"] in x["expected_records"][k] for k in ["run_records", "pass_records", "leaf_records"]),
    "source_top_function_present": "func " + x["selector"].split("/")[0] + "(" in (WORKTREE/x["file"]).read_text(encoding="utf-8"),
    "execution_NOT_RUN":x["execution"] == "NOT_RUN"} for x in rows]
checks = {
 "all11_prior_original_pins_match": all(x["matched"] for x in fixed_checks),
 "whole_controller_manifest43_members_match": len(member_checks)==manifest["member_count"]==43 and all(x["matched"] for x in member_checks),
 "four_immutable_source_pins_match": len(source_checks)==4 and all(x["matched"] for x in source_checks),
 "controller_spec_and_finite_roster_exactly_equal": rows==finite["rows"],
 "count49_41_8_45_4_89_89_49_29_21": counts=={"total":49,"new":41,"original":8,"resource_free":45,"OS_dependent":4,"expected_run":89,"expected_pass":89,"expected_leaf":49,"new_domain_closed":29,"four_table_driver_JSON":21},
 "49_unique_selectors_and_ids":len(set(x["id"] for x in rows))==len(set(x["selector"] for x in rows))==49,
 "all_static_selector_checks": all(all(x[k] for k in ["anchored_selector_correct","selected_is_expected_run_pass_leaf","source_top_function_present","execution_NOT_RUN"]) for x in selector_checks),
 "prior_source_review_has_no_REQUEST_but_no_acceptance":review["requested_changes"]==[] and review["source_accepted"] is False and review["parent_accepted"] is False,
 "prior_source_review_preserves_old_byte_bodies":review["verified_static_facts"]["original_test_bodies_comments_ids_byte_exact"] is True,
 "spec_source_acceptance_false":spec["authorized"] is False and spec["acceptance"] is False,
 "no_review_input_from_mutable_Main_state":not any(str(p) in json.dumps(inputs,ensure_ascii=False) for p in ["execution/v2.4/checkpoint.json","execution/v2.4/path_ownership.json","execution/v2.4/step_state.json"])
}
assert all(checks.values()), json.dumps(checks)
create("source-read-before.json", {"schema":"researchos.w09.controller-review-input-snapshot.v1","actor":ACTOR,"refs":inputs[:]})
audit_ref = create("static-source-audit.json", {"schema":"researchos.w09.controller-independent-static-audit.v1","reviewer":ACTOR,
 "status":"STATIC_READ_AND_SYNTAX_ONLY_NOT_CONTROLLER_READY","time_utc":datetime.now(timezone.utc).isoformat(),
 "checks":checks,"original_ref_checks":fixed_checks,"whole_manifest_member_checks":member_checks,
 "source_candidate_checks":source_checks,"AST_source_descriptors":syntax,"roster_counts":counts,
 "frozen_selector_checks":selector_checks,"OS_rows":[{"id":r["id"],"requirements":r["requires_resource"]} for r in rows if r["requires_resource"]],
 "exact_source_anchors":anchors,"original_source_assertions_preservation":"Previously independent byte-body check reused at same source hashes; no normalization or new Go parse/exec.",
 "actual_execution":{"controller":0,"helper":0,"target":0,"Go":0,"SQL":0,"network":0,"SDK_MODEL":0,"CAS":0},
 "actual_native_target_exit":None,"static_checks_are_not_native_PASS":True,"new_failure_origins":[]})
# Only fixed sealed inputs and own source are rechecked. Mutable Main state is never read.
after = []
for r in inputs[:]:
    p = Path(r["path"])
    if p.is_relative_to(OWN):
        continue
    now = pin(p)
    after.append({"before_ref":r,"after_ref":now,"unchanged":r==now})
assert all(v["unchanged"] for v in after)
after_ref = create("source-read-after.json", {"schema":"researchos.w09.controller-review-input-stability.v1","reviewer":ACTOR,"checks":after,"unchanged":True,"Main_state_read":False})
print(json.dumps({"audit_ref":audit_ref,"after_ref":after_ref,"checks":checks,"roster_counts":counts},ensure_ascii=False))

