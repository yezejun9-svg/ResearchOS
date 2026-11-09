"""One-shot, count-checked Source-only F5 transform; never edits fixed targets."""
from __future__ import annotations

import ast
from pathlib import Path

P = Path(__file__).resolve().parent
profile_path = P / "formal_profile_w09.after.py"
index_path = P / "formal_case_index.after.py"
profile = profile_path.read_text(encoding="utf-8")
index = index_path.read_text(encoding="utf-8")


def replace_once(source: str, old: str, new: str, label: str) -> str:
    assert source.count(old) == 1, (label, source.count(old))
    return source.replace(old, new, 1)


start = profile.index("def _capture_registry(api, reader, issuance):\n")
end = profile.index("def _independent(api, reader, owner, roots, context, outputs, global_rows):\n")
assert profile.count("def _capture_registry(api, reader, issuance):\n") == 1
assert profile.count("def _independent(api, reader, owner, roots, context, outputs, global_rows):\n") == 1
new_delivery = '''def _capture_registry(api, reader, issuance):
    """Only the current Root checkpoint can authorize the fixed capture index."""
    api.require(issuance.get("delivery_ref", {}).get("path", "").startswith(ROOT_CAPTURE_PREFIX),
                "ROOT_CAPTURE_REQUIRED", "author receipt cannot attest delivery")
    checkpoint = reader.read(reader.path("execution/v2.4/checkpoint.json"))
    work = checkpoint.get("work_in_progress")
    api.require(type(work) is dict, "ROOT_CAPTURE_AUTHORITY_OPEN", "current checkpoint slot absent")
    authority = work.get("w09_root_delivery_capture_index_ref")
    api.require(type(authority) is dict and set(authority) == {"path", "sha256", "bytes"},
                "ROOT_CAPTURE_AUTHORITY_OPEN", "Root approval absent")
    api.require(authority["path"] == ROOT_CAPTURE_INDEX
                and type(authority["bytes"]) is int and authority["bytes"] > 0,
                "ROOT_CAPTURE_AUTHORITY_OPEN", "fixed Root index pin")
    path = reader.ref(authority, ROOT_CAPTURE_PREFIX)
    api.require(path.stat().st_size == authority["bytes"],
                "ROOT_CAPTURE_AUTHORITY_OPEN", "approved index bytes")
    return reader.read(path)


def _root_original(api, reader, issuance, reviewer, roots):
    """Check the actual Root-chat message triple against the original audit log."""
    registry = _capture_registry(api, reader, issuance)
    api.require(registry.get("schema") == "researchos.root-delivery-capture-index.v2"
                and registry.get("writer_actor") == "codex:/root"
                and registry.get("Root_thread_id") == ROOT_THREAD_ID,
                "ROOT_CAPTURE_REGISTRY", "current Canon-pinned Root index")
    entries = api.sequence(registry.get("entries"), "Root capture entries")
    ids = [api.text(entry.get("event_id"), "event id") for entry in entries]
    api.require(len(ids) == len(set(ids)), "ROOT_CAPTURE_REGISTRY", "duplicate event")
    api.require(type(issuance.get("event_id")) is str and issuance["event_id"] in ids,
                "ROOT_CAPTURE_REQUIRED", "event not registered")
    entry = next(item for item in entries if item["event_id"] == issuance["event_id"])
    api.require(entry.get("capture_ref") == issuance["delivery_ref"]
                and entry.get("origin_ref") == issuance.get("origin_event_ref")
                and type(entry.get("origin_ref")) is dict,
                "ROOT_CAPTURE_REGISTRY", "exact original binding")
    capture = _doc(api, reader, entry["capture_ref"], ROOT_CAPTURE_PREFIX)
    origin_path = _ref(api, reader, entry["origin_ref"], ROOT_ORIGIN_PREFIX)
    origin_raw = origin_path.read_bytes()
    api.require(type(entry["origin_ref"].get("bytes")) is int
                and len(origin_raw) == entry["origin_ref"]["bytes"],
                "ROOT_ORIGINAL_EVENT", "captured original bytes")
    lines = origin_raw.splitlines(keepends=True)
    api.require(len(lines) == 3 and all(line.endswith(b"\\n") for line in lines),
                "ROOT_ORIGINAL_EVENT", "session and adjacent event lines")
    header, communication, message = [api.strict_json(line) for line in lines]
    api.require(all(type(item) is dict for item in (header, communication, message)),
                "ROOT_ORIGINAL_EVENT", "original record shape")
    api.require(header.get("type") == "session_meta"
                and type(header.get("ordinal")) is int and header["ordinal"] == 0
                and type(header.get("payload")) is dict
                and header["payload"].get("id") == ROOT_THREAD_ID,
                "ROOT_ORIGINAL_EVENT", "Root chat header")
    api.require(communication.get("type") == "inter_agent_communication_metadata"
                and type(communication.get("ordinal")) is int
                and type(communication.get("payload")) is dict
                and type(communication["payload"].get("trigger_turn")) is bool
                and message.get("type") == "response_item"
                and type(message.get("ordinal")) is int
                and message["ordinal"] == communication["ordinal"] + 1
                and message.get("timestamp") == communication.get("timestamp"),
                "ROOT_ORIGINAL_EVENT", "adjacent delivered pair")
    received = api.stamp(message["timestamp"], "original message timestamp")
    payload = api.fields(message.get("payload"),
                         ("type", "author", "content", "id", "recipient",
                          "internal_chat_message_metadata_passthrough"), label="actual agent message")
    metadata = api.fields(message.get("metadata"),
                          ("client_authored", "user_input_order"), label="actual message metadata")
    passthrough = api.fields(payload["internal_chat_message_metadata_passthrough"],
                             ("create_time", "turn_id"), label="actual message passthrough")
    api.require(payload["type"] == "agent_message"
                and payload["author"] == reviewer
                and payload["recipient"] == "/root"
                and payload["id"] == issuance["event_id"]
                and type(metadata["client_authored"]) is bool
                and metadata["client_authored"] is False
                and type(metadata["user_input_order"]) is int
                and type(passthrough["create_time"]) is float
                and type(passthrough["turn_id"]) is str and passthrough["turn_id"],
                "ROOT_ORIGINAL_EVENT", "actual sender, recipient and message id")
    content_items = payload["content"]
    api.require(type(content_items) is list and len(content_items) == 1
                and type(content_items[0]) is dict
                and set(content_items[0]) == {"type", "text"}
                and content_items[0]["type"] == "text"
                and type(content_items[0]["text"]) is str
                and content_items[0]["text"],
                "ROOT_ORIGINAL_PLAINTEXT_REQUIRED", "encrypted or mixed message content")
    content = content_items[0]["text"]
    api.require(capture.get("schema") == "researchos.root-actual-audit-formal-delivery.v1"
                and capture.get("issued_by") == "codex:/root"
                and capture.get("protocol_observation_only") is False
                and capture.get("W09_parent_or_formal_delivery") is True
                and capture.get("Root_thread_id") == ROOT_THREAD_ID
                and capture.get("message_id") == payload["id"]
                and capture.get("sender") == payload["author"]
                and capture.get("recipient") == payload["recipient"]
                and capture.get("received_at") == message["timestamp"]
                and capture.get("original_capture_ref") == entry["origin_ref"]
                and capture.get("review_ref") == issuance["review_ref"]
                and capture.get("context_ref") == issuance["context_ref"]
                and capture.get("content_sha256") == hashlib.sha256(content.encode("utf-8")).hexdigest()
                and issuance["review_ref"]["sha256"] in content
                and api.sha256(roots["context"]) in content,
                "ROOT_ORIGINAL_EVENT", "formal binding and exact message content")
    api.require(api.stamp(capture.get("root_observed_at"), "Root observation") >= received,
                "ROOT_ORIGINAL_EVENT", "Root observation time")
    offsets = capture.get("source_line_offsets")
    digests = capture.get("original_line_sha256")
    api.require(capture.get("source_audit_path") == ROOT_SOURCE_AUDIT_LOG
                and type(offsets) is list and len(offsets) == 3
                and all(type(offset) is int and offset >= 0 for offset in offsets)
                and offsets == sorted(set(offsets))
                and type(digests) is list and len(digests) == 3
                and all(type(value) is str and api.SHA.fullmatch(value) for value in digests)
                and type(capture.get("source_prefix_size_observed")) is int,
                "ROOT_ORIGINAL_SOURCE", "original audit offsets and hashes")
    source = Path(ROOT_SOURCE_AUDIT_LOG)
    api.require(source.is_file(), "ROOT_ORIGINAL_SOURCE", "Root audit log absent")
    with source.open("rb") as stream:
        for offset, digest, line in zip(offsets, digests, lines):
            api.require(offset + len(line) <= capture["source_prefix_size_observed"],
                        "ROOT_ORIGINAL_SOURCE", "source prefix boundary")
            stream.seek(offset)
            observed = stream.readline()
            api.require(observed == line and hashlib.sha256(observed).hexdigest() == digest,
                        "ROOT_ORIGINAL_SOURCE", "original audit bytes disagree")
            reader.w09_audit_ranges.append({"path": str(source), "offset": offset,
                                            "bytes": len(line), "sha256": digest})
    return capture, message


'''
profile = profile[:start] + new_delivery + profile[end:]
profile = replace_once(profile,
    'ROOT_ORIGIN_PREFIX = "execution/v2.4/root_original_events/W09/W09-99/"\n',
    'ROOT_ORIGIN_PREFIX = "execution/v2.4/root_original_events/W09/W09-99/"\n'
    'ROOT_THREAD_ID = "01a11007-5233-7ca1-b71f-9e9e5ce84c98"\n'
    'ROOT_SOURCE_AUDIT_LOG = "C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl"\n',
    "Root source constants")
profile = replace_once(profile,
    '    reader.w09_owned_inventories = []\n',
    '    reader.w09_owned_inventories = []\n    reader.w09_audit_ranges = []\n',
    "Root source CAS initialization")
profile = replace_once(profile,
    '    context["_verified_owned_inventories"] = list(reader.w09_owned_inventories)\n',
    '    context["_verified_owned_inventories"] = list(reader.w09_owned_inventories)\n'
    '    context["_verified_audit_ranges"] = list(reader.w09_audit_ranges)\n',
    "Root source CAS output")
profile = replace_once(profile,
    'api.stamp(origin["received_at"], "original received")',
    'api.stamp(capture["received_at"], "original received")',
    "Root receipt time")

index = replace_once(index,
    'def recheck_inputs(snapshot):\n',
    '''def _audit_range(item):
    path = Path(item["path"])
    require(type(item["offset"]) is int and item["offset"] >= 0
            and type(item["bytes"]) is int and item["bytes"] > 0,
            "ROOT_ORIGINAL_SOURCE", "range shape")
    with path.open("rb") as stream:
        stream.seek(item["offset"])
        observed = stream.read(item["bytes"])
    require(len(observed) == item["bytes"] and sha256_bytes(observed) == item["sha256"],
            "ROOT_ORIGINAL_SOURCE_CHANGED", str(path))


def recheck_inputs(snapshot):
''',
    "Root source range CAS function")
index = replace_once(index,
    'sha256_bytes(observed) == item["sha256"]',
    'hashlib.sha256(observed).hexdigest() == item["sha256"]',
    "range hash implementation")
index = replace_once(index,
    '        for inventory in snapshot.get("inventories", []):\n',
    '        for item in snapshot.get("audit_ranges", []):\n'
    '            _audit_range(item)\n'
    '        for inventory in snapshot.get("inventories", []):\n',
    "Root source recheck")
index = replace_once(index,
    '"product_business_acceptance_created": False, "dependency_snapshot": {"files": {}, "inventories": []}}',
    '"product_business_acceptance_created": False, "dependency_snapshot": {"files": {}, "inventories": [], "audit_ranges": []}}',
    "snapshot shape")
index = replace_once(index,
    'result["dependency_snapshot"]["inventories"].extend(context["_verified_owned_inventories"])',
    'result["dependency_snapshot"]["inventories"].extend(context["_verified_owned_inventories"])\n'
    '                    result["dependency_snapshot"]["audit_ranges"].extend(context["_verified_audit_ranges"])',
    "snapshot range output")
index = replace_once(index,
    '    try:\n        for inventory in result["dependency_snapshot"]["inventories"]:\n',
    '    try:\n        for item in result["dependency_snapshot"]["audit_ranges"]:\n'
    '            _audit_range(item)\n'
    '        for inventory in result["dependency_snapshot"]["inventories"]:\n',
    "final range CAS")

ast.parse(profile, filename=str(profile_path))
ast.parse(index, filename=str(index_path))
assert profile_path.read_text(encoding="utf-8").count("def _capture_registry(api, reader, issuance):\n") == 1
assert index_path.read_text(encoding="utf-8").count("def recheck_inputs(snapshot):\n") == 1
profile_path.write_text(profile, encoding="utf-8", newline="")
index_path.write_text(index, encoding="utf-8", newline="")
assert profile_path.read_text(encoding="utf-8") == profile
assert index_path.read_text(encoding="utf-8") == index
print("F5_V3_SOURCE_TRANSFORM_AST_PASS_TWO_OWNED_CANDIDATES")
