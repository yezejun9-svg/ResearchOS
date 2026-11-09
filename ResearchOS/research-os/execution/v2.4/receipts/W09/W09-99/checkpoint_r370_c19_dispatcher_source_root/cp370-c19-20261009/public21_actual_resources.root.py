"""Root publication of completed observations; imports the reviewed caller gates."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, sys, types, uuid

R=Path("D:/作品集/ResearchOS/research-os")
V=R/"execution/v2.4"
B=V/"receipts/W05/W05-99"
S=V/"receipts/W09/W09-99/checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009"
O=S/"public21-current-resource-root-20261010-01"
PC=B/"schema21_public_root_caller_source_codex/s21public-caller-20261010-01"
PCR=B/"schema21_public_root_caller_independent_review_codex/review-public21-caller-20261010-01"
ROOT="codex:/root"
THREAD="01a11007-5233-7ca1-b71f-9e9e5ce84c98"
CALLER=PC/"public21_root.source.py"
raw=CALLER.read_bytes()
# The explicit pin below is the accepted Source ref, with no generated alias.
assert len(raw)==55236 and hashlib.sha256(raw).hexdigest()=="010b3907632f6e065b9765b880fd57287950e5464d6410415484f8121111bd63"
api=types.ModuleType("root_public21_reviewed_caller")
api.__file__=str(CALLER)
exec(compile(raw,api.__file__,"exec"),api.__dict__)
base=api.base()

def now(): return datetime.now(timezone.utc).isoformat()
def pin(p): return api.pin(p)
def doc(p): return api.doc(pin(p))
def save(name,value): return api.save(O/name,value)
def refs_caller_review():
    return {k:pin(PCR/n) for k,n in (("hdf","HDF.json"),("mf","MF.json"),("decision","source-decision.json"))}
def common():
    refs=refs_caller_review()
    return dict(source_hdf_ref=pin(PC/"HDF.json"),source_mf_ref=pin(PC/"MF.json"),
        review_hdf_ref=refs["hdf"],review_mf_ref=refs["mf"],review_decision_ref=refs["decision"],
        review_hostpair_witness_ref=pin(O/"SOURCE_REVIEW_WITNESS.witness.root.json"),
        runner_source_refs=api.LEAF_REFS,runner_review_refs=api.RUNNER_ACCEPTED_REVIEW_REFS,
        runner_review_witness_ref=pin(O/"RUNNER_SOURCE_REVIEW_WITNESS.witness.root.json"))

def peer_wrap(generic,actor,operation,refs):
    old=doc(generic)
    assert old["actor_id"]==actor and old["Root_thread_id"]==THREAD
    raw=api.checked(old["original_capture_ref"])
    lines=raw.splitlines(keepends=True)
    rows=[base.strict(x) for x in lines]
    value=dict(schema="researchos.root-actual-peer-capture-binding.v2",issued_by=ROOT,
        root_thread_id=THREAD,source_audit_path=base.ROOT_AUDIT_LOG,
        source_line_offsets=old["source_line_offsets"],source_prefix_size_observed=old["source_prefix_size_observed"],
        original_line_sha256=old["original_line_sha256"],source_line_bytes=[len(x) for x in lines],
        original_capture_ref=old["original_capture_ref"],peer_actor=actor,
        message_id=rows[-1]["payload"]["id"],received_at=rows[-1]["timestamp"])
    ref=save(operation+".peer-binding.root.json",value)
    api.validate_peer_delivery(ref,list(refs.values()),actor,operation)
    return ref

def initialise():
    assert not O.exists()
    api.safe_directory(O,new=True)
    O.mkdir()
    cr=refs_caller_review()
    entries=[
        ("SOURCE_REVIEW_WITNESS",S/"w09.public21-caller-independent-review.actual-audit.root.json",
         "codex:/root/full_w09_source_review",cr),
        ("RUNNER_SOURCE_REVIEW_WITNESS",S/"w09.public21-source-review-v2.actual-audit.root.json",
         "codex:/root/attach_restore_independent_review",api.RUNNER_ACCEPTED_REVIEW_REFS)]
    result=[]
    for op,generic,actor,refs in entries:
        peer=peer_wrap(generic,actor,op,refs)
        request=dict(operation=op,observed_refs=list(refs.values()),peer_actor=actor,
                     peer_delivery_binding_ref=peer)
        result.append(save(op+".observation-request.root.json",request))
    print(json.dumps(dict(request_refs=result,formal_acceptance=False,execution_grant=False),ensure_ascii=False))

def observe(operation):
    q=doc(O/(operation+".observation-request.root.json"))
    assert q["operation"]==operation and operation in api.CAPTURE_OPS
    refs=q["observed_refs"]
    held=base.guard_primitives().SourceReadGuard(per_file_cap=512*1024*1024,total_cap=2*1024*1024*1024)
    try:
        held.acquire(refs)
        if q["peer_actor"] is not None:
            api.validate_peer_delivery(q["peer_delivery_binding_ref"],refs,q["peer_actor"],operation)
        value=dict(schema="researchos.root-public21-capture-result.v1",issued_by=ROOT,
            observer_actor=ROOT,root_thread_id=THREAD,operation=operation,source="tools.exec_command",
            observed_refs=refs,peer_actor=q["peer_actor"],formal_acceptance=False,
            observation_request_ref=pin(O/(operation+".observation-request.root.json")),observed_utc=now())
    finally:
        closure=held.close()
        save(operation+".observation.guard.closed.root.json",closure)
        assert closure.get("closed") is True and closure.get("retained_handles_count")==0 and not closure.get("errors")
    result_ref=save(operation+".typed-observation.root.json",value)
    print(json.dumps(dict(value,typed_observation_ref=result_ref),ensure_ascii=False))

def bind_root(operation,generic_path):
    old=doc(generic_path)
    assert old["actor_id"]==ROOT and old["Root_thread_id"]==THREAD
    raw=api.checked(old["original_capture_ref"])
    lines=raw.splitlines(keepends=True)
    rows=[base.strict(x) for x in lines]
    q=doc(O/(operation+".observation-request.root.json"))
    value=dict(schema="researchos.root-actual-tool-capture-binding.v1",issued_by=ROOT,root_thread_id=THREAD,
        scope_key=api.SCOPE_KEY,operation=operation,source_audit_path=base.ROOT_AUDIT_LOG,
        source_line_offsets=old["source_line_offsets"],source_prefix_size_observed=old["source_prefix_size_observed"],
        original_line_sha256=old["original_line_sha256"],source_line_bytes=[len(x) for x in lines],
        original_capture_ref=old["original_capture_ref"],original_call_id=rows[1]["payload"]["call_id"],
        tool_call_timestamp=rows[1]["timestamp"],tool_result_timestamp=rows[2]["timestamp"])
    if q["peer_actor"] is not None: value["peer_delivery_binding_ref"]=q["peer_delivery_binding_ref"]
    api.validate_root_capture(value,raw,q["observed_refs"],operation,q["peer_actor"])
    capture=save(operation+".actual-root-binding.root.json",value)
    if operation=="SOURCE_REVIEW_WITNESS":
        refs=refs_caller_review()
        witness=dict(schema="researchos.root-public21-external-review-witness.v1",issued_by=ROOT,
            root_thread_id=THREAD,created_utc=now(),capture_binding_ref=capture,
            review_hdf_ref=refs["hdf"],review_mf_ref=refs["mf"],review_decision_ref=refs["decision"])
        save(operation+".witness.root.json",witness)
    elif operation=="RUNNER_SOURCE_REVIEW_WITNESS":
        witness=dict(schema="researchos.root-public21-runner-review-witness.v1",issued_by=ROOT,
            root_thread_id=THREAD,created_utc=now(),capture_binding_ref=capture,
            review_author=q["peer_actor"],review_refs=q["observed_refs"])
        save(operation+".witness.root.json",witness)
    print(json.dumps(dict(capture_binding_ref=capture,formal_acceptance=False,execution_grant=False),ensure_ascii=False))

def resource_scope():
    q=common()
    # Actual, previously completed review/capture gates; no future witness.
    api.own_review(q)
    api.runner_chain(q)
    api.programme_chain()
    start=datetime.now(timezone.utc)
    scope=dict(schema="researchos.root-public21-runtime-qualification-scope.v1",issued_by=ROOT,
        root_thread_id=THREAD,slice_id="PUBLIC21_RUNTIME_RESOURCE_QUALIFICATION",
        formal_acceptance=False,execution_grant=False,source_hdf_ref=q["source_hdf_ref"],
        source_mf_ref=q["source_mf_ref"],caller_ref=pin(CALLER),runner_contract_ref=api.LEAF_REFS["contract_ref"],
        created_utc=start.isoformat(),lease_expires_at=(start+timedelta(seconds=1800)).isoformat())
    sr=save("qualification-scope.root.json",scope)
    current=[pin(p) for p in base.CANON]
    rev=dict(zip(("checkpoint","path_ownership","step_state","commands"),[api.doc(r).get("revision") for r in current]))
    api.current_four(current,rev)
    req=dict(operation="RUNTIME_MANIFEST_PREREQUISITES",
        observed_refs=[sr,q["source_hdf_ref"],q["source_mf_ref"],*q["runner_review_refs"].values(),*current],
        peer_actor=None)
    save("RUNTIME_MANIFEST_PREREQUISITES.observation-request.root.json",req)
    save("resource-prepare.partial.root.json",dict(q,qualification_scope_ref=sr,before_canonical_refs=current,
        expected_revisions=rev,output_root=str(B/"integration_codex"/("public21-runtime-"+uuid.uuid4().hex))))
    print(json.dumps(dict(qualification_scope_ref=sr,current_refs=current,expected_revisions=rev,
                         formal_acceptance=False,execution_grant=False),ensure_ascii=False))

def prepare_request():
    q=doc(O/"resource-prepare.partial.root.json")
    q.update(schema="researchos.root-public21-runtime-prepare-request.v1",issued_by=ROOT,root_thread_id=THREAD,
        execution_grant=False,preparation_host_binding_ref=pin(O/"RUNTIME_MANIFEST_PREREQUISITES.actual-root-binding.root.json"))
    ref=save("runtime-prepare.request.root.json",q)
    print(json.dumps(dict(request_ref=ref),ensure_ascii=False))

mode=sys.argv[1]
if mode=="initialise": initialise()
elif mode=="observe": observe(sys.argv[2])
elif mode=="bind": bind_root(sys.argv[2],Path(sys.argv[3]))
elif mode=="scope": resource_scope()
elif mode=="prepare-request": prepare_request()
else: raise ValueError("ROOT_HELPER_MODE")
