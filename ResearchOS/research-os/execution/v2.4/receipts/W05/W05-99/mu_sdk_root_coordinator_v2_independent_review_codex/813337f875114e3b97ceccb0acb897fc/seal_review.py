import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
def pin(p):
 raw=p.read_bytes()
 return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def put(n,v):
 p=O/n
 with p.open("x",encoding="utf-8",newline="\n") as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
 return pin(p)
r=json.loads((O/"independent-source-review.json").read_bytes())
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ("manifest.json","handoff.json")]
mf=put("manifest.json",{"schema":"researchos.independent-source-review-manifest.v1","actor_id":r["actor_id"],"decision":r["decision"],"members":members,"member_count":len(members),"source_ref":r["source_ref"],"fixed_pins_ref":r["fixed_pins_ref"],"provider_calls":0,"canonical_writes":0,"formal_acceptance":False})
hd=put("handoff.json",{"schema":"researchos.root-sdk-coordinator-independent-review-handoff.v1","actor_id":r["actor_id"],"decision":r["decision"],"review_ref":pin(O/"independent-source-review.json"),"report_ref":pin(O/"REVIEW.md"),"counterexamples_ref":pin(O/"pure-interface-counterexamples.json"),"source_verification_ref":pin(O/"source-verification.json"),"original_tool_io_ref":pin(O/"original-review-tool-io.json"),"pure_tool_io_ref":pin(O/"pure-counterexample.original-tool-io.json"),"manifest_ref":mf,"source_ref":r["source_ref"],"fixed_pins_ref":r["fixed_pins_ref"],"remaining_blockers":2,"actual_tool_failures":[724,726],"candidate_native_WinAPI_SQL_provider_calls":0,"canonical_writes":0,"runtime_qualification":False,"formal_acceptance":False,"execution_authority":False,"stopped":True})
print(json.dumps({"handoff_ref":hd,"manifest_ref":mf,"review_ref":pin(O/"independent-source-review.json"),"counterexamples_ref":pin(O/"pure-interface-counterexamples.json"),"member_count":len(members),"outer_scope":"Source review only"},ensure_ascii=False))

