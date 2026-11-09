import sys
sys.dont_write_bytecode=True
import hashlib,json,os,sqlite3,threading,time,types,uuid
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");B=R/"execution/v2.4/receipts/W05/W05-99";S=B/"sdk_five_go_root_adoption_preparation_codex/04a454a98b164aa2983f16245f273e9d";O=Path(__file__).resolve().parent
G=B/"source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py";C=B/"mu_sdk_controller_revision_v6_codex/c309fe6cec1c400ea212065fbd484e73"
P=B/"integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py";V=B/"mu_model_sdk_real_trial_v9_source_codex/8c135404809b41a5a795574699bd0249/mu_sdk_trial.v9.proposed.py"
CLI=S/"actual-go-validation-v3-fixtures/researchos.exe";HOST=S/"actual-go-validation-v3-fixtures/researchos-control.exe"
TRUST=R/".local/trusted-host-build-staged-85f7c8eccfaf4499b6c80261409ae2d2/trusted-qualification-host.exe"
REVIEW=B/"mu_sdk_trusted_host_v4_delta_review_codex/3874b7621ecbe249b42144ded9b65406/review.json"
PRIOR=B/"actual_cli_bootstrap_v3_component_independent_review_codex/d391a2e49cf24d559e7d58016b8eb41e/review.json"
seedpath=O/"seed.public.actual.json";seed=json.loads(seedpath.read_bytes());data=Path(seed["data_root"]);workspace=Path(seed["workspace_dir"]);discovery=Path(seed["discovery_file"]);config=Path(seed["cli_config_file"])
FIXED=[(G,"e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85"),(P,"6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad"),(V,"cbfa40e8376ad284df6521b43d64380488017ee41c7411a339dae853ed77a98f"),(CLI,"8098a45bcb7a5e8f4ca84738f99c985f417fcf37dcea49b2ca7f658c7a832c7d"),(HOST,"260e04d14beaac2ac87d581fe92a242b8aca33538484dffa779782f246476d05"),(TRUST,"117638d8215a20516693dc1b6380723e3d968c17220c918f3051f16b43560099"),(REVIEW,"06f6c01a597c877b915443433323460b55093ae2194960f545f3cab55140127a"),(PRIOR,"ce0691c2776d2ab6e95e19a019bb2f424c15b5aafc3b9ff2f20907cfda43cec4"),(C/"owned_job_hooks.py","418e46b0461d8a92a6163fa3a20057a773ae2238cdae40b1043522c288bd94e8"),(C/"job_deadline_watchdog.py","6af03123b3d8c47f07f9aa1a65d0b1b8bdc2c020244d36e51e4cc6568df035ba"),(C/"held_job_cleanup_producer.py","17ebea83cedcb443b5e5c3669eb9d9d7178b376c3d90557e008aaf3965e58cee")]
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def write(name,obj):
 p=O/name
 with p.open("xb") as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
def module(p,raw):
 m=types.ModuleType("root_staged_"+p.stem);m.__file__=str(p);exec(compile(raw,str(p),"exec"),m.__dict__);return m
for p,h in FIXED:assert pin(p)["sha256"]==h,str(p)
assert data==R/".local/mu-sdk-isolated-project-ed84838046934329a76733a005c9b162" and seed["project_id"]=="a814e5698c6b65a8423bbe0bcd1c94f1" and seed["draft_goal_id"]==""
CANON=[R/"execution/v2.4"/(n+".json") for n in ("checkpoint","path_ownership","step_state","commands")];canon_before={p:p.read_bytes() for p in CANON};assert json.loads(canon_before[CANON[0]])["revision"]==347
refs=[pin(p) for p,h in FIXED]+[pin(seedpath),pin(Path(seed["profile_file"])),pin(Path(seed["node_executable"])),pin(Path(seed["bundle_file"])),pin(Path(__file__).resolve()),pin(O/"public-route.actual.json")]
gm=module(G,G.read_bytes());guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024);guard.acquire(refs)
hooks=module(C/"owned_job_hooks.py",guard.get_buffer(str(C/"owned_job_hooks.py")));wm=module(C/"job_deadline_watchdog.py",guard.get_buffer(str(C/"job_deadline_watchdog.py")));pm=module(C/"held_job_cleanup_producer.py",guard.get_buffer(str(C/"held_job_cleanup_producer.py")));vm=module(V,guard.get_buffer(str(V)))
env={k:os.environ[k] for k in ("SystemRoot","WINDIR","PATH","USERPROFILE","LOCALAPPDATA","APPDATA","TEMP","TMP") if k in os.environ};env.update(SystemRoot="C:/Windows",WINDIR="C:/Windows",PATH="C:/Windows/System32;C:/Windows")
hostenv={**env,"RESEARCHOS_DATA_DIR":str(data),"RESEARCHOS_LISTEN":"127.0.0.1:0","RESEARCHOS_WEB_DIR":str(R/"apps/web/dist")};clienv={**env,"RESEARCHOS_CLI_DISCOVERY":str(discovery),"RESEARCHOS_CLI_CONFIG":str(config)}
jobs={};host_thread=None;host_started=threading.Event();host_stop=None;error=None;run_uuid=uuid.uuid4().hex
resident_owner=dict(actual_parent_pid=os.getpid(),jobs=jobs,source_guard=guard,parent_retained=False)
setattr(sys,"_researchos_staged_zero_provider_root_owner",resident_owner)
def retain_parent(reason):
 resident_owner.update(parent_retained=True,retention_reason=reason)
 try:write("parent-retained-unconfirmed.actual.json",dict(actual_parent_pid=os.getpid(),Source_guard_and_jobs_retained=True,error=reason,automatic_retry=False,provider_requests=0))
 except BaseException as exc:resident_owner["retention_report_error"]=repr(exc)
 finally:
  while True:
   try:threading.Event().wait(1)
   except BaseException as exc:resident_owner["retention_wait_error"]=repr(exc)
def safe_native(result):
 if not isinstance(result,dict):return False
 c=result.get("job_cleanup",{})
 return result.get("error") is None and c.get("errors")==[] and c.get("active_processes_last_observed")==0 and all(c.get(k) is True for k in ("unnamed_exclusive_job","kill_on_job_close_configured","assigned_before_resume","primary_exit_confirmed","job_idle_confirmed","handles_closed"))
def invoke(label,argv,child_env,timeout,zero=True):
 assert label not in jobs,"no automatic retry"
 rec=dict(label=label,result=None,producer=None,watchdog=None,identity=None,closure_ref=None);jobs[label]=rec
 def before(actual):
  rec["producer"]=pm.HeldJobCleanupProducer(run_uuid+":"+label,os.getpid());rec["identity"]=rec["producer"].capture_before_resume(actual)
  rec["watchdog"]=wm.JobDeadlineWatchdog(actual["job_handle"],actual["absolute_deadline_monotonic"]);rec["watchdog"].start()
  write(label+".before-resume.actual.json",dict(identity=rec["identity"],assigned_before_resume=actual["assigned_before_resume"],resumed=actual["resumed"],actual_deadline_monotonic=actual["absolute_deadline_monotonic"]))
  if label=="normal-host":host_started.set()
 try:
  with (O/(label+".stdout.raw")).open("xb") as stdout,(O/(label+".stderr.raw")).open("xb") as stderr:rec["result"]=hooks.run_owned_hooked(argv,str(R),child_env,stdout,stderr,timeout,before,creation_flags=0x08000000)
 finally:
  result=rec["result"]
  rec["invocation_ref"]=write(label+".invocation.json",dict(argv=argv,cwd=str(R),environment=child_env,result=result,actual_native_exit=result.get("actual_exit") if result else None,stdout_ref=pin(O/(label+".stdout.raw")),stderr_ref=pin(O/(label+".stderr.raw")),provider_requests=0,formal_acceptance=False))
 assert safe_native(rec["result"]),"native cleanup incomplete"
 if zero:assert rec["result"]["actual_exit"]==0 and not rec["result"]["timed_out"],label+" failed"
 return rec
def close_job(label):
 rec=jobs[label]
 if rec["closure_ref"] is not None:return rec["closure_ref"]
 start=time.monotonic();obs=rec["producer"].observe_current() if rec["producer"] else None;end=time.monotonic()
 proven=safe_native(rec["result"]) and obs is not None and obs.get("active_processes")==0 and all(obs.get(k) is True for k in ("primary_exit_confirmed","pid_match","creation_match")) and not obs.get("errors")
 dc=rec["watchdog"].stop_and_close() if proven and rec["watchdog"] else None
 pc=rec["producer"].close() if proven and dc and dc["duplicate_handle_closed"] and not dc["errors"] else None
 closed=bool(proven and dc and dc["duplicate_handle_closed"] and not dc["errors"] and pc and pc["closed"] and not pc["errors"])
 rec["closure_ref"]=write(label+".closure.actual.json",dict(schema="researchos.staged-native-owned-closure.v1",label=label,invocation_ref=rec["invocation_ref"],identity=rec["identity"],before_resume_ref=pin(O/(label+".before-resume.actual.json")),observed_monotonic_start=start,observed_monotonic_end=end,actual_fresh_cleanup=obs,watchdog_cleanup=dc,duplicate_producer_cleanup=pc,closed=closed))
 rec["closed"]=closed
 return rec["closure_ref"]
def stop_host(require_planned=False):
 global host_stop
 rec=jobs.get("normal-host")
 if require_planned:assert rec and host_thread and host_thread.is_alive(),"Host exited before planned handoff; forbid finalize"
 if rec and host_thread and host_thread.is_alive() and rec["watchdog"]:
  code=0xE0000508;ok=bool(rec["watchdog"].terminate(rec["watchdog"].handle,code));host_stop=dict(planned_pre_trial_host_teardown=True,requested_exit_code=code,actual_TerminateJobObject_return=ok);assert ok
 if host_thread:host_thread.join(20);assert not host_thread.is_alive(),"Host parent retained; no next helper while lease uncertain"
 if rec:close_job("normal-host");assert rec["closed"]
 if require_planned:assert host_stop is not None and host_stop["actual_TerminateJobObject_return"] and rec["result"]["actual_exit"]==host_stop["requested_exit_code"] and rec["result"]["timed_out"] is False,"Host handoff exit differs from explicit planned teardown"
def start_host():
 global error
 try:invoke("normal-host",[str(HOST),"--discovery-file",str(discovery),"--runtime-coordinator-config",str(data/"host/trusted-qualification-coordinator.json"),"--trial-readonly-model-vault-dir",seed["read_only_vault_dir"],"--trial-readonly-credential-ref",seed["credential_ref"],"--trial-readonly-provider",seed["provider"]],hostenv,60,False)
 except BaseException as exc:error=repr(exc)
write("continuation.intent.json",dict(schema="researchos.actual-cli-staged-continuation-intent.v1",actor="codex:/root",seed_ref=pin(seedpath),source_refs=refs,canonical_refs=[pin(p) for p in CANON],reuse_successful_init=True,qualification_admission_authorized=False,provider_requests_authorized=0,formal_acceptance=False))
try:
 cfgbefore=config.read_bytes();before=json.loads(cfgbefore);assert before["project_id"]==seed["project_id"] and before["session_id"]==""
 with (O/"cli-config.before-goal.raw").open("xb") as f:f.write(cfgbefore)
 invoke("runtime-prepare",[str(TRUST),"-phase","prepare-runtime","-seed",str(seedpath),"-receipt",str(O/"runtime.prepare.actual.json")],env,90)
 close_job("runtime-prepare");assert jobs["runtime-prepare"]["closed"]
 prepared=json.loads((O/"runtime.prepare.actual.json").read_bytes());assert prepared["status"]=="RUNTIME_READY" and prepared["provider_requests"]==0 and prepared["qualification_task_status"]=="DRAFT"
 host_thread=threading.Thread(target=start_host);host_thread.start();assert host_started.wait(5)
 until=time.monotonic()+15
 while True:
  assert time.monotonic()<until and host_thread.is_alive(),"actual normal Host did not refresh discovery"
  try:discovered=json.loads(discovery.read_bytes())
  except (FileNotFoundError,json.JSONDecodeError):time.sleep(0.03);continue
  if discovered["pid"]==jobs["normal-host"]["identity"]["runner_pid"]:break
  time.sleep(0.03)
 assert Path(discovered["data_dir"])==data and discovered["url"].startswith("http://127.0.0.1:")
 invoke("cli-goal",[str(CLI),"goal","Verify the isolated Mu SDK model and read tool roundtrip","--project",seed["project_id"],"--draft"],clienv,15)
 close_job("cli-goal");assert jobs["cli-goal"]["closed"]
 goalrows=[json.loads(line) for line in (O/"cli-goal.stdout.raw").read_text(encoding="utf-8").splitlines()]
 post=config.read_bytes()
 with (O/"cli-config.after-goal.raw").open("xb") as f:f.write(post)
 context=vm.verified_cli_draft_goal_transition({"_init_project_id":seed["project_id"]},before,goalrows,post)
 stop_host(require_planned=True)
 invoke("finalize-prepare",[str(TRUST),"-phase","finalize-prepare","-seed",str(seedpath),"-draft-goal-id",context["goal_id"],"-receipt",str(O/"prepare.finalized.actual.json")],env,45)
 close_job("finalize-prepare");assert jobs["finalize-prepare"]["closed"]
 finalized=json.loads((O/"prepare.finalized.actual.json").read_bytes());assert finalized["status"]=="PREPARED" and finalized["draft_goal_id"]==context["goal_id"] and finalized["provider_requests"]==0
 db=sqlite3.connect((data/"researchos.sqlite").as_uri()+"?mode=ro",uri=True);db.execute("PRAGMA query_only=ON")
 try:
  project=seed["project_id"];goals=[json.loads(row[0]) for row in db.execute("SELECT body FROM domain_objects WHERE project=? AND kind='Goal'",(project,))]
  ordinary=next(g for g in goals if g["id"]==context["goal_id"]);assert len(goals)==2 and ordinary["status"]=="DRAFT"
  tasks=[json.loads(row[0]) for row in db.execute("SELECT body FROM domain_objects WHERE project=? AND kind='Task'",(project,))]
  assert len(tasks)==1 and tasks[0]["id"]==prepared["qualification_task_id"] and tasks[0]["status"]=="DRAFT" and tasks[0]["task_type"]=="runtime_qualification" and tasks[0]["goal_id"]!=ordinary["id"]
  counts={kind:db.execute("SELECT count(*) FROM domain_objects WHERE project=? AND kind=?",(project,kind)).fetchone()[0] for kind in ("Task","Run","BudgetLedgerEntry")}
  counts["resource_effects"]=db.execute("SELECT count(*) FROM resource_effects WHERE project=?",(project,)).fetchone()[0];assert counts==dict(Task=1,Run=0,BudgetLedgerEntry=0,resource_effects=0)
  policies=vm.budget_chain(db,project,ordinary["id"],"DRAFT")
 finally:db.close()
 witness=(workspace/"evidence.txt").read_text(encoding="utf-8").strip()
 write("bootstrap.result.json",dict(stage="BOOTSTRAP_ONLY",actor_id="codex:/root",project_id=project,goal_id=ordinary["id"],data_root=str(data),workspace=str(workspace),workspace_ref=seed["workspace_ref"],discovery_file=str(discovery),cli_config_file=str(config),config_revision=json.loads(post)["config_revision"],workspace_witness=witness,workspace_witness_ref=pin(workspace/"evidence.txt"),initial_cli_init_component_review_ref=pin(PRIOR),cli_init_ref=pin(S/"actual-cli-bootstrap-v3-80c7b29a01c341a884597b7da9e17c4a/cli-init.invocation.json"),cli_goal_ref=jobs["cli-goal"]["invocation_ref"],policies=policies,db_counts=counts,qualification_task_id=tasks[0]["id"],qualification_task_status="DRAFT",ordinary_goal_tasks=0,typed_draft_context=context,provider_requests=0,qualification=None,formal_acceptance=None))
except BaseException as exc:
 error=error or repr(exc)
 raise
finally:
 try:stop_host()
 except BaseException as exc:error=error or repr(exc)
 closure_rows=[];unconfirmed=host_thread is not None and host_thread.is_alive()
 for label,rec in jobs.items():
  try:
   ref=close_job(label);obj=json.loads(Path(ref["path"]).read_bytes());closure_rows.append(obj);unconfirmed=unconfirmed or not rec.get("closed",False)
  except BaseException as exc:unconfirmed=True;closure_rows.append(dict(label=label,closed=False,error=repr(exc)))
 try:
  write("bootstrap.lifecycle.actual.json",dict(schema="researchos.actual-cli-staged-continuation-lifecycle.v1",actual_parent_pid=os.getpid(),error=error,jobs=[item for item in closure_rows if item["label"] in ("normal-host","cli-goal")],prepare_closed_refs=[jobs[n]["closure_ref"] for n in ("runtime-prepare","finalize-prepare") if n in jobs],initial_cli_init_component_review_ref=pin(PRIOR),host_stop=host_stop,all_owned_jobs_cleanup_confirmed=not unconfirmed,provider_requests=0,formal_acceptance=False))
 except BaseException as exc:error=error or repr(exc)
 finally:
  if unconfirmed:retain_parent(error or "actual Job cleanup unconfirmed")
 try:
  cleanup=guard.close()
 except BaseException as exc:
  retain_parent("Source guard close raised: "+repr(exc))
 if not (cleanup["closed"] and cleanup["retained_handles_count"]==0 and not cleanup["errors"]):
  retain_parent("Source guard close incomplete")
 write("bootstrap.source-guard.cleanup.actual.json",cleanup)
 assert all(p.read_bytes()==raw for p,raw in canon_before.items()),"canonical changed"
 resident_owner["all_jobs_and_source_guards_closed"]=True
if error:raise RuntimeError(error)
print(json.dumps(dict(stage="BOOTSTRAP_ONLY",bootstrap_ref=pin(O/"bootstrap.result.json"),runtime_prepare_ref=pin(O/"runtime.prepare.actual.json"),finalize_prepare_ref=pin(O/"prepare.finalized.actual.json"),lifecycle_ref=pin(O/"bootstrap.lifecycle.actual.json"),owned_jobs=4,provider_requests=0,qualification_admitted=False,formal_acceptance=False)),flush=True)

