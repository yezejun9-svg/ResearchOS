import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

O = Path(__file__).resolve().parent
Q = O.parent.parent / "w09_profile_registry_compat_source_codex/adfab031c6ab45ea947f1994b65b43f5"


def pin(p):
    raw = Path(p).read_bytes()
    return dict(path=str(p), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def read(p): return json.loads(Path(p).read_bytes())


def save(name, value):
    with (O / name).open("xb") as stream: stream.write((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())
    return pin(O / name)


source = read(Q / "HDF.json"); checks = read(O / "independent-source-checks.json")
for ref in read(Q / "MF.json")["members"]:
    observed = pin(ref["path"]); assert observed["sha256"] == ref["sha256"] and observed["bytes"] == ref["bytes"]
for path in O.rglob("*.py"): ast.parse(path.read_bytes())
guard = read(O / "review-source-guard.final.closed.json")
assert guard["closed"] is True and guard["retained_handles_count"] == 0 and not guard["errors"]
now = datetime.now(timezone.utc).isoformat()
decision = dict(schema="researchos.w09-profile-v5-independent-source-decision.v1", decision="ACCEPTED_SOURCE_ONLY", verdict="SOURCE_ACCEPTED_FOR_ROOT_ADOPTION_PROPOSAL", reviewed_utc=now, review_author="codex:/root/native_temp_independent_review", reviewer_role="INDEPENDENT_NON_AUTHOR", reviewer_thread_id="01a11e22-ecb2-7720-80d2-af63727d414d", root_thread_id="01a11007-5233-7ca1-b71f-9e9e5ce84c98", source_author=source["Source_author"], source_author_thread_id=None, source_author_thread_id_status="NOT_IN_SOURCE_PACKAGE_ROOT_MUST_BIND_REAL_DELIVERY", independent_non_author=True, source_hdf_ref=pin(Q / "HDF.json"), source_mf_ref=pin(Q / "MF.json"), profile_ref=source["candidate_profile_ref"], commands_proposal_ref=source["candidate_CM40_ref"], calling_contract_ref=source["calling_contract_ref"], independent_checks_ref=pin(O / "independent-source-checks.json"), source_guard_ref=pin(O / "review-source-guard.final.closed.json"), review_tool_pairs_ref=pin(O / "complete-review-tool-pairs.json"), findings=[], blockers=[],
    conclusions=[
        "Native tool refs accept precisely the existing NATIVE_PREFIX or SOURCE_PREFIX, with ordinary exact hash and Reader traversal protections preserved.",
        "Historical exception is confined to two fixed C19 invocation paths+SHA+bytes and the fixed physical CM39 archive. Current CM40 must equal the exact 32-command projection with only the intended four new routes. Other old receipt inputs still require current exact pins.",
        "Root may be actual executor and observer; independent peer Verifier must differ from all registered Source authors/executor/assembler/observer and is the sole issuer in review and issuance. Original fixed Root capture registry and peer delivery checks remain unchanged.",
        "Actual role authority requires current Canon-pinned fixed registry, typed actual origins, fixed Root-session raw audit byte ranges, and six exact Root scope/owner route leases. Synthetic Source fixtures confer none of these authorities.",
        "Full 71844-byte index and 51719-byte W04/W07 prefix are unchanged. Every profile patch reverses to exact original bytes with original CRLF/LF vectors preserved.",
        "23 independent checks and the original 46 plus new 57 finite controls passed. SourceReadGuard final closed with zero retained handles; current CP/OW were never opened or held. Historical CP370/OW174/CM39 archives supply creation baseline."
    ],
    root_continuation=["Capture this actual independent Source delivery with exact decision/HDF/MF refs and real actor/session identity.", "Issue a bounded real Root adoption Scope and current full input vector before changing Main profile or CM40; this review grants no execution.", "Issue actual role registry/audit evidence and route leases, run only newly authorized missing routes, preserve exact historical C19 receipt compatibility.", "Require independent actual mode and full W09 formal review plus actual peer plaintext delivery before any AcceptanceReceipt; Root remains observer, never self-issuer."],
    original_review_failures=[dict(ordinal=1024, full_tool_pair_ref=pin(O / "original-failure-1024.full-tool-pair.json"), first_attempt_guard_ref=pin(O / "review-source-guard.closed.json"), attribution="REVIEW_HARNESS_ONLY_NOT_SOURCE_FINDING")],
    other_nonzero_query_ref=pin(O / "query-no-match-101b99.full-tool-pair.json"), authority="NONE", execution_grant=False, actual_adoption=False, actual_role_or_formal_capture_issuance=False, actual_new_route_execution=False, programme_or_mode_qualification=False, formal_acceptance=False, parent_acceptance=False, current_C19_formal_count_delta=0, actual_Go_Native_dispatcher_model_SQLite="NOTRUN")
decision_ref = save("source-decision.json", decision)
members = [pin(p) for p in sorted(O.rglob("*")) if p.is_file() and p.name not in ("HDF.json", "MF.json")]
mf_ref = save("MF.json", dict(schema="researchos.w09-profile-v5-independent-source-manifest.v1", members=members, external_source_refs=[pin(Q / "HDF.json"), pin(Q / "MF.json")], formal_acceptance=False))
hdf_ref = save("HDF.json", dict(schema="researchos.w09-profile-v5-independent-source-handoff.v1", status="ACCEPTED_SOURCE_ONLY", decision="ACCEPTED_SOURCE_ONLY", authority="NONE", actor_id=decision["review_author"], actor_role="INDEPENDENT_NON_AUTHOR", review_author=decision["review_author"], reviewer_thread_id=decision["reviewer_thread_id"], root_thread_id=decision["root_thread_id"], source_author=source["Source_author"], source_author_thread_id=None, reviewed_utc=now, source_hdf_ref=pin(Q / "HDF.json"), source_mf_ref=pin(Q / "MF.json"), source_decision_ref=decision_ref, manifest_ref=mf_ref, profile_ref=source["candidate_profile_ref"], commands_proposal_ref=source["candidate_CM40_ref"], calling_contract_ref=source["calling_contract_ref"], independent_checks_ref=pin(O / "independent-source-checks.json"), original_review_tool_pairs_ref=pin(O / "complete-review-tool-pairs.json"), source_guard_ref=pin(O / "review-source-guard.final.closed.json"), source_guard_closed=True, retained_handles=0, independent_checks=23, finite_controls=dict(preserved=46, added=57, authority="SYNTHETIC_NONE"), original_failure_1024_ref=pin(O / "original-failure-1024.full-tool-pair.json"), historical_baseline_refs=checks["historical_baseline_refs"], current_CP_OW_opened=False, execution_grant=False, actual_adoption=False, formal_acceptance=False, parent_acceptance=False, required_next="Root must capture the actual independent Source delivery, then issue bounded adoption/role/route authority. Formal W09 requires later independent real peer delivery; no self-acceptance."))
for ref in read(O / "MF.json")["members"]: assert pin(ref["path"]) == ref
print(json.dumps(dict(HDF=hdf_ref, MF=mf_ref, decision=decision_ref, original1024=pin(O / "original-failure-1024.full-tool-pair.json"), guard_first=pin(O / "review-source-guard.closed.json"), guard_final=pin(O / "review-source-guard.final.closed.json"), member_count=len(members), decision_value="ACCEPTED_SOURCE_ONLY"), ensure_ascii=False))
