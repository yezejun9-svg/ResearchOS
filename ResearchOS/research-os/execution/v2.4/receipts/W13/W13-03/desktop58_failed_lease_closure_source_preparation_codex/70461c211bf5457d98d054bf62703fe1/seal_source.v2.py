import json,hashlib,difflib,ast
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");O=Path(__file__).parent
def ref(p):
 b=p.read_bytes();return {"path":p.relative_to(R).as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write(n,d):
 with (O/n).open("xb") as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+"\n").encode())
 return ref(O/n)
s=O/"lease_closure.sixth.proposed.py";new=s.read_bytes();q=json.loads((O/"request.template.json").read_bytes())
base=R/"execution/v2.4/receipts/W13/W13-03/desktop58_old_failed_lease_closure_cas_codex/5e2a75ea3da546b28b20975cc6a4d18f/lease_closure.v2.py";old=base.read_bytes()
delta=list(difflib.ndiff(old.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True)))
assert "".join(difflib.restore(delta,1)).encode()==old and "".join(difflib.restore(delta,2)).encode()==new
assert json.loads((O/"whole-byte-inverse.json").read_bytes())=={"base_ref":ref(base),"source_ref":ref(s),"ndiff":delta,"reverse_exact":True,"forward_exact":True}
inv=ref(O/"whole-byte-inverse.json")
checks=[]
def ck(n,v):checks.append({"name":n,"pass":bool(v)})
def p(x):
 p=Path(x);return p if p.is_absolute() else R/p
def walk(x):
 if isinstance(x,dict):
  if set(x)=={"path","sha256","bytes"}:yield x
  else:
   for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
for r in walk(q):
 b=p(r["path"]).read_bytes();ck("actual input pin:"+r["path"],len(b)==r["bytes"] and hashlib.sha256(b).hexdigest()==r["sha256"])
tree=ast.parse(new);defs={x.name:x for x in tree.body if isinstance(x,ast.FunctionDef)}
text=new.decode()
ck("only two CAS targets",text.count("os.replace(tmp,target)")==1 and 'enumerate(CANON[:2])' in text)
ck("one source and request preflight before draft/commit",text.index('context=preflight(q,a.request_sha256,a.source_sha256)')<text.index('if a.draft: draft(q,context)'))
ck("exact prepared literal",'"prepared.v2.json"' not in text and '"prepared.json"' in text)
ck("removed old fifth special failure","fifth_binding_ref" not in text and "fifth_registry" not in text and "failure-origin-614.original.json" not in text)
ck("Git callsites exactly4 =12 owned readonly",text.count('git_guard(q,b,"commit.')==3 and 'enumerate(CANON[:2])' in text)
ck("selected18 exact pending",len(q["pending_origin_refs"])==18)
ck("input timestamp needs Root",q["amended_at"] is None)
ck("ROOT actual output untouched",not list((R/q["namespace"]).iterdir()))
ck("all current canon bytes unchanged",all(hashlib.sha256(p(r["path"]).read_bytes()).hexdigest()==r["sha256"] for r in q["canonical_before"]))
ck("No reviewed gate relaxation",q["formal_increment"]==q["parent_acceptance_increment"]==0 and q["source_execution_grant"] is False)
assert all(x["pass"] for x in checks)
audit=write("final-static-audit.json",{"schema":"researchos.source-static-audit.v1","author":"codex:/root/w05_merge_review","checks":checks,"pass":True,"candidate_imported_or_executed":False,"actual_draft":False,"actual_CAS":False,"actual_native_Git":False,"new_failure_count":1})
contract=write("execution-contract.json",{"schema":"researchos.desktop58-failed-lease-closure-source-contract.v1","source_ref":ref(s),"owner":"codex:/root","namespace":q["namespace"],"input_path":q["namespace"]+"/original-input.json","input_template_ref":ref(O/"request.template.json"),"input_materialization":"Root copies request template, fills amended_at with explicit UTC timestamp, keeps actual source_ref; creates original-input.json once and pins exact raw SHA. No request has been written to Root output by this author.","draft_argv":[q["python_pin"]["path"],"-I","-S","-X","utf8",str(s),"--request-sha256","<actual original-input.json sha256>","--source-sha256",ref(s)["sha256"],"--draft"],"commit_argv":[q["python_pin"]["path"],"-I","-S","-X","utf8",str(s),"--request-sha256","<same actual original-input.json sha256>","--source-sha256",ref(s)["sha256"],"--commit-review-ref","<exact JSON {path,sha256,bytes} of actual F08 review>"],"independent_commit_review_contract":{"schema":"researchos.desktop58-failed-lease-closure-cas-review.v1","reviewer":"codex:/root/f08_whole_scope_review","decision":"READY_FOR_ROOT_OLD_FAILED_LEASE_CLOSURE_CAS_ONCE","requested_changes":[],"actual_registration_executed":False,"expected_before":q["before"],"expected_after":q["after"],"required_actual_ref_fields":["source_ref","prepared_ref","input_ref","audit_ref","manifest_ref","original_refs","desired_refs"]},"permissions":{"draft":"new Root receipt files and original pipeline opaque validator only; no Git/canonical/product","commit":"12 owned readonly Git commands (4 groups of head/status/index,30s each), exact2 CP/OW replacements; SS/CM byte-preserved","no_retry":True,"no_new_execution_grant":True,"formal_increment":0},"pure_metadata_controls_recommended":["Before any candidate run, independently compare request exact field set and all pins, reject changed before/after/origin ordering/source SHA.","Prepare actual once; independently inspect exactCP/OW pointer diff and unchanged SS/CM; negative review cases mismatched source/input/prepared/desired refs must reject before commit.started or nativeGit.","A separate review must exercise or statically establish partial-CAS failure stops forward-only with intent preserved; do not replay failed input."],"source_only":True})
report=write("report.json",{"schema":"researchos.source-preparation-report.v1","author":"codex:/root/w05_merge_review","decision":"SOURCE_PREPARATION_COMPLETE_PENDING_INDEPENDENT_REVIEW","source_ref":ref(s),"base_ref":ref(base),"whole_inverse_ref":inv,"static_audit_ref":audit,"execution_contract_ref":contract,"before":q["before"],"after":q["after"],"scope":"Only close failed b4d lease and append18 original opaque origins618..635; 636+ remain outside cut, never deleted or registered here.","preserved_functions":["need","safe","parse","encode","pin","verify","doc","save","copy_bytes","load_module","differences","job_ok","git_guard"],"changes":["New immutable actual input anchors/current337 canonical refs. Previous336 binding used only for toolchain/helper/Main facts/430 prefix.","All exact input refs/value/source/request hashes and failed execution identity validated before any sentinel/helper/native/temp/CAS.","Explicit --draft and --commit-review-ref; consistent prepared.json and actual F08 independent approval bound to complete prepared targets.","Recompute desired bytes before commit; only CP/OW narrow state/ref/revisions and append18; explicit lease execution_grant/qualification false/formal0.","Keep before/pre-replace0/pre-replace1/after12 owned readonly Git guards and immediate four-file byte checks; no automatic retry/rollback."],"baseline_execution_closure_ref":q["closure_review_ref"],"self_review_or_acceptance":False,"candidate_executed":False,"actual_draft":False,"actual_CAS":False,"product_execution_calls":0,"formal_increment":0,"new_failure_count":1,"remaining":["Source proposal requires non-author review; actual request and draft require Root execution and actual F08 approval.","This source does not claim runtime qualification, product acceptance, or closureCAS execution."]})
mf=write("manifest.json",{"schema":"researchos.source-manifest.v1","actor":"codex:/root/w05_merge_review","entries":[ref(x) for x in sorted(O.iterdir()) if x.is_file() and x.name not in ("manifest.json","handoff.json")],"self_excluded":True,"mutable_after_seal":False})
h=write("handoff.json",{"schema":"researchos.source-handoff.v1","actor":"codex:/root/w05_merge_review","decision":"SOURCE_PREPARATION_COMPLETE_PENDING_INDEPENDENT_REVIEW","source_ref":ref(s),"report_ref":report,"manifest_ref":mf,"contract_ref":contract,"whole_inverse_ref":inv,"actual_candidate_execution":False,"actual_draft":False,"actual_CAS":False,"new_failure_origins":[ref(O/"failure-origin.65ae37.json")],"new_failure_count":1,"status":"STOPPED"})
print(json.dumps({"source":ref(s),"report":report,"manifest":mf,"handoff":h,"contract":contract,"checks":len(checks),"new_failure_count":1},ensure_ascii=False))

