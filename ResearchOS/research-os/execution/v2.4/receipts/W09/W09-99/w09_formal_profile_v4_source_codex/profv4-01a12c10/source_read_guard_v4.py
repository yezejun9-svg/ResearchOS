"""Finite, read-only Source input guard with explicit handle closure."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

P = Path(__file__).resolve().parent
MAX_REFS = 96
SHA = re.compile(r"[0-9a-f]{64}")
opened = 0
closed = 0
active = 0


def read(path):
    global opened, closed, active
    opened += 1
    active += 1
    try:
        with Path(path).open("rb") as stream:
            return stream.read()
    finally:
        active -= 1
        closed += 1


def canonical(ref):
    assert type(ref) is dict and set(ref) == {"path", "sha256", "bytes"}
    assert type(ref["path"]) is str and Path(ref["path"]).is_absolute()
    assert type(ref["sha256"]) is str and SHA.fullmatch(ref["sha256"])
    assert type(ref["bytes"]) is int and ref["bytes"] >= 0
    return str(Path(ref["path"]).resolve(strict=True))


guard = json.loads(read(P / "source-guard.json"))
assert guard["schema"] == "researchos.w09-formal-profile-v4-sourceguard.v1"
assert guard["closed0"] is True
assert set(guard["refs"]) == {"v3_handoff", "v3_manifest", "independent_findings"}
refs = {}


def add(ref):
    key = canonical(ref)
    assert key not in refs or refs[key] == ref, ("CONFLICTING_SOURCE_PIN", key)
    refs[key] = ref
    assert len(refs) <= MAX_REFS


for ref in guard["refs"].values():
    add(ref)
v3_hdf = json.loads(read(guard["refs"]["v3_handoff"]["path"]))
v3_mf = json.loads(read(guard["refs"]["v3_manifest"]["path"]))
assert v3_hdf["manifest_ref"] == guard["refs"]["v3_manifest"]
for ref in v3_mf["members"]:
    add(ref)
for ref in v3_mf["target_after"].values():
    add(ref)

review_dir = Path(guard["refs"]["independent_findings"]["path"]).parent
review_hdf = {"path": str(review_dir / "HDF.json"),
              "sha256": "a619f6ba5291550d3194223939d885f4767e6eb4d76cf4787feb43c3b0dcc33b",
              "bytes": 2126}
review_mf = {"path": str(review_dir / "MF.json"),
             "sha256": "f5631a5baa324a8859011e041e3da839e3688252981c8137362922cd897e7ca7",
             "bytes": 4776}
review_decision = {"path": str(review_dir / "source-decision.json"),
                   "sha256": "12cd0023799dc7abaf7298ffef468d6870daddc3a756422c7eb008f4c729a321",
                   "bytes": 2903}
counterexample = {"path": str(review_dir / "native-terminal-counterexample.json"),
                  "sha256": "42f0b4fca7852be62f87454e4a62cf69a34b32541958d1645e583f7ead9a867c",
                  "bytes": 2283}
for ref in (review_hdf, review_mf, review_decision, counterexample):
    add(ref)
review_manifest = json.loads(read(review_mf["path"]))
for ref in review_manifest["members"]:
    add(ref)

native_review_dir = (P.parents[6] / "execution/v2.4/receipts/W09/W09-99/"
                     "main_c19_native_actual_independent_review_codex/review-1a12035-v2")
native_review_hdf = {"path": str(native_review_dir / "HDF.json"),
                     "sha256": "49dd4ae646af95ecc38004f9650245e7e6ed9e04aa9fe8711b5fd945dd840270",
                     "bytes": 6428}
native_review_mf = {"path": str(native_review_dir / "MF.json"),
                    "sha256": "eba83d3e4d1ade81a0566fed856e9cb3df3b1fa488f43868cf67f53b0254940a",
                    "bytes": 6343}
for ref in (native_review_hdf, native_review_mf):
    add(ref)

prior_counterexample = {"path": str(P.parents[6] / "execution/v2.4/receipts/W09/W09-99/"
                                     "w09_formal_profile_v2_independent_review_codex/"
                                     "profv2r-01a12b31/synthetic-counterexamples.json"),
                        "sha256": "4c82c2faa0779fdedbeb6c5cd8a4f14e43896089d189237230c0e3efd2c4e99b",
                        "bytes": 5259}
protocol_dir = (P.parents[6] / "execution/v2.4/receipts/W09/W09-99/"
                "checkpoint_r369_native_source_root/cp369-c19-20261009")
protocol_raw = {"path": str(protocol_dir / "nonformal-registration-delivery.original.root.jsonl"),
                "sha256": "219312642745d2ee5cc919a410faa2e59e560aba41b0dfef399e792aeeb7f900",
                "bytes": 24304}
protocol_binding = {"path": str(protocol_dir / "nonformal-registration-delivery.binding.root.json"),
                    "sha256": "a9efe15f1f68bfbab03f0426c6d9e7a1bb30536091eeeb4e0683bf703d6df56e",
                    "bytes": 1733}
fixed_index = {"path": str(P.parents[6] / "execution/v2.4/formal_case_index.py"),
               "sha256": "970ab391f2dd10a4f5e2713355a4a68757814994ef87b9aa92b9e555c12f1205",
               "bytes": 66854}
for ref in (prior_counterexample, protocol_raw, protocol_binding, fixed_index):
    add(ref)

for name in ("formal_case_index.before.py", "formal_case_index.after.py",
             "formal_profile_w09.after.py", "source_controls_v4.py", "source-guard.json"):
    path = P / name
    raw = read(path)
    add({"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})

checked = []
for key, ref in sorted(refs.items()):
    raw = read(key)
    assert len(raw) == ref["bytes"] and hashlib.sha256(raw).hexdigest() == ref["sha256"], key
    checked.append(ref)
assert active == 0 and opened == closed
print(json.dumps({"schema": "researchos.w09-v4-source-read-guard.v1",
                  "verification": "PASSED", "closed0": True, "refs": checked,
                  "refs_checked": len(checked), "opened": opened, "closed": closed,
                  "retained_handles_count": active, "errors": [],
                  "actual_native_execution": False, "formal_acceptance": False},
                 ensure_ascii=False, indent=2))
