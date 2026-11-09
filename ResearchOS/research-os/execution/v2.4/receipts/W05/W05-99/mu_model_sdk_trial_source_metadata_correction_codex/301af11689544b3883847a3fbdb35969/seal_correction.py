import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
root = Path(__file__).resolve().parent

def pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def put(path, value):
    with path.open("xb") as out:
        out.write((json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    return pin(path)

correction = json.loads((root / "correction.json").read_text(encoding="utf-8"))
actual = pin(Path(correction["original_report"]["path"]))
assert actual["sha256"] == correction["original_report"]["sha256"] and actual["bytes"] == correction["original_report"]["bytes"]
manifest = put(root / "manifest.json", {"schema": "researchos.mu-sdk-trial.metadata-correction-manifest.v1", "members": [pin(root / "correction.json"), pin(root / "seal_correction.py"), pin(root / "failure-origin-005.json")], "supersedes_original_bytes": False})
handoff = put(root / "handoff.json", {"schema": "researchos.mu-sdk-trial.metadata-correction-handoff.v1", "manifest_ref": manifest, "correction_ref": pin(root / "correction.json"), "original_report_ref": correction["original_report"], "source_and_formal_delta": 0})
print(json.dumps({"manifest": manifest, "handoff": handoff}, ensure_ascii=False))
