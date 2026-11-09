"""Keep the latest Root continuation and exact prior handoff bytes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os

R=Path("D:/作品集/ResearchOS/research-os")
V=R/"execution/v2.4"
W=V/"receipts/W09/W09-99"
B=V/"receipts/W05/W05-99"
N=Path(__file__).resolve().parent
def pin(p):
    p=Path(p);raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value,raw=False):
    data=value if raw else (json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode()
    with (N/name).open("xb") as f:
        f.write(data);f.flush();os.fsync(f.fileno())
    return pin(N/name)
prior_ref=pin(N/"RESUME.cp377-current-source-required.live1140.root.json")
prior=json.loads(Path(prior_ref["path"]).read_bytes())
current=[pin(V/(n+".json")) for n in ("checkpoint","path_ownership","step_state","commands")]
assert [(r["sha256"],r["bytes"]) for r in current]==[
    ("03f7fec737ca5e740762f934a9c74b3b80e987fde6c8b82e16c92bba30f74090",4804047),
    ("c55ae46b147b89bed48718dbc60c646c68a6198aac7596460bfe1d440d015698",232862),
    ("fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149",257446),
    ("12141a8ba01d34c7181ee35e054f4762732ca8627cbee87271610e65d6f28b97",67323)]
cp=json.loads(Path(current[0]["path"]).read_bytes())
assert cp["revision"]==377 and cp["work_in_progress"]["root_next_failure_ordinal_live"]==1134
scope_status=dict(
    source_nf5_hdf_ref=pin(W/"full_w09_main_native_producer_source_codex/fullw09-20261010-05/HDF.json"),
    source_registrar_nf5_hdf_ref=pin(W/"w09_nf4_root_registration_source_codex/register-20261010-02/HDF.json"),
    source_nf5_author_actual_ref=pin(N/"w09.nf5-source-author.actual-audit.root.json"),
    source_registrar_nf5_author_actual_ref=pin(N/"w09.nf5-registrar-author.actual-audit.root.json"),
    source_status="TASK100_INDEPENDENT_REVIEW_IN_PROGRESS_NO_FUTURE_SCOPE_CREATED",
    source_bridge03_hdf_ref=pin(W/"w09_formal_root_bridge_source_codex/bridge-20261010-03/HDF.json"),
    source_bridge03_actual_author_ref=pin(N/"w09.bridge03-author.actual-audit.root.json"),
    source_bridge03_status="TASK101_SOURCE_PREPARED_PENDING_NONAUTHOR_REVIEW",
    physical_C_resource_parent_ref=pin(N/"physical-C-native-v5-resource-parents.closed.root.json"),
    physical_C_resource_host_ref=pin(N/"w09.physical-C-native-v5-resource-parent.actual-audit.root.json"),
    physical_C_resource_parent="C:\\Users\\yqyyds\\.researchos\\w09-native-v5",
    future_Native_scopes_created=False,future_Native_runs=0,future_formal_consumers_run=0)
public=dict(
    caller01_source_review_hdf_ref=pin(B/"schema21_public_root_caller_independent_review_codex/review-public21-caller-20261010-01/HDF.json"),
    caller01_source_review_actual_ref=pin(N/"w09.public21-caller-independent-review.actual-audit.root.json"),
    caller01_review_verdict="SOURCE_ACCEPTED_FOR_ROOT_REGISTRATION",
    actual_directory_gate_finding="Actual Windows drive-root ancestor rejected by file-reference canonicalizer in safe_directory.",
    original1146_actual_ref=pin(N/"w09.public21-root-helper-original1146.actual-audit.root.json"),
    original1146_script_ref=pin(N/"public21_actual_resources.root.py"),
    original1146_actual_outer_exit=1,original1146_actual_python_exit=1,
    original1146_actual_Native_exit=None,original1146_actual_Go_exit=None,original1146_actual_SQL_exit=None,
    no_RuntimeScope_created=True,no_runtime_manifest_created=True,no_Native_process_started=True,
    status="DIRECTORY_GATE_FIX_AND_NONAUTHOR_REVIEW_REQUIRED_BEFORE_RUNTIME_PREPARE")
resume_ref=save("RESUME.cp377-current-source-required.live1147.root.json",dict(prior,
    schema="researchos.root-continuation.v2",issued_by="codex:/root",
    root_thread_id="01a11007-5233-7ca1-b71f-9e9e5ce84c98",created_utc=datetime.now(timezone.utc).isoformat(),
    prior_resume_ref=prior_ref,canonical_refs=current,
    canonical_checkpoint_revision=377,canonical_ownership_revision=181,
    expected_revisions=dict(checkpoint=377,path_ownership=181,step_state=None,commands=40),
    registered_through_original_ordinal=1133,next_registered_original_ordinal=1134,
    next_original_failure_ordinal=1147,pending_original_ordinals=list(range(1134,1147)),
    pending_capture_delivery_required=[],pending_source_draft="TASK103_NONROOT_DIAGNOSTIC_INPUTS_IN_PROGRESS",
    W09_current=scope_status,W05_public21_current=public,
    Goal_status="ACTIVE",active_parent_tasks=["W05","W09"],parent_tasks_required=22,
    formal_cases_required=42,formal_cases_currently_accepted=0,
    no_failure_counter_reset=True,no_historical_receipt_replay=True,
    next_actions=[
        "Close the pending diagnostics from real original hosts; Root alone issues the contiguous suffix.",
        "Register and run the independently qualified new NF5 generation once per four selectors.",
        "Independently qualify Bridge03, then execute six current CM40 consumers with physical C TEMP.",
        "Fix the public21 directory gate in a new immutable Source generation, review it, then prepare actual resources.",
        "Require true independent formal review, current Main verify_owner and state derive before acceptance."]))
handoff=V/"HANDOFF_RESUME_PACK.md"
old=handoff.read_bytes()
save("historical.HANDOFF.before-cp377.live1147.root.md",old,True)
prefix=("# Current Root continuation: CP377 / OW181 / CM40 / live next1147\n\n"
    "Registered through1133;1134..1146 preserved pending contiguous merge. Formal0/42, Goal ACTIVE. "
    "Current Main fixture adopted; old three Native scopes closed. NF5 producer/registrar Source independent review underway. "
    "Bridge03 fixes backend actor and physical C TEMP; independent review required. Public21 Caller01 Source accepted, "
    "but actual Windows drive-root directory gate failed before runtime preparation; narrow Source fix required. "
    "No future Native scope/resource qualification or bootstrap process created.\n\n"
    "Current resume: "+resume_ref["path"]+"\nSHA256 "+resume_ref["sha256"]+" bytes "+str(resume_ref["bytes"])+"\n\n").encode()
with handoff.open("wb") as f:
    f.write(prefix+old);f.flush();os.fsync(f.fileno())
assert handoff.read_bytes()==prefix+old
assert [pin(r["path"]) for r in current]==current
print(json.dumps(dict(resume_ref=resume_ref,canonical_unchanged=True,live_next=1147,
                     formal_acceptance=False),ensure_ascii=False))
