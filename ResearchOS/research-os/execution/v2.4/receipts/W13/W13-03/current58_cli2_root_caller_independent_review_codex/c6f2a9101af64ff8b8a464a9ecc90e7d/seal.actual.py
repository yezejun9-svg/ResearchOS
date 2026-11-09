"""Seal independent source review artifacts only, without candidate imports or execution."""
import sys
sys.dont_write_bytecode = True
import hashlib
import json
from pathlib import Path
OUT=Path(__file__).resolve().parent
def pin(path):
    raw=Path(path).read_bytes()
    return {"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def save(name,value):
    with (OUT/name).open("xb") as stream:
        stream.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode("utf-8"))
if not (sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode):
    raise RuntimeError("Pinned isolated Python flags required")
for name in ["review.json","static-audit.json","tool-observations.json","failure-origin.discovery-rg-no-match.json","inputs.before.json","inputs.after.json"]:
    json.loads((OUT/name).read_bytes())
handoff={
 "schema":"researchos.current58-cli2-root-caller-independent-review-handoff.v1",
 "author":"codex:/root/current58_caller_review",
 "decision":"READY_SOURCE_PREPARATION_ONLY","state":"STOPPED",
 "review_ref":pin(OUT/"review.json"),"static_audit_ref":pin(OUT/"static-audit.json"),
 "tool_observations_ref":pin(OUT/"tool-observations.json"),
 "new_failure_origins":[pin(OUT/"failure-origin.discovery-rg-no-match.json")],
 "frozen_inputs":8,"frozen_input_drift":0,"inverse_edits":5,"original_three_defs_AST_equal":True,
 "original_result_try_except_finally_exit_tail_bytes_equal":True,
 "future_grant_SHA":None,"future_Root_output_directory":None,"future_currentbinding_ref":None,
 "actual_candidate_native_exit":None,"caller_OS_lifecycle_qualification":False,
 "source_acceptance":False,"formal_increment":0,"candidate_imported":False,"candidate_executed":False,
 "Go_SQL_HTTP_Node_SDK_model_candidate_calls":0,
 "actual_review_python_native_exit":0,"native_evidence":"tool-observations.json explicit ACTUAL_PYTHON_EXIT0 chunk 80977e",
 "fixed_failurecut532_unchanged":True,"knownobserved540_source":"Root reported539 + this one new discovery origin; no canonical registration performed.",
 "manifest_relative_path":"manifest.json"
}
save("handoff.json",handoff)
files=sorted(p for p in OUT.iterdir() if p.is_file())
rows=[pin(p) for p in files]
save("manifest.json",{"schema":"researchos.source-review-manifest.v1","count":len(rows),"entries":rows,"self_excluded":True})
print(json.dumps({"decision":"READY_SOURCE_PREPARATION_ONLY","state":"STOPPED","review_ref":pin(OUT/"review.json"),"handoff_ref":pin(OUT/"handoff.json"),"manifest_ref":pin(OUT/"manifest.json"),"origin_ref":pin(OUT/"failure-origin.discovery-rg-no-match.json"),"count":len(rows)},ensure_ascii=False))

