"""Seal the patched Source package without invoking prepare, producer, Go or Native."""
import ast
import hashlib
import json
from pathlib import Path

N = Path(__file__).resolve().parent
OLD = N.parent / "fullw09-20261009-01"
REVIEW = N.parent.parent / "full_w09_main_native_producer_independent_source_review_codex" / "review-fullw09-20261009-01"
SOURCE = (
    "full_w09_runtime.source.py", "runtime-overrides.source.py",
    "full_w09_launcher.source.py", "prepare_full_w09.source.py",
    "run_full_w09.source.py", "source.choice.json",
    "root-calling-contract.json", "compiler-source-blueprint.json",
)
AUTHOR = "codex:/root/w09_formal_profile_source_impl"
SESSION = "01a12011-7d41-7991-a01c-de2d71701ff7"

def pin(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def check(ref):
    actual = pin(Path(ref["path"]))
    assert actual == ref, (actual, ref)

def put(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

old_hdf = pin(OLD / "HDF.json")
old_mf = pin(OLD / "MF.json")
prior_review = pin(REVIEW / "source-review-decision.json")
assert old_hdf["sha256"] == "ca8c9767daa5296c129f87f285672b9f6963c9133dd7d71c9ba1454afdeed6c6"
assert old_mf["sha256"] == "5914889742cf9e2cd0bae3fabfbf3ca93ec8013f901502eba55411321c6580a8"
assert prior_review["sha256"] == "9fcf90b54c306acc7243c5e0191356fe4fa42fbcf3ad0b20e7490924afd4b115"

inverse = []
for name in SOURCE:
    old = OLD / name
    saved = N / "inverse-old" / name
    assert old.read_bytes() == saved.read_bytes(), name
    inverse.append({"name": name, "prior_ref": pin(old), "inverse_saved_ref": pin(saved), "new_ref": pin(N / name)})

rebase = json.loads((N / "source-rebase.json").read_bytes())
choice = json.loads((N / "source.choice.json").read_bytes())
contract = json.loads((N / "root-calling-contract.json").read_bytes())
controls = json.loads((N / "peer-audit-controls.json").read_bytes())
guard = json.loads((N / "source-guard.closed.json").read_bytes())
hostpairs = json.loads((N / "actual-hostpairs.binding.json").read_bytes())
assert rebase["source_author"] == choice["actor_id"] == contract["author"] == AUTHOR
assert contract["status"] == "SOURCE_ONLY_NO_EXECUTION_GRANT"
assert controls["count"] == controls["pass"] == 20 and controls["fail"] == 0
assert controls["new_author_actual_peer_delivery"] == "PENDING_REAL_ROOT_DELIVERY"
assert guard["cleanup"]["closed"] and guard["cleanup"]["retained_handles_count"] == 0
assert guard["Canon_handles"] == guard["Native_calls"] == guard["Go_calls"] == guard["prepare_run_calls"] == 0
assert len(hostpairs["captures"]) == 5
for capture in hostpairs["captures"]:
    check(capture["actual_capture_ref"])
    raw_lines = Path(capture["actual_capture_ref"]["path"]).read_bytes().splitlines(keepends=True)
    assert len(raw_lines) == 3
    assert [len(line) for line in raw_lines] == capture["source_line_bytes"]
    assert [hashlib.sha256(line).hexdigest() for line in raw_lines] == capture["original_line_sha256"]
    with Path(hostpairs["source_log"]).open("rb") as source_log:
        for offset, line in zip(capture["source_line_offsets"], raw_lines):
            source_log.seek(offset)
            assert source_log.readline() == line

for name in SOURCE[:5]:
    ast.parse((N / name).read_text(encoding="utf-8"), filename=name)

pins = contract["bound_source_refs"]
for key, basename in contract["source_file_bindings"].items():
    assert basename == Path(pins[key]["path"]).name
    assert Path(pins[key]["path"]).parent == N
    check(pins[key])
check(choice["common"]["compiler_blueprint_ref"])
assert rebase["runtime_ref"] == pin(N / "full_w09_runtime.source.py")
assert rebase["choice_ref"] == pin(N / "source.choice.json")
assert rebase["contract_ref"] == pin(N / "root-calling-contract.json")
for old_id in rebase["prior_run_ids"].values():
    assert old_id.encode("ascii") not in b"".join((N / name).read_bytes() for name in SOURCE)
for key, rec in choice["selectors"].items():
    assert rec["run_id"] == rebase["new_run_ids"][key]
    assert not Path(rec["receipt_root"]).exists()
    assert not Path(rec["scratch_root"]).exists()
    assert not Path(rec["output_root"]).exists()

inverse_report = {
    "schema": "researchos.w09-fullw09-source-v2-exact-inverse-and-pins.v1",
    "status": "PASS_SOURCE_ONLY",
    "prior_hdf_ref": old_hdf,
    "prior_mf_ref": old_mf,
    "prior_independent_decision_ref": prior_review,
    "exact_old_copy_count": len(inverse),
    "inverse_files": inverse,
    "new_contract_bound_source_refs_verified": len(pins),
    "new_runs_fresh": True,
    "future_roots_absent": True,
    "new_source_ast_parse": "PASS",
    "actual_prepare_run": False,
    "go_native_dispatcher_model_calls": 0,
    "Canon_modified": False,
}
put(N / "inverse-and-pins.json", inverse_report)

members = [pin(path) for path in sorted(N.rglob("*"), key=lambda p: str(p).casefold())
           if path.is_file() and path.name not in {"MF.json", "HDF.json"}]
assert len({m["path"] for m in members}) == len(members)
put(N / "MF.json", {"schema": "researchos.w09-three-selector-producer-source-manifest.v2", "members": members})

hdf = {
    "schema": "researchos.w09-three-selector-producer-source-handoff.v2",
    "actor_id": AUTHOR,
    "source_thread_id": SESSION,
    "status": "SOURCE_READY_PENDING_INDEPENDENT_REVIEW_AND_REAL_ROOT_DELIVERY",
    "manifest_ref": pin(N / "MF.json"),
    "calling_contract_ref": pin(N / "root-calling-contract.json"),
    "source_choice_ref": pin(N / "source.choice.json"),
    "runtime_ref": pin(N / "full_w09_runtime.source.py"),
    "overrides_ref": pin(N / "runtime-overrides.source.py"),
    "launcher_ref": pin(N / "full_w09_launcher.source.py"),
    "prepare_caller_ref": pin(N / "prepare_full_w09.source.py"),
    "producer_caller_ref": pin(N / "run_full_w09.source.py"),
    "compiler_blueprint_ref": pin(N / "compiler-source-blueprint.json"),
    "peer_audit_controls_ref": pin(N / "peer-audit-controls.json"),
    "inverse_and_pins_ref": pin(N / "inverse-and-pins.json"),
    "source_guard_ref": pin(N / "source-guard.closed.json"),
    "actual_hostpairs_binding_ref": pin(N / "actual-hostpairs.binding.json"),
    "prior_source_hdf_ref": old_hdf,
    "prior_source_mf_ref": old_mf,
    "prior_independent_decision_ref": prior_review,
    "prior_author_controls_69_preserved_not_recounted": True,
    "prior_independent_controls_112_preserved_not_recounted": True,
    "new_finite_controls": {"pass": 20, "fail": 0},
    "selectors": {key: {"run_id": rec["run_id"], "receipt_root": rec["receipt_root"],
                        "scratch_root": rec["scratch_root"], "output_root": rec["output_root"]}
                  for key, rec in choice["selectors"].items()},
    "actual_executed": False,
    "actual_Go_runs": 0,
    "actual_Native_runs": 0,
    "actual_dispatcher_runs": 0,
    "actual_SQL_runs": 0,
    "actual_model_provider_calls": 0,
    "Main_written": False,
    "Canon_written": False,
    "current_CanonicalPair_held": False,
    "formal_case_accepted_delta": 0,
    "formal_acceptance": False,
    "parent_acceptance": False,
    "execution_grant": False,
    "future_Root_scope": None,
    "future_Root_request": None,
    "future_registration": None,
    "future_ModeProof": None,
    "future_route_leases": None,
    "future_capture_index": None,
    "new_author_actual_peer_delivery": "PENDING_REAL_ROOT_DELIVERY",
    "next_gate": "Independent non-author Source review and Root capture of actual author/reviewer delivery before any fresh execution grant.",
}
put(N / "HDF.json", hdf)
print(json.dumps({"HDF": pin(N / "HDF.json"), "MF": pin(N / "MF.json"),
                  "inverse": pin(N / "inverse-and-pins.json"), "members": len(members)}, ensure_ascii=False))
