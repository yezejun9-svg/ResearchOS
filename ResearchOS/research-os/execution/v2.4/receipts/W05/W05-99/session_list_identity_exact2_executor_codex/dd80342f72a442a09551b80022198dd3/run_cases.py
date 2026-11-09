import pathlib,json,hashlib,subprocess,os,datetime,sys
ROOT=pathlib.Path("D:/作品集/ResearchOS/research-os")
OUT=pathlib.Path(__file__).resolve().parent
WT=ROOT/".local/worktrees/codex-w0599-session-list-identity-r306"
NAMES=["NullContext","OwnedContext","ContextNotResultFilter","ExactReplayAfterCommit","ChangedPayloadConflict","ChangedSIDConflict","CrossProjectContext","ForeignPrincipalContext","ForeignPrincipalNullList","UnknownContext","ProjectGrantDenied","CrossProjectCursor","CrossPrincipalCursor","MalformedRequest"]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(n,d):
 with (OUT/n).open("x",encoding="utf-8") as f:json.dump(d,f,ensure_ascii=False,indent=2)
def actual(e):
 p=pathlib.Path(e["path"]);return {"path":str(p),"sha256":sha(p),"bytes":p.stat().st_size}
build=json.loads((OUT/"build.result.json").read_bytes())
if build["status"]!="COMPILED_ONLY_CASES_NOT_RUN":raise RuntimeError("no fresh build")
base=json.loads((OUT/"inputs.after_compile.json").read_bytes());work=json.loads((OUT/"compiled_WORK_vector.json").read_bytes());ex=json.loads((OUT/"testexe.json").read_bytes())
extra=[actual({"path":str(p)}) for p in [pathlib.Path(__file__),OUT/"scope.original.json",OUT/"testexe.json",OUT/"build.result.json",OUT/"go-list.stdout.raw",OUT/"launch_cases.py"]]
freeze=base+work+[actual(ex)]+extra
if len({e["path"] for e in freeze})!=len(freeze):
 unique={}
 for e in freeze:
  if e["path"] in unique and unique[e["path"]]!=e:raise RuntimeError("ambiguous compiled input")
  unique[e["path"]]=e
 freeze=list(unique.values())
mains=list((OUT/"generated").rglob("_testmain.go"))
if len(mains)!=1 or 'TestSessionListHTTPOriginalContextIdentity' not in mains[0].read_text(encoding="utf-8"):raise RuntimeError("actual generated testmain missing case")
current=[actual(e) for e in freeze]
if current!=freeze:raise RuntimeError("before firstcase source/compiler/exe drift")
save("inputs.before_first_case.json",current)
results=[];stop=None;total=0
# Windows API fixture executes no NativeHost, SDK, worker, provider, external network.
env=os.environ.copy();env["RESEARCHOS_SESSION_LIST_EVIDENCE"]=str(OUT/"cases");env["GOTOOLCHAIN"]="local";env["GOENV"]="off"
exe=ex["path"]
try:
 for idx,name in enumerate(NAMES):
  case={"id":f"L{idx+1:02d}","leaf":name,"status":"NOT_RUN"};results.append(case)
  if stop:continue
  args=[exe,"-test.run",r"^TestSessionListHTTPOriginalContextIdentity$/^"+name+r"$","-test.v","-test.timeout=150s"]
  stem=f"case-{idx+1:02d}";start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  with (OUT/(stem+".stdout.raw")).open("xb") as stdout,(OUT/(stem+".stderr.raw")).open("xb") as stderr:
   child=subprocess.run(args,cwd=WT/"internal/api",env=env,stdout=stdout,stderr=stderr,timeout=180)
  save(stem+".invocation.json",{"argv":args,"cwd":str(WT/"internal/api"),"environment_overrides":{"RESEARCHOS_SESSION_LIST_EVIDENCE":env["RESEARCHOS_SESSION_LIST_EVIDENCE"],"GOTOOLCHAIN":"local","GOENV":"off"},"actual_exit":child.returncode,"started_at":start,"ended_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"testexe_sha256":sha(exe),"stdout_sha256":sha(OUT/(stem+".stdout.raw")),"stderr_sha256":sha(OUT/(stem+".stderr.raw"))})
  case["native_exit"]=child.returncode
  stdout=(OUT/(stem+".stdout.raw")).read_text(encoding="utf-8",errors="strict")
  directory=OUT/"cases"/("TestSessionListHTTPOriginalContextIdentity__"+name)
  checks={"native0":child.returncode==0,"leaf_pass":("--- PASS: TestSessionListHTTPOriginalContextIdentity/"+name+" (") in stdout,"parent_pass":"--- PASS: TestSessionListHTTPOriginalContextIdentity (" in stdout,"no_fail_skip":"--- FAIL:" not in stdout and "--- SKIP:" not in stdout}
  for filename in ["assertions.json","closed-proof.json"]:
   q=directory/filename
   if q.is_file():
    obj=json.loads(q.read_bytes());case[filename]=obj
   else:checks[filename+"_exists"]=False
  cl=case.get("closed-proof.json",{});ass=case.get("assertions.json",{})
  checks["closed_semantics"]=cl.get("all_table_schema_multisets_equal") is True and cl.get("closed_copy_bytes_unchanged_by_read") is True
  checks["all_assertions_reached"]=ass.get("all_assertions_reached") is True
  calls=cl.get("HTTP_calls_including_setup");checks["HTTP_bound"]=isinstance(calls,int) and 0<calls<=16
  if isinstance(calls,int):total+=calls
  checks["aggregate_HTTP_bound"]=total<=224
  case["checks"]=checks
  if not all(checks.values()):stop=case["id"];case["status"]="UNEXPECTED_STOPPED";continue
  case["status"]="PASS_DEVELOPMENT_FIXTURE_ONLY"
except BaseException as e:
 stop=stop or "DRIVER_EXCEPTION";save("driver.exception.json",{"error":repr(e),"stop":stop,"no_retry":True});raise
finally:
 after=[actual(e) for e in freeze];save("inputs.after_cases.json",after)
 drift=[{"before":x,"after":y} for x,y in zip(freeze,after) if x!=y]
 save("result.json",{"cases":results,"remaining_NOT_RUN":[n for n in NAMES if n not in [x["leaf"] for x in results] or any(x["leaf"]==n and x["status"]=="NOT_RUN" for x in results)],"first_unexpected":stop,"input_count":len(freeze),"input_drift":drift,"HTTP_calls_including_setup":total,"SDK_worker_model_external_paid":0,"source_acceptance":False,"formal_increment":0})
 print(json.dumps({"pass":sum(x["status"]=="PASS_DEVELOPMENT_FIXTURE_ONLY" for x in results),"stop":stop,"inputs":len(freeze),"drift":len(drift),"HTTP_calls":total}))
 if drift:stop=stop or "INPUT_DRIFT"
if stop:sys.exit(1)
