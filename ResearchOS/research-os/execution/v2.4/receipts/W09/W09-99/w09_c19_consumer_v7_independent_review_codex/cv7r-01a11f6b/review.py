import sys
sys.dont_write_bytecode=True
import ast,copy,hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent
R=Path("D:/作品集/ResearchOS/research-os");W=R/"execution/v2.4/receipts/W09/W09-99"
C=W/"w09_c19_consumer_v7_caller_source_codex/consv7-1a11f5e"
S=W/"w09_c19_consumer_caller_source_codex/w09cons-1a11f30"
P=W/"w09_c19_caller_v7_source_codex/w09c19r3-1a11f30"
Q=W/"v7_fragment_independent_review_codex/v7r-01a11f3f"
GP=R/"execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
canonical={str((R/"execution/v2.4"/(n+".json")).resolve()).casefold() for n in ("checkpoint","path_ownership","step_state","commands")}
def pin(p):
 p=Path(p).resolve();assert str(p).casefold() not in canonical,"CURRENT_CANONICAL_FORBIDDEN"
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def verify(v):
 a=pin(v["path"]);assert (a["sha256"],a["bytes"])==(v["sha256"].removeprefix("sha256:"),v["bytes"]),v["path"];return a
def save(n,v):
 with (N/n).open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
checks=[]
def ck(n,v):
 checks.append(dict(name=n,passed=bool(v)))
 if not v:raise AssertionError(n)
h=verify(dict(path=str(C/"HDF.json"),sha256="d563d849166428e67cb38ea1630d973c16c72227660d804bd52077b7ed5630a0",bytes=7024))
m=verify(dict(path=str(C/"MF.json"),sha256="38446a3dfa23b1070d23ea90d27c1f7730188f57f408027070cd6e35fddb11dd",bytes=5748))
H=json.loads((C/"HDF.json").read_bytes());M=json.loads((C/"MF.json").read_bytes())
refs=[h,m]+[verify(v) for v in M["members"]]+[verify(v) for v in json.loads((C/"source-input-pins.original.json").read_bytes())]
refs += [pin(GP),pin(__file__),pin(sys.executable)]
refs=list({v["path"].casefold():v for v in refs}.values())
ck("guard_exact_source",pin(GP)["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85")
gm=types.ModuleType("cv7_independent_read_guard");gm.__file__=str(GP);sys.modules[gm.__name__]=gm
exec(compile(GP.read_bytes(),str(GP),"exec"),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
 guard.acquire(refs)
 def raw(p):return guard.get_buffer(str(Path(p).resolve()))
 def obj(p):return json.loads(raw(p))
 def enc(v):return (json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode()
 choice=obj(C/"source.choice.json");oldchoice=obj(S/"source.choice.json");contract=obj(C/"calling-contract.json")
 oldcontract=obj(S/"calling-contract.json");derived=obj(C/"consumer-contract.v7.json");oldderived=obj(oldchoice["contract_ref"]["path"])
 pc=obj(P/"source.integration.choice.json");closure="ops/ci/w09_evidence_closure.py"
 ck("HDF_manifest",H["manifest_ref"]==m)
 ck("author_controls_148",obj(C/"source-controls.json")["count"]==148 and all(x["passed"] for x in obj(C/"source-controls.json")["checks"]))
 ck("author_inputs_81",len(obj(C/"source-input-pins.original.json"))==81)
 replacements=[("w09c19-1a11f08","w09c19v7-1a11f30"),("w09c19-producer-1a11f08","w09c19v7-producer-1a11f30"),("w09c19-producer-env-1a11f08","w09c19v7-producer-env-1a11f30"),("w09c19-consumers-1a11f30","w09c19v7-consumers-1a11f30"),("w09c19-consumers-env-1a11f30","w09c19v7-consumers-env-1a11f30")]
 def paths(v):
  if isinstance(v,str):
   for a,b in replacements:v=v.replace(a,b)
   return v
  if isinstance(v,list):return [paths(x) for x in v]
  if isinstance(v,dict):return {k:paths(x) for k,x in v.items()}
  return v
 old=raw(S/"run_c19_consumers.actual_owned.py");new=raw(C/"run_c19_consumers.actual_owned.py")
 oldschema="vector=load(request['canonical_vector_ref']);require(vector['schema']=='researchos.w09-c19-canonical-input-vector.v1' and vector['checkpoint_revision']==365,'CANONICAL_VECTOR_CP365')"
 newschema="vector=load(request['canonical_vector_ref']);require(isinstance(vector,dict) and set(vector)=={'schema','checkpoint_revision','refs'} and vector['schema']=='researchos.w09-c19-canonical-input-vector.v1' and type(vector['checkpoint_revision']) is int and vector['checkpoint_revision']>0,'CANONICAL_VECTOR_EXPLICIT_REVISION')"
 oldrev="require(json.loads(canonical[0].read_bytes())['revision']==365 and json.loads(canonical[1].read_bytes())['revision']==169,'CP365_OW169')"
 newrev="checkpoint_revision=json.loads(canonical[0].read_bytes())['revision'];ownership_revision=json.loads(canonical[1].read_bytes())['revision']\n  require(type(checkpoint_revision) is int and checkpoint_revision==vector['checkpoint_revision'] and type(ownership_revision) is int and ownership_revision>0,'EXACT_VECTOR_BOUND_CANONICAL_REVISIONS')"
 substitutions=replacements+[("CHOICE_SHA='6dab14b88b18f5f8117ec179f85ceafce44f06ebfe9f16b024ffc69edb537ebf'","CHOICE_SHA='"+pin(C/"source.choice.json")["sha256"]+"'"),("CHOICE_BYTES=20131","CHOICE_BYTES="+str(pin(C/"source.choice.json")["bytes"])),(oldschema,newschema),(oldrev,newrev)]
 forward=old.decode();back=new.decode()
 for a,b in substitutions:
  ck("unique_old_"+a[:70],forward.count(a)==1);forward=forward.replace(a,b)
 for a,b in reversed(substitutions):back=back.replace(b,a)
 ck("independent_full_caller_forward",forward.encode()==new);ck("independent_full_caller_inverse",back.encode()==old)
 ck("independent_full_AST_inverse",ast.dump(ast.parse(back))==ast.dump(ast.parse(old)))
 proof=obj(C/"caller.allowed-substitutions.json")
 ck("exact_nine_substitution_contract",proof["substitutions"]==[dict(old=a,new=b,occurrences=1) for a,b in substitutions])
 of={x.name:x for x in ast.parse(old).body if isinstance(x,ast.FunctionDef)};nf={x.name:x for x in ast.parse(new).body if isinstance(x,ast.FunctionDef)}
 ck("function_set_unchanged",set(of)==set(nf))
 for name in of:
  if name!="main":ck("unchanged_function_"+name,ast.dump(of[name])==ast.dump(nf[name]))
 expected=paths(oldderived);expected["source_refs"][closure]=pc["sources"][closure];expected["calling_contract_ref"]=pin(P/"root-calling-contract.json")
 expected["source_derivation"]=dict(original_contract_ref=pin(oldchoice["contract_ref"]["path"]),r3_handoff_ref=pin(P/"HDF.json"),r3_manifest_ref=pin(P/"MF.json"),v7_review_handoff_ref=pin(Q/"HDF.json"),v7_review_manifest_ref=pin(Q/"MF.json"),old_registry_ref_historical_only=True,actual_execution=False)
 ck("derived_contract_entire_independent_bytes",enc(expected)==raw(C/"consumer-contract.v7.json"))
 expected=copy.deepcopy(oldchoice);expected["contract_ref"]=pin(C/"consumer-contract.v7.json");expected["six_source_refs"]=pc["sources"];expected["fixed_future_paths"]=paths(oldchoice["fixed_future_paths"])
 expected["source_revision"]=dict(status="SOURCE_PREPARED_PENDING_NEW_PRODUCER_QUALIFICATION_AND_ROOT_SCOPE",base_consumer_handoff_ref=pin(S/"HDF.json"),base_consumer_manifest_ref=pin(S/"MF.json"),r3_handoff_ref=pin(P/"HDF.json"),r3_manifest_ref=pin(P/"MF.json"),v7_review_handoff_ref=pin(Q/"HDF.json"),v7_review_manifest_ref=pin(Q/"MF.json"),v7_review_status=obj(Q/"HDF.json")["status"],current_canonical_not_read=True,canonical_at_source_preparation_is_historical=True,new_producer_and_mode_decisions_required=True,actual_ready=False)
 newrefs=[]
 for v in oldchoice["input_refs"]:
  p=Path(v["path"])
  if "w09_c19_caller_source_revision_codex" in p.parts or p==Path(oldchoice["contract_ref"]["path"]) or v==oldchoice["six_source_refs"][closure]:continue
  newrefs.append(verify(v))
 newrefs += [pin(C/"consumer-contract.v7.json"),verify(pc["sources"][closure])]+[pin(z/name) for z in (S,P,Q) for name in ("HDF.json","MF.json")]
 for z in (P,Q):
  members=obj(z/"MF.json")["members"];members=list(members.values()) if isinstance(members,dict) else members
  newrefs += [verify(v) for v in members]
 expected["input_refs"]=list({v["path"]:v for v in newrefs}.values())
 ck("choice_entire_independent_bytes",enc(expected)==raw(C/"source.choice.json"))
 expected=paths(oldcontract);expected.update(status="SOURCE_PREPARED_PENDING_NEW_PRODUCER_QUALIFICATION_AND_ROOT_SCOPE",known_blocker_ref=oldcontract["known_blocker_ref"],known_blocker_is_historical_v6_only=True,source_caller_ref=pin(C/"run_c19_consumers.actual_owned.py"),source_choice_ref=pin(C/"source.choice.json"))
 expected["Root_argv"][6]=expected["source_caller_ref"]["path"];expected["scope_fixed_values"]["source_caller_ref"]=expected["source_caller_ref"]
 expected["guard_contract"]=expected["guard_contract"].replace("at CP365/OW169","from the exact explicit Root vector also bound by producer pre-run")
 expected["canonical_vector_contract"]=dict(schema="researchos.w09-c19-canonical-input-vector.v1",exact_fields=["schema","checkpoint_revision","refs"],checkpoint_revision="POSITIVE_INT_EQUAL_PINNED_CHECKPOINT_CONTENT",ownership_revision="POSITIVE_INT_FROM_EXACT_VECTOR_PINNED_PATH_OWNERSHIP",same_ref_as_producer_pre_run_and_Root_scope=True,historical_source_canonical_not_runtime_binding=True,expected_future_revision=None)
 expected["v7_source_review_refs"]=[pin(Q/n) for n in ("HDF.json","MF.json")];expected["r3_producer_source_refs"]=[pin(P/n) for n in ("HDF.json","MF.json")]
 expected["new_producer_report_tool_mode_actual_review_and_Root_scope_required"]=True;expected["actual_ready"]=False
 ck("calling_contract_entire_independent_bytes",enc(expected)==raw(C/"calling-contract.json"))
 for proofname,op,np in [("caller.complete-byte-inverse.json",S/"run_c19_consumers.actual_owned.py",C/"run_c19_consumers.actual_owned.py"),("choice.complete-inverse.json",S/"source.choice.json",C/"source.choice.json"),("calling-contract.complete-inverse.json",S/"calling-contract.json",C/"calling-contract.json"),("consumer-contract.complete-inverse.json",oldchoice["contract_ref"]["path"],C/"consumer-contract.v7.json")]:
  proof=obj(C/proofname)
  ck("author_opcode_inverse_"+proofname,"".join(l for x in proof["opcodes"] for l in x["old_lines"]).encode()==raw(op))
  ck("author_opcode_forward_"+proofname,"".join(l for x in proof["opcodes"] for l in x["new_lines"]).encode()==raw(np))
 ck("six_sources_one_change",len(choice["six_source_refs"])==6 and all(v==(pc["sources"][closure] if k==closure else oldchoice["six_source_refs"][k]) for k,v in choice["six_source_refs"].items()))
 ck("Source21_same_roster",derived["source_roster"]==oldderived["source_roster"] and len(derived["source_roster"])==21 and closure in derived["source_roster"])
 ck("v7_exact_pin_and_independent_review",pc["sources"][closure]["sha256"]=="1cc37f4fec48d2e2bae39db3c1f8d1da9fdfe6bd788a44396ea0a8b877be6777" and obj(Q/"HDF.json")["candidate_ref"]==pc["sources"][closure])
 ck("historical_canonical_unchanged",choice["canonical_at_source_preparation"]==oldchoice["canonical_at_source_preparation"])
 for v in choice["input_refs"]:ck("no_current_pin_"+v["path"],v["path"].casefold() not in canonical)
 tree=ast.parse(new);preds={}
 for n in ast.walk(nf["main"]):
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="require" and len(n.args)==2 and isinstance(n.args[1],ast.Constant):preds[n.args[1].value]=compile(ast.Expression(n.args[0]),"<independent-predicate>","eval")
 base=dict(schema="researchos.w09-c19-canonical-input-vector.v1",checkpoint_revision=366,refs=[])
 def schema(v):return eval(preds["CANONICAL_VECTOR_EXPLICIT_REVISION"],{},dict(vector=v))
 def rev(v,cp,ow):return eval(preds["EXACT_VECTOR_BOUND_CANONICAL_REVISIONS"],{},dict(vector=v,checkpoint_revision=cp,ownership_revision=ow))
 for cp,ow in [(1,1),(365,169),(366,170),(367,171),(2**60,2**61)]:
  v=dict(base,checkpoint_revision=cp);ck("positive_dynamic_"+str(cp),schema(v) and rev(v,cp,ow))
 for n,v in [("none",None),("list",[]),("empty",{}),("extra",dict(base,x=1)),("wrong_schema",dict(base,schema="x")),("missing",{k:v for k,v in base.items() if k!="refs"})]:
  ck("reject_vector_"+n,not schema(v))
 for v in [0,-1,True,False,"366",366.0,None]:
  ck("reject_vector_revision_"+repr(v),not schema(dict(base,checkpoint_revision=v)))
 for cp,ow in [(365,170),(True,170),(366.0,170),(366,0),(366,-1),(366,True),(366,"170"),(366,170.0),(366,None)]:
  ck("reject_content_revision_"+repr((cp,ow)),not rev(base,cp,ow))
 constants={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ("ROUTES","EXPECTED_NATIVE","EXPECTED_FORMAL","SELECTED","CHOICE_SHA","CHOICE_BYTES")}
 ck("two_routes",constants["ROUTES"]==(("test.research.fixture","W09","","C19"),("test.retrieval","W09","","C19")))
 ck("three_formal_five_native",constants["EXPECTED_FORMAL"]==["C19-01","C19-02","C19-03"] and constants["EXPECTED_NATIVE"]==["C19-01","C19-02","C19-03","C19-04","C19-05"])
 src=new.decode()
 for text in ["pre['canonical_input_vector_ref']==request['canonical_vector_ref'] and pre['refs']==vector['refs']","scope[field]==request[field]","'canonical_vector_ref','modes'","SAME_INDEPENDENT_MODE_REVIEW","MODE_NONAUTHOR","MODE_RUN_BINDING","REVIEW_SAME_RUN","REVIEW_OS","COMPLETE_RAW_PACKET_MAPPING","EXACT_FOUR_PRODUCER_GUARDS","ALL_INPUTS_REMAIN_EXACT","CONSUMER_GUARD_CLEANUP_FAILED","formal_case_count=1,formal_cases_accepted=0","new_Go_SQL_API_model_calls=0","canonical_written=False,Main_adopted=False","'TEMP':str(PRODUCER_TEMP),'TMP':str(PRODUCER_TEMP)"]:
  ck("retained_contract_"+text,text in src)
 for p in choice["fixed_future_paths"]:ck("future_consumer_path_absent_"+p,not Path(p).exists())
 ck("no_actual_execution_grant",contract["do_not_execute"] is True and contract["actual_ready"] is False and contract["actual_consumers_executed"] is False)
 ck("input_exact_while_held",all(pin(v["path"])==v for v in refs))
finally:
 cleanup=guard.close();save("source-guard.cleanup.actual.json",cleanup)
ck("actual_guard_closed",cleanup["closed"] is True and not cleanup["errors"] and cleanup["retained_handles_count"]==0)
save("input-pins.json",refs);save("checks.json",checks)
save("result.json",dict(status="SOURCE_ACCEPTED_PENDING_NEW_PRODUCER_QUALIFICATION_AND_ROOT_SCOPE",checks=len(checks),input_count=len(refs),formal_acceptance=False,execution_grant=False,actual_caller_consumer_or_native_executed=False,current_canonical_read_or_written=False,actual_source_read_guard=True,all_acquired_guards_closed=True))
print(json.dumps(dict(status="PASS",checks=len(checks),input_count=len(refs),result_ref=pin(N/"result.json"),cleanup_ref=pin(N/"source-guard.cleanup.actual.json"))))

