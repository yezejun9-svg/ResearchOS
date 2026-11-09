"""Static and pure-data diagnostic-chain checks; never imports/runs constructor."""
import ast
import copy
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path("D:/作品集/ResearchOS/research-os")
HERE = Path(__file__).resolve().parent
OLD = ROOT / "execution/v2.4/receipts/W13/W13-03/desktop58_windows_resource_capture_source_revision_codex/3aff012b57924a41a233cb9e162cfc0d/construct_root_inputs.desktop58.wldp.proposed.py"
NEW = HERE / "construct_root_inputs.desktop58.conhost.proposed.py"
DIAG = ROOT / "execution/v2.4/receipts/W13/W13-03/desktop58_conhost_resource_diagnostic_codex/0a2dfbb74d3b4f0fb12192390b80cbea"
old_tree, new_tree = ast.parse(OLD.read_text(encoding="utf-8")), ast.parse(NEW.read_text(encoding="utf-8"))
compile(new_tree, str(NEW), "exec", dont_inherit=True)
old_fns = {n.name: n for n in old_tree.body if isinstance(n, ast.FunctionDef)}
new_fns = {n.name: n for n in new_tree.body if isinstance(n, ast.FunctionDef)}
assert set(new_fns) - set(old_fns) == {"validate_conhost_chain"}
assert all(ast.dump(old_fns[name], include_attributes=False) ==
           ast.dump(new_fns[name], include_attributes=False)
           for name in old_fns if name != "run")
src = NEW.read_text(encoding="utf-8")
assert src.count("[actual(ref) for ref in conhost_refs]") == 2
assert "len(runtime_rows) == 1289" in src and "len(runtime['files']) == 1303" in src
assert "len(union) == 23874" in src and "len(images) == 17" in src
template = json.loads((HERE / "root-q.conhost-fields.template.json").read_bytes())
q = template["new_root_q_fields"]
def load(name):
    return json.loads((DIAG / name).read_bytes())
delta, report, handoff, manifest, evidence = (
    load("exact-resource-delta.json"), load("report.json"), load("handoff.json"),
    load("manifest.json"), load("pe-and-catalog-evidence.json"))
pins = {key: (Path(ref["path"]).name, ref["sha256"], ref["bytes"])
        for key, ref in q.items()}
ns = {
    "Path": Path, "CONHOST_NS": DIAG, "CONHOST_PINS": pins,
    "CONHOST_EVIDENCE_REF": handoff["evidence_ref"],
    "OLD_WLDP_CONSTRUCTOR_REF": report["constructor_ref"],
}
mod = ast.fix_missing_locations(ast.Module(body=[new_fns["need"],
    new_fns["validate_conhost_chain"]], type_ignores=[]))
exec(compile(mod, str(NEW), "exec", dont_inherit=True), ns)
validate = ns["validate_conhost_chain"]
assert validate(q, delta, report, handoff, manifest, evidence) == delta["additions_to_catalog_and_runtime"]

def reject(mutator, reason):
    values = [copy.deepcopy(x) for x in (q, delta, report, handoff, manifest, evidence)]
    mutator(*values)
    try:
        validate(*values)
    except RuntimeError as exc:
        assert reason in str(exc), (reason, str(exc))
    else:
        raise AssertionError("accepted tampered diagnostic: " + reason)

reject(lambda q,d,r,h,m,e: d["additions_to_catalog_and_runtime"].__setitem__(1,
       d["additions_to_catalog_and_runtime"][0]), "Exactly six")
reject(lambda q,d,r,h,m,e: q["conhost_resource_delta_ref"].__setitem__("sha256",
       "0" * 64), "Conhost diagnostic pin")
reject(lambda q,d,r,h,m,e: d.__setitem__("static_images_add",
       [d["additions_to_catalog_and_runtime"][1]]), "Exactly six")
reject(lambda q,d,r,h,m,e: d["conditional_new_counts"].__setitem__("runtime_files",
       1304), "Conhost count contract")
reject(lambda q,d,r,h,m,e: r.__setitem__("reviewer",
       "codex:/root/not-independent"), "Conhost independent review chain")
reject(lambda q,d,r,h,m,e: h.__setitem__("resource_delta_ref",
       {"path": "D:/foreign/delta.json", "sha256": "0" * 64, "bytes": 0}),
       "Conhost independent review chain")
reject(lambda q,d,r,h,m,e: e["direct_edges"].__setitem__(
       slice(None), [edge for edge in e["direct_edges"] if
       edge["import_name"].casefold() != "icu.dll"]), "Reviewed direct dependency")

result = {
    "schema": "researchos.desktop58-conhost-source-static-precheck.v1",
    "candidate_ast_compiled": True, "candidate_imported": False,
    "constructor_executed": False, "actual_physical_pin_executed": False,
    "go_node_electron_cmd_dll_model_executed": False,
    "unchanged_prior_functions_ast": len(old_fns) - 1,
    "positive": "exact independent review chain + six-row delta accepted as data",
    "negative": ["duplicate path", "wrong diagnostic pin", "DLL in images",
                 "wrong count", "untrusted reviewer", "foreign delta", "missing PE edge"],
    "pre_post_physical_repin_static": True,
    "dynamic_loader_complete": False, "source_acceptance": False
}
with (HERE / "precheck.conhost.json").open("xb") as out:
    out.write((json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))
print(json.dumps(result, ensure_ascii=False))
