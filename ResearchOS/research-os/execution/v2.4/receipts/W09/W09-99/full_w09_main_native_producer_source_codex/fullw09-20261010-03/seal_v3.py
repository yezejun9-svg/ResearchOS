"""Seal compatible Source-only HDF/MF; no producer or authority action."""
import ast
import hashlib
import json
from pathlib import Path

N = Path(__file__).resolve().parent
OLD = N.parent / "fullw09-20261010-02"
REVIEW = N.parent.parent / "full_w09_main_native_producer_independent_source_review_codex" / "review-fullw09-20261010-02"
AUTHOR = "codex:/root/w09_formal_profile_source_impl"
SESSION = "01a12011-7d41-7991-a01c-de2d71701ff7"

def ref(path):
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def put(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

review = ref(REVIEW / "source-review-decision.json")
assert review["sha256"] == "ae1597399ee43d91eaeb96a70ecb5aeeeb0bbb1a758cfc2db17d65fc3a0e26dc"
rebase = json.loads((N / "source-v3-rebase.json").read_bytes())
choice = json.loads((N / "source.choice.json").read_bytes())
contract = json.loads((N / "root-calling-contract.json").read_bytes())
guard = json.loads((N / "source-guard.closed.json").read_bytes())
old_hdf = json.loads((OLD / "HDF.json").read_bytes())
assert choice["actor_id"] == contract["author"] == AUTHOR
assert contract["status"] == "SOURCE_ONLY_NO_EXECUTION_GRANT"
assert guard["cleanup"]["closed"] and guard["cleanup"]["retained_handles_count"] == 0
assert guard["Canon_handles"] == guard["Native_calls"] == guard["Go_calls"] == guard["prepare_run_calls"] == 0
assert old_hdf["new_finite_controls"] == {"pass": 20, "fail": 0}

for name in ("full_w09_runtime.source.py", "runtime-overrides.source.py", "full_w09_launcher.source.py",
             "prepare_full_w09.source.py", "run_full_w09.source.py"):
    ast.parse((N / name).read_text(encoding="utf-8"), filename=name)
    assert (N / name).read_bytes() == (OLD / name).read_bytes()
assert ref(N / "full_w09_runtime.source.py")["sha256"] == "1709bc96848fb52fe4ddde8591fe063576515aaabdc63d35630b1023a82ccc08"
for key, name in contract["source_file_bindings"].items():
    assert contract["bound_source_refs"][key] == ref(N / name)
assert choice["common"]["compiler_blueprint_ref"] == ref(N / "compiler-source-blueprint.json")
for key, item in choice["selectors"].items():
    assert item["run_id"] == rebase["new_run_ids"][key]
    for root in ("receipt_root", "scratch_root", "output_root"):
        assert not Path(item[root]).exists()

members = [ref(path) for path in sorted(N.iterdir(), key=lambda p: p.name.casefold())
           if path.is_file() and path.name not in {"HDF.json", "MF.json"}]
assert len({m["path"] for m in members}) == len(members)
put(N / "MF.json", {"schema": "researchos.w09-three-selector-producer-source-manifest.v1", "members": members})

hdf = {
    "schema": "researchos.w09-three-selector-producer-source-handoff.v1",
    "actor_id": AUTHOR,
    "source_thread_id": SESSION,
    "status": "SOURCE_READY_PENDING_INDEPENDENT_REVIEW",
    "manifest_ref": ref(N / "MF.json"),
    "calling_contract_ref": ref(N / "root-calling-contract.json"),
    "source_choice_ref": ref(N / "source.choice.json"),
    "runtime_ref": ref(N / "full_w09_runtime.source.py"),
    "overrides_ref": ref(N / "runtime-overrides.source.py"),
    "launcher_ref": ref(N / "full_w09_launcher.source.py"),
    "prepare_caller_ref": ref(N / "prepare_full_w09.source.py"),
    "producer_caller_ref": ref(N / "run_full_w09.source.py"),
    "compiler_blueprint_ref": ref(N / "compiler-source-blueprint.json"),
    "source_v3_rebase_ref": ref(N / "source-v3-rebase.json"),
    "source_guard_ref": ref(N / "source-guard.closed.json"),
    "prior_source_hdf_ref": ref(OLD / "HDF.json"),
    "prior_source_mf_ref": ref(OLD / "MF.json"),
    "prior_independent_review_ref": review,
    "reused_prior_author_controls_69": ref(OLD.parent / "fullw09-20261009-01" / "source-controls.json"),
    "reused_prior_independent_controls_112": ref(REVIEW.parent / "review-fullw09-20261009-01" / "independent-source-controls.json"),
    "reused_v2_peer_controls_20": ref(OLD / "peer-audit-controls.json"),
    "new_finite_controls": {"pass": 20, "fail": 0, "reused_not_rerun": True},
    "selectors": {key: {"run_id": item["run_id"], "receipt_root": item["receipt_root"],
                        "scratch_root": item["scratch_root"], "output_root": item["output_root"]}
                  for key, item in choice["selectors"].items()},
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
    "next_gate": "Root captures this author's plaintext full HDF path/SHA256/bytes peer delivery; independent non-author Source review; fresh Root selector scope/lease/Canon/request before execution.",
}
put(N / "HDF.json", hdf)
print(json.dumps({"HDF": ref(N / "HDF.json"), "MF": ref(N / "MF.json"),
                  "contract": ref(N / "root-calling-contract.json"), "members": len(members)}, ensure_ascii=False))
