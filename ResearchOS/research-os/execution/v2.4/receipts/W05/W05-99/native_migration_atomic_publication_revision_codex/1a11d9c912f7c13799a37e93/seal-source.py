"""Seal source-only atomic JSON revision; never import controller/helper."""
import ast, hashlib, json
from pathlib import Path
P=Path(__file__).resolve().parent
OLD=P.parent.parent/"native_migration_root_controller_source_codex/949c31b5ce9172756b85a2aa388"
def ref(p):
    b=p.read_bytes()
    return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def new(name,value):
    with (P/name).open("x",encoding="utf-8",newline="\n") as f:
        json.dump(value,f,ensure_ascii=True,indent=2)
        f.write("\n")
controller=P/"root_native_migration_controller.py"
observer=P/"windows_owned_observed.py"
code=controller.read_bytes().decode("utf-8")
ast.parse(code,filename=str(controller))
ast.parse(observer.read_bytes().decode("utf-8"),filename=str(observer))
assert observer.read_bytes()==(OLD/observer.name).read_bytes()
assert (P/"root-controller-api.json").read_bytes()==(OLD/"root-controller-api.json").read_bytes()
inverse=code
for change in reversed(json.loads((P/"controller-inverse-changes.json").read_bytes())):
    assert inverse.count(change["after"])==1
    inverse=inverse.replace(change["after"],change["before"])
assert inverse.encode("utf-8")==(OLD/controller.name).read_bytes()
inputs=json.loads((P/"public-input-pins.json").read_bytes())
for pin in inputs["inputs"]+[inputs["go_producer_reference"]]:
    actual=ref(Path(pin["path"]))
    assert actual["sha256"]==pin["sha256"] and actual["bytes"]==pin["bytes"]
oldmf=json.loads((OLD/"MF.json").read_bytes())
for name,pin in oldmf["members"].items():
    actual=ref(OLD/name)
    assert actual["sha256"]==pin["sha256"] and actual["bytes"]==pin["bytes"]
io=json.loads((P/"original-tool-io.json").read_bytes())
assert io["failed_construct"]["output"]["exit_code"]==1
assert io["successful_construct"]["output"]["exit_code"]==0
failure={
    "schema":"researchos.actual-mechanical-failure-origin.v1",
    "ordinal":813,
    "assignment":"Root assigned 813 to chunk 020cc5",
    "actualOuter":1,"actualPython":1,"native":None,
    "failed_construct_script_ref":ref(P/"construct-revision.py"),
    "actual_input":io["failed_construct"]["input"],
    "actual_output":io["failed_construct"]["output"],
    "failed_before_controller_output_write":True,
    "failure":"AssertionError in inverse raw-byte verification due to incorrect CRLF restoration",
    "actual_original_newline_probe":io["newline_probe"],
    "original_source_LF_count":699,"original_source_CRLF_count":0,
    "corrected_script_ref":ref(P/"construct-revision-v2.py"),
    "actual_corrected_input":io["successful_construct"]["input"],
    "actual_corrected_output":io["successful_construct"]["output"],
    "failed_original_and_corrected_scripts_separately_preserved":True,
    "no_old_source_or_binary_mutation":True,
    "controller_import_or_execution":False
}
new("failure-origin.813.json",failure)
members={p.relative_to(P).as_posix():ref(p) for p in sorted(P.rglob("*")) if p.is_file()}
assert "HDF.json" not in members and "MF.json" not in members
new("MF.json",{"schema":"researchos.native-controller-atomic-source-manifest.v1","members":members})
hdf={
    "schema":"researchos.native-controller-atomic-source-handoff.v1",
    "status":"SOURCE_IMPLEMENTED_PENDING_ROOT_INDEPENDENT_REVIEW_AND_ACTUAL_EXECUTION",
    "sourceStatus":"EXECUTION_REPORTED","formal":False,"production_ready":False,"execution_authority":False,
    "actor_id":"codex:/root/command_queue_impl",
    "source_root":str(P),"prior_handoff_ref":ref(OLD/"HDF.json"),
    "prior_manifest_ref":ref(OLD/"MF.json"),
    "source_refs":{controller.name:ref(controller),observer.name:ref(observer)},
    "manifest_ref":ref(P/"MF.json"),"manifest_member_count":len(members),
    "contract_ref":ref(P/"CONTRACT.md"),"api_ref":ref(P/"root-controller-api.json"),
    "diff_ref":ref(P/"controller-atomic-publication.patch"),
    "inverse_changes_ref":ref(P/"controller-inverse-changes.json"),
    "static_evidence_ref":ref(P/"static-evidence.json"),
    "public_input_pins_ref":ref(P/"public-input-pins.json"),
    "original_tool_io_ref":ref(P/"original-tool-io.json"),
    "failure813_origin_ref":ref(P/"failure-origin.813.json"),
    "mechanical_failures":[{"ordinal":813,"chunk_id":"020cc5","actualOuter":1,"actualPython":1,"native":None}],
    "failure813_corrected_construct":{"chunk_id":"0925a7","actualOuter":0,"actualPython":0,"native":None},
    "prior_failure805":"Remains independently preserved in prior 949c handoff; not repeated or renumbered.",
    "scope":{
        "only_controller_publication_consumption_and_source_contract_metadata":True,
        "prior_949c_e57c_T5_immutable":True,
        "observer_raw_byte_identical":True,"public_API_file_raw_byte_identical":True,
        "old_Source_inverse_raw_byte_identical":True,
        "changed_existing_functions":["write_new","_phase","serve","poll","snapshot","_approval"],
        "new_source_helpers":["PublicationPending","_complete_public_json"],
        "existing_context_pin_sign_publish_release_implementations_AST_unchanged":True
    },
    "implementation":{
        "publication":"Windows-only same-directory unique O_EXCL temporary, full write/flush/fsync/close, os.rename no-clobber",
        "temporary_cleanup":"only own successfully-created closed temporary; original error preserved; cleanup failure chained",
        "consumption":"complete unpinned JSON parsed and pinned from same buffer; pending reads defer with no approval or cancellation",
        "public_requests":"only complete exact Action/config/nonce requests become seen or queued",
        "Go_producer":"unchanged O_EXCL Write/Sync/Close; syntax completion alone does not assert producer Sync/Close success",
        "all_existing_pinned_hash_and_approval_boundaries_preserved":True
    },
    "verification":{
        "AST_only_no_module_import":True,
        "controller_inverse_raw_equal":True,
        "observer_raw_equal":True,"api_raw_equal":True,
        "old_manifest_members_reverified":len(oldmf["members"]),
        "direct_public_input_pins_reverified":len(inputs["inputs"])+1,
        "historical_20_external_pins_reexecuted":False,
        "actual_atomic_concurrency_tests_run":False,
        "actual_observe_cancel_timeout_tests_run":False
    },
    "source_author_actions":{
        "Go_gofmt_native_SQL_private_signing_model":False,
        "Main_canonical_e57_T5_writes":False,
        "provider_requests":0,
        "controller_or_observer_import":False
    },
    "root_required_next":[
        "independent Source review of no-clobber publication, pending JSON reads and cleanup",
        "actual isolated public atomic publication and observe/cancel/timeout checks",
        "retain original Root concrete approvals, expiry and private boundaries before any native migration authority case"
    ],
    "native_acceptance":"PENDING_ROOT","automatic_approval":False,"automatic_signing":False
}
new("HDF.json",hdf)
for name,pin in members.items(): assert ref(P/name)==pin
print(json.dumps({"HDF":ref(P/"HDF.json"),"MF":ref(P/"MF.json"),
    "source_refs":hdf["source_refs"],"members":len(members),
    "failure813":ref(P/"failure-origin.813.json"),"old_members_reverified":len(oldmf["members"]),
    "direct_input_pins":len(inputs["inputs"])+1,"AST_only":True},ensure_ascii=True))

