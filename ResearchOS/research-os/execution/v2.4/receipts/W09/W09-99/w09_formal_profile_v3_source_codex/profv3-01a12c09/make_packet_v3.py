"""Exclusive-create v3 Source seal, without adopting fixed targets."""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys

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


guard = json.loads((P / "source-guard.json").read_bytes())
assert guard["schema"] == "researchos.w09-formal-profile-v3-sourceguard.v1"
assert guard["closed0"] is True
assert set(guard["refs"]) == {"v2_handoff", "v2_manifest", "independent_findings"}
for ref in guard["refs"].values():
    assert pin(Path(ref["path"])) == ref
v2_handoff = json.loads(Path(guard["refs"]["v2_handoff"]["path"]).read_bytes())
v2_manifest = json.loads(Path(guard["refs"]["v2_manifest"]["path"]).read_bytes())
assert v2_handoff["manifest_ref"] == guard["refs"]["v2_manifest"]
for relative in ("execution/v2.4/formal_case_index.py", "execution/v2.4/formal_profile_w09.py"):
    assert pin(Path(v2_manifest["target_after"][relative]["path"])) == v2_manifest["target_after"][relative]
review_dir = Path(guard["refs"]["independent_findings"]["path"]).parent
review_hdf = {"path": str(review_dir / "HDF.json"),
              "sha256": "04b6b1de530b3aaaa41516a0c1de4be125412ec2180f6e78f198a75a7d5190e4",
              "bytes": 1811}
review_mf = {"path": str(review_dir / "MF.json"),
             "sha256": "83395a9eec04ef1b8a5e8950e211e5433ff29406226b076ac66e1c0b9bfb2066",
             "bytes": 3477}
assert pin(Path(review_hdf["path"])) == review_hdf
assert pin(Path(review_mf["path"])) == review_mf
findings = json.loads(Path(guard["refs"]["independent_findings"]["path"]).read_bytes())
assert findings["decision"] == "REQUEST_CHANGES"
assert {item["id"] for item in findings["findings"]} == {"F2", "F3", "F5"}

before = P / "formal_case_index.before.py"
after = P / "formal_case_index.after.py"
profile = P / "formal_profile_w09.after.py"
before_raw, after_raw, profile_raw = before.read_bytes(), after.read_bytes(), profile.read_bytes()
assert before_raw == (R / "execution/v2.4/formal_case_index.py").read_bytes()
assert not (R / "execution/v2.4/formal_profile_w09.py").exists()
assert before_raw[:51719] == after_raw[:51719]
assert hashlib.sha256(after_raw[:51719]).hexdigest() == "92341c7d3a49a4d2ee9e3519ff2897e1950c33aff2876124c11e556b78e134e1"
assert before_raw.count(b'if __name__ == "__main__":') == after_raw.count(b'if __name__ == "__main__":') == 1
ast.parse(after_raw, filename=str(after))
ast.parse(profile_raw, filename=str(profile))

completed = subprocess.run([sys.executable, "-I", "-S", "-B", "-X", "utf8", str(P / "source_controls_v3.py")],
                           cwd=R, capture_output=True, text=True, encoding="utf-8", check=False)
assert completed.returncode == 0, completed.stderr
controls = json.loads(completed.stdout)
assert controls["scope"] == "SYNTHETIC_NONAUTHORITATIVE"
assert controls["status"] == "PASS_SOURCE_ONLY" and len(controls["checks"]) == 37
assert len(controls["checks"]) == len(set(controls["checks"]))
assert controls["actual_native_runs"] == controls["actual_dispatcher_runs"] == 0
assert controls["formal_acceptance"] is False

left = before_raw.decode("utf-8").splitlines(keepends=True)
right = after_raw.decode("utf-8").splitlines(keepends=True)
forward = "".join(difflib.unified_diff(left, right,
                   fromfile="formal_case_index.before.py", tofile="formal_case_index.after.py")).encode("utf-8")
inverse = "".join(difflib.unified_diff(right, left,
                   fromfile="formal_case_index.after.py", tofile="formal_case_index.before.py")).encode("utf-8")
create("source-controls.json", json_bytes(controls))
create("formal_case_index.forward.diff", forward)
create("formal_case_index.inverse.diff", inverse)

member_names = [
    "formal_case_index.before.py", "formal_case_index.after.py", "formal_profile_w09.after.py",
    "formal_case_index.forward.diff", "formal_case_index.inverse.diff",
    "source_controls_v3.py", "source-controls.json", "source-guard.json",
    "source-contract.json", "fix-map.json", "REPORT.md",
    "original-tool-failures.md", "original-tool-failures-followup.md",
    "inspect_protocol_sample.py", "transform_f5_v3.py", "transform_controls_v3.py",
    "restore_index_prefix_v3.py", "fix_ref_shapes_v3.py", "fix_plaintext_shape_v3.py",
    "make_packet_v3.py",
]
manifest = {
    "schema": "researchos.w09-formal-profile-v3-source-manifest.v1",
    "status": "SOURCE_ONLY_PENDING_INDEPENDENT_REVIEW_NOT_ADOPTED",
    "source_guard_ref": pin(P / "source-guard.json"),
    "v2_independent_review": {"HDF": review_hdf, "MF": review_mf,
                              "findings": guard["refs"]["independent_findings"]},
    "target_before": {"execution/v2.4/formal_case_index.py": pin(before),
                      "execution/v2.4/formal_profile_w09.py": {"state": "ABSENT"}},
    "target_after": {"execution/v2.4/formal_case_index.py": pin(after),
                     "execution/v2.4/formal_profile_w09.py": pin(profile)},
    "complete_byte_inverse": pin(before),
    "members": [pin(P / name) for name in member_names],
    "w07_prefix": {"bytes": 51719, "sha256": hashlib.sha256(after_raw[:51719]).hexdigest()},
    "source_controls": {"scope": "SYNTHETIC_NONAUTHORITATIVE", "check_count": len(controls["checks"]),
                        "exit": completed.returncode, "formal_acceptance": False},
    "source_proof_guards_closed0": True,
    "source_packet_native_executions": 0,
    "canonical_writes": False,
    "formal_acceptance": False,
}
create("MF.json", json_bytes(manifest))
handoff = {
    "schema": "researchos.w09-formal-profile-v3-source-handoff.v1",
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
    "source_packet_native_executions": 0,
    "formal_acceptance": False,
    "STOP": True,
    "FINAL": True,
}
create("HDF.json", json_bytes(handoff))
print(json.dumps({"status": "SOURCE_V3_SEALED_NOT_ADOPTED",
                  "MF": pin(P / "MF.json"), "HDF": pin(P / "HDF.json"),
                  "checks": len(controls["checks"])}, ensure_ascii=False))
