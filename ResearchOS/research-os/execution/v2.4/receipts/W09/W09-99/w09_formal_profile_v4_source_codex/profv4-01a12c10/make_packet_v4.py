"""Exclusive-create v4 Source seal. This never adopts fixed targets."""
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


guard_ref = pin(P / "source-guard.json")
guard = json.loads((P / "source-guard.json").read_bytes())
assert guard["schema"] == "researchos.w09-formal-profile-v4-sourceguard.v1"
assert guard["closed0"] is True
assert set(guard["refs"]) == {"v3_handoff", "v3_manifest", "independent_findings"}
for ref in guard["refs"].values():
    assert pin(Path(ref["path"])) == ref
prior_hdf = json.loads(Path(guard["refs"]["v3_handoff"]["path"]).read_bytes())
prior_mf = json.loads(Path(guard["refs"]["v3_manifest"]["path"]).read_bytes())
assert prior_hdf["manifest_ref"] == guard["refs"]["v3_manifest"]
review = json.loads(Path(guard["refs"]["independent_findings"]["path"]).read_bytes())
assert review["decision"] == "REQUEST_CHANGES"
assert [finding["id"] for finding in review["findings"]] == ["F2-terminal-causality"]
counterexample_ref = review["findings"][0]["counterexample_ref"]
assert pin(Path(counterexample_ref["path"])) == counterexample_ref

before = P / "formal_case_index.before.py"
after = P / "formal_case_index.after.py"
previous = P / "formal_profile_w09.previous_proposal.py"
profile = P / "formal_profile_w09.after.py"
before_raw, after_raw = before.read_bytes(), after.read_bytes()
previous_raw, profile_raw = previous.read_bytes(), profile.read_bytes()
assert before_raw == (R / "execution/v2.4/formal_case_index.py").read_bytes()
assert not (R / "execution/v2.4/formal_profile_w09.py").exists()
prior_index_ref = prior_mf["target_after"]["execution/v2.4/formal_case_index.py"]
assert pin(Path(prior_index_ref["path"])) == prior_index_ref
assert {key: pin(after)[key] for key in ("sha256", "bytes")} == {
    key: prior_index_ref[key] for key in ("sha256", "bytes")}
assert pin(previous) == {"path": str(previous.resolve(strict=True)),
                         "sha256": prior_mf["target_after"]["execution/v2.4/formal_profile_w09.py"]["sha256"],
                         "bytes": prior_mf["target_after"]["execution/v2.4/formal_profile_w09.py"]["bytes"]}
assert before_raw[:51719] == after_raw[:51719]
assert hashlib.sha256(after_raw[:51719]).hexdigest() == "92341c7d3a49a4d2ee9e3519ff2897e1950c33aff2876124c11e556b78e134e1"
assert before_raw.count(b'if __name__ == "__main__":') == after_raw.count(b'if __name__ == "__main__":') == 1
ast.parse(after_raw, filename=str(after))
ast.parse(profile_raw, filename=str(profile))

start_marker = b"def _native_event_interval(api, raw, report, selected, label):\n"
end_marker = b"def _native(api, reader, row, closure, router, pinned, producer_sources):\n"
assert previous_raw.count(start_marker) == profile_raw.count(start_marker) == 1
assert previous_raw.count(end_marker) == profile_raw.count(end_marker) == 1
old_start, old_end = previous_raw.index(start_marker), previous_raw.index(end_marker)
new_start, new_end = profile_raw.index(start_marker), profile_raw.index(end_marker)
assert previous_raw[:old_start] == profile_raw[:new_start]
assert previous_raw[old_end:] == profile_raw[new_end:]

def run_source(name):
    completed = subprocess.run([sys.executable, "-I", "-S", "-B", "-X", "utf8", str(P / name)],
                               cwd=R, capture_output=True, text=True, encoding="utf-8", check=False)
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout), completed.returncode

read_guard, guard_exit = run_source("source_read_guard_v4.py")
assert read_guard["verification"] == "PASSED" and read_guard["closed0"] is True
assert read_guard["retained_handles_count"] == 0 and read_guard["opened"] == read_guard["closed"]
assert type(read_guard["refs_checked"]) is int and 30 <= read_guard["refs_checked"] <= 96
assert read_guard["errors"] == [] and read_guard["formal_acceptance"] is False
controls, controls_exit = run_source("source_controls_v4.py")
assert controls["schema"] == "researchos.w09-formal-profile-v4-controls.v1"
assert controls["scope"] == "SYNTHETIC_NONAUTHORITATIVE"
assert controls["status"] == "PASS_SOURCE_ONLY" and len(controls["checks"]) == 46
assert len(controls["checks"]) == len(set(controls["checks"]))
assert controls["actual_native_runs"] == controls["actual_dispatcher_runs"] == 0
assert controls["formal_acceptance"] is False

def diff(left, right, left_name, right_name):
    return "".join(difflib.unified_diff(
        left.decode("utf-8").splitlines(keepends=True),
        right.decode("utf-8").splitlines(keepends=True),
        fromfile=left_name, tofile=right_name)).encode("utf-8")

create("source-read-guard.json", json_bytes(read_guard))
create("source-controls.json", json_bytes(controls))
create("formal_case_index.forward.diff", diff(before_raw, after_raw,
       "formal_case_index.before.py", "formal_case_index.after.py"))
create("formal_case_index.inverse.diff", diff(after_raw, before_raw,
       "formal_case_index.after.py", "formal_case_index.before.py"))
create("formal_profile_w09.forward.diff", diff(previous_raw, profile_raw,
       "formal_profile_w09.previous_proposal.py", "formal_profile_w09.after.py"))
create("formal_profile_w09.inverse.diff", diff(profile_raw, previous_raw,
       "formal_profile_w09.after.py", "formal_profile_w09.previous_proposal.py"))

member_names = [
    "formal_case_index.before.py", "formal_case_index.after.py", "formal_profile_w09.previous_proposal.py",
    "formal_profile_w09.after.py", "formal_case_index.forward.diff", "formal_case_index.inverse.diff",
    "formal_profile_w09.forward.diff", "formal_profile_w09.inverse.diff",
    "source_controls_v4.py", "source-controls.json", "source_read_guard_v4.py", "source-read-guard.json",
    "source-guard.json", "source-contract.json", "fix-map.json", "REPORT.md",
    "original-failure-ledger.json", "original-tool-failures-v4.md",
    "apply_v4_source.py", "add_v4_controls.py", "fix_sealer_ref_v4.py", "make_packet_v4.py",
]
native_review_dir = (R / "execution/v2.4/receipts/W09/W09-99/"
                     "main_c19_native_actual_independent_review_codex/review-1a12035-v2")
manifest = {
    "schema": "researchos.w09-formal-profile-v4-source-manifest.v1",
    "status": "SOURCE_ONLY_PENDING_INDEPENDENT_REVIEW_NOT_ADOPTED",
    "source_guard_ref": guard_ref,
    "read_guard_ref": pin(P / "source-read-guard.json"),
    "v3_review_refs": {"HDF": pin(Path(guard["refs"]["independent_findings"]["path"]).parent / "HDF.json"),
                       "MF": pin(Path(guard["refs"]["independent_findings"]["path"]).parent / "MF.json"),
                       "findings": guard["refs"]["independent_findings"],
                       "counterexample": counterexample_ref},
    "native_mr2_refs": {"HDF": pin(native_review_dir / "HDF.json"),
                        "MF": pin(native_review_dir / "MF.json")},
    "target_before": {"execution/v2.4/formal_case_index.py": pin(before),
                      "execution/v2.4/formal_profile_w09.py": {"state": "ABSENT"}},
    "target_after": {"execution/v2.4/formal_case_index.py": pin(after),
                     "execution/v2.4/formal_profile_w09.py": pin(profile)},
    "complete_byte_inverse": pin(before),
    "members": [pin(P / name) for name in member_names],
    "w07_prefix": {"bytes": 51719, "sha256": hashlib.sha256(after_raw[:51719]).hexdigest()},
    "source_controls": {"scope": "SYNTHETIC_NONAUTHORITATIVE", "check_count": 46,
                        "exit": controls_exit, "formal_acceptance": False},
    "source_read_guard": {"refs_checked": read_guard["refs_checked"], "exit": guard_exit,
                          "closed0": True},
    "source_packet_native_executions": 0,
    "canonical_writes": False,
    "formal_case_accepted_delta": 0,
    "parent_accepted_delta": 0,
    "formal_acceptance": False,
}
create("MF.json", json_bytes(manifest))
handoff = {
    "schema": "researchos.w09-formal-profile-v4-source-handoff.v1",
    "status": "SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW_NOT_ADOPTED",
    "manifest_ref": pin(P / "MF.json"),
    "report_ref": pin(P / "REPORT.md"),
    "contract_ref": pin(P / "source-contract.json"),
    "fix_map_ref": pin(P / "fix-map.json"),
    "source_guard_ref": guard_ref,
    "source_read_guard_ref": pin(P / "source-read-guard.json"),
    "after_refs": [pin(after), pin(profile)],
    "original_index_ref": pin(before),
    "only_new_source_namespace_written": True,
    "root_adoption_required": True,
    "formal_case_accepted_delta": 0,
    "parent_accepted_delta": 0,
    "STOP": True,
    "FINAL": True,
}
create("HDF.json", json_bytes(handoff))
print(json.dumps({"status": "SOURCE_V4_SEALED_NOT_ADOPTED", "MF": pin(P / "MF.json"),
                  "HDF": pin(P / "HDF.json"), "checks": len(controls["checks"]),
                  "read_guard_refs": read_guard["refs_checked"]}, ensure_ascii=False))
