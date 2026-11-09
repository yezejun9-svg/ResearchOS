import json,hashlib
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");O=Path(__file__).parent
OLD=R/"execution/v2.4/receipts/W13/W13-03/desktop58_failed_lease_closure_source_preparation_codex/70461c211bf5457d98d054bf62703fe1"
def ref(p):
 b=p.read_bytes();return {"path":p.relative_to(R).as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def put(n,d):
 with (O/n).open("xb") as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+"\n").encode())
 return ref(O/n)
source=ref(O/"lease_closure.sixth.v2.proposed.py")
q=json.loads((O/"request.template.json").read_bytes())
prior=R/"execution/v2.4/receipts/W13/W13-03/desktop58_failed_lease_root_read_diagnostic_codex/70ec11-645/failure-origin-645.original.json"
pr=ref(prior);assert pr["sha256"]=="6176535b771089c82b8289a53d521747628626bfaec6b3447db6f8df3030d655" and pr["bytes"]==5298
contract=json.loads((OLD/"execution-contract.json").read_bytes())
contract["source_ref"]=source;contract["namespace"]=q["namespace"];contract["input_path"]=q["namespace"]+"/original-input.json";contract["input_template_ref"]=ref(O/"request.template.json")
for k in ("draft_argv","commit_argv"):
 contract[k][5]=str(O/"lease_closure.sixth.v2.proposed.py")
 pos=contract[k].index("--source-sha256");contract[k][pos+1]=source["sha256"]
contract["prior_failed_input_preserved_ref"]=pr
contract["same_failed_input_retry"]=False
cr=put("execution-contract.json",contract)
report=put("report.json",{"schema":"researchos.source-preparation-report.v1","author":"codex:/root/w05_merge_review","decision":"SOURCE_PREPARATION_COMPLETE_PENDING_INDEPENDENT_REVIEW","source_ref":source,"base_ref":ref(OLD/"lease_closure.sixth.proposed.py"),"whole_inverse_ref":ref(O/"whole-byte-inverse.json"),"static_audit_ref":ref(O/"static-audit.json"),"pure_metadata_controls_ref":ref(O/"pure-metadata-controls.json"),"execution_contract_ref":cr,"prior_failure_ref":pr,"prior_failure_counted_again":False,"changes":["Three literal occurrences change only immutable Root output namespace/run_uuid to c550b87c595048dca4187601e57ecf24.","Keep existing exact parent permissions and add only path/sha256/bytes pointers for the two fixed checkpoint WIP closure refs.","Require each new closure ref to be an exact3key dictionary equal to its request pin; all other pointer permissions remain unchanged."],"preservation":{"all_other_functions_byte_AST_equal":19,"original_helper_functions_unchanged":13,"differences_byte_unchanged":True,"pending_origins":18,"before":[337,165,617],"after":[338,166,635],"canonical_unchanged":True,"Root_output_still_empty":True},"controls":{"actual_current_CP_positive":True,"extra_ref_key_rejected":True,"missing_ref_key_rejected":True,"unrelated_head_rejected":True,"unrelated_WIP_rejected":True,"wrong_allowed_ref_value_rejected":True,"execution_scope":"Only AST-extracted need/differences/desired_values, pure dicts and copy fault-injection; no candidate module/main or actual draft."},"actual_candidate_main":False,"actual_draft":False,"actual_CAS":False,"actual_Git_or_product":False,"formal_increment":0,"new_failure_count":0,"self_approval":False,"remaining":"F08 non-author Source/data controls review, then Root new request+once draft, F08 actual prepared review before Root commit."})
mf=put("manifest.json",{"schema":"researchos.source-manifest.v1","actor":"codex:/root/w05_merge_review","entries":[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ("manifest.json","handoff.json")],"self_excluded":True,"mutable_after_seal":False})
h=put("handoff.json",{"schema":"researchos.source-handoff.v1","actor":"codex:/root/w05_merge_review","decision":"SOURCE_PREPARATION_COMPLETE_PENDING_INDEPENDENT_REVIEW","source_ref":source,"report_ref":report,"manifest_ref":mf,"contract_ref":cr,"inverse_ref":ref(O/"whole-byte-inverse.json"),"controls_ref":ref(O/"pure-metadata-controls.json"),"new_failure_count":0,"new_failure_origins":[],"actual_draft":False,"actual_CAS":False,"status":"STOPPED"})
print(json.dumps({"source":source,"report":report,"manifest":mf,"handoff":h,"contract":cr,"new_failure_count":0},ensure_ascii=False))

