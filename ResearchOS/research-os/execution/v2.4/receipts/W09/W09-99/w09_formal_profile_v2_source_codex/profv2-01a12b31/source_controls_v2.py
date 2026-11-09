"""Synthetic negative controls for five P1 fixes. No product or formal run."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import tempfile

P = Path(__file__).resolve().parent
R = P.parents[6]
old = (P / "formal_case_index.before.py").read_bytes()
index_raw = (P / "formal_case_index.after.py").read_bytes()
profile_raw = (P / "formal_profile_w09.after.py").read_bytes()
assert old[:51719] == index_raw[:51719]
assert hashlib.sha256(old[:51719]).hexdigest() == "92341c7d3a49a4d2ee9e3519ff2897e1950c33aff2876124c11e556b78e134e1"
ast.parse(index_raw)
ast.parse(profile_raw)
index = {"__name__": "w09_v2_synthetic_index"}
exec(compile(index_raw, "formal_case_index.after.py", "exec"), index)
profile = {"__name__": "w09_v2_synthetic_profile"}
exec(compile(profile_raw, "formal_profile_w09.after.py", "exec"), profile)
api = index["_profile_api"]()
checks = ["W04_W07_PREFIX_EXACT", "TWO_AFTER_AST_PASS"]


def reject(label, function, code):
    try:
        function()
    except index["InvalidEvidence"] as exc:
        assert exc.code == code, (label, exc.code)
        checks.append(label)
    else:
        raise AssertionError(label)


# F1: only exact Python int zero is a successful Native exit.
profile["_native_zero"](api, {"exit_code": 0}, {"native_exit_code": 0}, "synthetic")
checks.append("F1_TYPED_INT_ZERO_ACCEPTED_SYNTHETIC")
for name, report, tool in (
    ("FALSE_REPORT", {"exit_code": False}, {"native_exit_code": 0}),
    ("FLOAT_REPORT", {"exit_code": 0.0}, {"native_exit_code": 0}),
    ("NULL_REPORT", {"exit_code": None}, {"native_exit_code": 0}),
    ("FALSE_TOOL", {"exit_code": 0}, {"native_exit_code": False}),
    ("FLOAT_TOOL", {"exit_code": 0}, {"native_exit_code": 0.0}),
    ("NULL_TOOL", {"exit_code": 0}, {"native_exit_code": None}),
):
    reject("F1_" + name, lambda r=report, t=tool: profile["_native_zero"](api, r, t, "synthetic"),
           "NATIVE_EXIT_TYPE")


# F2: pinned execution clocks must precede independent review.
def route_time():
    return {"native_started_at": "2026-10-01T00:00:00Z",
            "native_ended_at": "2026-10-01T00:10:00Z",
            "started_at": "2026-10-01T01:00:00Z",
            "ended_at": "2026-10-01T01:10:00Z"}


routes = {str(i): route_time() for i in range(6)}
global_runs = {k: {"ended_at": "2026-10-01T01:20:00Z"} for k in ("C19", "A06")}
profile["_review_execution_cutoff"](api, routes, global_runs, "2026-10-02T00:00:00Z", "2026-10-03T00:00:00Z")
checks.append("F2_ORDERED_CLOCKS_ACCEPTED_SYNTHETIC")
future_native = {key: dict(value) for key, value in routes.items()}
future_native["0"]["native_ended_at"] = "2026-10-20T00:00:00Z"
reject("F2_FUTURE_NATIVE_REJECTED", lambda: profile["_review_execution_cutoff"](
    api, future_native, global_runs, "2026-10-02T00:00:00Z", "2026-10-03T00:00:00Z"),
    "REVIEW_EXECUTION_CUTOFF")
future_dispatch = {key: dict(value) for key, value in routes.items()}
future_dispatch["0"]["ended_at"] = "2026-10-20T00:00:00Z"
reject("F2_FUTURE_DISPATCH_REJECTED", lambda: profile["_review_execution_cutoff"](
    api, future_dispatch, global_runs, "2026-10-02T00:00:00Z", "2026-10-03T00:00:00Z"),
    "REVIEW_EXECUTION_CUTOFF")
future_global = dict(global_runs, A06={"ended_at": "2026-10-20T00:00:00Z"})
reject("F2_FUTURE_GLOBAL_REJECTED", lambda: profile["_review_execution_cutoff"](
    api, routes, future_global, "2026-10-02T00:00:00Z", "2026-10-03T00:00:00Z"),
    "REVIEW_EXECUTION_CUTOFF")


# F3: membership, bytes and prior-hash conflicts remain visible in CAS.
with tempfile.TemporaryDirectory(prefix="researchos-w09-v2-owned-") as temp:
    root = Path(temp)
    relative = "execution/receipts/W09/retrieval/run-synthetic/owned"
    folder = root / relative / "TestW09Synthetic"
    folder.mkdir(parents=True)
    first = folder / "00000001-assertion.raw"
    second = folder / "00000002-http.raw"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    def claim(path):
        raw = path.read_bytes()
        return {"path": path.relative_to(root).as_posix(),
                "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    claims = [claim(first), claim(second)]
    reader = index["Reader"](root)
    inventory = index["_owned_inventory"](reader, relative, claims)
    snapshot = {"files": {str(path): value for path, value in reader.read_hashes.items()},
                "inventories": [inventory]}
    assert index["recheck_inputs"](snapshot)["status"] == "PASS"
    checks.append("F3_COMPLETE_INVENTORY_SYNTHETIC")
    extra = folder / "00000003-added.raw"
    extra.write_bytes(b"added")
    assert index["recheck_inputs"](snapshot)["status"] == "INVALID"
    checks.append("F3_ADDED_RAW_REJECTED")
    extra.unlink()
    second.write_bytes(b"changed")
    assert index["recheck_inputs"](snapshot)["status"] == "INVALID"
    checks.append("F3_CHANGED_RAW_REJECTED")
    second.write_bytes(b"second")
    second.unlink()
    assert index["recheck_inputs"](snapshot)["status"] == "INVALID"
    checks.append("F3_DELETED_RAW_REJECTED")
    second.write_bytes(b"second")
    conflicted = index["Reader"](root)
    conflicted.read_hashes[first.resolve()] = "0" * 64
    reject("F3_PRIOR_HASH_CONFLICT_REJECTED", lambda: index["_owned_inventory"](
        conflicted, relative, claims), "INPUT_CHANGED_DURING_READ")
    reject("F3_OBSERVED_PRIOR_HASH_CONFLICT_REJECTED", lambda: profile["_pin_observed"](
        api, conflicted, first.resolve(), claims[0]["sha256"]), "INPUT_CHANGED_DURING_READ")


# F4: every current producer pin must be in the Native report and vector.
repo_reader = index["Reader"](R)
producer_path = repo_reader.path("ops/ci/retrieval.py")
producer_pin = index["sha256"](producer_path)
source_set = profile["_producer_sources"](api, repo_reader, {producer_path: producer_pin})
assert len(source_set) == 21
pins = {repo_reader.path(relative): index["sha256"](repo_reader.path(relative)) for relative in source_set}
source_hashes = {relative: "sha256:" + pins[repo_reader.path(relative)] for relative in source_set}
source_report = {"version_manifest": {"source_sha256": source_hashes}}
profile["_source21"](api, repo_reader, source_report, pins, source_set, "synthetic")
checks.append("F4_ALL_21_SOURCE_PINS_SYNTHETIC")
six = dict(list(source_hashes.items())[:6])
reject("F4_MISSING_15_REJECTED", lambda: profile["_source21"](
    api, index["Reader"](R), {"version_manifest": {"source_sha256": six}}, pins, source_set, "synthetic"),
    "NATIVE_SOURCE21_SET")
extra = dict(source_hashes, **{"synthetic/foreign.py": "sha256:" + "0" * 64})
reject("F4_EXTRA_SOURCE_REJECTED", lambda: profile["_source21"](
    api, index["Reader"](R), {"version_manifest": {"source_sha256": extra}}, pins, source_set, "synthetic"),
    "NATIVE_SOURCE21_SET")
changed = dict(source_hashes)
first_key = next(iter(changed))
changed[first_key] = "sha256:" + "0" * 64
reject("F4_VECTOR_HASH_DRIFT_REJECTED", lambda: profile["_source21"](
    api, index["Reader"](R), {"version_manifest": {"source_sha256": changed}}, pins, source_set, "synthetic"),
    "CURRENT_SOURCE_CLOSURE")


# F5: an author-written receipt or a fabricated delivery without original
# Root event origin cannot satisfy the fixed Root capture interface.
with tempfile.TemporaryDirectory(prefix="researchos-w09-v2-delivery-") as temp:
    root = Path(temp)
    reader = index["Reader"](root)
    reject("F5_AUTHOR_DELIVERY_REJECTED", lambda: profile["_capture_registry"](
        api, reader, {"delivery_ref": {"path": "execution/v2.4/receipts/W09/W09-99/fake.json",
                                               "sha256": "0" * 64}}), "ROOT_CAPTURE_REQUIRED")
    root_prefix = profile["ROOT_CAPTURE_PREFIX"]
    fake_ref = {"path": root_prefix + "fake.json", "sha256": "0" * 64}
    reject("F5_MISSING_FIXED_ROOT_INDEX_REJECTED", lambda: profile["_capture_registry"](
        api, reader, {"delivery_ref": fake_ref}), "FILE_MISSING")
    registry_path = root / profile["ROOT_CAPTURE_INDEX"]
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(json.dumps({"schema": "researchos.root-delivery-capture-index.v1",
                                         "writer_actor": "codex:/root",
                                         "entries": [{"event_id": "synthetic-event", "capture_ref": fake_ref}]}),
                             encoding="utf-8")
    issuance = {"event_id": "synthetic-event", "delivery_ref": fake_ref,
                "review_ref": {"path": root_prefix + "review.json", "sha256": "0" * 64},
                "context_ref": {"path": root_prefix + "context.json", "sha256": "0" * 64}}
    reject("F5_MISSING_ORIGINAL_EVENT_REJECTED", lambda: profile["_root_original"](
        api, index["Reader"](root), issuance, "independent-reviewer", {"context": registry_path}),
        "ROOT_CAPTURE_REGISTRY")

print(json.dumps({"schema": "researchos.w09-formal-profile-v2-controls.v1",
                  "scope": "SYNTHETIC_NONAUTHORITATIVE", "status": "PASS_SOURCE_ONLY",
                  "checks": checks, "actual_native_runs": 0, "actual_dispatcher_runs": 0,
                  "formal_acceptance": False}, ensure_ascii=False, indent=2))
