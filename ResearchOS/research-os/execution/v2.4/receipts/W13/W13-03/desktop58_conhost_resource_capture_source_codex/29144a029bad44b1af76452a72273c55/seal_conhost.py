"""Seal a SOURCE_ONLY conhost resource constructor proposal; never execute it."""
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
BASE = ROOT / "execution/v2.4/receipts/W13/W13-03/desktop58_windows_resource_capture_source_revision_codex/3aff012b57924a41a233cb9e162cfc0d/construct_root_inputs.desktop58.wldp.proposed.py"
SOURCE = HERE / "construct_root_inputs.desktop58.conhost.proposed.py"
REPORT = ROOT / "execution/v2.4/receipts/W13/W13-03/desktop58_conhost_resource_diagnostic_codex/0a2dfbb74d3b4f0fb12192390b80cbea/report.json"
MANIFEST = REPORT.with_name("manifest.json")
HANDOFF = REPORT.with_name("handoff.json")
DELTA = REPORT.with_name("exact-resource-delta.json")
ORIGINS = [HERE / "failure-origin-001.json", HERE / "failure-origin-002.json"]

def pin(path):
    raw = path.read_bytes()
    return {"path": str(path).replace("\\", "/"),
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def put(name, obj):
    raw = (json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    with (HERE / name).open("xb") as out:
        out.write(raw)

def patch(name, a, b, left, right):
    raw = "".join(difflib.unified_diff(a.splitlines(keepends=True),
        b.splitlines(keepends=True), fromfile=left, tofile=right)).encode("utf-8")
    with (HERE / name).open("xb") as out:
        out.write(raw)

assert pin(BASE) == {
    "path": str(BASE).replace("\\", "/"),
    "sha256": "9f64bd96b11ea017656e1262b0caaede1cf295ee5e75dd689751439a868834a7",
    "bytes": 25948}
assert pin(REPORT)["sha256"] == "6584aa7e854b9fad0978e7d09aa64f510eab86d77a478f72e76c0f6b869858fc"
assert pin(MANIFEST)["sha256"] == "d10e269678421a8741a09571df7a12e9fb6091be1bd50dbbde8849a99d4488db"
assert pin(HANDOFF)["sha256"] == "57f9799a1b69574894f59956853ef412229b778274d6458af760791a61a80b5c"
assert pin(DELTA)["sha256"] == "bf28231fe85094bb12fe7728b7dde3ad2f2616c295c982a3fc98654d9cbb80ae"
base_text, new_text = BASE.read_text(encoding="utf-8"), SOURCE.read_text(encoding="utf-8")
old_tree, new_tree = ast.parse(base_text), ast.parse(new_text)
compile(new_tree, str(SOURCE), "exec", dont_inherit=True)
old_fns = {n.name: n for n in old_tree.body if isinstance(n, ast.FunctionDef)}
new_fns = {n.name: n for n in new_tree.body if isinstance(n, ast.FunctionDef)}
assert set(new_fns) - set(old_fns) == {"validate_conhost_chain"}
assert all(ast.dump(old_fns[name], include_attributes=False) ==
           ast.dump(new_fns[name], include_attributes=False)
           for name in old_fns if name != "run")
trace = list(difflib.ndiff(base_text.splitlines(keepends=True), new_text.splitlines(keepends=True)))
assert "".join(difflib.restore(trace, 1)) == base_text
assert "".join(difflib.restore(trace, 2)) == new_text
check = json.loads((HERE / "precheck.conhost.json").read_bytes())
io = json.loads((HERE / "precheck.tool-io.json").read_bytes())
assert check["candidate_ast_compiled"] and not check["constructor_executed"]
assert io["actual_python_exit"] == io["result"]["exit_code"] == 0
assert len(ORIGINS) == 2 and all(json.loads(path.read_bytes())["counter_increment"] == 1 for path in ORIGINS)
patch("forward.wldp-to-conhost.patch", base_text, new_text,
      "a/construct_root_inputs.desktop58.wldp.proposed.py",
      "b/construct_root_inputs.desktop58.conhost.proposed.py")
patch("inverse.conhost-to-wldp.patch", new_text, base_text,
      "a/construct_root_inputs.desktop58.conhost.proposed.py",
      "b/construct_root_inputs.desktop58.wldp.proposed.py")
put("source-inverse.json", {
    "schema": "researchos.desktop58-conhost-source-inverse.v1",
    "base_ref": pin(BASE), "candidate_ref": pin(SOURCE),
    "forward_ref": pin(HERE / "forward.wldp-to-conhost.patch"),
    "inverse_ref": pin(HERE / "inverse.conhost-to-wldp.patch"),
    "full_bytes_roundtrip_equal": True,
    "old_functions_unchanged_except_run": sorted(name for name in old_fns if name != "run"),
    "added_pure_data_helper": "validate_conhost_chain",
    "candidate_executed": False})
report = {
    "schema": "researchos.desktop58-conhost-capture-source-proposal.v1",
    "stage": "SOURCE_RESOURCE_CANDIDATE_ONLY",
    "source_ref": pin(SOURCE), "base_ref": pin(BASE),
    "source_inverse_ref": pin(HERE / "source-inverse.json"),
    "independent_diagnostic_refs": [pin(REPORT), pin(MANIFEST), pin(HANDOFF), pin(DELTA)],
    "future_q_template_ref": pin(HERE / "root-q.conhost-fields.template.json"),
    "static_precheck_ref": pin(HERE / "precheck.conhost.json"),
    "precheck_tool_io_ref": pin(HERE / "precheck.tool-io.json"),
    "failure_origins": [pin(path) for path in ORIGINS],
    "new_tool_failure_count": 2,
    "source_delta": [
        "Require exact fixed independent diagnostic report/delta/handoff/manifest and all nine reviewed manifest member pins.",
        "Bind six unique System32 rows to reviewed static PE direct/delay evidence; reject prior-catalog overlap.",
        "Rehash each physical six-row pin before and after source-only construction.",
        "Add six rows to runtime/files and catalog/files, only conhost.exe to images; preserve wldp.",
        "Require premetadata runtime1289, final runtime1303, catalog23874, images17 and compiler22138."
    ],
    "image_total_with_generated_3_and_declared_alias_20": 40,
    "helper_image_limit": 64, "controller_static_image_limit": 60,
    "dynamic_loader_and_api_set_closure": None,
    "fresh_complete_capture_and_review_required": True,
    "new_root_uuid": None, "new_scope_or_grant": None,
    "actual_constructor_or_native_execution": 0,
    "main_or_canonical_modified": False,
    "source_acceptance": False, "formal_case_accepted_delta": 0,
    "status": "STOPPED_AFTER_SEAL"}
put("report.json", report)
members = [pin(path) for path in sorted(HERE.iterdir()) if path.is_file()
           and path.name not in {"manifest.json", "handoff.json"}]
put("manifest.json", {"schema": "researchos.desktop58-conhost-capture-source-manifest.v1",
                      "namespace": str(HERE).replace("\\", "/"),
                      "members": members, "members_count": len(members),
                      "source_only": True, "actual_target_executions": 0})
put("handoff.json", {
    "schema": "researchos.desktop58-conhost-capture-source-handoff.v1",
    "stage": "SOURCE_RESOURCE_CANDIDATE_ONLY",
    "source_ref": pin(SOURCE), "report_ref": pin(HERE / "report.json"),
    "manifest_ref": pin(HERE / "manifest.json"),
    "inverse_ref": pin(HERE / "source-inverse.json"),
    "template_ref": pin(HERE / "root-q.conhost-fields.template.json"),
    "precheck_ref": pin(HERE / "precheck.conhost.json"),
    "failure_origins": [pin(path) for path in ORIGINS],
    "new_root_authority": None, "actual_constructor_or_native_execution": 0,
    "source_acceptance": False, "formal_case_accepted_delta": 0,
    "status": "STOPPED_AFTER_SEAL"})
print(json.dumps({"report": pin(HERE / "report.json"),
                  "manifest": pin(HERE / "manifest.json"),
                  "handoff": pin(HERE / "handoff.json"),
                  "origins": [pin(path) for path in ORIGINS]}, ensure_ascii=False))
