import ast,difflib,hashlib,json,re
from pathlib import Path
O=Path(__file__).resolve().parent
R=Path(r"D:\作品集\ResearchOS\research-os")
B=R/"execution/v2.4/receipts/W05/W05-99"
C=B/"mu_sdk_controller_revision_v6_codex/c309fe6cec1c400ea212065fbd484e73"
V=B/"mu_sdk_job_observer_revision_v4_codex/cbb82ea19cf84175baf61427251b983c"
rows=[];seen={}
def ref(p,b=None):
 p=Path(p);b=p.read_bytes() if b is None else b
 return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def read(p,expected=None):
 p=Path(p);b=p.read_bytes();r=ref(p,b)
 if expected:assert r["sha256"]==expected["sha256"] and r["bytes"]==expected["bytes"],str(p)
 if str(p) not in seen:
  snap=O/"snapshots"/(r["sha256"]+".raw");snap.parent.mkdir(exist_ok=True)
  if not snap.exists():snap.write_bytes(b)
  row={"source_ref":r,"snapshot_ref":ref(snap,b)};rows.append(row);seen[str(p)]=row
 return b
def rr(r):return read(r["path"],r)
def write(n,x):
 p=O/n;p.write_bytes((json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode());return ref(p)
ch=json.loads(read(C/"handoff.json",{"sha256":"64d688f6f052f33dcf8ff503cb94d1dbbc7f18b5856320d33e7ce460c36b9d19","bytes":4813}))
oh=json.loads(read(V/"handoff.json",{"sha256":"cc97b80da5af317a7b6a3949ea27acbd87c4d4cbbedeb041870cfda9950608da","bytes":3275}))
cm=json.loads(rr(ch["manifest_ref"]));om=json.loads(rr(oh["manifest_ref"]))
for m in (cm,om):
 for item in m["members"]:rr(item)
pins=json.loads(rr(ch["source_pins_ref"]))
for section in ("sources","inputs"):
 for item in pins[section].values():rr(item)
oldcm=json.loads(rr(cm["derived_from_c5"]))
old_c_ref=next(x for x in oldcm["members"] if Path(x["path"]).name=="controller.py")
oldc=rr(old_c_ref);newc=rr(ch["controller_source_ref"])
oldo_ref=next(x for x in om["members"] if Path(x["path"]).name=="mu_sdk_job_observer.v3.proposed.py")
oldo=rr(oldo_ref);newo=rr(oh["source_ref"])
producer=rr(ch["cleanup_producer_source_ref"])
helpers={}
for name in ("canonical_transactions.py","owned_job_hooks.py","phase_worker.py","job_deadline_watchdog.py","job_probe_worker.py"):
 oldr=next(x for x in oldcm["members"] if Path(x["path"]).name==name)
 newr=next(x for x in cm["members"] if Path(x["path"]).name==name)
 helpers[name]=rr(oldr)==rr(newr);assert helpers[name]
def apply(before,diff):
 old=before.decode().splitlines(keepends=True);lines=diff.decode().splitlines(keepends=True)
 out=[];at=0;i=2
 while i<len(lines):
  m=re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@",lines[i]);assert m
  start=max(0,int(m.group(1))-1);out+=old[at:start];at=start;i+=1
  while i<len(lines) and not lines[i].startswith("@@ "):
   tag,body=lines[i][0],lines[i][1:]
   if tag in (" ","-"):assert old[at]==body;(None);at+=1
   if tag in (" ","+"):out.append(body)
   i+=1
 out+=old[at:];return "".join(out).encode()
diff_results={}
for label,old,new,fpath,ipath in (
 ("controller",oldc,newc,C/"controller.forward.diff",C/"controller.inverse.diff"),
 ("observer",oldo,newo,V/"forward.v3-to-v4.diff",V/"inverse.v4-to-v3.diff"),
 ("producer",b"",producer,C/"cleanup-producer.forward.diff",C/"cleanup-producer.inverse.diff")):
 f=read(fpath);i=read(ipath)
 assert apply(old,f)==new and apply(new,i)==old,label
 generated="".join(difflib.unified_diff(old.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True),fromfile="before",tofile="after")).encode()
 assert generated.splitlines(keepends=True)[2:]==f.splitlines(keepends=True)[2:],label
 diff_results[label]={"forward_full_bytes":True,"inverse_full_bytes":True,"independent_hunks_equal":True}
def funcs(raw):
 lines=raw.splitlines(keepends=True)
 return {n.name:b"".join(lines[n.lineno-1:n.end_lineno]) for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def delta(old,new):
 a,b=funcs(old),funcs(new)
 return {"changed":[k for k in a if k in b and a[k]!=b[k]],"added":[k for k in b if k not in a],"removed":[k for k in a if k not in b]}
prior=json.loads(rr(cm["c5_independent_review"]))
rr(prior["prior_c4_review_ref"]);rr(prior["actual_guard_probe_review_ref"])
# Only byte-check and reuse prior scoped results; do not rerun those probes.
tuple_refs={k:prior[k] for k in ("controller_source_ref","observer_source_ref","hooks_source_ref","runner_source_ref","phase_worker_source_ref","python_binary_ref")}
tuple_refs.update(controller_source_ref=ch["controller_source_ref"],observer_source_ref=oh["source_ref"],
 hooks_source_ref=pins["sources"]["owned_job_hooks"],phase_worker_source_ref=pins["sources"]["phase_worker"],
 cleanup_producer_source_ref=ch["cleanup_producer_source_ref"])
contexts={
 "controller_source":tuple_refs["controller_source_ref"],"observer_source":tuple_refs["observer_source_ref"],
 "hooks_source":tuple_refs["hooks_source_ref"],"phase_worker_source":tuple_refs["phase_worker_source_ref"],
 "runner_source":tuple_refs["runner_source_ref"],"canonical_transactions_source":pins["sources"]["canonical_transactions"],
 "job_watchdog_source":pins["sources"]["job_watchdog"],"source_guard_source":pins["sources"]["source_guard"],
 "base_owned_process_source":pins["sources"]["base_owned_process"],"cleanup_producer_source":tuple_refs["cleanup_producer_source_ref"],
 "python_binary":tuple_refs["python_binary_ref"]}
a={"schema":"researchos.c6-o4-independent-intake.v1","controller_handoff_ref":ref(C/"handoff.json"),
 "controller_manifest_ref":ch["manifest_ref"],"observer_handoff_ref":ref(V/"handoff.json"),"observer_manifest_ref":oh["manifest_ref"],
 "tuple":tuple_refs,"source_context":contexts,"helpers_identical_to_c5":helpers,"diffs":diff_results,
 "controller_delta":delta(oldc,newc),"observer_delta":delta(oldo,newo),
 "prior_c5_review_ref":cm["c5_independent_review"],"prior_c4_review_ref":prior["prior_c4_review_ref"],
 "actual_guard_probe_review_ref":prior["actual_guard_probe_review_ref"],"reused_not_rerun":prior["reused_not_rerun"],
 "author_controls_executed":0,"candidate_imports_or_native_calls":0,"rows":rows}
write("intake.json",a)
print(json.dumps({k:a[k] for k in ("controller_delta","observer_delta","helpers_identical_to_c5","diffs")},ensure_ascii=False))
print("INPUT_RECORDS",len(rows))

