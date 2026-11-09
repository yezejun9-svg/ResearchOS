"""Source-only metadata seal; no harness or controller imports/execution."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
REL="candidate-root/internal/domain/native_migration_authority_harness_windows_test.go"
def ref(p):
    b=p.read_bytes()
    return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def new(name,value):
    with (P/name).open("x",encoding="utf-8",newline="\n") as f:
        json.dump(value,f,ensure_ascii=True,indent=2);f.write("\n")
inputs=json.loads((P/"public-input-pins.json").read_bytes())["inputs"]
for pin in inputs:
    actual=ref(Path(pin["path"]))
    assert actual["sha256"]==pin["sha256"] and actual["bytes"]==pin["bytes"]
static=json.loads((P/"static-evidence.json").read_bytes())
candidate=P/REL
assert ref(candidate)==static["candidate_ref"]
inverse=candidate.read_bytes()
for change in reversed(json.loads((P/"ttl-replacements.json").read_bytes())):
    new_bytes,old_bytes=change["after"].encode(),change["before"].encode()
    assert inverse.count(new_bytes)==1
    inverse=inverse.replace(new_bytes,old_bytes)
assert inverse==Path(static["baseline_ref"]["path"]).read_bytes()
diagnostic=json.loads((P/"diagnostic-822.json").read_bytes())
assert diagnostic["ordinal"]==822
assert all(diagnostic[k] is None for k in ("actualOuter","actualPython","native"))
assert diagnostic["exec_command_started"] is False
members={p.relative_to(P).as_posix():ref(p) for p in sorted(P.rglob("*")) if p.is_file()}
assert "HDF.json" not in members and "MF.json" not in members
new("MF.json",{"schema":"researchos.native-harness-ttl-revision-manifest.v1","members":members})
hdf={
 "schema":"researchos.native-harness-ttl-revision-handoff.v1",
 "status":"SOURCE_IMPLEMENTED_PENDING_ROOT_INDEPENDENT_REVIEW_AND_FRESH_T7_BUILD",
 "sourceStatus":"EXECUTION_REPORTED","formal":False,"production_ready":False,"execution_authority":False,
 "actor_id":"codex:/root/command_queue_impl","source_root":str(P),
 "source_ref":ref(candidate),"actual_formatted_T5_baseline_ref":static["baseline_ref"],
 "manifest_ref":ref(P/"MF.json"),"manifest_member_count":len(members),
 "contract_ref":ref(P/"CONTRACT.md"),"minimal_diff_ref":ref(P/"credential-ttl.patch"),
 "static_evidence_ref":ref(P/"static-evidence.json"),
 "public_input_pins_ref":ref(P/"public-input-pins.json"),
 "original_tool_io_ref":ref(P/"original-tool-io.json"),
 "diagnostic822_ref":ref(P/"diagnostic-822.json"),
 "mechanical_failures":[{"ordinal":822,"layer":"functions.exec store before child tool dispatch",
                        "actualOuter":None,"actualPython":None,"native":None,"exec_command_started":False}],
 "repair":{"changed_file_count":1,"changed_expression_count":2,
           "from":"time.Hour","to":"15*time.Minute",
           "lines":[466,470],"production_TTL_changed":False,
           "credentials_reissued_or_refreshed":False},
 "static_validation":{"two_replacement_inverse_matches_entire_T5_raw_bytes":True,
     "all_other_assertions_scenarios_authority_Owner_nonce_payload_Job_cleanup_bytes_preserved":True,
     "actual_T5_compiler_inventory_source_pin_verified":True,
     "public_input_pin_count_reverified":len(inputs),
     "actual_test_or_Go_build_run":False},
 "original_failure820":{"preserved":True,"rerun":False,"actual_go_exit":1,
     "pid":53352,"creation_FILETIME_100ns":134359747687806045,
     "error":"INVALID_REQUEST: credential TTL must be at most 15 minutes",
     "original_error_line":468,"source_author_revalidated_closed_job_from_public_invocation":True,
     "source_author_read_retained_DB":False},
 "timing_contract":"All operations requiring initial Owner/executor credentials, including native invocation and replay, must finish before initial 15-minute credential expiry; controller hold does not extend validity; original four-minute grant interval remains.",
 "source_author_actions":{"Go_gofmt_native_SQL_private_signing_model":False,
                         "Main_canonical_T5_previous_Source_writes":False,
                         "controller_or_harness_execution":False,"provider_requests":0},
 "root_required_next":["independent minimal Source review","fresh isolated T7 composition and actual compiler/build receipts",
                       "fresh isolated case/config with original expiry and concrete approval boundaries",
                       "actual native execution and independent acceptance"],
 "native_acceptance":"PENDING_ROOT"
}
new("HDF.json",hdf)
for name,pin in members.items():assert ref(P/name)==pin
print(json.dumps({"HDF":ref(P/"HDF.json"),"MF":ref(P/"MF.json"),"candidate":ref(candidate),
 "diagnostic822":ref(P/"diagnostic-822.json"),"members":len(members),
 "input_pins":len(inputs),"inverse_raw_equal":True},ensure_ascii=True))

