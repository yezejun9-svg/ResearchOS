import sys
sys.dont_write_bytecode=True
import ast,hashlib,json,types,inspect
from pathlib import Path
P=Path(__file__).resolve().parent;R=Path("D:/作品集/ResearchOS/research-os")
def pin(p):
 p=Path(p);b=p.read_bytes();return {"path":str(p),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}
def save(n,v):
 p=P/n
 with p.open("xb") as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode())
 return pin(p)
source_refs=[pin(P/n) for n in ("owned_job_hooks.py","phase_worker.py","job_probe_worker.py","controller.py")]
for ref in source_refs:ast.parse(Path(ref["path"]).read_bytes());compile(Path(ref["path"]).read_bytes(),ref["path"],"exec")
h=types.ModuleType("pure_owned_hook");h.__file__=str(P/"owned_job_hooks.py")
exec(compile((P/"owned_job_hooks.py").read_bytes(),h.__file__,"exec"),h.__dict__)
derived=h.load_hooked_owned_process();signature=str(inspect.signature(derived.run_owned));assert "before_resume=None" in signature
base=h.BASE.read_bytes().decode();assert base.count(h.SIGNATURE)==base.count(h.ASSIGNED)==1
assert h.ASSIGNED in base and base.index(h.ASSIGNED)<base.index("prior = resume(pi.hThread)")
worker=ast.parse((P/"phase_worker.py").read_bytes());calls=[n for n in ast.walk(worker) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ("Popen","run","create_subprocess_exec")];assert not calls
report={"schema":"researchos.mu-sdk-controller-source-preparation.v1","actor_id":"codex:/root",
 "head":"adc460c2138528f163f7fdab5e8d81dde157b7fb","source_refs":source_refs,
 "derived_owned_base_ref":pin(h.BASE),"four_sources_compiled":True,"derived_signature":signature,
 "callback_position":"AFTER_ACTUAL_ASSIGN_BEFORE_RESUME","phase_worker":"SAME_PID_PRECHECK_THEN_PHASE",
 "native_candidate_executions":0,"actual_provider_requests":0,"qualification":False,"formal_acceptance":False,
 "source_execution_ready":False,"open":["TRUSTED_QUALIFICATION_HOST_ADMISSION_AND_DISPATCH",
 "INDEPENDENT_CONTROLLER_OBSERVER_SOURCE_REVIEW","ACTUAL_CALLBACK_PID_JOB_DEVELOPMENT_PROBE",
 "CURRENT_PHASE_SEED_AND_NONAUTHOR_OBSERVATION_AUTHORITY"],
 "pending_actual_failures":[680,681],"registered_failure_count":679,"observed_failure_count":681}
report_ref=save("report.json",report)
refs=[pin(x) for x in sorted(P.iterdir(),key=lambda x:x.name) if x.is_file() and x.name not in ("manifest.json","handoff.json")]
manifest_ref=save("manifest.json",{"schema":"researchos.immutable-source-manifest.v1","members":refs,"write_policy":"IMMUTABLE_AFTER_SEAL"})
handoff=save("handoff.json",{"schema":"researchos.controller-source-handoff.v1","actor_id":"codex:/root","state":"SOURCE_PREPARATION_ONLY_WITH_OPEN","manifest_ref":manifest_ref,"report_ref":report_ref,"source_refs":source_refs,"source_execution_ready":False,"execution_grant_issued":False,"open":report["open"],"stop_source_writes":True})
print(json.dumps({"handoff_ref":handoff,"manifest_ref":manifest_ref,"source_refs":source_refs}),flush=True)
