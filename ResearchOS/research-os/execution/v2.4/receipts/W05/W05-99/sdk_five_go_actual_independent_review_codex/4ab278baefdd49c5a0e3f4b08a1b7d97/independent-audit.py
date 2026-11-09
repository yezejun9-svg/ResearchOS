import hashlib,json,re
from pathlib import Path
R=Path(r"D:\作品集\ResearchOS\research-os");O=R/"execution/v2.4/receipts/W05/W05-99/sdk_five_go_actual_independent_review_codex/4ab278baefdd49c5a0e3f4b08a1b7d97"
P=R/"execution/v2.4/receipts/W05/W05-99/sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d"
C=R/"execution/v2.4/receipts/W13/W13-03/desktop58_scope7_failed_lease_close_cas_codex/b342fa5adb1e42d8813317e11e9f22c0"
checks=[];pins={};jobs=[];summaries=[]
def ck(n,v,d=None):checks.append({"name":n,"passed":bool(v),"detail":d})
def path(p):
 p=Path(p);return p if p.is_absolute() else R/p
def read(p):
 p=path(p);b=p.read_bytes();rp=p.relative_to(R).as_posix()
 pins[rp]={"path":rp,"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)};return b
def j(p):return json.loads(read(p))
def verify(r):
 b=read(r["path"]);ck("pin:"+r["path"],len(b)==r["bytes"] and hashlib.sha256(b).hexdigest()==r["sha256"]);return b
def ref(p):read(p);return pins[path(p).relative_to(R).as_posix()]
def checkjob(iv,name,expected):
 r=iv["result"];c=r["job_cleanup"]
 ck(name+":exact_native_exit",type(r["actual_exit"]) is int and r["actual_exit"]==expected)
 ck(name+":no_timeout_error",r["timed_out"] is False and r["error"] is None and r["resumed"] is True)
 ck(name+":real_pid_birth",type(r["owned_child_pid"]) is int and r["owned_child_pid"]>0 and type(r["creation_time_100ns"]) is int and r["creation_time_100ns"]>0)
 ck(name+":cleanup",c["errors"]==[] and c["active_processes_last_observed"]==0 and all(c[k] is True for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed")))
 out=verify(iv["stdout_ref"]);err=verify(iv["stderr_ref"])
 jobs.append({"name":name,"actual_exit":expected,"pid":r["owned_child_pid"],"birth_100ns_decimal":str(r["creation_time_100ns"]),"cleanup":c,"argv":iv["argv"]})
 return out,err
prep=j(P/"preparation.json");adopt=j(P/"main-adoption.closed.json")
ck("actual_adoption_closed_pin",ref(P/"main-adoption.closed.json")["sha256"]=="6e78a72689d2c2f6c15bafcc319c9082894bb21fba178ada4498213b22bdbfeb")
for row,target in zip(prep["mapping"],adopt["targets"]):
 b=verify(target);ck("current_main_equals_reviewed:"+row["target"],b==verify(row["proposal_ref"])==verify(row["prepared_ref"]))
 backup=verify(row["backup_ref"]);ck("full_original_backup:"+row["target"],hashlib.sha256(backup).hexdigest()==row["before_ref"]["sha256"] and len(backup)==row["before_ref"]["bytes"])
closure=j(adopt["closure_ref"]["path"]);verify(adopt["closure_ref"])
current=[verify(r) for r in closure["canonical_refs"]]
cp,ow=map(json.loads,current[:2])
ck("current_tuple_still340168672",[cp["revision"],ow["revision"],len(cp["failure_counters"])]==[340,168,672])
ck("two_failed_closed_states",cp["work_in_progress"]["desktop58_finite_validation_state"]==ow["card_path_bindings"]["W13-03"]["subtasks"]["desktop58_finite_validation"]["state"]=="FAILED_EXECUTION_CLOSED_QUALIFICATION_WITHHELD")
mf=j(C/"manifest.closed.json")
for x in mf["members"]:verify(x)
ck("closed_cas_exact_inventory",{x["path"] for x in mf["members"]}=={p.relative_to(R).as_posix() for p in C.iterdir() if p.is_file() and p.name!="manifest.closed.json"})
gitfiles=sorted(C.glob("*.invocation.json"));ck("exact12_git_jobs",len(gitfiles)==12)
expectedgroups={"commit.before","commit.pre-replace-0","commit.pre-replace-1","commit.after"}
ck("git_group_names",{p.name.rsplit(".",3)[0] for p in gitfiles}==expectedgroups)
for p in gitfiles:
 iv=j(p);out,err=checkjob(iv,"lease:"+p.name,0)
 ck("git_original_layers:"+p.name,iv["actual_stage_native_exit"]==0 and iv["wrapper_error"] is None and iv["qualifies_product_runtime"] is False)
 if ".head." in p.name:ck("git_head:"+p.name,out.decode().strip()==prep["old_head"])
 if ".status." in p.name:ck("git_status:"+p.name,hashlib.sha256(out).hexdigest()=="e03849874f27dcf3b079cb84c9bae69ad97311118da47c3122a5a9b32b9611b4" and len(out)==894)
 if ".index." in p.name:ck("git_index:"+p.name,out==b"")
operations=[("actual-go-validation","build-packages",1),("actual-go-validation-v2-readonly","build-packages",0),("actual-go-validation-v2-readonly","domain-qualification",0),("actual-go-validation-v2-readonly","cli-snapshot",1),("actual-go-validation-v3-fixtures","build-cli-binary",0),("actual-go-validation-v3-fixtures","build-control-binary",0),("actual-go-validation-v3-fixtures","cli-strict-response-with-compiled-binary",0),("actual-go-validation-v3-fixtures","host-control",0)]
for folder,name,code in operations:
 p=P/folder/(name+".invocation.json");iv=j(p);out,err=checkjob(iv,folder+"/"+name,code)
 intent=j(P/folder/(name+".intent.json"));ck(name+":"+folder+":intent_argv_env",iv["argv"]==intent["argv"] and iv["environment"]==intent["public_environment"] and iv["cwd"]==intent["cwd"])
 ck(name+":"+folder+":native_layer",iv["actual_native_exit"]==code and iv["exception"] is None and iv["source_qualification"] is False and iv["formal_acceptance"] is False)
 text=out.decode("utf8")
 top=re.findall(r"^--- (PASS|FAIL|SKIP): ([^ ]+)",text,re.M);allrows=re.findall(r"^\s*--- (PASS|FAIL|SKIP): ([^ ]+)",text,re.M)
 ck(name+":"+folder+":not_zero_tests",not("no tests to run" in text or "[no test files]" in text) and (len(top)>0 if "test" in iv["argv"] else True))
 summaries.append({"operation":folder+"/"+name,"invocation_ref":ref(p),"top_level_results":[{"result":s,"test":n} for s,n in top],"all_result_counts":{status:sum(s==status for s,n in allrows) for status in ("PASS","FAIL","SKIP")},"native_exit":code,"stdout_ref":iv["stdout_ref"],"stderr_ref":iv["stderr_ref"]})
 if folder=="actual-go-validation":ck("failure675_exact_cause","inconsistent vendoring" in err.decode("utf8") and iv["environment"]["GOFLAGS"]=="-mod=vendor -p=1")
 else:ck(name+":"+folder+":readonly_offline",iv["environment"]["GOFLAGS"]=="-mod=readonly -p=1" and iv["environment"]["GOPROXY"]=="off")
 if name=="domain-qualification":
  ck("domain10pass1skip",sum(s=="PASS" for s,n in top)==10 and [(s,n) for s,n in top if s!="PASS"]==[("SKIP","TestRuntimeMuTypedCancelStopsTransport")])
 if name=="cli-snapshot":
  ck("failure676_exact_prerequisite","compiled CLI and owned evidence directory are required" in text and sum(s=="PASS" for s,n in top)==6 and [(s,n) for s,n in top if s!="PASS"]==[("FAIL","TestCLIProtocolStrictResponse")])
 if name=="cli-strict-response-with-compiled-binary":ck("strict_cli_pass_no_skip",top==[("PASS","TestCLIProtocolStrictResponse")] and all(s=="PASS" for s,n in allrows))
 if name=="host-control":ck("four_host_control_pass_no_skip",len(top)==4 and all(s=="PASS" for s,n in allrows))
v3=j(P/"actual-go-validation-v3-fixtures/validation.closed.json")
for r in v3["operations"]+[v3["cli_binary_ref"],v3["control_binary_ref"]]:verify(r)
froot=P/"actual-go-validation-v3-fixtures/cli-protocol-fixtures";fixtures=[]
for d in sorted(froot.iterdir()):
 if not d.is_dir():continue
 name=d.name.removeprefix("TestCLIProtocolStrictResponse_");iv=j(d/"invocation.json")
 expected=0 if name in ("valid-null","large-exact") else 1
 ck("protocol_original_exit:"+name,iv["exit_code"]==expected and iv["timeout"] is False and iv["measurement_mode"]=="FIXTURE_PROTOCOL")
 ck("protocol_exact_compiled_binary:"+name,path(iv["actualargv"][0]).resolve()==path(v3["cli_binary_ref"]["path"]).resolve() and iv["actualargv"][1:]==["status"])
 ck("protocol_preserves_config:"+name,read(d/"config.before.json")==read(d/"config.after.json"))
 for f in d.iterdir():
  if f.is_file():read(f)
 fixtures.append({"case":name,"invocation_ref":ref(d/"invocation.json"),"exit_code":iv["exit_code"]})
ck("protocol34real_child_invocations",len(fixtures)==34)
for f in (P/"actual-go-validation-v3-fixtures/host-fixtures").rglob("*"):
 if f.is_file():read(f)
for name in ("failure-origin.675.actual-go-build.original.json","failure-origin.676.actual-cli-snapshot.original.json","root-main-adoption.once.original-tool-io.json","validate_five_go.local_owned.py","validate_five_go.local_owned.v2.readonly.py","validate_five_go.local_owned.v3.fixtures.py"):read(P/name)
failure675=j(P/"failure-origin.675.actual-go-build.original.json");failure676=j(P/"failure-origin.676.actual-cli-snapshot.original.json")
ck("failure675_layers_preserved",failure675["actual_outer_tool_exit"]==failure675["actual_python_exit"]==failure675["actual_native_exit"]==1 and failure675["original_tool_result"]["exit_code"]==1)
ck("failure676_layers_preserved",failure676["actual_outer_tool_exit"]==failure676["actual_python_exit"]==failure676["actual_native_exit"]==1 and failure676["polls"][-1]["result"]["exit_code"]==1)
for s in ("internal/domain/runtime_model_windows_test.go","internal/domain/runtime_qualification_test.go","apps/cli/cli_stream_test.go","internal/host/w03_current_contracts_test.go","internal/host/client_configuration_windows_test.go","apps/control/bootstrap_test.go"):read(R/s)
for r in closure["canonical_refs"]:verify(r)
report={"schema":"researchos.sdk-five-go-actual-independent-audit.v1","checks":checks,"failed_checks":[x for x in checks if not x["passed"]],"pins":list(pins.values()),"jobs":jobs,"test_summaries":summaries,"protocol_child_fixtures":fixtures,"actual_main_targets":adopt["targets"],"canonical_refs":closure["canonical_refs"],"skipped_test":"TestRuntimeMuTypedCancelStopsTransport","scope":"Local compile and fixture tests only; no SDK/model/runtime/formal qualification","reviewer_native_calls":0,"reviewer_git_calls":0,"reviewer_main_or_canonical_writes":0}
with (O/"audit.json").open("x",encoding="utf8",newline="\n") as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write("\n")
print(json.dumps({"checks":len(checks),"failed_checks":report["failed_checks"],"pins":len(pins),"jobs":len(jobs),"fixtures":len(fixtures),"test_summaries":[{"operation":x["operation"],"top":x["top_level_results"],"counts":x["all_result_counts"]} for x in summaries]},ensure_ascii=False))
