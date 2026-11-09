import ast
import datetime as dt
import hashlib
import json
import ntpath
from pathlib import Path
import re
import sys
import types

R = Path("D:/作品集/ResearchOS/research-os")
HERE = Path(__file__).resolve().parent
RUN = R / "execution/v2.4/receipts/W09/W09-99/w09_br8_actual_root/actual-20261010-01"
RAW_REVIEWER = "/root/backup_regression_resources"
ROOT_ACTOR = "codex:/root"
ROOT_THREAD = "01a11007-5233-7ca1-b71f-9e9e5ce84c98"
NEW_EVENT = "amsg_01a123f7-845b-7043-9dc7-f88b800cdf4b"
SHA = re.compile(r"[0-9a-f]{64}")
GUARD_REF = {"path": str(R / "execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"), "sha256": "e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85", "bytes": 11404}
OWNER_REF = {"path": str(RUN / "prospective-owner.literal02.actual.root.json"), "sha256": "4858c914f310e2fc83999a511fc070e054c57b12ce594ab14347e0f1612ee9d6", "bytes": 1085}
EXTRAS_REF = {"path": str(RUN / "check.literal02.actual.extras.root.json"), "sha256": "8b2307397e8fb6bc9b864d0d32d63a30db9677bb4dfb37155a892b855a2c80c2", "bytes": 1355}
PROPOSAL_REF = {"path": str(RUN / "capture-7d7d176970554ad3b9cdb72bc3b1ce8a/root-corrected-publication01/result.json"), "sha256": "04f15daf5921e4955859af90b39bde8f6283128c91da7db6713f1e5e8c433ce8", "bytes": 6146}
MAIN_REF = {"path": str(R / "execution/v2.4/formal_profile_w09.py"), "sha256": "1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087", "bytes": 71403}
REDELIVERY_REF = {"path": str(R / "execution/v2.4/receipts/W09/W09-99/w09_br8_prospective_owner_independent_approval_codex/approve-20261010-01/redelivery-metadata.json"), "sha256": "57421d40ecd5380dcb7fe3d49d11c017c8371c6b0cb8a500f2f89eb981a3e9b4", "bytes": 1826}

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON key: " + key)
        result[key] = value
    return result

def decode(raw):
    return json.loads(raw, object_pairs_hook=pairs)

def shape(ref, width):
    if type(ref) is not dict or set(ref) != ({"path", "sha256", "bytes"} if width == 3 else {"path", "sha256"}):
        raise ValueError("reference exact field shape")
    if type(ref["path"]) is not str or not ref["path"] or type(ref["sha256"]) is not str or not SHA.fullmatch(ref["sha256"]):
        raise ValueError("reference path/digest type")
    if width == 3 and (type(ref["bytes"]) is not int or ref["bytes"] < 0):
        raise ValueError("reference byte count")
    return ref

def path_for(ref, base=R):
    p = Path(ref["path"])
    return p if p.is_absolute() else base / p

def identity(ref, base=R):
    return ntpath.normcase(ntpath.normpath(str(path_for(ref, base))))

def same(left, right, left_base=R, right_base=R):
    return identity(left, left_base) == identity(right, right_base) and left["sha256"] == right["sha256"] and (left.get("bytes") is None or right.get("bytes") is None or left["bytes"] == right["bytes"])

def exact_read(ref):
    shape(ref, 3)
    raw = path_for(ref).read_bytes()
    if len(raw) != ref["bytes"] or digest(raw) != ref["sha256"]:
        raise ValueError("pin mismatch: " + ref["path"])
    return raw

def public_ref(path):
    raw = Path(path).read_bytes()
    return {"path": str(path), "sha256": digest(raw), "bytes": len(raw)}

def stamp(value):
    if type(value) is not str:
        raise ValueError("time string required")
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone required")
    return parsed.astimezone(dt.timezone.utc)

def write_new(name, doc):
    raw = (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with (HERE / name).open("xb") as stream:
        stream.write(raw)
    return {"path": str(HERE / name), "sha256": digest(raw), "bytes": len(raw)}

checks = []
def require(label, condition):
    if not condition:
        raise ValueError(label)
    checks.append({"id": label, "result": "PASS"})

owner_seed = decode(exact_read(OWNER_REF))
extras_seed = decode(exact_read(EXTRAS_REF))
proposal_seed = decode(exact_read(PROPOSAL_REF))
guard_raw = exact_read(GUARD_REF)
module = types.ModuleType("owner_literal02_guard")
module.__file__ = GUARD_REF["path"]
sys.modules[module.__name__] = module
exec(compile(guard_raw, module.__file__, "exec"), module.__dict__)
guard = module.SourceReadGuard()
primary = None
draft = None
closure = None
try:
    resources = [OWNER_REF, EXTRAS_REF, PROPOSAL_REF, MAIN_REF, REDELIVERY_REF, GUARD_REF]
    resources.extend(proposal_seed[key] for key in ("payload_ref", "origin_payload_ref", "capture_payload_ref", "issuance_ref"))
    for key in ("context_ref", "review_ref"):
        rr = shape(extras_seed[key], 2)
        raw = path_for(rr).read_bytes()
        require("SEED_" + key.upper() + "_SHA", digest(raw) == rr["sha256"])
        resources.append({"path": str(path_for(rr)), "sha256": rr["sha256"], "bytes": len(raw)})
    if "plan_ref" in extras_seed:
        resources.append(shape(extras_seed["plan_ref"], 3))
    refs = {}
    for source_ref in resources:
        shape(source_ref, 3)
        absolute_ref = dict(source_ref, path=str(path_for(source_ref)))
        key = identity(absolute_ref)
        if key in refs:
            require("RESOURCE_DUPLICATE_PIN_STABILITY", refs[key]["sha256"] == absolute_ref["sha256"] and refs[key]["bytes"] == absolute_ref["bytes"])
        refs[key] = absolute_ref
    guard.acquire(list(refs.values()))
    def raw(ref):
        return guard.get_buffer(str(path_for(ref)))
    def doc(ref):
        return decode(raw(ref))
    owner = doc(OWNER_REF)
    extras = doc(EXTRAS_REF)
    proposal = doc(PROPOSAL_REF)
    issuance = doc(proposal["issuance_ref"])
    capture = doc(proposal["capture_payload_ref"])
    index = doc(proposal["payload_ref"])
    review = decode(raw(extras["review_ref"]))
    redelivery = doc(REDELIVERY_REF)
    require("EXTRAS_EXACT_OWNER_PIN", extras["prospective_owner_ref"] == OWNER_REF or same(shape(extras["prospective_owner_ref"], 3), OWNER_REF))
    require("OWNER_ID_STATUS_AND_ROLES", owner["id"] == "W09-99" and owner["status"] == "ACCEPTED" and owner["executor_id"] == ROOT_ACTOR and owner["verifier_id"] == RAW_REVIEWER)
    require("PROPOSAL_NOT_FORMAL_ACCEPTANCE", proposal["schema"] == "researchos.w09-capture-publication-proposal.v1" and proposal["formal_acceptance"] is False)
    for key in ("context_ref", "review_ref"):
        shape(extras[key], 2)
        shape(issuance[key], 2)
        shape(capture[key], 2)
        require("CHAIN_" + key.upper(), extras[key] == issuance[key] == capture[key])
    require("ISSUANCE_METADATA_PIN", same(shape(extras["issuance_ref"], 2), shape(proposal["issuance_ref"], 3)))
    expected_evidence = (extras["context_ref"], extras["review_ref"], extras["issuance_ref"])
    require("OWNER_EXACTLY_THREE_EVIDENCE_REFS", type(owner["evidence"]) is list and len(owner["evidence"]) == 3)
    matched = []
    for evidence in owner["evidence"]:
        shape(evidence, 2)
        matches = [i for i, expected in enumerate(expected_evidence) if same(evidence, expected, R / "execution/v2.4", R)]
        require("OWNER_EVIDENCE_UNIQUE_EXACT_BINDING_" + str(len(matched)), len(matches) == 1 and matches[0] not in matched)
        matched.append(matches[0])
    require("REVIEW_ALREADY_ACCEPTED_EXACT_ROLES", review["schema"] == "researchos.w09.independent-review.v1" and review["decision"] == "ACCEPTED" and review["reviewer_id"] == review["issuer_id"] == RAW_REVIEWER and review["executor_id"] == ROOT_ACTOR and review["missing"] == [] and review["failed"] == [] and len(review["verdicts"]) == 8)
    require("REVIEW_CONTEXT_AND_RUN", review["context_ref"] == extras["context_ref"] and issuance["run_id"] == review["run_id"] and issuance["task_id"] == "W09" and issuance["step_id"] == "W09-99")
    require("ISSUANCE_OBSERVER_AND_ISSUER_ROLES", issuance["schema"] == "researchos.w09.root-observed-issuance.v1" and issuance["actor"] == issuance["observer_id"] == issuance["executor_id"] == ROOT_ACTOR and issuance["issuer_id"] == issuance["reviewer_id"] == RAW_REVIEWER)
    require("CAPTURE_ROOT_AND_RAW_BACKEND_ROLES", capture["schema"] == "researchos.root-actual-audit-formal-delivery.v1" and capture["issued_by"] == ROOT_ACTOR and capture["protocol_observation_only"] is False and capture["W09_parent_or_formal_delivery"] is True and capture["Root_thread_id"] == ROOT_THREAD and capture["sender"] == RAW_REVIEWER and capture["recipient"] == "/root")
    require("ROOT_EVENT_ID", capture["message_id"] == issuance["event_id"] == NEW_EVENT)
    require("PROPOSED_FIXED_DESTINATIONS", proposal["fixed_path"] == "execution/v2.4/root_delivery_captures/W09/W09-99/index.json" and proposal["origin_fixed_path"] == issuance["origin_event_ref"]["path"] and proposal["capture_fixed_path"] == issuance["delivery_ref"]["path"])
    for proposed_key, logical_ref in (("capture_payload_ref", issuance["delivery_ref"]), ("origin_payload_ref", issuance["origin_event_ref"])):
        shape(logical_ref, 3)
        require("PROPOSED_" + proposed_key.upper() + "_EXACT_BYTES", proposal[proposed_key]["sha256"] == logical_ref["sha256"] and proposal[proposed_key]["bytes"] == logical_ref["bytes"])
    require("CAPTURE_ORIGINAL_REF", capture["original_capture_ref"] == issuance["origin_event_ref"])
    require("INDEX_ROLE_SCHEMA", index["schema"] == "researchos.root-delivery-capture-index.v2" and index["writer_actor"] == ROOT_ACTOR and index["Root_thread_id"] == ROOT_THREAD)
    entries = [e for e in index["entries"] if e.get("event_id") == NEW_EVENT]
    require("INDEX_NEW_EVENT_UNIQUE_EXACT_BINDING", len(entries) == 1 and entries[0]["capture_ref"] == issuance["delivery_ref"] and entries[0]["origin_ref"] == issuance["origin_event_ref"])
    require("INDEX_PRESERVES_OLD_EVENT", any(e.get("event_id") == "amsg_01a123ef-ffeb-72c3-a175-28d043f4a946" and e.get("capture_ref", {}).get("sha256") == "8a0c51936c16d881ae54e1332271ff84531fb8d2524fd771ae13251ec5f99555" and e.get("origin_ref", {}).get("sha256") == "2cbe96245bbcdec9fae9b1b6fb1833cd2ec9aa80e9840c3dd0ed3eb9aefdc96d" for e in index["entries"]))
    original_lines = raw(proposal["origin_payload_ref"]).splitlines(keepends=True)
    require("ORIGINAL_EXACT_THREE_LF_LINES", len(original_lines) == 3 and all(line.endswith(b"\n") for line in original_lines))
    header, meta, final = [decode(line) for line in original_lines]
    require("ORIGINAL_ROOT_HEADER", header["type"] == "session_meta" and header["payload"]["id"] == ROOT_THREAD)
    require("ORIGINAL_ADJACENT_BACKEND_FINAL", meta["type"] == "inter_agent_communication_metadata" and final["type"] == "response_item" and type(meta["ordinal"]) is int and type(final["ordinal"]) is int and final["ordinal"] == meta["ordinal"] + 1 and meta["timestamp"] == final["timestamp"] == capture["received_at"])
    payload = final["payload"]
    require("ORIGINAL_REAL_RAW_BACKEND", payload["type"] == "agent_message" and payload["id"] == NEW_EVENT and payload["author"] == RAW_REVIEWER and payload["recipient"] == "/root" and final["metadata"]["client_authored"] is False)
    require("ORIGINAL_CONTENT_ONE_INPUT_TEXT", type(payload["content"]) is list and len(payload["content"]) == 1 and payload["content"][0]["type"] == "input_text" and type(payload["content"][0]["text"]) is str)
    content = payload["content"][0]["text"]
    require("ORIGINAL_FULL_CONTENT_DIGEST", digest(content.encode("utf-8")) == capture["content_sha256"])
    prefix = "Message Type: FINAL_ANSWER\nTask name: /root\nSender: " + RAW_REVIEWER + "\nPayload:\n"
    require("ORIGINAL_ANCHORED_FINAL_ENVELOPE", content.startswith(prefix))
    delivery = decode(content[len(prefix):])
    require("ORIGINAL_STRUCTURED_REVIEW_CONTEXT_BINDING", same(shape(delivery["review_ref"], 3), extras["review_ref"]) and shape(delivery["context_ref"], 2) == extras["context_ref"] and delivery["reviewer_id"] == RAW_REVIEWER and delivery["review_decision"] == "ACCEPTED")
    require("ORIGINAL_UNIQUE_REDELIVERY_BINDING", delivery["redelivery_digest"] == REDELIVERY_REF["sha256"] and same(shape(delivery["redelivery_metadata_ref"], 3), REDELIVERY_REF) and delivery["redelivery_id"] == redelivery["redelivery_id"])
    offsets = capture["source_line_offsets"]
    require("ORIGINAL_OFFSETS_AND_PREFIX", type(offsets) is list and len(offsets) == 3 and all(type(value) is int and value >= 0 for value in offsets) and offsets == sorted(set(offsets)) and type(capture["source_prefix_size_observed"]) is int and capture["source_prefix_size_observed"] >= max(offset + len(line) for offset, line in zip(offsets, original_lines)))
    require("ORIGINAL_EXACT_LINE_HASHES", capture["original_line_sha256"] == [digest(line) for line in original_lines])
    constants = {target.id: node.value for node in ast.parse(raw(MAIN_REF).decode("utf-8")).body if isinstance(node, ast.Assign) for target in node.targets if isinstance(target, ast.Name)}
    literal = ast.literal_eval(constants["ROOT_SOURCE_AUDIT_LOG"])
    require("MAIN_EXACT_SOURCE_AUDIT_LITERAL", capture["source_audit_path"] == literal)
    times = [stamp(review["issued_at"]), stamp(final["timestamp"]), stamp(capture["root_observed_at"]), stamp(issuance["observed_at"]), stamp(owner["accepted_at"]), dt.datetime.now(dt.timezone.utc)]
    require("TIME_ORDER_REVIEW_FINAL_OBSERVATION_ISSUANCE_OWNER_NOW", times == sorted(times))
    draft = {"schema": "researchos.w09-prospective-owner-independent-approval.v1", "decision": "APPROVED_PROSPECTIVE_OWNER_ONLY", "reviewer_id": RAW_REVIEWER, "prospective_owner_ref": OWNER_REF, "extras_ref": EXTRAS_REF, "proposed_publication_ref": PROPOSAL_REF, "proposed_capture_ref": proposal["capture_payload_ref"], "proposed_index_ref": proposal["payload_ref"], "original_three_line_ref": proposal["origin_payload_ref"], "issuance_ref": proposal["issuance_ref"], "review_ref": extras["review_ref"], "context_ref": extras["context_ref"], "Main_ref": MAIN_REF, "redelivery_metadata_ref": REDELIVERY_REF, "checks": checks, "approved_at": dt.datetime.now(dt.timezone.utc).isoformat(), "fixed_publication": "PENDING_ROOT", "Maincheck": "PENDING_ROOT", "SS_registration": "PENDING_ROOT", "independent_literal_repair_review": "ROOT_MANAGED_SEPARATE_OBLIGATION", "formal_review_replayed": False, "Native_or_Mode_or_product_replayed": False, "Main_or_Canon_or_SS_written": False, "derive_or_42_acceptance_claimed": False, "old_REFUSED_approval_retained": True, "old_original1250_retained": True}
except BaseException as exc:
    primary = {"type": type(exc).__name__, "message": str(exc)}
finally:
    closure = guard.close()
    closure_ref = write_new("SourceGuard.closed.json", closure)
if primary is not None or closure.get("closed") is not True or closure.get("retained_handles_count") != 0 or closure.get("errors"):
    rejection = {"schema": "researchos.w09-prospective-owner-independent-approval.v1", "decision": "REFUSED", "reviewer_id": RAW_REVIEWER, "prospective_owner_ref": OWNER_REF, "checks": checks, "primary_error": primary, "SourceGuard_ref": closure_ref, "fixed_publication": "PENDING_ROOT", "Maincheck": "NOT_RUN", "SS_registration": "NOT_RUN"}
    print(json.dumps({"approval_ref": write_new("approval.json", rejection), "decision": "REFUSED", "SourceGuard_ref": closure_ref}, ensure_ascii=False))
    print("ROOT_PYTHON_EXIT=1")
    sys.exit(1)
draft["SourceGuard_ref"] = closure_ref
draft["SourceGuard_closed"] = True
draft["retained_handles_count"] = 0
draft["SourceGuard_errors"] = []
approval_ref = write_new("approval.json", draft)
print(json.dumps({"decision": draft["decision"], "reviewer_id": RAW_REVIEWER, "approval_ref": approval_ref, "prospective_owner_ref": OWNER_REF, "SourceGuard_ref": closure_ref, "checks_passed": len(checks)}, ensure_ascii=False))
print("ROOT_PYTHON_EXIT=0")
