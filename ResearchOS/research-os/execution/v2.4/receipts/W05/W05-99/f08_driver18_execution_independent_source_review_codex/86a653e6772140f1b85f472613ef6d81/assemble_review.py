from pathlib import Path
import hashlib,json
OWN=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_execution_independent_source_review_codex/86a653e6772140f1b85f472613ef6d81")
def ref(p):
 raw=p.read_bytes()
 return {"path":p.as_posix(),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def save(n,d):
 p=OWN/n
 if p.exists():raise RuntimeError("new-only output exists")
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
before=json.loads((OWN/"inputs.before.json").read_bytes())
def find(filename):
 return next(r for r in before if Path(r["actual"]["path"]).name==filename)["actual"]
controller=find("driver18_controller.proposed.py");launcher=find("launch.proposed.py")
save("source-review.json",{
 "schema":"researchos.driver18.execution_preparation.independent_review.v1",
 "actor":"/root/f08_whole_scope_review","non_author":True,"verdict":"REQUEST_CHANGES",
 "source_refs":{"controller":controller,"launcher":launcher,"scope":find("scope.UNBOUND.proposed.json"),"resource_authority_contract":find("resource-and-authority-contract.json"),"I16_contract":find("I16-provenance-contract.json"),"finite_roster":find("finite-operation-roster.json")},
 "findings":[
  {"id":"D18-C01","severity":"Critical","ref":controller,"lines":[255,258],"condition":"main returns 0 and sys.exit(0) raises SystemExit, caught by except BaseException","effect":"every successful prepare/execute emits ENTRY failure and exits1; launcher job_ok refuses","fix":"compute exit_code=main() inside try; preserve actual exception branch; call sys.exit(exit_code) after try/except","do_not":"treat1 as success or authorize execute from prepared report without actual native/job success","verification":"source reasoning only; no candidate execution"},
  {"id":"D18-I01","severity":"Important","ref":controller,"lines":[143,151,193,224],"condition":"native starts before3300 but requested600/750 exceeds remaining","effect":"inner declared3300 deadline can be exceeded, outer3600 becomes termination mechanism","fix":"absolute inner deadline; finite min(nominal, remaining minus approved cleanup reserve), save nominal/effective timeouts and reject expired final qualification","example":"start3299 with750 permits until4049 before outer kill","verification":"source reasoning only"}
 ],
 "roster":{"ordered_cases":[f"I{i:02d}" for i in range(1,17)]+["I18"],"case_count":17,"native_count":30,"arithmetic":{"version":1,"graphs":3,"builds":4,"buildinfos":3,"cases":17,"I16_extra_phases":2},"cap":32,"I17":"OPEN_NOT_AUTHORIZED","all18_pass":False},
 "caps":{"native_calls":32,"compiler_seconds":600,"test_seconds":750,"inner_seconds":3300,"outer_seconds":3600,"cleanup_seconds":5,"images":64,"compiler_processes":2048,"job_active_processes":16},
 "I16":{"producer_lines":[17,41],"old_probe_lines":[19,44],"controller_lines":[210,230],"test_source_lines":[245,258],"real_cause":"no such function: ros_i16, *sqlite.Error primary1; before/after count1","third_stage":"original x7/count1; actual insert9/count2","closed_bytes":"exact before/after equality, no sidecars, fresh copies","ABI_coexistence":False,"report_alone_authority":False,"additional_SQL_full_inventory":"not executed / explicitly OPEN if separately required"},
 "I18":{"original_regression_ref":find("14-func_test.go.input.txt"),"original_source_hash":"85e63e33c8d22d89e426dd33dff7bfece1f472b4796cd067718d9a6d22fb4e54","bytes":35317,"direct_original_body":True,"two1000x200ms_loops":"retained unchanged / NOT_RUN"},
 "startup_and_authority":{"unbound_scope":"rejects before target","authority_adapter":"OPEN; separately reviewed actual Root adapter required","two_phase":"prepare grants do not authorize execute; exact successful prepared/result/native/job/manifest validation needed","fake_authorized_boolean_implemented":False,"resource_catalog":"NULL and incomplete unknowns reject; actual offline transitive Go/Python/OS universe still required","controller_qualifies_actual_source":"False; candidate prep only"},
 "helpers":{"utility":find("runner.v6.proposed.py"),"outer_owned":find("windows_owned_process.py"),"native_debug":find("windows_debug_job_tree.py"),"debug_active_limit_line":450,"debug_unknown_module_image_lines":[316,321],"debug_cleanup_seconds":5,"python_lifecycle_proof":"point-in-time only"},
 "source_closure":{"actual_selected_go_graph":"proposed -mod=readonly -compiled -deps -test / actual moduleDir and qualifiedReplace checks","fresh_build_cache_WORK_archives":"proposed fresh namespace only; no old exe","local_replace_sum_auth":"not claimed","1899_resource_review":"reused exact sealed independent source resource evidence; not rehashed fullmodule"},
 "minimal_future_verification":{"all_status":"NOT_RUN","entry_wrapper":["actual successful metadata prepare exit0 and correct receipt, Go_calls0","original failure remains actual nonzero and original stderr; no rewritten0/1","execute grant cannot proceed before authenticated prepare completion"],"deadline":["remaining budget below nominal produces effective bounded helper timeout with cleanup reserve","expired budget cannot launch another native or qualify late final result"],"main_cases":"only after newly sealed source, fresh Root grant/resources; I01-I16,I18 exactselectors once"},
 "mutation_counts":{"Main":0,"canonical":0,"module":0,"cache":0,"old_receipts":0,"failure_counters":0},
 "execution_counts":{"target":0,"Go":0,"gofmt":0,"AST_typecheck":0,"SQL":0,"driver":0,"HTTP":0,"Node":0,"SDK":0,"model":0},
 "new_origins":[],"new_origin_count":0,"failure_count_reset":False,
 "source_acceptance":False,"SQL24_permission":False,"formal_increment":0
})
print(json.dumps({"verdict":"REQUEST_CHANGES","critical":1,"important":1,"native_execution":0}))
