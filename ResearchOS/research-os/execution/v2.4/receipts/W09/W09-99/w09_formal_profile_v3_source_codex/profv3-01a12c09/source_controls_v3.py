"""Synthetic negative controls for v3 Source. No product or formal run."""
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
index = {"__name__": "w09_v3_synthetic_index"}
exec(compile(index_raw, "formal_case_index.after.py", "exec"), index)
profile = {"__name__": "w09_v3_synthetic_profile"}
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
            "native_event_started_at": "2026-10-01T00:01:00Z",
            "native_event_ended_at": "2026-10-01T00:09:00Z",
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
future_go = {key: dict(value) for key, value in routes.items()}
future_go["0"]["native_event_ended_at"] = "2026-10-20T00:00:00Z"
reject("F2_FUTURE_GO_EVENT_REJECTED", lambda: profile["_review_execution_cutoff"](
    api, future_go, global_runs, "2026-10-02T00:00:00Z", "2026-10-03T00:00:00Z"),
    "REVIEW_EXECUTION_CUTOFF")
go_events = [
    {"Time": "2026-10-20T00:00:00Z", "Action": "start", "Package": "example/p"},
    {"Time": "2026-10-20T00:00:01Z", "Action": "run", "Package": "example/p", "Test": "TestW09Synthetic"},
    {"Time": "2026-10-20T00:00:02Z", "Action": "pass", "Package": "example/p", "Test": "TestW09Synthetic"},
    {"Time": "2026-10-20T00:00:03Z", "Action": "pass", "Package": "example/p"},
]
go_raw = b"".join((json.dumps(event) + "\n").encode("utf-8") for event in go_events)
go_report = {"started_at": "2026-10-01T00:00:00Z", "ended_at": "2026-10-01T00:10:00Z"}
reject("F2_PINNED_FUTURE_GO_STREAM_REJECTED", lambda: profile["_native_event_interval"](
    api, go_raw, go_report, ["TestW09Synthetic"], "synthetic"), "GO_EVENT_CLOCK")
reviewer_example = (R / "execution/v2.4/receipts/W09/W09-99/"
                    "w09_formal_profile_v2_independent_review_codex/profv2r-01a12b31/"
                    "synthetic-counterexamples.json")
reviewer_raw = reviewer_example.read_bytes()
assert len(reviewer_raw) == 5259 and hashlib.sha256(reviewer_raw).hexdigest() == (
    "4c82c2faa0779fdedbeb6c5cd8a4f14e43896089d189237230c0e3efd2c4e99b")
reviewer_f2 = json.loads(reviewer_raw)["F2"]
reviewer_go = b"".join((json.dumps(event) + "\n").encode("utf-8")
                       for event in reviewer_f2["events"])
reject("F2_EXACT_V2_REVIEW_COUNTEREXAMPLE_REJECTED", lambda: profile["_native_event_interval"](
    api, reviewer_go, reviewer_f2["report_times"], ["TestW09Synthetic"], "synthetic"),
    "GO_EVENT_CLOCK")
go_events = [dict(event, Time=event["Time"].replace("2026-10-20", "2026-10-01"))
             for event in go_events]
go_raw = b"".join((json.dumps(event) + "\n").encode("utf-8") for event in go_events)
profile["_native_event_interval"](api, go_raw, go_report, ["TestW09Synthetic"], "synthetic")
checks.append("F2_GO_STREAM_WITHIN_REPORT_SYNTHETIC")
missing_terminal = go_events[:-1]
reject("F2_MISSING_PACKAGE_TERMINAL_REJECTED", lambda: profile["_native_event_interval"](
    api, b"".join((json.dumps(event) + "\n").encode("utf-8") for event in missing_terminal),
    go_report, ["TestW09Synthetic"], "synthetic"), "GO_EVENT_TERMINAL")
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
    extra_upper = folder / "00000003-added.RAW"
    extra_upper.write_bytes(b"added uppercase")
    assert extra_upper in list((root / relative).rglob("*.raw"))
    assert index["recheck_inputs"](snapshot)["status"] == "INVALID"
    checks.append("F3_WINDOWS_UPPERCASE_RAW_REJECTED")
    extra_upper.unlink()
    nested = folder / "Nested"
    nested.mkdir()
    nested_upper = nested / "00000004-added.RaW"
    nested_upper.write_bytes(b"nested mixed case")
    assert nested_upper in list((root / relative).rglob("*.raw"))
    assert index["recheck_inputs"](snapshot)["status"] == "INVALID"
    checks.append("F3_WINDOWS_NESTED_MIXED_RAW_REJECTED")
    nested_upper.unlink()
    nested.rmdir()
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


# F5: only current Canon-approved index plus an original Root-chat pair can
# authorize delivery. The real CP369 pair is protocol evidence, not W09 review.
sample_dir = (R / "execution/v2.4/receipts/W09/W09-99/"
              "checkpoint_r369_native_source_root/cp369-c19-20261009")
sample_path = sample_dir / "nonformal-registration-delivery.original.root.jsonl"
binding_path = sample_dir / "nonformal-registration-delivery.binding.root.json"
sample_raw = sample_path.read_bytes()
binding_raw = binding_path.read_bytes()
assert len(sample_raw) == 24304 and hashlib.sha256(sample_raw).hexdigest() == (
    "219312642745d2ee5cc919a410faa2e59e560aba41b0dfef399e792aeeb7f900")
assert len(binding_raw) == 1733 and hashlib.sha256(binding_raw).hexdigest() == (
    "a9efe15f1f68bfbab03f0426c6d9e7a1bb30536091eeeb4e0683bf703d6df56e")
binding = json.loads(binding_raw)
sample_lines = sample_raw.splitlines(keepends=True)
assert len(sample_lines) == 3
assert [hashlib.sha256(line).hexdigest() for line in sample_lines] == binding["original_line_sha256"]
header, communication, message = [json.loads(line) for line in sample_lines]
assert header["type"] == "session_meta" and header["payload"]["id"] == profile["ROOT_THREAD_ID"]
assert communication["type"] == "inter_agent_communication_metadata"
assert message["type"] == "response_item" and message["payload"]["type"] == "agent_message"
assert message["ordinal"] == communication["ordinal"] + 1
assert message["timestamp"] == communication["timestamp"] == binding["received_at"]
assert message["payload"]["id"] == binding["message_id"]
assert message["payload"]["author"] == binding["sender"]
assert message["payload"]["recipient"] == binding["recipient"]
assert len(message["payload"]["content"]) == 1
assert set(message["payload"]["content"][0]) == {"type", "text"}
assert message["payload"]["content"][0]["type"] == "input_text"
assert binding["protocol_observation_only"] is True
assert binding["W09_parent_or_formal_delivery"] is False
checks.append("F5_REAL_CP369_PAIR_PROTOCOL_OBSERVED_NONFORMAL")
for offset, line, digest in zip(binding["source_line_offsets"], sample_lines,
                                binding["original_line_sha256"]):
    index["_audit_range"]({"path": binding["source_audit_path"], "offset": offset,
                           "bytes": len(line), "sha256": digest})
checks.append("F5_ORIGINAL_AUDIT_OFFSETS_MATCH_CAPTURED_BYTES")

with tempfile.TemporaryDirectory(prefix="researchos-w09-v3-delivery-") as temp:
    root = Path(temp)
    root_prefix = profile["ROOT_CAPTURE_PREFIX"]
    origin_prefix = profile["ROOT_ORIGIN_PREFIX"]
    fake_ref = {"path": root_prefix + "fake.json", "sha256": "0" * 64, "bytes": 1}
    reader = index["Reader"](root)
    reject("F5_AUTHOR_DELIVERY_REJECTED", lambda: profile["_capture_registry"](
        api, reader, {"delivery_ref": {"path": profile["PREFIX"] + "fake.json",
                                               "sha256": "0" * 64}}), "ROOT_CAPTURE_REQUIRED")
    checkpoint_path = root / "execution/v2.4/checkpoint.json"
    checkpoint_path.parent.mkdir(parents=True)
    checkpoint_path.write_text(json.dumps({"work_in_progress": {}}), encoding="utf-8")
    reject("F5_NO_CANON_INDEX_APPROVAL_REJECTED", lambda: profile["_capture_registry"](
        api, index["Reader"](root), {"delivery_ref": fake_ref}), "ROOT_CAPTURE_AUTHORITY_OPEN")

    def write_ref(relative, raw):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return {"path": relative, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

    fake_origin = write_ref(origin_prefix + "invented.jsonl", b'{"source":"collaboration_tool_original"}\n')
    fake_capture = write_ref(root_prefix + "invented.json", b"{}\n")
    event_id = "invented-event-with-no-tool-channel"
    registry = {"schema": "researchos.root-delivery-capture-index.v2",
                "writer_actor": "codex:/root", "Root_thread_id": profile["ROOT_THREAD_ID"],
                "entries": [{"event_id": event_id, "capture_ref": fake_capture,
                             "origin_ref": fake_origin}]}
    registry_ref = write_ref(profile["ROOT_CAPTURE_INDEX"],
                             (json.dumps(registry) + "\n").encode("utf-8"))
    checkpoint_path.write_text(json.dumps({"work_in_progress": {
        "w09_root_delivery_capture_index_ref": registry_ref}}), encoding="utf-8")
    issuance = {"event_id": event_id, "delivery_ref": fake_capture,
                "origin_event_ref": fake_origin,
                "review_ref": {"path": root_prefix + "review.json", "sha256": "0" * 64},
                "context_ref": {"path": root_prefix + "context.json", "sha256": "0" * 64}}
    reject("F5_INVENTED_SOURCE_STRING_REJECTED", lambda: profile["_root_original"](
        api, index["Reader"](root), issuance, "independent-reviewer",
        {"context": root / "unused-context.json"}), "ROOT_ORIGINAL_EVENT")

    sample_origin = write_ref(origin_prefix + "cp369.sample.jsonl", sample_raw)
    sample_capture = write_ref(root_prefix + "cp369.sample.json", binding_raw)
    sample_id = binding["message_id"]
    registry = {"schema": "researchos.root-delivery-capture-index.v2",
                "writer_actor": "codex:/root", "Root_thread_id": profile["ROOT_THREAD_ID"],
                "entries": [{"event_id": sample_id, "capture_ref": sample_capture,
                             "origin_ref": sample_origin}]}
    registry_ref = write_ref(profile["ROOT_CAPTURE_INDEX"],
                             (json.dumps(registry) + "\n").encode("utf-8"))
    checkpoint_path.write_text(json.dumps({"work_in_progress": {
        "w09_root_delivery_capture_index_ref": registry_ref}}), encoding="utf-8")
    issuance = {"event_id": sample_id, "delivery_ref": sample_capture,
                "origin_event_ref": sample_origin,
                "review_ref": binding["review_decision_ref"],
                "context_ref": {"path": root_prefix + "context.json", "sha256": "0" * 64}}
    reject("F5_REAL_NONFORMAL_SAMPLE_CANNOT_AUTHORIZE_W09", lambda: profile["_root_original"](
        api, index["Reader"](root), issuance, binding["sender"],
        {"context": root / "unused-context.json"}), "ROOT_ORIGINAL_EVENT")

    range_path = root / "range-test.txt"
    range_path.write_bytes(b"original\n")
    range_claim = {"path": str(range_path), "offset": 0, "bytes": 9,
                   "sha256": hashlib.sha256(b"original\n").hexdigest()}
    assert index["recheck_inputs"]({"files": {}, "inventories": [],
                                     "audit_ranges": [range_claim]})["status"] == "PASS"
    range_path.write_bytes(b"changed!\n")
    assert index["recheck_inputs"]({"files": {}, "inventories": [],
                                     "audit_ranges": [range_claim]})["status"] == "INVALID"
    checks.append("F5_ORIGINAL_AUDIT_RANGE_CAS_CHANGE_REJECTED")

print(json.dumps({"schema": "researchos.w09-formal-profile-v3-controls.v1",
                  "scope": "SYNTHETIC_NONAUTHORITATIVE", "status": "PASS_SOURCE_ONLY",
                  "checks": checks, "actual_native_runs": 0, "actual_dispatcher_runs": 0,
                  "formal_acceptance": False}, ensure_ascii=False, indent=2))
