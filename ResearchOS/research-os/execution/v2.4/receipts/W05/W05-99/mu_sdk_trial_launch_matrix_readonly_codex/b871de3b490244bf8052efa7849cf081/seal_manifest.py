import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def put(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
report=pin(O/"report.md");matrix=pin(O/"launch-matrix.json");source=json.loads((O/"source-read-integrity.json").read_bytes())["source_ref"]
assert pin(Path(source["path"]))==source
handoff={"schema":"researchos.readonly-handoff.v1","status":"STOPPED_READONLY_EXTRACTION_COMPLETE_WITH_OPEN","owner":"codex:/root/command_queue_impl","namespace":str(O),"report_ref":report,"matrix_ref":matrix,"source_ref":source,"source_unchanged_on_exit":True,"manifest_path":str(O/"manifest.json"),"open_findings":["current commit Source binding","same-PID precheck and phase protocol","qualification identity freeze and admission before provider send","actual Windows Job lifecycle including assigned-before-resume","aggregate phase timing/once accounting","qualification Host/worker tree ownership"],"observed":{"candidate_imports":0,"candidate_executions":0,"native_product_executions":0,"sql_executions":0,"model_provider_requests":0,"authority_writes":0,"canonical_or_main_git_writes":0,"new_tool_failures":0},"authority":"This extraction is not a Root grant, source acceptance, live qualification, or formal acceptance. Existing Root failure counters are not changed."}
put("handoff.json",handoff)
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!="manifest.json"]
put("manifest.json",{"schema":"researchos.raw-manifest.v1","scope":str(O),"members":members,"member_count":len(members),"self_excluded":True,"source_inputs":[source],"source_exit_match":True})
assert all(pin(Path(r["path"]))==r for r in members)
print(json.dumps({"handoff":pin(O/"handoff.json"),"manifest":pin(O/"manifest.json"),"report":report,"matrix":matrix,"members":len(members),"input_drift":0,"status":"STOPPED_READONLY_EXTRACTION_COMPLETE_WITH_OPEN"},ensure_ascii=False))

