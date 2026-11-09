import ast,difflib,hashlib,json,pathlib
O=pathlib.Path(__file__).resolve().parent
R=pathlib.Path(r"D:\作品集\ResearchOS\research-os")
B=R/"execution/v2.4/receipts/W05/W05-99"
C=B/"mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc"
rows=[]
def ref(p,b=None):
 b=p.read_bytes() if b is None else b
 return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def read(p,expected=None):
 p=pathlib.Path(p);b=p.read_bytes();r=ref(p,b)
 if expected:assert r["sha256"]==expected["sha256"] and r["bytes"]==expected["bytes"],str(p)
 snap=O/(r["sha256"]+".raw")
 if not snap.exists():snap.write_bytes(b)
 rows.append({"source_ref":r,"snapshot_ref":ref(snap,b)})
 return b
def rr(r):return read(r["path"],r)
def write(n,x):
 p=O/n;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");return ref(p)
h=json.loads(read(C/"handoff.json",{"sha256":"ff4d54229ae082cfbec5536ecfae453c961944abf9bc9091a1a08f8cefe10229","bytes":4175}))
m=json.loads(rr(h["manifest_ref"]))
for r in m["members"]:rr(r)
pins=json.loads(rr(h["source_pins_ref"]))
for category in ("runtime_sources","external_static_sources","derived_from"):
 for r in pins[category]:rr(r)
c4manifest=json.loads(rr(m["derived_from_c4"]))
oldref=next(r for r in c4manifest["members"] if pathlib.Path(r["path"]).name=="controller.py")
old=rr(oldref);new=rr(h["source_ref"])
for r in m["members"]:
 name=pathlib.Path(r["path"]).name
 if name in ("canonical_transactions.py","owned_job_hooks.py","phase_worker.py","job_deadline_watchdog.py","job_probe_worker.py"):
  oldr=next(x for x in c4manifest["members"] if pathlib.Path(x["path"]).name==name)
  assert rr(oldr)==rr(r)
priorreviewref={"path":str(B/"mu_sdk_controller_v4_observer_v3_independent_review_codex/4987830389c544cdbcc3f5895a987bd4/independent-source-review.json"),"sha256":"fd3a258f97f0beacbb36d4fab2d4d0d140cb4e5d2b1c750c3c5241735b49fc4a","bytes":8833}
priorreview=json.loads(rr(priorreviewref))
tuplerefs={k:priorreview[k] for k in ("controller_source_ref","observer_source_ref","hooks_source_ref","runner_source_ref","phase_worker_source_ref","python_binary_ref")}
tuplerefs["controller_source_ref"]=h["source_ref"]
for key,name in (("hooks_source_ref","owned_job_hooks.py"),("phase_worker_source_ref","phase_worker.py")):
 tuplerefs[key]=next(r for r in m["members"] if pathlib.Path(r["path"]).name==name)
for r in tuplerefs.values():rr(r)
actualreviewref={"path":str(B/"source_guard_v2_actual_probe_independent_review_codex/7cf20b0f72ab42c6951a70e52aa41f77/review.json"),"sha256":"1d53a262a75ebd35c1e992eb6bcbb919c152e7ff1816021041f74d60f2154278","bytes":9615}
actualreview=json.loads(rr(actualreviewref))
assert actualreview["decision"]=="PASS_ACTUAL_PRIVATE_WINDOWS_COMPONENT_IN_SCOPE"
forward="".join(difflib.unified_diff(old.decode().splitlines(keepends=True),new.decode().splitlines(keepends=True),fromfile="before",tofile="after"))
inverse="".join(difflib.unified_diff(new.decode().splitlines(keepends=True),old.decode().splitlines(keepends=True),fromfile="before",tofile="after"))
authorforward=rr(h["forward_diff_ref"]).decode();authorinverse=rr(h["inverse_diff_ref"]).decode()
# Author diff headers may name their source versions; compare every hunk verbatim.
assert forward.splitlines(keepends=True)[2:]==authorforward.splitlines(keepends=True)[2:]
assert inverse.splitlines(keepends=True)[2:]==authorinverse.splitlines(keepends=True)[2:]
def apply_unified(before,diff):
 oldlines=before.decode().splitlines(keepends=True);lines=diff.splitlines(keepends=True);out=[];at=0;i=2
 import re
 while i<len(lines):
  match=re.match(r"@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@",lines[i]);assert match
  start=int(match.group(1))-1;out.extend(oldlines[at:start]);at=start;i+=1
  while i<len(lines) and not lines[i].startswith("@@ "):
   line=lines[i];tag=line[0];content=line[1:]
   if tag in (" ","-"):assert oldlines[at]==content;at+=1
   if tag in (" ","+"):out.append(content)
   i+=1
 out.extend(oldlines[at:]);return "".join(out).encode()
assert apply_unified(old,authorforward)==new and apply_unified(new,authorinverse)==old
(O/"independent.forward.diff").write_bytes(forward.encode());(O/"independent.inverse.diff").write_bytes(inverse.encode())
def functions(b):
 lines=b.splitlines(keepends=True)
 return {n.name:b"".join(lines[n.lineno-1:n.end_lineno]) for n in ast.parse(b).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
of,nf=functions(old),functions(new)
delta={"changed":[n for n in of if n in nf and of[n]!=nf[n]],"added":[n for n in nf if n not in of],"removed":[n for n in of if n not in nf]}
a={"schema":"researchos.c5-source-independent-intake.v1","source_ref":h["source_ref"],"source_author":h["actor"],"source_handoff_ref":ref(C/"handoff.json"),"source_manifest_ref":h["manifest_ref"],"source_pins_ref":h["source_pins_ref"],"tuple":tuplerefs,"prior_c4_review_ref":priorreviewref,"actual_guard_probe_review_ref":actualreviewref,"delta":delta,"independent_forward_inverse_full_bytes":True,"all_five_helpers_exact_c4":True,"reused_prior_evidence_not_rerun":{"O2":39,"v9":8,"guard_v2":31,"guard_v1":28,"actual_private_guard_probe":True},"author_controls_executed":0,"rows":rows}
write("intake.json",a)
print(json.dumps({k:v for k,v in a.items() if k not in ("rows","tuple")},ensure_ascii=False,indent=2))
print("INPUT_RECORDS",len(rows))
obs=ast.parse(pathlib.Path(tuplerefs["observer_source_ref"]["path"]).read_bytes())
for n in obs.body:
 if isinstance(n,ast.FunctionDef) and n.name=="validate_source_review":
  print("OBSERVER_VALIDATION_FUNCTION",ast.get_source_segment(pathlib.Path(tuplerefs["observer_source_ref"]["path"]).read_text(encoding="utf-8"),n))

