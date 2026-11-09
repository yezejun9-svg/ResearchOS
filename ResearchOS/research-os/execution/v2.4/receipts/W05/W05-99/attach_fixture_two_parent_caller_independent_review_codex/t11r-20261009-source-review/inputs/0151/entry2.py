from pathlib import Path
import hashlib,json,types
B=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99")
Q=B/"typed_runtime_goal_fixture_attach_binding_revision_codex/q5-1a11e02f790732395c39325fbb4668d"
O=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/typed_runtime_goal_fixture_attach_binding_independent_review_codex/9f3826821e4c4c2aa4bf4ba2b5e5f5c8")
G=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
raw=G.read_bytes()
assert len(raw)==11404 and hashlib.sha256(raw).hexdigest()=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
mod=types.ModuleType("verified_source_guard");exec(compile(raw,str(G),"exec"),mod.__dict__)
guard=mod.SourceReadGuard()
refs=[{"path":str(G),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)},
{"path":str(Q/"HDF.json"),"sha256":"5a503f141b0c167eb5071f8224c0b9594700f86b18855ca3903339b6f6f0a5af","bytes":10563},
{"path":str(Q/"MF.json"),"sha256":"c8bd3b7a4256c1e619d319d4debc745d91e98059ccb82e01e8ec51f44b0784e7","bytes":10896}]
try:
 guard.acquire(refs)
 for name in ("HDF.json","MF.json"):
  print("FILE",name); print(guard.get_buffer(str(Q/name)).decode())
finally:
 result=guard.close()
 (O/"entry2-guard.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("CLOSURE",json.dumps({"verification":result["verification"],"closed":result["closed"],"entries":len(result["entries"]),"errors":result["errors"]}))

