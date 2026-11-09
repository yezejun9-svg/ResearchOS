import sys,json,hashlib
from pathlib import Path
R=Path(r"D:/作品集/ResearchOS/research-os");O=Path(__file__).resolve().parent;C=Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-temp-controller-config-root-1791508950616");S=Path(r"D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-temp-positive-serve-root-1791509017626")
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
cfg=json.loads((C/"controller.public.config.json").read_bytes());hc=json.loads(Path(cfg["HarnessConfig"]["path"]).read_bytes())
go=json.loads((C/"controller-runtime/test.invocation.json").read_bytes());outer=json.loads((S/"serve-outer.invocation.json").read_bytes())
assert go["result"]["actual_exit"]==outer["result"]["actual_exit"]==1
for q in (go,outer):
 j=q["result"]["job_cleanup"];assert j["handles_closed"] and j["job_idle_confirmed"] and j["primary_exit_confirmed"] and j["active_processes_last_observed"]==0 and not j["errors"]
assert json.loads((C/"controller-runtime/controller.closed.json").read_bytes())["job_and_guards_closed"]
facts={"schema":"researchos.original-failure.v1","ordinal":868,"actual_outer_exit":1,"actual_python_exit":1,"actual_native_exit":1,"broker_private_helper_or_backup_child_launched":False,"broker_python_exit_source_reported":1,"broker_python_exit_independently_held":None,"diagnostic":"Go forwards four public temp keys; pinned Python broker still demands exact legacy SystemRoot/WINDIR pair and rejects before private read/helper/native rehearsal. Whole SQL unchanged; specific fixture released and both owned Root Python/Go jobs closed.","actual_native_Go_identity":{"pid":go["result"]["owned_child_pid"],"creation_time_100ns_decimal":str(go["result"]["creation_time_100ns"])},"actual_native_outer_Python_identity":{"pid":outer["result"]["owned_child_pid"],"creation_time_100ns_decimal":str(outer["result"]["creation_time_100ns"])},"original_tool_io_ref":pin(O/"original-root-native-tool-io.json"),"actual_go_invocation_ref":pin(C/"controller-runtime/test.invocation.json"),"actual_outer_invocation_ref":pin(S/"serve-outer.invocation.json"),"controller_closed_ref":pin(C/"controller-runtime/controller.closed.json"),"root_outer_closed_ref":pin(S/"serve-outer.closed.json"),"signatures_created":0,"original_trial_touched":False,"original_trial_provider_requests":None,"native_positive_accepted":False,"formal_acceptance":False,"counter_reset":False}
p=O/"failure-origin.868.json"
with p.open("xb") as f:f.write((json.dumps(facts,ensure_ascii=True,indent=2)+"\n").encode())
print(json.dumps({"failure_origin_ref":pin(p),"Root_owned_jobs_closed":2,"broker_private_helper_started":False}))
