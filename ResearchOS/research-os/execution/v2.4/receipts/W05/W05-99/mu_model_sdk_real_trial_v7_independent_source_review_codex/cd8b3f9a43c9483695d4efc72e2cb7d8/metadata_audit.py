"""Independent v7 byte/AST and finite in-memory data controls; no product entry point."""
import ast,copy,difflib,hashlib,json,re,sys
from datetime import datetime,timezone
from pathlib import Path
sys.dont_write_bytecode=True
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v7_independent_source_review_codex/cd8b3f9a43c9483695d4efc72e2cb7d8")
SRC=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_model_sdk_real_trial_v7_source_codex/73cdde53fe0e4da2ae29fb6898d4b7ef")
def pin(p):
 raw=Path(p).read_bytes(); return {"path":str(Path(p)).replace("\\","/"),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def doc(p): return json.loads(Path(p).read_bytes())
def verify(ref):
 actual=pin(ref["path"]); return {"expected":ref,"actual":actual,"matches":actual["sha256"]==ref["sha256"] and actual["bytes"]==ref["bytes"]}
h=doc(SRC/"handoff.json"); mf=doc(SRC/"manifest.json"); iv=doc(SRC/"source-inverse.json")
members=[verify(r) for r in mf["members"]]
external=[verify(r) for r in [iv["basis_ref"],h["review_ref"],h["unchanged_cli_producer_ref"],*h["unchanged_four_go_refs"]]]
old=Path(iv["basis_ref"]["path"]).read_text(encoding="utf-8"); new=Path(h["candidate_ref"]["path"]).read_text(encoding="utf-8")
def defs(s):
 lines=s.splitlines(keepends=True)
 return {n.name:(ast.dump(n,include_attributes=False),"".join(lines[n.lineno-1:n.end_lineno]),n.lineno,n.end_lineno)
         for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a,b=defs(old),defs(new)
unchanged=[n for n in a if n in b and a[n][:2]==b[n][:2]]
changed=[n for n in a if n in b and a[n][:2]!=b[n][:2]]
def regen(ref,left,right):
 raw=Path(ref["path"]).read_bytes(); head=raw.decode("utf-8").splitlines(keepends=True)
 gen="".join(difflib.unified_diff(left.splitlines(keepends=True),right.splitlines(keepends=True),fromfile=head[0][4:].rstrip("\r\n"),tofile=head[1][4:].rstrip("\r\n"))).encode()
 return {"ref":ref,"exact":raw==gen}
delta=list(difflib.ndiff(old.splitlines(keepends=True),new.splitlines(keepends=True)))
inverse={"forward":regen(iv["forward_diff_ref"],old,new),"reverse":regen(iv["reverse_diff_ref"],new,old),
 "restore_v6_exact":"".join(difflib.restore(delta,1))==old,"restore_v7_exact":"".join(difflib.restore(delta,2))==new,
 "unchanged_definitions_byte_ast":unchanged,"changed_definitions":changed}
names={"require","strict_consumed_json","original_cli_summary_stream","verified_cli_context_transition","verified_cli_draft_goal_transition",
 "object_by_id","exact_ref","object_by_ref","exact_artifact_ref","budget_chain","verify_ordinary_goal_graph"}
nodes=[n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef) and n.name in names]
space={"json":json,"re":re,"datetime":datetime,"timezone":timezone}
exec(compile(ast.Module(body=nodes,type_ignores=[]),"<independent-pure-data-functions>", "exec"),space)
text=(SRC/"precheck_stream_final.py").read_text(encoding="utf-8"); tree=ast.parse(text)
old_assignment=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="old" for t in n.targets))
old_context=ast.literal_eval(old_assignment.value); old_context["session_id"]="session-A"
fixture=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="fixture")
fx={"json":json,"old":old_context}
exec(compile(ast.Module(body=[fixture],type_ignores=[]),"<data-fixture-builder>","exec"),fx)
stream,post=fx["fixture"]("cli-run",4)
stream[-1]["operations"][0]["method"]="session.get"
stream[-1]["operations"][0]["result"]["snapshot"].update(goal_id="draft-goal",goal_status="DRAFT",active_run_id=None)
stream[-1]["operations"][-1]["result"]["snapshot"].update(goal_id="goal-A",goal_status="ACTIVE",active_run_id="run-A")
stream[-1]["last_verified_session_snapshot"].update(goal_status="ACTIVE")
controls=[]
def record(name,fn,expected_accept):
 try: fn(); accepted=True; error=None
 except (ValueError,KeyError,TypeError,AssertionError) as e: accepted=False; error=type(e).__name__+":"+str(e)
 controls.append({"name":name,"accepted":accepted,"expected_accept":expected_accept,"condition_satisfied":accepted is expected_accept,"error":error})
v=space["verified_cli_context_transition"]
record("session.get -> new Goal terminal with complete target and Artifact ref",lambda:v("cli-run",old_context,stream,post),True)
for field in ("goal_id","active_run_id"):
 for missing in (False,True):
  bad=copy.deepcopy(stream)
  if missing: bad[-1]["last_verified_session_snapshot"].pop(field)
  else: bad[-1]["last_verified_session_snapshot"][field]="foreign"
  record(("missing" if missing else "foreign")+" terminal "+field,lambda bad=bad:v("cli-run",old_context,bad,post),False)
for field in ("goal_id","task_id","run_id"):
 bad=copy.deepcopy(stream); bad[-1]["execution"].pop(field)
 record("missing execution "+field,lambda bad=bad:v("cli-run",old_context,bad,post),False)
for field,value in (("entity_type","Task"),("revision",True),("revision",2.0),("revision",0),("content_hash",""),("content_hash","sha256:wrong")):
 bad=copy.deepcopy(stream); bad[-2]["event"]["payload"]["artifact_ref"][field]=value
 record("AVAILABLE "+field+"="+repr(value),lambda bad=bad:v("cli-run",old_context,bad,post),False)
bad=copy.deepcopy(stream); duplicate=copy.deepcopy(bad[-2]); duplicate["event"].update(sequence=5,event_id="conflicting5"); duplicate["event"]["payload"]["artifact_ref"]["revision"]=3
bad.insert(-1,duplicate); bad[-1]["execution"]["event_sequence"]=5; bad[-1]["last_verified_session_snapshot"]["event_sequence"]=5
record("same id conflicting AVAILABLE version",lambda:v("cli-run",old_context,bad,post),False)
graph_tree=ast.parse((SRC/"precheck_graph_final.py").read_text(encoding="utf-8")); gx={"json":json}
policy=next(n for n in graph_tree.body if isinstance(n,ast.FunctionDef) and n.name=="policy")
exec(compile(ast.Module(body=[policy],type_ignores=[]),"<policy-values>","exec"),gx)
for n in graph_tree.body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ("objects","host","summary","doc","before","artifact_ref","stream_evidence","old_context","saved","snapshot","draft_row","post"):
  exec(compile(ast.Module(body=[n],type_ignores=[]),"<fixture-values>","exec"),gx)
# Separate physical row project/version indexes, to exercise a real historical/current split.
class MemoryRows:
 def __init__(self,objects,versions=None):
  self.objects=objects
  self.versions=versions if versions is not None else {("P",k,i,obj["revision"]):copy.deepcopy(obj) for (k,i),obj in objects.items() if k=="Artifact"}
 def execute(self,query,args):
  if query.startswith("SELECT id FROM domain_objects"):
   project,kind=args
   return [(i,) for (k,i),obj in self.objects.items() if k==kind and obj.get("project","P")==project]
  if query.startswith("SELECT body FROM domain_objects"):
   kind,identity,*project=args; obj=self.objects.get((kind,identity))
   return [(json.dumps(obj),)] if obj is not None and (not project or obj.get("project","P")==project[0]) else []
  if query.startswith("SELECT body FROM domain_versions"):
   project,kind,identity,revision=args; obj=self.versions.get((project,kind,identity,revision))
   return [(json.dumps(obj),)] if obj is not None else []
  raise AssertionError("unexpected SQL in memory stub")
objects=copy.deepcopy(gx["objects"]); db=MemoryRows(objects)
draft=space["budget_chain"](db,"P","G0","DRAFT")
graph=space["verify_ordinary_goal_graph"]
def graph_call(rows,refs=None,versions=None):
 return graph(MemoryRows(rows,versions),gx["doc"],gx["before"],gx["summary"],{"goal_id":"G0"},{"goal_id":"G1"},draft,refs if refs is not None else gx["stream_evidence"])
record("same original Artifact EntityRef -> historical + current DB version",lambda:graph_call(objects),True)
for field,value in (("revision",True),("revision",2.0),("revision",1),("entity_type","Task"),("content_hash","sha256:"+"b"*64)):
 refs=copy.deepcopy(gx["stream_evidence"]); refs["result_artifact_refs"]["A1"][field]=value
 record("graph original Artifact "+field+"="+repr(value),lambda refs=refs:graph_call(objects,refs),False)
versions={("P","Artifact","A1",2):copy.deepcopy(objects[("Artifact","A1")])}
for field,value in (("revision",3),("content_hash","sha256:"+"b"*64),("project","foreign")):
 current=copy.deepcopy(objects); current[("Artifact","A1")][field]=value
 record("old historical matching ref but current Artifact "+field+" differs",lambda current=current:graph_call(current,versions=versions),False)
refs=copy.deepcopy(gx["stream_evidence"]); refs["result_artifact_refs"]["foreign"]=refs["result_artifact_refs"]["A1"]
record("extra foreign result Artifact key",lambda:graph_call(objects,refs),False)
record("missing result Artifact vector",lambda:graph_call(objects,{"result_artifact_refs":{}}),False)
record("DRAFT admission saves context without terminal Run or final follow snapshot",lambda:space["verified_cli_draft_goal_transition"]({"_init_project_id":"P"},gx["old_context"],[gx["draft_row"]],gx["post"]),True)
source_lines=new.splitlines()
audit={"schema":"researchos.mu-sdk-v7-independent-source-audit.v1","actor_id":"codex:/root/f08_whole_scope_review",
 "candidate_ref":h["candidate_ref"],"manifest_members":members,"member_count":len(members),"members_all_exact":all(x["matches"] for x in members),
 "external_inputs":external,"external_all_exact":all(x["matches"] for x in external),"whole_inverse":inverse,
 "new_import_re_only":list(difflib.unified_diff(old.splitlines(),new.splitlines(),n=0))[:8],
 "definitions":{"original_cli_summary_stream":b["original_cli_summary_stream"][2:],"verify_ordinary_goal_graph":b["verify_ordinary_goal_graph"][2:],"main":b["main"][2:]},
 "ordinary_db_graph_consumes_original_stream_ref_vector":'stream_evidence = run_invocation["consumed_file_transition"]["context_evidence"]["stream_evidence"]' in new,
 "independent_pure_data_controls":controls,"all_controls_expected":all(x["condition_satisfied"] for x in controls),
 "previous_3requests_8192tokens_300s_root_authority_guards_unchanged":all(n in unchanged for n in ("authority_binding","validate_input","phase_basis","authorized_child","command_once")),
 "bootstrap_and_unknown_ledger_guards_unchanged":all(n in unchanged for n in ("verified_cli_draft_goal_transition","budget_chain","model_ledgers","exact_qualification")),
 "candidate_module_imported":False,"candidate_main_executed":False,"real_sql_executed":False,"go_cli_sdk_model_calls":0,"canonical_writes":0,"formal_delta":0}
with (BASE/"audit.json").open("xb") as f: f.write((json.dumps(audit,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
print(json.dumps({"audit_ref":pin(BASE/"audit.json"),"members":len(members),"members_exact":audit["members_all_exact"],"external_exact":audit["external_all_exact"],"whole_inverse":{"forward":inverse["forward"]["exact"],"reverse":inverse["reverse"]["exact"],"restore_v6":inverse["restore_v6_exact"],"restore_v7":inverse["restore_v7_exact"]},"unchanged":len(unchanged),"changed":changed,"control_count":len(controls),"unexpected":[x for x in controls if not x["condition_satisfied"]],"definitions":audit["definitions"]},ensure_ascii=False))

