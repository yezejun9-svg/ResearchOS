import ast,hashlib,json,difflib
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");O=Path(__file__).parent
B=R/"execution/v2.4/receipts/W13/W13-03/desktop58_old_failed_lease_closure_cas_codex/5e2a75ea3da546b28b20975cc6a4d18f/lease_closure.v2.py"
REG=R/"execution/v2.4/receipts/W13/W13-03/desktop58_failed_lease_closure_cas_codex/b8aebcea794f4d83b6371e90814f8e3c"
P=R/"execution/v2.4/receipts/W13/W13-03/desktop58_failed_execution_root_closure_codex/93044794230d43ba9a169420a8cf45d1"
BASE=B.read_bytes();assert hashlib.sha256(BASE).hexdigest()=="23c31e297e9ba9ee3ba5a1ad2bbfe9bbf00499722edb633d100078835d8ad242"
def pin(p):
 p=Path(p);b=p.read_bytes();return {"path":p.relative_to(R).as_posix() if p.is_relative_to(R) else str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def jd(p):return json.loads(Path(p).read_bytes())
def write(n,v):
 with (O/n).open("xb") as f:f.write(v if isinstance(v,bytes) else (json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(O/n)
report=jd(P/"report.json");h=jd(P/"handoff.json")
bindingpath=R/"execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r337-b4d53db07f1e4ab8b9c0b37e291a6da5/binding.json"
b=jd(bindingpath);lock=jd(Path(b["toolchain_lock_ref"]["path"]))
canon=[pin(R/"execution/v2.4"/(s+".json")) for s in ("checkpoint","path_ownership","step_state","commands")]
assert canon==report["canonical_refs_unchanged"]
cp=jd(R/canon[0]["path"]);ow=jd(R/canon[1]["path"])
assert [cp["revision"],ow["revision"],len(cp["failure_counters"])]==[337,165,617]
assert not list(REG.iterdir())
pipeline=next(x for x in b["metadata_code_refs"] if "metadata_pipeline." in x["path"])
pending=report["pending_failure_origin_records"]
assert [x["failure_index"] for x in pending]==list(range(618,636))
q={"schema":"researchos.desktop58-failed-lease-closure-input.v1","actor":"codex:/root","namespace":REG.relative_to(R).as_posix(),"run_uuid":REG.name,"old_run_uuid":"b4d53db07f1e4ab8b9c0b37e291a6da5","before":[337,165,617],"after":[338,166,635],"main_head":b["main_git"]["head"],"main_git":b["main_git"],"canonical_before":canon,"binding_ref":pin(bindingpath),"closure_review_ref":pin(R/"execution/v2.4/receipts/W13/W13-03/desktop58_failed_execution_independent_review_codex/884be18fbe7248a693e64774987db31c/review.json"),"closure_report_ref":h["report_ref"],"closure_manifest_ref":h["manifest_ref"],"closure_handoff_ref":pin(P/"handoff.json"),"pending_origin_refs":[x["origin_ref"] for x in pending],"pipeline_ref":pipeline,"helper_ref":b["owned_process_helper_ref"],"python_pin":pin(lock["tools"]["python"]["path"]),"formal_increment":0,"source_execution_grant":False,"parent_acceptance_increment":0,"automatic_retry":False,"counter_reset":False}
old=BASE.decode()
header=old[:old.index("def need(")].replace('NS=ROOT/"execution/v2.4/receipts/W13/W13-03/desktop58_old_failed_lease_closure_cas_codex/5e2a75ea3da546b28b20975cc6a4d18f"','NS=ROOT/'+repr(q["namespace"]))
helpers=old[old.index("def need("):old.index("def draft(q):")]
githelpers=old[old.index("def job_ok(r):"):old.index("def commit(q,review_ref):")]
blocks=(O/"candidate-functions.txt").read_text(encoding="utf8")
code=(header+"\nINPUT_BASE="+repr(q)+"\n\n"+helpers+blocks.split("# INSERT_GIT_HELPERS\n")[0]+githelpers+blocks.split("# INSERT_GIT_HELPERS\n")[1]).encode()
tree=ast.parse(code)
source_ref=write("lease_closure.sixth.proposed.py",code)
template=dict(q,source_ref=source_ref,amended_at=None)
write("request.template.json",template)
d=list(difflib.unified_diff(old.splitlines(keepends=True),code.decode().splitlines(keepends=True),fromfile="lease_closure.v2.py",tofile="lease_closure.sixth.proposed.py"))
write("source.diff.json",d)
oldtree=ast.parse(old)
defs=lambda t:{x.name:ast.dump(x,include_attributes=False) for x in t.body if isinstance(x,ast.FunctionDef)}
od,nd=defs(oldtree),defs(tree)
preserved=[n for n in od if n not in ("draft","commit","main")]
assert all(od[n]==nd[n] for n in preserved)
ranges=lambda t,s:{x.name:"".join(s.splitlines(keepends=True)[x.lineno-1:x.end_lineno]) for x in t.body if isinstance(x,ast.FunctionDef)}
orng,nrng=ranges(oldtree,old),ranges(tree,code.decode())
assert all(orng[n]==nrng[n] for n in preserved)
# Reverse is explicit complete edit replacement, never run the candidate.
replaced=[{"name":n,"old":orng[n],"new":nrng[n]} for n in ("draft","commit","main")]
write("inverse.json",{"base_ref":pin(B),"candidate_ref":source_ref,"preserved_functions":preserved,"preserved_function_bytes_and_AST_equal":True,"replaced_functions":replaced,"header_old":old[:old.index("def need(")],"header_new":code.decode()[:code.decode().index("def need(")],"added_functions":[n for n in nd if n not in od],"complete_base_bytes_sha256":hashlib.sha256(BASE).hexdigest()})
write("static-audit.json",{"schema":"researchos.source-static-audit.v1","actor":"codex:/root/w05_merge_review","candidate_AST_parsed":True,"preserved_functions":preserved,"preserved_bytes_AST_equal":True,"input_transition":q["before"]+q["after"],"original_origins":len(pending),"actual_source_execution":False,"actual_draft":False,"actual_CAS":False,"actual_Git":False,"original_canonical_refs":canon,"baseline_ref":pin(B),"source_ref":source_ref})
print(json.dumps({"source_ref":source_ref,"base_ref":pin(B),"preserved":preserved,"origins":len(pending),"canonical":canon},ensure_ascii=False))

