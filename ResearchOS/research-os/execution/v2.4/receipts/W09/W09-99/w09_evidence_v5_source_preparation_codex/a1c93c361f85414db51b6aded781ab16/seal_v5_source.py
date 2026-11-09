"""W09 v5 source-only static audit, inverse and exclusive seal."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True

here = Path(__file__).resolve().parent
root = here.parents[6]
old = here.parents[1] / "w09_evidence_revision_source_preparation_codex/fdbee1676fd64d8b9a93ce81076c6c4c"
review = here.parents[1] / "w09_evidence_revision_independent_source_review_codex/29754be17e2e49f183866442b9c2f92b/review.json"

def pin(path):
    raw = path.read_bytes()
    return {"path": str(path.resolve(strict=True)), "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw)}

def write_json(name, obj):
    path = here / name
    raw = (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with path.open("xb") as stream: stream.write(raw)
    return pin(path)

names = [
    ("domain_test.proposed.go", "domain_test.v5.proposed.go"),
    ("retrieval_test.proposed.go", "retrieval_test.v5.proposed.go"),
    ("retrieval.proposed.py", "retrieval.v5.proposed.py"),
    ("w09_evidence_export_test.proposed.go", "w09_evidence_export_test.v5.proposed.go"),
    ("w09_formal_router.v4.proposed.py", "w09_formal_router.v5.proposed.py"),
    ("w09_evidence_closure.py", "w09_evidence_closure.v5.proposed.py"),
]

# Audit every input and final source before writing any seal member.
assert pin(review)["sha256"] == "385ff994c0d8ddb1c63e28e10e3040038ff5807cd0a833fa62047d9dc9bdbc7b"
assert pin(review)["bytes"] == 22032
reviewed = json.loads(review.read_bytes())
assert reviewed["decision"] == "REQUEST_CHANGES"
old_refs = {Path(row["path"]).name: row for row in reviewed["selected_source_refs"]}
for old_name, new_name in names:
    assert pin(old / old_name)["sha256"] == old_refs[old_name]["sha256"]
    assert pin(old / old_name)["bytes"] == old_refs[old_name]["bytes"]
    assert (here / new_name).is_file()
for old_name, new_name in (names[0], names[3]):
    assert (old / old_name).read_bytes() == (here / new_name).read_bytes()

for _, new_name in names:
    if new_name.endswith(".py"):
        ast.parse((here / new_name).read_bytes(), filename=new_name)
mode = json.loads((here / "postrun-mode-interface.proposed.json").read_bytes())
assert mode["native_run_executed_in_source_preparation"] is False
assert mode["formal_case_accepted_delta"] == 0
old_router = ast.parse((old / names[4][0]).read_bytes())
new_router = ast.parse((here / names[4][1]).read_bytes())
def assignment(tree, name):
    return next(ast.dump(node.value, include_attributes=False) for node in tree.body
                if isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id == name)
for name in ("NATIVE", "FORMAL", "PRESERVED", "SOURCE_SCOPE", "SELECTED", "ASSERTION_OWNER"):
    assert assignment(old_router, name) == assignment(new_router, name)
old_go = (old / "retrieval_test.proposed.go").read_text(encoding="utf-8")
new_go = (here / "retrieval_test.v5.proposed.go").read_text(encoding="utf-8")
assert re.findall(r'w09Assertion\(t, "[A-Z0-9-]+"', old_go) == re.findall(
       r'w09Assertion\(t, "[A-Z0-9-]+"', new_go)
assert old_go.count("func TestW09") == new_go.count("func TestW09")
closure = (here / "w09_evidence_closure.v5.proposed.py").read_text(encoding="utf-8")
router = (here / "w09_formal_router.v5.proposed.py").read_text(encoding="utf-8")
producer = (here / "retrieval.v5.proposed.py").read_text(encoding="utf-8")
assert 're.fullmatch(r"simulated-opinion-(?:0[0-9]|1[0-9])", label)' in closure
assert 'simulated-opinion-binding' in closure and 'C19_RAW_OPINION_BODY_SET_MISMATCH' in closure
assert 'C19_SIM_HTTP_CALL_NOT_UNIQUE_' in closure and 'A06_CONTEXT_PERMISSION_CALL_GRAPH_MISSING' in closure
assert 'safe_repo_pin(root, item)' in closure and 'witness_allowlist' in closure
assert '["cmd.exe", "/c", "mklink", "/J",' in closure
assert 'NOT_RUN_POSTRUN_REVIEW_PENDING' in producer and 'native-tool-run.json' in producer
assert '_pinned_native_report()' in router and 'source, report, tool = _pinned_native_report()' in router
assert 'w09_evidence_closure import' in router
assert 'a06-materialize-stale-rejected' in new_go and 'a06-bundle-after-delete' in new_go
assert pin(here / "failure-origin-1.json")["sha256"] == "44f974bf98b3503ec203e041b53e971c684a9081fd612dbe7436259755b8c074"

diffs = []
for old_name, new_name in names:
    if (old / old_name).read_bytes() == (here / new_name).read_bytes():
        continue
    before = (old / old_name).read_text(encoding="utf-8").splitlines(keepends=True)
    after = (here / new_name).read_text(encoding="utf-8").splitlines(keepends=True)
    delta = "".join(difflib.unified_diff(before, after, fromfile="v4/" + old_name,
                                         tofile="v5/" + new_name, n=3))
    assert delta
    diffs.append((new_name + ".patch", delta))
for filename, data in diffs:
    with (here / filename).open("xb") as stream:
        stream.write(data.encode("utf-8"))

inverse = {
    "schema": "researchos.w09-v5-source-inverse.v1",
    "baseline_review_ref": pin(review),
    "six_source_pairs": [{"old": pin(old / before), "new": pin(here / after),
                          "exact_copy": (old / before).read_bytes() == (here / after).read_bytes()}
                         for before, after in names],
    "four_changed_unified_diff_refs": [pin(here / filename) for filename, _ in diffs],
    "preserved_router_selector_AST": ["NATIVE", "FORMAL", "PRESERVED", "SOURCE_SCOPE",
                                       "SELECTED", "ASSERTION_OWNER"],
    "preserved_Go_business_assertion_calls": True,
    "product_or_canonical_files_modified": [],
    "inverse_operation": "Discard this independent exclusive v5 source packet. No v4/Main/canonical source was changed.",
    "historical_earliest_overwrite_bytes_recovered": False
}
inverse_ref = write_json("source-inverse.json", inverse)
report = {
    "schema": "researchos.w09-v5-source-report.v1", "stage": "SOURCE_PREPARATION_ONLY",
    "decision": "READY_FOR_INDEPENDENT_SOURCE_REVIEW", "baseline_review_ref": pin(review),
    "candidate_source_refs": [pin(here / new) for _, new in names],
    "postrun_interface_ref": pin(here / "postrun-mode-interface.proposed.json"),
    "source_inverse_ref": inverse_ref,
    "R1": "Only the exact simulated-opinion-00..19 label set is opaque. The 20 same-run binding JSON events remain structured. Body set, owner, ordinal and body pin join are checked; JSON-looking body bytes remain opaque.",
    "R2": "retrieval.v5 writes native report/raw and a same-run tool-run with formal NOT_RUN. The v5 router consumes an already pinned native report/tool-run, then a later independent mode decision; it never starts W09 native/Go for formal closure. Missing review remains NOT_RUN.",
    "R3": "Witnesses use exact triple-key typed Root-relative refs, reject alias/reparse/dot/absolute/drive-relative before reading, and must equal the decision's two-item current-run allowlist. Junction checks all six argv tokens plus same-run Root and target and witness command.",
    "R4": "C19 simulated ordinal/body/artifact/evidence IDs are joined through each original POST /content, /artifacts and /evidence request/response raw pin. A06 emits original bundle IDs and each Materialize success/rejection result/error/manifest at the call site; consumer joins those locators to the same task, root, principal and snapshot transition.",
    "I01_historical_initial_seal": "OPEN: earliest overwritten bytes and adjacent original apply_patch wrapper are not recovered. This is a fresh immutable source packet, not a restoration of old bytes.",
    "static_verification": {"Python_AST": "PASS", "selector_AST_unchanged": True,
        "Go_business_assertion_calls_unchanged": True, "unchanged_source_exactcopies": 2,
        "changed_source_diffs": len(diffs), "candidate_imported": False,
        "native_Go_Node_model_Git_CAS_invocations": 0},
    "runtime_positive_negative_controls": "NOT_RUN; independent reviewer must test after Root adoption",
    "actual_native_report": None, "actual_mode_review": None,
    "actual_windows_witnesses": None, "actual_source_acceptance": False,
    "formal_case_accepted_delta": 0,
    "failure_origin_refs_new": [pin(here / "failure-origin-1.json")],
    "parent_fixed_fourth_cut_48_to_580_unchanged": True
}
report_ref = write_json("report.json", report)
manifest_members = [pin(here / new) for _, new in names] + [
    pin(here / "postrun-mode-interface.proposed.json"), inverse_ref, report_ref,
    pin(here / "failure-origin-1.json"), *[pin(here / filename) for filename, _ in diffs]]
assert len({row["path"].casefold() for row in manifest_members}) == len(manifest_members)
manifest = {"schema": "researchos.w09-v5-independent-source-manifest.v1",
            "stage": "SOURCE_PREPARATION_ONLY", "members": manifest_members,
            "member_count": len(manifest_members), "historical_I01": "OPEN",
            "source_acceptance": False, "formal_case_accepted_delta": 0}
manifest_ref = write_json("manifest.json", manifest)
handoff = {"schema": "researchos.w09-v5-independent-source-handoff.v1",
           "stage": "STOPPED_SOURCE_PREPARATION_ONLY", "decision": "REVIEW_REQUESTED",
           "report_ref": report_ref, "manifest_ref": manifest_ref,
           "source_inverse_ref": inverse_ref,
           "candidate_source_refs": [pin(here / new) for _, new in names],
           "postrun_interface_ref": pin(here / "postrun-mode-interface.proposed.json"),
           "new_failure_origin_refs": [pin(here / "failure-origin-1.json")],
           "historical_I01": "OPEN", "actual_native_or_formal_run": False,
           "formal_case_accepted_delta": 0}
handoff_ref = write_json("handoff.json", handoff)
print(json.dumps({"report": report_ref, "manifest": manifest_ref,
                  "handoff": handoff_ref, "inverse": inverse_ref}, ensure_ascii=False))
