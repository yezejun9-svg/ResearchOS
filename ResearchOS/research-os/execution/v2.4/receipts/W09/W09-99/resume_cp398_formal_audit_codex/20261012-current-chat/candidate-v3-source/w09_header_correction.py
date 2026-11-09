"""One incident's read-only W09 audit-header recovery; never issues acceptance.

The old Context, eight verdicts and original events remain immutable. The sole
compatible interpreter transition is the W09 profile pinned below. Admission
also requires a real current-chat delivery from a non-author reviewer, pinned
by the existing Root checkpoint. No receipt-supplied code is executed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

PROJECT_ID = "aede0678-7308-43dc-b9f2-cfe3d90cfdfb"
REPOSITORY = "D:/作品集/ResearchOS/research-os"
OLD_THREAD = "01a11007-5233-7ca1-b71f-9e9e5ce84c98"
OLD_LOG = "C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl"
CURRENT_THREAD = "01a12eb9-8243-7761-8f58-1e99a57f595e"
CURRENT_LOG = "C:/Users/yqyyds/.codex/sessions/2026/10/12/rollout-2026-10-12T14-07-51-01a12eb9-8243-7761-8f58-1e99a57f595e.jsonl"
CURRENT_HEADER_SHA = "eb12adcde10c59c067f34055b9c74ae278ca157856b2da606f2aa5427654af4e"
OLD_HEADER_SHA = "85ee364805d248e6bcf377f21ef902c143b8f9e189ff5c9f7309531339fcc273"
NEW_HEADER_SHA = "37776bec053b16e8649641360e06f1d8f2839eb653042cc5556917a89fe6f6b8"
PROFILE_PATH = "execution/v2.4/formal_profile_w09.py"
PROFILE_OLD_SHA = "1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087"
INDEX_PATH = "execution/v2.4/formal_case_index.py"
INDEX_SHA = "e08a7f605ca12d79c672b6af0360a02b26e2231d2a602207d0ea6a37f24f7b0b"
MODULE_PATH = "execution/v2.4/w09_header_correction.py"
AUTHOR = "/root/resume_audit"
PREFIX = "execution/v2.4/receipts/W09/W09-99/"
ORIGINAL_ROOT_HASHES = {
    "context": "70a5fc149e2fda2fbf6d9ce518ec7c34d11d07f2f1985cf8d68f32b20652562c",
    "review": "ddc2d04040a388d6bb189b4db7adb4b043ccdb31c650f4bedc70458064a8fda0",
    "issuance": "990c6364dec7489ca1fa946908b3d11323e81c49a5b7147d0780240184cf399d",
}
REVIEW_CHECKS = {"certificate_pins", "header_delta", "business_ranges",
                 "project_bindings", "interpreter_diff", "negative_controls"}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pinned(api, reader, ref, prefix=None):
    api.fields(ref, ("path", "sha256", "bytes"), label="correction reference")
    path = reader.ref({k: ref[k] for k in ("path", "sha256")}, prefix)
    api.require(type(ref["bytes"]) is int and path.stat().st_size == ref["bytes"],
                "CORRECTION_BYTES", ref["path"])
    return path


def header_delta(api, old_raw, new_raw):
    """Exact semantic delta, not a field-exclusion or normalization rule."""
    old, new = api.strict_json(old_raw), api.strict_json(new_raw)
    api.require(type(old) is dict and type(new) is dict
                and type(old.get("payload")) is dict
                and old["payload"].get("model_provider") == "openai",
                "CORRECTION_HEADER_DELTA", "old provider")
    expected = json.loads(json.dumps(old))
    expected["payload"]["model_provider"] = "custom"
    api.require(new == expected, "CORRECTION_HEADER_DELTA", "exactly openai to custom")


def audit_line(api, correction, offset, expected_sha, old_line, observed):
    """Return the actual range pin; unchanged records retain byte equality."""
    if offset == 0 and correction is not None:
        api.require(expected_sha == OLD_HEADER_SHA and digest(old_line) == OLD_HEADER_SHA
                    and digest(observed) == NEW_HEADER_SHA
                    and len(old_line) == len(observed) == 22732,
                    "CORRECTION_HEADER_PIN", "the sole approved historical header pair")
        header_delta(api, old_line, observed)
    else:
        api.require(observed == old_line and digest(observed) == expected_sha,
                    "CORRECTION_EVENT_CHANGED", "exact original event bytes")
    return {"path": OLD_LOG, "offset": offset, "bytes": len(observed), "sha256": digest(observed)}


def _triplet(api, reader, binding):
    capture = pinned(api, reader, binding["original_capture_ref"])
    lines = capture.read_bytes().splitlines(keepends=True)
    offsets, hashes = binding["source_line_offsets"], binding["original_line_sha256"]
    api.require(len(lines) == len(offsets) == len(hashes) == 3
                and offsets[0] == 0 and offsets == sorted(set(offsets))
                and all(type(x) is int and x >= 0 for x in offsets)
                and all(line.endswith(b"\n") for line in lines),
                "CORRECTION_TRIPLET", "complete ordered records")
    with Path(OLD_LOG).open("rb") as stream:
        for offset, expected, line in zip(offsets, hashes, lines):
            api.require(digest(line) == expected
                        and offset + len(line) <= binding["source_prefix_size_observed"],
                        "CORRECTION_TRIPLET", "frozen record and range")
            stream.seek(offset)
            observed = stream.readline()
            reader.w09_audit_ranges.append(audit_line(api, True, offset, expected, line, observed))


def certificate_evidence(api, reader, cert, roots):
    """Read real old evidence only. This function grants no interpreter authority."""
    api.fields(cert, ("schema", "status", "prepared_by", "prepared_in_thread",
                      "created_at", "project_identity_ref", "project_id", "repository",
                      "old_thread_id", "old_audit_log", "current_thread_id", "current_audit_log",
                      "current_header_sha256", "old_header_sha256", "new_header_sha256",
                      "exact_change", "original_roots", "role_registry_ref", "audit_bindings",
                      "old_profile_archive_ref", "old_profile_ref", "new_profile_ref",
                      "index_ref", "verifier_module_ref", "original_failure_ref"),
               label="one-incident correction certificate")
    api.require(cert["schema"] == "researchos.w09.header-metadata-correction.v1"
                and cert["status"] == "CANDIDATE_FOR_INDEPENDENT_REVIEW"
                and cert["prepared_by"] == AUTHOR
                and cert["prepared_in_thread"] == cert["current_thread_id"] == CURRENT_THREAD
                and cert["current_audit_log"] == CURRENT_LOG
                and cert["current_header_sha256"] == CURRENT_HEADER_SHA
                and cert["old_thread_id"] == OLD_THREAD and cert["old_audit_log"] == OLD_LOG
                and cert["old_header_sha256"] == OLD_HEADER_SHA
                and cert["new_header_sha256"] == NEW_HEADER_SHA
                and cert["exact_change"] == {"json_pointer": "/payload/model_provider",
                                              "before": "openai", "after": "custom"},
                "CORRECTION_SCOPE", "one known incident only")
    api.stamp(cert["created_at"], "certificate created_at")
    identity_path = pinned(api, reader, cert["project_identity_ref"])
    api.require(identity_path == reader.path("execution/project_identity.json")
                and reader.read(identity_path)["project_id"] == cert["project_id"] == PROJECT_ID
                and reader.repo == Path(REPOSITORY).resolve(strict=True)
                and cert["repository"] == REPOSITORY,
                "CORRECTION_PROJECT", "actual permanent project")
    api.exact_ids(list(cert["original_roots"]), ORIGINAL_ROOT_HASHES, "original root kinds")
    for name, ref in cert["original_roots"].items():
        api.require(ref["sha256"] == ORIGINAL_ROOT_HASHES[name]
                    and pinned(api, reader, ref, PREFIX) == roots[name],
                    "CORRECTION_ORIGINAL_ROOT", name)
    context = reader.read(roots["context"])
    issuance = reader.read(roots["issuance"])
    api.require(cert["role_registry_ref"] == context["role_policy"]["registry_ref"]
                and context["version_vector"]["components"]["model"]["status"] == "not_applicable",
                "CORRECTION_ROLE_BINDING", "unchanged roles and no business model dependency")
    role_registry = reader.read(pinned(api, reader, cert["role_registry_ref"]))
    wanted = []
    for proof in role_registry["provenance"]:
        audit = reader.read(pinned(api, reader, proof["actual_audit_ref"], PREFIX))
        wanted.append({"kind": "ROLE", "role": proof["role"], "actor_id": proof["actor_id"],
                       "audit_ref": proof["actual_audit_ref"], **{name: audit[name] for name in
                       ("original_capture_ref", "source_line_offsets", "original_line_sha256",
                        "source_prefix_size_observed")}})
        api.require(audit["source_audit_path"] == OLD_LOG and audit["Root_thread_id"] == OLD_THREAD,
                    "CORRECTION_ROLE_BINDING", "historical original source")
    capture = reader.read(pinned(api, reader, issuance["delivery_ref"]))
    wanted.append({"kind": "FORMAL_DELIVERY", "audit_ref": issuance["delivery_ref"],
                   **{name: capture[name] for name in ("original_capture_ref", "source_line_offsets",
                                                     "original_line_sha256", "source_prefix_size_observed")}})
    api.require(capture["source_audit_path"] == OLD_LOG and capture["Root_thread_id"] == OLD_THREAD
                and cert["audit_bindings"] == wanted and len(wanted) == 6,
                "CORRECTION_AUDIT_BINDINGS", "all five roles and formal delivery")
    for binding in wanted:
        _triplet(api, reader, binding)
    api.require(cert["old_profile_ref"] == {"path": PROFILE_PATH, "sha256": PROFILE_OLD_SHA}
                and cert["old_profile_ref"] in context["version_vector"]["source_files"]
                and cert["new_profile_ref"]["path"] == PROFILE_PATH
                and cert["index_ref"] == {"path": INDEX_PATH, "sha256": INDEX_SHA}
                and cert["verifier_module_ref"]["path"] == MODULE_PATH,
                "CORRECTION_INTERPRETER_SCOPE", "only W09 profile transition; index unchanged")
    api.fields(cert["new_profile_ref"], ("path", "sha256"), label="new profile pin")
    api.require(cert["old_profile_archive_ref"]["sha256"] == PROFILE_OLD_SHA,
                "CORRECTION_OLD_PROFILE", "original interpreter preserved")
    pinned(api, reader, cert["old_profile_archive_ref"], PREFIX)
    reader.ref(cert["index_ref"])
    pinned(api, reader, cert["original_failure_ref"], PREFIX)
    return role_registry


def _review_delivery(api, reader, cert_ref, review_ref, review, delivery_ref):
    capture = reader.read(pinned(api, reader, delivery_ref, PREFIX))
    api.fields(capture, ("schema", "source_audit_path", "thread_id", "original_capture_ref",
                         "source_line_offsets", "original_line_sha256"), label="current review capture")
    api.require(capture["schema"] == "researchos.w09.correction-review-delivery.v1"
                and capture["source_audit_path"] == CURRENT_LOG and capture["thread_id"] == CURRENT_THREAD,
                "CORRECTION_CURRENT_DELIVERY", "real current chat only")
    raw = pinned(api, reader, capture["original_capture_ref"], PREFIX).read_bytes()
    lines = raw.splitlines(keepends=True)
    offsets, hashes = capture["source_line_offsets"], capture["original_line_sha256"]
    api.require(len(lines) == len(offsets) == len(hashes) == 3 and offsets[0] == 0
                and offsets == sorted(set(offsets)) and all(type(n) is int and n >= 0 for n in offsets)
                and all(line.endswith(b"\n") for line in lines) and digest(lines[0]) == CURRENT_HEADER_SHA,
                "CORRECTION_CURRENT_DELIVERY", "current source ranges")
    header, meta, message = [api.strict_json(line) for line in lines]
    payload = message.get("payload", {})
    api.require(header.get("type") == "session_meta" and header.get("ordinal") == 0
                and header.get("payload", {}).get("id") == CURRENT_THREAD
                and meta.get("type") == "inter_agent_communication_metadata"
                and type(meta.get("ordinal")) is int and message.get("ordinal") == meta["ordinal"] + 1
                and meta.get("timestamp") == message.get("timestamp")
                and message.get("type") == "response_item" and payload.get("type") == "agent_message"
                and payload.get("author") == review["reviewer_id"] and payload.get("recipient") == "/root"
                and message.get("metadata", {}).get("client_authored") is False
                and type(payload.get("id")) is str and bool(payload["id"]),
                "CORRECTION_CURRENT_DELIVERY", "actual non-author peer delivery")
    content = payload.get("content")
    api.require(type(content) is list and len(content) == 1 and type(content[0]) is dict
                and set(content[0]) == {"type", "text"} and content[0]["type"] == "input_text"
                and type(content[0]["text"]) is str
                and cert_ref["sha256"] in content[0]["text"]
                and review_ref["sha256"] in content[0]["text"]
                and "ACCEPTED_RECOVERY_SOURCE_ONLY" in content[0]["text"]
                and api.stamp(review["issued_at"], "source review issued")
                    <= api.stamp(message["timestamp"], "source review delivered"),
                "CORRECTION_CURRENT_DELIVERY", "exact certificate and review binding")
    with Path(CURRENT_LOG).open("rb") as stream:
        for offset, expected, line in zip(offsets, hashes, lines):
            stream.seek(offset)
            observed = stream.readline()
            api.require(observed == line and digest(observed) == expected,
                        "CORRECTION_CURRENT_DELIVERY", "original current-chat bytes")
            reader.w09_audit_ranges.append({"path": CURRENT_LOG, "offset": offset,
                                            "bytes": len(observed), "sha256": expected})


def review_claim(api, cert, certificate_ref, roles, review):
    """Claim validation is separate from mandatory actual-delivery authentication."""
    api.fields(review, ("schema", "scope", "decision", "reviewer_id", "author_id", "issued_at",
                        "certificate_ref", "checks", "evidence_refs"), label="independent source review")
    excluded = {AUTHOR, "/root", *[x.casefold().removeprefix("codex:") for x in
                                   [*roles["roles"]["source_authors"], roles["roles"]["executor"],
                                    roles["roles"]["assembler"]]]}
    api.text(review["reviewer_id"], "current independent reviewer")
    api.require(review["schema"] == "researchos.w09.correction-independent-review.v1"
                and review["scope"] == "INTERPRETER_RECOVERY_ONLY"
                and review["decision"] == "ACCEPTED_RECOVERY_SOURCE_ONLY"
                and review["author_id"] == AUTHOR
                and review["reviewer_id"].casefold().removeprefix("codex:") not in excluded
                and review["certificate_ref"] == certificate_ref
                and type(review["checks"]) is dict and set(review["checks"]) == REVIEW_CHECKS
                and all(x == "PASS" for x in review["checks"].values())
                and api.stamp(cert["created_at"], "candidate created")
                    <= api.stamp(review["issued_at"], "source review issued"),
                "CORRECTION_REVIEW", "non-author source-only acceptance")


def authorize(api, reader, authority, roots):
    """Called only by the fixed profile after loading a Canon-pinned module."""
    api.fields(authority, ("schema", "certificate_ref", "verifier_module_ref", "review_ref", "delivery_ref"),
               label="Root correction authority")
    api.require(authority["schema"] == "researchos.w09.header-correction-authority.v1",
                "CORRECTION_AUTHORITY", "explicit Root registration")
    cert = reader.read(pinned(api, reader, authority["certificate_ref"], PREFIX))
    roles = certificate_evidence(api, reader, cert, roots)
    api.require(authority["verifier_module_ref"] == cert["verifier_module_ref"],
                "CORRECTION_MODULE", "reviewed module binding")
    pinned(api, reader, cert["verifier_module_ref"])
    reader.ref(cert["new_profile_ref"])
    review = reader.read(pinned(api, reader, authority["review_ref"], PREFIX))
    review_claim(api, cert, authority["certificate_ref"], roles, review)
    for ref in api.sequence(review["evidence_refs"], "actual source review evidence"):
        pinned(api, reader, ref, PREFIX)
    _review_delivery(api, reader, authority["certificate_ref"], authority["review_ref"],
                     review, authority["delivery_ref"])
    return cert
