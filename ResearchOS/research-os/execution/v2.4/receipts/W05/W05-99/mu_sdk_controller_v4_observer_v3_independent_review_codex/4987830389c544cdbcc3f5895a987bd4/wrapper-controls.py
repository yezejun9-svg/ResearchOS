import ast,copy,json,types
from pathlib import Path,PureWindowsPath
O=Path(__file__).resolve().parent
intake=json.loads((O/"intake.json").read_bytes());rows=intake["rows"]
r=next(x for x in rows if Path(x["source_ref"]["path"]).name=="controller.py")
raw=Path(r["snapshot_ref"]["path"]).read_bytes();tree=ast.parse(raw)
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="launch_reviewed_phase")
required=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="require")
class P:
 def __init__(self,p):self.p=PureWindowsPath(p.p if isinstance(p,P) else str(p))
 def __truediv__(self,p):return P(self.p/str(p))
 def __eq__(self,p):return isinstance(p,P) and self.p==p.p
 def __str__(self):return str(self.p)
 def resolve(self):return self
 @property
 def parent(self):return P(self.p.parent)
tuple_refs=intake["tuple"];helper=intake["helper_refs"];events=[];mode={}
review={"schema":"researchos.mu-sdk-controller-observer-independent-source-review.v2","decision":"READY_SOURCE_ONLY","actor_id":"codex:/root/command_queue_impl","formal_acceptance":False,**copy.deepcopy(tuple_refs)}
seed={"phase_ready_for_execution":True,"controller_source_review":{"path":"D:\\review-only\\independent-review.json","sha256":"1"*64,"bytes":123},"runner_source":copy.deepcopy(tuple_refs["runner_source_ref"]),"observer_source":copy.deepcopy(tuple_refs["observer_source_ref"]),"python_binary":copy.deepcopy(tuple_refs["python_binary_ref"])}
class Guard:
 def __init__(self):self.held=False
 def acquire(self,refs):
  events.append(("acquire",copy.deepcopy(refs)))
  if mode.get("acquire_fail"):raise RuntimeError("independent simulated held-pin mismatch")
  self.held=True
 def get_buffer(self,p):return b"changed review" if mode.get("review_changed") else json.dumps(current_review).encode()
 def close(self):
  events.append(("close",self.held));self.held=False
  return {"closed":True,"errors":[]}
def pure_pinned(ref):
 events.append(("pinned_review",copy.deepcopy(ref)))
 return P(ref["path"]),json.dumps(current_review).encode()
def pure_module(ref,name):events.append(("guard_module",copy.deepcopy(ref)));return types.SimpleNamespace(SourceReadGuard=Guard)
def inner_stub(s,g):
 events.append(("inner_holds_guard",g.held))
 if not g.held:raise RuntimeError("unheld guard")
 return "memory-only-inner-result"
env={"Path":P,"__file__":tuple_refs["controller_source_ref"]["path"],"HERE":P(tuple_refs["controller_source_ref"]["path"]).parent,"pinned":pure_pinned,"json":json,"module":pure_module,"_launch_reviewed_phase_with_guard":inner_stub,"PINNED_PYTHON_REF":tuple_refs["python_binary_ref"],**helper}
exec(compile(ast.Module(body=[required,fn],type_ignores=[]),"<C4 wrapper AST using inert memory guard and inner stub>","exec"),env)
cases=[]
def run(name,mutator=None,want_accept=False,newmode=None):
 global current_review
 current_review=copy.deepcopy(review);s=copy.deepcopy(seed);events.clear();mode.clear();mode.update(newmode or {})
 if mutator:mutator(current_review,s)
 error=None;value=None
 try:value=env["launch_reviewed_phase"](s)
 except RuntimeError as exc:error=str(exc)
 accepted=value=="memory-only-inner-result"
 cases.append({"case":name,"expected_accept":want_accept,"accepted":accepted,"matches_expected":accepted==want_accept,"error":error,"events":copy.deepcopy(events)})
run("SIX_REFS_AND_ALL_HELPERS_HELD_THROUGH_INNER",want_accept=True)
actualrefs=cases[0]["events"][2][1]
assert len(actualrefs)==11
assert all(r in actualrefs for r in tuple_refs.values())
assert all(r in actualrefs for r in helper.values())
assert seed["controller_source_review"] in actualrefs
for actor in ("codex:/root","codex:/root/w05_merge_review","",None):
 run("REJECT_NONINDEPENDENT_ACTOR_"+str(actor),lambda r,s,a=actor:r.update(actor_id=a))
run("REJECT_OLD_SCHEMA",lambda r,s:r.update(schema="researchos.mu-sdk-controller-observer-independent-source-review.v1"))
run("REJECT_REQUEST_CHANGES",lambda r,s:r.update(decision="REQUEST_CHANGES"))
run("REJECT_FORMAL_ACCEPTANCE_TRUE",lambda r,s:r.update(formal_acceptance=True))
run("REJECT_PHASE_NOT_READY",lambda r,s:s.update(phase_ready_for_execution=False))
run("REJECT_FOREIGN_RUNNER_REF",lambda r,s:r["runner_source_ref"].update(sha256="a"*64))
run("REJECT_FOREIGN_OBSERVER_REF",lambda r,s:r["observer_source_ref"].update(sha256="a"*64))
run("REJECT_FOREIGN_PYTHON_PIN_EVEN_IF_SEED_EQUALS_REVIEW",lambda r,s:(r["python_binary_ref"].update(sha256="a"*64),s["python_binary"].update(sha256="a"*64)))
for key in ("controller_source_ref","hooks_source_ref","phase_worker_source_ref"):
 run("REJECT_FOREIGN_"+key,lambda r,s,k=key:r[k].update(path="D:\\foreign\\source.py"))
run("HELD_PIN_ACQUISITION_FAILURE_BLOCKS_INNER",newmode={"acquire_fail":True})
run("REVIEW_CHANGED_BEFORE_GUARD_ACQUIRE_BLOCKS_INNER",newmode={"review_changed":True})
assert all(c["matches_expected"] for c in cases)
report={"schema":"researchos.c4-independent-wrapper-controls.v1","cases":cases,"count":len(cases),"matched":sum(c["matches_expected"] for c in cases),"candidate_module_imports":0,"actual_candidate_entry_calls":0,"real_source_guards_acquired":0,"actual_WinAPI_calls":0,"scope":"Selected wrapper AST only with pure path adapter, JSON review bytes, inert guard module, stubbed inner body. Tests decision, identity and guard ordering; does not prove actual OS locks."}
(O/"wrapper-controls.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"count":len(cases),"matched":report["matched"],"guarded_reference_count":11}))

