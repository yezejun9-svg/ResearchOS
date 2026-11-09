import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

N = Path(__file__).resolve().parent


def pin(p):
    raw = p.read_bytes()
    return dict(path=str(p), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def read(p): return json.loads(p.read_bytes())


def save(p, value):
    with p.open("xb") as stream: stream.write((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())
    return pin(p)


for p in N.glob("*.py"): ast.parse(p.read_bytes())
controls = read(N / "source-controls.final.json")
assert controls["status"] == "SOURCE_CONTROLS_PASSED" and controls["caller_ref"] == pin(N / "main23_root.source.py")
assert all(pin(Path(ref["path"])) == ref for ref in controls["canonical_after"])
for ref in read(N / "source-inputs.json")["references"]:
    actual = pin(Path(ref["path"]))
    assert actual["sha256"] == ref["sha256"] and actual["bytes"] == ref["bytes"]
members = [pin(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in ("HDF.json", "MF.json")]
mf = save(N / "MF.json", dict(schema="researchos.main23-root-source-manifest.v1", members=members, complete_namespace_members_excluding_hdf_mf=True, formal_acceptance=False))
hdf = save(N / "HDF.json", dict(schema="researchos.main23-root-source-handoff.v1", status="SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_BINDING", created_utc=datetime.now(timezone.utc).isoformat(), source_author="codex:/root/native_temp_independent_review", manifest_ref=mf, caller_ref=pin(N / "main23_root.source.py"), registrar_ref=pin(N / "main23_root.source.py"), contract_ref=pin(N / "root-calling-contract.source.json"), source_inputs_ref=pin(N / "source-inputs.json"), controls_ref=pin(N / "source-controls.final.json"), facts_ref=pin(N / "source-facts.json"), recorded_tool_pairs_ref=pin(N / "recorded-tool-pairs.json"), builder_review_refs=read(N / "root-calling-contract.source.json")["builder_review_refs"], controls_passed=len(controls["controls"]), original_pending_1016_ref=pin(N / "original-pending-f38b4f.fullhostpair.json"), original_pending_1019_ref=pin(N / "original-pending-1019.full-tool-pair.json"), original_1019_external_root_binding_pending=True, current_observed_canonical_refs=controls["canonical_after"], current_observed_revisions=controls["current_revisions"], future_canonical_refs=None, actual_public371_registration_ref=None, candidate_program_ref=None, qualification_ref=None, actual_registration=False, actual_builder_execution=False, owned_jobs_started=0, Go_processes=0, product_processes=0, sqlite_calls=0, native_calls=0, model_calls=0, formal_acceptance=False, parent_acceptance=False, independent_non_author_review_required=True, schema21="OPEN", full20to24="OPEN", main23to24="BLOCKED_MAIN_NOT_ADOPTED"))
assert all(pin(Path(ref["path"])) == ref for ref in read(N / "MF.json")["members"])
print(json.dumps(dict(HDF=hdf, MF=mf, caller=pin(N / "main23_root.source.py"), contract=pin(N / "root-calling-contract.source.json"), failure1019=pin(N / "original-pending-1019.full-tool-pair.json"), namespace_members=len(members), controls_passed=len(controls["controls"]), canonical_unchanged=True), ensure_ascii=False))
