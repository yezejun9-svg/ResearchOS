"""SOURCE PREPARATION ONLY; copy pinned sources into this unique receipt namespace."""
import ast
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path("D:/作品集/ResearchOS/research-os")
OWN = Path(__file__).resolve().parent
W13 = ROOT / "execution/v2.4/receipts/W13/W13-03"
OLD_ADAPTER = W13 / "desktop58_root_authority_adapter_revision_preparation_codex/fde71451a31d4404b8e3d57b396f270c/authorization_adapter.v2.proposed.py"
OLD_META = W13 / "desktop58_root_metadata_scope_binding_revision_preparation_codex/1c4ea6999d4d4437a0202c4e81ce581b"
OLD_TEMPLATE = W13 / "desktop58_root_metadata_binding_preparation_codex/a03b8a59d79049ae87694932ac40ce5d/scope.desktop58.template.json"
OLD_GATE_SHA = "6a8b87dd4b1edfcbe669a656d02fe5b0bc16a7ac1eca1412be5d737e1c4dadd8"
OLD_META_SHA = "ce57675388c87ced955106931425175adae974def5a10b214de01efdfb40836c"
OLD_BUILDER_SHA = "45585615bff3cb63c056b5e60a862371c7b3c2229cba56e15e1ff4b215466368"
OLD_TEMPLATE_SHA = "bf0775ad2a1131f0d0a8677822568f10abb866e02f0e6ac624de45bb7d5054c5"

def raw(path, expected=None):
    data = path.read_bytes()
    if expected is not None and hashlib.sha256(data).hexdigest() != expected:
        raise RuntimeError("Pinned source drift: " + str(path))
    return data

def pin(path):
    data = raw(path)
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}

def put(name, data):
    path = OWN / name
    with path.open("xb") as out:
        out.write(data)
    return path

def unique_replace(data, old, new, label):
    if data.count(old) != 1:
        raise RuntimeError("Not a unique source edit: " + label)
    return data.replace(old, new, 1)

old_gate = raw(OLD_ADAPTER, OLD_GATE_SHA).decode("utf-8")
old_pipeline_path = OLD_META / "metadata_pipeline.desktop58.bound.v2.proposed.py"
old_builder_path = OLD_META / "build_binding.desktop58.bound.v2.proposed.py"
old_pipeline = raw(old_pipeline_path, OLD_META_SHA).decode("utf-8")
old_builder = raw(old_builder_path, OLD_BUILDER_SHA).decode("utf-8")
old_template = json.loads(raw(OLD_TEMPLATE, OLD_TEMPLATE_SHA))
closure_source = raw(OWN / "cli_root_closure_function.py.txt").decode("utf-8")
if old_template["authorization_verifier_ref"] != pin(OLD_ADAPTER):
    raise RuntimeError("Old scope template/gate pin differs")
insert_at = "\ndef member(reader, members, item):"
old_call = "rt = sealed_manifest(reader, evidence['root_closed_manifest_ref'], 'members')"
new_call = (
    "rt = sealed_cli_root_closure(reader, evidence['root_closed_manifest_ref'], evidence['root_completion_ref'],\n"
    "        evidence['scope_ref'], evidence['grant_ref'], evidence['executor_manifest_ref'],\n"
    "        evidence['launcher_manifest_ref'], ex, la, q['run_uuid'])"
)
new_gate = unique_replace(old_gate, insert_at, "\n" + closure_source + insert_at, "aggregate function")
new_gate = unique_replace(new_gate, old_call, new_call, "aggregate call")
gate_path = put("authorization_adapter.v3.cli_root.proposed.py", new_gate.encode("utf-8"))
gate_ref = pin(gate_path)
new_pipeline = unique_replace(old_pipeline, OLD_GATE_SHA, gate_ref["sha256"], "pipeline gate pin")
pipeline_path = put("metadata_pipeline.desktop58.bound.v3.proposed.py", new_pipeline.encode("utf-8"))
pipeline_ref = pin(pipeline_path)
new_builder = unique_replace(old_builder, OLD_GATE_SHA, gate_ref["sha256"], "builder gate pin")
builder_path = put("build_binding.desktop58.bound.v3.proposed.py", new_builder.encode("utf-8"))
builder_ref = pin(builder_path)
wrappers = {}
wrapper_inverse = {}
for name in ("prepare.py", "register.py", "scope_builder.py", "grant_preflight.py", "run.py", "seal.py"):
    before = raw(OLD_META / name).decode("utf-8")
    old_literal = repr(str(old_pipeline_path))
    new_literal = repr(str(pipeline_path))
    after = unique_replace(before, old_literal, new_literal, name + " path")
    after = unique_replace(after, OLD_META_SHA, pipeline_ref["sha256"], name + " pipeline pin")
    output = put(name, after.encode("utf-8"))
    wrappers[name] = pin(output)
    wrapper_inverse[name] = (
        after.replace(pipeline_ref["sha256"], OLD_META_SHA, 1)
             .replace(new_literal, old_literal, 1) == before
    )
new_template = dict(old_template)
new_template["authorization_verifier_ref"] = gate_ref
template_path = put("scope.desktop58.template.v3.json",
                    (json.dumps(new_template, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
template_ref = pin(template_path)
all_python = [gate_path, pipeline_path, builder_path, *[OWN / n for n in wrappers]]
compile_checks = {}
for path in all_python:
    source = raw(path).decode("utf-8")
    ast.parse(source, filename=str(path))
    compile(source, str(path), "exec", dont_inherit=True)
    compile_checks[path.name] = True
inverse = {
    "schema": "researchos.cli-root-closure-source-inverse.v1",
    "old_adapter_ref": pin(OLD_ADAPTER),
    "old_pipeline_ref": pin(old_pipeline_path),
    "old_builder_ref": pin(old_builder_path),
    "old_template_ref": pin(OLD_TEMPLATE),
    "new_adapter_ref": gate_ref,
    "new_pipeline_ref": pipeline_ref,
    "new_builder_ref": builder_ref,
    "new_template_ref": template_ref,
    "new_wrapper_refs": wrappers,
    "adapter_exact_inverse": new_gate.replace(new_call, old_call, 1)
                                .replace("\n" + closure_source + insert_at, insert_at, 1) == old_gate,
    "pipeline_exact_inverse": new_pipeline.replace(gate_ref["sha256"], OLD_GATE_SHA, 1) == old_pipeline,
    "builder_exact_inverse": new_builder.replace(gate_ref["sha256"], OLD_GATE_SHA, 1) == old_builder,
    "template_only_verifier_ref_changed": {
        k:v for k,v in new_template.items() if k != "authorization_verifier_ref"
    } == {
        k:v for k,v in old_template.items() if k != "authorization_verifier_ref"
    },
    "wrapper_exact_inverse": wrapper_inverse,
    "ast_parse_and_compile_without_import": compile_checks,
    "candidate_imported_or_executed": False,
    "scope_cas_grant_or_target_executed": False,
}
put("inverse.json", (json.dumps(inverse, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
print(json.dumps({
    "new_adapter_ref": gate_ref, "new_pipeline_ref": pipeline_ref,
    "new_builder_ref": builder_ref, "new_template_ref": template_ref,
    "wrappers": wrappers, "inverse_ref": pin(OWN / "inverse.json")
}, ensure_ascii=False))
