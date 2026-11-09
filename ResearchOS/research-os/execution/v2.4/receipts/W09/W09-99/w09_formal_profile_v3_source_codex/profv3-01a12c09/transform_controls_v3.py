"""One-shot, AST-checked replacement of obsolete v2 F5 source controls."""
from __future__ import annotations

import ast
from pathlib import Path

path = Path(__file__).resolve().parent / "source_controls_v3.py"
source = path.read_text(encoding="utf-8")
start_marker = "# F5: an author-written receipt or a fabricated delivery without original\n"
end_marker = "print(json.dumps({\"schema\": \"researchos.w09-formal-profile-v3-controls.v1\",\n"
assert source.count(start_marker) == source.count(end_marker) == 1
start, end = source.index(start_marker), source.index(end_marker)
replacement = '''# F5: only current Canon-approved index plus an original Root-chat pair can
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

    fake_origin = write_ref(origin_prefix + "invented.jsonl", b'{"source":"collaboration_tool_original"}\\n')
    fake_capture = write_ref(root_prefix + "invented.json", b"{}\\n")
    event_id = "invented-event-with-no-tool-channel"
    registry = {"schema": "researchos.root-delivery-capture-index.v2",
                "writer_actor": "codex:/root", "Root_thread_id": profile["ROOT_THREAD_ID"],
                "entries": [{"event_id": event_id, "capture_ref": fake_capture,
                             "origin_ref": fake_origin}]}
    registry_ref = write_ref(profile["ROOT_CAPTURE_INDEX"],
                             (json.dumps(registry) + "\\n").encode("utf-8"))
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
                             (json.dumps(registry) + "\\n").encode("utf-8"))
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
    range_path.write_bytes(b"original\\n")
    range_claim = {"path": str(range_path), "offset": 0, "bytes": 9,
                   "sha256": hashlib.sha256(b"original\\n").hexdigest()}
    assert index["recheck_inputs"]({"files": {}, "inventories": [],
                                     "audit_ranges": [range_claim]})["status"] == "PASS"
    range_path.write_bytes(b"changed!\\n")
    assert index["recheck_inputs"]({"files": {}, "inventories": [],
                                     "audit_ranges": [range_claim]})["status"] == "INVALID"
    checks.append("F5_ORIGINAL_AUDIT_RANGE_CAS_CHANGE_REJECTED")

'''
candidate = source[:start] + replacement + source[end:]
ast.parse(candidate, filename=str(path))
assert path.read_text(encoding="utf-8") == source
path.write_text(candidate, encoding="utf-8", newline="")
assert path.read_text(encoding="utf-8") == candidate
print("V3_F5_CONTROLS_AST_PASS")
