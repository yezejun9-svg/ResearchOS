import hashlib,json,re
from pathlib import Path
R=Path(r"D:\作品集\ResearchOS\research-os");O=R/"execution/v2.4/receipts/W05/W05-99/sdk_typed_cancel_actual_independent_review_codex/b8612c056c734cd2b2b299cfba761338"
P=R/"execution/v2.4/receipts/W05/W05-99/sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d";V=P/"actual-go-validation-v4-mu-cancel"
checks=[];pins={}
def ck(n,v,d=None):checks.append({"name":n,"passed":bool(v),"detail":d})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def read(p):
 p=path(p);b=p.read_bytes();key=p.relative_to(R).as_posix() if p.is_relative_to(R) else str(p)
 pins[key]={"path":key,"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)};return b
def j(p):return json.loads(read(p))
def verify(r):
 b=read(r["path"]);ck("pin:"+r["path"],hashlib.sha256(b).hexdigest()==r["sha256"] and len(b)==r["bytes"]);return b
def ref(p):
 p=path(p);read(p);return pins[p.relative_to(R).as_posix() if p.is_relative_to(R) else str(p)]
terminal=j(P/"root-validation-v4.closed.original-tool-io.json");closed=j(V/"cancel.validation.closed.json")
ck("terminal_session",terminal["initial"]["result"]["session_id"]==terminal["terminal"]["input"]["session_id"]==71205)
ck("terminal_outer_python0",terminal["terminal"]["result"]["exit_code"]==0 and terminal["terminal"]["result"]["output"].splitlines()[-1]=="ACTUAL_PYTHON_EXIT=0")
rows=[json.loads(line) for line in terminal["terminal"]["result"]["output"].splitlines() if line.startswith("{")]
ck("three_terminal_records",len(rows)==3)
for idx,row in enumerate(rows):
 r=row["invocation_ref"] if idx<2 else row["cancel_validation_ref"];verify(r)
 ck("terminal_record_link:"+str(idx),r==closed["invocation_refs"][idx] if idx<2 else path(r["path"])==V/"cancel.validation.closed.json")
 if idx<2:ck("terminal_native_zero:"+str(idx),row["actual_native_exit"]==0)
jobs=[]
for i,r in enumerate(closed["invocation_refs"]):
 iv=json.loads(verify(r));run=iv["result"];c=run["job_cleanup"]
 ck("job_native0:"+str(i),type(run["actual_exit"]) is int and run["actual_exit"]==iv["actual_native_exit"]==0 and iv["exception"] is None)
 ck("job_identity:"+str(i),type(run["owned_child_pid"]) is int and run["owned_child_pid"]>0 and type(run["creation_time_100ns"]) is int and run["creation_time_100ns"]>0)
 ck("job_not_timedout:"+str(i),run["timed_out"] is False and run["error"] is None and run["resumed"] is True)
 ck("job_cleanup:"+str(i),c["errors"]==[] and c["active_processes_last_observed"]==0 and all(c[k] is True for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed")))
 stdout=verify(iv["stdout_ref"]);stderr=verify(iv["stderr_ref"])
 intent=j(V/("mu-bundle-build.intent.json" if i==0 else "mu-typed-cancel-actual-bundle.intent.json"))
 if i==0:build=intent;build_stdout=stdout;build_stderr=stderr
 else:
  test=iv;teststdout=stdout.decode("utf8")
  ck("test_exact_intent",iv["argv"]==intent["argv"] and iv["environment"]==intent["public_environment"] and iv["cwd"]==intent["cwd"])
 jobs.append({"invocation_ref":r,"intent":intent,"pid":run["owned_child_pid"],"birth_100ns_decimal":str(run["creation_time_100ns"]),"cleanup":c})
bundle=verify(closed["bundle_ref"]);meta=json.loads(verify(closed["bundle_metadata_ref"]))
ck("build_original_metadata_equals_stdout",meta==json.loads(build_stdout))
ck("actual_bundle_matches_metadata",hashlib.sha256(bundle).hexdigest()==meta["bundle_sha256"] and len(bundle)==meta["bundle_bytes"]==13786596)
ck("test_used_frozen_bundle",path(test["environment"]["RESEARCHOS_MU_BUNDLE"]).resolve()==path(closed["bundle_ref"]["path"]).resolve())
ck("test_exact_selector",test["argv"][1:]==["test","-count=1","-timeout=90s","-v","./internal/domain","-run","^TestRuntimeMuTypedCancelStopsTransport$"])
ck("test_actual_pass_not_skip",re.findall(r"^--- (PASS|FAIL|SKIP): ([^ ]+)",teststdout,re.M)==[("PASS","TestRuntimeMuTypedCancelStopsTransport")] and "no tests to run" not in teststdout and "SKIP" not in teststdout)
ck("test_http_sandbox_single_request_assertions","MU_CANCEL inflight_HTTP_stopped=true sandbox_stopped=true provider_calls=1" in teststdout)
worker=verify(build["worker_source_ref"]);builder=verify(build["build_script_ref"])
ck("bundle_current_worker_hash",hashlib.sha256(worker).hexdigest()==meta["source_sha256"])
ck("fixed_versions",meta["mu_commit"]=="8dfebe36508ac0c2508735bb866756dab9283e74" and meta["sdk_version"]==meta["ai_version"]=="0.87.1" and meta["esbuild_version"]=="0.28.2" and meta["vendored_files_verified"]==5083)
lock=j(R/"execution/toolchains/locked.json")
for name in ("go","node","git"):
 tool=lock["tools"][name];ck("current_pinned_tool:"+name,hashlib.sha256(read(tool["path"])).hexdigest()==tool["sha256"])
ck("actual_builder_node_and_script",path(build["argv"][0]).resolve()==path(lock["tools"]["node"]["path"]).resolve() and path(build["argv"][1]).resolve()==path(build["build_script_ref"]["path"]).resolve())
ck("actual_test_go",path(test["argv"][0]).resolve()==path(lock["tools"]["go"]["path"]).resolve())
runner=read(P/"validate_five_go.local_owned.v4.mu_cancel.py").decode("utf8")
ck("builder_job_argv_matches_source",'helper.run_owned([str(node), str(build_script), str(bundle)], str(ROOT), env, out, err, 180)' in runner)
ck("inherited_build_environment",build["public_environment"]=={k:v for k,v in test["environment"].items() if k!="RESEARCHOS_MU_BUNDLE"})
ck("builder_original_warning_preserved","ignored-bare-import" in build_stderr.decode("utf8"))
testsource=read(R/"internal/domain/runtime_model_windows_test.go").decode("utf8")
fixture_source=read(R/"internal/domain/domain_test.go").decode("utf8")
ck("actual_test_typed_path_source",'runtimeMuCancelStopsTransport(t, true)' in testsource and '"session.control"' in testsource and '"action": "CANCEL"' in testsource and '"ACKNOWLEDGED"' in testsource)
ck("http_stopped_assertion_source",'<-r.Context().Done(); close(stopped)' in testsource and 'inflight model request survived cancellation' in testsource)
ck("worker_stopped_assertion_source",'case e := <-done:' in testsource and 'cancelled worker did not stop' in testsource and 'cancelled turn was reported successful' in testsource)
ck("single_local_request_assertion_source",'calls.Load() != 1' in testsource and 'cancelled model request retried' in testsource)
ck("local_fixture_route_source",'server := httptest.NewServer(handler)' in fixture_source and 'modelFixtureConfig(server.URL + "/v1/chat/completions")' in testsource and 'MeasurementMode: "FIXTURE"' in testsource)
prep=j(P/"preparation.json");adopt=j(P/"main-adoption.closed.json")
for row in prep["mapping"]:ck("main_still_reviewed:"+row["target"],read(R/row["target"])==verify(row["prepared_ref"])==verify(row["proposal_ref"]))
closure=j(adopt["closure_ref"]["path"])
for r in closure["canonical_refs"]:verify(r)
cp,ow=[j(closure["canonical_refs"][i]["path"]) for i in (0,1)]
ck("canonical_still340168672",[cp["revision"],ow["revision"],len(cp["failure_counters"])]==[340,168,672])
ck("receipt_fixture_scope",closed["measurement_mode"]=="LOCAL_HTTP_FIXTURE_WITH_ACTUAL_CURRENT_MU_BUNDLE" and closed["actual_external_provider_requests"]==0 and closed["local_fixture_requests"]==1 and closed["formal_acceptance_delta"]==0)
for f in V.iterdir():
 if f.is_file():read(f)
report={"schema":"researchos.sdk-typed-cancel-actual-independent-audit.v1","checks":checks,"failed_checks":[x for x in checks if not x["passed"]],"pins":list(pins.values()),"jobs":jobs,"raw_test_stdout":teststdout,"bundle_metadata":meta,"closed_ref":ref(V/"cancel.validation.closed.json"),"root_original_io_ref":ref(P/"root-validation-v4.closed.original-tool-io.json"),"main_refs":[ref(R/row["target"]) for row in prep["mapping"]],"canonical_refs":closure["canonical_refs"],"builder_descendants":"Node builder runs Git rev-parse and esbuild under inherited owned Job; no separate per-child invocation or image-event ledger emitted by this local helper","real_external_provider_qualification":False,"actual_reviewer_native_calls":0}
with (O/"audit.json").open("x",encoding="utf8",newline="\n") as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write("\n")
print(json.dumps({"checks":len(checks),"failed_checks":report["failed_checks"],"pins":len(pins),"bundle_sha256":meta["bundle_sha256"],"audit_ref":ref(O/"audit.json")},ensure_ascii=False))
