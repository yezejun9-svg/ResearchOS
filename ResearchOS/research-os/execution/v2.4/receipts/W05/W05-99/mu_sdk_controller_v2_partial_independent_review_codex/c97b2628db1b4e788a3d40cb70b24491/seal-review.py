import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
PREV=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_controller_observer_independent_source_review_codex/da1388ae95d14653a26a1f167574d251")
def pin(p):
 raw=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def write(n,v):
 with (O/n).open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
intake=json.loads((O/"intake.json").read_bytes());rows=intake["rows"]
pm=pin(PREV/"manifest.json");assert pm["sha256"]=="dd43148f0ae2b7cf000003dfa59732378bc1fcd564e760cb41b055aa63858025" and pm["bytes"]==25615
prior=json.loads((PREV/"manifest.json").read_bytes())
for n in ["independent-source-review.json","independent_controls.py","controls.json"]:
 expected=next(r for r in prior["members"] if Path(r["path"]).name==n);assert pin(PREV/n)==expected
 assert next(r["source_ref"] for r in rows if Path(r["source_ref"]["path"]).name==n)==expected
for row in rows:assert pin(Path(row["source_ref"]["path"]))==row["source_ref"]
old=next(r["source_ref"] for r in rows if Path(r["source_ref"]["path"]).name=="controller.py" and "mu_sdk_controller_source_codex" in r["source_ref"]["path"]);assert old["sha256"]=="ddcf54587a9cb32cff4470ebf2fa2d34a57ef061dc64e27c71b5f7b610a39ae8"
new=next(r["source_ref"] for r in rows if Path(r["source_ref"]["path"]).name=="controller.py" and "revision_v2" in r["source_ref"]["path"])
rr=json.loads((O/"runner-env-read.json").read_bytes());rref={k:rr[k] for k in ("path","sha256","bytes")};assert pin(Path(rref["path"]))==rref
for ref in [pm,rref]:
 p=Path(ref["path"]);raw=p.read_bytes();snap=O/(ref["sha256"]+".raw")
 if not snap.exists():snap.write_bytes(raw)
 rows.append({"source_ref":ref,"snapshot_ref":pin(snap)})
review={"schema":"researchos.mu-sdk-controller-partial-independent-source-review.v2","decision":"REQUEST_CHANGES_WITH_PARTIAL_FIXES","actor_id":"codex:/root/command_queue_impl","scope":["CTRL-R01","CTRL-R03","CTRL-R04"],"source_ref":new,"previous_source_ref":old,"previous_review_ref":pin(PREV/"independent-source-review.json"),"results":{"CTRL-R01":"PASS_IN_SCOPE_SOURCE_ONLY","CTRL-R03":"PASS_IN_SCOPE_SOURCE_ONLY","CTRL-R04":"PARTIAL_FIX_REMAINING_BASIS_ENV_GAP"},"remaining_finding":{"id":"CTRL-R04","priority":2,"lines":[147,153],"accepted_unbound_keys":["ComSpec","PATHEXT"],"runner_basis_unchanged":True,"required":"Use the exact eight-key closed process environment or review a synchronized basis/observer extension"},"controls_ref":pin(O/"controls.json"),"report_ref":pin(O/"review.md"),"forward_inverse_byte_exact":True,"independent_cases":19,"expected_guard_mismatches":2,"whole_chain_ready":False,"formal_acceptance":False,"execution_ready":False,"new_tool_failures":0,"native_SQL_provider_calls":0,"candidate_module_imports":0,"canonical_Main_writes":0,"open_unchanged":["CTRL-R02","CTRL-R05","CTRL-R06","actual_job_callback_and_cleanup","trusted_qualification_host"],"source_inputs":len(rows),"input_drift":0}
write("independent-review.json",review)
write("source-exit-integrity.json",{"rows":rows,"input_drift":0,"input_count":len(rows),"prior_input_membership_verified":True})
print(json.dumps({"decision":review["decision"],"review_ref":pin(O/"independent-review.json"),"report_ref":pin(O/"review.md"),"input_count":len(rows),"input_drift":0,"new_tool_failures":0},ensure_ascii=False))

