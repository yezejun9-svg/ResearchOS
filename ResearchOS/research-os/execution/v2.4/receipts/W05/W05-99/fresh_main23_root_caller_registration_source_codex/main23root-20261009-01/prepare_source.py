"""Author-only Source contract writer; never calls proposed registration/runtime."""
import json
from pathlib import Path
import types

N = Path(__file__).resolve().parent
leaf = N / "main23_root.source.py"
m = types.ModuleType("main23_source_prepare"); m.__file__ = str(leaf)
exec(compile(leaf.read_bytes(), str(leaf), "exec"), m.__dict__)
b = m.builder_chain()
refs = list(m.BUILDER_REVIEW_REFS.values()) + [b["decision"]["author_hdf_ref"], b["decision"]["author_mf_ref"], b["source"]["builder_ref"], b["source"]["contract_ref"], b["source"]["input_manifest_ref"], m.GUARD_REF, m.TP_REF]
refs += [b["contract"][k] for k in ("base_helper_ref", "source_guard_ref", "owned_job_ref", "toolchain_lock_ref", "go_ref")]
inputs = m.save(N / "source-inputs.json", dict(schema="researchos.main23-root-source-inputs.v1", references=m.local_refs(refs), current_canon_refs_are_not_runtime_inputs=True, builder_expands_original_manifest_at_runtime=True, source_author=m.AUTHOR))
contract = dict(
    schema="researchos.main23-root-calling-contract.v1",
    status="SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_BINDING",
    source_author=m.AUTHOR, caller_ref=m.pin(leaf), registrar_ref=m.pin(leaf), source_inputs_ref=inputs,
    slice_id=m.SLICE, registered_state=m.STATE, independent_of_public_end22_lease=True,
    builder_entry=b["contract"]["entry"], builder_contract_ref=b["source"]["contract_ref"], builder_review_refs=m.BUILDER_REVIEW_REFS,
    phases=list(m.PHASES), Go_processes_maximum=5,
    entries={"propose": "propose(root_registration_request_ref) -> facts_ref; writes new registration receipt namespace only",
             "check": "register('check', facts_ref) -> check.result ref; no Canon write",
             "activate": "register('activate', facts_ref, fresh_root_activation_ref) -> activation.result ref; mandatory TP exclusive pair only",
             "execute": "execute(root_actual_request_ref) -> complete returned state; pinned accepted leaf only"},
    launcher="Locked Python -B main23_root.source.py MODE INPUT_PATH INPUT_SHA INPUT_BYTES [ACTIVATION_PATH ACTIVATION_SHA ACTIVATION_BYTES]; Root must capture complete external wrapper/tool request and raw response",
    future_bindings=dict(before_canonical_refs=None, expected_revisions=None, public371_registration_ref=None, review_hdf_ref=None, review_mf_ref=None, review_decision_ref=None, review_hostpair_witness_ref=None, runtime_qualification_ref=None, actual_registration_ref=None, current_canonical_refs=None),
    future_binding_policy="All null fields must be supplied as actual Root evidence after independent Source review. Current observed Canon is 370/174/39. Never invent CP371 refs. Registration requires current >=371/175 plus committed actual public371 lineage; increments exact current CP/OW by 1. Expected 372/176 only if before really 371/175.",
    registration_request=dict(schema="researchos.root-main23-registration-request.v1", required_fields=["issued_by=codex:/root", "formal_acceptance=false", "before_canonical_refs (ordered checkpoint,path_ownership,step_state,commands exact three-key refs)", "expected_revisions (four keys; absent step_state revision uses null)", "public371_registration_ref", "source_hdf_ref", "source_mf_ref", "review_hdf_ref", "review_mf_ref", "review_decision_ref", "review_hostpair_witness_ref", "root_resume_ref", "postreview_live_ref", "created_utc", "lease_expires_at", "case_request_ref", "caller_receipt_root", "registration_root", "pending_ref", "runtime_qualification_ref"]),
    root_resume_fields=["issued_by=codex:/root", "canonical_refs", "expected_revisions"],
    postreview_live_fields=["issued_by=codex:/root", "canonical_refs", "expected_revisions", "root_resume_ref", "review_decision_ref", "created_utc after Source review", "capture_binding_ref to actual external Root full4 read after review"],
    source_review_decision=dict(verdict="SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION", review_author="independent actor, not Root or Source author", source_author=m.AUTHOR, independent_non_author=True, formal_acceptance=False, execution_grant=False, exact_refs=["source_hdf_ref", "source_mf_ref", "caller_ref", "registrar_ref", "calling_contract_ref"]),
    source_review_hdf_fields=["review_author", "source_author", "manifest_ref", "source_decision_ref", "source_hdf_ref", "source_mf_ref", "reviewed_utc"],
    external_review_witness=dict(schema="researchos.root-main23-external-review-witness.v1", fields=["issued_by=codex:/root", "review_hdf_ref", "review_mf_ref", "review_decision_ref", "capture_binding_ref", "created_utc"]),
    capture_binding=dict(schema="researchos.root-actual-tool-capture-binding.v1", root_thread_id=m.ROOT_THREAD, fields=["issued_by=codex:/root", "original_capture_ref", "original_call_id", "original_line_sha256", "source_line_bytes", "tool_call_timestamp", "tool_result_timestamp"], rule="Validate raw JSONL session_meta and matching complete real call/output pair. Returned output binds exact expected SHA refs. Preserve raw integer FILETIME; do not roundtrip through IEEE-754 tools."),
    runtime_qualification=dict(schema="researchos.root-main23-qualified-runtime.v1", fields=["issued_by=codex:/root", "status=QUALIFIED_FOR_MAIN23_BUILD", "review_author (non-author, non-Root)", "independent_non_author=true", "formal_programme_qualification=false", "python_ref", "go_ref", "review_decision_ref", "resource_refs"], decision_fields=["verdict=RUNTIME_CLOSURE_ACCEPTED", "review_author", "independent_non_author=true", "resource_refs exactly equal qualification.resource_refs"], rule="Root supplies independently qualified Python/loaded-native/Go native dependency closure. Caller checks locked Python and Go, all presently loaded Python/native resources and own caller/TP/guard are inside qualified exact refs, then holds resources throughout leaf and cleanup. This Source does not produce runtime qualification."),
    activation_fields=["issued_by=codex:/root", "facts_ref", "before_canonical_refs", "created_utc after registration request", "capture_binding_ref to external Root read of facts+full4 after request"],
    actual_request=dict(schema="researchos.root-main23-actual-request.v1", fields=["issued_by=codex:/root", "formal_acceptance=false", "scope_ref", "facts_ref", "case_request_ref", "current_canonical_refs", "registration_result_ref", "host_call_intent_ref", "runtime_qualification_ref"]),
    host_call_intent_fields=["issued_by=codex:/root", "kind=ACTUAL_HOST_CALL_INTENT", "external_hostpair_required=true", "scope_ref", "case_request_ref"],
    new_roots={"output_root": "integration_codex/fresh-main23-<32lowerhex>", "caller_receipt_root": "integration_codex/fresh-main23-caller-<same case>", "registration_root": "integration_codex/fresh-main23-registration-<same case>"},
    acyclic_order=["Root request (no future scope/owner/worker refs)", "scope -> request", "owner -> scope", "worker -> owner+scope", "facts -> request+scope+owner+worker+full4 before raw archives", "Canon -> facts+scope+owner+worker", "actual Root request -> activation result+current4"],
    inverse="Pure transform verifies full before CP/OW inverse, original raw full4 archived; SS/CM held unchanged. TP callback does no file operations. SourceReadGuard excludes exclusive CP/OW before TP. Failed TP retains original partial journal; Root reconciliation only, no automatic inverse.",
    pending_policy="Root pending increment starts at current checkpoint.work_in_progress.root_next_failure_ordinal_live; contiguous unique invocation identities only. Existing counters stay byte-semantically unchanged. Missing process exit remains null, no retries/counter resets.",
    failure_policy="Persist exact builder returned state outside build root, including unpublished build.closed.json cases. If own persistence fails return entire record for external Root capture and persistence; Root assigns original ordinal. No self-synthesized external receipt or programme qualification.",
    public22="Separate slice remains end22 only", schema21="OPEN", full20to24="OPEN", main23to24="BLOCKED_MAIN_NOT_ADOPTED", qualification_ref=None, formal_acceptance=False, parent_acceptance=False)
contract_ref = m.save(N / "root-calling-contract.source.json", contract)
control = m.doc(m.pin(N / "source-controls.final.json"))
m.save(N / "source-facts.json", dict(schema="researchos.main23-root-source-facts.v1", source_author=m.AUTHOR, canonical_observed=control["canonical_after"], canonical_revisions=control["current_revisions"], source_controls_ref=m.pin(N / "source-controls.final.json"), original_failures=[1016, 1019], root_reported_next_original_failure_ordinal=1020, original_1019_pair_ref=m.pin(N / "original-pending-1019.full-tool-pair.json"), external_1019_root_capture_pending=True, actual_registration=False, actual_runtime_executed=False, future_canonical_refs=None, schema21="OPEN", full20to24="OPEN", main23to24="BLOCKED_MAIN_NOT_ADOPTED", formal_acceptance=False))
print(json.dumps({"contract_ref": contract_ref, "source_inputs_ref": inputs}, ensure_ascii=False))
