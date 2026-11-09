"""Exclusive seal for two distinct metadata overwrite operations."""
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]


def pin(path):
    data = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def write_once(name, value):
    with (HERE / name).open("xb") as stream:
        stream.write((json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode())
    return pin(HERE / name)


first = json.loads((HERE / "failure-origin-03.json").read_bytes())
second = json.loads((HERE / "failure-origin-04.json").read_bytes())
assert first["operation_id"] == "642053" and second["operation_id"] == "0a4bda"
assert first["actual_outer_exit"] == first["actual_python_exit"] == 0
assert second["actual_outer_exit"] == second["actual_python_exit"] == 0
members = [pin(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.name not in
           {"manifest.json", "handoff.json"}]
manifest = write_once("manifest.json", {"schema": "researchos.failure-origin-manifest.v1",
    "namespace": str(HERE.relative_to(ROOT)).replace("\\", "/"),
    "members": members, "member_count": len(members), "distinct_failure_origins": 2})
handoff = write_once("handoff.json", {"schema": "researchos.metadata-overwrite-origins-handoff.v1",
    "status": "SEALED", "manifest_ref": manifest,
    "failure_origin_refs": [pin(HERE / "failure-origin-03.json"), pin(HERE / "failure-origin-04.json")],
    "failure_count_delta": 2,
    "note": "Count the two distinct non-exclusive seal executions once each; do not count individual report/manifest/handoff files.",
    "earliest_overwritten_seal": "72ad3a.../dc4faf... original bytes not recovered; prior f72e09.../a26de8... bytes recovered in separate finalization annex."})
print(json.dumps({"status": "SEALED", "manifest": manifest, "handoff": handoff}, ensure_ascii=False))
