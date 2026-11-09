import sys
sys.dont_write_bytecode=True
import hashlib,json,types,threading
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";O=Path(__file__).resolve().parent
G=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
def pin(p):
 raw=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def load_source(ref,raw,name):
 assert len(raw)==ref["bytes"] and hashlib.sha256(raw).hexdigest()==ref["sha256"]
 m=types.ModuleType(name);m.__file__=ref["path"];exec(compile(raw,ref["path"],"exec"),m.__dict__);return m
refs=json.loads((O/"launch.refs.actual.json").read_bytes());gref=pin(G);assert gref["sha256"]=="e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"
gm=load_source(gref,G.read_bytes(),"root_v5_launch_guard");guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024)
guard.acquire([gref,refs["input_ref"],refs["review_ref"],refs["coordinator_source_ref"],pin(O/"launch.refs.actual.json"),pin(Path(__file__).resolve())])
setattr(sys,"_researchos_model_v5_wrapper_source_owner",guard)
def retained(reason):
 setattr(sys,"_researchos_model_v5_wrapper_retention_reason",reason)
 try:
  with (O/"wrapper.retained.original.json").open("xb") as f:f.write((json.dumps(dict(reason=reason,guard_retained=True))+"\n").encode())
 except BaseException:pass
 finally:
  while True:
   try:threading.Event().wait(1)
   except BaseException:pass
try:
 coordinator=load_source(refs["coordinator_source_ref"],guard.get_buffer(refs["coordinator_source_ref"]["path"]),"root_v5_model_coordinator")
 coordinator.run_resident(refs["input_ref"],refs["review_ref"])
finally:
 try:cleanup=guard.close()
 except BaseException as exc:retained(repr(exc))
 if not (cleanup["closed"] and cleanup["retained_handles_count"]==0 and not cleanup["errors"]):retained("wrapper Source guard incomplete")
 with (O/"wrapper.source-guard.cleanup.actual.json").open("xb") as f:f.write((json.dumps(cleanup,ensure_ascii=False,indent=2)+"\n").encode())

