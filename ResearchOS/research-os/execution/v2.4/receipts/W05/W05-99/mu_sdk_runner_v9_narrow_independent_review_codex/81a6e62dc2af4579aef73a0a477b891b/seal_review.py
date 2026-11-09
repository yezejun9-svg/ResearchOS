import hashlib,json,pathlib
O=pathlib.Path(__file__).resolve().parent
def ref(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write(name,data):
 p=O/name;p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");return ref(p)
a=json.loads((O/"audit.json").read_text(encoding="utf-8"))
for r in a["inputs"]:
 n=ref(pathlib.Path(r["path"]));assert n["sha256"]==r["sha256"] and n["bytes"]==r["bytes"]
review={"schema":"researchos.mu-sdk-trial-independent-source-review.v1","actor_id":"codex:/root/command_queue_impl","reviewer_id":"codex:/root/command_queue_impl","reviewer":"codex:/root/command_queue_impl","author_id":"codex:/root","independent":True,"decision":"READY_SOURCE_ONLY","verdict":"APPROVE_SOURCE_ONLY","scope":"V9_RUNNER_SINGLE_WRITE_PATHS_LITERAL_DELTA_ONLY","source_ref":a["source_ref"],"prior_source_ref":a["prior_source_ref"],"prior_review_ref":a["prior_review_ref"],"audit_ref":ref(O/"audit.json"),"controls_ref":ref(O/"independent-controls.json"),"original_tool_io_ref":ref(O/"original-tool-io.json"),"report_ref":ref(O/"report.md"),"verification":{"changed_function":"validate_input","only_delta":"write_paths == {} to == []","other39_full_function_bytes_unchanged":True,"top_level_assignments_unchanged":True,"template_unchanged":True,"full_forward_inverse_exact":True,"author_diffs_independently_regenerated_exact":True,"new_checks":8,"matched":8,"prior_v8_checks_reused":47,"prior_v8_checks_rerun":0,"inputs":len(a["inputs"]),"unique_inputs":len({r["path"] for r in a["inputs"]}),"drift":[]},"main_contract_ref":a["main_runtime_tool_paths_ref"],"main_contract_lines":a["main_contract_lines"],"requested_changes":[],"open":["Controller C4 and Observer O3 whole-tuple independent review pending.","Observer O2 RUNNER_REF still pins v8; O2 plus v9 is not a reviewed whole chain.","Actual OS Job lifecycle / trusted Host / provider trial / qualification / formal acceptance remain open."],"runtime_registration_issued":False,"execution_authority_issued":False,"trial_executed":False,"actual_provider_requests":0,"source_runtime_qualification":False,"source_acceptance":False,"formal_case_accepted_delta":0,"main_writes":0,"canonical_writes":0,"candidate_module_imports":0,"candidate_validate_input_or_main_calls":0,"sql_calls":0,"native_windows_api_calls":0,"product_native_executions":0,"new_tool_failures":2,"root_assigned_failure_numbers":[690,691],"failure_origin_refs":[ref(O/"failure-origin.690.json"),ref(O/"failure-origin.691.json")],"stop_after_source_review":True}
rr=write("review.json",review)
write("seal-input-verification.json",{"records":len(a["inputs"]),"drift":[]})
print(json.dumps({"review_ref":rr,"failure_origin_refs":review["failure_origin_refs"]},ensure_ascii=False,indent=2))

