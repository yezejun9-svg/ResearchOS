import sys
sys.dont_write_bytecode=True
import json,hashlib,types
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os")
O=Path(__file__).resolve().parent
B=R/"execution/v2.4/receipts/W05/W05-99"
CP,OW,SS,CM=[R/"execution/v2.4"/(v+".json") for v in ("checkpoint","path_ownership","step_state","commands")]
def pin(p):
 p=Path(p).resolve()
 with p.open("rb") as f:raw=f.read(64*1024*1024+1)
 assert len(raw)<=64*1024*1024
 return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def save(n,value):
 p=O/n
 with p.open("xb") as f:f.write((json.dumps(value,ensure_ascii=True,indent=2)+"\n").encode())
 return pin(p)
assert len(sys.argv)==7,"CP_SHA CP_BYTES CP_REV OW_SHA OW_BYTES OW_REV"
cp_sha,cp_bytes,cp_rev=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])
ow_sha,ow_bytes,ow_rev=sys.argv[4],int(sys.argv[5]),int(sys.argv[6])
assert cp_rev==366 and ow_rev==170
refs=[pin(p) for p in (CP,OW,SS,CM)]
assert (refs[0]["sha256"],refs[0]["bytes"])==(cp_sha,cp_bytes)
assert (refs[1]["sha256"],refs[1]["bytes"])==(ow_sha,ow_bytes)
assert (refs[2]["sha256"],refs[2]["bytes"])==("fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149",257446)
assert (refs[3]["sha256"],refs[3]["bytes"])==("b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129",68156)
scope_ref=pin(O/"scope-registration.root.json")
assert (scope_ref["sha256"],scope_ref["bytes"])==("ea710aa75478911bff82fd02243c02b60df660dbd3f8548c7cc47d0968f175e3",4907)
gp=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
gr=pin(gp)
assert (gr["sha256"],gr["bytes"])==("e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85",11404)
gm=types.ModuleType("root_w09_vector_guard")
gm.__file__=str(gp)
exec(compile(gp.read_bytes(),str(gp),"exec"),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=64*1024*1024,total_cap=256*1024*1024)
guard.acquire(refs+[scope_ref,gr,pin(__file__),pin(sys.executable)])
try:
 c=json.loads(guard.get_buffer(str(CP)));o=json.loads(guard.get_buffer(str(OW)))
 assert c["revision"]==cp_rev and o["revision"]==ow_rev
 assert c["head"]=="adc460c2138528f163f7fdab5e8d81dde157b7fb" and c["project_id"]=="aede0678-7308-43dc-b9f2-cfe3d90cfdfb"
 registered=o["card_path_bindings"]["W09-99"]["subtasks"]["c19_fixture_producer"]
 assert registered["owner"]=="codex:/root" and registered["scope_ref"]==scope_ref
 workers=[v for v in c["workers"] if v.get("step_id")=="W09-99" and v.get("slice_id")=="C19_FIXTURE_PRODUCER"]
 assert len(workers)==1 and workers[0]["owner"]=="codex:/root" and workers[0]["scope_ref"]==scope_ref
 assert c["work_in_progress"]["construction_active_parents"]==["W05","W09"]
 vector=save("canonical-input-vector.json",{"schema":"researchos.w09-c19-canonical-input-vector.v1","checkpoint_revision":cp_rev,"refs":refs})
 assert [pin(p) for p in (CP,OW,SS,CM)]==refs
finally:
 cleanup=guard.close()
 cleanup_ref=save("vector-source-guard.cleanup.actual.json",cleanup)
 assert cleanup["closed"] and not cleanup["errors"] and cleanup["retained_handles_count"]==0
print(json.dumps({"vector_ref":vector,"cleanup_ref":cleanup_ref,"checkpoint_ref":refs[0],"ownership_ref":refs[1],"formal_acceptance":False}),flush=True)

