"""Seal owned source-only files; no candidate import or product call."""
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]


def pin(path):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def write(name, data):
    (HERE / name).write_bytes((json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode())


excluded = {"manifest.json", "handoff.json"}
members = [pin(p) for p in sorted(HERE.rglob("*")) if p.is_file() and p.name not in excluded]
manifest = {"schema": "researchos.source-preparation-manifest.v1", "stage": "SOURCE_PREPARATION_ONLY",
            "namespace": str(HERE.relative_to(ROOT)).replace("\\", "/"),
            "members": members, "member_count": len(members), "formal_case_accepted_delta": 0}
write("manifest.json", manifest)
audit = json.loads((HERE / "static_audit.json").read_bytes())
handoff = {"schema": "researchos.w09-v4-source-preparation-handoff.v1", "status": "STOPPED_SOURCE_ONLY",
           "namespace": manifest["namespace"], "manifest_ref": pin(HERE / "manifest.json"),
           "report_ref": pin(HERE / "report.v4.json"), "evidence_map_ref": pin(HERE / "evidence_map.v4.json"),
           "static_audit_ref": pin(HERE / "static_audit.json"),
           "failure_origin_refs": [pin(HERE / "failure-origin-01.json"), pin(HERE / "failure-origin-02.json")],
           "candidate_refs": [row["candidate"] for row in audit["files"]],
           "formal_case_accepted_delta": 0, "main_changed": False,
           "next": "independent f08 source review before Root integration"}
write("handoff.json", handoff)
print(json.dumps({"status": handoff["status"], "members": len(members),
                  "manifest": handoff["manifest_ref"], "handoff": pin(HERE / "handoff.json")}, ensure_ascii=False))
