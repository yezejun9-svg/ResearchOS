import hashlib,json,pathlib
O=pathlib.Path(__file__).resolve().parent
def ref(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write(n,x):
 p=O/n;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");return ref(p)
r=json.loads((O/"independent-source-review.json").read_bytes())
members=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ("manifest.json","handoff.json")]
m=write("manifest.json",{"schema":"researchos.immutable-independent-source-review-manifest.v1","actor_id":"codex:/root/command_queue_impl","decision":"REQUEST_CHANGES","members":members,"member_count":len(members),"excludes":["manifest.json","handoff.json"]})
h=write("handoff.json",{"schema":"researchos.immutable-independent-source-review-handoff.v1","actor_id":"codex:/root/command_queue_impl","decision":"REQUEST_CHANGES","review_ref":ref(O/"independent-source-review.json"),"report_ref":ref(O/"review.md"),"findings_ref":ref(O/"findings.json"),"manifest_ref":m,"source_handoff_ref":r["source_handoff_ref"],"source_manifest_ref":r["source_manifest_ref"],"findings":["C5-R01","C5-R02"],"new_pure_controls":26,"matched":23,"counterexamples":3,"input_records":50,"input_drift":0,"new_tool_failures":0,"WinAPI_threads_native_SQL_provider_calls":0,"Main_canonical_writes":0,"whole_source_ready":False,"qualification":False,"formal_acceptance":False,"stopped":True})
print(json.dumps({"handoff":h,"manifest":m,"review":ref(O/"independent-source-review.json"),"members":len(members)},ensure_ascii=False,indent=2))

