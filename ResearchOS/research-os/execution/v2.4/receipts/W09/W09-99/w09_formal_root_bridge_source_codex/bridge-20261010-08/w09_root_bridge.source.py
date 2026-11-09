"""Source-only W09 Root bridge. Runtime stages require a real Root audit grant.
No import-time I/O; no producer, model, SQL or Go execution is implemented.
"""
from __future__ import annotations
import argparse
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import types

ROOT = Path(r"D:\作品集\ResearchOS\research-os")
HERE = Path(__file__).resolve().parent
AUTHOR = "codex:/root/full_w09_source_review"

AUTHOR_BACKEND = "/root/full_w09_source_review"
BRIDGE_GENERATION = "bridge-20261010-08"
PUBLIC_TEMP = Path(r"C:\Users\yqyyds\.researchos\w09-native-v5")
RESOURCE_PARENT_REF = {'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W09\\W09-99\\checkpoint_r370_c19_dispatcher_source_root\\cp370-c19-20261009\\physical-C-native-v5-resource-parents.closed.root.json', 'sha256': 'b85a53b28b489526cf7e7e68acb784ae0661283bea88b5e8c03e152e924ad698', 'bytes': 2199}
RESOURCE_AUDIT_REF = {'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W09\\W09-99\\checkpoint_r370_c19_dispatcher_source_root\\cp370-c19-20261009\\w09.physical-C-native-v5-resource-parent.actual-audit.root.json', 'sha256': 'a5cd6eaa9c8880bfa9148cb9235fe92fc75f5af651ed2f045f6182962364751b', 'bytes': 1103}
RESOURCE_OWNER_REF = {'path': 'C:\\Users\\yqyyds\\.researchos\\w09-native-v5\\RESOURCE_OWNER.json', 'sha256': 'd8de9a1122404c0f3a8edc4874ea3f95446cf743353428f5e91d8934b3027f12', 'bytes': 254}
ROOT_RESOURCE_AUDIT_PATH = 'C:\\Users\\yqyyds\\.codex\\sessions\\2026\\10\\06\\rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl'
ROOT_ACTOR = "codex:/root"
VERIFIER = "/root/backup_regression_resources"
THREAD = "01a11007-5233-7ca1-b71f-9e9e5ce84c98"
W = ROOT / "execution/v2.4/receipts/W09/W09-99"
PLAN = ROOT.parent / "ResearchOS_Implementation_Package_v2.4/contracts/execution.plan.json"
CANON = [ROOT / "execution/v2.4" / (n + ".json") for n in
         ("checkpoint", "path_ownership", "step_state", "commands")]
ROLE_PATH = "execution/v2.4/root_delivery_captures/W09/W09-99/execution-roles.json"
INDEX_PATH = "execution/v2.4/root_delivery_captures/W09/W09-99/index.json"
ORIGIN = "execution/v2.4/root_original_events/W09/W09-99/"
ROUTES = (("test.retrieval", "W09-G01", ""), ("test.retrieval", "W09-G02", ""),
          ("test.research.fixture", "", "C19"), ("test.retrieval", "", "C19"),
          ("test.retrieval", "", "A06"), ("test.security", "", "A06"))
NEW = tuple(r for r in ROUTES if r[2] != "C19")
GUARD = "execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
TP = "execution/v2.4/receipts/W05/W05-99/mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py"
OWNED = "execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
TRUSTED = {
 "execution/v2.4/formal_case_index.py": ("e08a7f605ca12d79c672b6af0360a02b26e2231d2a602207d0ea6a37f24f7b0b", 71844),
 "execution/v2.4/formal_profile_w09.py": ("1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087", 71403),
 "execution/v2.4/commands.json": ("12141a8ba01d34c7181ee35e054f4762732ca8627cbee87271610e65d6f28b97", 67323),
 "execution/command_dispatcher/dispatch.py": ("69c94d63050fb2274a4d995742e934e85c52bd43e9afd5bf9640a5f3404061e4", 12498),
 GUARD: ("e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85", 11404),
 TP: ("094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9", 6877),
 OWNED: ("6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad", 18901),
}

def need(ok, code):
    if not ok:
        raise ValueError(code)

def decode(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    def bad(value):
        raise ValueError("NONFINITE_JSON:" + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)

def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def stamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    need(result.tzinfo is not None, "TIMEZONE_REQUIRED")
    return result

def physical(path):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    need(not path.is_symlink() and not path.is_junction(), "PATH_ALIAS")
    result = path.resolve(strict=True)
    need(result.is_relative_to(ROOT) or result == PLAN, "REPO_PATH_REQUIRED")
    for parent in path.parents:
        if parent == ROOT.parent:
            break
        need(not parent.is_symlink() and not parent.is_junction(), "PARENT_ALIAS")
    return result

def pin(path, relative=False, size=True):
    path = physical(path)
    raw = path.read_bytes()
    ref = {"path": path.relative_to(ROOT).as_posix() if relative else str(path), "sha256": sha(raw)}
    if size:
        ref["bytes"] = len(raw)
    return ref

def checked(ref):
    need(type(ref) is dict and {"path", "sha256"} <= set(ref), "REF_REQUIRED")
    path = physical(ref["path"])
    raw = path.read_bytes()
    need(sha(raw) == ref["sha256"] and ("bytes" not in ref or len(raw) == ref["bytes"]), "PIN_CHANGED")
    return raw

def ref2(ref):
    return {key: ref[key] for key in ("path", "sha256")}

def document(ref):
    return decode(checked(ref))

def references(value):
    if type(value) is dict:
        if {"path", "sha256"} <= set(value):
            yield {k: value[k] for k in ("path", "sha256", "bytes") if k in value}
        else:
            for item in value.values():
                yield from references(item)
    elif type(value) is list:
        for item in value:
            yield from references(item)

def module(relative):
    path = ROOT / relative
    ref = pin(path)
    need((ref["sha256"], ref["bytes"]) == TRUSTED[relative], "TRUSTED_SOURCE_CHANGED")
    value = types.ModuleType("w09_bridge_" + path.stem)
    value.__file__ = str(path)
    sys.modules[value.__name__] = value
    exec(compile(checked(ref), str(path), "exec"), value.__dict__)
    return value

def save(path, value, raw=False):
    path = Path(path)
    need(path.parent.resolve().is_relative_to(ROOT), "OUTPUT_BOUNDARY")
    with path.open("xb") as stream:
        stream.write(value if raw else encoded(value))
        stream.flush()
        os.fsync(stream.fileno())
    return pin(path, True)


def environment_directory(value):
    """Only the fixed physical C parent is admissible as shared TEMP/TMP."""
    need(type(value) is str and value == str(PUBLIC_TEMP), "EXACT_SHARED_TEMP_PARENT")
    path = Path(value)
    need(path.is_absolute() and path.resolve(strict=True) == path, "ENVIRONMENT_PATH_ALIAS")
    for entry in (path, *path.parents):
        stat = entry.lstat()
        need(entry.is_dir() and not entry.is_symlink() and not entry.is_junction()
             and not (getattr(stat, "st_file_attributes", 0) & 0x400), "ENVIRONMENT_REPARSE")
    return path

def require_process_temp():
    """Fail before Main import or verification; never reset tempfile's cache."""
    parent = environment_directory(os.environ.get("TEMP"))
    need(environment_directory(os.environ.get("TMP")) == parent, "SAME_TEMP_TMP")
    import tempfile
    need(str(Path(tempfile.gettempdir())) == str(parent), "ACTUAL_PROCESS_TEMP_CACHE")
    return parent

def resource_environment():
    """Exact fixed resource metadata is read separately from general repo refs."""
    parent = environment_directory(str(PUBLIC_TEMP))
    resource = document(RESOURCE_PARENT_REF)
    need(resource["actor_id"] == ROOT_ACTOR and resource["resource_scope_only"] is True
         and resource["execution_grant"] is False and resource["RootScope_issued"] is False
         and resource["Native_calls"] == 0
         and resource["exact_parent_paths"] == [str(parent.parent), str(parent)]
         and resource["resource_owner_marker_ref"] == RESOURCE_OWNER_REF, "ROOT_RESOURCE_ONLY")
    marker = parent / "RESOURCE_OWNER.json"
    stat = marker.lstat()
    need(marker.resolve(strict=True) == marker and not marker.is_symlink() and not marker.is_junction()
         and not (getattr(stat, "st_file_attributes", 0) & 0x400), "RESOURCE_MARKER_ALIAS")
    raw = marker.read_bytes()
    need(RESOURCE_OWNER_REF == {"path":str(marker), "sha256":sha(raw), "bytes":len(raw)}, "RESOURCE_MARKER_PIN")
    need(decode(raw) == {"schema":"researchos.w09-native-private-resource-owner.v1",
         "project_id":"aede0678-7308-43dc-b9f2-cfe3d90cfdfb",
         "repository_root":str(ROOT), "scratch_parent":str(parent)}, "PROJECT_RESOURCE_OWNER")
    identity_ref = resource["project_identity_ref"]
    need(document(identity_ref)["project_id"] == "aede0678-7308-43dc-b9f2-cfe3d90cfdfb", "RESOURCE_PROJECT_IDENTITY")
    audit = document(RESOURCE_AUDIT_REF)
    need(audit["schema"] == "researchos.w09-native-producer.actual-audit.v1"
         and audit["actor_id"] == ROOT_ACTOR and audit["Root_thread_id"] == THREAD
         and audit["source_audit_path"] == ROOT_RESOURCE_AUDIT_PATH
         and audit["binding_sha256"] == RESOURCE_PARENT_REF["sha256"], "ROOT_RESOURCE_ACTUAL_BINDING")
    lines = checked(audit["original_capture_ref"]).splitlines(keepends=True)
    need(len(lines) == 3 and all(line.endswith(b"\n") for line in lines), "THREE_RESOURCE_ORIGINAL_LINES")
    header, call, result = [decode(line) for line in lines]
    first, last = call.get("payload", {}), result.get("payload", {})
    need(header.get("type") == "session_meta" and header.get("ordinal") == 0
         and header.get("payload", {}).get("id") == THREAD
         and call.get("type") == result.get("type") == "response_item"
         and type(call.get("ordinal")) is int and type(result.get("ordinal")) is int
         and 0 < call["ordinal"] < result["ordinal"]
         and first.get("type") in ("function_call", "custom_tool_call")
         and last.get("type") in ("function_call_output", "custom_tool_call_output")
         and type(first.get("call_id")) is str and bool(first["call_id"])
         and first["call_id"] == last.get("call_id")
         and RESOURCE_PARENT_REF["sha256"] in lines[1].decode("utf-8")+lines[2].decode("utf-8"),
         "ROOT_RESOURCE_ACTUAL_TOOL_PAIR")
    offsets, digests = audit["source_line_offsets"], audit["original_line_sha256"]
    size = audit["source_prefix_size_observed"]
    need(type(offsets) is list and len(offsets) == 3 and offsets == sorted(set(offsets))
         and offsets[0] == 0 and all(type(x) is int and x >= 0 for x in offsets)
         and type(digests) is list and len(digests) == 3 and type(size) is int and size > 0,
         "RESOURCE_AUDIT_RANGES")
    ranges = []
    with Path(ROOT_RESOURCE_AUDIT_PATH).open("rb") as stream:
        for offset, digest, line in zip(offsets, digests, lines):
            need(offset+len(line) <= size and sha(line) == digest, "RESOURCE_AUDIT_DIGEST")
            stream.seek(offset)
            need(stream.read(len(line)) == line, "ACTUAL_ROOT_RESOURCE_BYTES")
            ranges.append({"path":ROOT_RESOURCE_AUDIT_PATH,"offset":offset,"bytes":len(line),"sha256":digest})
    return {"refs":[RESOURCE_PARENT_REF, RESOURCE_AUDIT_REF, RESOURCE_OWNER_REF,
                    identity_ref, audit["original_capture_ref"]], "audit_ranges":ranges}

def environment_request(req):
    need(req["bridge_temp_parent"] == str(PUBLIC_TEMP)
         and req["resource_parent_ref"] == RESOURCE_PARENT_REF
         and req["resource_audit_ref"] == RESOURCE_AUDIT_REF
         and req["resource_owner_sha256"] == RESOURCE_OWNER_REF["sha256"], "ROOT_REQUEST_RESOURCE_BINDING")
    require_process_temp()
    return resource_environment()


def engine():
    api = module("execution/v2.4/formal_case_index.py")
    reader = api.Reader(ROOT)
    profile = module("execution/v2.4/formal_profile_w09.py")
    reader.w09_audit_ranges = []
    reader.w09_owned_inventories = []
    return api, reader, profile

def current4(refs):
    need(type(refs) is list and len(refs) == 4, "CURRENT4")
    need([physical(r["path"]) for r in refs] == CANON, "CURRENT4_ORDER")
    need(all(set(r)=={"path","sha256","bytes"} and Path(r["path"]).is_absolute() for r in refs),
         "CURRENT4_ABSOLUTE_EXACT_REFS")
    for ref in refs:
        checked(ref)
    need((refs[3]["sha256"], refs[3]["bytes"]) == TRUSTED["execution/v2.4/commands.json"], "CM40_ONLY")
    return [document(r) for r in refs]

def source_review(req, api, reader, profile):
    review = document(req["source_review_ref"])
    need(review.get("decision") == "ACCEPTED_SOURCE_ONLY" and review.get("formal_acceptance") is False,
         "INDEPENDENT_SOURCE_REVIEW_REQUIRED")
    need(review.get("reviewer_id") not in {AUTHOR, AUTHOR_BACKEND, ROOT_ACTOR, "/root"}
         and review.get("source_ref") == req["bridge_source_ref"], "SOURCE_REVIEW_BINDING")
    need(physical(req["bridge_source_ref"]["path"]) == Path(__file__).resolve(), "THIS_SOURCE_ONLY")
    checked(req["bridge_source_ref"])
    need(AUTHOR == "codex:" + AUTHOR_BACKEND, "FIXED_SOURCE_BACKEND_IDENTITY")
    need(physical(req["consumer_launcher_ref"]["path"]) == HERE / "consumer_launch.source.py"
         and review.get("consumer_launcher_ref") == req["consumer_launcher_ref"], "REVIEWED_CONSUMER_LAUNCHER")
    checked(req["consumer_launcher_ref"])
    need(physical(req["source_hdf_ref"]["path"]) == HERE / "HDF.json"
         and physical(req["source_mf_ref"]["path"]) == HERE / "MF.json"
         and review.get("source_hdf_ref") == req["source_hdf_ref"]
         and review.get("source_mf_ref") == req["source_mf_ref"], "SOURCE_PACKAGE_REVIEW_BINDING")
    handoff, manifest = document(req["source_hdf_ref"]), document(req["source_mf_ref"])
    need(handoff["source_ref"] == req["bridge_source_ref"]
         and handoff["consumer_launcher_ref"] == req["consumer_launcher_ref"]
         and handoff["source_author"] == AUTHOR and handoff["source_author_backend"] == AUTHOR_BACKEND
         and req["bridge_source_ref"] in manifest["members"]
         and req["consumer_launcher_ref"] in manifest["members"], "SOURCE_PACKAGE_MEMBERS")
    proof = req["source_review_audit"]
    need(proof["actor_id"] == review["reviewer_id"]
         and proof["raw_ref"]["sha256"] == req["source_review_ref"]["sha256"], "REVIEW_ACTUAL_AUTHOR")
    profile._role_audit(api._profile_api(), reader, proof, review)

def root_request(ref, stage):
    req = document(ref)
    need(req.get("schema") == "researchos.w09-root-bridge-request.v1"
         and req.get("actor_id") == ROOT_ACTOR and req.get("stage") == stage
         and req.get("Root_thread_id") == THREAD, "ROOT_REQUEST")
    need(stamp(req["expires_at"]) > datetime.now(timezone.utc) >= stamp(req["created_at"]), "FINITE_REQUEST")
    environment = environment_request(req)
    cp, ow, ss, cm = current4(req["current4"])
    need(cp.get("project_id") == "aede0678-7308-43dc-b9f2-cfe3d90cfdfb"
         and ow.get("active_integrator", {}).get("id") == ROOT_ACTOR, "ROOT_IDENTITY")
    need(ow["card_path_bindings"]["W09-99"]["owner"] == ROOT_ACTOR, "ROOT_W09_OWNER")
    api, reader, profile = engine()
    reader.w09_audit_ranges.extend(environment["audit_ranges"])
    source_review(req, api, reader, profile)
    # The noncircular, independently published grant binds this exact request hash.
    grant = document(req["grant_ref"])
    need(grant.get("issued_by") == ROOT_ACTOR and grant.get("stage") == stage
         and grant.get("request_body_sha256") == sha(encoded({k:v for k,v in req.items() if k not in {"grant_ref","grant_audit"}})),
         "ROOT_GRANT_BINDING")
    profile._role_audit(api._profile_api(), reader, req["grant_audit"], grant)
    need(req["grant_audit"]["actor_id"] == ROOT_ACTOR
         and req["grant_audit"]["raw_ref"]["sha256"] == req["grant_ref"]["sha256"], "ROOT_GRANT_ORIGINAL")
    out = Path(req["output_directory"])
    need(out.is_absolute() and out.parent.resolve().is_relative_to(W)
         and out != HERE and not out.exists(), "UNIQUE_ROOT_OUTPUT")
    out.mkdir()
    return req, out, (api, reader, profile)

def snapshot(api, reader, context=None, authority=False):
    data = {"files": {str(k):v for k,v in reader.read_hashes.items()
                      if authority or canonical_identity(k) not in CANON},
            "inventories": list(reader.w09_owned_inventories),
            "audit_ranges": list(reader.w09_audit_ranges)}
    if context:
        data["inventories"].append({"repo": str(ROOT), "coverage": context["source_coverage"],
                                    "paths": [r["path"] for r in context["version_vector"]["source_files"]]})
    need(api.recheck_inputs(data)["status"] == "PASS", "CAS_INPUT_DRIFT")
    return data

def canonical_identity(path):
    """Use physical()'s resolved identity; literal refs retain their exact spelling."""
    value = Path(path)
    if not value.is_absolute():
        value = ROOT / value
    return value.resolve(strict=True)

def validate_persistent_snapshot(data):
    need(type(data) is dict and type(data.get("files")) is dict,
         "DEPENDENCY_SNAPSHOT_REQUIRED")
    need(not any(canonical_identity(path) in CANON for path in data["files"]),
         "HISTORICAL_SNAPSHOT_CONTAINS_CANON")
    return data

def freeze_current4(req, out):
    """Called only by propose inside its current4 SourceReadGuard."""
    need(type(req["current4"]) is list and len(req["current4"]) == 4
         and [canonical_identity(r["path"]) for r in req["current4"]] == CANON,
         "ARCHIVE_EXACT_CANON_ORDER")
    archives = []
    for index, ref in enumerate(req["current4"]):
        need(set(ref) == {"path", "sha256", "bytes"} and type(ref["bytes"]) is int
             and Path(ref["path"]).is_absolute(), "ARCHIVE_EXACT_CANON_REF")
        raw = checked(ref)
        archive = save(out / ("canonical-" + CANON[index].stem + ".original.json"), raw, raw=True)
        need(archive["sha256"] == ref["sha256"] and archive["bytes"] == ref["bytes"],
             "ARCHIVE_ORIGINAL_BYTES")
        archives.append(archive)
    return {"schema":"researchos.w09-bridge-historical-current4.v1",
            "meaning":"ARCHIVED_HISTORICAL_CURRENT4_NOT_LIVE_AUTHORITY",
            "canonical_refs":copy.deepcopy(req["current4"]),"archive_refs":archives}

def proposal_archive_refs(proposal, proposal_ref, req):
    """Retain historical identity only with four exact immutable original archives."""
    need(proposal.get("schema") == "researchos.w09-bridge-proposal.v1"
         and proposal.get("generation") == BRIDGE_GENERATION
         and proposal.get("source_ref") == req["bridge_source_ref"]
         and proposal.get("source_review_ref") == req["source_review_ref"],
         "HISTORICAL_PROPOSAL_IDENTITY")
    proof = proposal.get("historical_current4")
    need(type(proof) is dict and set(proof) == {"schema","meaning","canonical_refs","archive_refs"}
         and proof["schema"] == "researchos.w09-bridge-historical-current4.v1"
         and proof["meaning"] == "ARCHIVED_HISTORICAL_CURRENT4_NOT_LIVE_AUTHORITY",
         "EXPLICIT_HISTORICAL_CURRENT4_PROOF")
    old, archives = proof["canonical_refs"], proof["archive_refs"]
    need(type(old) is list and type(archives) is list and len(old) == len(archives) == 4
         and old == proposal.get("current4")
         and [canonical_identity(ref["path"]) for ref in old] == CANON,
         "HISTORICAL_CURRENT4_ORDER_AND_IDENTITY")
    need(old[2:] == req["current4"][2:], "HISTORICAL_SS_CM_DRIFT")
    home = physical(proposal_ref["path"]).parent
    for index, (identity, archive) in enumerate(zip(old, archives)):
        need(type(identity) is dict and set(identity) == {"path","sha256","bytes"}
             and Path(identity["path"]).is_absolute() and type(identity["bytes"]) is int,
             "HISTORICAL_EXACT_CANON_REF")
        need(type(archive) is dict and set(archive) == {"path","sha256","bytes"}
             and type(archive["bytes"]) is int
             and physical(archive["path"]) == home / ("canonical-" + CANON[index].stem + ".original.json")
             and archive["sha256"] == identity["sha256"] and archive["bytes"] == identity["bytes"],
             "HISTORICAL_ARCHIVE_SAME_PROPOSAL_AND_BYTES")
        checked(archive)
    validate_persistent_snapshot(proposal["dependency_snapshot"])
    return archives

def historical_dependency_refs(value, ref, req, name):
    """Archive-covered current4 and typed audit ranges retain their dedicated checks."""
    cleaned = copy.deepcopy(value)
    archives = []
    if name == "proposal_ref":
        archives = proposal_archive_refs(value, ref, req)
        del cleaned["current4"]
        del cleaned["historical_current4"]
    if "dependency_snapshot" in cleaned:
        data = validate_persistent_snapshot(cleaned["dependency_snapshot"])
        if "audit_ranges" in data:
            ranges = data["audit_ranges"]
            need(type(ranges) is list, "HISTORICAL_AUDIT_RANGES_REQUIRED")
            for item in ranges:
                need(type(item) is dict and set(item) == {"path", "offset", "bytes", "sha256"}
                     and type(item["path"]) is str and Path(item["path"]).is_absolute()
                     and type(item["offset"]) is int and item["offset"] >= 0
                     and type(item["bytes"]) is int and item["bytes"] > 0
                     and type(item["sha256"]) is str
                     and re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is not None,
                     "HISTORICAL_AUDIT_RANGE_SHAPE")
                need(canonical_identity(item["path"]) not in CANON,
                     "UNDECLARED_HISTORICAL_CANONICAL_REFERENCE")
            del data["audit_ranges"]
    refs = list(references(cleaned))
    need(not any(canonical_identity(item["path"]) in CANON for item in refs),
         "UNDECLARED_HISTORICAL_CANONICAL_REFERENCE")
    return refs + archives

def request_dependency_refs(req):
    """Every direct request Canon ref must equal the fresh authority vector."""
    refs = list(references(req))
    authority = {canonical_identity(ref["path"]):ref for ref in req["current4"]}
    for ref in refs:
        path = canonical_identity(ref["path"])
        if path in CANON:
            need(ref == authority.get(path), "REQUEST_CANONICAL_AUTHORITY_CONFLICT")
    return refs


def native_inputs(req, eng):
    api, reader, profile = eng
    context = document(req["context_seed_ref"])
    pinned = profile._vector(api._profile_api(), reader, context)
    closure = profile._trusted_closure(api._profile_api(), reader, pinned)
    router = profile._router_contract(api._profile_api(), reader, pinned)
    sources = profile._producer_sources(api._profile_api(), reader, pinned)
    rows = context["registered_commands"]
    need(len(rows) == 6 and {tuple(r[k] for k in ("command_key","check_id","case_id")) for r in rows} == set(ROUTES),
         "EXACT_SIX_ROUTES")
    reader.bridge_native_checks = {}
    for row in rows:
        # All four selector Native runs must pass Main current Source21/mode gates.
        route = tuple(row[k] for k in ("command_key","check_id","case_id"))
        reader.bridge_native_checks[route] = profile._native(
            api._profile_api(), reader, row, closure, router, pinned, sources)
    return context, pinned, closure, router, sources


def consumer_plan(req, eng, context, pinned):
    """Choose four or six consumers only after Main has checked current Native evidence."""
    api, reader, profile = eng
    policy = req["c19_policy"]
    need(policy in {"REUSE_CURRENT_SOURCE21", "RUN_CURRENT_CM40"}, "C19_POLICY")
    proofs = getattr(reader, "bridge_native_checks", {})
    need(set(proofs) == set(ROUTES), "MAIN_CURRENT_NATIVE_GATE_REQUIRED")
    # Report identity and selector semantics are validated by Main _native, not by this map.
    selected = {}
    for row in context["registered_commands"]:
        key = row["check_id"] or row["case_id"]
        pair = (row["native_report_ref"]["path"], row["native_report_ref"]["sha256"],
                row["native_tool_run_ref"]["path"], row["native_tool_run_ref"]["sha256"])
        need(key not in selected or selected[key] == pair, "SAME_SELECTOR_NATIVE_BUNDLE")
        selected[key] = pair
    need(set(selected) == {"W09-G01","W09-G02","C19","A06"}
         and len({value[0] for value in selected.values()}) == 4, "FOUR_CURRENT_NATIVE_REPORTS")
    if policy == "RUN_CURRENT_CM40":
        return ROUTES
    # No fallback to stale history: a rejected Source21 or historical pin stops the stage.
    registry_path = reader.path("execution/v2.4/commands.json")
    registry = reader.read(registry_path)
    authority = document(req["c19_reuse_registry_ref"])
    need(authority["roles"]["executor"] == ROOT_ACTOR, "C19_REUSE_ACTUAL_EXECUTOR")
    for row in context["registered_commands"]:
        route = tuple(row[k] for k in ("command_key","check_id","case_id"))
        if route[2] != "C19":
            continue
        receipt = profile._doc(api._profile_api(), reader, row["receipt_ref"], "execution/invocations/")
        need(profile._historical_registry(api._profile_api(), reader, row, receipt, registry,
                                         pinned[registry_path]) is True, "ONLY_FIXED_CM39_C19_REUSE")
        report, native, mode, intervals = proofs[route]
        output = reader.document(receipt["stdout"])
        need(output.get("native_tool_run_ref") == row["native_tool_run_ref"]["path"]
             and output.get("mode_evidence") == mode
             and any(ref.get("path") == row["native_report_ref"]["path"]
                     and ref.get("sha256") == row["native_report_ref"]["sha256"]
                     for ref in output.get("source_pins", [])), "HISTORICAL_CONSUMER_SAME_NATIVE")
        decision = document(row["mode_decision_ref"])
        profile._route_execution_actor(api._profile_api(), reader, row, receipt, decision, authority)
    return NEW

def seed(req, out, eng):
    api, reader, profile = eng
    product = decode(checked(req["context_input_ref"]))
    sources = set(profile.MINIMUM_SOURCE)
    producer = ast.parse((ROOT/"ops/ci/retrieval.py").read_bytes())
    inventories = [ast.literal_eval(node.value) for node in producer.body if isinstance(node,ast.Assign)
                   and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=="SOURCES"]
    need(len(inventories)==1 and len(inventories[0])==21,"PRODUCER_SOURCE21")
    sources.update(inventories[0])
    for directory in ("internal/domain","adapters/retrieval"):
        sources.update(p.relative_to(ROOT).as_posix() for p in (ROOT/directory).glob("*.go") if p.is_file())
    vector = copy.deepcopy(product["version_vector"])
    vector["source_files"] = [pin(ROOT/path,True,False) for path in sorted(sources)]
    need(not any(physical(r["path"]) in CANON[:2] for r in vector["input_files"]),"NO_MUTABLE_CONTEXT_CP_OW")
    context = dict(product, schema="researchos.w09.current-context.v1", task_id="W09",step_id="W09-99",
                   executor_id=ROOT_ACTOR, created_at=utc(), version_vector=vector)
    context["source_coverage"]={"roots":[{"path":d,"patterns":["*.go"]} for d in ("internal/domain","adapters/retrieval")],
       "exact_files":sorted(sources),"paths_sha256":api.object_sha256(sorted(sources))}
    profile._vector(api._profile_api(),reader,context)
    return {"schema":"researchos.w09-bridge-context-seed.v1","context_ref":save(out/"context-seed.json",context),
            "dependency_snapshot":snapshot(api,reader,context),"formal_acceptance":False}

def propose(req, out, eng):
    api, reader, profile = eng
    context, pinned, *_ = native_inputs(req, eng)
    planned = consumer_plan(req, eng, context, pinned)
    need(context["executor_id"] == ROOT_ACTOR, "ROOT_EXECUTOR")
    lease = req["lease_expires_at"]
    need(datetime.now(timezone.utc) < stamp(lease) <= stamp(req["expires_at"]), "FINITE_LEASE")
    historical = freeze_current4(req, out)
    common = {"issued_by": ROOT_ACTOR, "source_actor": AUTHOR_BACKEND, "source_author_canonical": AUTHOR,
              "generation": BRIDGE_GENERATION, "source_ref": req["bridge_source_ref"],
              "source_hdf_ref": req["source_hdf_ref"], "source_mf_ref": req["source_mf_ref"],
              "bridge_temp_parent": req["bridge_temp_parent"],
              "resource_parent_ref": req["resource_parent_ref"], "resource_audit_ref": req["resource_audit_ref"],
              "resource_owner_sha256": req["resource_owner_sha256"],
              "source_review_ref": req["source_review_ref"], "created_at": utc(), "current4": req["current4"]}
    route_bindings = [dict(zip(("command_key","check_id","case_id"), route)) for route in planned]
    routes = list(dict.fromkeys(route[0] for route in planned))
    scope = dict(common, schema="researchos.w09-full-formal-consumers-scope.v1",
                 slice_id="W09_FULL_FORMAL_CONSUMERS", routes=routes, route_bindings=route_bindings)
    scope_ref = save(out / "scope.json", scope)
    assembly = dict(common, schema="researchos.w09-full-formal-assembly-scope.v1",
                    slice_id="W09_FULL_FORMAL_ASSEMBLY", routes=[])
    assembly_ref = save(out / "assembly-scope.json", assembly)
    docs = {}
    for name, sr, slice_id, rs in (("consumers",scope_ref,scope["slice_id"],routes),
                                    ("assembly",assembly_ref,assembly["slice_id"],[])):
        owner = {"schema": "researchos.w09-root-owner.v1", "owner_id": ROOT_ACTOR,
                 "selected_worker_id": ROOT_ACTOR, "slice_id": slice_id, "scope_ref": sr,
                 "lease_status": "ACTIVE", "lease_expires_at": lease, "routes": rs,
                 "source_ref": req["bridge_source_ref"], "source_review_ref": req["source_review_ref"],
                 "route_bindings": route_bindings if name == "consumers" else []}
        docs[name] = {"scope_ref": sr, "owner_ref": save(out / (name+"-owner.json"), owner)}
        docs[name]["worker_ref"] = save(out / (name+"-worker.json"), dict(owner, worker_id=ROOT_ACTOR))
    return {"schema": "researchos.w09-bridge-proposal.v1", "generation":BRIDGE_GENERATION,
            "historical_current4":historical, "documents": docs,
            "c19_policy": req["c19_policy"], "planned_routes": route_bindings,
            "context_seed_ref": req["context_seed_ref"], "source_ref": req["bridge_source_ref"],
            "source_review_ref": req["source_review_ref"], "current4": req["current4"],
            "dependency_snapshot": snapshot(api, reader, context), "execution_grant": False,
            "formal_acceptance": False}

def registration(req, out, eng):
    api, reader, profile = eng
    proposal = document(req["proposal_ref"])
    need(proposal["c19_policy"] == req["c19_policy"], "PROPOSAL_C19_POLICY")
    need(proposal["source_ref"] == req["bridge_source_ref"]
         and proposal["source_review_ref"] == req["source_review_ref"], "PROPOSAL_SOURCE_BINDING")
    proposal_archive_refs(proposal, req["proposal_ref"], req)
    need(proposal["current4"] == req["current4"], "ACTIVATION_PROPOSAL_CURRENT4")
    need(api.recheck_inputs(proposal["dependency_snapshot"])["status"] == "PASS", "PROPOSAL_DRIFT")
    docs = proposal["documents"]
    for value in docs.values():
        scope = document(value["scope_ref"])
        owner = document(value["owner_ref"])
        worker = document(value["worker_ref"])
        need(scope["issued_by"] == ROOT_ACTOR and owner["scope_ref"] == value["scope_ref"]
             and owner["selected_worker_id"] == worker["worker_id"] == ROOT_ACTOR
             and owner["lease_status"] == worker["lease_status"] == "ACTIVE"
             and stamp(owner["lease_expires_at"]) > datetime.now(timezone.utc), "PROPOSED_OWNER")
    def transform(cp, ow):
        cp, ow = copy.deepcopy(cp), copy.deepcopy(ow)
        work = cp.setdefault("work_in_progress", {})
        key = "w09_formal_bridge_registration_ref"
        need(key not in work, "ALREADY_REGISTERED")
        work[key] = req["proposal_ref"]
        binding = ow["card_path_bindings"]["W09-99"].setdefault("subtasks", {})
        for name, value in docs.items():
            owner = document(value["owner_ref"])
            slice_id = owner["slice_id"]
            need(slice_id not in binding and not any(r.get("slice_id") == slice_id for r in cp.get("workers", [])),
                 "DUPLICATE_OWNER")
            binding[slice_id] = dict(owner, owner_ref=value["owner_ref"], worker_ref=value["worker_ref"])
            cp.setdefault("workers", []).append(dict(owner, worker_id=ROOT_ACTOR, worker_ref=value["worker_ref"]))
        for doc in (cp, ow):
            previous = doc["revision"]
            doc["revision"] = previous + 1
            doc["expected_previous_revision"] = previous
        return cp, ow
    return transact(req, out, transform)

def transact(req, out, transform):
    # The held pair cannot be opened again from transform. Other canonical inputs stay guarded.
    guard = module(GUARD).SourceReadGuard()
    try:
        guard.acquire([dict(pin(r["path"]), sha256=r["sha256"], bytes=r["bytes"]) for r in req["current4"][2:]])
        current4(req["current4"])
        return module(TP).update_pair(req["current4"][:2], transform, out, "activate")
    finally:
        close = guard.close()
        save(out / "canonical-read-guard.closed.json", close)
        need(close["closed"] and close["retained_handles_count"] == 0 and not close["errors"], "GUARD_NOT_CLOSED")

def registered(req):
    cp, ow, *_ = current4(req["current4"])
    ref = cp["work_in_progress"]["w09_formal_bridge_registration_ref"]
    need(ref == req["proposal_ref"], "REGISTERED_PROPOSAL")
    proposal = document(ref)
    proposal_archive_refs(proposal, ref, req)
    need(proposal["c19_policy"] == req["c19_policy"], "REGISTERED_C19_POLICY")
    for name, refs in proposal["documents"].items():
        owner = document(refs["owner_ref"])
        key = owner["slice_id"]
        actual = ow["card_path_bindings"]["W09-99"]["subtasks"][key]
        need(actual["owner_ref"] == refs["owner_ref"] and actual["worker_ref"] == refs["worker_ref"]
             and actual["lease_status"] == "ACTIVE" and stamp(actual["lease_expires_at"]) > datetime.now(timezone.utc),
             "REGISTERED_FINITE_LEASE")
        need(any(r.get("slice_id") == key and r.get("worker_ref") == refs["worker_ref"] for r in cp["workers"]),
             "REGISTERED_WORKER")
    return proposal

def consume(req, out, eng):
    api, reader, profile = eng
    proposal = registered(req)
    context, pinned, *_ = native_inputs(req, eng)
    planned = consumer_plan(req, eng, context, pinned)
    need(proposal["planned_routes"] == [dict(zip(("command_key","check_id","case_id"), r)) for r in planned],
         "REGISTERED_EXACT_CONSUMER_ROUTES")
    snap = snapshot(api, reader, context)
    locked = decode((ROOT / "execution/toolchains/locked.json").read_bytes())
    python = locked["tools"]["python"]
    raw = Path(python["path"]).read_bytes()
    need(sha(raw) == python["sha256"], "LOCKED_PYTHON_CHANGED")
    helper = module(OWNED)
    rows = copy.deepcopy(context["registered_commands"])
    records = []
    for index, row in enumerate(rows):
        route = tuple(row[k] for k in ("command_key","check_id","case_id"))
        if route not in planned:
            checked(row["receipt_ref"])  # Exact fixed history already passed Main current Source21 gates.
            continue
        registered(req)
        need(api.recheck_inputs(snap)["status"] == "PASS", "PRECHILD_CAS")
        env = {"SystemRoot":"C:/Windows", "WINDIR":"C:/Windows", "ComSpec":"C:/Windows/System32/cmd.exe",
               "PATH":str(Path(python["path"]).parent)+";C:/Windows/System32", "PATHEXT":".COM;.EXE;.BAT;.CMD",
               "PYTHONUTF8":"1", "GIT_CONFIG_NOSYSTEM":"1","GIT_CONFIG_GLOBAL":"NUL",
               "GIT_TERMINAL_PROMPT":"0","GIT_OPTIONAL_LOCKS":"0"}
        environment_request(req)
        for key in ("TEMP","TMP"):
            env[key] = str(environment_directory(req["isolated_environment"][key]))
        for key in ("USERPROFILE","LOCALAPPDATA","APPDATA"):
            p = physical(req["isolated_environment"][key])
            need(p.is_dir(), "ISOLATED_ENV_DIRECTORY")
            env[key] = str(p)
        for key, stem in (("native_report_ref","NATIVE_REPORT"),("native_tool_run_ref","TOOL_RUN"),("mode_decision_ref","MODE_DECISION")):
            env["RESEARCHOS_W09_"+stem+"_REF"] = row[key]["path"]
            env["RESEARCHOS_W09_"+stem+"_SHA256"] = row[key]["sha256"]
        checked(req["consumer_launcher_ref"])
        argv = [python["path"],"-I","-S","-B","-X","utf8",str(HERE/"consumer_launch.source.py"),
                req["bridge_source_ref"]["sha256"],str(req["bridge_source_ref"]["bytes"]),*route]
        so, se = out / (str(index)+".stdout.raw"), out / (str(index)+".stderr.raw")
        record = {"argv":argv,"cwd":str(ROOT),"route":list(route),"actual_exit":None,"observation":None}
        records.append(record)
        try:
            with so.open("xb") as stdout, se.open("xb") as stderr:
                result = helper.run_owned(argv, str(ROOT), env, stdout, stderr, 120, creation_flags=0x08000000)
            # Preserve the observed process result before any fallible stream hashing.
            record["observation"] = result
            record["actual_exit"] = result.get("actual_exit")
            record["ended_at"] = utc()
            save(out / (str(index)+".process.json"), record)
            record["stdout_ref"], record["stderr_ref"] = pin(so,True), pin(se,True)
            cleanup = result.get("job_cleanup",{})
            need(type(record["actual_exit"]) is int and record["actual_exit"] == 0
                 and result.get("timed_out") is False and result.get("error") is None
                 and cleanup.get("job_idle_confirmed") is True and cleanup.get("active_processes_last_observed") == 0
                 and cleanup.get("handles_closed") is True and cleanup.get("primary_exit_confirmed") is True
                 and cleanup.get("assigned_before_resume") is True and cleanup.get("errors") == [],
                 "FIRST_CHILD_FAILURE_STOP")
            lines = so.read_bytes().splitlines()
            need(len(lines) == 1, "DISPATCH_SUMMARY")
            summary = decode(lines[0])
            receipt = physical(summary["receipt"])
            need(receipt.is_relative_to(ROOT/"execution/invocations") and receipt.name == "receipt.json", "RECEIPT_PATH")
            row["receipt_ref"] = pin(receipt, True, False)
            save(out / (str(index)+".complete.json"), record)
        except BaseException as exc:
            save(out / (str(index)+".failure.json"), dict(record, error=repr(exc)))
            raise
    need(api.recheck_inputs(snap)["status"] == "PASS", "POSTCHILD_CAS")
    return {"schema":"researchos.w09-bridge-consumers.v1","registered_commands":rows,"processes":records,
            "formal_acceptance":False,"producer_rerun":False,"c19_policy":req["c19_policy"],
            "executed_consumer_routes":[list(route) for route in planned]}

def roles(req, out, eng):
    api, reader, profile = eng
    proposal = registered(req)
    inputs = document(req["role_registry_input_ref"])
    registry = {"schema":"researchos.w09.execution-role-registry.v1","writer_actor":ROOT_ACTOR,
                "run_id":inputs["run_id"],"roles":inputs["roles"],"provenance":inputs["provenance"],
                "route_execution_refs":inputs["route_execution_refs"]}
    need(registry["roles"]["verifier"] == VERIFIER and AUTHOR_BACKEND in registry["roles"]["source_authors"]
         and AUTHOR not in registry["roles"]["source_authors"],
         "ACTUAL_VERIFIER_SOURCE_AUTHOR")
    # Validate every actual origin using Main before publishing a proposal.
    for proof in registry["provenance"]:
        profile._role_audit(api._profile_api(), reader, proof, document(proof["raw_ref"]))
    need(len(registry["route_execution_refs"]) == 6, "SIX_ROLE_ROUTES")
    return {"schema":"researchos.w09-role-publication-proposal.v1",
            "fixed_path":ROLE_PATH, "payload_ref":save(out/"execution-roles.proposed.json",registry),
            "proposal_ref":req["proposal_ref"],"dependency_snapshot":snapshot(api,reader),"formal_acceptance":False}

def publish_registration(req, out, eng):
    api, reader, profile = eng
    publication = document(req["publication_ref"])
    fixed = publication["fixed_path"]
    need(fixed in {ROLE_PATH, INDEX_PATH}, "FIXED_REGISTRY_ONLY")
    raw = checked(publication["payload_ref"])
    if fixed == INDEX_PATH:
        need((ROOT/publication["origin_fixed_path"]).read_bytes() == checked(publication["origin_payload_ref"])
             and (ROOT/publication["capture_fixed_path"]).read_bytes() == checked(publication["capture_payload_ref"]),
             "ROOT_ORIGINAL_AND_CAPTURE_PUBLICATION_REQUIRED")
    # Root publishes these reviewed exact bytes separately. No silent overwrite.
    need((ROOT/fixed).read_bytes() == raw, "ROOT_PUBLICATION_REQUIRED")
    ref = pin(ROOT/fixed, True)
    slot = "w09_execution_role_registry_ref" if fixed == ROLE_PATH else "w09_root_delivery_capture_index_ref"
    def transform(cp, ow):
        cp = copy.deepcopy(cp)
        work = cp.setdefault("work_in_progress",{})
        old = work.get(slot)
        need(old == req.get("expected_previous_registry_ref"), "REGISTRY_SLOT_CAS")
        work[slot] = ref
        cp["expected_previous_revision"] = cp["revision"]
        cp["revision"] += 1
        return cp, ow
    validate_persistent_snapshot(publication["dependency_snapshot"])
    need(api.recheck_inputs(publication["dependency_snapshot"])["status"] == "PASS", "PUBLICATION_CAS")
    return transact(req,out,transform)

def assemble(req, out, eng):
    api, reader, profile = eng
    registered(req)
    context, pinned, closure, router, sources = native_inputs(req, eng)
    context = copy.deepcopy(context)
    context["registered_commands"] = document(req["consumer_result_ref"])["registered_commands"]
    context["created_at"] = utc()
    policy = profile._role_registry(api._profile_api(),reader,context)
    need(policy["roles"]["verifier"] == VERIFIER, "ACTUAL_BACKEND_VERIFIER")
    plan = document(req["plan_ref"])
    outputs, facts = profile._dispatches(api._profile_api(),reader,context,pinned,closure,router,plan,sources,policy)
    catalog = {c["id"]:c for c in document(context["acceptance_baseline_ref"])["cases"]}
    context["global_evidence_refs"] = {}
    for case in ("C19","A06"):
        selected = [v for k,v in outputs.items() if k[2] == case]
        base = {"case_id":case,"run_id":context["run_id"]}
        run = dict(base,schema="researchos.w09.run-receipt.v1",environment_mode="FIXTURE",
                   **context["version_vector"]["environment"],
                   started_at=min((v["native_started_at"] for v in selected),key=stamp),
                   ended_at=max((v["ended_at"] for v in selected),key=stamp),
                   executor_id=context["executor_id"],verifier_id=policy["roles"]["verifier"])
        vector = context["version_vector"]
        manifest = dict(base,schema="researchos.w09.version-manifest.v1",package_version="2.4.0",
                        code_revision=req["code_revision"],dirty=req["dirty"],version_vector=vector,
                        components=vector["components"],lock_files=vector["lock_files"],input_files=vector["input_files"],
                        package_manifest_ref=req["package_manifest_ref"])
        command = dict(base,schema="researchos.w09.command-receipt.v1",
                       command_keys=catalog[case]["command_keys"],registered_commands=selected)
        assertions = []
        for frozen in catalog[case]["assertions"]:
            records = [next(r for r in fr if r["assertion_id"] == frozen["id"]) for route,fr in facts.items() if route[2] == case]
            need(len(records)==2 and records[0]["evidence"]==records[1]["evidence"],"GLOBAL_ROUTE_ACTUAL_AGREEMENT")
            refs = [dict(pin(r["owned_export_ref"]["path"],True,False),locator={"json_pointer":"/actual"}) for r in records]
            assertions.append({"id":frozen["id"],"expected":frozen["expected"],"actual":records[0]["evidence"],
                               "status":"PASS","raw_evidence_refs":refs,
                               "refusal_evidence_refs":req["refusal_evidence_refs"] if frozen["id"]=="A06-02" else []})
        docs = (run,manifest,command,dict(base,schema="researchos.w09.assertion-results.v1",assertions=assertions))
        context["global_evidence_refs"][case] = {key:{k:v for k,v in save(out/(case+"-"+key+".json"),doc).items() if k!="bytes"}
          for key,doc in zip(("run_receipt","version_manifest","command_receipt","assertion_results"),docs)}
    # This reviewer identity input is used only to validate GLOBAL shape, never an emitted review.
    profile._global(api._profile_api(),reader,context,outputs,facts,{"reviewer_id":policy["roles"]["verifier"]})
    snap = snapshot(api,reader,context)
    ref = ref2(save(out/"context.json",context))
    return {"schema":"researchos.w09-assembled-context.v1","context_ref":ref,"dependency_snapshot":snap,
            "review_required_from":VERIFIER,"formal_acceptance":False}

def capture(req, out, eng):
    api, reader, profile = eng
    context, review = document(req["context_ref"]),document(req["review_ref"])
    need(set(req["context_ref"])==set(req["review_ref"])=={"path","sha256"},"FORMAL_REF_TWO_KEYS")
    need(review["reviewer_id"] == review["issuer_id"] == VERIFIER and review["context_ref"] ==
         ref2(req["context_ref"]), "REAL_FORMAL_REVIEW")
    need(review["decision"] == "ACCEPTED" and review["missing"] == review["failed"] == [], "ACTUAL_REVIEW_REQUIRED")
    offsets = req["original_offsets"]
    need(type(offsets) is list and len(offsets)==3 and offsets==sorted(set(offsets))
         and all(type(n)is int and n>=0 for n in offsets), "THREE_ORIGINAL_OFFSETS")
    audit = Path(profile.ROOT_SOURCE_AUDIT_LOG)
    prefix = audit.stat().st_size
    with audit.open("rb") as stream:
        lines=[]
        for offset in offsets:
            stream.seek(offset); line=stream.readline()
            need(line.endswith(b"\n") and offset+len(line)<=prefix,"ORIGINAL_LINE_BOUNDARY")
            lines.append(line)
    header,meta,message = [decode(line) for line in lines]
    payload = message["payload"]
    need(header["type"]=="session_meta" and header["payload"]["id"]==THREAD
         and meta["type"]=="inter_agent_communication_metadata" and message["ordinal"]==meta["ordinal"]+1
         and meta["timestamp"]==message["timestamp"] and payload["type"]=="agent_message"
         and payload["author"]==VERIFIER and payload["recipient"]=="/root"
         and message["metadata"]["client_authored"] is False, "REAL_BACKEND_FINAL")
    content = payload["content"]
    need(type(content)is list and len(content)==1 and set(content[0])=={"type","text"}
         and content[0]["type"]=="input_text","PLAINTEXT_FINAL")
    text = content[0]["text"]
    need(req["review_ref"]["sha256"] in text and req["context_ref"]["sha256"] in text,"FINAL_FULL_DIGESTS")
    need(stamp(context["created_at"])<=stamp(review["issued_at"])<=stamp(message["timestamp"])<=datetime.now(timezone.utc),
         "REAL_DELIVERY_TIMES")
    event = payload["id"]
    need(re.fullmatch(r"[A-Za-z0-9_-]+",event) is not None,"EVENT_FILENAME")
    # Original bytes proposal must be published at this fixed prefix by Root.
    origin_path = ORIGIN+event+".jsonl"
    origin_payload = save(out/"original.proposed.jsonl",b"".join(lines),raw=True)
    origin_ref = dict(origin_payload,path=origin_path)
    capture_path = "execution/v2.4/root_delivery_captures/W09/W09-99/"+event+".json"
    observed=utc()
    c={"schema":"researchos.root-actual-audit-formal-delivery.v1","issued_by":ROOT_ACTOR,
       "protocol_observation_only":False,"W09_parent_or_formal_delivery":True,"Root_thread_id":THREAD,
       "message_id":event,"sender":payload["author"],"recipient":payload["recipient"],"received_at":message["timestamp"],
       "original_capture_ref":origin_ref,"review_ref":req["review_ref"],"context_ref":req["context_ref"],
       "content_sha256":sha(text.encode("utf-8")),"root_observed_at":observed,"source_line_offsets":offsets,
       "original_line_sha256":[sha(line) for line in lines],"source_audit_path":str(audit),
       "source_prefix_size_observed":prefix}
    cap_payload=save(out/"capture.proposed.json",c); cap_ref=dict(cap_payload,path=capture_path)
    previous = req.get("previous_index_ref")
    index = document(previous) if previous else {"schema":"researchos.root-delivery-capture-index.v2",
       "writer_actor":ROOT_ACTOR,"Root_thread_id":THREAD,"entries":[]}
    need(event not in {v["event_id"] for v in index["entries"]},"DUPLICATE_CAPTURE_EVENT")
    index["entries"].append({"event_id":event,"capture_ref":cap_ref,"origin_ref":origin_ref})
    issuance={"schema":"researchos.w09.root-observed-issuance.v1","task_id":"W09","step_id":"W09-99",
      "run_id":context["run_id"],"context_ref":req["context_ref"],"review_ref":req["review_ref"],"actor":ROOT_ACTOR,
      "observer_id":ROOT_ACTOR,"issuer_id":VERIFIER,"executor_id":context["executor_id"],"reviewer_id":VERIFIER,
      "event_id":event,"delivery_ref":cap_ref,"origin_event_ref":origin_ref,"observed_at":utc()}
    return {"schema":"researchos.w09-capture-publication-proposal.v1","fixed_path":INDEX_PATH,
      "payload_ref":save(out/"index.proposed.json",index),"origin_payload_ref":origin_payload,
      "origin_fixed_path":origin_path,"capture_payload_ref":cap_payload,"capture_fixed_path":capture_path,
      "issuance_ref":save(out/"issuance.json",issuance),"dependency_snapshot":snapshot(api,reader),
      "formal_acceptance":False}

def check(req, out, eng):
    api, reader, profile = eng
    owner = document(req["prospective_owner_ref"])
    roots = {key:physical(req[key+"_ref"]["path"]) for key in ("context","review","issuance")}
    for key in roots:
        checked(req[key+"_ref"])
    need(api._registered_roots(reader,owner,"W09")==roots,"PROSPECTIVE_OWNER_EXACT_ROOTS")
    # A separately approved prospective owner is only checked; never emitted or registered here.
    context=profile.verify_owner(api._profile_api(),reader,owner,roots,physical(req["plan_ref"]["path"]))
    return {"schema":"researchos.w09-main-owner-precheck.v1","status":"PASS",
            "owner_ref":req["prospective_owner_ref"],"dependency_snapshot":snapshot(api,reader,context),
            "canonical_acceptance_written":False}

def derive(req, out, eng):
    api, reader, profile = eng
    result=api.derive_formal_cases(ROOT,CANON[2],physical(req["plan_ref"]["path"]))
    result["bridge_CAS"]=api.recheck_inputs(result["dependency_snapshot"])
    need(result["bridge_CAS"]["status"]=="PASS","DERIVE_CAS")
    return result

STAGES={"seed":seed,"propose":propose,"activate":registration,"consume":consume,"roles":roles,
        "publish-registration":publish_registration,"assemble":assemble,"capture":capture,"check":check,"derive":derive}

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("stage",choices=STAGES)
    parser.add_argument("--request",required=True)
    parser.add_argument("--sha256",required=True)
    parser.add_argument("--bytes",required=True,type=int)
    args=parser.parse_args(argv)
    require_process_temp()
    req,out,eng=root_request({"path":args.request,"sha256":args.sha256,"bytes":args.bytes},args.stage)
    guard=module(GUARD).SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
    try:
        refs={}
        for ref in request_dependency_refs(req):
            path=physical(ref["path"])
            if args.stage in {"activate","publish-registration"} and path in CANON[:2]:
                continue
            raw=checked(ref)
            wanted={"path":str(path),"sha256":ref["sha256"],"bytes":len(raw)}
            need(str(path) not in refs or refs[str(path)]==wanted,"CONFLICTING_REQUEST_PINS")
            refs[str(path)] = wanted
        resource = environment_request(req)
        eng[1].w09_audit_ranges.extend(resource["audit_ranges"])
        # This single exact C marker is resource metadata, never a general checked/ref path.
        refs[RESOURCE_OWNER_REF["path"]] = dict(RESOURCE_OWNER_REF)
        for resource_ref in resource["refs"]:
            if resource_ref == RESOURCE_OWNER_REF:
                continue
            raw = checked(resource_ref)
            refs[str(physical(resource_ref["path"]))] = {"path":str(physical(resource_ref["path"])),
                "sha256":resource_ref["sha256"],"bytes":len(raw)}
        authority_snapshot = snapshot(eng[0],eng[1],authority=True)
        authority_snapshot["files"].update({str(path):ref["sha256"] for path,ref in zip(CANON,req["current4"])})
        for name in ("proposal_ref","publication_ref","role_registry_input_ref"):
            if name in req:
                for ref in historical_dependency_refs(document(req[name]),req[name],req,name):
                    path=physical(ref["path"])
                    if args.stage in {"activate","publish-registration"} and path in CANON[:2]:
                        continue
                    raw=checked(ref)
                    wanted={"path":str(path),"sha256":ref["sha256"],"bytes":len(raw)}
                    need(str(path) not in refs or refs[str(path)]==wanted,"CONFLICTING_DEPENDENCY_PINS")
                    refs[str(path)]=wanted
        if args.stage in {"propose","consume","assemble"}:
            native_inputs(req,eng)
        if args.stage == "consume":
            helper=module(OWNED)
            paths=set(helper.runtime_resource_paths())
            paths.update(str(Path(m.__file__).resolve()) for m in tuple(sys.modules.values())
                         if getattr(m,"__file__",None) and Path(m.__file__).is_file())
            for path in paths:
                raw=Path(path).read_bytes()
                refs[str(Path(path))]={"path":str(Path(path)),"sha256":sha(raw),"bytes":len(raw)}
        for path,digest in eng[1].read_hashes.items():
            if args.stage in {"activate","publish-registration"} and canonical_identity(path) in CANON[:2]:
                need(digest == req["current4"][CANON.index(canonical_identity(path))]["sha256"], "TP_AUTHORITY_DIGEST_CONFLICT")
                continue
            raw=Path(path).read_bytes()
            need(sha(raw)==digest,"PREHOLD_DEPENDENCY_DRIFT")
            refs[str(path)]={"path":str(path),"sha256":digest,"bytes":len(raw)}
        guard.acquire(list(refs.values()))
        need(eng[0].recheck_inputs(authority_snapshot)["status"]=="PASS","ROOT_AUTHORITY_CAS")
        environment_request(req)
        result=STAGES[args.stage](req,out,eng)
        save(out/"result.json",result)
        print(json.dumps({"result_ref":pin(out/"result.json"),"stage":args.stage},ensure_ascii=False))
        return 0 if args.stage!="derive" or result["integrity"]=="PASS" else 1
    except BaseException as exc:
        save(out/"failure.json",{"stage":args.stage,"error":repr(exc),"formal_acceptance":False})
        raise
    finally:
        closed=guard.close()
        save(out/"source-guard.closed.json",closed)
        need(closed["closed"] and closed["retained_handles_count"]==0 and not closed["errors"],"SOURCE_GUARD_CLOSED")

if __name__=="__main__":
    sys.exit(main())

