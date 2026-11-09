from pathlib import Path
import hashlib,json,types,re,sys
B=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99")
N=B/"session_expired_writer_attach_fixture_revision_codex/leg-1a11e3e93437fe089b15fdf6a164840"
O=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/session_expired_writer_attach_fixture_independent_review_codex/5f3e09c72caf4d1991adf5174a87b19e")
G=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
raw=G.read_bytes()
assert len(raw)==11404 and hashlib.sha256(raw).hexdigest()=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
module=types.ModuleType("verified_source_guard");exec(compile(raw,str(G),"exec"),module.__dict__)
guards=[]; refs={}; held={}
def norm(path):
 s=re.sub(r"\\u([0-9a-fA-F]{4})",lambda m:chr(int(m.group(1),16)),str(path))
 p=Path(s)
 return str(p if p.is_absolute() else N/p)
def hold(rows):
 fresh=[]
 for r in rows:
  p=norm(r["path"]);key=p.lower(); ref={"path":p,"sha256":r["sha256"],"bytes":r["bytes"]}
  if key in refs: assert refs[key]==ref
  else:refs[key]=ref;fresh.append(ref)
 if fresh:
  g=module.SourceReadGuard();guards.append(g);g.acquire(fresh)
  for r in fresh:held[r["path"].lower()]=g.get_buffer(r["path"])
def data(path):return held[norm(path).lower()]
def collect(v):
 out=[]
 if isinstance(v,dict):
  if all(k in v for k in ("path","sha256","bytes")):out.append({k:v[k] for k in ("path","sha256","bytes")})
  for x in v.values():out.extend(collect(x))
 elif isinstance(v,list):
  for x in v:out.extend(collect(x))
 return out
try:
 hold([{"path":str(G),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)},
 {"path":str(N/"HDF.json"),"sha256":"49fcfa0afbb15b0bb65f54cc459fd1abb9da5f973a56c4a55ad3ab237bb4cfda","bytes":7604},
 {"path":str(N/"MF.json"),"sha256":"a8590a83c616c510b48d15e43fff4f03ec6426acefe4f3f7da129d0a15a7be12","bytes":6932}])
 hdf=json.loads(data(N/"HDF.json"));mf=json.loads(data(N/"MF.json"))
 print("MF_SHAPE",type(mf).__name__,list(mf) if isinstance(mf,dict) else len(mf))
 hold(collect(mf))
 mode=sys.argv[1]
 if mode=="entry":
  for name in ("HDF.json","MF.json"):
   print("FILE",name);print(data(N/name).decode())
 else:
  hold(collect(hdf));hold(collect(json.loads(data(N/"sourceguard.final.json"))))
  if mode=="overview":
   for name in ("report.md","static-preservation.json","source-replacement.json","test.patch"):
    print("FILE",name);print(data(N/name).decode())
  elif mode=="slice":
   p=norm(sys.argv[2]);a=int(sys.argv[3]);z=int(sys.argv[4]);print("FILE",p)
   for i,l in enumerate(data(p).decode().splitlines(),1):
    if a<=i<=z:print(str(i)+":"+l)
  elif mode=="search":
   for key,blob in held.items():
    if sys.argv[2] in key:
     lines=blob.decode().splitlines();hits=set()
     for i,l in enumerate(lines):
      if any(x in l for x in sys.argv[3:]):hits.update(range(max(0,i-4),min(len(lines),i+14)))
     if hits:
      print("FILE",key)
      for i in sorted(hits):print(str(i+1)+":"+lines[i])
  elif mode=="refs":
   for ref in refs.values():print(json.dumps(ref,ensure_ascii=False))
  elif mode=="verify":
   rel="internal/domain/client_protocol_control_windows_test.go"
   base=data(N/"base-root"/rel);new=data(N/"candidate-root"/rel)
   changes=json.loads(data(N/"source-replacement.json"));oldbody=changes["old"].encode();newbody=changes["new"].encode()
   assert base.count(oldbody)==1 and new.count(newbody)==1
   assert base.replace(oldbody,newbody,1)==new and new.replace(newbody,oldbody,1)==base
   before,after=base.split(oldbody);newbefore,newafter=new.split(newbody)
   assert before==newbefore and after==newafter
   original=next(r for r in refs.values() if ".local" in r["path"] and r["path"].endswith("client_protocol_control_windows_test.go"))
   assert data(original["path"])==base
   tail=oldbody[oldbody.index(b"\tvar epoch int64"):]
   lease=tail[:tail.index(b"\tenv.CommandID = strptr(ID())")]
   stale=tail[tail.index(b"\tenv.CommandID = strptr(ID())"):]
   assert lease in newbody and stale in newbody
   tests=re.findall(rb"func (Test[A-Za-z0-9_]+)[(]",base)
   newtests=re.findall(rb"func (Test[A-Za-z0-9_]+)[(]",new)
   assert tests==newtests
   result={"Source_only":True,"members_verified":len(mf["members"]),"input_count":len(refs),"exact_forward":True,"exact_inverse":True,"outside_body_bytes_equal":True,"unchanged_prefix_bytes":len(before),"unchanged_suffix_bytes":len(after),"base_matches_actual_T6":True,"original_SQL_lease_epoch2_future_assertion_verbatim":True,"original_stale_revision_VERSION_CONFLICT_verbatim":True,"test_names":[x.decode() for x in tests],"Go_SQL_native_model_executed":False}
   (O/"static-independent-checks.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
   (O/"input-copies").mkdir(exist_ok=True);index=[]
   for i,r in enumerate(refs.values()):
    p=O/"input-copies"/(str(i).zfill(4)+"-"+Path(r["path"]).name);p.write_bytes(data(r["path"]));index.append({"source":r,"copy":{"path":str(p),"sha256":r["sha256"],"bytes":r["bytes"]}})
   (O/"input-copy-index.json").write_text(json.dumps(index,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
   print(json.dumps(result,ensure_ascii=False,indent=2))
 (O/"input-pins.json").write_text(json.dumps(list(refs.values()),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("INPUTS",len(refs))
finally:
 closure={"guards":[g.close() for g in guards]}
 closure["closed"]=all(x["closed"] for x in closure["guards"]);closure["retained"]=sum(x["retained_handles_count"] for x in closure["guards"])
 closure["errors"]=[e for x in closure["guards"] for e in x["errors"]]
 (O/("guard-"+sys.argv[1]+".json")).write_text(json.dumps(closure,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("CLOSED",closure["closed"],"RETAINED",closure["retained"],"ERRORS",closure["errors"])

