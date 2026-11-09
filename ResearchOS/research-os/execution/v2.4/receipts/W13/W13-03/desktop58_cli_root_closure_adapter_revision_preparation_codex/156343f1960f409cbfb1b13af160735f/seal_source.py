"""Seal SOURCE_PREPARATION_ONLY receipts; never import or execute candidates."""
import hashlib
import json
import sys
from pathlib import Path
sys.dont_write_bytecode = True
OWN = Path(__file__).resolve().parent

def pin(path):
    data = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}

def save(path, obj):
    with path.open("x", encoding="utf-8") as out:
        out.write(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n")

names = [
    "authorization_adapter.v3.cli_root.proposed.py",
    "metadata_pipeline.desktop58.bound.v3.proposed.py",
    "build_binding.desktop58.bound.v3.proposed.py",
    "scope.desktop58.template.v3.json",
    "prepare.py", "register.py", "scope_builder.py", "grant_preflight.py",
    "run.py", "seal.py", "cli_root_closure_function.py.txt",
    "source_writer.py", "seal_source.py", "inverse.json", "tool-observations.json",
    "failure-origin-01.json", "failure-origin-02.json", "failure-origin-03.json",
]
entries = {name: pin(OWN / name) for name in names}
inverse = json.loads((OWN / "inverse.json").read_text(encoding="utf-8"))
diagnostic_ref = {
    "path": "D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop58_cli2_root_closure_seam_diagnostic_codex/bd59e233e8834c0b80976f0067a12a91/review.json",
    "sha256": "da44c9bdd6cfb812eb7e21a48724f6023ba299173808ae04255d0b557904ae5c",
    "bytes": 7516,
}
manifest = {
    "schema": "researchos.cli-root-closure-adapter-source-manifest.v1",
    "stage": "SOURCE_PREPARATION_ONLY",
    "entries": entries,
    "base_refs": {
        "adapter": inverse["old_adapter_ref"],
        "pipeline": inverse["old_pipeline_ref"],
        "builder": inverse["old_builder_ref"],
        "scope_template": inverse["old_template_ref"],
    },
    "independent_diagnostic_ref": diagnostic_ref,
    "all_inverse_true": inverse["adapter_exact_inverse"] and
        inverse["pipeline_exact_inverse"] and inverse["builder_exact_inverse"] and
        inverse["template_only_verifier_ref_changed"] and
        all(inverse["wrapper_exact_inverse"].values()),
    "all_ast_parse_compile_true": all(inverse["ast_parse_and_compile_without_import"].values()),
    "candidate_import_or_execution": False,
    "scope_or_cas_execution": False,
    "source_acceptance": False,
    "formal_increment": 0,
    "new_failure_origins_count": 3,
}
save(OWN / "manifest.json", manifest)
handoff = {
    "schema": "researchos.cli-root-closure-adapter-source-handoff.v1",
    "status": "SOURCE_PREPARATION_ONLY",
    "manifest_ref": pin(OWN / "manifest.json"),
    "adapter_ref": entries["authorization_adapter.v3.cli_root.proposed.py"],
    "pipeline_ref": entries["metadata_pipeline.desktop58.bound.v3.proposed.py"],
    "builder_ref": entries["build_binding.desktop58.bound.v3.proposed.py"],
    "scope_template_ref": entries["scope.desktop58.template.v3.json"],
    "wrapper_refs": {n: entries[n] for n in
        ("prepare.py","register.py","scope_builder.py","grant_preflight.py","run.py","seal.py")},
    "inverse_ref": entries["inverse.json"],
    "failure_origin_refs": [entries["failure-origin-01.json"],
                            entries["failure-origin-02.json"],
                            entries["failure-origin-03.json"]],
    "provenance_diagnostic_ref": diagnostic_ref,
    "repair": "Q/E/L retain single-namespace validation; only pinned Root aggregate uses exact producer READS169. Root must allocate new REG/tuple/cut and independently review before prepare.",
    "candidate_import_or_execution": False,
    "provider_or_product_call": False,
    "scope_or_cas_execution": False,
    "source_acceptance": False,
    "formal_increment": 0,
}
save(OWN / "handoff.json", handoff)
print(json.dumps({
    "handoff": pin(OWN / "handoff.json"),
    "manifest": pin(OWN / "manifest.json"),
    "adapter": entries["authorization_adapter.v3.cli_root.proposed.py"],
    "inverse": entries["inverse.json"],
    "failure_origins": handoff["failure_origin_refs"],
}, ensure_ascii=False))
