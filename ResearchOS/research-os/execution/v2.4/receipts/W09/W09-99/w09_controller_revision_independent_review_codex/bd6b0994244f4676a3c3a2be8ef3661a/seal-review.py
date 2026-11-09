from pathlib import Path
import hashlib
import json

BASE = Path(__file__).resolve().parent
ACTOR = "codex:/root/f08_i17_binding_impl"
CANDIDATE = BASE.parents[2] / "w09_controller_revision_preparation_codex" / "c1eefb6423544a4eaf22fb9045692630"

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": path.as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}

def json_read(path):
    return json.loads(Path(path).read_bytes())

def write_new(name, value):
    target = BASE / name
    require(target.parent.resolve() == BASE, "Own namespace required")
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with target.open("xb") as stream:
        stream.write(raw)
    return ref(target)

def pinned(path, digest, size):
    result = ref(path)
    require(result["sha256"] == digest and result["bytes"] == size, "Fixed input drift: " + str(path))
    return result

require(BASE.name == "bd6b0994244f4676a3c3a2be8ef3661a", "Wrong review namespace")
require(BASE.parent.name == "w09_controller_revision_independent_review_codex", "Wrong ownership")
# Fixed sealed inputs only; mutable MAIN state is never read.
# Derive the sibling source namespace from the actual owned receipt hierarchy.
CANDIDATE = BASE.parent.parent / "w09_controller_revision_preparation_codex" / "c1eefb6423544a4eaf22fb9045692630"
candidate_handoff_ref = pinned(CANDIDATE / "handoff.json", "b105a28528300c250d176941be2c86427bb595ae123e08597f63ff37013c4a57", 7003)
candidate_manifest_ref = pinned(CANDIDATE / "manifest.json", "7b3e072c962165ff3fd372dc313e0c371afd79005bd01292fe2e9dc20adac954", 20600)
postseal_annex_ref = pinned(CANDIDATE / "postseal-audit.json", "a68219e764836febbfb78f57c741be13b1e6aef207ce18a35fb69379dcfeb41b", 413)
origin_ref = pinned(BASE / "coordination-failure-origin.json", "21eb69a5dcc61a1f6ea23ca7ef9075a4e9f3b928ea409643671b263ea713161f", 2400)
audit_ref = pinned(BASE / "static-source-audit.json", "9b83243985a5c8cb5c6e641e1c5d7c9d5c4957d3bda2f8c10d351f597de3ed06", 157979)
before_ref = pinned(BASE / "inputs.before.json", "5a64eaccaa6114f2a6dcd52998c03232338fb03ea2f7e5ce24c2fc39f79169fa", 47585)
after_ref = pinned(BASE / "inputs.after.json", "eef79ec063ab88e1693036c3e84f6a790625e2a87fc0ec0571558392fe6581fa", 106900)
audit = json_read(BASE / "static-source-audit.json")
handoff = json_read(CANDIDATE / "handoff.json")
manifest = json_read(CANDIDATE / "manifest.json")
tools = json_read(BASE / "tool-observations.json")
require(handoff["author"] == "codex:/root/command_queue_impl" and handoff["author"] != ACTOR, "Non-author review identity required")
require(all(audit["checks"].values()) and len(audit["checks"]) == 12, "Independent static checks not all satisfied")
require(audit["candidate_imported_or_executed"] is False, "Candidate execution outside authorization")
require(audit["C05_real_root_producer_currently_present"] is False, "Do not turn consumer schema into actual producer proof")
require(manifest["member_count"] == 64 and len(manifest["members"]) == 64, "Preserve original declared membership")
require(tools["new_failed_tools"] == {"total": 1, "coordination": 1, "exec_command": 0, "native_product": 0}, "Failure count changed")
require(audit["old_os206_recounted"] is False and audit["local_exec_command_failures"] == 0, "Preserve original NULL failure facts")
require(all(value == 0 for value in audit["execution_counts"].values()), "Target or mutable MAIN access occurred")
source_anchor_locations = [{key: anchor[key] for key in ("file", "start", "end")} for anchor in audit["source_anchors"]]
dispositions = [
    {
        "id": "C01",
        "disposition": "SOURCE_CONTROL_FIX_VERIFIED",
        "source": "selected/windows_debug_job_tree.py:343-451; cleanup:569-582",
        "finding": "Unknown or rejected image event sets failure and prevents continuation. A held owned event can continue only after successful actual TerminateJobObject. Failed termination retains pending event; cleanup cannot resume it without observed termination success and ownership.",
        "actual_job_or_unknown_image_execution": "NOT_RUN",
    },
    {
        "id": "C02",
        "disposition": "SOURCE_CONTROL_FIX_VERIFIED",
        "source": "selected/windows_debug_job_tree.py:108-110,368-370,408-408,592-609",
        "finding": "The live generations list is published before event processing. Partial process generations survive exceptions and timeouts; unobserved identity/exit facts remain NULL. Requested termination code is separate from independently observed native exit.",
        "actual_timeout_or_exception_run": "NOT_RUN",
    },
    {
        "id": "C03",
        "disposition": "SOURCE_CONTROL_FIX_VERIFIED",
        "source": "selected/controller.py:run/resources; exact original line excerpts in static-source-audit.json",
        "finding": "run no longer permits allow_nonzero or overwrites actual exit with zero. Unexpected symlink or junction resource failure records failure and stops. Only explicitly unavailable resources in the grant yield the preserved planned HOLD branch.",
        "actual_OS_resource_creation": "NOT_RUN",
    },
    {
        "id": "C04",
        "disposition": "SOURCE_CONTROL_FIX_VERIFIED",
        "source": "selected/seal_readonly.py:23-45; selected/controller_common.py:204-208",
        "finding": "Every native invocation is checked through require_job without a case-dependent exception. Grant/spec/output root must match; HOLD requires an explicitly unavailable required resource and NULL native exit. Native success requires observed integer zero, matching owned result, closed Job lifecycle, no failure or timeout, and preserved stdout/stderr refs.",
        "actual_sealer_or_native_invocation": "NOT_RUN",
    },
    {
        "id": "C05",
        "disposition": "CONSUMER_FAIL_CLOSED_ADDED_ACTUAL_ROOT_PRODUCER_OPEN",
        "source": "selected/controller_common.py:66-155; root-authority-contract.proposed.json",
        "finding": "A proposed consumer contract checks the exact root capsule, original tool registration/audit/review, canonical tuples, whole refs, owner lease, nonce, source/scope, reviewed issuance and execution payload. Current root_binding is NULL and actual grant is false, so this candidate rejects execution. Author-written JSON cannot prove actual Root identity or supply missing real producer output.",
        "actual_root_capsule_or_CAS_producer": "OPEN",
        "fully_closed": False,
    },
    {
        "id": "C06",
        "disposition": "SOURCE_CONTROL_FIX_VERIFIED",
        "source": "selected/controller_common.py:51-56,157-202; selected/case_worker.py:14-16",
        "finding": "Seven ordered role refs, unique exact paths, reviewed current entry, interpreter/tool/helper pins and output boundary are bound to the spec. trusted_module compiles the exact verified raw bytes rather than re-reading a different file. No public production export or test assertion weakens this binding.",
        "actual_role_or_entry_execution": "NOT_RUN",
    },
]
known_open = [
    {
        "gate": "ACTUAL_ROOT_PRODUCER_AND_CURRENT_SCOPE_AUTHORITY",
        "state": "OPEN",
        "reason": "Actual independently reviewed Root capsule producer/adapter, registered original tool facts, current canonical field paths and full grant issuance proof are absent; root_binding remains NULL. Local schema and actor strings do not grant authority.",
    },
    {
        "gate": "FULL_RESOURCES_AND_EXECUTION_REVIEW",
        "state": "OPEN",
        "reason": "A future Root lease/source/scope/nonce and whole-resource capsule must be independently bound and reviewed. This preparation review is not the protocol's future READY_FOR_ROOT_W09_FINITE_ONCE decision.",
    },
    {
        "gate": "WHOLE_SOURCE_COMPOSITION",
        "state": "OPEN",
        "reason": "The separate W09 v2/v3 export and vector-prefix changes remain an independent combination gate; they were not mixed into this pinned 2098 revision candidate.",
    },
    {
        "gate": "ACTUAL_FINITE_49_AND_OS_SPLIT",
        "state": "OPEN",
        "reason": "All 49 roster cases remain NOT_RUN: 45 resource-free plus four OS-dependent cases; the expected 89 RUN/PASS events are preserved expectations, not observed passes. Job cleanup, image rejection and OS resource behavior need the authorized actual run.",
    },
    {
        "gate": "PRODUCTION_AND_CONSUMER_EVIDENCE",
        "state": "OPEN",
        "reason": "The preserved business producers/consumers remain the original limited evidence paths. Driver JSON/export and ordinary domain/adapter output do not prove whole database rowid, typeof-before-CAST, original native production, SQL24, model B0 or W09 formal acceptance.",
    },
]
review = {
    "schema": "researchos.w09.controller-revision-independent-source-review.v1",
    "reviewer": ACTOR,
    "candidate_author": handoff["author"],
    "decision": "READY_PREPARATION_ONLY",
    "writer_status": "STOPPED_AFTER_SEAL",
    "source_only": True,
    "non_author_review": True,
    "candidate_handoff_ref": candidate_handoff_ref,
    "candidate_manifest_ref": candidate_manifest_ref,
    "candidate_postseal_annex_ref": postseal_annex_ref,
    "candidate_selected_spec_ref": handoff["selected_spec_ref"],
    "candidate_selected_sources": handoff["selected_sources"],
    "original_request_review_ref": handoff["original_review_ref"],
    "authority_contract_ref": handoff["authority_contract_ref"],
    "dispositions": dispositions,
    "all_six_gaps_fully_closed": False,
    "new_source_requested_changes": [],
    "known_open": known_open,
    "candidate_preserved_known_open": handoff["known_open"],
    "static_audit_ref": audit_ref,
    "inputs_before_ref": before_ref,
    "inputs_after_ref": after_ref,
    "static_checks": audit["checks"],
    "counts": audit["counts"],
    "whole_byte_inverses": audit["whole_byte_inverses"],
    "unrequested_function_raw_byte_bodies_verified": len(audit["unrequested_functions_byte_unchanged"]),
    "AST_sources_parsed_only": len(audit["parsed_AST_sources"]),
    "changed_modules": audit["changed_modules"],
    "source_anchors": source_anchor_locations,
    "candidate_manifest_scope": audit["candidate_manifest_scope"],
    "manifest_scope_note": "All 64 declared candidate members and all 43 original members are verified. The separately pinned postseal-audit.json is an external annex, so 64 members do not imply coverage of every physical file. No member count or source was modified.",
    "tool_observations_ref": ref(BASE / "tool-observations.json"),
    "new_failure_origin_ref": origin_ref,
    "new_failed_tools": tools["new_failed_tools"],
    "original_os206_recounted": False,
    "candidate_author_original_native_exit": None,
    "actual_target_exit": None,
    "execution_counts": audit["execution_counts"],
    "source_accepted": False,
    "controller_execution_ready": False,
    "Root_actual_grant": False,
    "formal_increment": 0,
    "model_B0_increment": 0,
    "SQL24_permission": False,
    "candidate_or_shared_originals_modified": False,
    "metadata_sealer_actual_native_exit_at_write": None,
}
review_ref = write_new("review.json", review)
own_handoff = {
    "schema": "researchos.w09.controller-revision-independent-review-handoff.v1",
    "reviewer": ACTOR,
    "candidate_author": handoff["author"],
    "decision": "READY_PREPARATION_ONLY",
    "writer_status": "STOPPED_AFTER_SEAL",
    "review_ref": review_ref,
    "audit_ref": audit_ref,
    "input_before_ref": before_ref,
    "input_after_ref": after_ref,
    "original_request_review_ref": handoff["original_review_ref"],
    "candidate_handoff_ref": candidate_handoff_ref,
    "candidate_manifest_ref": candidate_manifest_ref,
    "candidate_postseal_annex_ref": postseal_annex_ref,
    "selected_spec_ref": handoff["selected_spec_ref"],
    "selected_sources": handoff["selected_sources"],
    "tool_observations_ref": ref(BASE / "tool-observations.json"),
    "new_failure_origins": [origin_ref],
    "new_failed_tools": tools["new_failed_tools"],
    "old_os206_recounted": False,
    "source_dispositions": [{"id": item["id"], "disposition": item["disposition"]} for item in dispositions],
    "known_open": known_open,
    "source_accepted": False,
    "Root_actual_grant": False,
    "formal_increment": 0,
    "model_B0_increment": 0,
    "SQL24_permission": False,
    "actual_target_native_exit": None,
    "execution_counts": audit["execution_counts"],
    "metadata_sealer_actual_native_exit_at_write": None,
    "manifest": {"schema": manifest["schema"], "path": (BASE / "manifest.json").as_posix(), "members": "Every owned receipt file including this handoff; only manifest.json excluded"},
}
own_handoff_ref = write_new("handoff.json", own_handoff)
members = [ref(path) for path in sorted(BASE.iterdir()) if path.is_file() and path.name != "manifest.json"]
own_manifest_ref = write_new("manifest.json", {"schema": manifest["schema"], "members": members, "member_count": len(members), "self_excluded": True})
print(json.dumps({"decision": "READY_PREPARATION_ONLY", "writer_status": "STOPPED_AFTER_SEAL", "review_ref": review_ref, "handoff_ref": own_handoff_ref, "manifest_ref": own_manifest_ref, "manifest_members": len(members), "audit_ref": audit_ref, "coordination_failure_origin_ref": origin_ref, "new_failed_tools": tools["new_failed_tools"], "all_six_gaps_fully_closed": False, "candidate_or_shared_originals_modified": False, "execution_counts": audit["execution_counts"]}, ensure_ascii=False, indent=2))

