"""Independent source review. IO and AST only; never imports or executes any candidate."""
import sys
sys.dont_write_bytecode = True
import ast
import difflib
import hashlib
import json
import os
from pathlib import Path

ROOT = Path("D:/作品集/ResearchOS/research-os")
OUT = Path(__file__).resolve().parent
PREP = ROOT / "execution/v2.4/receipts/W13/W13-03/current58_cli2_root_caller_preparation_codex/b8e3c81d266b43a89ca6810f044acb04"
seen = {}
def demand(ok, message):
    if not ok:
        raise RuntimeError(message)
def read(path):
    path = Path(path)
    demand(path.is_absolute() and path.is_file(), "Missing exact input: " + str(path))
    demand(path.resolve() == path.absolute(), "Input path alias: " + str(path))
    for parent in [path] + list(path.parents):
        if os.path.lexists(parent):
            attrs = parent.lstat()
            demand(not parent.is_symlink() and not (getattr(attrs, "st_file_attributes", 0) & 0x400), "Reparse input: " + str(parent))
    raw = path.read_bytes()
    key = str(path)
    demand(key not in seen or seen[key] == raw, "Changed input: " + key)
    seen[key] = raw
    return raw
def ref(path):
    path = Path(path)
    raw = read(path)
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
def verify(expected):
    actual = ref(expected["path"])
    demand(actual == expected, "Hash/size mismatch: " + expected["path"])
    return seen[expected["path"]]
def doc(path):
    return json.loads(read(path).decode("utf-8"))
def save(name, value):
    with (OUT / name).open("xb") as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8"))

demand(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode, "Pinned isolated Python flags")
demand(ref("C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe")["sha256"] == "cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b", "Pinned Python SHA")
demand(Path(sys.executable).resolve() == Path("C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe").resolve(), "Actual interpreter path")

verify({"path": str(PREP / "manifest.json"), "sha256": "1d8a20753f0cb7d843bb149da125371cbca651f77484e6baa9e992521810c6cb", "bytes": 3867})
manifest = doc(PREP / "manifest.json")
demand(manifest["count"] == len(manifest["entries"]) == 12 and manifest["self_excluded"] is True, "Preparation 12+self manifest")
demand(len({x["path"] for x in manifest["entries"]}) == 12, "Duplicate preparation members")
demand({str(p) for p in PREP.iterdir() if p.is_file()} == {x["path"] for x in manifest["entries"]} | {str(PREP / "manifest.json")}, "Preparation inventory closure")
for item in manifest["entries"]:
    demand(Path(item["path"]).parent == PREP, "Foreign preparation member")
    verify(item)
verify({"path": str(PREP / "handoff.json"), "sha256": "695feb9e5ce2157bd95a7be94b94bbcbbf9d4bbd9882ca9afc511d4783976978", "bytes": 3205})
handoff = doc(PREP / "handoff.json")
contract = doc(PREP / "contract.json")
reported = doc(PREP / "static-audit.json")
inverse = doc(PREP / "edits.inverse.json")
frozen = doc(PREP / "inputs.before.json")
demand(len(frozen) == 8 and frozen == doc(PREP / "inputs.after.json") == doc(PREP / "inputs.sealed.after.json"), "Eight frozen vectors")
for item in frozen:
    verify(item)
baseline_ref = inverse["baseline_ref"]
baseline = verify(baseline_ref)
demand(baseline_ref["sha256"] == "bc191ffe9a2752cd8e339371cd8f96c1c992742d63aeda92f2cc29a42e5ef6ad" and baseline_ref["bytes"] == 4540, "Old r331 caller baseline")
old_manifest = doc(Path(baseline_ref["path"]).parent / "root-launch.closed.manifest.json")
demand(next(x for x in old_manifest["members"] if Path(x["path"]).name == "root-launch-once.v2.py") == baseline_ref, "Old caller closed manifest anchor")
candidate_ref = inverse["candidate_ref"]
candidate = verify(candidate_ref)
demand(candidate_ref == handoff["caller_ref"] and candidate_ref["sha256"] == "766a838c12a641b2c3bf249e648d71706ac45edb027a1b1bfc66261af06b84bb" and len(candidate) == 5799, "Exact candidate caller")
demand(len(inverse["edits"]) == 5, "Five finite inverse edits")
restored = candidate.decode("utf-8")
forward = baseline.decode("utf-8")
for edit in inverse["edits"]:
    demand(forward.count(edit["old"]) == 1, "Nonunique forward edit")
    forward = forward.replace(edit["old"], edit["new"], 1)
demand(forward.encode("utf-8") == candidate, "Full forward bytes")
for edit in reversed(inverse["edits"]):
    demand(restored.count(edit["new"]) == 1, "Nonunique inverse edit")
    restored = restored.replace(edit["new"], edit["old"], 1)
demand(restored.encode("utf-8") == baseline, "Full inverse bytes")
original_ast = ast.parse(baseline)
proposed_ast = ast.parse(candidate)
defs = lambda tree: {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, ast.FunctionDef)}
demand(set(defs(original_ast)) == {"need", "pin", "save"} and defs(original_ast) == defs(proposed_ast), "Three original helper ASTs")
demand(baseline[baseline.index(b"result = None"):] == candidate[candidate.index(b"result = None"):], "Original result/try/finally/exit tail")
rendered_diff = "".join(difflib.unified_diff(baseline.decode().splitlines(True), candidate.decode().splitlines(True), fromfile=baseline_ref["path"], tofile=candidate_ref["path"])).encode()
demand(read(PREP / "source.diff") == rendered_diff, "Exact recorded diff")
calls = [n for n in ast.walk(proposed_ast) if isinstance(n, ast.Call)]
launches = [n for n in calls if isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == "subprocess" and n.func.attr == "run"]
demand(len(launches) == 1 and {k.arg: ast.literal_eval(k.value) for k in launches[0].keywords if k.arg in ["timeout", "check"]} == {"timeout":3900, "check":False}, "Original sole caller launch")
demand(sum(isinstance(n.func, ast.Name) and n.func.id == "save" and n.args and isinstance(n.args[0], ast.Constant) and n.args[0].value == "root-launch.intent.json" for n in calls) == 1, "Single caller intent")
opens = [n for n in calls if isinstance(n.func, ast.Attribute) and n.func.attr == "open"]
demand(len(opens) == 3 and all(n.args and ast.literal_eval(n.args[0]) == "xb" for n in opens), "All three exclusive open sites")
demand(not any(isinstance(n.func, ast.Attribute) and n.func.attr == "mkdir" for n in calls), "Caller performs no output allocation")
text = candidate.decode("utf-8")
demand("124f16da796d16dd4a066d3b5ed8a00db8e744f7ca690d614cf46b14b8ac0f81" not in text, "No old grant SHA")
scope = doc(contract["scope_ref"]["path"])
verify(contract["scope_ref"])
demand(contract["scope_ref"]["sha256"] == "459f00078d742e754631294d17210329280c2e1fec0cf7925b94fb4333c3bc84" and contract["scope_ref"]["bytes"] == 8853, "Fixed r334-v2 scope")
demand(scope["source_commit"] == contract["source_commit"] == "e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7", "Source identity")
demand(scope["registration_namespace"] == "execution/v2.4/receipts/W05/W05-99/integration_codex/cli58-fresh-held2-r334-v2-0e298790cd484ec9ba319a379e7e34ed", "Actual registration namespace")
demand(scope["ordered_cases"] == ["real-existing-open-readonly", "real-existing-self-send"] and scope["limits"]["SDK_MODEL_Node_external_paid_private_calls"] == 0, "Exact held2 roster/no SDK model Node")
demand(scope["launch_limits"] == {"outer_timeout_seconds":3600,"inner_soft_deadline_seconds":3300,"termination_cleanup_seconds":5}, "Original owned lifecycle limits")
demand(scope["expected_before_registration"] == [333,161,524] and scope["expected_registration"] == [334,162,532], "Fixed original failure registration cut")
demand(set(scope["public_environment"]) == {"SystemRoot","WINDIR","ComSpec","PATH","PATHEXT"}, "Public environment only")
grant_path = str(Path(scope["new_authorization_root"]) / "authorization.execute.json")
demand(contract["future_grant_path"] == grant_path and contract["actual_grant_ref"] is None and contract["current_binding_ref"] is None, "Open exact-scope-derived grant/binding")
demand(handoff["future_grant_SHA"] is None and handoff["future_Root_output_directory"] is None and handoff["future_current_binding_ref"] is None, "No future authority self grant")
demand(handoff["candidate_executed"] is False and handoff["source_acceptance"] is False and handoff["formal_increment"] == 0 and contract["formal_increment"] == 0, "Source-only decision boundary")
module_sources = {}
for key in ["launcher_ref","runner_ref","authorization_gate_ref","owned_process_helper_ref","debug_tree_helper_ref"]:
    raw = verify(scope[key])
    ast.parse(raw)
    module_sources[key] = raw.decode("utf-8")
demand(scope["launcher_ref"]["sha256"] == "0a958ae65c1f3cf5449b4b4f7b09257a515cc17691fd8ae1f99852057a140f11" and scope["launcher_ref"]["bytes"] == 7190, "Original launcher exact pin")
gate = module_sources["authorization_gate_ref"]
launcher = module_sources["launcher_ref"]
runner = module_sources["runner_ref"]
owned = module_sources["owned_process_helper_ref"]
demand("grant['binding'] == binding(scope)" in gate and "grant['scope_ref'] == scope_ref" in gate and "Grant location" in gate and "actual_registration_completed" in gate, "Existing exact grant/binding verification")
demand("canonical_copies" in gate and "Registration independent review" in gate and "Actual current43 source authority missing" in gate, "Existing canonical/independent authority gates")
demand("len(set(roots)) == 4" in gate and "Overlapping roots" in gate and "Reparse/symlink path" in gate and "Path alias" in gate, "Four independent roots and alias validation")
demand("candidate.mkdir();out=candidate" in launcher and "util.safe(scope['new_wrapper_root']" in launcher and "util.job_ok(result)" in launcher and "helper.run_owned(argv,str(util.ROOT),env,stdout,stderr,3600)" in launcher, "Exclusive launcher wrapper and real owned child")
demand("'primary_exit_confirmed', 'job_idle_confirmed', 'handles_closed'" in runner and "'active_processes_last_observed'] == 0" in runner and "'Owned process cleanup incomplete'" in runner, "Actual closed cleanup gate")
demand("time.monotonic() - started < 3300" in runner and "deadline = time.monotonic() + 5.0" in owned, "3300 soft limit/5 cleanup")
before = [ref(path) for path in sorted(seen)]
save("inputs.before.json", before)
after = [ref(path) for path in sorted(seen)]
demand(before == after, "Independent source input drift")
save("inputs.after.json", after)
save("static-audit.json", {
    "schema":"researchos.current58-cli2-root-caller-independent-static-audit.v1",
    "candidate_ref":candidate_ref, "preparation_manifest_ref":ref(PREP/"manifest.json"),
    "preparation_manifest_members":12, "preparation_manifest_closed":True,
    "frozen_inputs":8,"frozen_input_drift":0,"whole_inverse_exact":True,"inverse_edit_count":5,
    "unified_diff_hunk_count":rendered_diff.decode().count("@@ -"),"original_three_defs_AST_equal":True,
    "original_result_try_except_finally_exit_tail_bytes_equal":True,
    "caller_exclusive_open_sites":3,"caller_output_file_names":contract["outputs"],
    "caller_single_subprocess_run":True,"caller_subprocess_timeout_seconds":3900,
    "caller_OS_lifecycle_qualification":False,"scope_ref":contract["scope_ref"],
    "exact_current58_source_commit":scope["source_commit"],"module_refs":{k:scope[k] for k in module_sources},
    "public_environment":scope["public_environment"],"grant_path_derived_only_from_fixed_scope":grant_path,
    "grant_ref":None,"future_grant_SHA":None,"future_Root_output_directory":None,"future_currentbinding_ref":None,
    "scope_roots_distinct_nonoverlapping_reparse_guarded":True,
    "caller_output_alias_guard":"Canonical absolute resolve equality; no ..; public receipt only; rejects preparation and registration tree; existing-empty requirement.",
    "caller_output_existing_historical_parent_limitation":"Root must allocate a new independent public directory. An empty historical descendant is not distinguished by caller; Root allocation remains OPEN. Overlap with wrapper/output roots causes independent fresh-path gates to fail, never grants authority.",
    "owned_launcher_timeout_seconds":3600,"runner_soft_deadline_seconds":3300,"cleanup_seconds":5,
    "runtime_qualification_requires_actual_closed":True,"actual_closed_runtime_evidence":None,
    "first_cause_semantics":"Original caller tail preserved. Preflight failures require outer raw stderr; primary process errors retained in caller_error and write/hash failures in secondary.",
    "known_finalization_limit":contract["known_finalization_limit"],
    "old_r331_evidence_scope":"Source/manifest/interface only; no current58 compiler or case qualification",
    "source_acceptance":False,"formal_increment":0,"candidate_imported":False,"candidate_executed":False,
    "Go_SQL_HTTP_Node_SDK_model_candidate_calls":0,"input_count":len(before),"input_drift":0,
    "decision":"READY_SOURCE_PREPARATION_ONLY","state":"STOPPED"
})
print(json.dumps({"decision":"READY_SOURCE_PREPARATION_ONLY","state":"STOPPED","static_audit_ref":ref(OUT/"static-audit.json"),"input_count":len(before),"candidate_calls":0},ensure_ascii=False))

