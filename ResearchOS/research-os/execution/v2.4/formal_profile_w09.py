"""Read-only W09 formal owner profile; source candidate until Root adopts it.

Contract: context/review/issuance are three distinct registered W09 JSON roots.
Each context route has a dispatcher receipt, a native report, a Root tool-run
receipt and a later independent mode decision. All are SHA-pinned. The six
routes, two owned cases and their GLOBAL files are mandatory. This source is
loaded only from execution/v2.4/formal_profile_w09.py after adoption; no
receipt-provided Python is executed.
"""
from __future__ import annotations

import hashlib
import ast
import json
from pathlib import Path
import re

PREFIX = "execution/v2.4/receipts/W09/W09-99/"
SOURCE_PREFIX = "execution/v2.4/receipts/W09/"
NATIVE_PREFIX = "execution/receipts/W09/"
ROOT_CAPTURE_PREFIX = "execution/v2.4/root_delivery_captures/W09/W09-99/"
ROOT_CAPTURE_INDEX = ROOT_CAPTURE_PREFIX + "index.json"
ROOT_ORIGIN_PREFIX = "execution/v2.4/root_original_events/W09/W09-99/"
ROOT_THREAD_ID = "01a11007-5233-7ca1-b71f-9e9e5ce84c98"
ROOT_SOURCE_AUDIT_LOG = "C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl"
SCHEMAS = {"context": "researchos.w09.current-context.v1",
           "review": "researchos.w09.independent-review.v1",
           "issuance": "researchos.w09.root-observed-issuance.v1"}
ROUTES = (("test.retrieval", "W09-G01", ""),
          ("test.retrieval", "W09-G02", ""),
          ("test.research.fixture", "", "C19"),
          ("test.retrieval", "", "C19"),
          ("test.retrieval", "", "A06"),
          ("test.security", "", "A06"))
IDS = {"W09-G01": ("W09-G01",), "W09-G02": ("W09-G02",),
       "C19": ("C19-01", "C19-02", "C19-03"),
       "A06": ("A06-01", "A06-02", "A06-03")}
MINIMUM_SOURCE = {"execution/v2.4/formal_case_index.py",
                  "execution/v2.4/formal_profile_w09.py",
                  "execution/command_dispatcher/dispatch.py",
                  "ops/ci/w09_formal_router.py", "ops/ci/w09_evidence_closure.py",
                  "ops/ci/retrieval.py", "internal/domain/retrieval_test.go",
                  "internal/domain/domain_test.go", "internal/domain/w09_evidence_export_test.go"}


def _ref(api, reader, value, prefix=PREFIX):
    api.fields(value, ("path", "sha256"), label="W09 pinned reference")
    return reader.ref(value, prefix)


def _doc(api, reader, value, prefix=PREFIX):
    return reader.read(_ref(api, reader, value, prefix))


def _raw(api, reader, value):
    """W09 locator check; Reader.raw remains the immutable W04 reader."""
    api.fields(value, ("path", "sha256", "locator"), label="W09 raw reference")
    scope = NATIVE_PREFIX if value["path"].startswith(NATIVE_PREFIX) else SOURCE_PREFIX
    path = reader.ref(value, scope, locator=True)
    raw = path.read_bytes()
    locator = api.obj(value["locator"], "W09 raw locator")
    if set(locator) == {"json_pointer"}:
        pointer = locator["json_pointer"]
        api.require(type(pointer) is str and (pointer == "" or pointer.startswith("/")), "RAW_LOCATOR", str(pointer))
        found = api.strict_json(raw)
        for token in pointer[1:].split("/") if pointer else ():
            api.require(re.search(r"~(?![01])", token) is None, "RAW_LOCATOR", pointer)
            token = token.replace("~1", "/").replace("~0", "~")
            if type(found) is dict:
                api.require(token in found, "RAW_LOCATOR_MISSING", pointer)
                found = found[token]
            else:
                api.require(type(found) is list and re.fullmatch(r"0|[1-9][0-9]*", token)
                            and int(token) < len(found), "RAW_LOCATOR_MISSING", pointer)
                found = found[int(token)]
    elif set(locator) == {"line_start", "line_end"}:
        start, end = locator["line_start"], locator["line_end"]
        lines = raw.decode("utf-8").splitlines()
        api.require(type(start) is int and type(end) is int and 1 <= start <= end <= len(lines),
                    "RAW_LOCATOR", value["path"])
        found = "\n".join(lines[start - 1:end])
    else:
        raise api.InvalidEvidence("RAW_LOCATOR", value["path"])
    api.require(api.meaningful(found), "RAW_EMPTY", value["path"])
    return found


def _same(api, left, right):
    for value in (left, right):
        api.fields(value, ("path", "sha256"), label="reference identity")
    return left == right


# W09 v5: exact CM39 reuse and Root-registered execution role provenance.
CM39_ARCHIVE = {
    "path": "execution/v2.4/receipts/W09/W09-99/checkpoint_r369_native_source_root/cp369-c19-20261009/historical.cp369.commands.json",
    "sha256": "28b4ba18ce2ab3ce03287651e311ae2bd36293b53fd8c298e5bf1f231f56d027",
    "bytes": 68968,
}
LEGACY_C19_RECEIPTS = {
    "test.research.fixture": {
        "path": "execution/invocations/83d5069c-d717-416b-9a60-e228aa5e7024/receipt.json",
        "sha256": "bf2ac8d0ef42db4662d1bfa553a749ed9fc50b0e79421825692a2c98f7281e02",
        "bytes": 2367,
    },
    "test.retrieval": {
        "path": "execution/invocations/51bd0940-8cb7-4705-9bf6-60ffcb916077/receipt.json",
        "sha256": "f1a1f6b15629bcfdf0a7234ba0716fd9a81487cb51975b0015ccb2d509284e3a",
        "bytes": 2331,
    },
}
ROLE_REGISTRY_PATH = ROOT_CAPTURE_PREFIX + "execution-roles.json"
ROLE_POLICY_SCHEMA = "researchos.w09.execution-role-policy.v1"


def _witness(api, reader, ref, prefix=SOURCE_PREFIX):
    api.fields(ref, ("path", "sha256", "bytes"), label="W09 public provenance pin")
    api.require(type(ref["bytes"]) is int and ref["bytes"] > 0,
                "PROVENANCE_BYTES", ref["path"])
    path = reader.ref({"path": ref["path"], "sha256": ref["sha256"]}, prefix)
    api.require(path.stat().st_size == ref["bytes"], "PROVENANCE_BYTES", ref["path"])
    return path, reader.read(path)


def _native_tool_doc(api, reader, ref):
    api.fields(ref, ("path", "sha256"), label="W09 native tool reference")
    relative = api.text(ref["path"], "native tool path")
    api.require(relative.startswith((NATIVE_PREFIX, SOURCE_PREFIX)),
                "PATH_SCOPE", relative)
    return _doc(api, reader, ref, NATIVE_PREFIX if relative.startswith(NATIVE_PREFIX) else SOURCE_PREFIX)


def _cm40_commands(cm39):
    """The only authorized four-route delta; all unrelated entries are copied."""
    commands = json.loads(json.dumps(cm39["commands"], ensure_ascii=False))
    retrieval = commands["test.retrieval"]
    for ident in ("W09-G01", "W09-G02"):
        if ident not in retrieval["selectors"]["check_id"]:
            retrieval["selectors"]["check_id"].append(ident)
    if "A06" not in retrieval["selectors"]["case_id"]:
        retrieval["selectors"]["case_id"].append("A06")
    security = commands["test.security"]
    security["executable_tool"] = "python"
    security["argv"] = ["-B", "-X", "utf8", "ops/ci/w09_formal_router.py", "test.security"]
    for name in cm39["commands"]["test.retrieval"]["allowed_env"]:
        if name not in security["allowed_env"]:
            security["allowed_env"].append(name)
    security["tool_env"]["RESEARCHOS_GO"] = "go"
    security["selectors"]["task_id"].append("W09")
    security["selectors"]["case_id"] = ["A06"]
    return commands


def _historical_registry(api, reader, row, receipt, registry, current_hash):
    """No author-supplied old registry or newly minted old receipt is admitted."""
    if receipt.get("registered_command_revision") == current_hash:
        return False
    key = row["command_key"]
    allowed = LEGACY_C19_RECEIPTS.get(key)
    api.require(row["check_id"] == "" and row["case_id"] == "C19"
                and allowed is not None
                and row["receipt_ref"] == {k: allowed[k] for k in ("path", "sha256")}
                and receipt.get("registered_command_revision") == CM39_ARCHIVE["sha256"],
                "LEGACY_RECEIPT_NOT_ALLOWED", key)
    path = reader.ref(row["receipt_ref"], "execution/invocations/")
    api.require(path.stat().st_size == allowed["bytes"], "LEGACY_RECEIPT_NOT_ALLOWED", key)
    _, archive = _witness(api, reader, CM39_ARCHIVE)
    metadata = {"revision", "revision_note", "updated_at", "updated_by"}
    api.require(archive.get("revision") == 39 and registry.get("revision") == 40
                and set(registry) == set(archive)
                and all(registry[name] == value for name, value in archive.items()
                        if name not in metadata | {"commands"})
                and registry.get("updated_by") == "codex:/root"
                and set(registry["commands"]) == set(archive["commands"])
                and registry["commands"] == _cm40_commands(archive),
                "REGISTRY_SEMANTICS_CHANGED", key)
    before, after = archive["commands"][key], registry["commands"][key]
    api.require({k: v for k, v in before.items() if k != "selectors"}
                == {k: v for k, v in after.items() if k != "selectors"}
                and set(before["selectors"]) == set(after["selectors"])
                and all(set(values) <= set(after["selectors"][name])
                        for name, values in before["selectors"].items()),
                "REGISTRY_SEMANTICS_CHANGED", key)
    return True


def _dispatcher_input(api, reader, ref, pinned, historical, ident):
    api.fields(ref, ("path", "sha256"), label="dispatcher input pin")
    if historical and ref["path"] == "execution/v2.4/commands.json":
        api.require(ref["sha256"] == CM39_ARCHIVE["sha256"],
                    "DISPATCH_INPUT_UNPINNED", ident)
        _witness(api, reader, CM39_ARCHIVE)
        return
    api.require(pinned.get(reader.ref(ref)) == ref["sha256"],
                "DISPATCH_INPUT_UNPINNED", ident)


# This executable trust pin is part of the reviewed profile, never Canon input.
CORRECTION_MODULE_SHA256 = "d8ae05d8ecc1e6544b82a2b3744ebf369b330e977b47430c626a88b17f20bac6"
CORRECTION_MODULE_BYTES = 16374


def _header_correction(api, reader, roots):
    """Optional, independently reviewed one-incident interpreter authority."""
    checkpoint = reader.read(reader.path("execution/v2.4/checkpoint.json"))
    authority = checkpoint.get("work_in_progress", {}).get("w09_header_metadata_correction")
    if authority is None:
        return None
    api.fields(authority, ("schema", "certificate_ref", "verifier_module_ref", "review_ref", "delivery_ref"),
               label="Root header correction authority")
    ref = authority["verifier_module_ref"]
    api.fields(ref, ("path", "sha256", "bytes"), label="fixed correction module")
    api.require(ref["path"] == "execution/v2.4/w09_header_correction.py",
                "CORRECTION_MODULE", "fixed repository verifier source only")
    api.require(ref["sha256"] == CORRECTION_MODULE_SHA256
                and type(ref["bytes"]) is int and ref["bytes"] == CORRECTION_MODULE_BYTES,
                "CORRECTION_MODULE_PIN", "profile-owned executable trust pin")
    path = reader.ref({key: ref[key] for key in ("path", "sha256")})
    api.require(path == reader.repo / ref["path"] and not path.is_symlink()
                and path.stat().st_size == CORRECTION_MODULE_BYTES,
                "CORRECTION_MODULE", "reviewed fixed module bytes")
    raw = path.read_bytes()
    api.require(len(raw) == CORRECTION_MODULE_BYTES
                and hashlib.sha256(raw).hexdigest() == CORRECTION_MODULE_SHA256,
                "CORRECTION_MODULE_PIN", "verify exact executable bytes before compile or exec")
    namespace = {"__name__": "researchos_trusted_w09_header_correction", "__file__": str(path)}
    exec(compile(raw, str(path), "exec"), namespace)
    api.require(api.sha256(path) == ref["sha256"], "INPUT_CHANGED_DURING_READ", str(path))
    cert = namespace["authorize"](api, reader, authority, roots)
    return {"certificate": cert, "audit_line": namespace["audit_line"]}


def _audit_line(api, reader, offset, digest, line, observed, code, detail):
    correction = getattr(reader, "w09_header_correction", None)
    if correction is not None:
        return correction["audit_line"](api, correction["certificate"], offset, digest, line, observed)
    api.require(observed == line and hashlib.sha256(observed).hexdigest() == digest, code, detail)
    return {"path": ROOT_SOURCE_AUDIT_LOG, "offset": offset, "bytes": len(line), "sha256": digest}


def _role_audit(api, reader, proof, origin):
    """A provenance string is insufficient: match finite original Root audit bytes."""
    _, audit = _witness(api, reader, proof["actual_audit_ref"])
    api.fields(audit, ("schema", "actor_id", "role", "Root_thread_id", "source_audit_path",
                       "source_line_offsets", "original_line_sha256", "source_prefix_size_observed",
                       "original_capture_ref", "binding_sha256"), label="actual role audit")
    api.require(audit["schema"] == "researchos.w09.actual-role-audit.v1"
                and audit["actor_id"] == proof["actor_id"] and audit["role"] == proof["role"]
                and audit["Root_thread_id"] == ROOT_THREAD_ID
                and audit["source_audit_path"] == ROOT_SOURCE_AUDIT_LOG,
                "ROLE_ACTUAL_AUDIT", "actual actor/session binding")
    ref = audit["original_capture_ref"]
    api.fields(ref, ("path", "sha256", "bytes"), label="actual role original capture")
    path = reader.ref({name: ref[name] for name in ("path", "sha256")}, ROOT_ORIGIN_PREFIX)
    raw = _pin_observed(api, reader, path, ref["sha256"])
    lines = raw.splitlines(keepends=True)
    api.require(type(ref["bytes"]) is int and ref["bytes"] == len(raw)
                and len(lines) == 3 and all(line.endswith(b"\n") for line in lines),
                "ROLE_ACTUAL_AUDIT", "three original records")
    header, call, result = [api.strict_json(line) for line in lines]
    api.require(all(type(item) is dict for item in (header, call, result))
                and type(call.get("payload")) is dict and type(result.get("payload")) is dict
                and type(call.get("ordinal")) is int and call["ordinal"] > 0
                and type(result.get("ordinal")) is int and result["ordinal"] > call["ordinal"],
                "ROLE_ACTUAL_AUDIT", "original record shape and order")
    api.require(header.get("type") == "session_meta" and header.get("ordinal") == 0
                and header.get("payload", {}).get("id") == ROOT_THREAD_ID,
                "ROLE_ACTUAL_AUDIT", "Root original session")
    payload = result.get("payload", {})
    if proof["actor_id"] == "codex:/root":
        first = call.get("payload", {})
        api.require(call.get("type") == result.get("type") == "response_item"
                    and first.get("type") in {"function_call", "custom_tool_call"}
                    and payload.get("type") in {"function_call_output", "custom_tool_call_output"}
                    and type(first.get("call_id")) is str and bool(first["call_id"])
                    and first["call_id"] == payload.get("call_id")
                    and type(first.get("name")) is str and bool(first["name"]),
                    "ROLE_ACTUAL_AUDIT", "actual Root tool call and matching result")
    else:
        api.require(call.get("type") == "inter_agent_communication_metadata"
                    and result.get("type") == "response_item"
                    and type(call.get("ordinal")) is int
                    and result.get("ordinal") == call["ordinal"] + 1
                    and call.get("timestamp") == result.get("timestamp")
                    and payload.get("type") == "agent_message"
                    and payload.get("author") == proof["actor_id"]
                    and payload.get("recipient") == "/root"
                    and result.get("metadata", {}).get("client_authored") is False
                    and type(payload.get("content")) is list
                    and len(payload["content"]) == 1
                    and type(payload["content"][0]) is dict
                    and payload["content"][0].get("type") == "input_text"
                    and type(payload["content"][0].get("text")) is str,
                    "ROLE_ACTUAL_AUDIT", "actual peer delivery; no relabeled Source author")
    bindings = {proof["raw_ref"]["sha256"]}
    for name in ("source_hdf_ref", "source_mf_ref", "source_review_ref", "scope_ref", "independent_review_ref"):
        if type(origin.get(name)) is dict:
            bindings.add(origin[name].get("sha256"))
    bindings.add(origin.get("report_sha256"))
    api.require(type(audit["binding_sha256"]) is str
                and api.SHA.fullmatch(audit["binding_sha256"])
                and audit["binding_sha256"] in bindings
                and audit["binding_sha256"] in lines[1].decode("utf-8") + lines[2].decode("utf-8"),
                "ROLE_ACTUAL_AUDIT", "origin artifact in the original call/delivery")
    offsets, digests = audit["source_line_offsets"], audit["original_line_sha256"]
    api.require(type(offsets) is list and len(offsets) == 3
                and all(type(value) is int and value >= 0 for value in offsets)
                and offsets == sorted(set(offsets))
                and type(digests) is list and len(digests) == 3
                and all(type(value) is str and api.SHA.fullmatch(value) for value in digests)
                and type(audit["source_prefix_size_observed"]) is int,
                "ROLE_ACTUAL_AUDIT", "original offset/hash format")
    with Path(ROOT_SOURCE_AUDIT_LOG).open("rb") as stream:
        for offset, digest, line in zip(offsets, digests, lines):
            api.require(offset + len(line) <= audit["source_prefix_size_observed"],
                        "ROLE_ACTUAL_AUDIT", "original prefix boundary")
            stream.seek(offset)
            observed = stream.readline()
            reader.w09_audit_ranges.append(_audit_line(api, reader, offset, digest, line, observed,
                                                      "ROLE_ACTUAL_AUDIT", "original source bytes"))


def _role_registry(api, reader, context):
    policy = api.fields(context.get("role_policy"),
                        ("schema", "registry_ref"), label="W09 role policy")
    api.require(policy["schema"] == ROLE_POLICY_SCHEMA, "ROLE_POLICY", "W09")
    checkpoint = reader.read(reader.path("execution/v2.4/checkpoint.json"))
    authority = checkpoint.get("work_in_progress", {}).get("w09_execution_role_registry_ref")
    api.require(type(authority) is dict and set(authority) == {"path", "sha256", "bytes"}
                and authority == policy["registry_ref"]
                and authority["path"] == ROLE_REGISTRY_PATH,
                "ROLE_AUTHORITY_OPEN", "current Root role registry")
    _, registry = _witness(api, reader, authority, ROOT_CAPTURE_PREFIX)
    api.fields(registry, ("schema", "writer_actor", "run_id", "roles", "provenance",
                          "route_execution_refs"), label="Root W09 role registry")
    api.require(registry["schema"] == "researchos.w09.execution-role-registry.v1"
                and registry["writer_actor"] == "codex:/root"
                and registry["run_id"] == context["run_id"],
                "ROLE_AUTHORITY_OPEN", "registered role context")
    roles = api.fields(registry["roles"],
                       ("source_authors", "executor", "assembler", "verifier", "root_observer"),
                       label="execution roles")
    authors = api.sequence(roles["source_authors"], "source authors")
    for actor in authors:
        api.text(actor, "source author")
    api.require(len({actor.casefold() for actor in authors}) == len(authors),
                "ROLE_PROVENANCE", "duplicate author")
    for name in ("executor", "assembler", "verifier", "root_observer"):
        api.text(roles[name], name)
    api.require(roles["executor"] == context["executor_id"]
                and roles["root_observer"] == "codex:/root"
                and roles["verifier"].casefold() not in
                {actor.casefold() for actor in
                 [*authors, roles["executor"], roles["assembler"], roles["root_observer"]]},
                "INDEPENDENT_ACTOR", "Verifier is a non-author, non-executor issuer")
    expected = {("SOURCE_AUTHOR", actor) for actor in authors} | {
        ("EXECUTOR", roles["executor"]), ("EVIDENCE_ASSEMBLER", roles["assembler"]),
        ("VERIFIER", roles["verifier"]), ("ROOT_OBSERVER", roles["root_observer"])}
    provenance = api.sequence(registry["provenance"], "role provenance")
    seen = set()
    for proof in provenance:
        api.fields(proof, ("role", "actor_id", "origin_kind", "raw_ref", "actual_audit_ref"), label="role provenance")
        pair = proof["role"], proof["actor_id"]
        api.require(pair in expected and pair not in seen,
                    "ROLE_PROVENANCE", "unknown or duplicate actor/role")
        allowed_origins = {
            "SOURCE_AUTHOR": ("ROOT_SCOPE_REGISTRATION", "/source_actor"),
            "EXECUTOR": ("ACTUAL_MODE_DECISION", "/producer_id"),
            "EVIDENCE_ASSEMBLER": ("ROOT_OWNER_REGISTRATION", "/selected_worker_id"),
            "VERIFIER": ("ACTUAL_MODE_DECISION", "/reviewer_id"),
            "ROOT_OBSERVER": ("ROOT_SCOPE_REGISTRATION", "/issued_by"),
        }
        kind, pointer = allowed_origins[proof["role"]]
        api.require(proof["origin_kind"] == kind
                    and proof["raw_ref"].get("locator") == {"json_pointer": pointer},
                    "ROLE_PROVENANCE", "typed actual origin")
        origin_ref = {name: proof["raw_ref"][name] for name in ("path", "sha256")}
        origin = _doc(api, reader, origin_ref, SOURCE_PREFIX)
        if kind == "ROOT_SCOPE_REGISTRATION":
            api.require(origin.get("issued_by") == "codex:/root"
                        and type(origin.get("schema")) is str
                        and re.fullmatch(r"researchos\.w09[-.][a-z0-9.-]*scope\.v1", origin["schema"])
                        is not None, "ROLE_PROVENANCE", "Root scope origin")
        elif kind == "ACTUAL_MODE_DECISION":
            api.require(origin.get("schema") == "researchos.w09-mode-decision.v2"
                        and origin.get("decision") == "QUALIFIED"
                        and origin.get("reviewer_role") == "INDEPENDENT_NON_AUTHOR",
                        "ROLE_PROVENANCE", "qualified actual mode origin")
        else:
            scope_ref = origin.get("scope_ref", {})
            api.fields(scope_ref, ("path", "sha256", "bytes"), label="assembler Scope")
            scope_path = Path(scope_ref["path"])
            if not scope_path.is_absolute():
                scope_path = reader.repo / scope_path
            api.require(scope_path.resolve().is_relative_to((reader.repo / SOURCE_PREFIX).resolve()),
                        "ROLE_PROVENANCE", "assembler Scope path")
            relative = scope_path.resolve().relative_to(reader.repo).as_posix()
            _, assembly_scope = _witness(api, reader, dict(scope_ref, path=relative))
            api.require(assembly_scope.get("issued_by") == "codex:/root"
                        and assembly_scope.get("slice_id") == "W09_FULL_FORMAL_ASSEMBLY"
                        and origin.get("owner_id") in {"codex:/root", roles["executor"]}
                        and origin.get("lease_status") == "ACTIVE",
                        "ROLE_PROVENANCE", "actual assembly owner registration")
            api.require(api.stamp(context["created_at"], "assembly context")
                        <= api.stamp(origin.get("lease_expires_at"), "assembly lease"),
                        "EXECUTION_LEASE", "assembly lease was valid for the context")
        api.require(_raw(api, reader, proof["raw_ref"]) == proof["actor_id"],
                    "ROLE_PROVENANCE", "claimed actor differs from pinned actual origin")
        _role_audit(api, reader, proof, origin)
        seen.add(pair)
    api.require(seen == expected, "ROLE_PROVENANCE", "all five roles have pinned origins")
    routes = api.sequence(registry["route_execution_refs"], "route execution origins")
    api.require(len(routes) == 6 and
                {(row["command_key"], row["check_id"], row["case_id"]) for row in routes}
                == set(ROUTES), "ROLE_PROVENANCE", "six exact execution origins")
    return registry


def _route_execution_actor(api, reader, row, receipt, decision, registry):
    roles = registry["roles"]
    api.require(decision.get("producer_id") == roles["executor"],
                "EXECUTOR_ORIGIN", "actual Native mode producer")
    origin = next(item for item in registry["route_execution_refs"]
                  if (item["command_key"], item["check_id"], item["case_id"])
                  == (row["command_key"], row["check_id"], row["case_id"]))
    api.fields(origin, ("command_key", "check_id", "case_id", "scope_ref", "owner_ref"),
               label="actual route owner origin")
    scope_path, scope = _witness(api, reader, origin["scope_ref"])
    _, owner = _witness(api, reader, origin["owner_ref"])
    scope_pin = owner.get("scope_ref", {})
    scope_value = scope_pin.get("path", "")
    api.require(type(scope_value) is str and bool(scope_value), "EXECUTOR_ORIGIN", "scope path")
    scope_claim = Path(scope_value)
    if not scope_claim.is_absolute():
        scope_claim = reader.repo / scope_claim
    api.require(scope.get("issued_by") == "codex:/root"
                and scope_claim.resolve() == scope_path
                and scope_pin.get("sha256") == origin["scope_ref"]["sha256"]
                and scope_pin.get("bytes") == origin["scope_ref"]["bytes"]
                and owner.get("owner_id") in {"codex:/root", roles["executor"]}
                and owner.get("selected_worker_id") == roles["executor"]
                and owner.get("lease_status") == "ACTIVE"
                and row["command_key"] in owner.get("routes", [])
                and row["command_key"] in scope.get("routes", []),
                "EXECUTOR_ORIGIN", "Root Scope and actual selected worker")
    started, ended = api.interval(receipt, "original execution lease")
    api.require(ended <= api.stamp(owner.get("lease_expires_at"), "original lease expiry"),
                "EXECUTION_LEASE", "lease was valid for the original invocation")


def _independent_roles(api, registry, context, review, issuance, owner):
    roles = registry["roles"]
    executor, reviewer = context["executor_id"], api.text(review.get("reviewer_id"), "reviewer")
    api.require(reviewer == roles["verifier"]
                and review.get("executor_id") == executor
                and review.get("issuer_id") == reviewer
                and issuance.get("actor") == roles["root_observer"] == "codex:/root"
                and issuance.get("observer_id") == roles["root_observer"]
                and issuance.get("issuer_id") == reviewer
                and issuance.get("executor_id") == executor
                and issuance.get("reviewer_id") == reviewer
                and owner.get("executor_id") == executor
                and owner.get("verifier_id") == reviewer,
                "INDEPENDENT_ACTOR", "Verifier issues; Root observes original delivery")
    return reviewer


def _vector(api, reader, context):
    vector = api.fields(context["version_vector"],
                        ("schema", "package_version", "spec_files", "source_files", "input_files",
                         "lock_files", "tool_files", "environment", "components"), label="W09 vector")
    api.require(vector["schema"] == "researchos.w09.version-vector.v1"
                and vector["package_version"] == "2.4.0", "SCHEMA", "W09 vector")
    pinned = {}
    for group in ("spec_files", "source_files", "input_files", "lock_files", "tool_files"):
        rows = api.sequence(vector[group], group, False)
        api.require(len(rows) == len({r["path"] for r in rows}), "DUPLICATE_REFERENCE", group)
        for ref in rows:
            current_ref = ref
            correction = getattr(reader, "w09_header_correction", None)
            if correction is not None and ref == correction["certificate"]["old_profile_ref"]:
                current_ref = correction["certificate"]["new_profile_ref"]
            try:
                path = reader.ref(current_ref)
            except api.InvalidEvidence as exc:
                if exc.code in {"HASH_MISMATCH", "FILE_MISSING"}:
                    raise api.InvalidEvidence("NEEDS_REVALIDATION", ref["path"]) from exc
                raise
            api.require(path not in pinned or pinned[path] == current_ref["sha256"], "VECTOR_CONFLICT", ref["path"])
            pinned[path] = current_ref["sha256"]
    sources = {r["path"] for r in vector["source_files"]}
    api.require(MINIMUM_SOURCE <= sources, "SOURCE_COVERAGE", "W09 trusted and product sources")
    for directory in ("internal/domain", "adapters/retrieval"):
        required = {p.relative_to(reader.repo).as_posix()
                    for p in (reader.repo / directory).glob("*.go") if p.is_file()}
        api.require(required <= sources, "SOURCE_COVERAGE", directory + " Go source inventory")
    api.coverage(reader, context["source_coverage"], vector["source_files"])
    for name, digest in api.FROZEN_HASHES.items():
        api.require(any(Path(r["path"]).name == name and r["sha256"] == digest
                        for r in vector["spec_files"]), "VECTOR_BASELINE", name)
    for name in ("execution/v2.4/commands.json", "execution/toolchains/locked.json"):
        api.require(reader.path(name) in pinned, "VECTOR_INPUT", name)
    environment = api.fields(vector["environment"], ("os", "arch", "timezone"), label="environment")
    for value in environment.values():
        api.text(value, "environment")
    components = api.fields(vector["components"], ("model", "adapter", "rubric", "policy"), label="components")
    for name, component in components.items():
        api.fields(component, ("status", "reason") if name in {"model", "rubric"} else
                   ("status", "version", "refs"), label=name)
        if name in {"model", "rubric"}:
            api.require(component["status"] == "not_applicable" and api.text(component["reason"], name),
                        "COMPONENT_STATUS", name)
        else:
            api.require(component["status"] == "applicable" and api.text(component["version"], name),
                        "COMPONENT_STATUS", name)
            for ref in api.sequence(component["refs"], name):
                api.require(pinned.get(reader.ref(ref)) == ref["sha256"], "COMPONENT_UNPINNED", name)
    return pinned


def _trusted_closure(api, reader, pinned):
    """Only fixed repository code may inspect the Native graph."""
    source = reader.path("ops/ci/w09_evidence_closure.py")
    api.require(source in pinned and not source.is_symlink(), "TRUSTED_SOURCE", str(source))
    raw = source.read_bytes()
    api.require(hashlib.sha256(raw).hexdigest() == pinned[source], "INPUT_CHANGED_DURING_READ", str(source))
    namespace = {"__name__": "researchos_trusted_w09_closure", "__file__": str(source)}
    exec(compile(raw, str(source), "exec"), namespace)
    api.require(api.sha256(source) == pinned[source], "INPUT_CHANGED_DURING_READ", str(source))
    return namespace


def _router_contract(api, reader, pinned):
    """Read fixed router literals without running the router or receipt code."""
    path = reader.path("ops/ci/w09_formal_router.py")
    api.require(path in pinned and not path.is_symlink(), "TRUSTED_SOURCE", str(path))
    raw = path.read_bytes()
    api.require(hashlib.sha256(raw).hexdigest() == pinned[path], "INPUT_CHANGED_DURING_READ", str(path))
    values = {}
    for node in ast.parse(raw, filename=str(path)).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in {"NATIVE", "FORMAL", "SELECTED"}:
                values[name] = ast.literal_eval(node.value)
    api.require(set(values) == {"NATIVE", "FORMAL", "SELECTED"}, "ROUTER_CONTRACT", "fixed route tables")
    api.require(api.sha256(path) == pinned[path], "INPUT_CHANGED_DURING_READ", str(path))
    return values


def _pin_observed(api, reader, path, expected):
    """One compare-before-register path for every non-JSON Native input."""
    api.require(type(expected) is str and api.SHA.fullmatch(expected), "HASH_FORMAT", str(path))
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    api.require(digest == expected, "HASH_MISMATCH", str(path))
    api.require(path not in reader.read_hashes or reader.read_hashes[path] == digest,
                "INPUT_CHANGED_DURING_READ", str(path))
    reader.read_hashes[path] = digest
    return raw


def _native_zero(api, report, tool, label):
    api.require(type(report.get("exit_code")) is int and report["exit_code"] == 0
                and type(tool.get("native_exit_code")) is int and tool["native_exit_code"] == 0,
                "NATIVE_EXIT_TYPE", label)


def _source21(api, reader, report, pinned, producer_sources, label):
    source_hashes = api.obj(report.get("version_manifest", {}).get("source_sha256"), "Native Source21")
    api.require(set(source_hashes) == producer_sources and len(source_hashes) == 21,
                "NATIVE_SOURCE21_SET", label)
    for relative, digest in source_hashes.items():
        api.require(type(digest) is str and digest.startswith("sha256:")
                    and api.SHA.fullmatch(digest[7:]), "SOURCE_HASH", relative)
        path = reader.path(relative)
        api.require(pinned.get(path) == digest[7:], "CURRENT_SOURCE_CLOSURE", relative)
        _pin_observed(api, reader, path, digest[7:])


def _producer_sources(api, reader, pinned):
    """The actual producer's 21-name execution inventory is a pinned input."""
    path = reader.path("ops/ci/retrieval.py")
    api.require(path in pinned, "SOURCE_COVERAGE", "producer source")
    raw = _pin_observed(api, reader, path, pinned[path])
    matches = []
    for node in ast.parse(raw, filename=str(path)).body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "SOURCES"):
            matches.append(ast.literal_eval(node.value))
    api.require(len(matches) == 1 and type(matches[0]) is list
                and len(matches[0]) == len(set(matches[0])) == 21,
                "PRODUCER_SOURCE_INVENTORY", "exact 21 source paths")
    api.require(all(type(name) is str and name for name in matches[0]),
                "PRODUCER_SOURCE_INVENTORY", "source path type")
    return set(matches[0])


def _native_event_interval(api, raw, report, selected, label):
    """Bind each Go package and test lifecycle to pinned original JSONL order."""
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise api.InvalidEvidence("GO_EVENT_CLOCK", label + " UTF-8") from exc
    api.require(bool(lines), "GO_EVENT_CLOCK", label + " empty stream")
    events = [api.strict_json(line.encode("utf-8")) for line in lines]
    api.require(all(type(event) is dict for event in events), "GO_EVENT_CLOCK", label + " event shape")
    clocks = [api.stamp(event.get("Time"), label + " Go Time") for event in events]
    started, ended = api.interval(report, "native " + label)
    first, last = min(clocks), max(clocks)
    api.require(started <= first <= last <= ended, "GO_EVENT_CLOCK", label + " report/raw contradiction")

    packages = {}
    for position, (event, clock) in enumerate(zip(events, clocks)):
        package = event.get("Package")
        api.require(type(package) is str and package
                    and event.get("Action") in {"start", "run", "pause", "cont", "pass",
                                                "fail", "skip", "output", "bench"},
                    "GO_EVENT_TERMINAL", label + " event identity")
        test = event.get("Test")
        api.require(test is None or (type(test) is str and test),
                    "GO_EVENT_TERMINAL", label + " test identity")
        packages.setdefault(package, []).append((position, event, clock))
    api.require(bool(packages), "GO_EVENT_TERMINAL", label + " no package")

    selected_seen = set()
    for package, rows in packages.items():
        package_events = [(i, event, clock) for i, event, clock in rows if not event.get("Test")]
        starts = [row for row in package_events if row[1]["Action"] == "start"]
        terminals = [row for row in package_events
                     if row[1]["Action"] in {"pass", "fail", "skip"}]
        api.require(len(starts) == len(terminals) == 1
                    and terminals[0][1]["Action"] == "pass",
                    "GO_EVENT_TERMINAL", label + " " + package + " package endpoints")
        start_row, terminal_row = starts[0], terminals[0]
        api.require(start_row[0] < terminal_row[0]
                    and start_row[2] <= terminal_row[2]
                    and rows[0][0] == start_row[0] and rows[-1][0] == terminal_row[0]
                    and all(start_row[0] <= i <= terminal_row[0]
                            and start_row[2] <= clock <= terminal_row[2]
                            for i, _event, clock in rows)
                    and all(left[2] <= right[2] for left, right in zip(rows, rows[1:])),
                    "GO_EVENT_TERMINAL", label + " " + package + " lifecycle")

        tests = {}
        for row in rows:
            test = row[1].get("Test")
            if test:
                tests.setdefault(test, []).append(row)
        api.require(any(test in selected for test in tests),
                    "GO_EVENT_TERMINAL", label + " " + package + " unmatched package")
        for test, test_rows in tests.items():
            runs = [row for row in test_rows if row[1]["Action"] == "run"]
            terminal_tests = [row for row in test_rows
                              if row[1]["Action"] in {"pass", "fail", "skip"}]
            api.require(len(runs) == len(terminal_tests) == 1
                        and terminal_tests[0][1]["Action"] == "pass",
                        "GO_EVENT_TERMINAL", label + " " + package + " " + test + " endpoints")
            run_row, pass_row = runs[0], terminal_tests[0]
            api.require(start_row[0] < run_row[0] < pass_row[0] < terminal_row[0]
                        and start_row[2] <= run_row[2] <= pass_row[2] <= terminal_row[2]
                        and test_rows[0][0] == run_row[0]
                        and test_rows[-1][0] == pass_row[0]
                        and all(run_row[0] <= i <= pass_row[0]
                                and run_row[2] <= clock <= pass_row[2]
                                for i, _event, clock in test_rows),
                        "GO_EVENT_TERMINAL", label + " " + package + " " + test + " lifecycle")
            if test in selected:
                api.require(test not in selected_seen, "GO_EVENT_TERMINAL",
                            label + " duplicate selected test " + test)
                selected_seen.add(test)
    api.require(selected_seen == set(selected)
                and len(selected) == len(set(selected)),
                "GO_EVENT_TERMINAL", label + " selected test ownership")
    return first.isoformat(), last.isoformat()


def _native(api, reader, row, closure, router, pinned, producer_sources):
    """Recompute actual Go JSONL, owned raw graph, HTTP/DB/file facts and mode."""
    report_ref, tool_ref, decision_ref = (row[name] for name in
                                          ("native_report_ref", "native_tool_run_ref", "mode_decision_ref"))
    report = _doc(api, reader, report_ref, NATIVE_PREFIX)
    tool = _native_tool_doc(api, reader, tool_ref)
    route = (row["command_key"], "W09", row["check_id"], row["case_id"])
    key = row["check_id"] or row["case_id"]
    api.require(route in router["NATIVE"] and route in router["FORMAL"] and route in router["SELECTED"],
                "ROUTER_CONTRACT", key)
    api.exact_ids(list(router["FORMAL"][route]), IDS[key], "router formal IDs")
    _native_zero(api, report, tool, key)
    native_start, native_end = api.interval(report, "native " + key)
    api.require(report.get("formal_construction_acceptance") == "NOT_RUN_POSTRUN_REVIEW_PENDING"
                and report.get("status") == "PASS" and report.get("task_id") == "W09"
                and report.get("check_id") == (row["check_id"] or None)
                and report.get("case_id") == (row["case_id"] or None)
                and report.get("scope") == ("LIVE_WINDOWS_LOCAL" if key == "W09-G02"
                                             else "FIXTURE_IMPLEMENTED_SERVICE")
                and report.get("timed_out") is False
                and type(report.get("assertion_ids")) is list
                and len(report["assertion_ids"]) == len(set(report["assertion_ids"]))
                and sorted(report["assertion_ids"]) == sorted(router["NATIVE"][route])
                and type(report.get("expected_assertion_ids")) is list
                and sorted(report["expected_assertion_ids"]) == sorted(router["NATIVE"][route])
                and sorted(report.get("selected_tests", [])) == sorted(router["SELECTED"][route])
                and sorted(report.get("passed_tests", [])) == sorted(router["SELECTED"][route])
                and tool.get("schema") == "researchos.w09-native-producer-tool-run.v1"
                and tool.get("report_ref") == report_ref["path"]
                and tool.get("report_sha256") == report_ref["sha256"]
                and tool.get("run_id") == report.get("run_id")
                and tool.get("native_exit_code") == report.get("exit_code")
                and tool.get("formal_acceptance") == "NOT_RUN"
                and tool.get("actual_invocation") == report.get("actual_invocation"),
                "NATIVE_TOOL_RUN", key)
    source = dict(report, report_reference=report_ref["path"])
    # The report, its native streams, all owned members and every source hash
    # become Reader/CAS inputs. The closure replays their semantics below.
    api.require(report_ref["path"].startswith(NATIVE_PREFIX), "PATH_SCOPE", key)
    streams = api.sequence(report.get("raw_evidence_references"), "native streams")
    api.require(len(streams) == 2, "NATIVE_STREAMS", key)
    stream_raw = []
    for relative, claimed in zip(streams, (tool.get("stdout_sha256"), tool.get("stderr_sha256"))):
        path = reader.path(relative, NATIVE_PREFIX)
        stream_raw.append(_pin_observed(api, reader, path, claimed))
    api.require(tool.get("stdout_ref") == report["raw_evidence_references"][0]
                and tool.get("stderr_ref") == report["raw_evidence_references"][1]
                and tool.get("stdout_sha256") == reader.read_hashes[reader.path(tool["stdout_ref"], NATIVE_PREFIX)]
                and tool.get("stderr_sha256") == reader.read_hashes[reader.path(tool["stderr_ref"], NATIVE_PREFIX)],
                "NATIVE_TOOL_STREAMS", key)
    claims = api.sequence(report.get("owned_export", {}).get("members"), "owned raw members")
    owned_dir = (Path(report_ref["path"]).parent / "owned").as_posix()
    inventory = api._owned_inventory(reader, owned_dir, claims)
    reader.w09_owned_inventories.append(inventory)
    _source21(api, reader, report, pinned, producer_sources, key)
    locked = reader.read(reader.path("execution/toolchains/locked.json"))
    go = locked["tools"]["go"]
    reader.local_tool(go["path"], go["sha256"])
    selected = router["SELECTED"][route]
    go_interval = _native_event_interval(api, stream_raw[0], report, selected, key)
    owner = {"C19-01": "TestW09C19ExplicitOriginAndUnknown",
             "C19-02": "TestW09C19ExplicitOriginAndUnknown",
             "C19-03": "TestW09C19ExplicitOriginAndUnknown",
             "C19-04": "TestW09C19ExplicitOriginAndUnknown",
             "C19-05": "TestW09C19ChainInvalidation",
             "A06-01": "TestW09A06HTTPInvalidationAndContext",
             "A06-02": "TestW09A06HTTPInvalidationAndContext",
             "A06-03": "TestW09A06FTSFallbackAndDuplicatePath",
             "W09-G02-UNICODE-LOCATOR": "TestW09UnicodeLocator",
             "W09-G02-ROOT-REPLACEMENT": "TestW09RootReplacementCannotFeedProduct",
             "W09-G02-STALE-INPUT-BODY": "TestW09TaskInputCannotRematerializeStaleLocalBody",
             "W09-G02-LEGACY-ROOT": "TestW09LegacyRootMigrationRevokesUnidentifiedRoot"}
    native = closure["verify_native"](reader.repo, source, report, router["NATIVE"][route], selected)
    owned = closure["verify_owned"](reader.repo, source, report, selected, owner)
    if key == "C19" or key == "W09-G01":
        closure["verify_c19"](owned)
    if key in {"A06", "W09-G01", "W09-G02"}:
        closure["verify_a06"](owned)
    decision = _doc(api, reader, decision_ref, SOURCE_PREFIX)
    for witness in (decision.get("independent_review_ref"), decision.get("host_witness"),
                    decision.get("junction_witness")):
        if witness is not None:
            api.fields(witness, ("path", "sha256", "bytes"), label="mode witness")
            path = reader.path(witness["path"], SOURCE_PREFIX)
            _pin_observed(api, reader, path, witness["sha256"])
            api.require(type(witness["bytes"]) is int and path.stat().st_size == witness["bytes"],
                        "MODE_WITNESS_PIN", witness["path"])
    mode = closure["verify_mode"](reader.repo, source, report, route, owned, native,
                                  decision_ref["path"], decision_ref["sha256"])
    api.require(mode["formal_authority"] is False and mode["mode"] ==
                ("LIVE_WINDOWS" if key == "W09-G02" else "FIXTURE"), "MODE_SCOPE", key)
    return report, native, mode, (native_start, native_end, go_interval)


def _dispatches(api, reader, context, pinned, closure, router, plan, producer_sources, role_registry):
    rows = api.sequence(context["registered_commands"], "six registered commands")
    api.require(len(rows) == 6, "ROUTE_SET", "six exact routes")
    step = next(s for s in plan["steps"] if s["id"] == "W09-99")
    frozen = {(x["key"], x.get("check_id", ""), x.get("case_id", "")): x
              for x in step["verification_commands"]}
    api.require(set(frozen) == set(ROUTES), "FROZEN_ROUTE_SET", "W09")
    api.require({(r["command_key"], r["check_id"], r["case_id"]) for r in rows} == set(ROUTES),
                "ROUTE_SET", "W09")
    registry_path = reader.path("execution/v2.4/commands.json")
    registry = reader.read(registry_path)
    locked_path = reader.path("execution/toolchains/locked.json")
    locked = reader.read(locked_path)
    outputs = {}
    facts = {}
    for row in rows:
        key, check, case = row["command_key"], row["check_id"], row["case_id"]
        ident = check or case
        binding = frozen[(key, check, case)]
        api.exact_ids(binding["expected_assertion_ids"], IDS[ident], "frozen assertions")
        receipt = _doc(api, reader, row["receipt_ref"], "execution/invocations/")
        api.require(receipt.get("command_key") == key and receipt.get("status") == "PASS"
                    and type(receipt.get("exit_code")) is int and receipt["exit_code"] == 0
                    and type(receipt.get("child_exit_code")) is int and receipt["child_exit_code"] == 0
                    and receipt.get("scope") == "CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE",
                    "COMMAND_EXIT", ident)
        historical = _historical_registry(api, reader, row, receipt, registry, pinned.get(registry_path))
        api.require(receipt.get("selectors") == {"task_id": "W09", "check_id": check, "case_id": case}
                    and receipt.get("registry_spec") == "v2.4"
                    and (historical or receipt.get("registered_command_revision") == pinned.get(registry_path))
                    and receipt.get("toolchain_revision") == pinned.get(locked_path)
                    and receipt.get("dispatcher_sha256") == pinned.get(reader.path("execution/command_dispatcher/dispatch.py")),
                    "COMMAND_IDENTITY", ident)
        entry = registry["commands"][key]
        selector = "check_id" if check else "case_id"
        api.require(entry["state"] == "BOUND" and "W09" in entry["selectors"]["task_id"]
                    and ident in entry["selectors"][selector]
                    and receipt["argv"][1:] == entry["argv"]
                    and Path(receipt["cwd"]).resolve() == reader.repo,
                    "COMMAND_UNBOUND", ident)
        tool = locked["tools"][entry["executable_tool"]]
        reader.local_tool(tool["path"], tool["sha256"])
        api.require(Path(receipt["argv"][0]).resolve() == Path(tool["path"]).resolve(),
                    "DISPATCH_EXECUTABLE", ident)
        api.interval(receipt, ident)
        for ref in api.sequence(receipt["input_versions"], "dispatcher input versions"):
            _dispatcher_input(api, reader, ref, pinned, historical, ident)
        for name in ("stdout", "stderr"):
            ref = receipt[name]
            api.require(ref["path"] == "execution/invocations/" + receipt["invocation_id"] + "/" + name + ".txt",
                        "DISPATCH_RAW_IDENTITY", ident)
            reader.ref(ref, "execution/invocations/")
        output = reader.document(receipt["stdout"])
        api.require(output.get("status") == "PASS" and output.get("task_id") == "W09"
                    and output.get("check_id") == (check or None)
                    and output.get("case_id") == (case or None)
                    and output.get("formal_acceptance") == "PENDING_INDEPENDENT_VERIFIER"
                    and type(output.get("assertions")) is int and output["assertions"] == len(IDS[ident]),
                    "COMMAND_OUTPUT", ident)
        api.exact_ids(output["assertion_ids"], IDS[ident], "dispatcher output")
        report, native, mode, native_interval = _native(api, reader, row, closure, router, pinned,
                                                       producer_sources)
        actual_mode = _doc(api, reader, row["mode_decision_ref"], SOURCE_PREFIX)
        _route_execution_actor(api, reader, row, receipt, actual_mode, role_registry)
        source_pins = [{"path": relative, "sha256": api.sha256(reader.path(relative, NATIVE_PREFIX)),
                        "bytes": reader.path(relative, NATIVE_PREFIX).stat().st_size}
                       for relative in [*report["raw_evidence_references"], row["native_report_ref"]["path"]]]
        api.require(output.get("mode_evidence") == mode
                    and output.get("source_pins") == source_pins
                    and output.get("native_tool_run_ref") == row["native_tool_run_ref"]["path"]
                    and receipt.get("assertion_ids") == list(IDS[ident]), "DISPATCH_NATIVE_LINK", ident)
        outputs[(key, check, case)] = {"receipt": row["receipt_ref"], "output": receipt["stdout"],
                                      "report": row["native_report_ref"], "run_id": native["run_id"],
                                      "mode": mode["mode"], "started_at": receipt["started_at"],
                                      "ended_at": receipt["ended_at"],
                                      "native_started_at": report["started_at"],
                                      "native_ended_at": report["ended_at"],
                                      "native_event_started_at": native_interval[2][0],
                                      "native_event_ended_at": native_interval[2][1]}
        facts[(key, check, case)] = report["assertion_results"]
    return outputs, facts


def _global(api, reader, context, outputs, facts, review):
    cases = api.fields(context["global_evidence_refs"], ("C19", "A06"), label="GLOBAL case map")
    acceptance = reader.read(reader.ref(context["acceptance_baseline_ref"]))
    catalog = {case["id"]: case for case in acceptance["cases"]}
    accepted_rows = {}
    for cid in ("C19", "A06"):
        refs = api.fields(cases[cid], ("run_receipt", "version_manifest", "command_receipt", "assertion_results"),
                          label=cid + " GLOBAL")
        paths = [_ref(api, reader, ref) for ref in refs.values()]
        api.require(len(set(paths)) == 4, "DUPLICATE_REFERENCE", cid)
        run, manifest, command, assertions = [reader.read(path) for path in paths]
        for doc, name in ((run, "run-receipt"), (manifest, "version-manifest"),
                          (command, "command-receipt"), (assertions, "assertion-results")):
            api.require(doc.get("schema") == "researchos.w09." + name + ".v1"
                        and doc.get("case_id") == cid and doc.get("run_id") == context["run_id"],
                        "GLOBAL_IDENTITY", cid + name)
        api.fields(run, ("schema", "case_id", "run_id", "environment_mode", "os", "arch", "timezone",
                         "started_at", "ended_at", "executor_id", "verifier_id"), label="run receipt")
        api.require(run["environment_mode"] == catalog[cid]["mode"] == "FIXTURE"
                    and run["executor_id"] == context["executor_id"]
                    and run["verifier_id"] == review["reviewer_id"]
                    and {k: run[k] for k in ("os", "arch", "timezone")} == context["version_vector"]["environment"],
                    "GLOBAL_RUN", cid)
        api.interval(run, cid)
        route_times = [outputs[route] for route in outputs if route[2] == cid]
        api.require(len(route_times) == 2 and all(
            api.stamp(run["started_at"], cid + " start") <= api.stamp(item["native_started_at"], "native start")
            <= api.stamp(item["native_event_started_at"], "Go first event")
            <= api.stamp(item["native_event_ended_at"], "Go last event")
            <= api.stamp(item["native_ended_at"], "native end")
            <= api.stamp(item["started_at"], "dispatch start")
            <= api.stamp(item["ended_at"], "dispatch end") <= api.stamp(run["ended_at"], cid + " end")
            for item in route_times), "GLOBAL_RUN_TIME", cid)
        api.require(manifest.get("package_version") == "2.4.0"
                    and api.COMMIT.fullmatch(manifest.get("code_revision", ""))
                    and type(manifest.get("dirty")) is bool
                    and manifest.get("version_vector") == context["version_vector"]
                    and manifest.get("components") == context["version_vector"]["components"]
                    and manifest.get("lock_files") == context["version_vector"]["lock_files"]
                    and manifest.get("input_files") == context["version_vector"]["input_files"],
                    "GLOBAL_VERSION", cid)
        package_ref = manifest.get("package_manifest_ref")
        package_path = reader.ref(package_ref)
        api.require(package_path.name == "PACKAGE_MANIFEST.json"
                    and package_ref in context["version_vector"]["spec_files"],
                    "GLOBAL_PACKAGE_PIN", cid)
        expected = [value for route, value in outputs.items() if route[2] == cid]
        api.require(len(expected) == 2 and command.get("registered_commands") == expected
                    and command.get("command_keys") == list(catalog[cid]["command_keys"]),
                    "GLOBAL_COMMAND", cid)
        rows = api.sequence(assertions.get("assertions"), "GLOBAL assertions")
        api.exact_ids([row["id"] for row in rows], IDS[cid], "GLOBAL assertions")
        for row in rows:
            api.fields(row, ("id", "expected", "actual", "status", "raw_evidence_refs", "refusal_evidence_refs"),
                       label="GLOBAL assertion")
            frozen = next(x for x in catalog[cid]["assertions"] if x["id"] == row["id"])
            api.require(row["expected"] == frozen["expected"] and row["status"] == "PASS"
                        and api.meaningful(row["actual"]), "GLOBAL_ASSERTION", row["id"])
            accepted_rows[row["id"]] = row
            claim_matches = []
            for route, records in facts.items():
                if route[2] != cid:
                    continue
                rec = next((item for item in records if item["assertion_id"] == row["id"]), None)
                api.require(rec is not None, "GLOBAL_ASSERTION", row["id"] + " absent in native route")
                owned = rec["owned_export_ref"]
                raw_path = Path(owned["path"]).resolve(strict=True)
                api.require(raw_path.is_relative_to(reader.repo), "RAW_PATH", row["id"])
                claim_matches.append((rec["evidence"], raw_path.relative_to(reader.repo).as_posix(),
                                      owned["sha256"]))
            api.require(len(claim_matches) == 2, "GLOBAL_ASSERTION", row["id"] + " two native routes")
            for raw in api.sequence(row["raw_evidence_refs"], "raw evidence"):
                actual = _raw(api, reader, raw)
                api.require(raw["locator"] == {"json_pointer": "/actual"}
                            and any((actual, raw["path"], raw["sha256"]) == match
                                    and row["actual"] == actual for match in claim_matches),
                            "GLOBAL_RAW_LINK", row["id"])
            for raw in api.sequence(row["refusal_evidence_refs"], "refusal evidence", False):
                _raw(api, reader, raw)
            if row["id"] == "A06-02":
                api.require(bool(row["refusal_evidence_refs"]), "GLOBAL_NEGATIVE", row["id"])
    return accepted_rows


def _review_execution_cutoff(api, outputs, global_runs, context_created, review_issued):
    cutoff = api.stamp(review_issued, "review")
    api.require(all(
        api.stamp(item["native_started_at"], "native start")
        <= api.stamp(item["native_event_started_at"], "Go first event")
        <= api.stamp(item["native_event_ended_at"], "Go last event")
        <= api.stamp(item["native_ended_at"], "native end")
        <= api.stamp(item["started_at"], "dispatch start")
        <= api.stamp(item["ended_at"], "dispatch end")
        <= api.stamp(context_created, "context") <= cutoff
        for item in outputs.values()), "REVIEW_EXECUTION_CUTOFF", "all six routes")
    api.require(len(outputs) == 6 and set(global_runs) == {"C19", "A06"},
                "REVIEW_EXECUTION_CUTOFF", "six routes and two GLOBAL receipts")
    for case, run in global_runs.items():
        api.require(api.stamp(run["ended_at"], case + " GLOBAL end") <= cutoff,
                    "REVIEW_EXECUTION_CUTOFF", case)
    return cutoff


def _capture_registry(api, reader, issuance):
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
    path = reader.ref({"path": authority["path"], "sha256": authority["sha256"]},
                      ROOT_CAPTURE_PREFIX)
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
    capture_ref, origin_ref = entry["capture_ref"], entry["origin_ref"]
    api.require(type(capture_ref) is dict and set(capture_ref) == {"path", "sha256", "bytes"}
                and type(origin_ref) is dict and set(origin_ref) == {"path", "sha256", "bytes"},
                "ROOT_CAPTURE_REGISTRY", "strict capture references")
    capture_path = reader.ref({"path": capture_ref["path"], "sha256": capture_ref["sha256"]},
                              ROOT_CAPTURE_PREFIX)
    api.require(type(capture_ref["bytes"]) is int
                and capture_path.stat().st_size == capture_ref["bytes"],
                "ROOT_CAPTURE_REGISTRY", "capture bytes")
    capture = reader.read(capture_path)
    origin_path = reader.ref({"path": origin_ref["path"], "sha256": origin_ref["sha256"]},
                             ROOT_ORIGIN_PREFIX)
    origin_raw = origin_path.read_bytes()
    api.require(type(entry["origin_ref"].get("bytes")) is int
                and len(origin_raw) == entry["origin_ref"]["bytes"],
                "ROOT_ORIGINAL_EVENT", "captured original bytes")
    lines = origin_raw.splitlines(keepends=True)
    api.require(len(lines) == 3 and all(line.endswith(b"\n") for line in lines),
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
                and content_items[0]["type"] == "input_text"
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
            reader.w09_audit_ranges.append(_audit_line(api, reader, offset, digest, line, observed,
                                                      "ROOT_ORIGINAL_SOURCE", "original audit bytes disagree"))
    return capture, message


def _independent(api, reader, owner, roots, context, outputs, global_rows, role_registry):
    review, issuance = reader.read(roots["review"]), reader.read(roots["issuance"])
    api.require(review.get("schema") == SCHEMAS["review"]
                and issuance.get("schema") == SCHEMAS["issuance"], "SCHEMA", "W09 review/issuance")
    reviewer = _independent_roles(api, role_registry, context, review, issuance, owner)
    for doc in (review, issuance):
        api.require(doc.get("task_id") == "W09" and doc.get("step_id") == "W09-99"
                    and doc.get("run_id") == context["run_id"]
                    and reader.ref(doc["context_ref"], PREFIX) == roots["context"],
                    "REVIEW_IDENTITY", "W09")
    api.require(_ref(api, reader, issuance["review_ref"]) == roots["review"]
                and review.get("acceptance_baseline_ref") == context["acceptance_baseline_ref"]
                and review.get("version_vector") == context["version_vector"]
                and review.get("registered_commands") == context["registered_commands"]
                and review.get("global_evidence_refs") == context["global_evidence_refs"]
                and review.get("decision") == "ACCEPTED"
                and review.get("missing") == [] and review.get("failed") == []
                and not review.get("supersedes_review_refs"), "REVIEW_VERDICT", "W09")
    verdicts = api.sequence(review.get("verdicts"), "formal verdicts")
    api.exact_ids([v["id"] for v in verdicts], (*IDS["C19"], *IDS["A06"], "W09-G01", "W09-G02"),
                  "formal verdicts")
    for verdict in verdicts:
        api.require(verdict.get("status") == "PASS" and api.meaningful(verdict.get("actual")),
                    "REVIEW_VERDICT", verdict["id"])
        if verdict["id"] in global_rows:
            api.require(verdict["actual"] == global_rows[verdict["id"]]["actual"]
                        and verdict.get("expected") == global_rows[verdict["id"]]["expected"],
                        "REVIEW_GLOBAL_LINK", verdict["id"])
        else:
            gate = next((value for route, value in outputs.items() if route[1] == verdict["id"]), None)
            api.require(gate is not None and verdict.get("mode") == gate["mode"]
                        and verdict.get("run_id") == gate["run_id"],
                        "REVIEW_GATE_LINK", verdict["id"])
            api.require(any(raw.get("path") == gate["report"]["path"]
                            and raw.get("sha256") == gate["report"]["sha256"]
                            and raw.get("locator") == {"json_pointer": "/assertion_results"}
                            for raw in verdict["raw_evidence_refs"]),
                        "REVIEW_GATE_RAW", verdict["id"])
        for raw in api.sequence(verdict.get("raw_evidence_refs"), "review raw evidence"):
            _raw(api, reader, raw)
    # This registry and the original event are Root-owned fixed inputs. They
    # must be captured from the actual collaboration delivery after it occurs;
    # an author-written W09 receipt cannot stand in for either file.
    capture, origin = _root_original(api, reader, issuance, reviewer, roots)
    global_runs = {case: _doc(api, reader, context["global_evidence_refs"][case]["run_receipt"])
                   for case in ("C19", "A06")}
    cutoff = _review_execution_cutoff(api, outputs, global_runs, context["created_at"], review["issued_at"])
    api.require(cutoff <= api.stamp(capture["received_at"], "original received")
                <= api.stamp(capture["root_observed_at"], "Root capture")
                <= api.stamp(issuance["observed_at"], "Root observed")
                <= api.stamp(owner["accepted_at"], "owner accepted"),
                "REGISTERED_TIME_ORDER", "original Root delivery")


def verify_owner(api, reader, owner, roots, plan_path):
    api.require(owner.get("status") == "ACCEPTED", "OWNER_NOT_ACCEPTED", "W09-99")
    context = reader.read(roots["context"])
    api.require(context.get("schema") == SCHEMAS["context"]
                and context.get("task_id") == "W09" and context.get("step_id") == "W09-99",
                "SCHEMA", "W09 context")
    api.text(context.get("executor_id"), "executor")
    api.text(context.get("run_id"), "run id")
    baseline = reader.ref(context["acceptance_baseline_ref"])
    api.require(baseline.name == "acceptance.json"
                and context["acceptance_baseline_ref"]["sha256"] == api.FROZEN_HASHES["acceptance.json"],
                "FROZEN_BASELINE", "W09")
    reader.w09_audit_ranges = []
    reader.w09_header_correction = _header_correction(api, reader, roots)
    pinned = _vector(api, reader, context)
    role_registry = _role_registry(api, reader, context)
    role_ref = context["role_policy"]["registry_ref"]
    role_path = reader.ref({name: role_ref[name] for name in ("path", "sha256")}, ROOT_CAPTURE_PREFIX)
    api.require(pinned.get(role_path) == role_ref["sha256"], "ROLE_POLICY_UNPINNED", "current input vector")
    plan = reader.read(Path(plan_path).resolve(strict=True))
    step = next(s for s in plan["steps"] if s["id"] == "W09-99")
    state = reader.read(reader.path("execution/v2.4/step_state.json"))
    statuses = {s["id"]: s["status"] for s in state["steps"]}
    api.require(all(statuses.get(dep) == "ACCEPTED" for dep in step["dependencies"]),
                "DEPENDENCY", "W09 parent")
    closure = _trusted_closure(api, reader, pinned)
    router = _router_contract(api, reader, pinned)
    producer_sources = _producer_sources(api, reader, pinned)
    reader.w09_owned_inventories = []
    outputs, facts = _dispatches(api, reader, context, pinned, closure, router, plan, producer_sources, role_registry)
    review = reader.read(roots["review"])
    global_rows = _global(api, reader, context, outputs, facts, review)
    _independent(api, reader, owner, roots, context, outputs, global_rows, role_registry)
    for inventory in reader.w09_owned_inventories:
        api.require(api._owned_inventory(reader, inventory["directory"], inventory["members"]) == inventory,
                    "OWNED_INVENTORY_CHANGED", inventory["directory"])
    reader.finish()
    context["_verified_owned_inventories"] = list(reader.w09_owned_inventories)
    context["_verified_audit_ranges"] = list(reader.w09_audit_ranges)
    return context
