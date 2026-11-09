import hashlib,json,pathlib
O=pathlib.Path(__file__).resolve().parent
def ref(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write(name,data):
 p=O/name;p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");return ref(p)
members=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in {"manifest.json","handoff.json"}]
mf=write("manifest.json",{"schema":"researchos.independent-source-review-manifest.v1","actor":"codex:/root/command_queue_impl","members":members,"excludes":["manifest.json","handoff.json"]})
h=write("handoff.json",{"schema":"researchos.independent-source-review-handoff.v1","actor":"codex:/root/command_queue_impl","decision":"READY_SOURCE_ONLY","scope":"V9_RUNNER_SINGLE_WRITE_PATHS_LITERAL_DELTA_ONLY","review_ref":ref(O/"review.json"),"report_ref":ref(O/"report.md"),"manifest_ref":mf,"members":len(members),"new_tool_failures":2,"failure_origin_refs":[ref(O/"failure-origin.690.json"),ref(O/"failure-origin.691.json")],"runtime_authority":False,"whole_chain_ready":False,"provider_requests":0,"formal_increment":0,"main_writes":0,"canonical_writes":0,"stopped":True})
print(json.dumps({"handoff":h,"manifest":mf,"review":ref(O/"review.json"),"members":len(members)},ensure_ascii=False,indent=2))

