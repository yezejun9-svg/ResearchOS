import sys
sys.dont_write_bytecode=True
import ast,copy,hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent
C=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/w09_evidence_v7_fragment_source_codex/fragv7-1a11f30")
def pin(p):
 p=Path(p).resolve();b=p.read_bytes()
 return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def verify(v):
 q=pin(v["path"])
 assert q["sha256"]==v["sha256"].removeprefix("sha256:") and q["bytes"]==v["bytes"],v["path"]
 return q
def save(name,value):
 with (N/name).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+"\n")
checks=[]
def check(name,ok,detail=None):
 checks.append(dict(name=name,passed=bool(ok),detail=detail))
 if not ok:raise AssertionError(name)
def rejected(name,call,kind=ValueError,code=None):
 err=None
 try:call()
 except kind as e:err=e
 check(name,err is not None and (code is None or str(err)==code),str(err) if err is not None else None)
h=verify(dict(path=str(C/"HDF.json"),sha256="bb664f6f7c248b35836b95e36c079aa0bdb45d649a49898163f477cd627bfd39",bytes=4934))
m=verify(dict(path=str(C/"MF.json"),sha256="a6b18e560edb37fb14c372f6d20e5760cf03b3d2ad11bd8d4e7ecbfed17dcda7",bytes=4199))
H=json.loads(Path(h["path"]).read_bytes());M=json.loads(Path(m["path"]).read_bytes())
members=[verify(v) for v in M["members"]]
check("all_14_exact_manifest_members",len(members)==14)
check("HDF_manifest_exact",H["manifest_ref"]==m)
I=json.loads((C/"source-inputs.json").read_bytes())
P=json.loads((C/"source-provenance.json").read_bytes())
refs=[h,m]+members+[verify(v) for v in I["refs"]]+[pin(__file__),pin(sys.executable)]
refs=list({v["path"]:v for v in refs}.values())
gp=Path(I["guard_ref"]["path"]);verify(I["guard_ref"])
check("guard_exact_accepted_hash",pin(gp)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85")
gm=types.ModuleType("v7_independent_actual_read_guard");gm.__file__=str(gp);sys.modules[gm.__name__]=gm
exec(compile(gp.read_bytes(),str(gp),"exec"),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
notes={}
try:
 guard.acquire(refs)
 def buf(ref):return guard.get_buffer(ref["path"])
 raw=buf(H["candidate_source_ref"]);old=buf(H["original_source_ref"])
 check("candidate_exact",len(raw)==42716 and hashlib.sha256(raw).hexdigest()=="1cc37f4fec48d2e2bae39db3c1f8d1da9fdfe6bd788a44396ea0a8b877be6777")
 check("old_exact",len(old)==42128 and hashlib.sha256(old).hexdigest()=="2989eb2c89a0647cf9bf9fb99841dcb8e943d64c6dd84d0a0fe7bca4b9568eec")
 tree=ast.parse(raw);oldtree=ast.parse(old)
 functions={x.name:x for x in tree.body if isinstance(x,ast.FunctionDef)}
 previous={x.name:x for x in oldtree.body if isinstance(x,ast.FunctionDef)}
 check("exact_one_new_function",set(functions)-set(previous)=={"_go_assertions"} and not(set(previous)-set(functions)))
 for name,node in previous.items():
  if name!="verify_native":check("unchanged_AST_"+name,ast.dump(node,include_attributes=False)==ast.dump(functions[name],include_attributes=False))
 oldnative=previous["verify_native"];newnative=functions["verify_native"]
 oldidx=next(i for i,x in enumerate(oldnative.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="assertions" for t in x.targets))
 newidx=next(i for i,x in enumerate(newnative.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="assertions" for t in x.targets))
 check("old_parser_exact_adjacent_assign_and_for",isinstance(oldnative.body[oldidx+1],ast.For))
 callast=ast.parse("assertions = _go_assertions(events, selected, refs[0])").body[0]
 check("new_parser_call_exact",ast.dump(newnative.body[newidx],include_attributes=False)==ast.dump(callast,include_attributes=False))
 rebuilt=copy.deepcopy(newnative);rebuilt.body[newidx:newidx+1]=copy.deepcopy(oldnative.body[oldidx:oldidx+2])
 check("verify_native_AST_inverse_preserves_every_other_validation",ast.dump(rebuilt,include_attributes=False)==ast.dump(oldnative,include_attributes=False))
 oldlines=old.decode("utf-8").splitlines(keepends=True);newlines=raw.decode("utf-8").splitlines(keepends=True)
 oldblock="".join(oldlines[oldnative.body[oldidx].lineno-1:oldnative.body[oldidx+1].end_lineno])
 newcall="".join(newlines[newnative.body[newidx].lineno-1:newnative.body[newidx].end_lineno])
 helper="".join(newlines[functions["_go_assertions"].lineno-1:newnative.lineno-1])
 check("exact_helper_and_call_singletons",raw.decode().count(helper)==1 and raw.decode().count(newcall)==1)
 inverse=raw.decode().replace(helper,"",1).replace(newcall,oldblock,1).encode()
 check("independent_full_file_byte_inverse",inverse==old)
 restored=ast.parse(inverse)
 check("independent_whole_module_AST_inverse",ast.dump(restored,include_attributes=False)==ast.dump(oldtree,include_attributes=False))
 check("author_opcodes_exact_old_and_new", "".join(line for op in P["opcodes"] for line in op["old_lines"]).encode()==old and "".join(line for op in P["opcodes"] for line in op["new_lines"]).encode()==raw)
 ctr=json.loads(buf(H["source_controls_ref"]))
 check("all_author_181_controls_recorded_PASS",ctr["count"]==181 and len(ctr["checks"])==181 and all(c["passed"] is True for c in ctr["checks"]))
 for ref in H["guard_cleanup_refs"]:
  cleanup=json.loads(buf(ref))
  check("author_guard_closed_"+Path(ref["path"]).name,cleanup["closed"] is True and cleanup["errors"]==[] and cleanup["retained_handles_count"]==0 and all(e["closed"] and e["verified"] and e["final_path_match"] for e in cleanup["entries"]))
 canon=I["canonical_refs"]
 check("canonical_four_fixed_count",len(canon)==4 and all(verify(v)==v for v in canon))
 check("canonical_CP365_OW169",json.loads(buf(canon[0]))["revision"]==365 and json.loads(buf(canon[1]))["revision"]==169)
 env={"json":json}
 exec(compile(ast.Module(body=[functions["require"],functions["_go_assertions"]],type_ignores=[]),"<independent-extracted-v7-parser>","exec"),env)
 parse=env["_go_assertions"]
 stdout=buf(I["actual_stdout_ref"]);report=json.loads(buf(I["actual_report_ref"]))
 events=[json.loads(line) for line in stdout.decode("utf-8").splitlines()]
 selected=report["selected_tests"];ref=report["raw_evidence_references"][0];actual=parse(events,selected,ref)
 check("real_29_JSONL_events",len(events)==29)
 check("real_5_assertions_equal_immutable_report",len(actual)==5 and actual==report["assertion_results"])
 def typed_equal(a,b):
  if type(a) is not type(b):return False
  if isinstance(a,dict):return a.keys()==b.keys() and all(typed_equal(a[k],b[k]) for k in a)
  if isinstance(a,list):return len(a)==len(b) and all(typed_equal(x,y) for x,y in zip(a,b))
  return a==b
 check("real_assertions_type_sensitive_recursive_equality",typed_equal(actual,report["assertion_results"]))
 check("real_assertions_canonical_JSON_exact",json.dumps(actual,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(",",":"))==json.dumps(report["assertion_results"],sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(",",":")))
 check("C19_05_fragments_22_23_join",events[22]["Package"]==events[23]["Package"] and events[22]["Test"]==events[23]["Test"] and not events[22]["Output"].endswith("\n") and actual[-1]["assertion_id"]=="C19-05")
 evtidx=next(i for i,x in enumerate(newnative.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="events" for t in x.targets))
 lockidx=next(i for i,x in enumerate(newnative.body) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="locked_path" for t in x.targets))
 fn=ast.parse("def replay(events, selected, expected, report, refs, run_id):\n    pass").body[0]
 fn.body=copy.deepcopy(newnative.body[evtidx+1:lockidx])+[ast.Return(value=ast.Name(id="assertions",ctx=ast.Load()))]
 ast.fix_missing_locations(fn);exec(compile(ast.Module(body=[fn],type_ignores=[]),"<independent-native-prefix-only>","exec"),env)
 def replay(es=events,rp=report):return env["replay"](es,selected,report["assertion_ids"],rp,report["raw_evidence_references"],report["run_id"])
 check("actual_native_exact_prefix_pass",replay()==actual)
 for key in ("assertion_id","status","run_id"):
  changed=copy.deepcopy(report);changed["assertion_results"][0][key]="changed"
  rejected("report_"+key+"_tamper",lambda rp=changed:replay(rp=rp),code="STDOUT_ASSERTION_REPLAY_MISMATCH")
 changed=copy.deepcopy(report);changed["assertion_results"].reverse()
 rejected("report_order_tamper",lambda:replay(rp=changed),code="STDOUT_ASSERTION_REPLAY_MISMATCH")
 for action in ("fail","skip"):
  es=events+[dict(Action=action,Package="p",Test=selected[0])]
  rejected("roster_"+action,lambda es=es:replay(es=es),code="GO_TEST_ROSTER_NOT_PASS")
 es=events+[dict(Action="pass",Package="p",Test=selected[0])]
 rejected("duplicate_pass_roster",lambda:replay(es=es),code="GO_TEST_ROSTER_NOT_PASS")
 es=events+[dict(Action="pass",Package="p",Test="Foreign")]
 rejected("foreign_terminal_test",lambda:replay(es=es),code="FOREIGN_GO_TEST")
 # Every possible split position in the actual formerly-failing C19-05 line.
 joined=events[22]["Output"]+events[23]["Output"]
 for cut in range(len(joined)+1):
  es=events[:22]+[dict(events[22],Output=joined[:cut]),dict(events[23],Output=joined[cut:])]+events[24:]
  check("C19_05_split_"+str(cut),typed_equal(parse(es,selected,ref),actual))
 def event(text,test="T",package="p"):return dict(Action="output",Package=package,Test=test,Output=text)
 base=dict(test_name="T",assertion_id="A",run_id="0"*32,status="PASS",evidence={"integer":9007199254740993,"negative":-9007199254740993,"text":"汉字🙂\u2028\u2029\u0085 CR\\rLF\\n"})
 other=dict(base,test_name="U",assertion_id="B")
 def line(rec):return "W09_ASSERTION "+json.dumps(rec,ensure_ascii=False,separators=(",",":"))+"\n"
 la,lb=line(base),line(other)
 def expected(rec):return dict(rec,raw_evidence_reference="RAW")
 check("large_integer_no_float_rounding",typed_equal(parse([event(la)],["T"],"RAW"),[expected(base)]))
 check("Unicode_separators_retained_inside_JSON_strings",parse([event(la)],["T"],"RAW")[0]["evidence"]["text"]==base["evidence"]["text"])
 check("CRLF_split_preserves_JSON",typed_equal(parse([event(la[:-1]+"\r"),event("\n")],["T"],"RAW"),[expected(base)]))
 check("character_fragments",typed_equal(parse([event(x) for x in la],["T"],"RAW"),[expected(base)]))
 check("empty_and_absent_Output",typed_equal(parse([event(""),dict(Action="pass",Package="p",Test="T"),event(la)],["T"],"RAW"),[expected(base)]))
 check("completion_order_for_interleaved_owners",typed_equal(parse([event(la[:20]),event(lb,test="U"),event(la[20:])],["T","U"],"RAW"),[expected(other),expected(base)]))
 check("package_level_stream_cannot_merge_test_line",typed_equal(parse([event("log ",test=None),event(la),event("done\n",test=None)],["T"],"RAW"),[expected(base)]))
 check("multiple_lines_in_one_Output",typed_equal(parse([event("log\n\n"+la+la)],["T"],"RAW"),[expected(base),expected(base)]))
 badcases=[
 ("marker_tail",[event("W09_ASS")],"GO_OUTPUT_DANGLING_FRAGMENT"),
 ("JSON_tail",[event("W09_ASSERTION {")],"GO_OUTPUT_DANGLING_FRAGMENT"),
 ("complete_JSON_no_LF",[event(la[:-1])],"GO_OUTPUT_DANGLING_FRAGMENT"),
 ("plain_log_tail",[event("tail")],"GO_OUTPUT_DANGLING_FRAGMENT"),
 ("CR_only_terminator",[event(la[:-1]+"\r")],"GO_OUTPUT_DANGLING_FRAGMENT"),
 ("Unicode_separator_not_line_terminator",[event(la[:-1]+"\u2028")],"GO_OUTPUT_DANGLING_FRAGMENT"),
 ("cross_Test_fragments",[event(la[:20]),event(la[20:],test="U")],"GO_OUTPUT_DANGLING_FRAGMENT"),
 ("mixed_Package_fragments",[event(la[:20],package="p1"),event(la[20:],package="p2")],"GO_OUTPUT_DANGLING_FRAGMENT"),
 ("Test_owner_mismatch",[event(lb)],"ASSERTION_STDOUT_OWNER_MISMATCH"),
 ("unselected_Test",[event(lb,test="U")],"ASSERTION_STDOUT_OWNER_MISMATCH"),
 ("None_Test_assertion",[event(la,test=None)],"ASSERTION_STDOUT_OWNER_MISMATCH"),
 ("invalid_Package_type",[event(la,package=1)],"GO_OUTPUT_OWNER_NOT_TEXT"),
 ("invalid_Test_type",[event(la,test=[])],"GO_OUTPUT_OWNER_NOT_TEXT"),
 ("nonstring_Output",[event(None)],"GO_OUTPUT_NOT_TEXT")]
 for label,es,code in badcases:rejected(label,lambda es=es:parse(es,["T"],"RAW"),code=code)
 for label,txt in [("malformed","W09_ASSERTION {bad}\n"),("truncated_with_LF","W09_ASSERTION {\n"),("raw_CR_in_JSON_string",'W09_ASSERTION {"test_name":"T","x":"bad\rtext"}\n'),("two_JSON_on_same_line",la[:-1]+la)]:
  rejected(label,lambda txt=txt:parse([event(txt)],["T"],"RAW"),kind=json.JSONDecodeError)
 rejected("nonobject_assertion",lambda:parse([event("W09_ASSERTION []\n")],["T"],"RAW"),code="ASSERTION_STDOUT_OWNER_MISMATCH")
 # Compatibility characterization: Package allowlisting is outside both old/new parser.
 oldfn=ast.parse("def old_parse(events, selected, refs):\n    pass").body[0]
 oldfn.body=copy.deepcopy(oldnative.body[oldidx:oldidx+2])+[ast.Return(value=ast.Name(id="assertions",ctx=ast.Load()))]
 ast.fix_missing_locations(oldfn);exec(compile(ast.Module(body=[oldfn],type_ignores=[]),"<independent-old-parser-only>","exec"),env)
 rejected("v6_original_known_split_exception_handled",lambda:env["old_parse"](events,selected,[ref]),kind=json.JSONDecodeError)
 plain=dict(base,evidence={"integer":9007199254740993})
 whole=[event(line(plain),package="other-package")]
 check("whole_foreign_Package_acceptance_is_inherited_not_new",env["old_parse"](whole,["T"],["RAW"])==parse(whole,["T"],"RAW"))
 notes["package_boundary"]="New code isolates fragment streams by exact Package/Test; neither v6 nor v7 allowlists complete Package values. Report/raw/native provenance remains the existing outer trust boundary. Mixed-Package partial join rejects; this review does not claim new package authenticity enforcement."
 notes["numeric_boundary"]="stdlib json parsing preserves actual integers and independently compared current records with type-sensitive recursion and canonical JSON. Existing verify_native Python == semantics are unchanged and are not newly advertised as type-strict on arbitrary synthetic numeric/bool values."
 notes["line_boundary"]="LF only. CRLF is accepted as JSON trailing whitespace; raw CR inside JSON string rejects; Unicode separators inside JSON string remain data, not a terminator."
 notes["execution_scope"]="Only require/_go_assertions, old parser, and exact events-to-assertions prefix AST extracted in memory. No full verify_native, consumer/router/Go/native/SQL/API/model execution."
 for v in refs:check("input_pin_unchanged_"+v["path"],pin(v["path"])==v)
 save("checks.json",dict(all_passed=all(x["passed"] for x in checks),count=len(checks),checks=checks))
 save("input-pins.json",refs)
 save("result.json",dict(status="SOURCE_ACCEPTED_PENDING_NEW_PRODUCER_AND_MODE_DECISIONS",check_count=len(checks),input_count=len(refs),candidate_ref=H["candidate_source_ref"],actual_events=29,actual_records=5,typed_equal=True,full_byte_inverse=True,full_AST_inverse=True,old_raw_and_report_unchanged=True,CP365_OW169_unchanged=True,actual_source_read_guard_held=True,product_executed=False,full_consumer_executed=False,formal_acceptance=False,notes=notes,new_failures=[],STOP_FINAL=True))
 print(json.dumps(dict(status="SOURCE_ACCEPTED_PENDING_NEW_PRODUCER_AND_MODE_DECISIONS",checks=len(checks),inputs=len(refs),real_events=29,real_records=5,split_positions=len(joined)+1,actual_source_read_guard_held=True)),flush=True)
finally:
 cleanup=guard.close();save("source-guard.cleanup.json",cleanup)
 assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
