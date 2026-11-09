import json,hashlib,os,stat
from pathlib import Path
from collections import Counter
R=Path("D:/作品集/ResearchOS/research-os");O=Path(__file__).parent
N=R/"execution/v2.4/receipts/W13/W13-03/desktop58_failed_execution_root_closure_codex/93044794230d43ba9a169420a8cf45d1"
checks=[];reads={}
def ck(k,v,d=None):checks.append({"name":k,"pass":bool(v),"detail":d})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def raw(p):
 p=path(p);b=p.read_bytes();reads[str(p)]={"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)};return b
def jd(p):return json.loads(raw(p))
def vr(r):
 b=raw(r["path"]);ck("pin:"+r["path"],len(b)==r["bytes"] and hashlib.sha256(b).hexdigest()==r["sha256"]);return b
def refs(x):
 if isinstance(x,dict):
  if {"path","sha256","bytes"}<=set(x):yield x
  else:
   for v in x.values():yield from refs(v)
 elif isinstance(x,list):
  for v in x:yield from refs(v)
def canon(p):return os.path.normcase(os.path.abspath(str(path(p))))
def put(n,d):
 with (O/n).open("xb") as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+"\n").encode())
r=jd(N/"report.json");s=json.loads(vr(r["scope_ref"]));g=json.loads(vr(r["grant_ref"]));pv=jd(N/"original-tool-payload.v2.json")
E=path(s["output_root"]);er=json.loads(vr(pv["executor_result_ref"]));dc=er["last_child_result"]["debug_capture"]
# Reconstruct event lifetimes, without inventing creation-time in exit events.
active={};created=[];exited=[]
for n,e in enumerate(dc["events"]):
 if e["code"]==3:
  ck("CREATE no active PID collision:"+str(n),e["pid"] not in active)
  active[e["pid"]]=e.get("process_generation");created.append(e)
 elif e["code"]==5:
  ck("EXIT has observed CREATE:"+str(n),e["pid"] in active)
  active.pop(e["pid"],None);exited.append(e)
ck("all 805 creates exited",len(created)==805==len(exited) and active=={})
ck("ordered unique generation1..805",[x.get("process_generation") for x in created]==list(range(1,806)))
ck("rejected module process linked",created[-1]["pid"]==85216 and created[-1]["process_generation"]==805)
mods=dc["modules"];ck("8130 actual-hFile records",len(mods)==8130 and dc["actual_loaded_file_handles_only"] is True)
ck("all module PID/creation exact integer",all(type(x.get("creation_time_100ns")) is int and x["creation_time_100ns"]>2**53 and type(x.get("pid")) is int for x in mods))
ck("rejected conhost not success modules",not any(x["path_from_actual_file_handle"].lower().endswith("system32\\conhost.exe") for x in mods))
ck("module before digests complete",all(type(x.get("before")) is dict and len(x["before"].get("sha256",""))==64 and type(x["before"].get("bytes")) is int for x in mods))
vectors={}
for f in sorted(E.glob("*.vector.json")):
 v=jd(f);vectors[f.name]=v
 ck(f.name+" exact equality",v["expected_members"]==v["observed_members"] and v["drift"]==[] and v["file_count"]==len(v["expected_members"]))
ck("initial/Git/export stable",vectors["initial.vector.json"]==vectors["git-head-native-after.vector.json"]==vectors["export-blobs-native-after.vector.json"])
ck("beforebuild/afterbuild/final stable",vectors["before-build.vector.json"]==vectors["build-current58-native-after.vector.json"]==vectors["final.vector.json"])
ledgers=[jd(f) for f in sorted(E.glob("ledger-add-*.json"))]
ck("3 exact ledger revisions",[v["revision"] for v in ledgers]==[1,2,3])
prev={}
for l in ledgers:
 full={canon(x["path"]):x for x in l["full_members"]}
 ck("ledger keeps prefix rev"+str(l["revision"]),all(k in full and full[k]==v for k,v in prev.items()))
 additions={canon(x["path"]):x for x in l["added"]}
 ck("ledger additions exact rev"+str(l["revision"]),{k:v for k,v in full.items() if k not in prev}==additions)
 prev=full
ck("final vector is final ledger",vectors["final.vector.json"]["expected_members"]==ledgers[-1]["full_members"])
expected={canon(x["path"]):(x["sha256"],x["bytes"]) for x in vectors["before-build.vector.json"]["expected_members"]}
def cleanhandle(x):return x[4:] if x.startswith("\\\\?\\") else x
ck("8130 successful recorded loads have prepin",all(expected.get(canon(cleanhandle(x["path_from_actual_file_handle"])))==(x["before"]["sha256"],x["before"]["bytes"]) for x in mods))
ck("rejected conhost absent prepin",canon("C:/Windows/System32/conhost.exe") not in expected)
rt=[]
for f in sorted(E.glob("*runtime*.json")):
 x=jd(f);rt.append(x)
 ck(f.name+" point-time only",x.get("point_in_time_only") is True and x.get("Python_lifecycle_proof") is False)
ck("runtime observations stable files",bool(rt) and all(x["files"]==rt[0]["files"] for x in rt))
for f in sorted(E.glob("*.invocation.json")):
 x=jd(f);res=x["result"]
 ck(f.name+" native bridge equal",x["actual_native_exit"]==res["actual_exit"] and x["exception"] is None)
 if f.name!="build-current58.invocation.json":
  cl=res["job_cleanup"];ck(f.name+" native0 closed",res["actual_exit"]==0 and cl["job_idle_confirmed"] and cl["handles_closed"] and cl["errors"]==[])
 ck(f.name+" original request refs",isinstance(x["request"],dict))
# Inspect/hash nested sealed grant and preflight manifests and metadata references.
for rr in refs(g):
 vr(rr)
 p=path(rr["path"])
 if "manifest" in p.name.lower() and p.suffix==".json":
  mm=jd(p)
  for z in refs(mm):vr(z)
# Current Main facts by direct read, and native frozen source proof.
head=raw(R/".git/HEAD").decode().strip();ck("direct HEAD is symbolic main",head=="ref: refs/heads/main")
if head.startswith("ref: "):
 commit=raw(R/".git"/head[5:]).decode().strip()
 ck("current Main e2",commit=="e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7")
ck("original git-head raw",raw(E/"git-head.stdout.raw").decode().strip()=="e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7")
# Export read pins are already rehashed by primary audit. No follow through junction.
original=jd(N/"original-tool-payload.json")
ck("original caller Tool objects preserved",original["root_originals"]==pv["root_originals"])
ann=jd(N/"tool-observations.failed-closure.closed.original.json")
shape={"annex_keys":list(ann),"module_with_after":sum("after" in x for x in mods),"exit_code_counts":dict(Counter(str(x.get("actual_exit_event_code")) for x in exited)),"vectors":[{"name":k,"revision":v["revision"],"count":v["file_count"]} for k,v in vectors.items()],"ledgers":[{"revision":x["revision"],"label":x["label"],"added":len(x["added"]),"full":len(x["full_members"])} for x in ledgers]}
put("supplement.json",{"checks":checks,"passed":sum(x["pass"] for x in checks),"failed":[x for x in checks if not x["pass"]],"facts":shape,"reads":list(reads.values()),"new_product_native_calls":0})
print(json.dumps({"checks":len(checks),"failed":[x for x in checks if not x["pass"]],"facts":shape},ensure_ascii=False))

