import sys
sys.dont_write_bytecode=True
import hashlib,json,os,sqlite3,threading,time,types,uuid
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");O=Path(__file__).resolve().parent
B=R/"execution/v2.4/receipts/W05/W05-99";S=B/"sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d"
G=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py"
C=B/"mu_sdk_controller_revision_v6_codex/c309fe6cec1c400ea212065fbd484e73"
P=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py"
CLI=S/"actual-go-validation-v3-fixtures/researchos.exe";HOST=S/"actual-go-validation-v3-fixtures/researchos-control.exe"
V=B/"mu_model_sdk_real_trial_v9_source_codex/8c135404809b41a5a795574699bd0249/mu_sdk_trial.v9.proposed.py"
PY=Path("C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe")
FIXED=[(V,"cbfa40e8376ad284df6521b43d64380488017ee41c7411a339dae853ed77a98f",90096),(G,"e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85",11404),(P,"6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad",18901),(CLI,"8098a45bcb7a5e8f4ca84738f99c985f417fcf37dcea49b2ca7f658c7a832c7d",19838976),(HOST,"260e04d14beaac2ac87d581fe92a242b8aca33538484dffa779782f246476d05",33458688),(C/"owned_job_hooks.py","418e46b0461d8a92a6163fa3a20057a773ae2238cdae40b1043522c288bd94e8",2263),(C/"job_deadline_watchdog.py","6af03123b3d8c47f07f9aa1a65d0b1b8bdc2c020244d36e51e4cc6568df035ba",2953),(C/"held_job_cleanup_producer.py","17ebea83cedcb443b5e5c3669eb9d9d7178b376c3d90557e008aaf3965e58cee",9499),(PY,"cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b",106328)]
def pin(p):
 b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def write(name,value):
 p=O/name
 with p.open("xb") as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
def module(p,raw):
 m=types.ModuleType("bootstrap_"+p.stem);m.__file__=str(p);exec(compile(raw,str(p),"exec"),m.__dict__);return m
for p,h,n in FIXED:assert pin(p)["sha256"]==h and pin(p)["bytes"]==n
CANON=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")]
canon_before={str(p):p.read_bytes() for p in CANON}
assert json.loads(canon_before[str(CANON[0])])["revision"]==346
gm=module(G,G.read_bytes());guard=gm.SourceReadGuard();guard.acquire([pin(p) for p,h,n in FIXED]+[pin(Path(__file__).resolve())])
hooks=module(C/"owned_job_hooks.py",guard.get_buffer(str(C/"owned_job_hooks.py")))
wm=module(C/"job_deadline_watchdog.py",guard.get_buffer(str(C/"job_deadline_watchdog.py")))
pm=module(C/"held_job_cleanup_producer.py",guard.get_buffer(str(C/"held_job_cleanup_producer.py")))
run_uuid=uuid.uuid4().hex;data=R/".local"/("mu-sdk-isolated-project-"+run_uuid);workspace=data/"workspace"
assert not data.exists();workspace.mkdir(parents=True);(data/"trial-control").mkdir()
witness="RESEARCHOS-WITNESS-"+run_uuid[:16]
(workspace/"evidence.txt").write_bytes((witness+"\n").encode())
discovery=data/"discovery.json";config=data/"cli-config.json"
allowed=["SystemRoot","WINDIR","PATH","USERPROFILE","LOCALAPPDATA","APPDATA","TEMP","TMP"]
env={k:os.environ[k] for k in allowed if k in os.environ};env["SystemRoot"]=env["WINDIR"]="C:/Windows";env["PATH"]="C:/Windows/System32;C:/Windows"
host_env={**env,"RESEARCHOS_DATA_DIR":str(data),"RESEARCHOS_LISTEN":"127.0.0.1:0","RESEARCHOS_WEB_DIR":str(R/"apps/web/dist")}
cli_env={**env,"RESEARCHOS_CLI_DISCOVERY":str(discovery),"RESEARCHOS_CLI_CONFIG":str(config)}
assert (R/"apps/web/dist/index.html").is_file()
intent=write("bootstrap.intent.json",{"schema":"researchos.actual-cli-bootstrap-intent.v1","actor":"codex:/root","phase":"BOOTSTRAP_ONLY_PRE_TRIAL","source_commit":"adc460c2138528f163f7fdab5e8d81dde157b7fb","data_root":str(data),"workspace":str(workspace),"discovery_file":str(discovery),"cli_config_file":str(config),"witness_ref":pin(workspace/"evidence.txt"),"source_refs":[pin(p) for p,h,n in FIXED],"canonical_refs":[pin(p) for p in CANON],"no_runtime_coordinator":True,"provider_requests":0,"formal_acceptance":False})
jobs={};job_lock=threading.Lock();host_thread=None;error=None;host_started=threading.Event();host_stop=None;provider_requests=0
def safe_native(result):
 if not isinstance(result,dict):return False
 c=result.get("job_cleanup",{})
 return result.get("error") is None and c.get("errors")==[] and c.get("active_processes_last_observed")==0 and all(c.get(k) is True for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
def invoke(label,argv,child_env,timeout,expect_zero=True):
 record={"label":label,"argv":argv,"cwd":str(R),"environment":child_env,"result":None,"watchdog":None,"producer":None,"identity":None}
 with job_lock:jobs[label]=record
 def before(actual):
  producer=pm.HeldJobCleanupProducer(run_uuid+":"+label,os.getpid());record["producer"]=producer
  record["identity"]=producer.capture_before_resume(actual)
  watchdog=wm.JobDeadlineWatchdog(actual["job_handle"],actual["absolute_deadline_monotonic"]);record["watchdog"]=watchdog;watchdog.start()
  write(label+".before-resume.actual.json",{"actor":"codex:/root","identity":record["identity"],"actual_deadline_monotonic":actual["absolute_deadline_monotonic"],"assigned_before_resume":actual["assigned_before_resume"],"resumed":actual["resumed"]})
  if label=="normal-host":host_started.set()
 with (O/(label+".stdout.raw")).open("xb") as out,(O/(label+".stderr.raw")).open("xb") as err:
  record["result"]=hooks.run_owned_hooked(argv,str(R),child_env,out,err,timeout,before,creation_flags=0x08000000)
 result=record["result"]
 write(label+".invocation.json",{"argv":argv,"cwd":str(R),"environment":child_env,"result":result,"actual_native_exit":result.get("actual_exit"),"stdout_ref":pin(O/(label+".stdout.raw")),"stderr_ref":pin(O/(label+".stderr.raw")),"provider_requests":0,"formal_acceptance":False})
 assert safe_native(result),"actual owned child cleanup incomplete"
 if expect_zero:assert result["actual_exit"]==0 and result["timed_out"] is False,"CLI command did not succeed"
 return [json.loads(line) for line in (O/(label+".stdout.raw")).read_text(encoding="utf-8").splitlines()] if expect_zero else result
def start_host():
 global error
 try:invoke("normal-host",[str(HOST),"--discovery-file",str(discovery)],host_env,30,False)
 except BaseException as exc:error=repr(exc)
try:
 host_thread=threading.Thread(target=start_host);host_thread.start()
 assert host_started.wait(5),"normal Host did not reach actual suspended capture"
 until=time.monotonic()+10
 while not discovery.is_file():
  assert time.monotonic()<until and host_thread.is_alive(),"normal Host discovery unavailable"
  time.sleep(0.05)
 discovered=json.loads(discovery.read_bytes());assert discovered["pid"]==jobs["normal-host"]["identity"]["runner_pid"]
 assert Path(discovered["data_dir"])==data and discovered["url"].startswith("http://127.0.0.1:")
 assert not config.exists()
 init_rows=invoke("cli-init",[str(CLI),"init",str(workspace)],cli_env,10)
 projects={row["project_id"] for row in init_rows if row.get("project_id")};assert len(projects)==1
 project_id=projects.pop();initial_config=config.read_bytes();before_config=json.loads(initial_config);assert before_config["project_id"]==project_id and before_config["session_id"]==""
 with (O/"cli-init.config.after.raw").open("xb") as f:f.write(initial_config)
 goal_rows=invoke("cli-goal",[str(CLI),"goal","Verify the isolated Mu SDK model and read tool roundtrip","--project",project_id,"--draft"],cli_env,10)
 assert len(goal_rows)==1 and goal_rows[0]["execution"]=={"status":"NOT_STARTED","independent_acceptance":"NOT_EVALUATED"}
 post_config=config.read_bytes();after_config=json.loads(post_config)
 with (O/"cli-goal.config.after.raw").open("xb") as f:f.write(post_config)
 V=B/"mu_model_sdk_real_trial_v9_source_codex/8c135404809b41a5a795574699bd0249/mu_sdk_trial.v9.proposed.py"
 assert pin(V)["sha256"]=="cbfa40e8376ad284df6521b43d64380488017ee41c7411a339dae853ed77a98f"
 vm=module(V,guard.get_buffer(str(V)));context=vm.verified_cli_draft_goal_transition({"_init_project_id":project_id},before_config,goal_rows,post_config)
 db=sqlite3.connect((data/"researchos.sqlite").as_uri()+"?mode=ro",uri=True)
 try:
  goals=[json.loads(row[0]) for row in db.execute("SELECT body FROM domain_objects WHERE project=? AND kind='Goal'",(project_id,))]
  assert len(goals)==1 and goals[0]["status"]=="DRAFT" and goals[0]["id"]==context["goal_id"]
  counts={kind:db.execute("SELECT count(*) FROM domain_objects WHERE project=? AND kind=?",(project_id,kind)).fetchone()[0] for kind in ("Task","Run","BudgetLedgerEntry")}
  counts["resource_effects"]=db.execute("SELECT count(*) FROM resource_effects WHERE project=?",(project_id,)).fetchone()[0]
  assert all(n==0 for n in counts.values())
  policies=vm.budget_chain(db,project_id,goals[0]["id"],"DRAFT")
 finally:db.close()
 write("bootstrap.result.json",{"stage":"BOOTSTRAP_ONLY","actor_id":"codex:/root","project_id":project_id,"goal_id":goals[0]["id"],"data_root":str(data),"workspace":str(workspace),"workspace_ref":after_config["workspace_ref"],"discovery_file":str(discovery),"cli_config_file":str(config),"config_revision":after_config["config_revision"],"workspace_witness":witness,"workspace_witness_ref":pin(workspace/"evidence.txt"),"cli_init_ref":pin(O/"cli-init.invocation.json"),"cli_goal_ref":pin(O/"cli-goal.invocation.json"),"policies":policies,"db_counts":counts,"typed_draft_context":context,"provider_requests":0,"qualification":None,"formal_acceptance":None})
except BaseException as exc:
 error=error or repr(exc)
 raise
finally:
 host=jobs.get("normal-host");wd=host.get("watchdog") if host else None
 if wd is not None and host_thread is not None and host_thread.is_alive():
  code=0xE0000508;ok=bool(wd.terminate(wd.handle,code));host_stop={"planned_pre_trial_host_teardown":True,"requested_exit_code":code,"actual_TerminateJobObject_return":ok,"at_monotonic":time.monotonic()}
  if not ok:error=error or "Root explicit Host teardown failed"
 if host_thread is not None:host_thread.join(35)
 cleanup_records=[];unconfirmed=False
 for label,record in jobs.items():
  result=record["result"];producer=record["producer"];watchdog=record["watchdog"]
  try:observation=producer.observe_current() if producer is not None else None
  except BaseException as exc:observation={"errors":[repr(exc)],"observation_failed":True}
  proven=safe_native(result) and observation is not None and observation.get("active_processes")==0 and observation.get("primary_exit_confirmed") is True and observation.get("pid_match") is True and observation.get("creation_match") is True and not observation.get("errors")
  try:dc=watchdog.stop_and_close() if proven and watchdog is not None else None
  except BaseException as exc:dc={"duplicate_handle_closed":False,"errors":[repr(exc)]}
  try:pc=producer.close() if proven and dc is not None and dc["duplicate_handle_closed"] is True and not dc["errors"] else None
  except BaseException as exc:pc={"closed":False,"errors":[repr(exc)]}
  closed=proven and dc is not None and dc["duplicate_handle_closed"] is True and not dc["errors"] and pc is not None and pc["closed"] is True and not pc["errors"]
  unconfirmed=unconfirmed or not closed
  cleanup_records.append({"label":label,"original_native_cleanup_confirmed":safe_native(result),"actual_fresh_cleanup":observation,"watchdog_cleanup":dc,"duplicate_producer_cleanup":pc,"closed":closed})
 if host_thread is not None and host_thread.is_alive():unconfirmed=True
 write("bootstrap.lifecycle.actual.json",{"actual_parent_pid":os.getpid(),"error":error,"jobs":cleanup_records,"host_stop":host_stop,"all_owned_jobs_cleanup_confirmed":not unconfirmed,"provider_requests":0,"formal_acceptance":False})
 if unconfirmed:
  write("bootstrap.parent-retained-unconfirmed.json",{"state":"SAME_PARENT_RETAINED_UNCONFIRMED","actual_parent_pid":os.getpid(),"data_root":str(data),"Source_guard_and_job_objects_retained":True,"automatic_retry":False,"provider_requests":0})
  while True:time.sleep(1)
 gc=guard.close();write("bootstrap.source-guard.cleanup.actual.json",gc)
 assert gc["closed"] is True and gc["retained_handles_count"]==0 and not gc["errors"]
 assert {str(p):p.read_bytes() for p in CANON}==canon_before
if error is not None:raise RuntimeError(error)
assert (O/"bootstrap.result.json").is_file()
print(json.dumps({"stage":"BOOTSTRAP_ONLY","receipt_ref":pin(O/"bootstrap.result.json"),"lifecycle_ref":pin(O/"bootstrap.lifecycle.actual.json"),"data_root":str(data),"normal_host_teardown_observed_exit":jobs["normal-host"]["result"]["actual_exit"],"cli_native_exits":[jobs[k]["result"]["actual_exit"] for k in ("cli-init","cli-goal")],"provider_requests":0,"canonical_unchanged":True,"formal_acceptance":False}),flush=True)

