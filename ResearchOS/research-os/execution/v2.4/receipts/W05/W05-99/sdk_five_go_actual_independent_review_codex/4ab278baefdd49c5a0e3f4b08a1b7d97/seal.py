import hashlib,json
from pathlib import Path
R=Path(r"D:\作品集\ResearchOS\research-os");O=R/"execution/v2.4/receipts/W05/W05-99/sdk_five_go_actual_independent_review_codex/4ab278baefdd49c5a0e3f4b08a1b7d97"
P=R/"execution/v2.4/receipts/W05/W05-99/sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d"
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def pin(p):
 p=path(p);b=p.read_bytes();return {"path":p.relative_to(R).as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def j(p):return json.loads(path(p).read_bytes())
def save(n,d):
 with (O/n).open("x",encoding="utf8",newline="\n") as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write("\n")
 return pin(O/n)
a=j(O/"audit.json");assert not a["failed_checks"]
for r in a["pins"]:
 p=pin(r["path"]);assert p["sha256"]==r["sha256"] and p["bytes"]==r["bytes"],r["path"]
terminal=j(P/"root-validation-v3.closed.original-tool-io.json")
assert terminal["actual_outer_exit"]==terminal["actual_python_exit"]==0 and terminal["actual_native_exits"]==[0]*4
assert terminal["original_initial_result"]["session_id"]==89547
poll=terminal["terminal_polls"][-1];assert poll["input"]["session_id"]==89547 and poll["result"]["exit_code"]==0
lines=poll["result"]["output"].splitlines();assert lines[-1]=="ACTUAL_PYTHON_EXIT=0"
records=[json.loads(x) for x in lines if x.startswith("{")]
assert len(records)==5
v3=j(P/"actual-go-validation-v3-fixtures/validation.closed.json")
for i,row in enumerate(records):
 r=row["invocation_ref"] if i<4 else row["validation_ref"]
 actual=pin(r["path"]);assert actual["sha256"]==r["sha256"] and actual["bytes"]==r["bytes"]
 if i<4:assert row["actual_native_exit"]==0 and r==v3["operations"][i]
review={"schema":"researchos.sdk-five-go-actual-independent-review.v1","reviewer_id":"codex:/root/w05_merge_review","executor_id":"codex:/root","decision":"LOCAL_BUILD_AND_PASSED_TEST_SUBSET_VERIFIED_TYPED_CANCEL_SKIPPED","requested_changes":[],"source_adoption_review_only":False,"current_main_five_go_bytes_equal_reviewed_proposals":True,"main_refs":a["actual_main_targets"],"canonical_tuple":[340,168,672],"canonical_refs":a["canonical_refs"],"audit_ref":pin(O/"audit.json"),"checks":391,"failed_checks":[],"fresh_preseal_rehashed_files":402,"v3_terminal_chain_independently_checked":True,"v3_original_tool_io_ref":pin(P/"root-validation-v3.closed.original-tool-io.json"),"v3_validation_ref":pin(P/"actual-go-validation-v3-fixtures/validation.closed.json"),"actual_adoption_ref":pin(P/"main-adoption.closed.json"),"scope7_closure_ref":j(P/"main-adoption.closed.json")["closure_ref"],"native_job_review":{"scope7_owned_git":12,"scope7_git_native_zero":12,"go_operations":8,"go_native_zero":6,"go_expected_retained_native_nonzero":2,"all20_original_raw_stream_pins_and_job_cleanup_closed":True,"pid_birth_values_read_as_python_integers":True,"original_layer_exit_not_inferred":True},"passed_test_subset":{"top_level_total":21,"domain_s1_fix":10,"cli_inline":6,"cli_strict":1,"host_control":4,"strict_cli_actual_binary_fixture_invocations":34,"strict_cli_positive_exits":2,"strict_cli_expected_nonzero_exits":32,"strict_cli_full_run_results_including_subtests":59,"zero_tests_or_assertion_elision_claim":False,"no_tests_to_run_warnings":False,"host_control_skips":0,"strict_cli_skips":0},"unverified":[{"test":"TestRuntimeMuTypedCancelStopsTransport","status":"SKIP","reason":"requires explicitly built immutable Mu bundle; RESEARCHOS_MU_BUNDLE absent in v2 environment","stdout_ref":next(x["stdout_ref"] for x in a["test_summaries"] if x["operation"].endswith("/domain-qualification")),"independent_actual_cancel_acceptance":False}],"failures_preserved":[{"index":675,"origin_ref":pin(P/"failure-origin.675.actual-go-build.original.json"),"outer_python_native":[1,1,1],"cause":"-mod=vendor cannot use the repository vendor content as a consistent Go module vendor tree","recovery":"new immutable v2 used -mod=readonly and GOPROXY=off"},{"index":676,"origin_ref":pin(P/"failure-origin.676.actual-cli-snapshot.original.json"),"outer_python_native":[1,1,1],"cause":"compiled CLI and owned evidence directory missing for strict-response fixtures","recovery":"new immutable v3 builds binary and supplies fixture prerequisites; original suite failure retained"}],"scope_limits":["Local Go compilation and original fixture tests establish the recorded subset only.","Typed cancel was not exercised by v2; later separately supplied immutable-bundle execution requires its own actual review.","Tests use local fixtures/httptest/SQLite; this is not the authorized real provider qualification1+ordinary2 trial.","No new commit or current Main checkpoint update is established by this review."],"source_runtime_qualification":False,"formal_acceptance_delta":0,"reviewer_native_or_git_calls":0,"reviewer_main_or_canonical_writes":0,"new_actual_tool_failures":0,"original_tool_io_ref":pin(O/"original-tool-io.json")}
rr=save("review.json",review)
mf=save("manifest.json",{"schema":"researchos.receipt-manifest.v1","owner":"codex:/root/w05_merge_review","members":[pin(p) for p in sorted(O.iterdir()) if p.is_file()],"self_excluded":True,"handoff_excluded":True})
hd=save("handoff.json",{"schema":"researchos.sdk-five-go-actual-independent-handoff.v1","decision":review["decision"],"review_ref":rr,"manifest_ref":mf,"checks":391,"failed_checks":[],"passed_top_level_tests":21,"skipped_typed_cancel":1,"source_runtime_qualification":False,"formal_acceptance_delta":0})
print(json.dumps({"review_ref":rr,"manifest_ref":mf,"handoff_ref":hd},ensure_ascii=False))
