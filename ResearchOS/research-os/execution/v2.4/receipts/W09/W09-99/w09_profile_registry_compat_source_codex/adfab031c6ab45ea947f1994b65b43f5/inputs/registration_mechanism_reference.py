"""Prepared Root CP370/OW174 C19 two-dispatcher registrar.

No entry point runs on import. Root alone may later invoke build, check, and
activate after independent Source review. This Source package grants nothing.
"""
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import types

R = Path(r"D:\作品集\ResearchOS\research-os")
N = Path(__file__).resolve().parent
W = R / "execution/v2.4/receipts/W09/W09-99"
B = R / "execution/v2.4/receipts/W05/W05-99"
CANON = [R / "execution/v2.4" / (name + ".json") for name in
         ("checkpoint", "path_ownership", "step_state", "commands")]
BEFORE = (("dd997457f14314374ee4577fff6fd87317e05ad908f4c24d01ce302af72edeb7",4370868),
          ("da777233cf369e433d4db61f75b579cfcd9a3b9f5092f6b7acafc7c3106cc5d2",206009),
          ("fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149",257446),
          ("28b4ba18ce2ab3ce03287651e311ae2bd36293b53fd8c298e5bf1f231f56d027",68968))
BASE = B / "checkpoint_r368_restored21_v2_source_root/cp368-w05v2-20261009/register_cp368.source.py"
GP = B / "source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
TP = B / "mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py"
CALLER_SOURCE_ROOT = W / "w09_main_c19_dispatcher_caller_source_codex"
CALLER_REVIEW_ROOT = W / "main_c19_dispatcher_caller_independent_review_codex"
ROOT = "codex:/root"
AUTHOR = "codex:/root/w09_formal_profile_source_impl"
SLICE = "C19_MAIN_TWO_DISPATCHERS"
KEY = "c19_main_two_dispatchers"
STATE = "ROOT_REGISTERED_PENDING_C19_MAIN_TWO_DISPATCHERS"
ROUTES = ["test.research.fixture", "test.retrieval"]
ROOT_OUTPUT_BOUNDARY = W
ROOT_INPUT_DIR = W / "checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009"
ROOT_PENDING_DIR = W / "checkpoint_r369_native_source_root/cp369-c19-20261009"
CAPTURE_CLASSES = {"SOURCE_RECORDED_ORIGINAL_EVIDENCE",
                   "SOURCE_RECORDED_ORIGINAL_TOOL_IO", "ROOT_RECORDED_ORIGINAL_TOOL_IO",
                   "OBSERVED_TRUNCATED_NOT_FULL", "OBSERVED_NOT_FULL",
                   "VISIBLE_TRANSCRIPTION_NOT_HOST_RAW"}
SOURCE_REVIEW_SCHEMA = "researchos.w09-main-c19-two-dispatchers-independent-source-decision.v1"
SOURCE_SCOPE_SCHEMA = "researchos.w09-c19-main-two-dispatcher-scope.v1"
DESIGNATED_REVIEWER = "codex:/root/native_temp_independent_review"
ROOT_THREAD_ID = "01a11007-5233-7ca1-b71f-9e9e5ce84c98"
V6_SOURCE_HDF_SHA = "8a5c60ca1a8ec12ad273f098091b5ff580de5be8f72ffe38c19afb8ae64ddd78"
V6_SOURCE_MF_SHA = "68e4889942de67e656ebecc5ffab7007109271c482c2f287aac1f312ae71b077"
V6_CALLER_SHA = "f3d044d49980f4399ee91723d9548fd3f856999de38d082b43cd262b025bc9de"
V6_CONTRACT_SHA = "faea1af12742ecfd08285339aba669bd974750a252908c08bed16cf36673802d"
V6_REVIEW_HDF_SHA = "103ec67601f523d545499c8a7d0dc3b16f21d601c8152c232309f916815e0174"
V6_REVIEW_MF_SHA = "0da7ad889c241c41c80ac309b32ea3cfc17e1401ac4a75ca9d32c56050a9a53c"
V6_REVIEW_DECISION_SHA = "0586fb5d30533d656fbfd6d4a4d2741bc1e088cdf34bcac1801af88e500fae26"
EXACT = {
    str(BASE): ("05079c1be355bd7a55bafaa840b278a0030a681b8aef23cb592ff269b3775d03",15197),
    str(GP): ("e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85",11404),
    str(TP): ("094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9",6877),
}


def require(ok, code):
    if not ok: raise ValueError(code)


def decode(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, "DUPLICATE_JSON_KEY")
            value[key] = item
        return value
    def nonfinite(_):
        raise ValueError("NONFINITE_JSON")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def pin(path):
    path = Path(path)
    require(not path.is_symlink(), "PIN_ALIAS")
    path = path.resolve(strict=True)
    raw = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def exact_ref(ref):
    require(type(ref) is dict and set(ref) == {"path", "sha256", "bytes"}, "REF_3_KEYS")
    require(type(ref["path"]) is str and Path(ref["path"]).is_absolute(), "REF_ABSOLUTE")
    require(type(ref["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", ref["sha256"]), "REF_SHA")
    require(type(ref["bytes"]) is int and 0 <= ref["bytes"] <= 256*1024*1024, "REF_BYTES")
    require(pin(ref["path"]) == ref, "REF_CHANGED")
    return ref


def load(ref):
    exact_ref(ref)
    raw = Path(ref["path"]).read_bytes()
    require(len(raw) == ref["bytes"] and hashlib.sha256(raw).hexdigest() == ref["sha256"],
            "REF_CHANGED_AFTER_PIN")
    return decode(raw)


def embedded_refs(value):
    if type(value) is dict:
        if set(value) == {"path", "sha256", "bytes"}:
            yield exact_ref(value)
        else:
            for child in value.values(): yield from embedded_refs(child)
    elif type(value) is list:
        for child in value: yield from embedded_refs(child)


def verified_module(path, expected):
    path = Path(path)
    require(not path.is_symlink(), "TRUSTED_MODULE_ALIAS")
    raw = path.read_bytes()
    require((hashlib.sha256(raw).hexdigest(), len(raw)) == expected,
            "TRUSTED_MODULE_CHANGED")
    module = types.ModuleType("cp370_trusted_" + Path(path).stem)
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def save(name, value):
    require(Path(name).name == name, "ROOT_RECEIPT_NAME")
    path = N / name
    with path.open("xb") as file:
        file.write(encoded(value)); file.flush(); os.fsync(file.fileno())
    return pin(path)


def before_refs():
    return [{"path": str(path), "sha256": sha, "bytes": size}
            for path, (sha, size) in zip(CANON, BEFORE)]


def check_before_pair():
    refs = before_refs()
    require([pin(p) for p in CANON] == refs, "CURRENT_FOUR_CANON_NOT_CP369")
    cp, ow, ss, cm = [load(ref) for ref in refs]
    require(type(cp.get("revision")) is int and cp["revision"] == 369
            and type(cp.get("expected_previous_revision")) is int
            and cp["expected_previous_revision"] == 368
            and type(ow.get("revision")) is int and ow["revision"] == 173
            and type(cm.get("revision")) is int and cm["revision"] == 39,
            "CANON_REVISIONS")
    require(cp.get("project_id") == "aede0678-7308-43dc-b9f2-cfe3d90cfdfb"
            and cp.get("head") == "adc460c2138528f163f7fdab5e8d81dde157b7fb"
            and ow.get("active_integrator", {}).get("id") == ROOT
            and ow.get("card_path_bindings", {}).get("W09-99", {}).get("owner") == ROOT
            and ow.get("shared_integrator") == "qoder-desktop:/root/platform_owner",
            "CURRENT_ROOT_IDENTITY")
    require(cp.get("work_in_progress", {}).get("construction_active_parents") == ["W05", "W09"],
            "TWO_CONSTRUCTION_PARENTS")
    require(type(cp.get("failure_counters")) is list and len(cp["failure_counters"]) == 963,
            "CP369_FAILURE_BASELINE")
    require(KEY not in ow["card_path_bindings"]["W09-99"]["subtasks"]
            and not any(row.get("slice_id") == SLICE for row in cp.get("workers", [])),
            "SINGLE_NEW_SLICE")
    return refs, cp, ow


def ensure_caller_source(hdf_ref, mf_ref):
    for path, expected in EXACT.items():
        require((pin(path)["sha256"], pin(path)["bytes"]) == expected, "PINNED_SOURCE_CHANGED")
    exact_ref(hdf_ref); exact_ref(mf_ref)
    require(hdf_ref["sha256"] == V6_SOURCE_HDF_SHA
            and mf_ref["sha256"] == V6_SOURCE_MF_SHA, "FINAL_V6_CALLER_ONLY")
    require(Path(hdf_ref["path"]).name == "HDF.json"
            and Path(mf_ref["path"]).name == "MF.json"
            and Path(hdf_ref["path"]).parent == Path(mf_ref["path"]).parent
            and Path(hdf_ref["path"]).parent.parent == CALLER_SOURCE_ROOT,
            "CALLER_SOURCE_LOCATION")
    hdf, mf = load(hdf_ref), load(mf_ref)
    caller_ref = exact_ref(hdf["caller_source_ref"])
    contract_ref = exact_ref(hdf["root_contract_ref"])
    require(caller_ref["sha256"] == V6_CALLER_SHA
            and contract_ref["sha256"] == V6_CONTRACT_SHA,
            "FINAL_V6_CALLER_MEMBERS")
    require(Path(caller_ref["path"]).parent == Path(hdf_ref["path"]).parent
            and Path(contract_ref["path"]).parent == Path(hdf_ref["path"]).parent,
            "CALLER_SOURCE_COHERENCE")
    require(hdf.get("status") == "SOURCE_ONLY_PENDING_ROOT_REGISTRATION"
            and hdf.get("manifest_ref") == mf_ref
            and hdf.get("caller_source_ref") == caller_ref
            and hdf.get("root_contract_ref") == contract_ref
            and mf.get("caller_source_ref") == caller_ref
            and mf.get("contract_ref") == contract_ref,
            "CALLER_HDF_MF_CONTRACT")
    return hdf_ref, mf_ref, caller_ref, contract_ref


def validate_review(request, caller):
    hdf_ref = exact_ref(request["review_hdf_ref"])
    mf_ref = exact_ref(request["review_mf_ref"])
    decision_ref = exact_ref(request["review_decision_ref"])
    rh, rm, d = load(hdf_ref), load(mf_ref), load(decision_ref)
    require(hdf_ref["sha256"] == V6_REVIEW_HDF_SHA
            and mf_ref["sha256"] == V6_REVIEW_MF_SHA
            and decision_ref["sha256"] == V6_REVIEW_DECISION_SHA,
            "FINAL_V6_INDEPENDENT_REVIEW_ONLY")
    require(Path(hdf_ref["path"]).name == "HDF.json"
            and Path(mf_ref["path"]).name == "MF.json"
            and Path(hdf_ref["path"]).parent == Path(mf_ref["path"]).parent
            and Path(decision_ref["path"]).parent == Path(hdf_ref["path"]).parent
            and Path(hdf_ref["path"]).parent.parent == CALLER_REVIEW_ROOT,
            "INDEPENDENT_REVIEW_LOCATION")
    require(rh.get("manifest_ref") == mf_ref
            and rh.get("source_decision_ref") == decision_ref
            and rh.get("actor_id") == d.get("actor_id")
            and rh.get("actor_role") == "INDEPENDENT_NON_AUTHOR",
            "REAL_REVIEW_HDF_MF_DECISION")
    validate_review_members(rm, decision_ref, caller)
    require(d.get("schema") == SOURCE_REVIEW_SCHEMA
            and d.get("decision") == "ACCEPTED_SOURCE_ONLY"
            and d.get("actor_role") == "INDEPENDENT_NON_AUTHOR"
            and d.get("source_author_id") == AUTHOR
            and d.get("source_hdf_ref") == caller[0]
            and d.get("source_mf_ref") == caller[1]
            and d.get("caller_ref") == caller[2]
            and d.get("root_contract_ref") == caller[3]
            and d.get("SourceAcceptedonly") is True
            and d.get("noactualorformal") is True
            and d.get("actual_dispatcher_run") is False
            and d.get("execution_grant") is False
            and d.get("formal_acceptance") is False
            and d.get("parent_acceptance") is False
            and type(d.get("formal_case_accepted_delta")) is int
            and d["formal_case_accepted_delta"] == 0,
            "CALLER_SOURCE_REVIEW_NOT_ACCEPTED")
    validate_reviewer_actor(d.get("actor_id"))
    return hdf_ref, mf_ref, decision_ref, d


def validate_review_members(manifest, decision_ref, caller):
    require(type(manifest) is dict and type(manifest.get("members")) is list
            and decision_ref in manifest["members"]
            and manifest.get("source_hdf_ref") == caller[0]
            and manifest.get("source_mf_ref") == caller[1],
            "REVIEW_MANIFEST_NOT_BOUND")


def validate_reviewer_actor(actor):
    require(type(actor) is str and actor == DESIGNATED_REVIEWER,
            "REVIEWER_NOT_CANONICAL_NONAUTHOR")


def utc(iso):
    require(type(iso) is str, "UTC_TIME_TYPE")
    try: value = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError as exc: raise ValueError("UTC_TIME_INVALID") from exc
    require(value.tzinfo is not None and value.utcoffset().total_seconds() == 0,
            "UTC_TIME_REQUIRED")
    return value


def validate_invocation_identities(rows):
    seen = set()
    for row in rows:
        identity = (row["origin_ref"]["sha256"], row["origin_selector"])
        require(identity not in seen, "ORIGINAL_INVOCATION_REUSED")
        seen.add(identity)


def validate_observed_result(observed, live, pending_ref, witness, python_exit, exit_line):
    require(type(observed) is dict
            and observed.get("qualification_ref") == live["qualification_ref"]
            and observed.get("pending_ref") == pending_ref
            and type(observed.get("next_original")) is int
            and observed["next_original"] == live["next_original_failure_ordinal"]
            and observed.get("Canonical_unchanged") is True
            and type(observed.get("formal_delta")) is int
            and observed["formal_delta"] == 0
            and type(python_exit) is int
            and exit_line == "ROOT_SOURCE_PYTHON_EXIT=" + str(python_exit),
            "HOST_STDOUT_QUALIFICATION_NOT_BOUND")
    if witness["phase"] == "POSTSEAL_ACTIVATION":
        require(observed.get("registrar_review_refs") == witness["registrar_review_refs"]
                and observed.get("canonical_refs") == before_refs(),
                "HOST_POSTSEAL_REVIEW_CANON_NOT_BOUND")


def extract_original_result_block(blocks):
    """Accept only observed host envelopes: metadata, optional empty object, result."""
    require(type(blocks) is list and len(blocks) in (2, 3)
            and all(type(item) is dict and set(item) == {"type", "text"}
                    and item["type"] == "input_text" and type(item["text"]) is str
                    for item in blocks), "HOST_OUTPUT_NOT_PLAINTEXT")
    require(re.fullmatch(r"Script completed\nWall time [0-9]+(?:\.[0-9]+)? seconds\nOutput:\n",
                         blocks[0]["text"]) is not None,
            "HOST_OUTPUT_METADATA_INVALID")
    if len(blocks) == 3:
        require(blocks[1]["text"] == "{}", "HOST_OUTPUT_MULTIPLE_RESULTS")
    try:
        result = decode(blocks[-1]["text"])
    except (ValueError, TypeError) as exc:
        raise ValueError("HOST_OUTPUT_FINAL_RESULT_REQUIRED") from exc
    require(type(result) is dict and type(result.get("chunk_id")) is str
            and type(result.get("exit_code")) is int
            and type(result.get("output")) is str,
            "HOST_OUTPUT_FINAL_RESULT_REQUIRED")
    return result


def validate_qualification(qualification, live):
    require(type(qualification) is dict and set(qualification) == {
        "schema", "issued_by", "root_thread_id", "created_utc",
        "source_pending_ref", "before_canonical_refs", "source_cutoff",
        "next_original_failure_ordinal", "rows", "formal_acceptance",
        "parent_acceptance", "counter_reset"}, "QUALIFICATION_FIELDS")
    require(qualification["schema"] == "researchos.root-cp370-original-invocation-qualification.v1"
            and qualification["issued_by"] == ROOT
            and qualification["root_thread_id"] == ROOT_THREAD_ID
            and qualification["before_canonical_refs"] == before_refs()
            and qualification["source_cutoff"] == live["source_cutoff"]
            and qualification["next_original_failure_ordinal"] == live["next_original_failure_ordinal"]
            and qualification["formal_acceptance"] is False
            and qualification["parent_acceptance"] is False
            and qualification["counter_reset"] is False
            and type(qualification["rows"]) is list
            and len(qualification["rows"]) == len(live["pending"])
            and utc(qualification["created_utc"]) <= utc(live["created_utc"]),
            "QUALIFICATION_ROOT_AND_CUTOFF")
    source_pending_ref = exact_ref(qualification["source_pending_ref"])
    source_document = load(source_pending_ref)
    require(type(source_document) is dict and type(source_document.get("pending")) is list,
            "ROOT_PENDING_SOURCE_FIELDS")
    source_rows = source_document["pending"]
    require(Path(source_pending_ref["path"]).parent == ROOT_PENDING_DIR
            and len(source_rows) == len(live["pending"])
            and [{key: source[key] for key in ("ordinal", "origin_ref", "description")}
                 for source in source_rows] == live["pending"],
            "ROOT_PENDING_SOURCE_NOT_BOUND")
    by_ordinal = {}
    for source, row in zip(source_rows, qualification["rows"]):
        require(type(row) is dict and set(row) == {"ordinal", "origin_ref",
                "origin_selector", "exit_qualification", "capture_completeness",
                "description",
                "actual_outer_exit", "actual_python_exit", "actual_native_exit",
                "actual_dispatcher_exit", "actual_model_exit"}, "QUALIFICATION_ROW_FIELDS")
        require(type(row["ordinal"]) is int and row["ordinal"] == source["ordinal"]
                and row["origin_ref"] == source["origin_ref"]
                and row["description"] == source["description"]
                and type(row["origin_selector"]) is str
                and row["origin_selector"].strip() == row["origin_selector"]
                and row["origin_selector"] != ""
                and row["capture_completeness"] in CAPTURE_CLASSES,
                "QUALIFICATION_INVOCATION_IDENTITY")
        for field in ("origin_selector", "actual_outer_exit", "actual_python_exit",
                      "actual_native_exit", "actual_dispatcher_exit", "actual_model_exit"):
            if field in source:
                require(source[field] == row[field] and type(source[field]) is type(row[field]),
                        "PRIOR_ORIGINAL_EXIT_OR_SELECTOR_CHANGED")
        q = row["exit_qualification"]
        require(type(q) is dict and {"schema", "authority", "unknown_is_null",
                "source_capture_ref", "source_capture_selector", "diagnostic_source_ref",
                "diagnostic_source_selector"} <= set(q)
                and set(q) <= {"schema", "authority", "unknown_is_null",
                "source_capture_ref", "source_capture_selector", "diagnostic_source_ref",
                "diagnostic_source_selector", "observed_failed_child_exit"}
                and q["schema"] == "researchos.root-original-exit-qualification.v1"
                and q["authority"] == "ROOT_OBSERVED_DIAGNOSTIC_ONLY"
                and q["unknown_is_null"] is True
                and q["source_capture_ref"] == row["origin_ref"]
                and q["source_capture_selector"] == row["origin_selector"]
                and q["diagnostic_source_ref"] == source_pending_ref
                and q["diagnostic_source_selector"] ==
                "pending[ordinal=" + str(row["ordinal"]) + "]",
                "ORIGINAL_EXIT_QUALIFICATION_NOT_BOUND")
        if "observed_failed_child_exit" in q:
            require(q["observed_failed_child_exit"] is None
                    or type(q["observed_failed_child_exit"]) is int,
                    "CHILD_EXIT_QUALIFICATION_TYPED")
        for field in ("actual_outer_exit", "actual_python_exit", "actual_native_exit",
                      "actual_dispatcher_exit", "actual_model_exit"):
            require(row[field] is None or type(row[field]) is int, "QUALIFICATION_EXIT_TYPED")
        by_ordinal[row["ordinal"]] = row
    validate_invocation_identities(qualification["rows"])
    return by_ordinal


def validate_live(live, phase="source"):
    require(phase in ("source", "activation"), "LIVE_PHASE")
    common = {"schema", "issued_by", "root_thread_id", "created_utc",
              "source_cutoff", "next_original_failure_ordinal", "pending",
              "qualification_ref"}
    witness_key = "activation_witness_ref" if phase == "activation" else "seed_witness_ref"
    expected = common | {witness_key}
    require(type(live) is dict and set(live) == expected, "LIVE_FIELDS")
    schema = ("researchos.root-cp370-source-live-context.v2" if phase == "source"
              else "researchos.root-cp370-postseal-live-context.v2")
    require(live["schema"] == schema and live["issued_by"] == ROOT
            and live["root_thread_id"] == ROOT_THREAD_ID
            and live["source_cutoff"] == {"highest_ordinal": 965, "next_failure_ordinal": 966}
            and type(live["next_original_failure_ordinal"]) is int
            and live["next_original_failure_ordinal"] >= 970
            and type(live["pending"]) is list
            and utc(live["created_utc"]) <= datetime.now(timezone.utc), "LIVE_NO_RESET_OR_FUTURE")
    require([row.get("ordinal") for row in live["pending"]] ==
            list(range(966, live["next_original_failure_ordinal"])), "LIVE_CONTIGUOUS_ORIGINALS")
    for row in live["pending"]:
        require(type(row) is dict and set(row) == {"ordinal", "origin_ref", "description"}
                and type(row["ordinal"]) is int
                and type(row["description"]) is str and row["description"].strip() != "",
                "LIVE_ROW_TYPED")
        exact_ref(row["origin_ref"])
    require(Path(exact_ref(live["qualification_ref"])["path"]).parent == ROOT_INPUT_DIR,
            "ROOT_QUALIFICATION_LOCATION")
    qualification = load(live["qualification_ref"])
    qualified = validate_qualification(qualification, live)
    validate_root_witness(live[witness_key], live,
                          "POSTSEAL_ACTIVATION" if phase == "activation" else "SEED")
    return qualified


def validate_root_witness(witness_ref, live, phase):
    """Bind a Root witness to three original audit records and their exact bytes."""
    witness_ref = exact_ref(witness_ref)
    require(Path(witness_ref["path"]).parent == ROOT_INPUT_DIR, "ROOT_WITNESS_LOCATION")
    witness = load(witness_ref)
    require(type(witness) is dict and set(witness) == {
        "schema", "issued_by", "root_thread_id", "created_utc", "phase",
        "next_original_failure_ordinal", "canonical_refs", "qualification_ref",
        "original_tool_io_ref", "actual_host_capture_ref", "capture_binding_ref",
        "registrar_review_refs", "formal_acceptance", "parent_acceptance",
        "counter_reset"}, "ROOT_WITNESS_FIELDS")
    require(witness["schema"] == "researchos.root-cp370-actual-observation-witness.v1"
            and witness["issued_by"] == ROOT
            and witness["root_thread_id"] == ROOT_THREAD_ID
            and witness["phase"] == phase
            and type(witness["next_original_failure_ordinal"]) is int
            and witness["next_original_failure_ordinal"] == live["next_original_failure_ordinal"]
            and witness["canonical_refs"] == before_refs()
            and witness["qualification_ref"] == live["qualification_ref"]
            and witness["formal_acceptance"] is False
            and witness["parent_acceptance"] is False
            and witness["counter_reset"] is False
            and utc(witness["created_utc"]) < utc(live["created_utc"]),
            "ROOT_WITNESS_NOT_BOUND")
    require(type(witness["registrar_review_refs"]) is list
            and (witness["registrar_review_refs"] == [] if phase == "SEED"
                 else len(witness["registrar_review_refs"]) == 3),
            "ROOT_WITNESS_REVIEW_PHASE")
    refs = [witness_ref]
    for key in ("original_tool_io_ref", "actual_host_capture_ref", "capture_binding_ref"):
        ref = exact_ref(witness[key])
        require(Path(ref["path"]).parent == ROOT_INPUT_DIR and ref != witness_ref,
                "ROOT_WITNESS_DEPENDENCY_LOCATION")
        refs.append(ref)
    original = load(refs[1])
    raw = Path(refs[2]["path"]).read_bytes()
    require(len(raw) == refs[2]["bytes"] and hashlib.sha256(raw).hexdigest() == refs[2]["sha256"],
            "HOST_CAPTURE_CHANGED")
    lines = raw.splitlines(keepends=True)
    binding = load(refs[3])
    require(type(binding) is dict and set(binding) == {
        "schema", "issued_by", "root_thread_id", "original_capture_ref",
        "source_audit_path", "source_prefix_size_observed", "source_line_offsets",
        "source_line_bytes", "original_line_sha256", "original_call_id",
        "tool_result_chunk_id", "tool_call_timestamp", "tool_result_timestamp",
        "formal_authority", "parent_acceptance"}, "HOST_CAPTURE_BINDING_FIELDS")
    require(binding["schema"] == "researchos.root-actual-tool-capture-binding.v1"
            and binding["issued_by"] == ROOT
            and binding["root_thread_id"] == ROOT_THREAD_ID
            and binding["original_capture_ref"] == refs[2]
            and binding["formal_authority"] is False
            and binding["parent_acceptance"] is False
            and type(binding["source_prefix_size_observed"]) is int
            and type(binding["source_line_offsets"]) is list
            and type(binding["source_line_bytes"]) is list
            and type(binding["original_line_sha256"]) is list
            and len(lines) == len(binding["source_line_offsets"]) ==
                len(binding["source_line_bytes"]) == len(binding["original_line_sha256"]) == 3,
            "HOST_CAPTURE_BINDING")
    audit_path = Path(binding["source_audit_path"])
    require(audit_path == Path(r"C:\Users\yqyyds\.codex\sessions\2026\10\06\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl")
            and audit_path.is_file() and not audit_path.is_symlink(),
            "ROOT_AUDIT_SOURCE")
    with audit_path.open("rb") as audit:
        for index, line in enumerate(lines):
            offset = binding["source_line_offsets"][index]
            size = binding["source_line_bytes"][index]
            require(type(offset) is int and type(size) is int
                    and 0 <= offset and 0 < size
                    and offset + size <= binding["source_prefix_size_observed"]
                    and len(line) == size
                    and hashlib.sha256(line).hexdigest() ==
                        binding["original_line_sha256"][index], "HOST_CAPTURE_LINE_PIN")
            audit.seek(offset)
            require(audit.read(size) == line, "HOST_AUDIT_RANGE_CHANGED")
    header, call, output = [decode(line) for line in lines]
    require(header.get("type") == "session_meta"
            and header.get("payload", {}).get("id") == ROOT_THREAD_ID
            and call.get("type") == output.get("type") == "response_item"
            and call.get("payload", {}).get("type") == "custom_tool_call"
            and output.get("payload", {}).get("type") == "custom_tool_call_output"
            and call["payload"].get("name") == "exec"
            and call["payload"].get("call_id") ==
                output["payload"].get("call_id") == binding["original_call_id"]
            and call.get("timestamp") == binding["tool_call_timestamp"]
            and output.get("timestamp") == binding["tool_result_timestamp"]
            and utc(call["timestamp"]) < utc(output["timestamp"])
            and utc(output["timestamp"]) < utc(witness["created_utc"]),
            "HOST_AUDIT_PAIR_NOT_ORIGINAL")
    blocks = output["payload"].get("output")
    actual_result = extract_original_result_block(blocks)
    require(type(original) is dict and set(original) == {
        "schema", "actor_id", "actual_outer_exit", "actual_python_exit",
        "actual_native_exit", "actual_dispatcher_exit", "actual_model_exit",
        "args", "result"}, "ROOT_ORIGINAL_TOOL_IO_FIELDS")
    require(original["schema"] == "researchos.root-original-tool-io.v1"
            and original["actor_id"] == ROOT
            and type(original["args"]) is dict
            and type(original["result"]) is dict
            and original["result"] == actual_result
            and original["result"].get("chunk_id") == binding["tool_result_chunk_id"]
            and type(original["actual_outer_exit"]) is int
            and original["actual_outer_exit"] == original["result"].get("exit_code"),
            "HOST_ORIGINAL_TOOL_IO_MISMATCH")
    call_input = call["payload"].get("input")
    command = original["args"].get("cmd")
    require(type(call_input) is str and type(command) is str
            and "exec_command" in call_input
            and json.dumps(command, ensure_ascii=False)[1:-1] in call_input,
            "HOST_CALL_ARGUMENTS_NOT_BOUND")
    stdout = original["result"].get("output")
    require(type(stdout) is str and len(stdout.splitlines()) == 2,
            "HOST_RESULT_STDOUT_SHAPE")
    result_lines = stdout.splitlines()
    observed = decode(result_lines[0])
    validate_observed_result(observed, live,
                             load(live["qualification_ref"])["source_pending_ref"],
                             witness, original["actual_python_exit"], result_lines[1])
    for key in ("actual_python_exit", "actual_native_exit", "actual_dispatcher_exit",
                "actual_model_exit"):
        require(original[key] is None or type(original[key]) is int,
                "HOST_ORIGINAL_EXIT_TYPED")
    return witness, refs


def validate_activation_context(fresh, seed, facts):
    """A separate Root audit event must follow a sealed independent review."""
    require(fresh is not seed and fresh["schema"] != seed["schema"], "FRESH_CONTEXT_REQUIRED")
    seed_q = validate_live(seed, "source")
    fresh_q = validate_live(fresh, "activation")
    validate_qualification_continuity(seed, seed_q, fresh, fresh_q)
    witness, witness_refs = validate_root_witness(fresh["activation_witness_ref"],
                                                  fresh, "POSTSEAL_ACTIVATION")
    reviews = witness["registrar_review_refs"]
    require(type(reviews) is list and len(reviews) == 3,
            "POSTSEAL_REVIEW_THREE_REFS")
    rh_ref, rm_ref, rd_ref = [exact_ref(ref) for ref in reviews]
    rh, rm, rd = load(rh_ref), load(rm_ref), load(rd_ref)
    seed_binding = load(load(seed["seed_witness_ref"])["capture_binding_ref"])
    fresh_binding = load(witness["capture_binding_ref"])
    validate_postseal_host_provenance(seed_binding, fresh_binding, rd["reviewed_at"],
                                     load(seed["seed_witness_ref"])["actual_host_capture_ref"],
                                     witness["actual_host_capture_ref"])
    require(type(rm) is dict and type(rm.get("members")) is list
            and rd_ref in rm["members"]
            and rh.get("manifest_ref") == rm_ref
            and rh.get("source_decision_ref") == rd_ref
            and rh.get("actor_id") == rd.get("actor_id")
            and rd.get("schema") == "researchos.w09-cp370-registrar-independent-source-decision.v1"
            and rd.get("decision") == "ACCEPTED_SOURCE_ONLY"
            and rd.get("actor_role") == "INDEPENDENT_NON_AUTHOR"
            and rd.get("actor_id") == "codex:/root/attach_fixture_source_review"
            and rd.get("source_author_id") == AUTHOR
            and rd.get("registrar_ref") == pin(__file__)
            and rd.get("root_contract_ref") == pin(N / "ROOT_BUILDER_CONTRACT.source.md")
            and rd.get("source_hdf_ref") == exact_ref(rm["source_hdf_ref"])
            and rd.get("source_mf_ref") == exact_ref(rm["source_mf_ref"])
            and Path(rd["source_hdf_ref"]["path"]).parent == N
            and Path(rd["source_mf_ref"]["path"]).parent == N
            and rd.get("actual_registration") is False
            and rd.get("formal_acceptance") is False
            and rd.get("parent_acceptance") is False,
            "REGISTRAR_SOURCE_REVIEW_NOT_QUALIFIED")
    validate_postseal_times(seed["created_utc"], rd["reviewed_at"],
                            witness["created_utc"], fresh["created_utc"])
    return [*witness_refs, rh_ref, rm_ref, rd_ref,
            rd["source_hdf_ref"], rd["source_mf_ref"]]


def validate_postseal_times(seed_at, reviewed_at, witnessed_at, fresh_at):
    require(utc(reviewed_at) < utc(witnessed_at) < utc(fresh_at)
            and utc(seed_at) < utc(witnessed_at), "POSTSEAL_WITNESS_TIME_ORDER")


def validate_postseal_host_provenance(seed_binding, fresh_binding, reviewed_at,
                                     seed_capture_ref, fresh_capture_ref):
    require(fresh_capture_ref != seed_capture_ref
            and fresh_binding["original_call_id"] != seed_binding["original_call_id"]
            and utc(fresh_binding["tool_call_timestamp"]) > utc(reviewed_at)
            and utc(fresh_binding["tool_result_timestamp"]) > utc(reviewed_at),
            "POSTSEAL_REQUIRES_NEW_HOST_CALL_AFTER_REVIEW")


def validate_qualification_continuity(seed, seed_q, fresh, fresh_q):
    old_count = len(seed["pending"])
    def immutable(row):
        frozen = copy.deepcopy(row)
        del frozen["exit_qualification"]["diagnostic_source_ref"]
        return frozen
    require(fresh["next_original_failure_ordinal"] >= seed["next_original_failure_ordinal"]
            and fresh["pending"][:old_count] == seed["pending"]
            and all(ordinal in fresh_q and immutable(fresh_q[ordinal]) == immutable(seed_q[ordinal])
                    for ordinal in seed_q),
            "SOURCE_ORIGINALS_CHANGED_AFTER_SEAL")


def _future(iso):
    require(type(iso) is str, "LEASE_TIME_TYPE")
    try: time = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError as exc: raise ValueError("LEASE_TIME_INVALID") from exc
    require(time.tzinfo is not None and time > datetime.now(timezone.utc), "LEASE_EXPIRED")


def validate_root_build_request(request, live):
    require(type(request) is dict and set(request) == {"schema", "issued_by", "created_utc",
            "caller_hdf_ref", "caller_mf_ref", "review_hdf_ref", "review_mf_ref",
            "review_decision_ref", "native_hdf_ref", "native_handoff_ref",
            "native_historical_request_ref", "frozen_plan_ref", "historical_cp369_archives",
            "before_canonical_refs", "source_reviewer", "lease_expires_at",
            "authorized_output_root", "live_ref", "source_qualification_ref",
            "no_actual_consumer_run"},
            "BUILD_REQUEST_EXACT_FIELDS")
    require(request["schema"] == "researchos.root-cp370-c19-dispatcher-build-request.v1"
            and request["issued_by"] == ROOT
            and request["no_actual_consumer_run"] is True
            and type(request["created_utc"]) is str
            and utc(request["created_utc"]) >= utc(live["created_utc"]),
            "BUILD_ROOT_ONLY")
    _future(request["lease_expires_at"])
    canonical_output_root(request["authorized_output_root"])
    require(request["before_canonical_refs"] == before_refs(), "BUILD_BEFORE_CANON")
    archives = request["historical_cp369_archives"]
    require(type(archives) is list and len(archives) == 4, "HISTORICAL_ARCHIVE_FOUR")
    for name, old, archive in zip(("checkpoint", "path_ownership", "step_state", "commands"),
                                  before_refs(), archives):
        exact_ref(archive)
        require(Path(archive["path"]).name == "historical.cp369." + name + ".json"
                and archive["sha256"] == old["sha256"] and archive["bytes"] == old["bytes"],
                "HISTORICAL_CP369_ARCHIVE_BYTES")
    require(load(request["live_ref"]) == live, "LIVE_REF_CHANGED")
    require(request["source_qualification_ref"] == live["qualification_ref"],
            "BUILD_QUALIFICATION_REF")
    validate_live(live, "source")


def canonical_output_root(raw):
    require(type(raw) is str, "OUTPUT_ROOT_TYPE")
    path = Path(raw)
    resolved = path.resolve()
    require(path.is_absolute() and str(path) == str(resolved)
            and ".." not in path.parts and "." not in path.parts
            and resolved != ROOT_OUTPUT_BOUNDARY.resolve()
            and resolved.is_relative_to(ROOT_OUTPUT_BOUNDARY.resolve()),
            "OUTPUT_ROOT_SCOPE")
    return str(resolved)


def held_guard(refs, exclude_pair):
    gm = verified_module(GP, EXACT[str(GP)])
    refs = list(refs)
    for module in tuple(sys.modules.values()):
        for key in ("__file__", "__cached__"):
            path = getattr(module, key, None)
            if path and Path(path).is_file(): refs.append(pin(path))
    unique = {}
    for ref in refs:
        exact_ref(ref)
        key = ref["path"].casefold()
        require(key not in unique or unique[key] == ref, "CONFLICTING_SOURCE_PINS")
        unique[key] = ref
    if exclude_pair:
        for path, expected in zip(CANON[:2], before_refs()[:2]):
            key = str(path).casefold()
            if key in unique:
                require(unique[key] == expected, "CANON_PAIR_EXPECTED_PIN")
                del unique[key]
    guard = gm.SourceReadGuard(per_file_cap=256*1024*1024, total_cap=2*1024*1024*1024)
    guard.acquire(list(unique.values()))
    return guard, len(unique)


def build_root_docs(request_ref):
    """Root-only later build. Never called during Source preparation."""
    require(Path(exact_ref(request_ref)["path"]).parent == ROOT_INPUT_DIR,
            "ROOT_BUILD_REQUEST_LOCATION")
    request = load(request_ref)
    refs, _, _ = check_before_pair()
    live = load(request["live_ref"])
    validate_root_build_request(request, live)
    caller = ensure_caller_source(request["caller_hdf_ref"], request["caller_mf_ref"])
    require(request["caller_hdf_ref"] == caller[0]
            and request["caller_mf_ref"] == caller[1], "ROOT_CALLER_INPUT")
    rh, rm, decision_ref, decision = validate_review(request, caller)
    require(request["source_reviewer"] == decision["actor_id"], "REVIEWER_ID_BINDING")
    for field, expected in (("native_hdf_ref", "49dd4ae646af95ecc38004f9650245e7e6ed9e04aa9fe8711b5fd945dd840270"),
                            ("native_handoff_ref", "cc4e8de2bf69b1b322fb500369b85bc4d737b26f761fa746a52e8088c6257835"),
                            ("native_historical_request_ref", "8c0b984f4bdcd4a89464645e82780dfafbaeba8dfcdb0dbed0958df7b283e84e"),
                            ("frozen_plan_ref", "a6669dd94b16bc833526f569c3c86ab08180ff6a39087ca9921ea898817eea17")):
        ref = exact_ref(request[field]); require(ref["sha256"] == expected, "ROOT_INPUT_PIN_" + field)
    scope = dict(schema=SOURCE_SCOPE_SCHEMA, issued_by=ROOT, slice_id=SLICE,
                 formal_dispatcher=True, formal_acceptance=False, parent_acceptance=False,
                 formal_case_accepted_delta=0, expected_checkpoint_revision=370,
                 expected_previous_checkpoint_revision=369, expected_path_ownership_revision=174,
                 routes=ROUTES, source_actor=AUTHOR, source_reviewer=decision["actor_id"],
                 source_hdf_ref=caller[0], source_mf_ref=caller[1], caller_ref=caller[2],
                 root_contract_ref=caller[3], source_review_ref=decision_ref,
                 frozen_plan_ref=request["frozen_plan_ref"],
                 native_qualified_hdf_ref=request["native_hdf_ref"],
                 native_handoff_ref=request["native_handoff_ref"],
                 native_historical_request_ref=request["native_historical_request_ref"],
                 before_canonical_refs=refs,
                 before_canonical_revisions={"checkpoint":369,"path_ownership":173,"commands":39},
                 authorized_output_root=canonical_output_root(request["authorized_output_root"]))
    caller_module = verified_module(caller[2]["path"], (caller[2]["sha256"], caller[2]["bytes"]))
    caller_module.validate_scope(scope)
    _, seed_witness_refs = validate_root_witness(live["seed_witness_ref"], live, "SEED")
    input_refs = [request_ref, request["live_ref"], request["source_qualification_ref"],
                  *seed_witness_refs,
                  *refs, rh, rm, decision_ref,
                  *[request[k] for k in ("native_hdf_ref", "native_handoff_ref",
                   "native_historical_request_ref", "frozen_plan_ref")],
                  *request["historical_cp369_archives"], *caller]
    for ref in (seed_witness_refs[0], seed_witness_refs[1], seed_witness_refs[3]):
        input_refs.extend(embedded_refs(load(ref)))
    for value in (load(caller[0]), load(caller[1]), load(rh), load(rm),
                  load(decision_ref), load(request["native_hdf_ref"]),
                  load(request["native_handoff_ref"])):
        input_refs.extend(embedded_refs(value))
    input_refs.extend(row["origin_ref"] for row in live["pending"])
    input_refs.extend(embedded_refs(load(request["source_qualification_ref"])))
    input_refs.extend(embedded_refs(load(load(live["qualification_ref"])["source_pending_ref"])))
    input_refs.extend(pin(p) for p in (BASE, GP, TP, __file__,
                                       N / "ROOT_BUILDER_CONTRACT.source.md", sys.executable))
    for module in tuple(sys.modules.values()):
        for key in ("__file__", "__cached__"):
            path = getattr(module, key, None)
            if path and Path(path).is_file(): input_refs.append(pin(path))
    guard, _ = held_guard(input_refs, exclude_pair=False)
    try:
        scope_ref = save("scope-registration.root.json", scope)
        common = dict(step_id="W09-99", slice_id=SLICE, state=STATE,
                      scope_ref=scope_ref, output_root=scope["authorized_output_root"],
                      routes=ROUTES, lease_status="ACTIVE",
                      lease_expires_at=request["lease_expires_at"])
        owner_doc = dict(common, owner_id=ROOT, selected_worker_id=ROOT)
        owner_ref = save("owner-document.root.json", owner_doc)
        worker_doc = dict(common, worker_id=ROOT, selected_owner_ref=owner_ref)
        worker_ref = save("worker-document.root.json", worker_doc)
        facts = dict(schema="researchos.root-cp370-c19-two-dispatcher-registration-facts.v1",
                     issued_by=ROOT, created_utc=request["created_utc"],
                     before_canonical_refs=refs, scope_ref=scope_ref,
                     owner_document_ref=owner_ref, worker_document_ref=worker_ref,
                     source_hdf_ref=caller[0], source_mf_ref=caller[1],
                     source_review_hdf_ref=rh, source_review_mf_ref=rm,
                     source_review_decision_ref=decision_ref,
                     build_request_ref=request_ref, live_ref=request["live_ref"],
                     source_qualification_ref=request["source_qualification_ref"],
                     source_cutoff={"highest_ordinal":965,"next_failure_ordinal":966},
                     root_next_failure_ordinal_live=live["next_original_failure_ordinal"],
                     no_actual_consumer_run=True, formal_dispatcher=True,
                     formal_acceptance=False, parent_acceptance=False,
                     formal_case_accepted_delta=0)
        facts_ref = save("registration-facts.root.json", facts)
    finally:
        cleanup = guard.close()
        save("build-source-guard.cleanup.root.json", cleanup)
        require(cleanup["closed"] and cleanup["retained_handles_count"] == 0
                and cleanup["errors"] == [], "BUILD_READER_NOT_CLOSED")
    return facts_ref


def transformed_pair(cp, ow, facts, live, old_cp, old_ow, facts_ref):
    require(cp == old_cp and ow == old_ow, "CANON_PAIR_CHANGED")
    qualified = validate_live(live, "activation" if "activation_witness_ref" in live else "source")
    scope = load(facts["scope_ref"])
    owner_doc, worker_doc = load(facts["owner_document_ref"]), load(facts["worker_document_ref"])
    require(scope["formal_dispatcher"] is True and scope["formal_acceptance"] is False
            and scope["parent_acceptance"] is False and scope["before_canonical_refs"] == before_refs(),
            "EXACT_SCOPE_NO_ACCEPTANCE")
    require(owner_doc["selected_worker_id"] == ROOT
            and worker_doc["selected_owner_ref"] == facts["owner_document_ref"]
            and owner_doc["scope_ref"] == worker_doc["scope_ref"] == facts["scope_ref"],
            "ACYCLIC_OWNER_WORKER")
    require(KEY not in ow["card_path_bindings"]["W09-99"]["subtasks"]
            and not any(row.get("slice_id") == SLICE for row in cp["workers"]),
            "UNIQUE_CANON_SLICE")
    owner = dict(owner_doc, owner=ROOT, current_source_writer=None,
                 source_handoff_ref=facts["source_hdf_ref"],
                 source_review_ref=facts["source_review_decision_ref"],
                 owner_document_ref=facts["owner_document_ref"],
                 worker_document_ref=facts["worker_document_ref"],
                 formal_case_accepted_delta=0, parent_acceptance=False)
    worker = dict(worker_doc, owner=ROOT,
                  source_handoff_ref=facts["source_hdf_ref"],
                  source_review_ref=facts["source_review_decision_ref"],
                  worker_document_ref=facts["worker_document_ref"])
    ow["card_path_bindings"]["W09-99"]["subtasks"][KEY] = owner
    cp["workers"].append(worker)
    seen = set()
    for existing in cp["failure_counters"]:
        payload = existing.get("original_payload", {})
        prior_ref = payload.get("immutable_origin_ref")
        prior_selector = payload.get("origin_selector")
        if type(prior_ref) is dict and type(prior_selector) is str and prior_selector:
            seen.add((prior_ref.get("sha256"), prior_selector))
    for row in live["pending"]:
        origin = row["origin_ref"]
        q = qualified[row["ordinal"]]
        identity = (origin["sha256"], q["origin_selector"])
        require(identity not in seen, "ORIGINAL_INVOCATION_REUSED")
        seen.add(identity)
        key = hashlib.sha256((origin["sha256"] + "#" + q["origin_selector"]).encode()).hexdigest()
        cp["failure_counters"].append(dict(origin_key=key,evidence_ref=origin,
            original_payload=dict(observed_ordinal=row["ordinal"],
                immutable_origin_ref=origin, origin_selector=q["origin_selector"],
                exit_qualification=q["exit_qualification"],
                capture_completeness=q["capture_completeness"],
                actual_outer_exit=q["actual_outer_exit"],
                actual_python_exit=q["actual_python_exit"],
                actual_native_exit=q["actual_native_exit"],
                actual_dispatcher_exit=q["actual_dispatcher_exit"],
                actual_model_exit=q["actual_model_exit"],
                diagnostic=row["description"]),
            counted_once=True,counter_reset=False,automatic_retry=False))
    work = cp["work_in_progress"]
    require("mu_sdk_r370" not in work and "w09_c19_two_dispatcher_scope_ref" not in work,
            "UNIQUE_CP370_WIP")
    prior_pending = work.get("later_diagnostics_observed_after_cutoff")
    require(type(prior_pending) is list
            and [row.get("ordinal") for row in prior_pending] == list(range(966, 970))
            and type(work.get("root_next_failure_ordinal_live")) is int
            and work["root_next_failure_ordinal_live"] == 970,
            "CP369_PENDING_BASELINE")
    for old_row, current_row in zip(prior_pending, live["pending"][:4]):
        require(type(old_row) is dict and set(old_row) == {"ordinal", "origin_ref", "description"}
                and all(old_row[k] == current_row[k] for k in old_row),
                "CP369_PENDING_ORIGIN_CHANGED")
    work["mu_sdk_r370"] = dict(scope_ref=facts["scope_ref"], facts_ref=facts_ref,
        source_review_ref=facts["source_review_decision_ref"],
        status=STATE, prior_native_status="QUALIFIED_COMPONENT_ONLY",
        W05_qualification="DEVELOPMENT_TESTS_13_ACTUAL_PASS_COMPONENT_PARTIAL_NATIVE_QUALIFICATION_OPEN",
        registered_failure_count=len(cp["failure_counters"]),
        highest_registered_ordinal_at_cutoff=live["next_original_failure_ordinal"]-1,
        next_failure_ordinal_at_cutoff=live["next_original_failure_ordinal"],
        formal_case_accepted_delta=0,parent_acceptance=False)
    work["w09_c19_two_dispatcher_scope_ref"] = facts["scope_ref"]
    work["root_next_failure_ordinal_live"] = live["next_original_failure_ordinal"]
    work["later_diagnostics_observed_after_cutoff"].extend(
        {key: copy.deepcopy(row[key]) for key in ("ordinal", "origin_ref", "description")}
        for row in live["pending"][4:])
    cp.update(revision=370, expected_previous_revision=369,
              updated_at=live["created_utc"], updated_by=ROOT,
              note="Root registered exact C19 Main two-dispatcher caller slice; Source-qualified only, no consumer or formal acceptance.")
    ow.update(revision=174,updated_at=live["created_utc"],updated_by=ROOT)
    caller_ref = load(facts["scope_ref"])["caller_ref"]
    caller_module = verified_module(caller_ref["path"],
                                    (caller_ref["sha256"], caller_ref["bytes"]))
    caller_module.validate_scope(scope)
    caller_module.validate_canon_lease(
        cp, ow, scope, facts["scope_ref"], facts["source_hdf_ref"],
        facts["source_review_decision_ref"], facts["owner_document_ref"],
        facts["worker_document_ref"], owner_doc, worker_doc,
        Path(scope["authorized_output_root"]) / "registrar-lease-check")
    inverse_cp = copy.deepcopy(cp)
    for key in ("failure_counters", "workers", "work_in_progress", "revision",
                "expected_previous_revision", "updated_at", "updated_by", "note"):
        inverse_cp[key] = copy.deepcopy(old_cp[key])
    inverse_ow = copy.deepcopy(ow)
    del inverse_ow["card_path_bindings"]["W09-99"]["subtasks"][KEY]
    for key in ("revision", "updated_at", "updated_by"):
        inverse_ow[key] = copy.deepcopy(old_ow[key])
    require(encoded(inverse_cp) == encoded(old_cp)
            and encoded(inverse_ow) == encoded(old_ow), "COMPLETE_BYTE_INVERSE_MODEL")
    require((hashlib.sha256(encoded(old_cp)).hexdigest(), len(encoded(old_cp))) == BEFORE[0]
            and (hashlib.sha256(encoded(old_ow)).hexdigest(), len(encoded(old_ow))) == BEFORE[1],
            "BEFORE_CANON_EXACT_BYTES")
    require(cp["failure_counters"][:963] == old_cp["failure_counters"]
            and cp["workers"][:-1] == old_cp["workers"], "PRIOR_WORK_PRESERVED")
    return cp, ow


def register(mode, facts_ref, live_ref):
    require(mode in ("check", "activate"), "MODE")
    facts, live = load(facts_ref), load(live_ref)
    require(Path(exact_ref(live_ref)["path"]).parent == ROOT_INPUT_DIR,
            "ROOT_LIVE_LOCATION")
    require(type(facts) is dict and set(facts) == {"schema", "issued_by", "created_utc",
            "before_canonical_refs", "scope_ref", "owner_document_ref",
            "worker_document_ref", "source_hdf_ref", "source_mf_ref",
            "source_review_hdf_ref", "source_review_mf_ref",
            "source_review_decision_ref", "build_request_ref", "live_ref",
            "source_qualification_ref",
            "source_cutoff", "root_next_failure_ordinal_live", "no_actual_consumer_run",
            "formal_dispatcher", "formal_acceptance", "parent_acceptance",
            "formal_case_accepted_delta"}, "FACTS_KEYS")
    seed = load(facts["live_ref"])
    require(facts.get("schema") == "researchos.root-cp370-c19-two-dispatcher-registration-facts.v1"
            and facts.get("issued_by") == ROOT
            and facts.get("source_cutoff") == {"highest_ordinal":965,"next_failure_ordinal":966}
            and type(facts.get("root_next_failure_ordinal_live")) is int
            and facts["root_next_failure_ordinal_live"] == seed["next_original_failure_ordinal"]
            and facts.get("source_qualification_ref") == seed.get("qualification_ref")
            and facts.get("no_actual_consumer_run") is True
            and facts.get("formal_dispatcher") is True
            and facts.get("formal_acceptance") is False
            and facts.get("parent_acceptance") is False
            and type(facts.get("formal_case_accepted_delta")) is int
            and facts["formal_case_accepted_delta"] == 0,
            "FACTS_EXACT_SCOPE")
    require(Path(facts_ref["path"]) == N / "registration-facts.root.json"
            and Path(facts["scope_ref"]["path"]) == N / "scope-registration.root.json"
            and Path(facts["owner_document_ref"]["path"]) == N / "owner-document.root.json"
            and Path(facts["worker_document_ref"]["path"]) == N / "worker-document.root.json",
            "ROOT_BUILDER_OUTPUT_LOCATION")
    validate_live(seed, "source")
    if mode == "check":
        require(live_ref == facts["live_ref"] and live == seed,
                "CHECK_REQUIRES_SOURCE_CONTEXT")
        activation_refs = []
    else:
        require(live_ref != facts["live_ref"], "ACTIVATION_REQUIRES_FRESH_CONTEXT")
        activation_refs = validate_activation_context(live, seed, facts)
    refs, old_cp, old_ow = check_before_pair()
    require(facts["before_canonical_refs"] == refs, "FACTS_BEFORE_CANON")
    caller = ensure_caller_source(facts["source_hdf_ref"], facts["source_mf_ref"])
    require(facts["source_hdf_ref"] == caller[0]
            and facts["source_mf_ref"] == caller[1], "FACTS_SOURCE")
    request = load(facts["build_request_ref"])
    require(Path(exact_ref(facts["build_request_ref"])["path"]).parent == ROOT_INPUT_DIR,
            "ROOT_BUILD_REQUEST_LOCATION")
    validate_root_build_request(request, seed)
    require(request["created_utc"] == facts["created_utc"]
            and request["live_ref"] == facts["live_ref"]
            and request["source_qualification_ref"] == facts["source_qualification_ref"]
            and request["caller_hdf_ref"] == facts["source_hdf_ref"]
            and request["caller_mf_ref"] == facts["source_mf_ref"]
            and request["review_hdf_ref"] == facts["source_review_hdf_ref"]
            and request["review_mf_ref"] == facts["source_review_mf_ref"]
            and request["review_decision_ref"] == facts["source_review_decision_ref"],
            "FACTS_BUILD_REQUEST_CHANGED")
    rh, rm, decision_ref, decision = validate_review(request, caller)
    require((rh, rm, decision_ref) == (facts["source_review_hdf_ref"],
            facts["source_review_mf_ref"], facts["source_review_decision_ref"]),
            "FACTS_REVIEW_BINDING")
    scope = load(facts["scope_ref"])
    require(scope["source_hdf_ref"] == caller[0]
            and scope["source_mf_ref"] == caller[1]
            and scope["caller_ref"] == caller[2]
            and scope["root_contract_ref"] == caller[3]
            and scope["source_review_ref"] == decision_ref
            and scope["source_reviewer"] == decision["actor_id"]
            and scope["frozen_plan_ref"] == request["frozen_plan_ref"]
            and scope["native_qualified_hdf_ref"] == request["native_hdf_ref"]
            and scope["native_handoff_ref"] == request["native_handoff_ref"]
            and scope["native_historical_request_ref"] == request["native_historical_request_ref"]
            and scope["before_canonical_refs"] == refs
            and scope["authorized_output_root"] == canonical_output_root(request["authorized_output_root"]),
            "SCOPE_BUILD_REQUEST_BINDING")
    caller_module = verified_module(caller[2]["path"], (caller[2]["sha256"], caller[2]["bytes"]))
    caller_module.validate_scope(scope)
    caller_module.validate_source_review(decision, scope, *caller)
    _, seed_witness_refs = validate_root_witness(seed["seed_witness_ref"], seed, "SEED")
    all_refs = [facts_ref, live_ref, facts["live_ref"], *seed_witness_refs,
                facts["source_qualification_ref"], live["qualification_ref"],
                *activation_refs, pin(__file__),
                pin(N / "ROOT_BUILDER_CONTRACT.source.md"), pin(sys.executable),
                pin(BASE), pin(GP), pin(TP), *refs[2:],
                *[facts[key] for key in ("scope_ref", "owner_document_ref",
                    "worker_document_ref", "source_hdf_ref", "source_mf_ref",
                    "source_review_hdf_ref", "source_review_mf_ref",
                    "source_review_decision_ref", "build_request_ref")], *caller,
                *request["historical_cp369_archives"],
                *[request[key] for key in ("native_hdf_ref", "native_handoff_ref",
                   "native_historical_request_ref", "frozen_plan_ref")]]
    all_refs.extend(row["origin_ref"] for row in live["pending"])
    for qualifier_ref in (facts["source_qualification_ref"], live["qualification_ref"]):
        qualification = load(qualifier_ref)
        all_refs.extend(embedded_refs(qualification))
        all_refs.extend(embedded_refs(load(qualification["source_pending_ref"])))
    for value in (load(caller[0]), load(caller[1]), load(rh), load(rm),
                  load(decision_ref), load(request["native_hdf_ref"]),
                  load(request["native_handoff_ref"])):
        all_refs.extend(embedded_refs(value))
    for ref in (seed_witness_refs[0], seed_witness_refs[1], seed_witness_refs[3]):
        all_refs.extend(embedded_refs(load(ref)))
    if activation_refs:
        for index, ref in enumerate(activation_refs):
            if index != 2:  # The held original JSONL is raw bytes, not a JSON document.
                all_refs.extend(embedded_refs(load(ref)))
    for module in tuple(sys.modules.values()):
        for key in ("__file__", "__cached__"):
            path = getattr(module, key, None)
            if path and Path(path).is_file(): all_refs.append(pin(path))
    guard, count = held_guard(all_refs, exclude_pair=True)
    try:
        proposed = transformed_pair(copy.deepcopy(old_cp),copy.deepcopy(old_ow),facts,
                                    live,old_cp,old_ow,facts_ref)
        if mode == "activate":
            trusted = verified_module(TP, EXACT[str(TP)])
            transaction = trusted.update_pair(refs[:2],
                lambda cp,ow: transformed_pair(cp,ow,facts,live,old_cp,old_ow,facts_ref),
                N,"activate")
            require([pin(p) for p in CANON[2:]] == refs[2:], "SS_COMMANDS_CHANGED")
        else:
            transaction = None
            require([pin(p) for p in CANON] == refs, "CHECK_MODE_CANON_CHANGED")
    finally:
        cleanup = guard.close()
        save("source-guard.cleanup." + mode + ".root.json",cleanup)
        require(cleanup["closed"] and cleanup["retained_handles_count"] == 0
                and cleanup["errors"] == [], "REGISTER_GUARD_NOT_CLOSED")
    return save("registration." + mode + ".root.json", dict(
        schema="researchos.root-cp370-c19-two-dispatcher-registration-result.v1",
        mode=mode, transaction=transaction, source_guard_ref_count=count,
        complete_inverse=True, prior_failure_records_preserved=963,
        later_originals_registered=len(live["pending"]),
        proposed_after_refs=[{"path":str(path),"sha256":hashlib.sha256(encoded(value)).hexdigest(),
                              "bytes":len(encoded(value))}
                             for path,value in zip(CANON[:2],proposed)],
        SS_commands_unchanged=True, Native_rerun=False, dispatcher_run=False,
        formal_case_accepted_delta=0,parent_acceptance=False,formal_acceptance=False))


def main():
    require(len(sys.argv) == 8, "USAGE_MODE_INPUT3_LIVE3")
    mode = sys.argv[1]
    input_ref = {"path":sys.argv[2],"sha256":sys.argv[3],"bytes":int(sys.argv[4])}
    live_ref = {"path":sys.argv[5],"sha256":sys.argv[6],"bytes":int(sys.argv[7])}
    if mode == "build":
        require(load(input_ref)["live_ref"] == live_ref, "BUILD_LIVE_REF")
        output = build_root_docs(input_ref)
    else:
        output = register(mode,input_ref,live_ref)
    print(json.dumps(output,ensure_ascii=False),flush=True)


if __name__ == "__main__": main()
