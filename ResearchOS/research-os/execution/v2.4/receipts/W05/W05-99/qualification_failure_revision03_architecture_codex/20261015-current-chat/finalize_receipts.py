"""Freeze this design-only evidence directory; never touch source or actual roots."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent


def ref(path):
    data = path.read_bytes()
    return {"path": path.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main():
    target = ROOT / "FINAL-manifest.json"
    if target.exists():
        raise SystemExit("manifest already frozen")
    entries = [ref(p) for p in sorted(ROOT.iterdir()) if p.is_file()]
    result = {
        "schema": "researchos.qualification-failure-revision03-architecture-manifest.v1",
        "mode": "DESIGN_AND_READONLY_PROOF_ANALYSIS_ONLY",
        "scope_sha256": "83018d17124b8c15c8f66c96fd6ae04e64baf1cb5d204de39f68abc30f2c6ae3",
        "inputs": "frozen-inputs.json",
        "status": "revision03-status.json",
        "diagnostics": "diagnostics.jsonl",
        "entries": entries,
        "entry_count": len(entries),
        "excluded": ["FINAL-manifest.json"],
        "write_scope": str(ROOT),
        "source_writes": 0,
        "actual_actions": 0,
        "tests_executed": 0,
        "formal_increment": 0,
        "self_acceptance": False,
    }
    with target.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    for entry in entries:
        assert ref(ROOT / entry["path"]) == entry
    print(json.dumps({"manifest": ref(target), "entry_count": len(entries), "verified": True}))


if __name__ == "__main__":
    main()
