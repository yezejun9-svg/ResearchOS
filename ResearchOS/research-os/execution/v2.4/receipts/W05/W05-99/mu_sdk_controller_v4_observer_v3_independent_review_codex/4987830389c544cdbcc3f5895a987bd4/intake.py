import ast,difflib,hashlib,json,pathlib
O=pathlib.Path(__file__).resolve().parent
R=pathlib.Path(r"D:\作品集\ResearchOS\research-os")
B=R/"execution/v2.4/receipts/W05/W05-99"
rows=[]
def ref(p,b=None):
 b=p.read_bytes() if b is None else b
 return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def read(p,expected=None):
 p=pathlib.Path(p);p=p if p.is_absolute() else R/p
 b=p.read_bytes();r=ref(p,b)
 if expected is not None:assert r["sha256"]==expected["sha256"] and r["bytes"]==expected["bytes"],str(p)
 s=O/(r["sha256"]+".raw")
 if not s.exists():s.write_bytes(b)
 rows.append({"source_ref":r,"snapshot_ref":ref(s,b)})
 return b
def rr(r):return read(r["path"],r)
def jo(b):return json.loads(b)
def write(n,x):p=O/n;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");return ref(p)
def assignments(b):
 t=ast.parse(b.decode())
 return {n.targets[0].id:ast.literal_eval(n.value) for n in t.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and isinstance(n.value,(ast.Constant,ast.Dict,ast.List,ast.Tuple,ast.Set))}
c4dir=B/"mu_sdk_controller_revision_v4_codex/dfcc33b4fb8f47c387bf2c10c0073bcd"
c4=jo(read(c4dir/"handoff.json",{"sha256":"1e87f80d0d88e7e40890668415fdfeaa7c642dfabaabafc2f915ca111044d7f3","bytes":3623}))
cm=jo(rr(c4["manifest_ref"]))
for r in cm["members"]:rr(r)
c4raw=rr(c4["source_ref"]);ct=ast.parse(c4raw.decode());ca=assignments(c4raw)
for k in ("source_read_guard_ref","python_binary_ref"):rr(c4[k])
for k in ("CANONICAL_TRANSACTION_REF","JOB_WATCHDOG_REF","SOURCE_READ_GUARD_REF","PINNED_PYTHON_REF","BASE_OWNED_PROCESS_REF"):rr(ca[k])
c3=jo(rr(c4["old_handoff_ref"]))
c3refs={pathlib.Path(r["path"]).name:r for r in c3["source_refs"]}
c3raw=rr(c3refs["controller.py"]);c3watch=rr(c3refs["job_deadline_watchdog.py"])
o3dir=B/"mu_sdk_job_observer_revision_v3_codex/7a43feff8ec24250b87d04d0e346a52e"
o3=jo(read(o3dir/"handoff.json",{"sha256":"6af7b96b945a31b58d601effae5e8d8da5a85cd6914ba3164d6a291e0cc77660","bytes":2288}))
om=jo(rr(o3["manifest_ref"]))
for r in om["members"]:rr(r)
o3raw=rr(o3["source_ref"]);o3a=assignments(o3raw)
o2ref={"path":str(B/"mu_sdk_job_observer_revision_v2_codex/099b315944fa42e393af8d9190e7c14e/mu_sdk_job_observer.v2.proposed.py"),"sha256":"7077b2b70098f64f6b0a4aa5d993c59fb6cb3ffa4f08e66eb73cdb00cecc7dc0","bytes":31072}
o2raw=rr(o2ref);o2a=assignments(o2raw)
v9raw=rr(o3["runner_ref"])
prior=B/"mu_sdk_controller_v3_chain_independent_review_codex/4cc88a7e4c8d4d2caa049d1b324ac8eb"
pm=jo(read(prior/"manifest.json",{"sha256":"75f0e7f30119ed85b87a68523786d1ae6e347974a4a06252105a9064ae8fde23","bytes":23097}))
wanted={"canonical-controls.py","canonical-controls.json","watchdog-controls.py","watchdog-controls.json","independent-source-review.json","findings.json"}
for r in pm["members"]:
 if pathlib.Path(r["path"]).name in wanted:rr(r)
o2review=jo(read(B/"mu_sdk_observer_v2_independent_source_review_codex/75b8c18a1ee84e2db9738de1ac2a1d0b/independent-review.json",{"sha256":"6218cdce466b4676ce0586d52cb719f43fe7d3f9ac105764df844e9a6ffda299","bytes":2992}))
v9review=jo(read(B/"mu_sdk_runner_v9_narrow_independent_review_codex/81a6e62dc2af4579aef73a0a477b891b/review.json",{"sha256":"09141c7dc34fb40c848a5f3a676131d087b5fa7b2dabbfcad8627b039a31e2e2","bytes":5134}))
def function_bytes(raw):
 lines=raw.splitlines(keepends=True)
 return {n.name:b"".join(lines[n.lineno-1:n.end_lineno]) for n in ast.parse(raw.decode()).body if isinstance(n,ast.FunctionDef)}
cf,of=function_bytes(c4raw),function_bytes(c3raw)
controller_delta={"changed":[k for k in of if k in cf and of[k]!=cf[k]],"added":[k for k in cf if k not in of],"removed":[k for k in of if k not in cf]}
assert function_bytes(o2raw)==function_bytes(o3raw)
ot=ast.parse(o2raw.decode());nt=ast.parse(o3raw.decode())
def striprunner(tree):
 tree=ast.parse(ast.unparse(tree))
 tree.body=[n for n in tree.body if not(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="RUNNER_REF" for t in n.targets))]
 return ast.dump(tree,include_attributes=False)
assert striprunner(ot)==striprunner(nt)
assert o3a["RUNNER_REF"]==o3["runner_ref"]
obefore=next(n for n in ot.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="RUNNER_REF" for t in n.targets))
oafter=next(n for n in nt.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="RUNNER_REF" for t in n.targets))
oldspan=ast.get_source_segment(o2raw.decode(),obefore).encode();newspan=ast.get_source_segment(o3raw.decode(),oafter).encode()
assert o2raw.replace(oldspan,newspan)==o3raw and o3raw.replace(newspan,oldspan)==o2raw
for tag,before,after in [("controller",c3raw,c4raw),("watchdog",c3watch,rr(c4["job_watchdog_ref"])),("observer",o2raw,o3raw)]:
 f="".join(difflib.unified_diff(before.decode().splitlines(keepends=True),after.decode().splitlines(keepends=True),fromfile="before",tofile="after"))
 inv="".join(difflib.unified_diff(after.decode().splitlines(keepends=True),before.decode().splitlines(keepends=True),fromfile="before",tofile="after"))
 (O/(tag+".independent.forward.diff")).write_text(f,encoding="utf-8",newline="")
 (O/(tag+".independent.inverse.diff")).write_text(inv,encoding="utf-8",newline="")
 if tag!="observer":
  assert f.encode()==(c4dir/(tag+".forward.diff")).read_bytes()
  assert inv.encode()==(c4dir/(tag+".inverse.diff")).read_bytes()
for filename in ("canonical_transactions.py","owned_job_hooks.py","phase_worker.py","job_probe_worker.py"):
 oldmember=next(r for r in jo(rr(c3["manifest_ref"]))["members"] if pathlib.Path(r["path"]).name==filename)
 newmember=next(r for r in cm["members"] if pathlib.Path(r["path"]).name==filename)
 assert rr(oldmember)==rr(newmember)
summary={"controller_delta":controller_delta,"o3_all_functions_exact_o2":True,"o3_only_RUNNER_REF_assignment_delta_full_bytes":True,"o3_runner_matches_v9":True,"o2_independent_39_reused_not_rerun":True,"v9_independent_8_reused_not_rerun":True,"controller_watchdog_diffs_independently_regenerated_exact":True,"inherited_helpers_exact":True,"tuple":{"controller_source_ref":c4["source_ref"],"observer_source_ref":o3["source_ref"],"hooks_source_ref":c4["hooks_ref"],"runner_source_ref":o3["runner_ref"],"phase_worker_source_ref":c4["phase_worker_ref"],"python_binary_ref":c4["python_binary_ref"]},"helper_refs":{k:ca[k] for k in ("CANONICAL_TRANSACTION_REF","JOB_WATCHDOG_REF","SOURCE_READ_GUARD_REF","BASE_OWNED_PROCESS_REF")},"prior_review_refs":{"c3":next(r for r in pm["members"] if pathlib.Path(r["path"]).name=="independent-source-review.json"),"o2":next(r["source_ref"] for r in rows if r["source_ref"]["sha256"]=="6218cdce466b4676ce0586d52cb719f43fe7d3f9ac105764df844e9a6ffda299"),"v9":next(r["source_ref"] for r in rows if r["source_ref"]["sha256"]=="09141c7dc34fb40c848a5f3a676131d087b5fa7b2dabbfcad8627b039a31e2e2")},"rows":rows,"input_drift":[]}
write("intake.json",summary)
print(json.dumps({k:v for k,v in summary.items() if k not in ("rows","prior_review_refs")},ensure_ascii=False,indent=2))
print("ROWS",len(rows))
print("OLD_CONTROLS",[r["source_ref"]["path"] for r in rows if pathlib.Path(r["source_ref"]["path"]).name in wanted])

