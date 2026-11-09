"""Exclusive, one-shot immutable annex seal. Pure IO."""
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
SOURCE = ROOT / "execution/v2.4/receipts/W09/W09-99/w09_evidence_revision_source_preparation_codex/fdbee1676fd64d8b9a93ce81076c6c4c"


def pin(path):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def exclusive(name, value):
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    with (HERE / name).open("xb") as file:
        file.write(raw)
    return pin(HERE / name)


base = str(HERE.relative_to(ROOT)).replace("\\", "/")
members = [pin(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.name not in
           {"manifest.final-v2.json", "handoff.final-v2.json"}]
manifest = exclusive("manifest.final-v2.json", {"schema": "researchos.w09-source-finalization-manifest.v1",
    "namespace": base, "members": members, "member_count": len(members), "formal_case_accepted_delta": 0})
source_manifest = pin(SOURCE / "manifest.json")
source_handoff = pin(SOURCE / "handoff.json")
assert source_manifest["sha256"] == "96f188cc56191613f3f7df85e0d777117fc6d93e60a10faebf043dbe1f8ba095"
assert source_handoff["sha256"] == "6cb9ca75c51a1a88ec0ab54b26620f2a288698aa4b4a6567b8f2f05986c1ba06"
handoff = exclusive("handoff.final-v2.json", {"schema": "researchos.w09-source-finalization-handoff.v1",
    "status": "STOPPED_SOURCE_ONLY", "namespace": base, "manifest_ref": manifest,
    "report_ref": pin(HERE / "finalization.report.json"),
    "current_source_manifest_ref": source_manifest,
    "current_source_handoff_ref": source_handoff,
    "recovered_prior_manifest_ref": pin(HERE / "manifest.prior-seal.json"),
    "recovered_prior_handoff_ref": pin(HERE / "handoff.prior-seal.json"),
    "failure_origin_refs": [pin(SOURCE / "failure-origin-01.json"), pin(SOURCE / "failure-origin-02.json")],
    "formal_case_accepted_delta": 0, "main_changed": False})
print(json.dumps({"status": "STOPPED_SOURCE_ONLY", "members": len(members),
                  "manifest": manifest, "handoff": handoff}, ensure_ascii=False))
