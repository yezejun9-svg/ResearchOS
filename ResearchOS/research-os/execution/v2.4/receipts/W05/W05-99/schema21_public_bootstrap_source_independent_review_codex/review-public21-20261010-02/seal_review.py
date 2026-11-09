import hashlib,json,os
from pathlib import Path
N=Path(__file__).resolve().parent
def pin(p):
 p=Path(p);b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write(p,data):
 with Path(p).open("xb") as f:
  f.write((json.dumps(data,ensure_ascii=False,indent=2)+"\n").encode());f.flush();os.fsync(f.fileno())
 return pin(p)
inputs=json.loads((N/"source-inputs.json").read_bytes())
for ref in inputs["references"]:
 if pin(ref["path"])!=ref:raise ValueError("SEAL_INPUT_DRIFT:"+ref["path"])
decision=json.loads((N/"source-decision.json").read_bytes())
hdf={"schema":"researchos.schema21-public-bootstrap-independent-source-review-handoff.v1",
 "reviewer":"codex:/root/attach_restore_independent_review","decision":decision["decision"],
 "source_hdf_ref":decision["source_hdf_ref"],"source_mf_ref":decision["source_mf_ref"],
 "source_runner_ref":decision["runner_ref"],"source_contract_ref":decision["contract_ref"],
 "decision_ref":pin(N/"source-decision.json"),"delta_review_ref":pin(N/"delta-review.json"),
 "tool_io_ref":pin(N/"actual-tool-io.json"),"source_guard_ref":pin(N/"source-guard.closed.json"),
 "reviewed_input_count":len(inputs["references"]),"new_AST_only_fault_controls":12,"actual_author_pairs_checked":12,
 "resolved_findings":["PUBLIC21-OBSERVATION-001"],"findings":[],
 "original_mechanical_failures_created":[],"old146_not_rerun":True,"author56_not_rerun":True,
 "old_counterexample_not_rerun":True,"Root_scope_or_runtime_qualification_granted":False,
 "Leaf_Native_Go_SQL_model_TP_calls":0,"execution_grant":False,"formal_acceptance":False,"parent_acceptance":False,
 "STOP":True}
write(N/"HDF.json",hdf)
members=[pin(p) for p in sorted(N.rglob("*")) if p.is_file() and p.name not in ("MF.json","postseal-tool-io.json")]
write(N/"MF.json",{"schema":"researchos.independent-source-review-manifest.v1","members":members,
 "member_count":len(members),"exclusions":["MF.json self","postseal-tool-io.json separately pinned"]})
print(json.dumps({"HDF":pin(N/"HDF.json"),"MF":pin(N/"MF.json"),"decision":pin(N/"source-decision.json"),
                  "member_count":len(members)},ensure_ascii=False))

