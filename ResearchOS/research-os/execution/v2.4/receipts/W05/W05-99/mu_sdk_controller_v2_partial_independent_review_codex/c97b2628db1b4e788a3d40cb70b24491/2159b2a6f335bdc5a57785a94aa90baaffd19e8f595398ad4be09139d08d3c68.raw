import sys
sys.dont_write_bytecode=True
import ast,hashlib,json,difflib,types
from pathlib import Path
BASE=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/mu_sdk_controller_source_codex/2e716ffb2df44199b7d3d28cdbdddbed");P=Path(__file__).resolve().parent
def pin(p):
 b=Path(p).read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(n,v):
 p=P/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
source=(BASE/"controller.py").read_text(encoding="utf-8");assert pin(BASE/"controller.py")["sha256"]=="ddcf54587a9cb32cff4470ebf2fa2d34a57ef061dc64e27c71b5f7b610a39ae8"
old='    require(pin(path)==reference,"pinned input changed")\n    return path,path.read_bytes()'
new='    raw=path.read_bytes()\n    require({"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}==reference,"pinned input changed")\n    return path,raw'
assert source.count(old)==1;source=source.replace(old,new)
old='    public_env=dict(seed["public_environment"])'
new='''    public_env=dict(seed["public_environment"])
    allowed_env={"SystemRoot","WINDIR","ComSpec","PATH","PATHEXT",
                 "USERPROFILE","LOCALAPPDATA","APPDATA","TEMP","TMP"}
    require(set(public_env)<=allowed_env and all(type(k) is str and type(v) is str
            and "\\x00" not in k and "\\x00" not in v for k,v in public_env.items()),
            "public process environment is not closed")
    require(public_env.get("SystemRoot")=="C:/Windows" and
            public_env.get("WINDIR")=="C:/Windows","unexpected Windows system root")'''
assert source.count(old)==1;source=source.replace(old,new)
old='''def close_canonical_lease(doc,phase_dir,native_result,error):
    cp_path=ROOT/"execution/v2.4/checkpoint.json";ow_path=ROOT/"execution/v2.4/path_ownership.json"'''
new='''def cleanup_confirmed(result):
    if type(result) is not dict:return False
    c=result.get("job_cleanup",{})
    return (type(c) is dict and c.get("errors")==[] and
            c.get("active_processes_last_observed")==0 and
            all(c.get(k) is True for k in
                ("primary_exit_confirmed","job_idle_confirmed","handles_closed")))

def close_canonical_lease(doc,phase_dir,native_result,error):
    if not cleanup_confirmed(native_result):
        return exclusive_json(phase_dir/"canonical-lease.retained-unconfirmed.json",{
            "run_uuid":doc["run_uuid"],"state":"CLEANUP_UNCONFIRMED_ACTIVE_LEASE_RETAINED",
            "native_result":native_result,"exception":error,
            "checkpoint_ref":pin(ROOT/"execution/v2.4/checkpoint.json"),
            "ownership_ref":pin(ROOT/"execution/v2.4/path_ownership.json"),
            "automatic_recovery":False,"formal_acceptance":False})
    cp_path=ROOT/"execution/v2.4/checkpoint.json";ow_path=ROOT/"execution/v2.4/path_ownership.json"'''
assert source.count(old)==1;source=source.replace(old,new)
(P/"controller.py").write_text(source,encoding="utf-8",newline="")
for name in ("owned_job_hooks.py","phase_worker.py","job_probe_worker.py"):
 (P/name).write_bytes((BASE/name).read_bytes())
for name in ("controller.py","owned_job_hooks.py","phase_worker.py","job_probe_worker.py"):
 ast.parse((P/name).read_bytes());compile((P/name).read_bytes(),str(P/name),"exec")
(P/"controller.forward.diff").write_text("".join(difflib.unified_diff((BASE/"controller.py").read_text().splitlines(True),source.splitlines(True),fromfile="v1/controller.py",tofile="v2/controller.py")),encoding="utf-8",newline="")
(P/"controller.inverse.diff").write_text("".join(difflib.unified_diff(source.splitlines(True),(BASE/"controller.py").read_text().splitlines(True),fromfile="v2/controller.py",tofile="v1/controller.py")),encoding="utf-8",newline="")
tree=ast.parse(source); defs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
m=types.ModuleType("revision2_pure_cleanup");m.__dict__["Path"]=Path
exec(compile(ast.Module(body=[defs["cleanup_confirmed"]],type_ignores=[]),"<pure cleanup>","exec"),m.__dict__)
complete={"job_cleanup":{"errors":[],"active_processes_last_observed":0,"primary_exit_confirmed":True,"job_idle_confirmed":True,"handles_closed":True}}
assert m.cleanup_confirmed(complete)
controls=[]
for field,value in (("active_processes_last_observed",1),("job_idle_confirmed",False),("primary_exit_confirmed",False),("handles_closed",False),("errors",["actual cleanup error"])):
 c=json.loads(json.dumps(complete));c["job_cleanup"][field]=value;assert not m.cleanup_confirmed(c);controls.append({"field":field,"unsafe_release_refused":True})
assert not m.cleanup_confirmed(None)
report=save("report.json",{"schema":"researchos.mu-sdk-controller-partial-revision.v2","actor_id":"codex:/root",
"closed_source_changes_proposed":["R01_UNCONFIRMED_CLEANUP_RETAINS_LEASE","R03_SINGLE_VERIFIED_READ_USED","R04_CLOSED_PUBLIC_ENV_BEFORE_INTENT"],
"pure_cleanup_controls":controls,"four_sources_compiled":True,"source_refs":[pin(P/n) for n in ("controller.py","owned_job_hooks.py","phase_worker.py","job_probe_worker.py")],
"open":["R02_CANONICAL_TRANSACTION_OS_OWNERSHIP","R05_CALLBACK_ABSOLUTE_WATCHDOG","R06_OBSERVER_ARGV_CWD_PYTHON_WORKER_BINDING","NONAUTHOR_REVIEW","HOST_QUALIFICATION_INTEGRATION","ACTUAL_NATIVE_JOB_PROBE"],
"execution_ready":False,"native_candidate_executions":0,"provider_requests":0,"formal_acceptance":False,
"registered_failures":681,"observed_failures":681})
mf=save("manifest.json",{"schema":"researchos.immutable-source-manifest.v1","members":[pin(x) for x in sorted(P.iterdir(),key=lambda x:x.name) if x.is_file() and x.name not in ("manifest.json","handoff.json")]})
h=save("handoff.json",{"schema":"researchos.mu-sdk-controller-partial-revision-handoff.v2","state":"SOURCE_ONLY_WITH_OPEN_NO_EXECUTION","actor_id":"codex:/root","source_previous_handoff_ref":pin(BASE/"handoff.json"),"manifest_ref":mf,"report_ref":report,"execution_ready":False,"stop_source_writes":True})
print(json.dumps({"handoff_ref":h,"manifest_ref":mf,"report_ref":report,"controller_ref":pin(P/"controller.py")}),flush=True)
