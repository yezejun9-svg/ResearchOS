"""Exclusive-create Source v2 seal. This script never adopts fixed targets."""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
R = P.parents[6]


def pin(path):
    raw = path.read_bytes()
    return {"path": str(path.resolve(strict=True)), "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw)}


def create(name, raw):
    with (P / name).open("xb") as stream:
        stream.write(raw)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


sourceguard = json.loads((P / "source-guard.json").read_bytes())
assert sourceguard["schema"] == "researchos.w09-formal-profile-v2-sourceguard.v1"
assert sourceguard["closed0"] is True
assert set(sourceguard["refs"]) == {"v1_handoff", "v1_manifest", "independent_findings"}
for ref in sourceguard["refs"].values():
    assert pin(Path(ref["path"])) == ref
v1_manifest = json.loads(Path(sourceguard["refs"]["v1_manifest"]["path"]).read_bytes())
v1_handoff = json.loads(Path(sourceguard["refs"]["v1_handoff"]["path"]).read_bytes())
assert v1_handoff["manifest_ref"] == sourceguard["refs"]["v1_manifest"]
for name in ("formal_case_index.py", "formal_profile_w09.py"):
    assert pin(Path(v1_manifest["proposed_after"]["execution/v2.4/" + name]["path"])) == v1_manifest["proposed_after"]["execution/v2.4/" + name]

before = P / "formal_case_index.before.py"
after = P / "formal_case_index.after.py"
profile = P / "formal_profile_w09.after.py"
assert before.read_bytes() == (R / "execution/v2.4/formal_case_index.py").read_bytes()
assert not (R / "execution/v2.4/formal_profile_w09.py").exists()
assert before.read_bytes()[:51719] == after.read_bytes()[:51719]
assert hashlib.sha256(after.read_bytes()[:51719]).hexdigest() == "92341c7d3a49a4d2ee9e3519ff2897e1950c33aff2876124c11e556b78e134e1"
ast.parse(after.read_bytes(), filename=str(after))
ast.parse(profile.read_bytes(), filename=str(profile))
controls = json.loads((P / "source-controls.json").read_bytes())
assert controls["scope"] == "SYNTHETIC_NONAUTHORITATIVE" and len(controls["checks"]) == 26
assert controls["actual_native_runs"] == controls["actual_dispatcher_runs"] == 0

left = before.read_text(encoding="utf-8").splitlines(keepends=True)
right = after.read_text(encoding="utf-8").splitlines(keepends=True)
create("formal_case_index.forward.diff", "".join(difflib.unified_diff(
    left, right, fromfile="formal_case_index.before.py", tofile="formal_case_index.after.py")).encode("utf-8"))
create("formal_case_index.inverse.diff", "".join(difflib.unified_diff(
    right, left, fromfile="formal_case_index.after.py", tofile="formal_case_index.before.py")).encode("utf-8"))

members = ["formal_case_index.before.py", "formal_case_index.after.py", "formal_profile_w09.after.py",
           "formal_case_index.forward.diff", "formal_case_index.inverse.diff", "source_controls_v2.py",
           "source-controls.json", "source-guard.json", "source-contract.json", "fix-map.json",
           "REPORT.md", "make_packet_v2.py"]
manifest = {
    "schema": "researchos.w09-formal-profile-v2-source-manifest.v1",
    "status": "SOURCE_ONLY_PENDING_INDEPENDENT_REVIEW_NOT_ADOPTED",
    "source_guard_ref": pin(P / "source-guard.json"),
    "review_findings_ref": sourceguard["refs"]["independent_findings"],
    "target_before": {"execution/v2.4/formal_case_index.py": pin(before),
                      "execution/v2.4/formal_profile_w09.py": {"state": "ABSENT"}},
    "target_after": {"execution/v2.4/formal_case_index.py": pin(after),
                     "execution/v2.4/formal_profile_w09.py": pin(profile)},
    "complete_byte_inverse": pin(before),
    "members": [pin(P / name) for name in members],
    "w07_prefix": {"bytes": 51719,
                   "sha256": hashlib.sha256(after.read_bytes()[:51719]).hexdigest()},
    "source_controls": {"scope": "SYNTHETIC_NONAUTHORITATIVE", "check_count": 26,
                        "exit": 0, "formal_acceptance": False},
    "source_proof_guards_closed0": True,
    "actual_native_runs": 0,
    "canonical_writes": False,
    "formal_acceptance": False,
}
create("MF.json", json_bytes(manifest))
handoff = {
    "schema": "researchos.w09-formal-profile-v2-source-handoff.v1",
    "status": "SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW_NOT_ADOPTED",
    "manifest_ref": pin(P / "MF.json"),
    "report_ref": pin(P / "REPORT.md"),
    "contract_ref": pin(P / "source-contract.json"),
    "fix_map_ref": pin(P / "fix-map.json"),
    "source_guard_ref": pin(P / "source-guard.json"),
    "after_refs": [pin(after), pin(profile)],
    "original_index_ref": pin(before),
    "only_new_source_namespace_written": True,
    "root_adoption_required": True,
    "actual_native_runs": 0,
    "formal_acceptance": False,
    "STOP": True,
    "FINAL": True,
}
create("HDF.json", json_bytes(handoff))
print(json.dumps({"status": "SOURCE_V2_SEALED_NOT_ADOPTED",
                  "MF": pin(P / "MF.json"), "HDF": pin(P / "HDF.json")}, ensure_ascii=False))
