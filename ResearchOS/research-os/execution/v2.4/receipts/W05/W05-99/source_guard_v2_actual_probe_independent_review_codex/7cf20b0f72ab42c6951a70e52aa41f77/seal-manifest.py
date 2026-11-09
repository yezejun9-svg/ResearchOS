import hashlib,json,pathlib
O=pathlib.Path(__file__).resolve().parent
def ref(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write(n,x):
 p=O/n;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");return ref(p)
r=json.loads((O/"review.json").read_bytes())
members=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ("manifest.json","handoff.json")]
m=write("manifest.json",{"schema":"researchos.independent-actual-component-review-manifest.v1","actor":"codex:/root/command_queue_impl","decision":r["decision"],"members":members,"member_count":len(members),"excludes":["manifest.json","handoff.json"]})
h=write("handoff.json",{"schema":"researchos.independent-actual-component-review-handoff.v1","actor":"codex:/root/command_queue_impl","decision":r["decision"],"review_ref":ref(O/"review.json"),"report_ref":ref(O/"review.md"),"manifest_ref":m,"source_handoff_ref":r["source_handoff_ref"],"source_manifest_ref":r["source_manifest_ref"],"guard_source_ref":r["guard_source_ref"],"root_original_tool_io_ref":r["root_original_tool_io_ref"],"actual_pid":41408,"root_outer_parent_child_exits":[0,0,0],"input_records":41,"input_drift":0,"old_failed_probe_numbers_preserved":[696,698],"old698_raw_success_and_error":"UNKNOWN_NOT_BACKFILLED","new_reviewer_tool_failures":0,"reviewer_WinAPI_SQL_product_provider_executions":0,"reviewer_Main_canonical_writes":0,"whole_controller_ready":False,"qualification":False,"formal_acceptance":False,"stopped":True})
print(json.dumps({"handoff":h,"manifest":m,"review":ref(O/"review.json"),"members":len(members)},ensure_ascii=False,indent=2))

