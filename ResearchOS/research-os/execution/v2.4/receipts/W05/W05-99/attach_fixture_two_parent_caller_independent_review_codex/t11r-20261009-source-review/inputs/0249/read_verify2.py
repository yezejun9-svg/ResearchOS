from pathlib import Path
import hashlib,json,types,re,sys
B=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99")
Q=B/"typed_runtime_goal_fixture_attach_binding_revision_codex/q5-1a11e02f790732395c39325fbb4668d"
O=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_attach_binding_independent_review_codex/9f3826821e4c4c2aa4bf4ba2b5e5f5c8")
G=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
raw=G.read_bytes()
assert len(raw)==11404 and hashlib.sha256(raw).hexdigest()=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
mod=types.ModuleType("verified_source_guard");exec(compile(raw,str(G),"exec"),mod.__dict__)
guards=[]; held={}; references={}
def normalized(path):
 s=re.sub(r"\\u([0-9a-fA-F]{4})",lambda m:chr(int(m.group(1),16)),str(path))
 return str(Path(s))
def hold(refs):
 fresh=[]
 for r in refs:
  p=normalized(r["path"]); key=str(Path(p)).lower()
  ref={"path":p,"sha256":r["sha256"],"bytes":r["bytes"]}
  if key in references:
   assert references[key]==ref,(references[key],ref)
  else: references[key]=ref;fresh.append(ref)
 if fresh:
  g=mod.SourceReadGuard(); guards.append(g);g.acquire(fresh)
  for r in fresh: held[str(Path(r["path"])).lower()]=g.get_buffer(r["path"])
def data(p): return held[str(Path(normalized(p))).lower()]
def collect(x):
 out=[]
 if isinstance(x,dict):
  if all(k in x for k in ("path","sha256","bytes")) and isinstance(x["path"],str):out.append({k:x[k] for k in ("path","sha256","bytes")})
  for v in x.values():out.extend(collect(v))
 elif isinstance(x,list):
  for v in x:out.extend(collect(v))
 return out
try:
 hold([{"path":str(G),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)},
 {"path":str(Q/"HDF.json"),"sha256":"5a503f141b0c167eb5071f8224c0b9594700f86b18855ca3903339b6f6f0a5af","bytes":10563},
 {"path":str(Q/"MF.json"),"sha256":"c8bd3b7a4256c1e619d319d4debc745d91e98059ccb82e01e8ec51f44b0784e7","bytes":10896}])
 hdf=json.loads(data(Q/"HDF.json")); mf=json.loads(data(Q/"MF.json"))
 hold(list(mf["members"].values()))
 hold(collect(hdf)+collect(json.loads(data(Q/"source-input.json"))))
 hold(collect(json.loads(data(Q/"sourceguard.final.json"))))
 for key,blob in list(held.items()):
  if key.endswith("actual-tagged-compiler-input-inventory.json"):
   hold([r for r in collect(json.loads(blob)) if normalized(r["path"]).endswith("client_transcript.go")])
 (O/"input-pins.json").write_text(json.dumps(list(references.values()),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 mode=sys.argv[1]
 if mode=="verify":
  own=(O/"static_analysis_v2.py").read_bytes();exec(compile(own,str(O/"static_analysis_v2.py"),"exec"),globals())
 if mode=="overview":
  for name in ("report.md","assertion-inspection.json","static-preservation.json"):
   print("FILE",name);print(data(Q/name).decode())
  for name in ("source-input.json","source-replacements.json"):
   value=json.loads(data(Q/name));print("SHAPE",name,type(value).__name__,str(list(value) if isinstance(value,dict) else [list(v) if isinstance(v,dict) else type(v).__name__ for v in value])[:8000])
 elif mode=="file":
  for name in sys.argv[2:]:
   print("FILE",name); print(data(Q/name).decode())
 elif mode=="slice":
  name=sys.argv[2];a=int(sys.argv[3]);z=int(sys.argv[4]); p=Q/name if not Path(name).is_absolute() else Path(name)
  print("FILE",p)
  for i,l in enumerate(data(p).decode().splitlines(),1):
   if a<=i<=z:print(str(i)+":"+l)
 elif mode=="refs":
  for r in references.values():print(json.dumps(r,ensure_ascii=False))
 elif mode=="shapes":
  for name in ("source-replacements.json","sourceguard.final.json"):
   value=json.loads(data(Q/name)); print("SHAPE",name)
   if name=="source-replacements.json":
    for k,v in value.items(): print(k,[(list(r), {key:(len(val) if isinstance(val,str) else val) for key,val in r.items()}) for r in v])
   else: print(list(value))
 elif mode=="search":
  selected=sys.argv[2]; terms=sys.argv[3:]
  for key,blob in held.items():
   if selected in key:
    lines=blob.decode().splitlines(); hits=set()
    for i,line in enumerate(lines):
     if any(term in line for term in terms):hits.update(range(max(0,i-4),min(len(lines),i+12)))
    if hits:
     print("FILE",key)
     for i in sorted(hits):print(str(i+1)+":"+lines[i])
 elif mode=="inventory":
  for key,blob in list(held.items()):
   if key.endswith("actual-tagged-compiler-input-inventory.json"):
    value=json.loads(blob); print("KEYS",list(value))
    refs=collect(value);print("REFS",len(refs));print(json.dumps([r for r in refs if any(term in r["path"].lower() for term in sys.argv[2:])],ensure_ascii=False,indent=2))
 print("VERIFIED",len(references),"MF",len(mf["members"]))
finally:
 results=[g.close() for g in guards]
 summary={"schema":"researchos.independent-source-guard-closure.v1","guards":results,"entries":sum(len(x["entries"]) for x in results),"closed":all(x["closed"] for x in results),"retained":sum(x["retained_handles_count"] for x in results),"errors":[e for x in results for e in x["errors"]]}
 (O/("read-"+(sys.argv[1] if len(sys.argv)>1 else "none")+"-guard.json")).write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("GUARD_CLOSED",summary["closed"],"ENTRIES",summary["entries"],"RETAINED",summary["retained"],"ERRORS",summary["errors"])

