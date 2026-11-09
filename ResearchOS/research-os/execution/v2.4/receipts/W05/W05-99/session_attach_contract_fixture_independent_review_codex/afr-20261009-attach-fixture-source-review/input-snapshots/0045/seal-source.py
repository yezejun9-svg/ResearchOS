"""Seal ATT3 source; pure file checks and timestamp arithmetic only."""
import json,hashlib,re,itertools
from pathlib import Path
from datetime import datetime,timezone,timedelta
P=Path(__file__).resolve().parent
def ref(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def out(n,v):
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
# Independent integer-nanosecond vector arithmetic, not a Go parser model.
def instant(raw):
 m=re.fullmatch(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,9}))?(Z|[+-]\d\d:\d\d)",raw)
 if not m:raise ValueError("unknown timestamp")
 date=datetime.strptime(m[1],"%Y-%m-%dT%H:%M:%S")
 if date==datetime(1,1,1) and not m[2] and m[3]=="Z":raise ValueError("unknown zero")
 delta=timedelta(0)
 if m[3]!="Z":
  h,minute=map(int,m[3][1:].split(":"))
  if h>23 or minute>59:raise ValueError("bad offset")
  delta=timedelta(hours=h,minutes=minute)*(1 if m[3][0]=="+" else -1)
 utc=date.replace(tzinfo=timezone(delta)).astimezone(timezone.utc)
 difference=utc-datetime(1970,1,1,tzinfo=timezone.utc)
 return (difference.days*86400+difference.seconds)*1000000000+int((m[2] or "").ljust(9,"0"))
pairs=[
 ["2026-10-09T00:00:00.1Z","2026-10-09T00:00:00.11Z"],
 ["2026-10-09T00:00:00Z","2026-10-09T00:00:00.000000001Z"],
 ["2026-10-09T08:00:00.1+08:00","2026-10-09T00:00:00.11Z"]]
results=[]
for pair in pairs:
 older,newer=map(instant,pair);assert newer>older
 for reverse in (False,True):
  rows=[(older,True),(newer,False)]
  if reverse:rows.reverse()
  latest=None;valid=False
  for observed,okay in rows:
   if latest is None or observed>latest:latest,valid=observed,okay
   elif observed==latest:valid=valid and okay
  assert latest==newer and not valid
  results.append({"pair":pair,"reverse_input":reverse,"latest_partial_refused":True})
assert sorted(pairs[0],reverse=True)[0]==pairs[0][0]
tie=["2026-10-09T00:00:00.1Z","2026-10-09T08:00:00.100+08:00"]
assert instant(tie[0])==instant(tie[1])
for states in itertools.permutations([True,False]):
 latest_valid=states[0] and states[1];assert not latest_valid
chain=["2026-10-09T00:00:00.1Z","2026-10-09T00:00:00.11Z","2026-10-09T00:00:00.111Z","2026-10-09T00:00:00.1111Z"]
assert all(instant(a)<instant(b) for a,b in zip(chain,chain[1:]))
invalid=["","unknown","!2026-10-09T00:00:00Z","2026-10-09","2026-02-30T00:00:00Z","2026-10-09T00:00:00","0001-01-01T00:00:00Z"]
for raw in invalid:
 try:instant(raw)
 except ValueError:pass
 else:raise AssertionError("invalid vector accepted")
out("timestamp-static-evidence.json",{"kind":"PURE_PYTHON_VECTOR_ARITHMETIC_NOT_GO_SQL_NATIVE","old_TEXT_sort_reversal_confirmed":True,"variable_fraction_pairs":results,"equal_instants":tie,"equal_instant_partial_refused_both_orders":True,"barrier_observation_handoff_expiry_chain":chain,"invalid_vectors":invalid,"invalid_vectors_rejected":True})
inputs=json.loads((P/"public-input-pins.json").read_bytes())["inputs"]
for pin in inputs:assert ref(Path(pin["path"]))==pin
e=json.loads((P/"static-evidence.json").read_bytes())
base=Path(e["base_ref"]["path"]);assert ref(base)==e["base_ref"]
production=P/"candidate-root/internal/domain/client_protocol.go"
assert ref(production)==e["candidate_ref"]
code=production.read_text(encoding="utf-8")
inverse=code
for c in reversed(json.loads((P/"production-replacements.json").read_bytes())):
 at=c["position"];assert inverse[at:at+len(c["after"])]==c["after"]
 inverse=inverse[:at]+c["before"]+inverse[at+len(c["after"]):]
assert inverse.encode()==base.read_bytes()
files=sorted((P/"candidate-root/internal/domain").glob("*.go"));assert len(files)==4
for p in files:delimiters(p.read_text(encoding="utf-8"))
for name in ["client_protocol_attach_contract_windows_test.go","client_protocol_attach_restore_windows_test.go"]:
 assert (production.parent/name).read_bytes()==(base.parent/name).read_bytes()
helper=code.split("// clientAttachRestoreTime compares",1)[1].split("// journal appends",1)[0]
assert all(x not in helper for x in ["max(restored_at)","ORDER BY observed_at","ExecContext","INSERT ","UPDATE ","ObserveRuntime(","return true, true, nil\n\t\t}\n\t}\n\tif err = events.Err"])
assert "order.add(observed, valid)" in helper and "if !order.seen || !order.valid || firstFresh.IsZero()" in helper
assert "return recovered, true, nil" in helper
assert "if decodeErr != nil || !timeValid || !expiryValid || !expires.After(effective)" in helper
tests=[line.split("(")[0].split()[-1] for p in files if p.name.endswith("_test.go") for line in p.read_text(encoding="utf-8").splitlines() if line.startswith("func Test")]
assert len(tests)==10
out("final-static-checks.json",{"input_pin_count":len(inputs),"inverse_raw_byte_equal":True,"old_two_test_files_byte_equal":True,"Go_lexical_delimiters_only":True,"no_TEXT_timestamp_max_or_order_in_restore_helper":True,"latest_observation_accumulator_by_instant":True,"all_related_handoff_timestamps_scanned":True,"helper_read_only":True,"tests_source_only":tests,"Go_parser_build_tests_SQL_native_model_executed":False,"new_mechanical_failures":[]})
members={p.relative_to(P).as_posix():ref(p) for p in sorted(P.rglob("*")) if p.is_file()}
assert "HDF.json" not in members and "MF.json" not in members
out("MF.json",{"schema":"researchos.attach-restore-time-source-manifest.v1","members":members})
out("HDF.json",{"schema":"researchos.attach-restore-time-source-handoff.v1","finding":"ATTACH-RESTORE-002","status":"SOURCE_ONLY_PENDING_INDEPENDENT_REVIEW_BUILD_AND_TEST","sourceStatus":"EXECUTION_REPORTED","actor_id":"codex:/root/command_queue_impl","formal":False,"production_ready":False,"execution_authority":False,"self_approved":False,"source_root":str(P),"manifest_ref":ref(P/"MF.json"),"manifest_member_count":len(members),"source_refs":{p.name:ref(p) for p in files},"base_ref":e["base_ref"],"input_pins_ref":ref(P/"public-input-pins.json"),"mapping_ref":ref(P/"CONTRACT-MAPPING.md"),"diff_ref":ref(P/"restore-time.patch"),"replacements_ref":ref(P/"production-replacements.json"),"static_checks_ref":ref(P/"final-static-checks.json"),"timestamp_evidence_ref":ref(P/"timestamp-static-evidence.json"),"tool_io_ref":ref(P/"original-tool-io.json"),"new_mechanical_failures":[],"preserved_prior_failure_ordinals":[827,829,831,832,834,838],"prior_Source_rejections_preserved":["ATTACH-RESTORE-001","ATTACH-RESTORE-002"],"scope":{"parsed_UTC_barrier_max":True,"parsed_UTC_observation_latest":True,"equal_instant_partial_refused":True,"unknown_related_timestamp_refused":True,"all_related_handoff_times_checked":True,"original_identity_hash_contract_gates_preserved":True,"no_barrier_active_renewal_unchanged":True,"no_queue_control_resume_fence_write":True,"old_two_test_sources_byte_equal":True},"positive_restore_acceptance":"BLOCKED/PENDING_ROOT_RESOURCE","native_positive_or_authority_fabricated":False,"actions":{"Go_gofmt_parser_build_test_SQL_native_model":False,"Main_T6_canonical_oldSource_write":False},"root_required":["independent Source review","fresh isolated composition and Go build/tests","actual authorized native restore observation resource and positive transfer/replay/recovered renewal/new barrier acceptance"],"open_branches":["active asynchronous takeover","historical cached ACK reconciliation"],"STOP":True})
for name,pin in members.items():assert ref(P/name)==pin
print(json.dumps({"HDF":ref(P/"HDF.json"),"MF":ref(P/"MF.json"),"source_refs":{p.name:ref(p) for p in files},"members":len(members),"inputs":len(inputs),"tests_source_only":len(tests),"new_failures":[]},ensure_ascii=True))

