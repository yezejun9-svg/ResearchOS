"""Seal Source only with read-only public-input checks. No Go or database execution."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
def ref(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def out(n,obj):
 with (P/n).open("x",encoding="utf-8",newline="\n") as f:json.dump(obj,f,ensure_ascii=True,indent=2);f.write("\n")
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
inputs=json.loads((P/"public-input-pins.json").read_bytes())["inputs"]
for pin in inputs:assert ref(Path(pin["path"]))==pin
files=sorted((P/"candidate-root/internal/domain").glob("*.go"))
assert len(files)==3
for path in files:delimiters(path.read_text(encoding="utf-8"))
e=json.loads((P/"static-evidence.json").read_bytes())
assert ref(Path(e["base"]["path"]))==e["base"]
assert ref(P/"candidate-root/internal/domain/client_protocol.go")==e["candidate"]
code=(P/"candidate-root/internal/domain/client_protocol.go").read_text(encoding="utf-8")
inverse=code
for c in reversed(json.loads((P/"production-replacements.json").read_bytes())):
 at=c["position"];assert inverse[at:at+len(c["after"])]==c["after"]
 inverse=inverse[:at]+c["before"]+inverse[at+len(c["after"]):]
assert inverse.encode()==Path(e["base"]["path"]).read_bytes()
helper=code.split("func clientAttachRestoreState(",1)[1].split("// journal appends",1)[0]
assert "ExecContext" not in helper and "ObserveRuntime(" not in helper and "UPDATE " not in helper and "INSERT " not in helper
assert code.index("renewAfterRestore, restoreReady")<code.index("if renewAfterRestore &&")
old=Path(e["base"]["path"]).parents[3]
old_hdf=json.loads((old/"HDF.json").read_bytes())
assert ref(Path(old_hdf["actual_T6_base_ref"]["path"]))==old_hdf["actual_T6_base_ref"]
assert (P/"candidate-root/internal/domain/client_protocol_attach_contract_windows_test.go").read_bytes()==(old/"candidate-root/internal/domain/client_protocol_attach_contract_windows_test.go").read_bytes()
tests=[]
for path in files:
 if path.name.endswith("_test.go"):
  tests.extend(line.split("(")[0].split()[-1] for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("func Test"))
assert len(tests)==7
out("final-static-checks.json",{"Go_lexical_delimiters_only":True,"Go_parser_build_tests_executed":False,"production_inverse_raw_equal":True,"prior_contract_test_raw_equal":True,"input_pins_reverified":len(inputs),"helper_read_only":True,"restore_gate_precedes_lease_write":True,"tests_source_only":tests,"real_restore_positive":"BLOCKED/PENDING_ROOT_RESOURCE","mechanical_failures":[832,834]})
members={p.relative_to(P).as_posix():ref(p) for p in sorted(P.rglob("*")) if p.is_file()}
assert "HDF.json" not in members and "MF.json" not in members
out("MF.json",{"schema":"researchos.attach-restore-source-manifest.v1","members":members})
out("HDF.json",{"schema":"researchos.attach-restore-source-handoff.v1","finding":"ATTACH-RESTORE-001","status":"SOURCE_ONLY_PENDING_INDEPENDENT_REVIEW_BUILD_AND_TEST","sourceStatus":"EXECUTION_REPORTED","formal":False,"production_ready":False,"execution_authority":False,"actor_id":"codex:/root/command_queue_impl","source_root":str(P),"manifest_ref":ref(P/"MF.json"),"manifest_member_count":len(members),"source_refs":{p.name:ref(p) for p in files},"base_ref":e["base"],"actual_T6_base_ref":old_hdf["actual_T6_base_ref"],"input_pins_ref":ref(P/"public-input-pins.json"),"mapping_ref":ref(P/"CONTRACT-MAPPING.md"),"diff_ref":ref(P/"restore.patch"),"replacements_ref":ref(P/"production-replacements.json"),"static_checks_ref":ref(P/"final-static-checks.json"),"tool_io_ref":ref(P/"original-tool-io.json"),"diagnostics_ref":ref(P/"diagnostics-832-834.json"),"mechanical_failures":[{"ordinal":832,"actualOuter":1,"actualPython":None,"native":None},{"ordinal":834,"actualOuter":0,"actualPython":None,"native":None}],"preserved_prior_failure_ordinals":[827,829,831],"scope":{"restore_claim_before_any_lease_write":True,"current_run_epoch_strict_fresh_double_settled":True,"real_post_restore_handoff_generation_required":True,"ordinary_active_owner_lease_only":True,"cached_ACK_Execute_dispatch_unchanged":True,"barrier_queue_control_resume_flags_untouched":True,"schema_migrations":False},"positive_restore_acceptance":"BLOCKED/PENDING_ROOT_RESOURCE","root_required":["independent Source review","compose fresh isolated candidate with separately owned legacy test revision","Go compilation and authored negative/ordinary positive tests","authorized real fresh restore observation plus one-generation transfer/exact replay/recovered renewal/new-barrier tests","retain original native failures and qualify any acceptance limits"],"open_branches":["active asynchronous takeover","historical cached ACK reconciliation"],"actions":{"Go_gofmt_parser_native_SQL_model_private_signing":False,"canonical_Main_T6_old_Source_write":False,"provider_requests":0},"self_approved":False})
for name,pin in members.items():assert ref(P/name)==pin
print(json.dumps({"HDF":ref(P/"HDF.json"),"MF":ref(P/"MF.json"),"source_refs":{p.name:ref(p) for p in files},"diagnostics":ref(P/"diagnostics-832-834.json"),"members":len(members),"inputs":len(inputs),"tests_source_only":len(tests)},ensure_ascii=True))

