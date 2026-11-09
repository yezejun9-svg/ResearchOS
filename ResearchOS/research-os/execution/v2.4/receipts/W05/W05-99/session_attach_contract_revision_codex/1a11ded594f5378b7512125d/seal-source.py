"""Seal bounded attach Source; no Go import, build, native process, or database action."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
def ref(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def new(n,v):
 with (P/n).open("x",encoding="utf-8",newline="\n") as f:json.dump(v,f,ensure_ascii=True,indent=2);f.write("\n")
def delimiters(text):
 stack=[];i=0;pair={")":"(","]":"[","}":"{"}
 while i<len(text):
  if text.startswith("//",i):
   end=text.find("\n",i);i=len(text) if end<0 else end+1;continue
  if text.startswith("/*",i):
   end=text.find("*/",i+2);assert end>=0;i=end+2;continue
  c=text[i]
  if c in ('"', "'",chr(96)):
   quote=c;i+=1
   while i<len(text):
    if text[i]==quote:i+=1;break
    if quote!=chr(96) and text[i]=="\\":i+=2
    else:i+=1
   else:raise AssertionError("unterminated Go literal")
   continue
  if c in "([{":stack.append(c)
  elif c in ")]}":assert stack and stack.pop()==pair[c]
  i+=1
 assert not stack
files=[P/"candidate-root/internal/domain/client_protocol.go",P/"candidate-root/internal/domain/client_protocol_attach_contract_windows_test.go"]
for p in files:delimiters(p.read_text(encoding="utf-8"))
e=json.loads((P/"static-evidence.json").read_bytes())
base=Path(e["production_baseline_ref"]["path"])
assert ref(base)==e["production_baseline_ref"]
assert ref(files[0])==e["production_candidate_ref"]
code=files[0].read_text(encoding="utf-8")
inverse=code
for c in reversed(json.loads((P/"production-replacements.json").read_bytes())):
 at=c["position"];assert inverse[at:at+len(c["after"])]==c["after"]
 inverse=inverse[:at]+c["before"]+inverse[at+len(c["after"]):]
assert inverse.encode()==base.read_bytes()
inputs=json.loads((P/"public-input-pins.json").read_bytes())["inputs"]
for pin in inputs:
 actual=ref(Path(pin["path"]));assert actual["sha256"]==pin["sha256"] and actual["bytes"]==pin["bytes"]
q4=P.parent.parent/"typed_runtime_goal_fixture_attach_revision_codex/7d0b8a53d3d24e629a085fccb30b7d1e"
assert ref(q4/"HDF.json")["sha256"]=="3eaeaf6219589c36b13fa730e3e4cfb0a42b2bba016bb6cf6f5b6eafc9be44c0"
assert ref(q4/"MF.json")["sha256"]=="dd7615e9b9f5f2584089c07180d7f0da00a3c787e5450565b345e56ed7e66707"
test=files[1].read_text(encoding="utf-8")
tests=[line.split("(")[0].split()[-1] for line in test.splitlines() if line.startswith("func Test")]
assert len(tests)==5
assert all(s in test for s in ("expired-same-owner","other-client","unowned","CANCELLED","FAILED","COMPLETED","ErrIdemConflict","foreign-profile"))
new("final-static-checks.json",{"schema":"researchos.attach-final-static.v1",
 "Go_lexical_delimiters_only":True,"not_Go_parser_or_build":True,"production_inverse_raw_byte_equal":True,
 "direct_input_pins_reverified":len(inputs),"test_source_functions":tests,
 "runtime_binding_regression_functions":["TestHandlerRuntimeStoredProfileExactMapping","TestHandlerRuntimeTaskNeedsExactSession"],
 "tests_executed":False,"q4_block_handoff_ref":ref(q4/"HDF.json"),"q4_block_manifest_ref":ref(q4/"MF.json"),
 "known_legacy_ACK_expectation":"TestClientSameWriterRenewsExpiredLease; unchanged in T6",
 "mechanical_failures":[827]})
members={p.relative_to(P).as_posix():ref(p) for p in sorted(P.rglob("*")) if p.is_file()}
assert "HDF.json" not in members and "MF.json" not in members
new("MF.json",{"schema":"researchos.session-attach-repair-source-manifest.v1","members":members})
new("HDF.json",{
 "schema":"researchos.session-attach-repair-source-handoff.v1",
 "status":"BOUNDED_COMPONENT_SOURCE_PENDING_INDEPENDENT_REVIEW_BUILD_AND_TEST",
 "sourceStatus":"EXECUTION_REPORTED","formal":False,"production_ready":False,"execution_authority":False,
 "actor_id":"codex:/root/command_queue_impl","source_root":str(P),
 "source_refs":{p.name:ref(p) for p in files},"actual_T6_base_ref":ref(base),
 "manifest_ref":ref(P/"MF.json"),"manifest_member_count":len(members),
 "mapping_ref":ref(P/"CONTRACT-MAPPING.md"),"diff_ref":ref(P/"client-protocol-attach.patch"),
 "inverse_replacements_ref":ref(P/"production-replacements.json"),
 "static_evidence_refs":[ref(P/"static-evidence.json"),ref(P/"final-static-checks.json")],
 "input_pins_ref":ref(P/"public-input-pins.json"),"original_tool_io_ref":ref(P/"original-tool-io.json"),
 "diagnostic827_ref":ref(P/"diagnostic-827.json"),"q4_block_handoff_ref":ref(q4/"HDF.json"),
 "mechanical_failures":[{"ordinal":827,"layer":"functions.exec JS parse","actualOuter":None,"actualPython":None,"native":None,"process_started":False}],
 "scope":{"valid_same_owner_lease_only_renewal":True,"synchronous_settled_transfer_true_AttachResult":True,
          "old_generation_replay_and_command_identity_unchanged":True,
          "terminal_but_unsettled_transfer_refused":True,"schema_migration":False},
 "preserved":{"entire_Execute_and_dispatch_bytes":True,"session_control_and_journal_bytes":True,
              "runtime_profile_native_session_bindings":True,"Main_T5_T6_TTL_Q3_unchanged":True},
 "open_branches":["full active asynchronous takeover requires pending intent/pause/settlement completion resource",
                  "historical cached attach ACK requires separately specified reconciliation"],
 "legacy_test_conflict":{"file":"client_protocol_control_windows_test.go","test":"TestClientSameWriterRenewsExpiredLease",
     "old_expectation":"ACKNOWLEDGED","new_actual_contract":"COMPLETED/AttachResult; epoch=2 expiry and stale revision remain",
     "existing_test_modified":False,"broad_suite_acceptance_claimed":False},
 "source_author_actions":{"Go_gofmt_native_SQL_model_private_signing":False,"canonical_or_Main_T5_T6_write":False,"provider_requests":0},
 "root_required_next":["independent bounded Source review","fresh isolated build with actual frozen inputs",
 "execute new Source tests and existing real runtime/profile/session rejection tests",
 "independently reconcile the known legacy ACK expectation before broad suite claims",
 "authorized eight-leaf native validation with original failures retained"],
 "native_acceptance":"PENDING_ROOT","all_attach_contract_branches_completed":False})
for name,pin in members.items():assert ref(P/name)==pin
print(json.dumps({"HDF":ref(P/"HDF.json"),"MF":ref(P/"MF.json"),"source_refs":{p.name:ref(p) for p in files},
 "diagnostic827":ref(P/"diagnostic-827.json"),"members":len(members),"inputs":len(inputs),"tests":len(tests),
 "inverse_raw_equal":True,"lexical_checks_only":True},ensure_ascii=True))

