"""Standalone Root registration/caller proposal for the separate old21 build.

Import does not register, open native APIs or start a child. Future Canon refs,
old21 Source qualification and external Root review captures are runtime inputs.
"""
from __future__ import annotations
import copy
from datetime import datetime, timezone
import hashlib
import json
import ntpath
from pathlib import Path
import re
import sys
import types

R = Path("D:/作品集/ResearchOS/research-os")
V = R / "execution/v2.4"
B = V / "receipts/W05/W05-99"
N = Path(__file__).resolve().parent
CANON = [V / (x + ".json") for x in ("checkpoint", "path_ownership", "step_state", "commands")]
ROOT = "codex:/root"
ROOT_THREAD = "01a11007-5233-7ca1-b71f-9e9e5ce84c98"
CALLER_AUTHOR = "codex:/root/backup_regression_resources"
BUILDER_AUTHOR = "codex:/root/native_temp_independent_review"
AUTHOR = CALLER_AUTHOR
SLICE = "HISTORICAL_SCHEMA21_PROGRAMME_BUILD"
KEY = "schema21_programme_build"
STATE = "ROOT_REGISTERED_PENDING_SCHEMA21_BUILD"
PHASES = ("prepare", "go-version", "control-declared", "control-export", "control-build", "control-inspect", "backup-declared", "backup-export", "backup-build", "backup-inspect", "complete")
GUARD_REF = {"path": (B / "source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py").as_posix(), "sha256": "e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85", "bytes": 11404}
TP_REF = {"path": (B / "mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py").as_posix(), "sha256": "094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9", "bytes": 6877}
BUILDER_SOURCE_REFS = {'hdf': {'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\schema21_programme_builder_source_codex\\main21b-20261010-01\\HDF.json', 'sha256': '355407c30d1d0081a5fac90d32e8c7c47f95ddb0d56681768d8688bf2684ef84', 'bytes': 3255}, 'mf': {'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\schema21_programme_builder_source_codex\\main21b-20261010-01\\MF.json', 'sha256': '6e40bbe378edf370ac8cb870f581d76cd8b48b3c127534855068787c66188069', 'bytes': 103057}, 'builder_ref': {'path': 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/schema21_programme_builder_source_codex/main21b-20261010-01/old21_builder.py', 'sha256': 'b590cc502c90408f3c5b91332982a31acfec09ac279a5e0ebcc417d0a91ae320', 'bytes': 27200}, 'contract_ref': {'path': 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/schema21_programme_builder_source_codex/main21b-20261010-01/contract.v2.json', 'sha256': '1472e40c8806dcb82de62352378c306077fef8e674925b57941f305527bf4402', 'bytes': 22410}, 'input_manifest_ref': {'path': 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/schema21_programme_builder_source_codex/main21b-20261010-01/input-manifest.json', 'sha256': 'bfa48741c773883c11a31f75dc58a6ee9c2d295dfc47dc7218e418e6f6cfc0b0', 'bytes': 5281064}, 'frozen_source_manifest_ref': {'path': 'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/schema21_programme_builder_source_codex/main21b-20261010-01/frozen-source-manifest.json', 'sha256': '054a3814fcfbb3561f8c1264726c17e85ad999cf4300bd5b802fa51cb1c13943', 'bytes': 162891}}
_guard_module = None


def need(ok, code):
    if not ok:
        raise ValueError(code)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def strict(raw):
    def pairs(rows):
        result = {}
        for k, v in rows:
            need(k not in result, "DUPLICATE_JSON_KEY")
            result[k] = v
        return result
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: need(False, "NONFINITE_NUMBER"))


def guard_primitives():
    global _guard_module
    if _guard_module is None:
        raw = Path(GUARD_REF["path"]).read_bytes()
        need(len(raw) == GUARD_REF["bytes"] and hashlib.sha256(raw).hexdigest() == GUARD_REF["sha256"], "GUARD_BOOTSTRAP_PIN")
        module = types.ModuleType("old21_existing_guard")
        module.__file__ = GUARD_REF["path"]
        exec(compile(raw, module.__file__, "exec"), module.__dict__)
        _guard_module = module
    return _guard_module


def canonical(path):
    return guard_primitives()._canonical(path)


def shape(ref):
    need(type(ref) is dict and set(ref) == {"path", "sha256", "bytes"}, "EXACT_THREE_KEY_REF")
    canonical(ref["path"])
    need(type(ref["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", ref["sha256"]) is not None and type(ref["bytes"]) is int and 0 <= ref["bytes"] <= 512 * 1024 * 1024, "REF_PIN_SHAPE")
    return ref


def same_ref(left, right):
    shape(left); shape(right)
    return canonical(left["path"]) == canonical(right["path"]) and left["sha256"] == right["sha256"] and left["bytes"] == right["bytes"]


def physical(path):
    lexical = canonical(str(path)); p = Path(path)
    need(p.is_absolute() and not p.is_symlink() and not p.is_junction(), "REGULAR_PHYSICAL_PATH_REQUIRED")
    resolved = p.resolve(strict=True)
    need(resolved.is_file() and not resolved.is_symlink() and not resolved.is_junction() and canonical(str(resolved)) == lexical, "REPARSE_ALIAS_PROHIBITED")
    return resolved


def pin(path):
    p = physical(path); raw = p.read_bytes()
    return {"path": str(p), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def checked(ref):
    shape(ref); p = physical(ref["path"]); raw = p.read_bytes()
    need(len(raw) == ref["bytes"] and hashlib.sha256(raw).hexdigest() == ref["sha256"], "REF_BYTES_CHANGED")
    return raw


def doc(ref):
    return strict(checked(ref))


def load(ref, name):
    module = types.ModuleType(name); module.__file__ = ref["path"]
    exec(compile(checked(ref), module.__file__, "exec"), module.__dict__)
    return module


def save(path, value):
    with Path(path).open("xb") as stream:
        stream.write(encoded(value)); stream.flush()
    return pin(path)


def when(value):
    need(type(value) is str, "UTC_TIME_REQUIRED")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    need(result.tzinfo is not None, "TIMEZONE_REQUIRED")
    return result


def local_refs(refs, excluded=()):
    excluded = {canonical(str(p)) for p in excluded}; unique = {}
    for ref in refs:
        checked(ref); key = canonical(ref["path"])
        if key in excluded:
            continue
        need(key not in unique or same_ref(unique[key], ref), "CONFLICTING_REF")
        unique.setdefault(key, ref)  # Preserve the exact original Source spelling.
    return list(unique.values())


def manifest(ref):
    value = doc(ref)
    need(type(value.get("members")) is list and value["members"], "MANIFEST_MEMBERS_REQUIRED")
    for member in value["members"]:
        checked(member)
    return value



def validate_builder_chain(review_refs, review, review_mf, decision, source, source_mf, contract):
    need(type(review_refs) is dict and set(review_refs) == {"hdf", "mf", "decision"}, "EXACT_BUILDER_REVIEW_REFS")
    need(review.get("status") == "SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION" and decision.get("verdict") == "SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION", "BUILDER_SOURCE_NOT_ACCEPTED")
    reviewer = decision.get("review_author")
    need(type(reviewer) is str and re.fullmatch(r"codex:/root/[a-z0-9_]+", reviewer) and reviewer not in (ROOT, CALLER_AUTHOR, BUILDER_AUTHOR) and reviewer == review.get("review_author") and decision.get("source_author") == review.get("source_author") == BUILDER_AUTHOR and decision.get("independent_non_author") is True, "BUILDER_NONAUTHOR_REQUIRED")
    need(same_ref(review["decision_ref"], review_refs["decision"]) and same_ref(review["manifest_ref"], review_refs["mf"]) and any(same_ref(review_refs["decision"], x) for x in review_mf["members"]), "BUILDER_REVIEW_CHAIN")
    for field, key in (("author_hdf_ref", "hdf"), ("author_mf_ref", "mf")):
        need(same_ref(decision[field], review[field]) and same_ref(decision[field], BUILDER_SOURCE_REFS[key]), "BUILDER_AUTHOR_REF_MISMATCH")
    need(source.get("source_author") == BUILDER_AUTHOR and same_ref(source["manifest_ref"], BUILDER_SOURCE_REFS["mf"]), "BUILDER_SOURCE_AUTHOR")
    for field, decision_field in (("builder_ref", "author_builder_ref"), ("contract_ref", "author_contract_ref"), ("input_manifest_ref", "author_input_manifest_ref")):
        need(same_ref(source[field], decision[decision_field]) and same_ref(source[field], BUILDER_SOURCE_REFS[field]) and any(same_ref(source[field], member) for member in source_mf["members"]), "BUILDER_SOURCE_HDF_CHAIN")
    need(same_ref(source["frozen_source_manifest_ref"], BUILDER_SOURCE_REFS["frozen_source_manifest_ref"]), "FROZEN_SCHEMA21_SOURCE_REQUIRED")
    need(same_ref(contract["builder_ref"], source["builder_ref"]) and same_ref(contract["input_manifest_ref"], source["input_manifest_ref"]) and same_ref(contract["frozen_source_manifest_ref"], source["frozen_source_manifest_ref"]) and contract.get("schema") == "researchos.old21-programme-builder-contract.v2" and contract.get("schema_version") == 21 and contract.get("source_author") == BUILDER_AUTHOR and contract.get("source_commit") == "f6e4a0ed54d697c7214a75743cd1b83dc3685ddb" and contract.get("historical_source_file_count") == 272, "BUILDER_CONTRACT_CHAIN")
    sql = contract["runtime_source_refs"]
    numbered = [k for k in sql if k.startswith("migrations/sqlite/") and k.endswith(".sql")]
    need(all(re.fullmatch(r"migrations/sqlite/[0-9]{4}_[^/]+\.sql", k) for k in numbered) and sorted(int(Path(k).name[:4]) for k in numbered) == list(range(1, 22)), "EXACT_SCHEMA21_NUMBERED_SQL")
    need(contract.get("phases") == list(PHASES), "DUAL_CONTROL_BACKUP_PHASE_CONTRACT")
    need(decision.get("formal_programme_qualification") is False and decision.get("candidate_program_ref") is None and decision.get("qualification_ref") is None and decision.get("formal_acceptance") is False and decision.get("execution_grant", False) is False, "SOURCE_REVIEW_NOT_PROGRAMME_QUALIFICATION")
    return True



def builder_chain(review_refs, witness_ref):
    need(type(review_refs) is dict and set(review_refs) == {"hdf", "mf", "decision"}, "EXACT_BUILDER_REVIEW_REFS")
    review = doc(review_refs["hdf"]); review_mf = manifest(review_refs["mf"]); decision = doc(review_refs["decision"])
    source = doc(BUILDER_SOURCE_REFS["hdf"]); source_mf = manifest(BUILDER_SOURCE_REFS["mf"]); contract = doc(source["contract_ref"])
    validate_builder_chain(review_refs, review, review_mf, decision, source, source_mf, contract)
    witness = doc(witness_ref)
    need(witness.get("schema") == "researchos.root-old21-builder-review-witness.v1" and witness.get("issued_by") == ROOT and witness.get("root_thread_id") == ROOT_THREAD and witness.get("review_author") == decision["review_author"], "ROOT_BUILDER_REVIEW_WITNESS")
    need(type(witness.get("review_refs")) is dict and set(witness["review_refs"]) == set(review_refs) and all(same_ref(witness["review_refs"][k], review_refs[k]) for k in review_refs), "BUILDER_REVIEW_WITNESS_REFS")
    capture = doc(witness["capture_binding_ref"])
    validate_root_capture(capture, checked(capture["original_capture_ref"]), list(review_refs.values()), "BUILDER_SOURCE_REVIEW_WITNESS", decision["review_author"])
    need(when(review["reviewed_utc"]) <= when(capture["tool_result_timestamp"]) <= when(witness["created_utc"]) <= datetime.now(timezone.utc), "BUILDER_REVIEW_WITNESS_TIME_ORDER")
    inputs = doc(source["input_manifest_ref"])
    need(type(inputs.get("items")) is list and inputs["items"], "BUILDER_SOURCE_INPUTS_REQUIRED")
    peer = doc(capture["peer_delivery_binding_ref"])
    refs = list(BUILDER_SOURCE_REFS.values()) + list(review_refs.values()) + source_mf["members"] + review_mf["members"] + [x["ref"] for x in inputs["items"]]
    refs += [witness_ref, witness["capture_binding_ref"], capture["original_capture_ref"], capture["peer_delivery_binding_ref"], peer["original_capture_ref"]]
    refs += [contract[k] for k in ("common_builder_ref", "common_source_review_ref", "base_helper_ref", "source_guard_ref", "owned_job_ref", "toolchain_lock_ref", "go_ref")]
    return {"review": review, "decision": decision, "source": source, "contract": contract, "refs": refs, "review_refs": review_refs}


ROOT_AUDIT_LOG = "C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl"
CAPTURE_RESULT_SCHEMA = "researchos.root-old21-capture-result.v2"
CAPTURE_OPERATIONS = {"SOURCE_REVIEW_WITNESS", "POSTREVIEW_CURRENT_FOUR", "ACTIVATION_FACTS_CURRENT_FOUR", "RUNTIME_QUALIFICATION_ISSUANCE", "BUILDER_SOURCE_REVIEW_WITNESS", "OLD21_BUILD_PREREQUISITES"}


def structured_documents(value):
    """Decode complete JSON values/lines, never digest-containing substrings."""
    values = []
    def visit(item, depth):
        need(depth <= 24, "CAPTURE_STRUCTURE_DEPTH")
        if type(item) is dict:
            values.append(item)
            for child in item.values(): visit(child, depth + 1)
        elif type(item) is list:
            for child in item: visit(child, depth + 1)
        elif type(item) is str:
            texts = [item] + item.splitlines() if "\n" in item else [item]
            seen = set()
            for text in texts:
                text = text.strip()
                if text in seen or not text.startswith(("{", "[")): continue
                seen.add(text)
                try: parsed = strict(text)
                except (ValueError, TypeError): continue
                if type(parsed) in (dict, list): visit(parsed, depth + 1)
    visit(value, 0)
    return values


def exact_ref_set(refs):
    need(type(refs) is list and refs, "CAPTURE_COMPLETE_REFS_REQUIRED")
    result = []
    for ref in refs:
        shape(ref)
        result.append((canonical(ref["path"]), ref["sha256"], ref["bytes"]))
    need(len(set(result)) == len(result), "CAPTURE_DUPLICATE_REFS")
    return set(result)


def original_capture_rows(binding, raw, peer=False):
    need(type(binding) is dict and binding.get("schema") == ("researchos.root-actual-peer-capture-binding.v2" if peer else "researchos.root-actual-tool-capture-binding.v1")
         and binding.get("issued_by") == ROOT and binding.get("root_thread_id") == ROOT_THREAD, "EXTERNAL_ROOT_CAPTURE_IDENTITY")
    lines = raw.splitlines(keepends=True)
    need(len(lines) == 3 and len(raw) <= 32 * 1024 * 1024 and all(x.endswith(b"\n") for x in lines), "EXTERNAL_CAPTURE_BOUNDS")
    need([hashlib.sha256(x).hexdigest() for x in lines] == binding.get("original_line_sha256")
         and [len(x) for x in lines] == binding.get("source_line_bytes"), "EXTERNAL_CAPTURE_LINE_PINS")
    need(same_ref(binding.get("original_capture_ref"), dict(binding["original_capture_ref"], sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))), "EXTERNAL_CAPTURE_RAW_PIN")
    rows = [strict(x) for x in lines]
    need(all(type(x) is dict for x in rows) and rows[0].get("type") == "session_meta"
         and type(rows[0].get("ordinal")) is int and rows[0]["ordinal"] == 0
         and type(rows[0].get("payload")) is dict and rows[0]["payload"].get("id") == ROOT_THREAD, "EXTERNAL_ROOT_SESSION_REQUIRED")
    offsets = binding.get("source_line_offsets")
    prefix = binding.get("source_prefix_size_observed")
    need(binding.get("source_audit_path") == ROOT_AUDIT_LOG
         and type(offsets) is list and len(offsets) == 3 and offsets[0] == 0
         and all(type(x) is int and x >= 0 for x in offsets) and offsets == sorted(set(offsets))
         and type(prefix) is int and prefix > 0, "EXTERNAL_ORIGINAL_SOURCE_REQUIRED")
    with Path(ROOT_AUDIT_LOG).open("rb") as stream:
        for offset, line in zip(offsets, lines):
            need(offset + len(line) <= prefix, "EXTERNAL_ORIGINAL_SOURCE_REQUIRED")
            stream.seek(offset)
            need(stream.readline() == line, "EXTERNAL_ORIGINAL_SOURCE_BYTES")
    first, last = rows[1:]
    need(type(first.get("ordinal")) is int and first["ordinal"] > 0
         and type(last.get("ordinal")) is int and last["ordinal"] > first["ordinal"]
         and type(first.get("payload")) is dict and type(last.get("payload")) is dict, "COMPLETE_EXTERNAL_ROOT_PAIR_REQUIRED")
    need(when(last.get("timestamp")) >= when(first.get("timestamp")), "EXTERNAL_PAIR_TIME_ORDER")
    return first, last


def validate_peer_delivery(binding_ref, expected_refs, peer_actor, operation):
    need(type(peer_actor) is str and re.fullmatch(r"codex:/root/[a-z0-9_]+", peer_actor)
         and peer_actor not in (ROOT, CALLER_AUTHOR, BUILDER_AUTHOR), "ACTUAL_NONAUTHOR_PEER_REQUIRED")
    binding = doc(binding_ref)
    first, last = original_capture_rows(binding, checked(binding["original_capture_ref"]), peer=True)
    payload = last["payload"]
    need(first.get("type") == "inter_agent_communication_metadata" and type(first["payload"].get("trigger_turn")) is bool
         and last.get("type") == "response_item" and last["ordinal"] == first["ordinal"] + 1
         and first.get("timestamp") == last.get("timestamp") and payload.get("type") == "agent_message"
         and payload.get("author") == peer_actor.removeprefix("codex:") and payload.get("recipient") == "/root"
         and type(last.get("metadata")) is dict and last["metadata"].get("client_authored") is False
         and type(payload.get("content")) is list and len(payload["content"]) == 1
         and type(payload["content"][0]) is dict and set(payload["content"][0]) == {"type", "text"}
         and payload["content"][0]["type"] == "input_text" and type(payload["content"][0]["text"]) is str,
         "ACTUAL_PEER_DELIVERY_REQUIRED")
    text = payload["content"][0]["text"]
    envelope = "Message Type: FINAL_ANSWER\nTask name: /root\nSender: " + peer_actor.removeprefix("codex:") + "\nPayload:\n"
    try:
        delivered = strict(text[len(envelope):] if text.startswith(envelope) else text)
    except (ValueError, TypeError):
        need(False, "PEER_TYPED_DELIVERY_REQUIRED")
    need(type(delivered) is dict and delivered.get("schema") == "researchos.old21-peer-review-delivery.v2",
         "PEER_TYPED_DELIVERY_REQUIRED")
    need(delivered.get("review_author") == peer_actor and delivered.get("root_thread_id") == ROOT_THREAD
         and delivered.get("operation") == operation and delivered.get("verdict") == "ACCEPTED_SOURCE_ONLY"
         and delivered.get("formal_acceptance") is False and delivered.get("execution_grant") is False
         and exact_ref_set(delivered.get("review_refs")) == exact_ref_set(expected_refs), "PEER_REVIEW_REF_BINDING")
    need(binding.get("peer_actor") == peer_actor and binding.get("message_id") == payload.get("id")
         and type(payload.get("id")) is str and payload["id"]
         and binding.get("received_at") == last["timestamp"], "PEER_ORIGINAL_IDENTITY")
    return binding, when(last["timestamp"])


def validate_root_capture(binding, raw, expected_refs, operation=None, peer_actor=None):
    """Three actual Root records, typed return provenance and complete exact refs."""
    first, last = original_capture_rows(binding, raw)
    need(operation in CAPTURE_OPERATIONS and binding.get("operation") == operation, "EXTERNAL_CAPTURE_OPERATION")
    call, output = first["payload"], last["payload"]
    call_id = binding.get("original_call_id")
    need(type(call_id) is str and call_id, "EXTERNAL_CALL_ID_REQUIRED")
    need(first.get("type") == last.get("type") == "response_item"
         and call.get("type") in ("custom_tool_call", "function_call")
         and output.get("type") in ("custom_tool_call_output", "function_call_output")
         and call.get("call_id") == output.get("call_id") == call_id
         and call.get("name") in {"exec", "functions.exec", "exec_command", "functions.exec_command"}
         and (call.get("name") in {"exec_command", "functions.exec_command"} or (type(call.get("input", call.get("arguments"))) is str and "tools.exec_command" in call.get("input", call.get("arguments"))))
         and type(call.get("input", call.get("arguments"))) is str
         and "OLD21_CAPTURE_OPERATION:" + operation in call.get("input", call.get("arguments"))
         and output.get("output"), "COMPLETE_EXTERNAL_ROOT_PAIR_REQUIRED")
    need(binding.get("tool_call_timestamp") == first["timestamp"]
         and binding.get("tool_result_timestamp") == last["timestamp"], "EXTERNAL_PAIR_ORIGINAL_TIMESTAMPS")
    hosts = [x for x in structured_documents(output["output"]) if type(x.get("chunk_id")) is str and x.get("chunk_id")
             and type(x.get("exit_code")) is int and x.get("exit_code") == 0 and type(x.get("output")) is str]
    need(len(hosts) == 1, "EXPECTED_ACTUAL_EXEC_HOST_RESULT")
    result_docs = [x for x in structured_documents(hosts[0]["output"]) if x.get("schema") == CAPTURE_RESULT_SCHEMA]
    need(len(result_docs) == 1, "EXPECTED_TYPED_ROOT_CAPTURE_RESULT")
    observed = result_docs[0]
    need(observed.get("issued_by") == observed.get("observer_actor") == ROOT
         and observed.get("root_thread_id") == ROOT_THREAD and observed.get("operation") == operation
         and observed.get("source") == "tools.exec_command" and observed.get("formal_acceptance") is False
         and exact_ref_set(observed.get("observed_refs")) == exact_ref_set(expected_refs), "EXTERNAL_PAIR_DOES_NOT_BIND_REVIEW_REFS")
    if peer_actor is not None:
        need(observed.get("peer_actor") == peer_actor and binding.get("peer_delivery_binding_ref") is not None,
             "ACTUAL_NONAUTHOR_PEER_REQUIRED")
        _, received = validate_peer_delivery(binding["peer_delivery_binding_ref"], expected_refs, peer_actor, operation)
        need(received <= when(first["timestamp"]), "ROOT_WITNESS_PRECEDES_PEER_DELIVERY")
    else:
        need(observed.get("peer_actor") is None, "EXTERNAL_CAPTURE_ACTOR_CONTEXT")
    return True


def runtime_review_chain(qualification_ref, qualification, contract):
    need(qualification.get("schema") == "researchos.root-old21-qualified-runtime.v2"
         and qualification.get("root_thread_id") == ROOT_THREAD and qualification.get("issued_by") == ROOT,
         "QUALIFIED_RUNTIME_ACTUAL_REVIEW_CHAIN_REQUIRED")
    payload = doc(qualification["payload_ref"])
    projected = {k: v for k, v in qualification.items() if k not in {"payload_ref", "root_issuance_binding_ref", "schema", "created_utc"}}
    need(payload.get("schema") == "researchos.root-old21-runtime-qualification-payload.v2"
         and {k: v for k, v in payload.items() if k != "schema"} == projected, "QUALIFICATION_PAYLOAD_EXACT_BINDING")
    author = qualification.get("review_author")
    need(type(author) is str and re.fullmatch(r"codex:/root/[a-z0-9_]+", author)
         and author not in (ROOT, CALLER_AUTHOR, BUILDER_AUTHOR), "QUALIFIED_RUNTIME_REVIEW_REQUIRED")
    source_ref, source_mf_ref = qualification["source_hdf_ref"], qualification["source_mf_ref"]
    source, source_mf = doc(source_ref), manifest(source_mf_ref)
    need(same_ref(source_ref, pin(N / "HDF.json")) and same_ref(source_mf_ref, pin(N / "MF.json"))
         and source.get("source_author") == CALLER_AUTHOR and same_ref(source["manifest_ref"], source_mf_ref)
         and same_ref(source["caller_ref"], qualification["caller_ref"]) and same_ref(qualification["caller_ref"], pin(__file__))
         and doc(qualification["builder_contract_ref"]) == contract, "RUNTIME_REVIEW_SOURCE_PINS")
    scope_ref = qualification["qualification_scope_ref"]; scope = doc(scope_ref)
    need(scope.get("schema") == "researchos.root-old21-runtime-qualification-scope.v2"
         and scope.get("issued_by") == ROOT and scope.get("root_thread_id") == ROOT_THREAD
         and scope.get("slice_id") == "OLD21_RUNTIME_RESOURCE_QUALIFICATION"
         and scope.get("formal_acceptance") is False and scope.get("execution_grant") is False
         and same_ref(scope["source_hdf_ref"], source_ref) and same_ref(scope["source_mf_ref"], source_mf_ref)
         and same_ref(scope["caller_ref"], qualification["caller_ref"])
         and same_ref(scope["builder_contract_ref"], qualification["builder_contract_ref"])
         and when(scope["lease_expires_at"]) > datetime.now(timezone.utc), "RUNTIME_ROOT_QUALIFICATION_SCOPE")
    review_refs = [qualification[k] for k in ("review_hdf_ref", "review_mf_ref", "review_decision_ref")]
    review, review_mf, decision = doc(review_refs[0]), manifest(review_refs[1]), doc(review_refs[2])
    need(review.get("schema") == "researchos.old21-runtime-independent-review-hdf.v2"
         and review.get("review_author") == decision.get("review_author") == author
         and review.get("source_author") == decision.get("source_author") == CALLER_AUTHOR
         and review.get("builder_source_author") == decision.get("builder_source_author") == BUILDER_AUTHOR
         and review.get("root_thread_id") == decision.get("root_thread_id") == ROOT_THREAD
         and same_ref(review["manifest_ref"], review_refs[1]) and same_ref(review["decision_ref"], review_refs[2])
         and any(same_ref(review_refs[2], ref) for ref in review_mf["members"]), "RUNTIME_REVIEW_HDF_MF_BINDING")
    need(decision.get("schema") == "researchos.old21-runtime-independent-review-decision.v2"
         and decision.get("independent_non_author") is True and decision.get("verdict") == "RUNTIME_CLOSURE_ACCEPTED"
         and decision.get("formal_acceptance") is False and decision.get("execution_grant") is False
         and decision.get("resource_refs") == qualification["resource_refs"]
         and exact_ref_set(decision["resource_refs"]) == exact_ref_set(qualification["resource_refs"]), "RUNTIME_DECISION_BINDING")
    for name, ref in (("source_hdf_ref", source_ref), ("source_mf_ref", source_mf_ref),
                      ("caller_ref", qualification["caller_ref"]), ("builder_contract_ref", qualification["builder_contract_ref"]),
                      ("qualification_scope_ref", scope_ref), ("python_ref", qualification["python_ref"]), ("go_ref", qualification["go_ref"])):
        need(same_ref(review[name], ref) and same_ref(decision[name], ref), "RUNTIME_REVIEW_SOURCE_SCOPE_REFS")
    runtime_manifest_ref = qualification["runtime_manifest_ref"]
    runtime_manifest = doc(runtime_manifest_ref)
    need(runtime_manifest.get("schema") == "researchos.root-old21-runtime-manifest.v1" and runtime_manifest.get("issued_by") == ROOT and runtime_manifest.get("root_thread_id") == ROOT_THREAD and runtime_manifest.get("source_author") == CALLER_AUTHOR and runtime_manifest.get("builder_source_author") == BUILDER_AUTHOR and runtime_manifest.get("formal_acceptance") is False and runtime_manifest.get("execution_grant") is False and exact_ref_set(runtime_manifest["resource_refs"]) == exact_ref_set(qualification["resource_refs"]) and same_ref(decision["runtime_manifest_ref"], runtime_manifest_ref) and same_ref(review["runtime_manifest_ref"], runtime_manifest_ref), "RUNTIME_MANIFEST_INDEPENDENT_BINDING")
    for field, expected in (("source_hdf_ref", source_ref), ("source_mf_ref", source_mf_ref), ("caller_ref", qualification["caller_ref"]), ("builder_contract_ref", qualification["builder_contract_ref"]), ("qualification_scope_ref", scope_ref)):
        need(same_ref(runtime_manifest[field], expected), "RUNTIME_MANIFEST_SOURCE_SCOPE_BINDING")
    peer_binding, received = validate_peer_delivery(qualification["review_hostpair_binding_ref"], review_refs, author,
                                                     "RUNTIME_QUALIFICATION_ISSUANCE")
    root_binding = doc(qualification["root_issuance_binding_ref"])
    expected = [qualification["payload_ref"], scope_ref] + review_refs + [qualification["review_hostpair_binding_ref"]]
    validate_root_capture(root_binding, checked(root_binding["original_capture_ref"]), expected,
                          "RUNTIME_QUALIFICATION_ISSUANCE")
    need(when(scope["created_utc"]) <= when(review["reviewed_utc"]) <= received
         <= when(qualification["payload_created_utc"]) <= when(root_binding["tool_call_timestamp"])
         <= when(root_binding["tool_result_timestamp"]) <= when(qualification["created_utc"])
         <= datetime.now(timezone.utc), "RUNTIME_ORIGINAL_REVIEW_ISSUANCE_TIME_ORDER")
    refs = [runtime_manifest_ref, qualification["payload_ref"], qualification["root_issuance_binding_ref"], root_binding["original_capture_ref"],
            qualification["review_hostpair_binding_ref"], peer_binding["original_capture_ref"], scope_ref,
            source_ref, source_mf_ref, qualification["caller_ref"], qualification["builder_contract_ref"]] + review_refs
    return refs + review_mf["members"] + source_mf["members"]


def own_review(request):
    source = doc(request["source_hdf_ref"]); source_mf = manifest(request["source_mf_ref"])
    review = doc(request["review_hdf_ref"]); review_mf = manifest(request["review_mf_ref"]); decision = doc(request["review_decision_ref"])
    need(source.get("status") == "SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_BINDING" and source.get("source_author") == AUTHOR and same_ref(source["manifest_ref"], request["source_mf_ref"]) and same_ref(source["caller_ref"], pin(__file__)) and same_ref(source["registrar_ref"], pin(__file__)), "CALLER_SOURCE_BINDING")
    for field in ("caller_ref", "contract_ref", "source_inputs_ref"):
        need(any(same_ref(source[field], x) for x in source_mf["members"]), "CALLER_SOURCE_MANIFEST")
    reviewer = decision.get("review_author")
    need(decision.get("verdict") == "SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION" and type(reviewer) is str and reviewer not in ("", ROOT, AUTHOR) and decision.get("source_author") == AUTHOR and decision.get("independent_non_author") is True and decision.get("formal_acceptance") is False and decision.get("execution_grant") is False, "CALLER_NONAUTHOR_REVIEW_REQUIRED")
    for field, expected in (("source_hdf_ref", request["source_hdf_ref"]), ("source_mf_ref", request["source_mf_ref"]), ("caller_ref", source["caller_ref"]), ("registrar_ref", source["registrar_ref"]), ("calling_contract_ref", source["contract_ref"])):
        need(same_ref(decision[field], expected), "CALLER_DECISION_REF_BINDING")
    need(review.get("review_author") == reviewer and review.get("source_author") == AUTHOR and same_ref(review["manifest_ref"], request["review_mf_ref"]) and same_ref(review["source_decision_ref"], request["review_decision_ref"]) and same_ref(review["source_hdf_ref"], request["source_hdf_ref"]) and same_ref(review["source_mf_ref"], request["source_mf_ref"]), "CALLER_REVIEW_HDF_CHAIN")
    need(any(same_ref(request["review_decision_ref"], x) for x in review_mf["members"]), "CALLER_REVIEW_MANIFEST")
    witness = doc(request["review_hostpair_witness_ref"])
    need(witness.get("issued_by") == ROOT and witness.get("schema") == "researchos.root-old21-external-review-witness.v1", "ROOT_REVIEW_WITNESS")
    for field in ("review_hdf_ref", "review_mf_ref", "review_decision_ref"):
        need(same_ref(witness[field], request[field]), "ROOT_REVIEW_WITNESS_BINDING")
    capture = doc(witness["capture_binding_ref"]); raw = checked(capture["original_capture_ref"])
    validate_root_capture(capture, raw, [request[x] for x in ("review_hdf_ref", "review_mf_ref", "review_decision_ref")], "SOURCE_REVIEW_WITNESS", reviewer)
    need(when(capture["tool_result_timestamp"]) >= when(review["reviewed_utc"]) and when(witness["created_utc"]) >= when(capture["tool_result_timestamp"]), "ROOT_REVIEW_WITNESS_NOT_AFTER_REVIEW")
    refs = [request[x] for x in ("source_hdf_ref", "source_mf_ref", "review_hdf_ref", "review_mf_ref", "review_decision_ref", "review_hostpair_witness_ref")]
    refs += source_mf["members"] + review_mf["members"] + [source["source_inputs_ref"], witness["capture_binding_ref"], capture["original_capture_ref"]]
    peer_ref = capture["peer_delivery_binding_ref"]
    refs += [peer_ref, doc(peer_ref)["original_capture_ref"]]
    refs += doc(source["source_inputs_ref"])["references"]
    return {"source": source, "review": review, "reviewer": reviewer, "witness": witness, "refs": refs}


def current_four(expected_refs, expected_revisions):
    need(type(expected_refs) is list and len(expected_refs) == 4 and type(expected_revisions) is dict and set(expected_revisions) == {"checkpoint", "path_ownership", "step_state", "commands"}, "FULL_FOUR_BEFORE_REQUIRED")
    raw, physical_refs, documents = [], [], []
    for expected, target in zip(expected_refs, CANON):
        need(canonical(expected["path"]) == canonical(str(target)), "CANON_TARGET_MISMATCH")
        value = checked(expected); raw.append(value); documents.append(strict(value)); physical_refs.append(pin(target))
    for key, value in zip(("checkpoint", "path_ownership", "step_state", "commands"), documents):
        revision = expected_revisions[key]
        need((revision is None or type(revision) is int) and value.get("revision") == revision, "CURRENT_CANON_REVISION_DRIFT")
    need(expected_revisions["checkpoint"] >= 373 and expected_revisions["path_ownership"] >= 177 and documents[1].get("active_integrator", {}).get("id") == ROOT, "ROOT_CURRENT_CANON_REQUIRED")
    need(all(same_ref(a, b) for a, b in zip(expected_refs, physical_refs)), "CURRENT_CANON_BYTES_DRIFT")
    return {"requested_refs": expected_refs, "physical_refs": physical_refs, "raw": raw, "documents": documents, "revisions": expected_revisions}


def public371_evidence(*args, **kwargs):
    need(False, "PUBLIC22_SCOPE_CANNOT_AUTHORIZE_OLD21")


def future_request(request_ref):
    q = doc(request_ref)
    need(q.get("schema") == "researchos.root-old21-registration-request.v1" and q.get("issued_by") == ROOT and q.get("formal_acceptance") is False, "ROOT_REGISTRATION_REQUEST")
    current = current_four(q["before_canonical_refs"], q["expected_revisions"])
    need("public371_registration_ref" not in q, "PUBLIC22_SCOPE_CANNOT_AUTHORIZE_OLD21")
    source = own_review(q); builder = builder_chain(q["builder_review_refs"], q["builder_review_witness_ref"])
    resume = doc(q["root_resume_ref"]); live = doc(q["postreview_live_ref"])
    for row in (resume, live):
        need(row.get("issued_by") == ROOT and row.get("canonical_refs") == q["before_canonical_refs"] and row.get("expected_revisions") == q["expected_revisions"], "ROOT_REFRESH_CURRENT_FULL_FOUR")
    need(same_ref(live["root_resume_ref"], q["root_resume_ref"]) and same_ref(live["review_decision_ref"], q["review_decision_ref"]) and when(live["created_utc"]) > when(source["review"]["reviewed_utc"]) and when(q["created_utc"]) >= when(live["created_utc"]), "POSTREVIEW_ROOT_REFRESH_REQUIRED")
    need(when(q["lease_expires_at"]) > datetime.now(timezone.utc), "LEASE_EXPIRED")
    case = doc(q["case_request_ref"])
    need(set(case) == {"case_id", "output_root"} and type(case["case_id"]) is str and re.fullmatch("[0-9a-f]{32}", case["case_id"]), "BUILD_CASE_SHAPE")
    parent = B / "integration_codex"
    need(parent.resolve(strict=True) == parent and not parent.is_junction() and not parent.is_symlink(), "OUTPUT_PARENT_PHYSICAL")
    paths = [parent / (prefix + case["case_id"]) for prefix in ("old21-build-", "old21-caller-", "old21-registration-")]
    need(all(not p.exists() for p in paths[:2]) and case["output_root"] == str(paths[0]) and q["caller_receipt_root"] == str(paths[1]) and q["registration_root"] == str(paths[2]), "FRESH_SEPARATE_OUTPUT_ROOTS")
    live_capture = doc(live["capture_binding_ref"])
    validate_root_capture(live_capture, checked(live_capture["original_capture_ref"]), q["before_canonical_refs"], "POSTREVIEW_CURRENT_FOUR")
    need(when(live_capture["tool_result_timestamp"]) > when(source["review"]["reviewed_utc"]), "LIVE_ROOT_CAPTURE_PRECEDES_REVIEW")
    refs = [request_ref, q["root_resume_ref"], q["postreview_live_ref"], q["case_request_ref"], live["capture_binding_ref"], live_capture["original_capture_ref"]] + source["refs"] + builder["refs"]
    return q, current, source, builder, refs


def failure_rows(pending_ref, cp):
    value = doc(pending_ref)
    need(value.get("issued_by") == ROOT and value.get("counter_reset") is False and type(value.get("pending")) is list, "ROOT_PENDING_LEDGER_REQUIRED")
    start = cp["work_in_progress"]["root_next_failure_ordinal_live"]
    need(type(start) is int and [x.get("ordinal") for x in value["pending"]] == list(range(start, value["next_original_failure_ordinal"])), "PENDING_CONTIGUOUS_CURRENT_COUNTER")
    refs = [pending_ref]
    for row in value["pending"]:
        checked(row["origin_ref"]); refs.append(row["origin_ref"])
        need(type(row.get("origin_selector")) is str and row["origin_selector"], "ORIGINAL_SELECTOR_REQUIRED")
        for field in ("actual_outer_exit", "actual_python_exit", "actual_native_exit", "actual_dispatcher_exit", "actual_model_exit"):
            need(field in row and (row[field] is None or type(row[field]) is int), "UNKNOWN_EXIT_NULL_REQUIRED")
        if row.get("capture_binding_ref") is not None:
            binding = doc(row["capture_binding_ref"]); refs.append(row["capture_binding_ref"])
            need(same_ref(binding.get("original_capture_ref", binding.get("actual_capture_ref")), row["origin_ref"]), "ORIGINAL_CAPTURE_BINDING")
    return value, refs


def projection(old_cp, old_ow, scope_ref, owner_ref, worker_ref, facts_ref, owner, worker, pending, created):
    """Pure TP transform. No file open, pin or reference validation in callback."""
    cp = copy.deepcopy(old_cp); ow = copy.deepcopy(old_ow)
    need(KEY not in ow["card_path_bindings"]["W05-99"]["subtasks"] and not any(x.get("slice_id") == SLICE for x in cp["workers"]), "DUPLICATE_BUILD_SLICE")
    need(owner["scope_ref"] == worker["scope_ref"] == scope_ref and worker["selected_owner_ref"] == owner_ref and owner["selected_worker_id"] == worker["worker_id"] == ROOT, "ACYCLIC_OWNER_WORKER")
    ow["card_path_bindings"]["W05-99"]["subtasks"][KEY] = dict(owner, owner_document_ref=owner_ref, worker_document_ref=worker_ref, current_source_writer=None, formal_case_accepted_delta=0, parent_acceptance=False)
    cp["workers"].append(dict(worker, worker_document_ref=worker_ref))
    seen = {(x.get("original_payload", {}).get("immutable_origin_ref", {}).get("sha256"), x.get("original_payload", {}).get("origin_selector")) for x in cp["failure_counters"]}
    for row in pending["pending"]:
        identity = (row["origin_ref"]["sha256"], row["origin_selector"])
        need(identity not in seen, "ORIGINAL_INVOCATION_REUSED"); seen.add(identity)
        payload = {k: copy.deepcopy(v) for k, v in row.items() if k.startswith("actual_")}
        payload.update(observed_ordinal=row["ordinal"], immutable_origin_ref=row["origin_ref"], origin_selector=row["origin_selector"], capture_binding_ref=row.get("capture_binding_ref"), diagnostic=row["description"])
        cp["failure_counters"].append(dict(origin_key=hashlib.sha256((identity[0] + "#" + identity[1]).encode()).hexdigest(), evidence_ref=row["origin_ref"], original_payload=payload, counted_once=True, counter_reset=False, automatic_retry=False))
    cp["work_in_progress"].update(fresh_old21_root_scope_ref=scope_ref, fresh_old21_registration_facts_ref=facts_ref, root_next_failure_ordinal_live=pending["next_original_failure_ordinal"])
    cp["work_in_progress"]["later_diagnostics_observed_after_cutoff"].extend({k: copy.deepcopy(row[k]) for k in ("ordinal", "origin_ref", "description")} for row in pending["pending"])
    cp.update(revision=old_cp["revision"] + 1, expected_previous_revision=old_cp["revision"], updated_at=created, updated_by=ROOT, note="Root registered a separate fresh old21 build slice; candidate programme qualification remains pending.")
    ow.update(revision=old_ow["revision"] + 1, updated_at=created, updated_by=ROOT)
    inverse_cp = copy.deepcopy(cp); inverse_ow = copy.deepcopy(ow)
    for key in ("workers", "failure_counters", "work_in_progress", "revision", "expected_previous_revision", "updated_at", "updated_by", "note"):
        if key in old_cp: inverse_cp[key] = copy.deepcopy(old_cp[key])
        else: inverse_cp.pop(key, None)
    del inverse_ow["card_path_bindings"]["W05-99"]["subtasks"][KEY]
    for key in ("revision", "updated_at", "updated_by"):
        if key in old_ow: inverse_ow[key] = copy.deepcopy(old_ow[key])
        else: inverse_ow.pop(key, None)
    need(encoded(inverse_cp) == encoded(old_cp) and encoded(inverse_ow) == encoded(old_ow), "COMPLETE_INVERSE_PAIR")
    return cp, ow


def propose(request_ref):
    q, current, source, builder, refs = future_request(request_ref)
    pending, _ = failure_rows(q["pending_ref"], current["documents"][0])
    root = Path(q["registration_root"]); need(not root.exists(), "REGISTRATION_ROOT_MUST_BE_NEW"); root.mkdir()
    scope = dict(schema="researchos.root-old21-scope.v1", issued_by=ROOT, slice_id=SLICE, case_request_ref=q["case_request_ref"], registration_request_ref=request_ref, builder_contract_ref=builder["source"]["contract_ref"], builder_ref=builder["source"]["builder_ref"], output_root=doc(q["case_request_ref"])["output_root"], caller_receipt_root=q["caller_receipt_root"], lease_expires_at=q["lease_expires_at"], formal_acceptance=False, parent_acceptance=False)
    scope_ref = save(root / "scope.root.json", scope)
    common = dict(step_id="W05-99", slice_id=SLICE, state=STATE, owner=ROOT, scope_ref=scope_ref, output_root=scope["output_root"], lease_status="ACTIVE", lease_expires_at=q["lease_expires_at"])
    owner = dict(common, owner_id=ROOT, selected_worker_id=ROOT); owner_ref = save(root / "owner.root.json", owner)
    worker = dict(common, worker_id=ROOT, selected_owner_ref=owner_ref); worker_ref = save(root / "worker.root.json", worker)
    archives = []
    for index, raw in enumerate(current["raw"]):
        path = root / (str(index) + ".before.raw.json")
        with path.open("xb") as stream: stream.write(raw)
        archives.append(pin(path))
    facts = dict(schema="researchos.root-old21-registration-facts.v1", issued_by=ROOT, registration_request_ref=request_ref, before_canonical_refs=current["requested_refs"], before_archive_refs=archives, scope_ref=scope_ref, owner_ref=owner_ref, worker_ref=worker_ref, formal_acceptance=False)
    facts_ref = save(root / "facts.root.json", facts)
    after = projection(*current["documents"][:2], scope_ref, owner_ref, worker_ref, facts_ref, owner, worker, pending, q["created_utc"])
    for index, value in enumerate(after): save(root / (str(index) + ".after.proposed.json"), value)
    return facts_ref


def runtime_closure(qualification_ref, contract):
    qualification = doc(qualification_ref)
    need(qualification.get("schema") == "researchos.root-old21-qualified-runtime.v2" and qualification.get("issued_by") == ROOT and qualification.get("independent_non_author") is True and qualification.get("review_author") not in (None, "", ROOT, CALLER_AUTHOR, BUILDER_AUTHOR), "QUALIFIED_RUNTIME_REVIEW_REQUIRED")
    need(qualification.get("status") == "QUALIFIED_FOR_OLD21_BUILD" and qualification.get("formal_programme_qualification") is False, "RUNTIME_QUALIFICATION_STATUS")
    review_refs = runtime_review_chain(qualification_ref, qualification, contract)
    locked = doc(contract["toolchain_lock_ref"]); python = pin(sys.executable)
    need(canonical(contract["go_ref"]["path"]) == canonical(locked["tools"]["go"]["path"]) and contract["go_ref"]["sha256"] == locked["tools"]["go"]["sha256"], "LOCKED_GO_DRIFT")
    need(canonical(python["path"]) == canonical(locked["tools"]["python"]["path"]) and python["sha256"] == locked["tools"]["python"]["sha256"] and same_ref(qualification["python_ref"], python) and same_ref(qualification["go_ref"], contract["go_ref"]), "QUALIFIED_PYTHON_GO_BINDING")
    decision = doc(qualification["review_decision_ref"])
    need(decision.get("review_author") == qualification["review_author"] and decision.get("independent_non_author") is True and decision.get("verdict") == "RUNTIME_CLOSURE_ACCEPTED" and decision.get("resource_refs") == qualification["resource_refs"], "RUNTIME_DECISION_BINDING")
    job = load(contract["owned_job_ref"], "old21_qualified_job")
    required = [python, contract["go_ref"], GUARD_REF, TP_REF, pin(__file__)] + [pin(p) for p in job.runtime_resource_paths()]
    for module in tuple(sys.modules.values()):
        for key in ("__file__", "__cached__"):
            path = getattr(module, key, None)
            if path and Path(path).is_file(): required.append(pin(path))
    qualified = {canonical(x["path"]): x for x in qualification["resource_refs"]}
    need(all(canonical(x["path"]) in qualified and same_ref(x, qualified[canonical(x["path"])]) for x in required), "UNQUALIFIED_LOADED_RUNTIME_RESOURCE")
    return [qualification_ref, contract["toolchain_lock_ref"]] + review_refs + qualification["resource_refs"]


def register(mode, facts_ref, activation_ref=None):
    need(mode in ("check", "activate"), "REGISTRATION_MODE")
    facts = doc(facts_ref); q, current, source, builder, refs = future_request(facts["registration_request_ref"])
    root = Path(q["registration_root"])
    need(same_ref(facts_ref, pin(root / "facts.root.json")) and facts.get("issued_by") == ROOT and facts.get("before_canonical_refs") == current["requested_refs"], "REGISTRATION_FACTS_BINDING")
    scope = doc(facts["scope_ref"]); owner = doc(facts["owner_ref"]); worker = doc(facts["worker_ref"])
    need(same_ref(scope["registration_request_ref"], facts["registration_request_ref"]) and same_ref(scope["case_request_ref"], q["case_request_ref"]) and scope["lease_expires_at"] == q["lease_expires_at"] and scope["slice_id"] == SLICE, "SCOPE_REQUEST_BINDING")
    for row in (owner, worker):
        need(row.get("owner") == ROOT and row.get("slice_id") == SLICE and row.get("lease_expires_at") == scope["lease_expires_at"] and row.get("output_root") == scope["output_root"] and row.get("lease_status") == "ACTIVE" and row.get("state") == STATE, "OWNER_WORKER_SCOPE_BINDING")
    for archive, raw in zip(facts["before_archive_refs"], current["raw"]): need(checked(archive) == raw, "FULL_BEFORE_ARCHIVE_CHANGED")
    need(len(facts["before_archive_refs"]) == 4, "FOUR_RAW_BEFORE_ARCHIVES")
    pending, pending_refs = failure_rows(q["pending_ref"], current["documents"][0])
    if mode == "activate":
        activation = doc(activation_ref)
        need(activation.get("issued_by") == ROOT and same_ref(activation["facts_ref"], facts_ref) and activation.get("before_canonical_refs") == current["requested_refs"] and when(activation["created_utc"]) > when(q["created_utc"]), "FRESH_ROOT_ACTIVATION_REQUIRED")
        capture = doc(activation["capture_binding_ref"])
        validate_root_capture(capture, checked(capture["original_capture_ref"]), [facts_ref] + current["requested_refs"], "ACTIVATION_FACTS_CURRENT_FOUR")
        need(when(capture["tool_result_timestamp"]) > when(q["created_utc"]), "ACTIVATION_CAPTURE_NOT_FRESH")
        refs += [activation_ref, activation["capture_binding_ref"], capture["original_capture_ref"]]
    refs += pending_refs + [facts_ref, facts["scope_ref"], facts["owner_ref"], facts["worker_ref"], GUARD_REF, TP_REF] + facts["before_archive_refs"] + current["physical_refs"][2:]
    tp = load(TP_REF, "old21_pair_transaction")
    refs += runtime_closure(q["runtime_qualification_ref"], builder["contract"])
    held = guard_primitives().SourceReadGuard(per_file_cap=512 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
    transaction = None
    def transform(cp, ow):
        need(cp == current["documents"][0] and ow == current["documents"][1], "EXCLUSIVE_PAIR_DRIFT")
        return projection(cp, ow, facts["scope_ref"], facts["owner_ref"], facts["worker_ref"], facts_ref, owner, worker, pending, q["created_utc"])
    try:
        held.acquire(local_refs(refs, CANON[:2]))
        after = transform(*current["documents"][:2])
        if mode == "activate": transaction = tp.update_pair(current["physical_refs"][:2], transform, root, "activate")
        else: need(all(same_ref(a, pin(p)) for a, p in zip(current["physical_refs"], CANON)), "CHECK_CHANGED_CANON")
        need(all(same_ref(a, pin(p)) for a, p in zip(current["physical_refs"][2:], CANON[2:])), "SS_CM_CHANGED")
    finally:
        cleanup = held.close(); save(root / (mode + ".guard-cleanup.json"), cleanup)
        need(cleanup.get("closed") is True and cleanup.get("retained_handles_count") == 0 and not cleanup.get("errors"), "REGISTRATION_GUARD_CLEANUP")
    return save(root / (mode + ".result.json"), dict(schema="researchos.root-old21-registration-result.v1", mode=mode, facts_ref=facts_ref, scope_ref=facts["scope_ref"], proposed_after_refs=[dict(path=str(p), sha256=hashlib.sha256(encoded(v)).hexdigest(), bytes=len(encoded(v))) for p, v in zip(CANON[:2], after)], transaction=transaction, complete_inverse=True, full_before_archive_refs=facts["before_archive_refs"], SS_CM_unchanged=True, formal_acceptance=False))


def live_lease(actual, require_new=False):
    scope = doc(actual["scope_ref"]); facts = doc(actual["facts_ref"]); q = doc(scope["registration_request_ref"])
    owner = doc(facts["owner_ref"]); worker = doc(facts["worker_ref"])
    need(scope.get("issued_by") == ROOT and scope.get("slice_id") == SLICE and scope.get("formal_acceptance") is False and scope.get("parent_acceptance") is False and same_ref(facts["scope_ref"], actual["scope_ref"]) and same_ref(facts["registration_request_ref"], scope["registration_request_ref"]), "ACTUAL_SCOPE_FACTS_BINDING")
    need(same_ref(actual["case_request_ref"], scope["case_request_ref"]) and same_ref(q["case_request_ref"], scope["case_request_ref"]) and same_ref(worker["selected_owner_ref"], facts["owner_ref"]) and owner["selected_worker_id"] == worker["worker_id"] == ROOT, "ACTUAL_OWNER_WORKER_ACYCLIC")
    expected = dict(q["expected_revisions"])
    expected["checkpoint"] += 1; expected["path_ownership"] += 1
    current = current_four(actual["current_canonical_refs"], expected)
    need(all(same_ref(a, b) for a, b in zip(q["before_canonical_refs"][2:], current["physical_refs"][2:])), "ACTUAL_SS_CM_DRIFT")
    cp, ow = current["documents"][:2]
    need(same_ref(cp["work_in_progress"]["fresh_old21_root_scope_ref"], actual["scope_ref"]) and same_ref(cp["work_in_progress"]["fresh_old21_registration_facts_ref"], actual["facts_ref"]), "CURRENT_BUILD_REGISTRATION")
    task = ow["card_path_bindings"]["W05-99"]["subtasks"][KEY]
    workers = [x for x in cp["workers"] if x.get("slice_id") == SLICE]
    need(len(workers) == 1, "SINGLE_CANON_WORKER_REQUIRED")
    for row in (owner, worker, task, workers[0]):
        need(row.get("step_id") == "W05-99" and row.get("slice_id") == SLICE and row.get("owner") == ROOT and row.get("state") == STATE and row.get("lease_status") == "ACTIVE" and same_ref(row["scope_ref"], actual["scope_ref"]) and row.get("lease_expires_at") == scope["lease_expires_at"] and row.get("output_root") == scope["output_root"], "LIVE_OWNER_WORKER_SCOPE_DRIFT")
    need(same_ref(task["owner_document_ref"], facts["owner_ref"]) and same_ref(task["worker_document_ref"], facts["worker_ref"]) and same_ref(workers[0]["worker_document_ref"], facts["worker_ref"]), "LIVE_DOCUMENT_BINDING")
    need(when(scope["lease_expires_at"]) > datetime.now(timezone.utc), "LIVE_BUILD_LEASE_EXPIRED")
    case = doc(actual["case_request_ref"])
    need(set(case) == {"case_id", "output_root"} and case["output_root"] == scope["output_root"] and scope["caller_receipt_root"] == q["caller_receipt_root"], "LIVE_CASE_BINDING")
    need(Path(case["output_root"]) == B / "integration_codex" / ("old21-build-" + case["case_id"]) and Path(scope["caller_receipt_root"]) == B / "integration_codex" / ("old21-caller-" + case["case_id"]), "LIVE_OUTPUT_ROOT_BINDING")
    if require_new: need(not Path(scope["output_root"]).exists() and not Path(scope["caller_receipt_root"]).exists(), "ACTUAL_OUTPUT_ROOT_ALREADY_USED")
    return scope, facts, q, current



def prebuild_authority(actual, builder, current):
    qualification_ref = actual["runtime_qualification_ref"]
    qualification = doc(qualification_ref)
    need(same_ref(qualification["builder_contract_ref"], builder["source"]["contract_ref"]), "OLD21_QUALIFIED_BUILDER_BINDING")
    binding_ref = actual["prebuild_host_binding_ref"]; binding = doc(binding_ref)
    expected = [actual[k] for k in ("scope_ref", "facts_ref", "registration_result_ref", "runtime_qualification_ref")] + list(builder["review_refs"].values()) + current["physical_refs"]
    validate_root_capture(binding, checked(binding["original_capture_ref"]), expected, "OLD21_BUILD_PREREQUISITES")
    need(when(binding["tool_result_timestamp"]) <= when(actual["created_utc"]) <= datetime.now(timezone.utc), "PREBUILD_PAIR_MUST_ALREADY_BE_COMPLETE")
    return dict(input_manifest_ref=builder["source"]["input_manifest_ref"], source_review_ref=builder["review_refs"]["decision"], resource_qualification_ref=qualification_ref, runtime_manifest_ref=qualification["runtime_manifest_ref"], outer_host_binding_ref=binding_ref, source_author=BUILDER_AUTHOR, reviewer_actor=builder["decision"]["review_author"]), [binding_ref, binding["original_capture_ref"]]


class LiveScope:
    def __init__(self, actual, held, context, resource_binding):
        self.actual = actual; self.held = held; self.context = context; self.resource_binding = copy.deepcopy(resource_binding); self.next_phase = 0

    def require_registered(self, contract_ref, request_ref, source_author):
        need(self.held is not None, "ROOT_RESOURCE_CLOSURE_RELEASED")
        scope, _, _, _ = live_lease(self.actual)
        need(source_author == BUILDER_AUTHOR and same_ref(contract_ref, scope["builder_contract_ref"]) and same_ref(request_ref, self.actual["case_request_ref"]), "REGISTERED_BUILDER_MISMATCH")

    def require_resources(self, contract_ref, input_manifest_ref):
        need(self.held is not None, "ROOT_RESOURCE_CLOSURE_RELEASED")
        scope, _, _, _ = live_lease(self.actual)
        need(same_ref(contract_ref, scope["builder_contract_ref"]) and same_ref(input_manifest_ref, BUILDER_SOURCE_REFS["input_manifest_ref"]), "RESOURCE_CONTRACT_INPUT_MISMATCH")
        binding = self.resource_binding
        need(set(binding) == {"input_manifest_ref", "source_review_ref", "resource_qualification_ref", "runtime_manifest_ref", "outer_host_binding_ref", "source_author", "reviewer_actor"} and binding["source_author"] == BUILDER_AUTHOR and type(binding["reviewer_actor"]) is str and re.fullmatch(r"codex:/root/[a-z0-9_]+", binding["reviewer_actor"]) and binding["reviewer_actor"] not in (ROOT, CALLER_AUTHOR, BUILDER_AUTHOR), "EXACT_ACTUAL_RESOURCE_AUTHORITY")
        for key in ("input_manifest_ref", "source_review_ref", "resource_qualification_ref", "runtime_manifest_ref", "outer_host_binding_ref"): checked(binding[key])
        need(same_ref(binding["input_manifest_ref"], input_manifest_ref) and same_ref(binding["resource_qualification_ref"], self.actual["runtime_qualification_ref"]) and same_ref(binding["outer_host_binding_ref"], self.actual["prebuild_host_binding_ref"]), "ACTUAL_RESOURCE_BINDING_DRIFT")
        return copy.deepcopy(binding)

    def require_phase(self, phase, request_ref, output_root):
        need(self.held is not None, "ROOT_RESOURCE_CLOSURE_RELEASED")
        scope, _, _, _ = live_lease(self.actual)
        need(self.next_phase < len(PHASES) and phase == PHASES[self.next_phase] and same_ref(request_ref, self.actual["case_request_ref"]) and canonical(output_root) == canonical(scope["output_root"]), "BUILD_PHASE_SEQUENCE_OR_SCOPE")
        self.next_phase += 1

    def receipt_context(self):
        need(self.held is not None, "ROOT_RESOURCE_CLOSURE_RELEASED")
        live_lease(self.actual)
        return copy.deepcopy(self.context)


def execute(actual_ref):
    """Actual Root-only future entry. Original outer hostpair is external evidence."""
    actual = doc(actual_ref)
    need(actual.get("schema") == "researchos.root-old21-actual-request.v1" and actual.get("issued_by") == ROOT and actual.get("formal_acceptance") is False, "ROOT_ACTUAL_REQUEST_REQUIRED")
    scope, facts, q, current = live_lease(actual, require_new=True)
    source = own_review(q); builder = builder_chain(q["builder_review_refs"], q["builder_review_witness_ref"])
    need(same_ref(scope["builder_ref"], builder["source"]["builder_ref"]) and same_ref(scope["builder_contract_ref"], builder["source"]["contract_ref"]), "EXACT_ACCEPTED_BUILDER_REQUIRED")
    result = doc(actual["registration_result_ref"])
    need(result.get("schema") == "researchos.root-old21-registration-result.v1" and result.get("mode") == "activate" and result.get("complete_inverse") is True and result.get("SS_CM_unchanged") is True and result.get("formal_acceptance") is False and result.get("transaction") is not None and same_ref(result["facts_ref"], actual["facts_ref"]) and same_ref(result["scope_ref"], actual["scope_ref"]) and all(same_ref(a, b) for a, b in zip(result["proposed_after_refs"], current["physical_refs"][:2])) and len(result["proposed_after_refs"]) == 2, "ACTUAL_REGISTRATION_RESULT_REQUIRED")
    journal = Path(result["transaction"]["transaction_journal"])
    need(journal.parent == Path(q["registration_root"]) and not journal.is_symlink() and not journal.is_junction(), "BUILD_TRANSACTION_JOURNAL_PATH")
    committed_ref = pin(journal / "committed.json"); committed = doc(committed_ref)
    need(committed.get("both_verified_while_exclusively_held") is True and committed.get("written_indices") == [0, 1] and all(same_ref(a, b) for a, b in zip(committed["after_refs"], current["physical_refs"][:2])) and len(committed["after_refs"]) == 2, "BUILD_TRANSACTION_COMMIT_REQUIRED")
    intent = doc(actual["host_call_intent_ref"])
    need(intent.get("issued_by") == ROOT and intent.get("kind") == "ACTUAL_HOST_CALL_INTENT" and intent.get("external_hostpair_required") is True and same_ref(intent["scope_ref"], actual["scope_ref"]) and same_ref(intent["case_request_ref"], actual["case_request_ref"]), "ROOT_FULL_HOSTPAIR_INTENT_REQUIRED")
    # Load the leaf before qualifying all Python/native modules; no child starts on import.
    leaf = load(builder["source"]["builder_ref"], "old21_accepted_builder")
    refs = source["refs"] + builder["refs"] + [actual_ref, actual["scope_ref"], actual["facts_ref"], actual["case_request_ref"], actual["registration_result_ref"], actual["host_call_intent_ref"], scope["registration_request_ref"], facts["owner_ref"], facts["worker_ref"], committed_ref] + current["physical_refs"]
    refs += runtime_closure(actual["runtime_qualification_ref"], builder["contract"])
    resource_binding, prebuild_refs = prebuild_authority(actual, builder, current)
    refs += prebuild_refs
    held = guard_primitives().SourceReadGuard(per_file_cap=512 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
    state = None; error = None; cleanup = None; live = None
    receipt_root = Path(scope["caller_receipt_root"])
    try:
        held.acquire(local_refs(refs))
        live_lease(actual, require_new=True)
        need(receipt_root.parent.resolve(strict=True) == receipt_root.parent and not receipt_root.parent.is_symlink() and not receipt_root.parent.is_junction(), "CALLER_RECEIPT_PARENT_PHYSICAL")
        receipt_root.mkdir()
        live = LiveScope(actual, held, {"root_request_ref": actual_ref, "scope_ref": actual["scope_ref"], "registration_result_ref": actual["registration_result_ref"], "host_call_intent_ref": actual["host_call_intent_ref"], "source_review_ref": builder["review_refs"]["decision"], "caller_source_review_ref": q["review_decision_ref"], "resource_qualification_ref": actual["runtime_qualification_ref"], "runtime_manifest_ref": resource_binding["runtime_manifest_ref"], "prebuild_host_binding_ref": actual["prebuild_host_binding_ref"], "actual_build_hostpair_external_after_return": True}, resource_binding)
        state = leaf.run_registered_build(builder["source"]["contract_ref"], actual["case_request_ref"], live)
        need(live.next_phase == len(PHASES) or bool(state.get("first_failure")), "INCOMPLETE_DUAL_ENTRY_PHASES")
    except BaseException as exc:
        error = {"type": type(exc).__name__, "message": str(exc), "phase": "root_caller", "last_child_exit": None, "original_ordinal": None, "Root_assignment_required": True}
    finally:
        if live is not None: live.held = None
        try:
            cleanup = held.close()
            need(cleanup.get("closed") is True and cleanup.get("retained_handles_count") == 0 and not cleanup.get("errors"), "ROOT_SOURCE_GUARD_CLEANUP_UNCONFIRMED")
        except BaseException as exc:
            if error is None: error = {"type": type(exc).__name__, "message": str(exc), "phase": "root_guard_close", "last_child_exit": None, "original_ordinal": None, "Root_assignment_required": True}
    record = dict(schema="researchos.root-old21-caller-return.v1", actual_request_ref=actual_ref, builder_returned_state=state, caller_error=error, source_guard_cleanup=cleanup, external_original_hostpair_required=True, Root_failure_assignment_required=bool(error or state and state.get("first_failure")), automatic_retry=False, candidate_qualification_ref=None, formal_acceptance=False, parent_acceptance=False)
    if receipt_root.is_dir():
        try:
            if state is not None: record["persisted_builder_state_ref"] = save(receipt_root / "builder-returned-state.root.json", state)
            record["return_record_ref"] = save(receipt_root / "caller-return.root.json", record)
        except BaseException as exc:
            record["persistence_error"] = {"type": type(exc).__name__, "message": str(exc), "original_ordinal": None}
            record["Root_failure_assignment_required"] = True
    record["Root_must_persist_full_return"] = "return_record_ref" not in record
    return record


if __name__ == "__main__":
    need(len(sys.argv) in (5, 8), "USAGE_mode_input_path_sha_bytes_optional_activation_path_sha_bytes")
    mode = sys.argv[1]; first = dict(path=sys.argv[2], sha256=sys.argv[3], bytes=int(sys.argv[4]))
    need(mode in ("propose", "check", "activate", "execute"), "ENTRY_MODE")
    activation = dict(path=sys.argv[5], sha256=sys.argv[6], bytes=int(sys.argv[7])) if len(sys.argv) == 8 else None
    returned = propose(first) if mode == "propose" else execute(first) if mode == "execute" else register(mode, first, activation)
    print(json.dumps(returned, ensure_ascii=False), flush=True)
