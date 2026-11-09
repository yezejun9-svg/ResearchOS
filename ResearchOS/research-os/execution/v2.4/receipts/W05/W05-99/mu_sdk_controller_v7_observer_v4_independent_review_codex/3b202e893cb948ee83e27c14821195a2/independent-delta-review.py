import ast,copy,difflib,hashlib,json,re
from pathlib import Path
O=Path(__file__).resolve().parent;B=Path(r"D:\作品集\ResearchOS\research-os\execution\v2.4\receipts\W05\W05-99")
C=B/"mu_sdk_controller_revision_v7_codex/eb109cbc91534fffa3cbe2bd72919d5b"
rows=[];seen=set()
def ref(p,b=None):
 p=Path(p);b=p.read_bytes() if b is None else b
 return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def read(p,expected=None):
 p=Path(p);raw=p.read_bytes();r=ref(p,raw)
 if expected:assert r["sha256"]==expected["sha256"] and r["bytes"]==expected["bytes"],str(p)
 if str(p) not in seen:
  target=O/"snapshots"/(r["sha256"]+".raw");target.parent.mkdir(exist_ok=True)
  if not target.exists():target.write_bytes(raw)
  rows.append({"source_ref":r,"snapshot_ref":ref(target,raw)});seen.add(str(p))
 return raw
def rr(r):return read(r["path"],r)
def put(n,value):
 p=O/n;p.write_bytes((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode());return ref(p)
h=json.loads(read(C/"handoff.json",{"sha256":"1be3853e1497a6d79dbf2dce87a0ffdf3946f4279579c121965e9ec5b9803985","bytes":3595}))
m=json.loads(rr(h["manifest_ref"]))
for item in m["members"]:rr(item)
pins=json.loads(rr(h["source_pins_ref"]))
for section in ("inputs","sources"):
 for item in pins[section].values():rr(item)
ph=json.loads(rr(h["independent_c6_o4_review_ref"]))
prior=json.loads(rr(ph["review_ref"]))
rr(ph["controls_ref"]);rr(ph["findings_ref"])
oldref=prior["controller_source_ref"];old=rr(oldref);new=rr(h["controller_source_ref"])
for item in prior["additional_dependencies"]:rr(item)
for name in ("runner_source_ref","observer_source_ref","python_binary_ref"):rr(prior[name])
cases=[]
def add(name,ok,**details):
 assert ok,name
 cases.append({"case":name,"pass":bool(ok),**details})
def apply(before,diff):
 oldlines=before.decode().splitlines(keepends=True);lines=diff.decode().splitlines(keepends=True);out=[];at=0;i=2
 while i<len(lines):
  match=re.match(r"@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@",lines[i]);assert match
  start=max(0,int(match.group(1))-1);out+=oldlines[at:start];at=start;i+=1
  while i<len(lines) and not lines[i].startswith("@@ "):
   tag,body=lines[i][0],lines[i][1:]
   if tag in (" ","-"):assert oldlines[at]==body;at+=1
   if tag in (" ","+"):out.append(body)
   i+=1
 out+=oldlines[at:];return "".join(out).encode()
forward=rr(h["forward_diff_ref"]);inverse=rr(h["inverse_diff_ref"])
assert apply(old,forward)==new and apply(new,inverse)==old
expected_diff="".join(difflib.unified_diff(old.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True),fromfile="before",tofile="after")).encode()
assert expected_diff.splitlines(keepends=True)[2:]==forward.splitlines(keepends=True)[2:]
nt=ast.parse(new);oldtree=ast.parse(old)
inner=next(n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name=="_launch_reviewed_phase_with_guard")
callback=next(n for n in inner.body if isinstance(n,ast.FunctionDef) and n.name=="before_resume")
assignment=next(n for n in callback.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="context" for t in n.targets))
actual_pairs={ast.literal_eval(k):v for k,v in zip(assignment.value.keys,assignment.value.values)}
added={"canonical_transactions_source":"CANONICAL_TRANSACTION_REF","job_watchdog_source":"JOB_WATCHDOG_REF",
 "source_guard_source":"SOURCE_READ_GUARD_REF","base_owned_process_source":"BASE_OWNED_PROCESS_REF"}
add("ACTUAL_CALLBACK_EXACT_FOUR_SOURCE_KEYS",all(k in actual_pairs and isinstance(actual_pairs[k],ast.Name) and actual_pairs[k].id==v for k,v in added.items()) and len(actual_pairs)==len(assignment.value.keys),line=assignment.lineno)
stripped=copy.deepcopy(nt);sin=next(n for n in stripped.body if isinstance(n,ast.FunctionDef) and n.name==inner.name)
scb=next(n for n in sin.body if isinstance(n,ast.FunctionDef) and n.name=="before_resume")
sa=next(n for n in scb.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="context" for t in n.targets))
pairs=[(k,v) for k,v in zip(sa.value.keys,sa.value.values) if ast.literal_eval(k) not in added]
sa.value.keys=[k for k,v in pairs];sa.value.values=[v for k,v in pairs]
add("REMOVE_FOUR_FIELDS_RESTORES_COMPLETE_C6_AST_AND_BYTES",ast.dump(stripped,include_attributes=False)==ast.dump(oldtree,include_attributes=False),full_forward_inverse_bytes=True,independent_hunks_equal=True)
oldC=Path(oldref["path"]).parent
helper_records={}
for name in pins["unmodified_helper_bytes"]:
 oldbytes=read(oldC/name);newbytes=read(C/name);helper_records[name]=oldbytes==newbytes
 assert helper_records[name],name
# Pure top-level constants only, using this exact C7 __file__ for HERE relocation.
env={"Path":Path,"__file__":str(C/"controller.py")}
assignments=[n for n in nt.body if isinstance(n,ast.Assign) and all(isinstance(t,ast.Name) for t in n.targets)]
exec(compile(ast.Module(body=assignments,type_ignores=[]),"<C7 constants AST only>","exec"),env)
selected=[n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name in ("require","expected_source_provenance","require_non_author","validate_review_actor")]
exec(compile(ast.Module(body=selected,type_ignores=[]),"<C7 pure review gates AST>","exec"),env)
localrefs={"CANONICAL_TRANSACTION_REF":"canonical_transactions.py","JOB_WATCHDOG_REF":"job_deadline_watchdog.py","CLEANUP_PRODUCER_REF":"held_job_cleanup_producer.py"}
add("SIX_HELPERS_IDENTICAL_AND_LOCAL_PINS_RELOCATED",all(helper_records.values()) and all(env[k]==ref(C/name) for k,name in localrefs.items()),helpers=helper_records)
t={k:copy.deepcopy(prior[k]) for k in ("controller_source_ref","observer_source_ref","hooks_source_ref","runner_source_ref","phase_worker_source_ref","python_binary_ref","cleanup_producer_source_ref")}
t.update(controller_source_ref=h["controller_source_ref"],hooks_source_ref=ref(C/"owned_job_hooks.py"),
 phase_worker_source_ref=ref(C/"phase_worker.py"),cleanup_producer_source_ref=env["CLEANUP_PRODUCER_REF"])
contexts={"controller_source":t["controller_source_ref"],"observer_source":t["observer_source_ref"],
 "hooks_source":t["hooks_source_ref"],"phase_worker_source":t["phase_worker_source_ref"],"runner_source":t["runner_source_ref"],
 "canonical_transactions_source":env["CANONICAL_TRANSACTION_REF"],"job_watchdog_source":env["JOB_WATCHDOG_REF"],
 "source_guard_source":env["SOURCE_READ_GUARD_REF"],"base_owned_process_source":env["BASE_OWNED_PROCESS_REF"],
 "cleanup_producer_source":t["cleanup_producer_source_ref"],"python_binary":t["python_binary_ref"]}
for item in contexts.values():rr(item)
review={"schema":"researchos.mu-sdk-controller-observer-independent-source-review.v2","decision":"READY_SOURCE_ONLY",
 "actor_id":"codex:/root/command_queue_impl","callback_contract":"REAL_ASSIGNED_SUSPENDED_FRAME_BEFORE_FIRST_RESUME",
 "formal_acceptance":False,**t,"source_provenance":env["expected_source_provenance"](contexts)}
obst=ast.parse(rr(t["observer_source_ref"]));oe={}
for n in obst.body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in (
  "SOURCE_AUTHOR_POLICY","SOURCE_PROVENANCE_SCHEMA","RUNNER_REF","ROOT_ACTOR","AUTHOR","ACTOR"):
  oe[n.targets[0].id]=ast.literal_eval(n.value)
fns=[n for n in obst.body if isinstance(n,ast.FunctionDef) and n.name in ("require","source_author_provenance","validate_source_review")]
exec(compile(ast.Module(body=fns,type_ignores=[]),"<unchanged O4 pure gates AST>","exec"),oe)
byname={Path(v["path"]).name:v for v in contexts.values()}
seed={"phase_ready_for_execution":True,"runner_source":t["runner_source_ref"],"observer_source":t["observer_source_ref"],
 "controller_source_review":{"synthetic":"unissued in-memory review test only"},"python_binary":t["python_binary_ref"]}
callback_env={**env,"doc":{"outer_job_contract":{"synthetic":True}},"controller_ref":t["controller_source_ref"],
 "pin":lambda p:copy.deepcopy(byname[Path(p).name]),"phase_dir":Path("D:/synthetic-not-created"),
 "public_env":{},"seed":seed}
actual=eval(compile(ast.Expression(assignment.value),"<actual C7 callback context expression>","eval"),callback_env)
oe["validate_source_review"](review,actual)
old_context={k:v for k,v in actual.items() if k not in added}
prior_failure=None
try:oe["validate_source_review"](review,old_context)
except KeyError as ex:prior_failure=str(ex)
add("ACTUAL_C7_CONTEXT_PASSES_UNCHANGED_O4_GATE",review["source_provenance"]==oe["source_author_provenance"](actual) and prior_failure=="'canonical_transactions_source'",prior_counterexample_reproduced=prior_failure,source_provenance=review["source_provenance"])
# Original entry prefix through author-policy validation; stop before module/guard imports.
outer=next(n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name=="launch_reviewed_phase")
cut=next(i for i,n in enumerate(outer.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="references" for t in n.targets))
gate_env={**env,"source_owner":object(),"_require_source_owner":lambda value:None,
 "seed":seed,"json":json,"pinned":lambda value:(Path("D:/synthetic-not-created"),json.dumps(review).encode())}
exec(compile(ast.Module(body=outer.body[:cut],type_ignores=[]),"<C7 actual pre-import review prefix AST>","exec"),gate_env)
add("ACTUAL_C7_PREIMPORT_GATE_ACCEPTS_CURRENT_TUPLE",gate_env["tuple_context"]==contexts,import_or_WinAPI_performed=False)
summary={"total":len(cases),"passed":len(cases),"counterexamples":0}
put("independent-delta-controls.json",{"schema":"researchos.c7-independent-delta-controls.v1","summary":summary,
 "cases":cases,"candidate_module_imports":0,"actual_candidate_entry_calls":0,"real_WinAPI_SQL_provider_calls":0,
 "real_threads_started":0,"Main_canonical_writes":0,"author_controls_executed":0,
 "scope":"Exact four-field callback delta, current namespace pins and unchanged O4 pure gate. Prior 67 C6/O4 controls and components are reused, not rerun."})
put("intake.json",{"schema":"researchos.c7-independent-narrow-intake.v1","controller_handoff_ref":ref(C/"handoff.json"),
 "controller_manifest_ref":h["manifest_ref"],"prior_review_handoff_ref":h["independent_c6_o4_review_ref"],
 "prior_review_ref":ph["review_ref"],"prior_controls_ref":ph["controls_ref"],"prior_findings_ref":ph["findings_ref"],
 "review_fields":review,"source_context":contexts,"summary":summary,"rows":rows})
print(json.dumps({"summary":summary,"source_inputs":len(rows),"finding_C6_O4_R01":"CLOSED_IN_SOURCE","scope":"SOURCE_ONLY_NO_NATIVE_GRANT"},ensure_ascii=False,indent=2))

