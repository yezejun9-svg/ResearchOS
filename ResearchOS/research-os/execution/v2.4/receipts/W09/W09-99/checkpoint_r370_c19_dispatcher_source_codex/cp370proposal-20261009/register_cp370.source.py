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
SOURCE_REVIEW_SCHEMA = "researchos.w09-main-c19-two-dispatchers-independent-source-decision.v1"
SOURCE_SCOPE_SCHEMA = "researchos.w09-c19-main-two-dispatcher-scope.v1"
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
    require(Path(hdf_ref["path"]).name == "HDF.json"
            and Path(mf_ref["path"]).name == "MF.json"
            and Path(hdf_ref["path"]).parent == Path(mf_ref["path"]).parent
            and Path(hdf_ref["path"]).parent.parent == CALLER_SOURCE_ROOT,
            "CALLER_SOURCE_LOCATION")
    hdf, mf = load(hdf_ref), load(mf_ref)
    caller_ref = exact_ref(hdf["caller_source_ref"])
    contract_ref = exact_ref(hdf["root_contract_ref"])
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
    require(d.get("schema") == SOURCE_REVIEW_SCHEMA
            and d.get("decision") == "ACCEPTED_SOURCE_ONLY"
            and d.get("actor_role") == "INDEPENDENT_NON_AUTHOR"
            and type(d.get("actor_id")) is str
            and d["actor_id"] not in (ROOT, AUTHOR, "")
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
    return hdf_ref, mf_ref, decision_ref, d


def validate_live(live):
    require(type(live) is dict and set(live) == {"schema", "issued_by", "created_utc",
            "source_cutoff", "next_original_failure_ordinal", "pending"}, "LIVE_FIELDS")
    require(live["schema"] == "researchos.root-postseal-live-diagnostic-context.v1"
            and live["issued_by"] == ROOT
            and live["source_cutoff"] == {"highest_ordinal": 965, "next_failure_ordinal": 966}
            and type(live["next_original_failure_ordinal"]) is int
            and live["next_original_failure_ordinal"] >= 970
            and type(live["pending"]) is list,
            "LIVE_NO_RESET")
    require([row.get("ordinal") for row in live["pending"]] ==
            list(range(966, live["next_original_failure_ordinal"])), "LIVE_CONTIGUOUS_ORIGINALS")
    for row in live["pending"]:
        require(type(row) is dict and set(row) == {"ordinal", "origin_ref", "description",
                "actual_outer_exit", "actual_python_exit", "actual_native_exit"}, "LIVE_ROW_FIELDS")
        require(type(row["ordinal"]) is int and type(row["description"]) is str,
                "LIVE_ROW_TYPED")
        for field in ("actual_outer_exit", "actual_python_exit", "actual_native_exit"):
            require(row[field] is None or type(row[field]) is int, "LIVE_EXIT_TYPED")
        exact_ref(row["origin_ref"])


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
            "authorized_output_root", "live_ref", "no_actual_consumer_run"},
            "BUILD_REQUEST_EXACT_FIELDS")
    require(request["schema"] == "researchos.root-cp370-c19-dispatcher-build-request.v1"
            and request["issued_by"] == ROOT
            and request["no_actual_consumer_run"] is True
            and type(request["created_utc"]) is str, "BUILD_ROOT_ONLY")
    _future(request["lease_expires_at"])
    output_root = Path(request["authorized_output_root"])
    require(output_root.is_absolute() and output_root.resolve().is_relative_to(ROOT_OUTPUT_BOUNDARY)
            and output_root != ROOT_OUTPUT_BOUNDARY, "OUTPUT_ROOT_SCOPE")
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
    validate_live(live)


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
        require(not any(str(path).casefold() in unique for path in CANON[:2]),
                "CANON_PAIR_ONLY_TRANSACTION")
    guard = gm.SourceReadGuard(per_file_cap=256*1024*1024, total_cap=2*1024*1024*1024)
    guard.acquire(list(unique.values()))
    return guard, len(unique)


def build_root_docs(request_ref):
    """Root-only later build. Never called during Source preparation."""
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
                 authorized_output_root=str(Path(request["authorized_output_root"]).resolve()))
    caller_module = verified_module(caller[2]["path"], (caller[2]["sha256"], caller[2]["bytes"]))
    caller_module.validate_scope(scope)
    input_refs = [request_ref, request["live_ref"], *refs, rh, rm, decision_ref,
                  *[request[k] for k in ("native_hdf_ref", "native_handoff_ref",
                   "native_historical_request_ref", "frozen_plan_ref")],
                  *request["historical_cp369_archives"], *caller]
    for value in (load(caller[0]), load(caller[1]), load(rh), load(rm),
                  load(decision_ref), load(request["native_hdf_ref"]),
                  load(request["native_handoff_ref"])):
        input_refs.extend(embedded_refs(value))
    input_refs.extend(row["origin_ref"] for row in live["pending"])
    input_refs.extend(pin(p) for p in (BASE, GP, TP, __file__, sys.executable))
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
    validate_live(live)
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
    seen = {row.get("origin_key") for row in cp["failure_counters"]}
    for row in live["pending"]:
        origin = row["origin_ref"]
        key = hashlib.sha256((origin["sha256"] + "#" + str(row["ordinal"])).encode()).hexdigest()
        require(key not in seen, "ORIGINAL_DUPLICATE")
        seen.add(key)
        cp["failure_counters"].append(dict(origin_key=key,evidence_ref=origin,
            original_payload=dict(observed_ordinal=row["ordinal"],
                immutable_origin_ref=origin, actual_outer_exit=row["actual_outer_exit"],
                actual_python_exit=row["actual_python_exit"],
                actual_native_exit=row["actual_native_exit"], diagnostic=row["description"]),
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
              updated_at=facts["created_utc"], updated_by=ROOT,
              note="Root registered exact C19 Main two-dispatcher caller slice; Source-qualified only, no consumer or formal acceptance.")
    ow.update(revision=174,updated_at=facts["created_utc"],updated_by=ROOT)
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
    require(type(facts) is dict and set(facts) == {"schema", "issued_by", "created_utc",
            "before_canonical_refs", "scope_ref", "owner_document_ref",
            "worker_document_ref", "source_hdf_ref", "source_mf_ref",
            "source_review_hdf_ref", "source_review_mf_ref",
            "source_review_decision_ref", "build_request_ref", "live_ref",
            "source_cutoff", "root_next_failure_ordinal_live", "no_actual_consumer_run",
            "formal_dispatcher", "formal_acceptance", "parent_acceptance",
            "formal_case_accepted_delta"}, "FACTS_KEYS")
    require(facts.get("schema") == "researchos.root-cp370-c19-two-dispatcher-registration-facts.v1"
            and facts.get("issued_by") == ROOT and facts.get("live_ref") == live_ref
            and facts.get("source_cutoff") == {"highest_ordinal":965,"next_failure_ordinal":966}
            and type(facts.get("root_next_failure_ordinal_live")) is int
            and facts["root_next_failure_ordinal_live"] == live["next_original_failure_ordinal"]
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
    validate_live(live)
    refs, old_cp, old_ow = check_before_pair()
    require(facts["before_canonical_refs"] == refs, "FACTS_BEFORE_CANON")
    caller = ensure_caller_source(facts["source_hdf_ref"], facts["source_mf_ref"])
    require(facts["source_hdf_ref"] == caller[0]
            and facts["source_mf_ref"] == caller[1], "FACTS_SOURCE")
    request = load(facts["build_request_ref"])
    validate_root_build_request(request, live)
    require(request["created_utc"] == facts["created_utc"]
            and request["live_ref"] == live_ref
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
            and scope["authorized_output_root"] == str(Path(request["authorized_output_root"]).resolve()),
            "SCOPE_BUILD_REQUEST_BINDING")
    caller_module = verified_module(caller[2]["path"], (caller[2]["sha256"], caller[2]["bytes"]))
    caller_module.validate_scope(scope)
    caller_module.validate_source_review(decision, scope, *caller)
    all_refs = [facts_ref, live_ref, pin(__file__), pin(sys.executable),
                pin(BASE), pin(GP), pin(TP), *refs[2:],
                *[facts[key] for key in ("scope_ref", "owner_document_ref",
                    "worker_document_ref", "source_hdf_ref", "source_mf_ref",
                    "source_review_hdf_ref", "source_review_mf_ref",
                    "source_review_decision_ref", "build_request_ref")], *caller,
                *request["historical_cp369_archives"],
                *[request[key] for key in ("native_hdf_ref", "native_handoff_ref",
                   "native_historical_request_ref", "frozen_plan_ref")]]
    all_refs.extend(row["origin_ref"] for row in live["pending"])
    for value in (load(caller[0]), load(caller[1]), load(rh), load(rm),
                  load(decision_ref), load(request["native_hdf_ref"]),
                  load(request["native_handoff_ref"])):
        all_refs.extend(embedded_refs(value))
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
